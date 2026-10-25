---
skill_name: aws-sam-patterns
description: AWS SAM template patterns, local testing, layers, pipeline integration
category: Cloud & DevOps
version: 1.0.0
---

# AWS Serverless Application Model (SAM) Patterns

## Basic SAM Template

Define serverless applications with CloudFormation.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Description: Serverless API application

Globals:
  Function:
    Timeout: 30
    Runtime: python3.11
    Environment:
      Variables:
        TABLE_NAME: !Ref UsersTable
        ENVIRONMENT: !Ref Environment

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - staging
      - prod

Conditions:
  IsProd: !Equals [!Ref Environment, 'prod']

Resources:
  # API Gateway
  ServerlessApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      TracingEnabled: true
      MethodSettings:
        - ResourcePath: '/*'
          HttpMethod: '*'
          LoggingLevel: INFO
          DataTraceEnabled: true
          MetricsEnabled: true
      DefinitionBody:
        swagger: '2.0'
        info:
          title: !Sub 'API ${Environment}'
        paths:
          /users/{id}:
            get:
              x-amazon-apigateway-integration:
                httpMethod: POST
                type: aws_proxy
                uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${GetUserFunction.Arn}/invocations'

  # Lambda Functions
  GetUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/handlers/users/
      Handler: get.lambda_handler
      Runtime: python3.11
      Events:
        GetUserAPI:
          Type: Api
          Properties:
            RestApiId: !Ref ServerlessApi
            Path: /users/{id}
            Method: get
      Environment:
        Variables:
          FUNCTION_NAME: GetUser
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable

  CreateUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/handlers/users/
      Handler: create.lambda_handler
      Runtime: python3.11
      Events:
        CreateUserAPI:
          Type: Api
          Properties:
            RestApiId: !Ref ServerlessApi
            Path: /users
            Method: post
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable

  ProcessEventsFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/handlers/events/
      Handler: process.lambda_handler
      Runtime: python3.11
      Events:
        SQSEvent:
          Type: SQS
          Properties:
            Queue: !GetAtt EventQueue.Arn
            BatchSize: 10
            BatchWindow: 30
      Policies:
        - SQSPollerPolicy:
            QueueName: !GetAtt EventQueue.QueueName

  ScheduledTaskFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/handlers/tasks/
      Handler: schedule.lambda_handler
      Runtime: python3.11
      Events:
        ScheduleEvent:
          Type: Schedule
          Properties:
            Schedule: 'cron(0 2 * * ? *)'
            Enabled: !If [IsProd, true, false]

  # DynamoDB Table
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'users-${Environment}'
      AttributeDefinitions:
        - AttributeName: userId
          AttributeType: S
        - AttributeName: createdAt
          AttributeType: N
      KeySchema:
        - AttributeName: userId
          KeyType: HASH
        - AttributeName: createdAt
          KeyType: RANGE
      BillingMode: PAY_PER_REQUEST
      StreamSpecification:
        StreamViewType: NEW_AND_OLD_IMAGES
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: !If [IsProd, true, false]

  # SQS Queue
  EventQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub 'events-${Environment}'
      VisibilityTimeout: 300
      MessageRetentionPeriod: 1209600

  DeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub 'events-dlq-${Environment}'

  # CloudWatch Log Group
  ApiLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/apigateway/api-${Environment}'
      RetentionInDays: !If [IsProd, 30, 7]

Outputs:
  ApiEndpoint:
    Description: API Gateway endpoint
    Value: !Sub 'https://${ServerlessApi}.execute-api.${AWS::Region}.amazonaws.com/${Environment}'

  UsersTableName:
    Description: Users table name
    Value: !Ref UsersTable

  EventQueueUrl:
    Description: SQS Queue URL
    Value: !Ref EventQueue
```

## Lambda Layers in SAM

Package shared dependencies.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.11
    Layers:
      - !Ref CommonLibrariesLayer
      - !Ref DatabaseModelsLayer

Resources:
  CommonLibrariesLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub 'common-libraries-${AWS::StackName}'
      Description: Common utilities and decorators
      ContentUri: layers/common/
      CompatibleRuntimes:
        - python3.11
      RetentionPolicy: Delete

  DatabaseModelsLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub 'database-models-${AWS::StackName}'
      Description: Database models and schemas
      ContentUri: layers/models/
      CompatibleRuntimes:
        - python3.11

  ApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/handlers/api/
      Handler: handler.lambda_handler
      Runtime: python3.11
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /data
            Method: get
```

