---
skill_name: aws-lambda-patterns
description: AWS Lambda patterns for cold starts, concurrency, error handling, layers, VPC config, and power tuning
category: Cloud & DevOps
version: 1.0.0
---

# AWS Lambda Patterns

## Cold Start Optimization

Cold starts are the biggest Lambda performance killer. A Lambda function takes 5-15 seconds on first invocation if it hasn't run in a while. Here's how to minimize them:

### Provisioned Concurrency
Reserve capacity to eliminate cold starts for critical functions:

```json
{
  "ProvisionedConcurrentExecutions": 10
}
```

**Cost vs. benefit**: At `$0.015/hour per provisioned unit`, 10 reserved executions cost ~$130/month. Only use for APIs with predictable traffic.

### Lambda@Edge and CloudFront
Pre-warm functions by integrating with CloudFront. CloudFront invokes functions on edge locations, maintaining warm connections.

### Minimal Dependencies
Package only what you need. Every MB adds startup time.

```bash
# Bad: 125 MB zip with unused packages
zip -r lambda.zip . --exclude "node_modules/aws-sdk/*"

# Good: Prune devDependencies
npm prune --production
zip -r lambda.zip .
```

### Java/Python Startup Tips
- **Java**: Use GraalVM native-image to reduce heap size and startup time from 2+ seconds to <500ms
- **Python**: Avoid importing heavy libraries at module level; import inside handlers

```python
# Bad: loads model on cold start
import tensorflow as tf
model = tf.keras.models.load_model('model.h5')

def lambda_handler(event, context):
    return model.predict(...)

# Good: lazy load on first invocation
model = None

def lambda_handler(event, context):
    global model
    if model is None:
        import tensorflow as tf
        model = tf.keras.models.load_model('model.h5')
    return model.predict(...)
```

## Lambda Layers

Layers separate code from dependencies, reduce package size, and enable reuse.

### Layer Structure
```
layer/
  nodejs/
    node_modules/  (node_modules go here, NOT in a src/ subdir)
    package.json
  python/
    lib/python3.11/site-packages/  (for Python)
```

### Creating a Layer
```bash
mkdir -p layer/nodejs
cd layer/nodejs
npm install --production aws-sdk axios
cd ..
zip -r ../my-layer.zip .

# Upload
aws lambda publish-layer-version \
  --layer-name my-layer \
  --zip-file fileb://../my-layer.zip \
  --compatible-runtimes nodejs18.x
```

### Using Layers
```bash
aws lambda create-function \
  --function-name my-func \
  --layers arn:aws:lambda:us-east-1:123456789012:layer:my-layer:1 \
  --zip-file fileb://function.zip
```

**Gotcha**: Layers add to cold start time. Test layer size; AWS allows max 250 MB total (function + layers).

## Concurrency Management

Lambda manages concurrency at the account level (default 1000 concurrent executions).

### Reserved Concurrency
Guarantee capacity for critical functions and prevent throttling:

```bash
aws lambda put-function-concurrency \
  --function-name my-func \
  --reserved-concurrent-executions 100
```

### Provisioned Concurrency
Keep functions warm and initialized:

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name my-func \
  --provisioned-concurrent-executions 50 \
  --qualifier LIVE
```

### Graceful Degradation
When hitting concurrency limits, Lambda queues requests up to 6 hours then drops them. Return meaningful errors:

```python
import json

def lambda_handler(event, context):
    try:
        # If this gets invoked, concurrency is available
        result = expensive_operation()
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        # Log and fail gracefully
        print(f"Error: {e}")
        return {
            'statusCode': 503,
            'body': json.dumps({'error': 'Service temporarily unavailable'})
        }
```

## Error Handling and Retries

### Dead Letter Queues (DLQ)
Async invocations (events, SNS, SQS) can fail. Capture failures:

```bash
aws lambda put-function-event-invoke-config \
  --function-name my-func \
  --maximum-event-age 3600 \
  --maximum-retry-attempts 2 \
  --on-failure '{"Type":"SQS","Destination":"arn:aws:sqs:us-east-1:123456789012:dlq"}'
