---
skill_name: aws-dynamodb-patterns
description: DynamoDB design patterns for single-table design, GSIs, LSIs, streams, TTL, transactions, and capacity planning
category: Cloud & DevOps
version: 1.0.0
---

# AWS DynamoDB Patterns

## Single-Table Design

Multiple entity types in one table using sort keys to distinguish them.

### Schema Design
```
PK (Partition Key): Entity ID
SK (Sort Key): Entity Type#Timestamp or Entity Type#ID
```

### Example: SaaS Application
```python
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SaaS')

# User entity
user_id = str(uuid.uuid4())
table.put_item(Item={
    'PK': f'USER#{user_id}',
    'SK': f'PROFILE#{datetime.now().isoformat()}',
    'email': 'user@example.com',
    'name': 'John Doe',
    'created_at': datetime.now().isoformat()
})

# Tenant entity
tenant_id = str(uuid.uuid4())
table.put_item(Item={
    'PK': f'TENANT#{tenant_id}',
    'SK': f'CONFIG#{datetime.now().isoformat()}',
    'name': 'Acme Corp',
    'plan': 'pro',
    'billing_email': 'billing@acme.com'
})

# Organization membership
table.put_item(Item={
    'PK': f'TENANT#{tenant_id}',
    'SK': f'MEMBER#{user_id}',
    'role': 'admin',
    'added_at': datetime.now().isoformat()
})

# Query all members of a tenant
response = table.query(
    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues={
        ':pk': f'TENANT#{tenant_id}',
        ':sk': 'MEMBER#'
    }
)

print([item for item in response['Items']])
```

**Advantages**:
- Single table = one set of provisioned capacity
- Fewer tables to manage
- Efficient queries across entity types

**Gotcha**: Can't query across different PK values efficiently. Use GSI for that.

## Global Secondary Indexes (GSI)

Create alternate indexes for flexible queries.

### GSI with Sparse Indexes
```python
# Table definition (in CloudFormation or Terraform)
table_config = {
    'AttributeDefinitions': [
        {'AttributeName': 'PK', 'AttributeType': 'S'},
        {'AttributeName': 'SK', 'AttributeType': 'S'},
        {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
        {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
    ],
    'KeySchema': [
        {'AttributeName': 'PK', 'KeyType': 'HASH'},
        {'AttributeName': 'SK', 'KeyType': 'RANGE'}
    ],
    'GlobalSecondaryIndexes': [
        {
            'IndexName': 'GSI1',
            'KeySchema': [
                {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'ProvisionedThroughput': {
                'ReadCapacityUnits': 100,
                'WriteCapacityUnits': 100
            }
        }
    ]
}

# Populate items with GSI attributes (sparse index)
table.put_item(Item={
    'PK': 'USER#123',
    'SK': 'PROFILE#2024',
    'email': 'user@example.com',
    'GSI1PK': f'EMAIL#{email}',  # Only users have this
    'GSI1SK': 'ACTIVE',
})

# Query by email (GSI1)
response = table.query(
    IndexName='GSI1',
    KeyConditionExpression='GSI1PK = :pk',
    ExpressionAttributeValues={':pk': f'EMAIL#{email}'}
)
```

**Sparse Index**: Only include GSI1PK/SK when needed, reducing index size and cost.

## Local Secondary Indexes (LSI)

10 GB size limit, same partition key as base table. Use for range key flexibility.

```python
# LSI definition
{
    'LocalSecondaryIndexes': [
        {
            'IndexName': 'LSI1',
            'KeySchema': [
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'LSI1SK', 'AttributeType': 'S', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }
    ]
}

# Add LSI attributes to items
table.put_item(Item={
    'PK': 'TENANT#123',
    'SK': 'INVOICE#2024-01-01',
    'LSI1SK': datetime.now().isoformat(),  # Alternate sort key
    'amount': 1000
})

# Query with LSI sort key
response = table.query(
    IndexName='LSI1',
    KeyConditionExpression='PK = :pk AND LSI1SK BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':pk': 'TENANT#123',
        ':start': '2024-01-01',
        ':end': '2024-12-31'
    }
)
```

## DynamoDB Streams

Capture item changes in real-time.

