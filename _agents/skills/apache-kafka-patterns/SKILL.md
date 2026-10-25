---
skill_name: Apache Kafka Patterns
description: Build streaming systems with producers, consumers, streams, schema registry, and connect
category: Data
version: 1.0.0
---

# Apache Kafka Patterns

## Overview
Kafka powers real-time data pipelines. Master producers, consumers, streams processing, and schema management.

## Broker Setup

```yaml
# docker-compose.yml
version: '3'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

## Producer Pattern

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',  # Wait for all replicas
    retries=3
)

# Send event
event = {
    'user_id': 123,
    'action': 'purchase',
    'amount': 99.99
}

future = producer.send('user-events', event)

# Block until sent
record_metadata = future.get(timeout=10)
print(f"Sent to topic {record_metadata.topic}, partition {record_metadata.partition}")

producer.close()
```

## Consumer Pattern

```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'user-events',
    bootstrap_servers=['localhost:9092'],
    group_id='analytics-group',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest'  # Start from beginning
)

# Consume events
for message in consumer:
    event = message.value
    print(f"Event: {event}")
    
    # Process
    process_event(event)
    
    # Offset committed automatically

consumer.close()
```

## Streams Processing

```python
from kafka import KafkaConsumer, KafkaProducer
from collections import defaultdict

class EventAggregator:
    def __init__(self, window_size_seconds=60):
        self.window_size = window_size_seconds
        self.events = defaultdict(list)

    def process_stream(self):
        consumer = KafkaConsumer('user-events', group_id='aggregator')
        producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode())

        for message in consumer:
            event = json.loads(message.value.decode())
            user_id = event['user_id']

            self.events[user_id].append(event)

            # Simple windowing (sliding window)
            self._aggregate_and_emit(producer, user_id)

    def _aggregate_and_emit(self, producer, user_id):
        if len(self.events[user_id]) >= 5:
            aggregate = {
                'user_id': user_id,
                'event_count': len(self.events[user_id]),
                'total_amount': sum(e.get('amount', 0) for e in self.events[user_id])
            }
            producer.send('user-aggregates', aggregate)
            self.events[user_id] = []

aggregator = EventAggregator()
aggregator.process_stream()
```

## Schema Registry

```python
from confluent_kafka import Producer, Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer

# Schema Registry client
sr_client = SchemaRegistryClient({'url': 'http://localhost:8081'})

# Define schema
schema_str = """{
    "type": "record",
    "name": "UserEvent",
    "fields": [
        {"name": "user_id", "type": "int"},
        {"name": "action", "type": "string"},
        {"name": "timestamp", "type": "long"}
    ]
}"""

# Serializer
avro_serializer = AvroSerializer(sr_client, schema_str)
avro_deserializer = AvroDeserializer(sr_client)

# Producer with schema
producer = Producer({
    'bootstrap.servers': 'localhost:9092',
    'value.serializer': avro_serializer
})

event = {'user_id': 123, 'action': 'click', 'timestamp': 1234567890}
producer.produce('events', value=event)

# Consumer
consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-group',
    'value.deserializer': avro_deserializer
})

consumer.subscribe(['events'])
msg = consumer.poll(timeout=1.0)
if msg:
    print(f"Received: {msg.value()}")
```

## Kafka Connect

Auto-sync data between systems:

```json
{
  "name": "postgres-to-kafka",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "localhost",
    "database.port": 5432,
    "database.user": "postgres",
    "database.password": "password",
    "database.dbname": "analytics",
    "database.server.name": "production",
    "table.include.list": "public.orders",
    "plugin.name": "pgoutput",
    "publication.name": "dbz_publication",
    "slot.name": "dbz_slot"
  }
}
```

## Consumer Groups & Partitioning

```python
from kafka.admin import KafkaAdminClient, NewTopic

# Create topic with partitions
admin = KafkaAdminClient(bootstrap_servers=['localhost:9092'])
topic = NewTopic(
    name='distributed-topic',
    num_partitions=4,
    replication_factor=3
)
admin.create_topics([topic])

# Multiple consumers (one per partition for max throughput)
consumer = KafkaConsumer(
    'distributed-topic',
    bootstrap_servers=['localhost:9092'],
    group_id='high-throughput-group',
    max_poll_records=500,  # Batch size
    session_timeout_ms=30000
)
```

## Error Handling

```python
from kafka.errors import KafkaError

class ResilientConsumer:
    def consume(self):
        consumer = KafkaConsumer(
            'events',
            bootstrap_servers=['localhost:9092'],
            group_id='resilient-group'
        )

        for message in consumer:
            try:
                event = json.loads(message.value.decode())
                self.process(event)
                consumer.commit()  # Only commit on success
            except Exception as e:
                # Log and continue
                print(f"Error processing event: {e}")
                # Don't commit, will retry
                continue

    def process(self, event):
        # Business logic
        pass
```

## Monitoring Metrics

```python
# Track lag
from kafka.admin import KafkaAdminClient

admin = KafkaAdminClient(bootstrap_servers=['localhost:9092'])

for group_id in admin.describe_consumer_groups(['my-group']).result()['groups']:
    offsets = admin.list_consumer_group_offsets(group_id)
    for (topic, partition), offset in offsets.items():
        print(f"{group_id} {topic}[{partition}]: lag={offset.offset}")
```

## Production Checklist

- [ ] Use 3+ brokers for replication
- [ ] Set replication factor = 3
- [ ] Monitor consumer lag
- [ ] Implement schema validation
- [ ] Use transactional producers for exactly-once
- [ ] Scale partitions with throughput needs
- [ ] Implement dead letter queues
- [ ] Monitor broker disk usage
- [ ] Set retention policies
- [ ] Use consumer groups for parallel processing
- [ ] Implement circuit breaker on failures
- [ ] Log all errors and anomalies
