---
skill_name: aws-cloudfront-cdn
description: CloudFront CDN patterns for cache behaviors, origins, Lambda@Edge, WAF integration, and invalidations
category: Cloud & DevOps
version: 1.0.0
---

# AWS CloudFront CDN

## Distribution Setup

CloudFront caches content at edge locations worldwide.

### Create Distribution
```bash
aws cloudfront create-distribution --distribution-config '{
  "CallerReference": "unique-id-'$(date +%s)'",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-bucket",
        "DomainName": "my-bucket.s3.us-east-1.amazonaws.com",
        "S3OriginConfig": {}
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-bucket",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    }
  },
  "Enabled": true
}'
```

## Cache Behaviors

Define caching rules for different URL patterns.

### Multiple Origins with Path-Based Routing
```json
{
  "Origins": {
    "Quantity": 2,
    "Items": [
      {
        "Id": "S3-static",
        "DomainName": "my-bucket.s3.us-east-1.amazonaws.com"
      },
      {
        "Id": "API-backend",
        "DomainName": "api.example.com",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only"
        }
      }
    ]
  },
  "CacheBehaviors": [
    {
      "PathPattern": "/api/*",
      "TargetOriginId": "API-backend",
      "ViewerProtocolPolicy": "https-only",
      "CachePolicyId": "4135ea3d-c35d-46eb-81d7-reampleID00",
      "AllowedMethods": {
        "Quantity": 7,
        "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
      }
    },
    {
      "PathPattern": "/static/*",
      "TargetOriginId": "S3-static",
      "ViewerProtocolPolicy": "redirect-to-https",
      "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6"
    }
  ]
}
```

## Cache Policies

Control caching behavior without managing TTLs manually.

### Predefined Cache Policies
```bash
# Managed policies (use IDs instead of creating custom ones)
# CachingDisabled: 4135ea3d-c35d-46eb-81d7-reampleID00
# CachingOptimized: 658327ea-f89d-4fab-a63d-7e88639e58f6
# Elemental-MediaPackage: 08645691-4635-49c4-92cc-3ea3ffd3a8d6

aws cloudfront list-cache-policies
```

### Custom Cache Policy
```bash
aws cloudfront create-cache-policy --cache-policy-config '{
  "Name": "my-cache-policy",
  "Comment": "Cache for 1 hour, include headers",
  "DefaultTTL": 3600,
  "MaxTTL": 86400,
  "MinTTL": 0,
  "ParametersInCacheKeyAndForwardedToOrigin": {
    "EnableAcceptEncodingGzip": true,
    "EnableAcceptEncodingBrotli": true,
    "HeadersConfig": {
      "HeaderBehavior": "whitelist",
      "Headers": ["CloudFront-Is-Desktop-Viewer", "CloudFront-Is-Mobile-Viewer"]
    },
    "QueryStringsConfig": {
      "QueryStringBehavior": "whitelist",
      "QueryStrings": ["utm_source", "utm_campaign"]
    },
    "CookiesConfig": {
      "CookieBehavior": "whitelist",
      "Cookies": ["session_id"]
    }
  }
}'
```

## Origin Access Identity (OAI)

Restrict S3 bucket access to CloudFront only.

```bash
# Create OAI
oai=$(aws cloudfront create-cloud-front-origin-access-identity \
  --cloud-front-origin-access-identity-config \
  CallerReference=unique-ref-$(date +%s) \
  --query 'CloudFrontOriginAccessIdentity.Id' \
  --output text)

# Update distribution to use OAI
aws cloudfront update-distribution --distribution-config '{
  "Origins": {
    "Items": [
      {
        "S3OriginConfig": {
          "OriginAccessIdentity": "origin-access-identity/cloudfront/'$oai'"
        }
      }
    ]
  }
}'

# Update bucket policy to allow OAI only
aws s3api put-bucket-policy --bucket my-bucket --policy '{
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity '$oai'"
    },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*"
  }]
}'
```

## Lambda@Edge

Run Lambda at edge locations before content is served.

### CloudFront Event Types
- **Viewer Request**: Before CloudFront cache lookup
- **Viewer Response**: Before returning to viewer
- **Origin Request**: Before forwarding to origin
- **Origin Response**: After receiving from origin