### Enable Streams
```bash
aws dynamodb update-table \
  --table-name my-table \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

**StreamViewType Options**:
- `KEYS_ONLY`: Only key attributes
- `NEW_IMAGE`: Item after update
- `OLD_IMAGE`: Item before update
- `NEW_AND_OLD_IMAGES`: Both (most comprehensive)

### Lambda Stream Handler
```python
import json
import boto3

sqs = boto3.client('sqs')

def lambda_handler(event, context):
    for record in event['Records']:
        event_id = record['eventID']
        event_name = record['eventName']  # INSERT, MODIFY, REMOVE
        dynamodb = record['dynamodb']

        if event_name == 'INSERT':
            item = dynamodb['NewImage']
            print(f"New item: {item}")
        elif event_name == 'MODIFY':
            new_image = dynamodb['NewImage']
            old_image = dynamodb['OldImage']
            print(f"Changed from {old_image} to {new_image}")
        elif event_name == 'REMOVE':
            old_image = dynamodb['OldImage']
            print(f"Deleted: {old_image}")

        # Send to SQS for downstream processing
        sqs.send_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789012/events',
            MessageBody=json.dumps({
                'eventName': event_name,
                'item': item if event_name != 'REMOVE' else old_image
            })
        )

    return {'statusCode': 200}
```

## TTL (Time To Live)

Automatically delete items after expiration.

### Setup TTL
```python
# Enable TTL on expiration_time attribute
dynamodb.meta.client.update_time_to_live(
    TableName='my-table',
    TimeToLiveSpecification={
        'AttributeName': 'expiration_time',
        'Enabled': True
    }
)

# Add expiration timestamp (Unix epoch)
from time import time

table.put_item(Item={
    'PK': 'SESSION#123',
    'SK': 'DATA',
    'user_id': 'user123',
    'expiration_time': int(time()) + 3600  # Expire in 1 hour
})
```

**Use cases**: Sessions, temporary tokens, caches, rate-limit counters.

## Transactions

ACID transactions for multiple items.

### TransactWriteItems
```python
response = dynamodb.batch_write_item(
    RequestItems={
        'my-table': [
            {
                'Put': {
                    'Item': {
                        'PK': 'ORDER#123',
                        'SK': 'SUMMARY',
                        'user_id': 'user456',
                        'total': 99.99
                    }
                }
            },
            {
                'Update': {
                    'Key': {'PK': 'USER#user456', 'SK': 'PROFILE'},
                    'UpdateExpression': 'SET order_count = order_count + :inc',
                    'ExpressionAttributeValues': {':inc': 1}
                }
            }
        ]
    }
)
```

### TransactGetItems (Read)
```python
response = dynamodb.batch_get_item(
    RequestItems={
        'my-table': {
            'Keys': [
                {'PK': 'ORDER#123', 'SK': 'SUMMARY'},
                {'PK': 'ORDER#124', 'SK': 'SUMMARY'}
            ]
        }
    }
)

for item in response['Responses']['my-table']:
    print(item)
```

**Gotcha**: 25 items max per transaction, 4 MB max size.

## Capacity Planning

### Provisioned vs. On-Demand
**Provisioned** (RCU/WCU):
- 1 RCU = 1 strongly consistent read (4 KB) or 2 eventually consistent reads
- 1 WCU = 1 write (1 KB)
- Pay for reserved capacity regardless of usage

**On-Demand**:
- Pay per request
- No capacity planning needed
- 2.5x more expensive at scale

```bash
# Estimate capacity
# 100 read requests/sec of 4 KB each = 100 RCU
# 50 write requests/sec of 1 KB each = 50 WCU

aws dynamodb create-table \
  --table-name my-table \
  --attribute-definitions \
    AttributeName=PK,AttributeType=S \
    AttributeName=SK,AttributeType=S \
  --key-schema \
    AttributeName=PK,KeyType=HASH \
    AttributeName=SK,KeyType=RANGE \
  --billing-mode PROVISIONED \
  --provisioned-throughput \
    ReadCapacityUnits=100,WriteCapacityUnits=50
```

## Best Practices

1. **Single-table design**: Combine related entities in one table
2. **Sparse indexes**: Only add GSI attributes when needed
3. **Projection**: Use selective projections to reduce size
4. **Batch operations**: Group reads/writes to reduce API calls
5. **Conditional writes**: Use conditions to avoid race conditions
6. **TTL**: Clean up old data automatically
7. **Monitor**: CloudWatch for throttling, consumed capacity
8. **Hot partitions**: Distribute writes across partition keys
