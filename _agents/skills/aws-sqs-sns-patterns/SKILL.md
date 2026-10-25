---
skill_name: aws-sqs-sns-patterns
description: SQS and SNS patterns for queues, dead-letter queues, FIFO, fan-out, and message filtering
category: Cloud & DevOps
version: 1.0.0
---

# AWS SQS and SNS Patterns

## SQS Fundamentals

SQS is a managed message queue service for decoupling applications.

### Standard Queue
Guarantees at-least-once delivery but no ordering guarantee.

```bash
aws sqs create-queue \
  --queue-name my-queue \
  --attributes \
    VisibilityTimeout=30 \
    MessageRetentionPeriod=345600 \
    ReceiveMessageWaitTimeSeconds=20
```

### FIFO Queue
First-In-First-Out with exactly-once processing guarantee.

```bash
aws sqs create-queue \
  --queue-name my-queue.fifo \
  --attributes \
    FifoQueue=true \
    ContentBasedDeduplication=true \
    MessageRetentionPeriod=345600
```

FIFO queues require `MessageGroupId` for ordering:

```python
import boto3
import json

sqs = boto3.client('sqs')

# Send to FIFO queue
response = sqs.send_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789012/my-queue.fifo',
    MessageBody=json.dumps({'order_id': '12345', 'amount': 99.99}),
    MessageGroupId='customer-123',  # Required for FIFO
    MessageDeduplicationId='order-12345-attempt-1'  # Optional if ContentBasedDeduplication=true
)

print(response['MessageId'])
```

## Dead Letter Queues (DLQ)

Capture messages that fail processing after max retries.

### Setup DLQ
```bash
# Create DLQ
aws sqs create-queue --queue-name my-queue-dlq

# Get DLQ ARN
dlq_arn=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/my-queue-dlq \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

# Create main queue with DLQ reference
aws sqs create-queue \
  --queue-name my-queue \
  --attributes \
    RedrivePolicy="{\"deadLetterTargetArn\":\"$dlq_arn\",\"maxReceiveCount\":3}"
```

### Processing with DLQ
```python
import boto3
import json
import time

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/123456789012/my-queue'

while True:
    # Receive messages
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20  # Long polling
    )

    if 'Messages' not in response:
        continue

    for message in response['Messages']:
        try:
            body = json.loads(message['Body'])
            print(f"Processing: {body}")

            # Process message
            result = process_order(body)

            # Delete successful message
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
        except Exception as e:
            print(f"Error: {e}")
            # Don't delete — will retry up to maxReceiveCount times
            # After max retries, message goes to DLQ
```

## SNS Topics

Publish-subscribe for broadcast messaging.

### Create Topic and Subscribe
```bash
# Create topic
topic_arn=$(aws sns create-topic --name my-topic --query 'TopicArn' --output text)

# Subscribe SQS queue
aws sns subscribe \
  --topic-arn $topic_arn \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:123456789012:my-queue

# Subscribe Lambda
aws sns subscribe \
  --topic-arn $topic_arn \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:my-function

# Subscribe email
aws sns subscribe \
  --topic-arn $topic_arn \
  --protocol email \
  --notification-endpoint user@example.com
```

### Publishing Messages
```python
import boto3
import json

sns = boto3.client('sns')

# Publish to topic
response = sns.publish(
    TopicArn='arn:aws:sns:us-east-1:123456789012:my-topic',
    Subject='Order Confirmed',
    Message=json.dumps({
        'order_id': '12345',
        'customer': 'john@example.com',
        'total': 99.99
    })
)

print(f"Message ID: {response['MessageId']}")
```

## Message Filtering

Subscribe to only relevant messages.

### Filter Policy
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:123456789012:urgent-queue \
  --attributes '{"FilterPolicy":"{\"priority\":[\"urgent\",\"critical\"]}"}'
```

### Publishing with Attributes
```python
import boto3

sns = boto3.client('sns')