### Lambda@Edge Function
```python
def lambda_handler(event, context):
    request = event['Records'][0]['cf']['request']

    # Add security headers in response
    if 'response' in event['Records'][0]['cf']:
        response = event['Records'][0]['cf']['response']
        response['headers']['strict-transport-security'] = [{
            'key': 'Strict-Transport-Security',
            'value': 'max-age=31536000; includeSubDomains'
        }]
        response['headers']['x-content-type-options'] = [{
            'key': 'X-Content-Type-Options',
            'value': 'nosniff'
        }]
        return response

    # Modify request — add custom header
    request['headers']['x-origin-verify'] = [{
        'key': 'X-Origin-Verify',
        'value': 'cloudfront-edge'
    }]
    return request
```

### Deploy Lambda@Edge
```bash
# Package function
zip function.zip lambda_function.py

# Create IAM role for Lambda@Edge (must be in us-east-1)
role_arn=$(aws iam create-role \
  --role-name lambda-edge-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "Service": ["lambda.amazonaws.com", "edgelambda.amazonaws.com"]
      },
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

# Create function in us-east-1
version=$(aws lambda create-function \
  --region us-east-1 \
  --function-name cloudfront-security-headers \
  --runtime python3.11 \
  --role $role_arn \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --query 'Version' \
  --output text)

# Publish version (required for Lambda@Edge)
published=$(aws lambda publish-version \
  --region us-east-1 \
  --function-name cloudfront-security-headers \
  --query 'FunctionArn' \
  --output text)

# Attach to CloudFront distribution
aws cloudfront update-distribution --id E1234ABCD \
  --distribution-config '{
    "DefaultCacheBehavior": {
      "LambdaFunctionAssociations": {
        "Quantity": 1,
        "Items": [{
          "EventType": "viewer-response",
          "LambdaFunctionARN": "'$published'"
        }]
      }
    }
  }'
```

### Lambda@Edge Use Cases
- **Security headers**: Add HSTS, CSP, X-Frame-Options
- **Authentication**: Validate credentials at edge
- **Geoblocking**: Reject requests from certain countries
- **A/B testing**: Route requests to different origins
- **Image optimization**: Resize images based on device

## Invalidation

Update cached content without waiting for TTL expiration.

### Invalidate by Path
```bash
aws cloudfront create-invalidation \
  --distribution-id E1234ABCD \
  --paths "/index.html" "/api/*" "/static/*"

# Wildcard invalidation (invalidates everything)
aws cloudfront create-invalidation \
  --distribution-id E1234ABCD \
  --paths "/*"
```

### Monitor Invalidation Status
```bash
# Check status
aws cloudfront get-invalidation \
  --distribution-id E1234ABCD \
  --id I1234567890ABC

# Cost: $0.005 per invalidation path (first 3000/month free)
```

## WAF Integration

Protect against common web exploits.

```bash
# Create WAF Web ACL
acl=$(aws wafv2 create-web-acl \
  --name cloudfront-waf \
  --scope CLOUDFRONT \
  --default-action Block={} \
  --rules '[
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 0,
      "OverrideAction": {"None": {}},
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "CommonRuleSet"
      }
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=waf-metrics \
  --query 'Summary.ARN' \
  --output text)

# Associate with CloudFront
aws cloudfront update-distribution --id E1234ABCD \
  --distribution-config '{
    "WebACLId": "'$acl'"
  }'
```

## Performance Optimization

### Enable Compression
```json
{
  "CacheBehaviors": [
    {
      "Compress": true,
      "ParametersInCacheKeyAndForwardedToOrigin": {
        "EnableAcceptEncodingGzip": true,
        "EnableAcceptEncodingBrotli": true
      }
    }
  ]
}
```

### HTTP/2 and Keep-Alive
CloudFront automatically uses HTTP/2 and persistent connections (enabled by default).

### Cache Hit Ratio Optimization
```bash
# Monitor cache hit ratio
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name CacheHitRate \
  --dimensions Name=DistributionId,Value=E1234ABCD \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

Target: >90% for static content, >50% for dynamic content.

## Best Practices

1. **Use OAI**: Restrict S3 access to CloudFront only
2. **Enable compression**: Reduce bandwidth 40-60%
3. **Cache long-lived assets**: Versioned CSS/JS with far-future expires
4. **Invalidate selectively**: Use path patterns, avoid wildcards
5. **Monitor metrics**: Cache hit ratio, error rate, requests
6. **Lambda@Edge sparingly**: Small functions, sub-100ms execution
7. **Security headers**: Add via Lambda@Edge or origin
8. **HTTPS only**: Redirect HTTP to HTTPS, use HSTS
