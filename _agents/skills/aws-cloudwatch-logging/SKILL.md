---
skill_name: aws-cloudwatch-logging
description: CloudWatch patterns for metric filters, composite alarms, dashboards, Container Insights, and X-Ray
category: Cloud & DevOps
version: 1.0.0
---

# AWS CloudWatch Logging and Monitoring

## Log Groups and Streams

### Create Log Group
```bash
aws logs create-log-group \
  --log-group-name /aws/lambda/my-function \
  --tags Environment=prod,Application=my-app

# Set retention policy (30 days)
aws logs put-retention-policy \
  --log-group-name /aws/lambda/my-function \
  --retention-in-days 30
```

### Log Retention Cost Optimization
```bash
# Archive logs older than 90 days to S3
aws logs put-subscription-filter \
  --log-group-name /aws/lambda/my-function \
  --filter-name archive-to-s3 \
  --filter-pattern "" \
  --destination-arn arn:aws:lambda:us-east-1:123456789012:function:archive-logs
```

## Metric Filters

Extract metrics from logs.

### Create Metric Filter for Errors
```bash
aws logs put-metric-filter \
  --log-group-name /aws/lambda/my-function \
  --filter-name ErrorCount \
  --filter-pattern "[time, request_id, level = ERROR, ...]" \
  --metric-transformations \
    metricName=ErrorCount,\
metricNamespace=MyApp,\
metricValue=1,\
defaultValue=0
```

### Python Application Logging with Filters
```python
import logging
import json
from datetime import datetime

# Structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Process request
        result = process_order(event)

        # Log success
        logger.info(json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': context.request_id,
            'level': 'INFO',
            'message': 'Order processed',
            'order_id': result['order_id'],
            'status': 'success'
        }))

        return {'statusCode': 200, 'body': json.dumps(result)}
    except Exception as e:
        # Log error with structured format
        logger.error(json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': context.request_id,
            'level': 'ERROR',
            'message': str(e),
            'exception_type': type(e).__name__
        }))
        return {'statusCode': 500}
```

### Query Metric Data
```bash
# Get error count over last hour
aws cloudwatch get-metric-statistics \
  --namespace MyApp \
  --metric-name ErrorCount \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## CloudWatch Insights Queries

Analyze logs with SQL-like syntax.

### Common Queries
```sql
-- Count errors by level
fields @timestamp, @message
| stats count() as error_count by level

-- Find slow requests (duration > 1 second)
fields @timestamp, @duration
| filter @duration > 1000
| stats avg(@duration) as avg_duration, max(@duration) as max_duration

-- Extract and analyze status codes
fields @timestamp, status
| stats count() as request_count by status

-- Find top 10 error messages
fields @message
| filter level = "ERROR"
| stats count() as freq by @message
| sort freq desc
| limit 10

-- Calculate p95 latency
fields @duration
| filter @duration > 0
| stats pct(@duration, 95) as p95_latency
```

### Save Query
```bash
aws logs put-query-definition \
  --name slow-requests \
  --log-group-names /aws/lambda/my-function \
  --query-string 'fields @timestamp, @duration
| filter @duration > 1000
| stats count() as slow_requests'
```

## Alarms and Alerts

### Create Metric Alarm
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name high-error-rate \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name ErrorRate \
  --namespace MyApp \
  --statistic Average \
  --period 300 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

### Composite Alarm
```bash
aws cloudwatch put-composite-alarm \
  --alarm-name critical-service-down \
  --alarm-description "Alert if both API and DB are unhealthy" \
  --alarm-rule "ALARM(api-health-alarm) AND ALARM(db-health-alarm)" \
  --actions-enabled \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:critical-alerts
```

### Anomaly Detection
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name api-latency-anomaly \
  --comparison-operator LessThanLowerOrGreaterThanUpperThreshold \
  --evaluation-periods 1 \
  --metrics '[{
    "Id": "e1",
    "ReturnData": true,
    "MetricStat": {
      "Metric": {
        "Namespace": "MyApp",
        "MetricName": "Latency"
      },
      "Period": 300,
      "Stat": "Average"
    }
  },
  {
    "Id": "m1",
    "Expression": "ANOMALY_DETECTION_BAND(e1, 2)",
    "ReturnData": true
  }]'
```

## Dashboards

### Create Dashboard with JSON
```bash
aws cloudwatch put-dashboard \
  --dashboard-name MyApp-Dashboard \
  --dashboard-body file://dashboard.json
```

### dashboard.json
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["MyApp", "RequestCount", {"stat": "Sum"}],
          [".", "ErrorCount", {"stat": "Sum"}],
          [".", "Latency", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Service Metrics"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "fields @timestamp, @message | filter level = 'ERROR' | stats count()",
        "region": "us-east-1",
        "title": "Error Rate"
      }
    }
  ]
}
```

## Container Insights

Monitor ECS and EKS containers.

### Enable Container Insights on ECS
```bash
aws ecs create-cluster \
  --cluster-name my-cluster \
  --cluster-settings name=containerInsights,value=enabled
```

### CloudWatch Agent for Container Insights
```bash
# Install on EC2 instances
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "metrics": {
    "namespace": "CWAgent",
    "metrics_collected": {
      "cpu": {
        "measurement": [{"name": "cpu_usage_idle", "rename": "CPU_IDLE", "unit": "Percent"}],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": [{"name": "mem_used_percent"}],
        "metrics_collection_interval": 60
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

## X-Ray Tracing

Distributed tracing for microservices.

### Enable X-Ray in Lambda
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()  # Patch AWS SDK

@xray_recorder.capture('process_order')
def process_order(event):
    # Code here is automatically traced
    return {'order_id': '12345'}

def lambda_handler(event, context):
    result = process_order(event)
    return {'statusCode': 200, 'body': json.dumps(result)}
```

### X-Ray Subsegment
```python
from aws_xray_sdk.core import xray_recorder

def lambda_handler(event, context):
    with xray_recorder.capture('db_query'):
        # Database query here
        results = db.query("SELECT * FROM users")

    with xray_recorder.capture('process_results'):
        # Processing here
        processed = [transform(r) for r in results]

    return processed
```

### View Service Map
```bash
# Query service map data
aws xray get-service-graph \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --query 'ServiceGraph.Services'
```

## Best Practices

1. **Structured logging**: Use JSON format for easier parsing
2. **Log levels**: Use ERROR, WARN, INFO strategically
3. **Metric filters**: Extract KPIs from logs
4. **Alarms**: Set thresholds for critical metrics
5. **Log retention**: Archive old logs to S3
6. **Dashboards**: Visualize key metrics
7. **Container Insights**: Monitor containerized workloads
8. **X-Ray**: Trace distributed requests
9. **Cost optimization**: Use log group retention policies
10. **Anomaly detection**: Automatic threshold learning
