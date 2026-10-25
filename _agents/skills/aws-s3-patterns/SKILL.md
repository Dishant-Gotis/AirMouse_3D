---
skill_name: aws-s3-patterns
description: S3 best practices for lifecycle policies, versioning, replication, static hosting, presigned URLs, and event triggers
category: Cloud & DevOps
version: 1.0.0
---

# AWS S3 Patterns

## Lifecycle Policies

Automatically manage object lifecycle to reduce storage costs.

### Multi-tier Storage Strategy
```json
{
  "Rules": [
    {
      "Id": "transition-to-ia",
      "Filter": {"Prefix": "logs/"},
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      },
      "Status": "Enabled"
    }
  ]
}
```

**Storage Classes**:
- **STANDARD**: Hot data, immediate access ($0.023/GB)
- **STANDARD_IA**: Warm data, 30-day minimum ($0.0125/GB, retrieval fee)
- **GLACIER**: Cold data, hours to restore ($0.004/GB, retrieval cost)
- **DEEP_ARCHIVE**: Archive, 12-hour restore ($0.00099/GB, minimal retrieval)

### Cost Example
100 GB logs accessed daily for 30 days, then archived:
- STANDARD only: $2.30/month × 12 = $27.60/year
- With lifecycle: $2.30 (30 days) + $1.25 (60 days IA) + $0.40 (275 days Glacier) = ~$4/year

## Versioning and Rollback

Enable versioning to protect against accidental deletion and enable rollback.

```bash
aws s3api put-bucket-versioning \
  --bucket my-bucket \
  --versioning-configuration Status=Enabled

# Upload multiple versions of same object
aws s3 cp app-v1.zip s3://my-bucket/app.zip
aws s3 cp app-v2.zip s3://my-bucket/app.zip

# List versions
aws s3api list-object-versions --bucket my-bucket

# Rollback to previous version
aws s3api get-object \
  --bucket my-bucket \
  --key app.zip \
  --version-id abc123 \
  app-previous.zip
```

### Versioning with Lifecycle
Automatically delete old versions:

```json
{
  "Rules": [
    {
      "Id": "delete-old-versions",
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "STANDARD_IA"
        }
      ],
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      },
      "Status": "Enabled"
    }
  ]
}
```

## Replication (CRR and SRR)

Cross-Region Replication (CRR) for disaster recovery; Same-Region Replication (SRR) for backup.

### Setup CRR
```bash
# Create replication role
aws iam create-role --role-name s3-replication-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "s3.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policy
aws iam put-role-policy --role-name s3-replication-role \
  --policy-name s3-replication-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "s3:GetReplicationConfiguration",
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::source-bucket"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObjectVersionForReplication",
        "s3:GetObjectVersionAcl"
      ],
      "Resource": "arn:aws:s3:::source-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ReplicateObject",
        "s3:ReplicateDelete"
      ],
      "Resource": "arn:aws:s3:::dest-bucket/*"
    }]
  }'
```

### Replication Configuration
```json
{
  "Role": "arn:aws:iam::123456789012:role/s3-replication-role",
  "Rules": [
    {
      "Id": "replicate-all",
      "Filter": {"Prefix": ""},
      "Status": "Enabled",
      "Destination": {
        "Bucket": "arn:aws:s3:::dest-bucket",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": {"Minutes": 15}
        },
        "Metrics": {
          "Status": "Enabled",
          "EventThreshold": {"Minutes": 15}
        }
      }
    }
  ]
}
```

## Static Website Hosting

Host a static website directly from S3 with CloudFront.

### Enable Static Hosting
```bash
aws s3 website s3://my-website \
  --index-document index.html \
  --error-document error.html
```

### Bucket Policy for Public Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-website/*"
    }
  ]
}
```

### CloudFront Distribution (Better than bucket website endpoint)
```bash
aws cloudfront create-distribution --distribution-config '{
  "CallerReference": "unique-string",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "s3-origin",
        "DomainName": "my-website.s3.us-east-1.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    }
  },
  "Enabled": true
}'
```

## Presigned URLs

Generate temporary access links without exposing AWS credentials.

### Python Example
```python
import boto3
from datetime import datetime, timedelta

s3_client = boto3.client('s3')

