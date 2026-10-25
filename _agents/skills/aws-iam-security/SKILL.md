---
skill_name: aws-iam-security
description: IAM security patterns for roles, policies, permission boundaries, cross-account access, and SCPs
category: Cloud & DevOps
version: 1.0.0
---

# AWS IAM Security

## IAM Roles and Policies

### Create IAM Role
```bash
# Create role with trust policy
role=$(aws iam create-role \
  --role-name my-app-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

echo "Role ARN: $role"
```

### Inline vs Managed Policies
**Inline Policy** (not recommended — creates tight coupling):
```bash
aws iam put-role-policy \
  --role-name my-app-role \
  --policy-name s3-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-bucket/*"
    }]
  }'
```

**Managed Policy** (recommended — reusable, versioned):
```bash
# Create managed policy
policy=$(aws iam create-policy \
  --policy-name S3ReadPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    }]
  }' \
  --query 'Policy.Arn' \
  --output text)

# Attach to role
aws iam attach-role-policy \
  --role-name my-app-role \
  --policy-arn $policy
```

### Policy with Conditions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::prod-bucket/*",
      "Condition": {
        "StringEquals": {
          "aws:SourceVpc": "vpc-12345"
        },
        "IpAddress": {
          "aws:SourceIp": ["203.0.113.0/24"]
        },
        "StringLike": {
          "aws:username": "alice-*"
        }
      }
    }
  ]
}
```

## Permission Boundaries

Limit maximum permissions for a role.

```bash
# Create permission boundary policy
boundary=$(aws iam create-policy \
  --policy-name DeveloperBoundary \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ec2:*",
          "s3:*",
          "rds:Describe*",
          "logs:*"
        ],
        "Resource": "*"
      },
      {
        "Effect": "Deny",
        "Action": [
          "iam:*",
          "organizations:*",
          "kms:*"
        ],
        "Resource": "*"
      }
    ]
  }' \
  --query 'Policy.Arn' \
  --output text)

# Apply boundary to role
aws iam put-role-permissions-boundary \
  --role-name my-developer-role \
  --permissions-boundary $boundary
```

Even if a developer has an admin policy, the boundary limits them to EC2, S3, RDS, CloudWatch.

## Cross-Account Access

Access resources in another AWS account.

### Setup Cross-Account Role
In **target account (123456789012)**:

```bash
# Create role in target account
target_role=$(aws iam create-role \
  --role-name CrossAccountRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::TRUSTING_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

# Attach permission policy
aws iam attach-role-policy \
  --role-name CrossAccountRole \
  --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
```

In **trusting account (987654321098)**:

```bash
# Create policy to assume role in target account
policy=$(aws iam create-policy \
  --policy-name AssumeRolePolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::123456789012:role/CrossAccountRole"
    }]
  }' \
  --query 'Policy.Arn' \
  --output text)

# Attach to developer role
aws iam attach-role-policy \
  --role-name my-developer-role \
  --policy-arn $policy
```

In **Python application**:

```python
import boto3

# Assume role in target account
sts = boto3.client('sts')
assumed = sts.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/CrossAccountRole',
    RoleSessionName='cross-account-session',
    ExternalId='unique-external-id'
)

credentials = assumed['Credentials']

# Create client with assumed role credentials
s3 = boto3.client(
    's3',
    aws_access_key_id=credentials['AccessKeyId'],
    aws_secret_access_key=credentials['SecretAccessKey'],
    aws_session_token=credentials['SessionToken']
)

# Now can access resources in target account
s3.list_buckets()
```

## Service Control Policies (SCPs)

Organization-wide policy guardrails (AWS Organizations required).

```bash
# Create SCP to prevent deletion of CloudTrail
scp=$(aws organizations create-policy \
  --content '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Deny",
        "Action": [
          "cloudtrail:DeleteTrail",
          "cloudtrail:StopLogging"
        ],
        "Resource": "*"
      },
      {
        "Effect": "Deny",
        "Action": [
          "organizations:LeaveOrganization"
        ],
        "Resource": "*"
      }
    ]
  }' \
  --type SERVICE_CONTROL_POLICY \
  --name PreventCloudTrailDisable \
  --query 'Policy.PolicySummary.Id' \
  --output text)

# Attach to OU
aws organizations attach-policy \
  --policy-id $scp \
  --target-id ou-xxx
```

## Credential Security

### IAM Users vs Roles
**Avoid IAM users with long-term credentials.** Instead:
- Use **IAM Roles** with temporary credentials (STS)
- For humans: Use IAM Identity Center (formerly AWS SSO)
- For applications: Use EC2 instance profiles, Lambda execution roles

### Access Keys Best Practices
```bash
# Create access key (only when necessary)
access_key=$(aws iam create-access-key \
  --user-name app-user \
  --query 'AccessKey.[AccessKeyId,SecretAccessKey]' \
  --output text)

# Rotate keys every 90 days
# Delete old key after new is in use
aws iam delete-access-key \
  --user-name app-user \
  --access-key-id AKIAIOSFODNN7EXAMPLE

# Use IAM Credential Report
aws iam get-credential-report | base64 -d | head -20
```

### Temporary Credentials (STS)
```bash
# Get temporary credentials for 1 hour
temp=$(aws sts get-session-token \
  --duration-seconds 3600 \
  --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
  --output text)

export AWS_ACCESS_KEY_ID=$(echo $temp | awk '{print $1}')
export AWS_SECRET_ACCESS_KEY=$(echo $temp | awk '{print $2}')
export AWS_SESSION_TOKEN=$(echo $temp | awk '{print $3}')
```

## Resource-Based Policies

Control access to resources directly.

### S3 Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT:role/MyRole"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-bucket/*"
    },
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::my-bucket/*",
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### KMS Key Policy
```json
{
  "Sid": "Allow cross-account use",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::TRUSTED_ACCOUNT:role/AppRole"
  },
  "Action": [
    "kms:Decrypt",
    "kms:GenerateDataKey"
  ],
  "Resource": "*"
}
```

## IAM Access Analyzer

Find unintended public access.

```bash
# Create analyzer
analyzer=$(aws accessanalyzer create-analyzer \
  --analyzer-name prod-analyzer \
  --type ACCOUNT \
  --query 'arn' \
  --output text)

# Find public resources
aws accessanalyzer list-findings \
  --analyzer-arn $analyzer \
  --filter 'resourceType={"eq":["AWS::S3::Bucket"]}' \
  --query 'findings[?publicAccess==`true`]'
```

## Best Practices Summary

1. **Principle of least privilege**: Grant minimum permissions
2. **Use roles, not users**: Avoid long-term access keys
3. **Permission boundaries**: Limit maximum permissions for developers
4. **Resource-based policies**: Control access at resource level
5. **Cross-account roles**: Enable secure delegation
6. **SCPs**: Organization-wide guardrails
7. **Rotate credentials**: Change access keys every 90 days
8. **MFA**: Enable for sensitive operations
9. **Monitor**: Use CloudTrail, IAM Access Analyzer
10. **Review regularly**: Quarterly access reviews