sns.publish(
    TopicArn='arn:aws:sns:us-east-1:123456789012:my-topic',
    Message='Order processed',
    MessageAttributes={
        'priority': {
            'DataType': 'String',
            'StringValue': 'urgent'
        },
        'customer_id': {
            'DataType': 'String',
            'StringValue': 'customer-123'
        },
        'amount': {
            'DataType': 'Number',
            'StringValue': '99.99'
        }
    }
)
```

### Complex Filter Policy
```json
{
  "price": [{"numeric": [">", 100]}],
  "store": ["example_corp"],
  "event": [{"anything-but": "order-cancel"}],
  "priority": [{"anything-but-prefix": "low"}]
}
```

## Fan-Out Pattern

Publish once, deliver to multiple destinations (SQS + Lambda + Email).

### Architecture
```
SNS Topic
├── SQS Queue 1 (Fulfillment)
├── SQS Queue 2 (Analytics)
├── Lambda (Notification)
└── Email (Confirmation)
```

### Setup
```bash
# Create topic
topic_arn=$(aws sns create-topic --name orders --query 'TopicArn' --output text)

# Subscribe queues and functions
aws sns subscribe --topic-arn $topic_arn --protocol sqs --notification-endpoint arn:aws:sqs:us-east-1:123456789012:fulfillment-queue
aws sns subscribe --topic-arn $topic_arn --protocol sqs --notification-endpoint arn:aws:sqs:us-east-1:123456789012:analytics-queue
aws sns subscribe --topic-arn $topic_arn --protocol lambda --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:send-notification
aws sns subscribe --topic-arn $topic_arn --protocol email --notification-endpoint orders@example.com
```

### Publishing
```python
import boto3

sns = boto3.client('sns')

# Single publish delivers to all subscribers
sns.publish(
    TopicArn=topic_arn,
    Subject='New Order',
    Message='Order 12345 placed by john@example.com for $99.99'
)
```

## Batch Operations

Send multiple messages efficiently.

### SQS Batch Send
```python
import boto3

sqs = boto3.client('sqs')

# Send 10 messages in one request
entries = [
    {
        'Id': str(i),
        'MessageBody': f'Message {i}',
        'MessageGroupId': 'order-batch'  # Required for FIFO
    }
    for i in range(10)
]

response = sqs.send_message_batch(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/123456789012/my-queue.fifo',
    Entries=entries
)

print(f"Successful: {len(response.get('Successful', []))}")
print(f"Failed: {len(response.get('Failed', []))}")

# Handle failures
for failed in response.get('Failed', []):
    print(f"Failed to send message {failed['Id']}: {failed['Code']}")
```

### SQS Batch Delete
```python
# Delete processed messages
entries = [
    {
        'Id': str(i),
        'ReceiptHandle': messages[i]['ReceiptHandle']
    }
    for i in range(len(messages))
]

response = sqs.delete_message_batch(
    QueueUrl=queue_url,
    Entries=entries
)
```

## Long Polling

Wait for messages instead of polling repeatedly.

```python
import boto3

sqs = boto3.client('sqs')

# Long polling: wait up to 20 seconds for messages
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20  # Long polling enabled
)

if 'Messages' in response:
    for message in response['Messages']:
        print(message['Body'])
```

**Benefits**:
- Reduces API calls (and cost)
- Lower latency compared to polling every second
- Better for worker processes

## Visibility Timeout

Control how long a message is invisible after reception.

```python
# Receive message
response = sqs.receive_message(QueueUrl=queue_url)
message = response['Messages'][0]

# Process...
# If processing takes longer than visibility timeout, message reappears

# Extend visibility while processing
sqs.change_message_visibility(
    QueueUrl=queue_url,
    ReceiptHandle=message['ReceiptHandle'],
    VisibilityTimeout=120  # Extend to 120 seconds
)

# Complete processing and delete
sqs.delete_message(
    QueueUrl=queue_url,
    ReceiptHandle=message['ReceiptHandle']
)
```

## Best Practices

1. **Use FIFO for ordering**: Standard queues don't guarantee order
2. **Always use DLQ**: Capture and monitor failed messages
3. **Long polling**: Reduce API calls with WaitTimeSeconds
4. **Batch operations**: Send/delete multiple messages at once
5. **Idempotency**: Design handlers to safely retry
6. **Message deduplication**: Use MessageDeduplicationId for exactly-once
7. **Filter policies**: Reduce queue noise with SNS filtering
8. **Monitor**: CloudWatch metrics for queue depth, age, delays
