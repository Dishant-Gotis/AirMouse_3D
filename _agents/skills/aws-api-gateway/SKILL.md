---
skill_name: aws-api-gateway
description: API Gateway patterns for REST vs HTTP APIs, authorizers, throttling, caching, and request transforms
category: Cloud & DevOps
version: 1.0.0
---

# AWS API Gateway

## REST API vs HTTP API

### REST API (Feature-rich, higher latency)
- Full request/response transformations
- Request validators
- Multiple integrations
- More expensive

### HTTP API (Fast, cost-effective)
- 60% cheaper than REST API
- Lower latency (~40ms vs 100ms)
- Simpler integrations
- OpenAPI 3.0 support

**Choose HTTP API** for most new APIs unless you need specialized REST features.

## HTTP API Creation

```bash
# Create HTTP API
api=$(aws apigatewayv2 create-api \
  --name my-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:123456789012:function:my-function \
  --query 'ApiId' \
  --output text)

# Create stage
aws apigatewayv2 create-stage \
  --api-id $api \
  --stage-name prod \
  --auto-deploy

# Get API endpoint
endpoint=$(aws apigatewayv2 get-api \
  --api-id $api \
  --query 'ApiEndpoint' \
  --output text)

echo "API URL: https://$endpoint"
```

## REST API with Lambda Integration

```bash
# Create REST API
rest_api=$(aws apigateway create-rest-api \
  --name order-api \
  --description "Order management API" \
  --query 'id' \
  --output text)

# Get root resource
root_id=$(aws apigateway get-resources \
  --rest-api-id $rest_api \
  --query 'items[0].id' \
  --output text)

# Create /orders resource
orders=$(aws apigateway create-resource \
  --rest-api-id $rest_api \
  --parent-id $root_id \
  --path-part orders \
  --query 'id' \
  --output text)

# Create GET /orders method
aws apigateway put-method \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method GET \
  --authorization-type NONE

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:get-orders/invocations

# Create deployment
deployment=$(aws apigateway create-deployment \
  --rest-api-id $rest_api \
  --stage-name prod \
  --query 'id' \
  --output text)

echo "API URL: https://$rest_api.execute-api.us-east-1.amazonaws.com/prod"
```

## Lambda Authorizers

Control API access with custom logic.

### Lambda Authorizer Function
```python
import json
import jwt
import os

def lambda_handler(event, context):
    # Get token from Authorization header
    token = event['authorizationToken']

    try:
        # Verify JWT token
        payload = jwt.decode(
            token,
            os.environ['JWT_SECRET'],
            algorithms=['HS256']
        )

        # Build policy
        policy = {
            'principalId': payload['sub'],
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Allow',
                    'Resource': event['methodArn']
                }]
            },
            'context': {
                'userId': payload['sub'],
                'email': payload['email']
            }
        }

        return policy

    except jwt.InvalidTokenError:
        raise Exception('Unauthorized')
```

### Attach Authorizer to API
```bash
# Create authorizer
authorizer=$(aws apigateway create-authorizer \
  --rest-api-id $rest_api \
  --name jwt-authorizer \
  --type TOKEN \
  --authorizer-uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:jwt-authorizer/invocations \
  --identity-source method.request.header.Authorization \
  --authorizer-result-ttl-in-seconds 300 \
  --query 'id' \
  --output text)

# Apply authorizer to method
aws apigateway put-method \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method GET \
  --authorization-type CUSTOM \
  --authorizer-id $authorizer
```

## Request Validation

Validate requests before forwarding to Lambda.

```bash
# Create request validator
validator=$(aws apigateway create-request-validator \
  --rest-api-id $rest_api \
  --name request-validator \
  --validate-request-body \
  --validate-request-parameters \
  --query 'id' \
  --output text)

# Create method with validator
aws apigateway put-method \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method POST \
  --authorization-type AWS_IAM \
  --request-validator-id $validator
```

## Throttling and Rate Limiting

Protect API from abuse.