# Generate presigned URL (valid for 1 hour)
url = s3_client.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': 'my-bucket',
        'Key': 'private/file.pdf'
    },
    ExpiresIn=3600  # 1 hour
)

print(url)
# https://my-bucket.s3.amazonaws.com/private/file.pdf?AWSAccessKeyId=...&Signature=...&Expires=...

# Presigned POST (for file uploads)
response = s3_client.generate_presigned_post(
    Bucket='my-bucket',
    Key='uploads/${filename}',
    ExpiresIn=3600
)

# Use in HTML form
print(f"""
<form method="POST" action="{response['url']}" enctype="multipart/form-data">
  {' '.join(f'<input type="hidden" name="{k}" value="{v}">' for k, v in response['fields'].items())}
  <input type="file" name="file" required>
  <input type="submit" value="Upload">
</form>
""")
```

### Node.js Example
```javascript
const AWS = require('aws-sdk');

const s3 = new AWS.S3();

// Get presigned URL
const url = s3.getSignedUrl('getObject', {
  Bucket: 'my-bucket',
  Key: 'file.pdf',
  Expires: 3600
});

// Put presigned URL (for upload)
const uploadUrl = s3.getSignedUrl('putObject', {
  Bucket: 'my-bucket',
  Key: 'uploads/file.zip',
  Expires: 3600,
  ContentType: 'application/zip'
});
```

## Event Triggers

Trigger Lambda, SNS, or SQS when objects are created/deleted/modified.

### Lambda Trigger
```bash
aws s3api put-bucket-notification-configuration \
  --bucket my-bucket \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [
      {
        "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:process-image",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {
            "FilterRules": [
              {"Name": "prefix", "Value": "uploads/"},
              {"Name": "suffix", "Value": ".jpg"}
            ]
          }
        }
      }
    ]
  }'
```

### Lambda Handler
```python
import json
import boto3
from urllib.parse import unquote_plus

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Event structure
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        event_name = record['eventName']  # s3:ObjectCreated:Put

        print(f"Processing {event_name} for {key} in {bucket}")

        # Process object
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()

        # Do work...

    return {'statusCode': 200}
```

### SNS/SQS Trigger
```bash
aws s3api put-bucket-notification-configuration \
  --bucket my-bucket \
  --notification-configuration '{
    "QueueConfigurations": [
      {
        "QueueArn": "arn:aws:sqs:us-east-1:123456789012:my-queue",
        "Events": ["s3:ObjectCreated:*"],
        "Filter": {
          "Key": {"FilterRules": [{"Name": "prefix", "Value": "events/"}]}
        }
      }
    ]
  }'
```

## Performance and Costs

### Multipart Upload
Large files upload faster with parallelization:

```python
import boto3

s3 = boto3.client('s3')

# Upload 100 MB file in 10 MB chunks
with open('large-file.zip', 'rb') as f:
    mpu = s3.create_multipart_upload(Bucket='my-bucket', Key='large-file.zip')

    parts = []
    for i in range(1, 11):
        chunk = f.read(10 * 1024 * 1024)  # 10 MB
        response = s3.upload_part(
            Bucket='my-bucket',
            Key='large-file.zip',
            PartNumber=i,
            UploadId=mpu['UploadId'],
            Body=chunk
        )
        parts.append({'ETag': response['ETag'], 'PartNumber': i})

    s3.complete_multipart_upload(
        Bucket='my-bucket',
        Key='large-file.zip',
        UploadId=mpu['UploadId'],
        MultipartUpload={'Parts': parts}
    )
```

### Request Rate Optimization
S3 can handle 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD per prefix per second. If hitting limits, use multiple prefixes:
- `data/2024-01-01/file1.json` (prefix: `data/2024-01-01/`)
- `data/2024-01-02/file1.json` (prefix: `data/2024-01-02/`)

## Security Best Practices

1. **Enable versioning**: Protect against accidental deletion
2. **Enable MFA Delete**: Require MFA to permanently delete objects
3. **Use server-side encryption**: AES-256 (default) or KMS
4. **Block public access**: `BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`
5. **Enable logging**: CloudTrail for API calls, S3 Access Logs for HTTP requests
6. **Use presigned URLs**: Never expose bucket directly
7. **Enable versioning + lifecycle**: Automatic archive and deletion