```

### Retry Decorator
```python
import time
import json

def retry(max_attempts=3, delay=1, backoff=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    print(f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator

@retry(max_attempts=3, delay=1, backoff=2)
def call_unreliable_api():
    # API call that might fail
    pass
```

## VPC Configuration

Lambda functions in a VPC lose access to the internet and incur ENI attachment overhead. Use VPC only when necessary.

### VPC Setup
```bash
aws lambda update-function-configuration \
  --function-name my-func \
  --vpc-config SubnetIds=subnet-12345,subnet-67890 \
    SecurityGroupIds=sg-12345
```

**Cold start impact**: VPC attachment adds 10+ seconds. Consider NAT Gateway instead if you only need to call internet services.

### RDS Proxy
Instead of managing connections in Lambda, use RDS Proxy:

```python
import pymysql
import os

def lambda_handler(event, context):
    connection = pymysql.connect(
        host=os.environ['DB_PROXY_ENDPOINT'],  # RDS Proxy endpoint
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASS'],
        database='mydb'
    )
    # Connection pooling handled by RDS Proxy
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    connection.close()
    return result
```

## Power Tuning

Lambda is billed by GB-seconds. More memory = faster execution = lower total cost (up to a point).

### AWS Lambda Power Tuning Tool
```bash
npm install -g aws-lambda-power-tuning

# Test function across 11 different memory configurations
aws-lambda-power-tuning \
  --function-name my-func \
  --payload '{"key":"value"}' \
  --num-runs 100 \
  --step 1024 \
  --max 10240
```

### Optimal Configuration
- **CPU-bound**: Max out memory (usually 3008 MB) — pay more per invocation but finish faster
- **Network I/O**: 1024-2048 MB is usually sweet spot
- **Cost-optimized**: Use AWS Lambda Power Tuning reports to find inflection point

### Example Result Interpretation
- 512 MB: 5,000 ms, $0.00001041/invocation
- 1024 MB: 1,500 ms, $0.00001284/invocation
- 3008 MB: 800 ms, $0.00002688/invocation

If 3008 MB is 2.6x the cost but 6.25x faster, use 3008 MB.

## Environment Variables and Secrets

### Using Environment Variables
```python
import os
import json

def lambda_handler(event, context):
    api_key = os.environ.get('API_KEY')
    environment = os.environ.get('ENVIRONMENT', 'dev')

    return {
        'statusCode': 200,
        'body': json.dumps({'env': environment})
    }
```

### Secrets Manager vs. Environment Variables
- **Environment Variables**: Non-sensitive config (database name, log level)
- **Secrets Manager**: Sensitive values (passwords, API keys) — enable encryption at rest, automatic rotation

```python
import boto3
import json

secrets_client = boto3.client('secretsmanager')

def get_secret(secret_name):
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

def lambda_handler(event, context):
    secret = get_secret('prod/db/password')
    # Use secret
    pass
```

## Timeout and Memory Guidelines

- **Default timeout**: 3 seconds (set to max 15 minutes)
- **Memory range**: 128 MB to 10,240 MB
- **Disk space**: 512 MB `/tmp` (ephemeral, not persistent)

Set conservatively:
```bash
aws lambda update-function-configuration \
  --function-name my-func \
  --timeout 60 \
  --memory-size 512
```

## Best Practices Summary

1. **Minimize cold starts**: Use Provisioned Concurrency for critical functions
2. **Package light**: Exclude unused dependencies and `node_modules/aws-sdk`
3. **Reserve capacity**: Set reserved concurrency to prevent throttling
4. **Use DLQs**: Capture async failures for debugging
5. **Power tune**: Test across memory configs to optimize cost
6. **Encrypt secrets**: Store sensitive data in Secrets Manager
7. **Monitor**: CloudWatch Insights for duration, errors, throttles
