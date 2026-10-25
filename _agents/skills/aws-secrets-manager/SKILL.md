---
skill_name: aws-secrets-manager
description: Secrets Manager patterns for secret rotation, cross-account sharing, Lambda integration, and caching
category: Cloud & DevOps
version: 1.0.0
---

# AWS Secrets Manager

## Creating and Managing Secrets

### Create Secret
```bash
# Create database password secret
aws secretsmanager create-secret \
  --name prod/db/password \
  --description "Production database password" \
  --secret-string "$(openssl rand -base64 32)" \
  --tags Key=Environment,Value=prod Key=Application,Value=my-app

# Create API key secret
aws secretsmanager create-secret \
  --name prod/api/key \
  --secret-string '{"api_key":"abc123","api_secret":"xyz789"}'

# Create SSL certificate
aws secretsmanager create-secret \
  --name prod/ssl/cert \
  --secret-binary file://certificate.pem
```

### Retrieve Secret
```bash
# Get secret string
secret=$(aws secretsmanager get-secret-value \
  --secret-id prod/db/password \
  --query 'SecretString' \
  --output text)

# Parse JSON secret
api_key=$(aws secretsmanager get-secret-value \
  --secret-id prod/api/key \
  --query 'SecretString' \
  --output text | jq -r '.api_key')

# Get binary secret
aws secretsmanager get-secret-value \
  --secret-id prod/ssl/cert \
  --query 'SecretBinary' \
  --output text | base64 -d > cert.pem
```

### List Secrets
```bash
aws secretsmanager list-secrets \
  --filters Key=name,Values=prod \
  --query 'SecretList[].Name' \
  --output table
```

## Secret Rotation

Automatically rotate passwords without downtime.

### Setup Automatic Rotation
```bash
# Create Lambda for rotation (example for RDS)
cat > rotate-rds-password.py << 'EOF'
import json
import boto3
import pymysql
import os

sm_client = boto3.client('secretsmanager')
rds_client = boto3.client('rds')

def lambda_handler(event, context):
    secret_id = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    # Get current secret
    current = sm_client.get_secret_value(
        SecretId=secret_id,
        VersionId=token,
        VersionStage='AWSCURRENT'
    )
    current_secret = json.loads(current['SecretString'])

    if step == "create":
        # Generate new password
        import string, random
        new_password = ''.join(random.choices(
            string.ascii_letters + string.digits, k=32
        ))

        # Create new version with new password
        new_secret = current_secret.copy()
        new_secret['password'] = new_password

        sm_client.put_secret_value(
            SecretId=secret_id,
            ClientRequestToken=token,
            SecretString=json.dumps(new_secret),
            VersionStages=['AWSPENDING']
        )

    elif step == "set":
        # Update database with new password
        new = sm_client.get_secret_value(
            SecretId=secret_id,
            VersionId=token,
            VersionStage='AWSPENDING'
        )
        new_secret = json.loads(new['SecretString'])

        conn = pymysql.connect(
            host=current_secret['host'],
            user=current_secret['username'],
            password=current_secret['password'],
            database='mysql'
        )
        cursor = conn.cursor()
        cursor.execute(f"ALTER USER '{current_secret['username']}'@'%' IDENTIFIED BY '{new_secret['password']}'")
        conn.commit()
        conn.close()

    elif step == "finish":
        # Mark new version as current
        sm_client.update_secret_version_stage(
            SecretId=secret_id,
            VersionStage='AWSCURRENT',
            MoveToVersionId=token,
            RemoveFromVersionId=current['VersionId']
        )

    return {'statusCode': 200}
EOF
```

### Enable Automatic Rotation
```bash
aws secretsmanager rotate-secret \
  --secret-id prod/db/password \
  --rotation-rules AutomaticallyAfterDays=30 \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:rotate-rds-password

# Check rotation status
aws secretsmanager describe-secret \
  --secret-id prod/db/password \
  --query 'RotationRules'
```

## Cross-Account Access

Share secrets with other AWS accounts.

### Setup Cross-Account Access
In **source account (111111111111)**:

```bash
# Create secret
secret=$(aws secretsmanager create-secret \
  --name shared/api-key \
  --secret-string 'my-secret-value' \
  --query 'ARN' \
  --output text)

# Create policy to allow other account to read
aws secretsmanager put-resource-policy \
  --secret-id $secret \
  --resource-policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::222222222222:role/app-role"
      },
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "*"
    }]
  }'
```