```bash
# Create usage plan
usage=$(aws apigateway create-usage-plan \
  --name standard-plan \
  --description "Standard tier rate limit" \
  --throttle-settings burstLimit=5000,rateLimit=2000 \
  --query 'id' \
  --output text)

# Create API key
api_key=$(aws apigateway create-api-key \
  --name client-key \
  --enabled \
  --query 'id' \
  --output text)

# Add API key to usage plan
aws apigateway create-usage-plan-key \
  --usage-plan-id $usage \
  --key-id $api_key \
  --key-type API_KEY

# Require API key for method
aws apigateway put-method \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method GET \
  --authorization-type NONE \
  --api-key-required
```

**Throttling**: Burst limit (5000 requests at once), Rate limit (2000 sustained).

## Caching

Cache responses to reduce backend load.

```bash
# Create cache cluster
aws apigateway create-stage \
  --rest-api-id $rest_api \
  --stage-name prod \
  --cache-cluster-enabled \
  --cache-cluster-size small  # Options: 0.5, 1.6, 6.1, 13.5, 28.4, 58.2, 118.0, 237.0

# Enable method caching
aws apigateway put-method-response \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method GET \
  --status-code 200 \
  --response-models application/json=Empty

aws apigateway put-integration-response \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method GET \
  --status-code 200 \
  --cache-key-parameters method.request.querystring.limit \
  --cache-namespace orders-cache
```

## Request/Response Transformation

Transform requests before Lambda and responses before client.

### Request Mapping Template
```bash
aws apigateway put-integration \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method GET \
  --type AWS_PROXY \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:get-orders/invocations \
  --request-templates '{
    "application/json": {
      "body": {
        "limit": "$input.params(\"limit\")",
        "offset": "$input.params(\"offset\")",
        "sort": "$input.params(\"sort\")"
      }
    }
  }'
```

### Response Mapping Template
```bash
aws apigateway put-integration-response \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method GET \
  --status-code 200 \
  --response-templates '{
    "application/json": "{\"orders\": $input.path(\"$.Items\"), \"count\": #set($c=$input.path(\"$.Items\").size())$c}"
  }'
```

## CORS Configuration

Enable cross-origin requests.

```bash
# Create OPTIONS method
aws apigateway put-method \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method OPTIONS \
  --authorization-type NONE

# Add CORS integration
aws apigateway put-integration \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method OPTIONS \
  --type MOCK

# Add CORS headers
aws apigateway put-method-response \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters \
    method.response.header.Access-Control-Allow-Headers=true \
    method.response.header.Access-Control-Allow-Methods=true \
    method.response.header.Access-Control-Allow-Origin=true

aws apigateway put-integration-response \
  --rest-api-id $rest_api \
  --resource-id $orders \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters \
    method.response.header.Access-Control-Allow-Headers="'Content-Type,X-Amz-Date,Authorization,X-Api-Key'" \
    method.response.header.Access-Control-Allow-Methods="'GET,POST,PUT,DELETE'" \
    method.response.header.Access-Control-Allow-Origin="'*'"
```

## Monitoring and Logging

```bash
# Enable CloudWatch logs
aws apigateway update-stage \
  --rest-api-id $rest_api \
  --stage-name prod \
  --logging-level INFO \
  --metrics-enabled

# Create log role
log_role=$(aws iam create-role \
  --role-name api-gateway-logs \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "apigateway.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

aws iam put-role-policy \
  --role-name api-gateway-logs \
  --policy-name CloudWatchLogs \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/api-gateway/*"
    }]
  }'
```

## Best Practices

1. **Use HTTP API**: Faster, cheaper, sufficient for most use cases
2. **API key + Usage Plan**: Implement rate limiting
3. **Lambda authorizers**: Centralize auth logic
4. **Request validators**: Validate schema before Lambda
5. **Caching**: Reduce backend load with cache clusters
6. **CORS**: Properly configure for browser clients
7. **Logging**: CloudWatch Logs for debugging
8. **WAF**: Attach to API Gateway for DDoS protection
9. **Versioning**: Use stages (dev, test, prod)
10. **Monitoring**: CloudWatch metrics for latency, errors