## Local Testing with SAM

Test SAM applications locally.

```bash
# Start local API and DynamoDB
sam local start-api --template template.yaml

# Start only DynamoDB
sam local start-dynamodb

# Test specific function
sam local invoke GetUserFunction --event events/get-user.json

# Debug mode
sam local start-api --debug --debug-port 5858
```

**Event file for testing**:

```json
// events/get-user.json
{
  "requestContext": {
    "accountId": "123456789012",
    "apiId": "test",
    "stage": "test"
  },
  "headers": {
    "Accept": "application/json",
    "Host": "localhost:3000"
  },
  "pathParameters": {
    "id": "user-123"
  },
  "httpMethod": "GET",
  "path": "/users/user-123"
}
```

## SAM Pipeline Integration

Deploy with SAM in CI/CD pipelines.

```yaml
# Makefile
.PHONY: build test deploy

build:
	sam build

test:
	sam local start-api &
	pytest tests/ -v
	pkill -f "sam local"

deploy-staging:
	sam deploy --stack-name myapp-staging --parameter-overrides Environment=staging

deploy-prod:
	sam deploy --stack-name myapp-prod --parameter-overrides Environment=prod --confirm-changeset
```

**GitHub Actions pipeline**:

```yaml
name: Deploy SAM

on:
  push:
    branches: [main, develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v3

      - uses: aws-actions/setup-sam@v2

      - uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::ACCOUNT:role/GithubRole
          aws-region: us-east-1

      - name: Build
        run: sam build

      - name: Test
        run: |
          sam local start-api --port 3000 &
          sleep 3
          pytest tests/ -v

      - name: Deploy
        run: |
          sam deploy \
            --stack-name myapp-${GITHUB_REF#refs/heads/} \
            --no-confirm-changeset \
            --parameter-overrides Environment=${GITHUB_REF#refs/heads/}
```

## Structured Logging

Use AWS Lambda Powertools for JSON logging.

```python
# requirements.txt
aws-lambda-powertools==2.0.0

# handler.py
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()
metrics = Metrics()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_cold_start_metric
def lambda_handler(event, context: LambdaContext):
    logger.info(f"Processing request: {event['requestContext']['requestId']}")

    # Trace service calls
    with tracer.capture_subsegment("fetch_data"):
        data = fetch_from_database()

    # Add metrics
    metrics.add_metadata("request_id", event['requestContext']['requestId'])
    metrics.add_metric(name="data_processed", unit="Count", value=len(data))

    logger.info("Request processed successfully", extra={"data_count": len(data)})
    return {
        'statusCode': 200,
        'body': json.dumps(data)
    }
```

## Monitoring and Alarms

Configure CloudWatch alarms for functions.

```yaml
Resources:
  ApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: handler.lambda_handler
      Runtime: python3.11

  FunctionErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub 'api-function-errors-${Environment}'
      MetricName: Errors
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 5
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: FunctionName
          Value: !Ref ApiFunction
      AlarmActions:
        - !Ref AlertTopic

  FunctionThrottleAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub 'api-function-throttles-${Environment}'
      MetricName: Throttles
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 60
      Threshold: 1
      ComparisonOperator: GreaterThanOrEqualToThreshold
      Dimensions:
        - Name: FunctionName
          Value: !Ref ApiFunction
      AlarmActions:
        - !Ref AlertTopic

  AlertTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub 'api-alerts-${Environment}'
      Subscription:
        - Endpoint: alerts@example.com
          Protocol: email
```

## Environment Validation

Use custom validation resources.

```yaml
Resources:
  ValidateEnvironmentFunction:
    Type: AWS::Lambda::Function
    Properties:
      Runtime: python3.11
      Handler: index.handler
      Code:
        ZipFile: |
          import cfnresponse
          def handler(event, context):
            environment = event['ResourceProperties']['Environment']
            if environment not in ['dev', 'staging', 'prod']:
              cfnresponse.send(event, context, cfnresponse.FAILED, {})
            else:
              cfnresponse.send(event, context, cfnresponse.SUCCESS, {})

  EnvironmentValidation:
    Type: Custom::EnvironmentValidation
    Properties:
      ServiceToken: !GetAtt ValidateEnvironmentFunction.Arn
      Environment: !Ref Environment
```