In **target account (222222222222)**:

```bash
# Create IAM policy to access secret
aws iam put-role-policy \
  --role-name app-role \
  --policy-name read-shared-secret \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:us-east-1:111111111111:secret:shared/api-key"
    }]
  }'

# Access secret from other account
aws secretsmanager get-secret-value \
  --secret-id arn:aws:secretsmanager:us-east-1:111111111111:secret:shared/api-key
```

## Lambda Integration

Access secrets securely in Lambda.

### Lambda Function with Secrets
```python
import json
import boto3
import os
from functools import lru_cache

sm_client = boto3.client('secretsmanager')

@lru_cache(maxsize=1)
def get_secret(secret_id):
    """Cache secret to avoid repeated API calls"""
    response = sm_client.get_secret_value(SecretId=secret_id)
    return json.loads(response['SecretString'])

def lambda_handler(event, context):
    # Get database credentials
    db_secret = get_secret(os.environ['DB_SECRET_ARN'])

    # Connect to database
    import pymysql
    conn = pymysql.connect(
        host=db_secret['host'],
        user=db_secret['username'],
        password=db_secret['password'],
        database=db_secret['dbname']
    )

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT 10")
    results = cursor.fetchall()
    conn.close()

    return {
        'statusCode': 200,
        'body': json.dumps({'users': results})
    }
```

### Lambda Execution Role
```bash
aws iam put-role-policy \
  --role-name lambda-execution-role \
  --policy-name secrets-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/*"
    }]
  }'
```

## Secret Caching

Reduce API calls with local caching.

### In-Memory Cache
```python
import json
import boto3
import hashlib
from datetime import datetime, timedelta

sm_client = boto3.client('secretsmanager')

class SecretCache:
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, secret_id):
        # Check if cached and not expired
        if secret_id in self.cache:
            cached_time, secret = self.cache[secret_id]
            if (datetime.now() - cached_time).seconds < self.ttl:
                return secret

        # Fetch from Secrets Manager
        response = sm_client.get_secret_value(SecretId=secret_id)
        secret = json.loads(response['SecretString'])

        # Cache result
        self.cache[secret_id] = (datetime.now(), secret)
        return secret

cache = SecretCache(ttl_seconds=3600)

def lambda_handler(event, context):
    # Uses cache, updates only if TTL expired
    db_creds = cache.get('prod/db/password')
    # ...
```

## Encryption and Key Management

### Encrypt Secret with KMS
```bash
# Create KMS key
key=$(aws kms create-key \
  --description "Secrets Manager key" \
  --query 'KeyMetadata.KeyId' \
  --output text)

# Create secret with custom KMS key
aws secretsmanager create-secret \
  --name prod/encrypted/secret \
  --secret-string 'my-secret' \
  --kms-key-id $key
```

### Grant Cross-Account KMS Access
```bash
# Allow other account to decrypt
aws kms create-grant \
  --key-id $key \
  --grantee-principal arn:aws:iam::222222222222:role/app-role \
  --operations Decrypt GenerateDataKey
```

## Secrets Compliance

### Enforce Secret Naming Convention
```bash
# Use Secrets Manager tags for organization
aws secretsmanager tag-resource \
  --secret-id prod/db/password \
  --tags Key=Team,Value=platform Key=CostCenter,Value=eng-001

# List secrets by tag
aws secretsmanager list-secrets \
  --filters Key=tag-key,Values=Team
```

### Audit Secret Access
Enable CloudTrail to log all secret access:

```bash
# Query CloudTrail for secret access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=secretsmanager.amazonaws.com \
  --max-results 50
```

## Best Practices

1. **Use Secrets Manager for passwords**: Not environment variables
2. **Enable rotation**: Automatic password rotation reduces risk
3. **Cross-account sharing**: Use resource policies
4. **Lambda caching**: Reduce API calls with TTL cache
5. **KMS encryption**: Use custom keys for sensitive data
6. **Audit access**: CloudTrail logging for compliance
7. **Resource tagging**: Organize by team/application
8. **Least privilege**: Only grant access to needed secrets
9. **Secrets in CloudFormation**: Use SecretsManager references
10. **Monitor rotation failures**: Set up CloudWatch alarms
