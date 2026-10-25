---
skill_name: AWS CloudWatch Monitoring
description: Implement comprehensive monitoring with metrics, custom dashboards, alarms, log analysis, and anomaly detection
category: DevOps
version: 1.0.0
---

# AWS CloudWatch Monitoring

## Overview
CloudWatch provides observability into AWS resources and applications. Master metrics, logs, alarms, and dashboards to detect and respond to issues proactively.

## Metrics & Custom Dashboards

### Publish Custom Metrics

```python
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

# Publish application metric
cloudwatch.put_metric_data(
    Namespace='MyApplication',
    MetricData=[
        {
            'MetricName': 'ProcessingTime',
            'Value': 156.5,
            'Unit': 'Milliseconds',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Environment', 'Value': 'prod'},
                {'Name': 'Service', 'Value': 'api-gateway'}
            ]
        },
        {
            'MetricName': 'QueueDepth',
            'Value': 42,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'QueueName', 'Value': 'orders'}
            ]
        }
    ]
)

# Query metric statistics
response = cloudwatch.get_metric_statistics(
    Namespace='MyApplication',
    MetricName='ProcessingTime',
    Dimensions=[
        {'Name': 'Environment', 'Value': 'prod'}
    ],
    StartTime=datetime(2024, 1, 1),
    EndTime=datetime(2024, 1, 2),
    Period=300,  # 5 minutes
    Statistics=['Average', 'Maximum', 'Minimum', 'Sum', 'SampleCount'],
    ExtendedStatistics=['p99', 'p95']
)
```

### Create Dashboards

```python
dashboard_body = {
    'widgets': [
        {
            'type': 'metric',
            'properties': {
                'metrics': [
                    ['AWS/EC2', 'CPUUtilization', {'stat': 'Average'}],
                    ['AWS/EC2', 'NetworkIn', {'stat': 'Sum'}],
                    ['MyApplication', 'ProcessingTime', {'stat': 'p99'}]
                ],
                'period': 300,
                'stat': 'Average',
                'region': 'us-east-1',
                'title': 'Application Health',
                'yAxis': {'left': {'min': 0}},
                'view': 'timeSeries',
                'stacked': False
            }
        },
        {
            'type': 'log',
            'properties': {
                'query': '''
                  fields @timestamp, @message, @duration
                  | filter @message like /ERROR/
                  | stats count() as error_count by bin(5m)
                ''',
                'region': 'us-east-1',
                'title': 'Errors per 5 minutes'
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='ApplicationDashboard',
    DashboardBody=json.dumps(dashboard_body)
)
```

## Alarms & Notifications

### Metric-Based Alarms

```python
# High CPU utilization alarm
cloudwatch.put_metric_alarm(
    AlarmName='HighCPUUtilization',
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Period=300,
    EvaluationPeriods=2,
    Threshold=80.0,
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:us-east-1:123456789012:alert-topic'],
    TreatMissingData='notBreaching'
)

# Composite alarm (multiple conditions)
cloudwatch.put_composite_alarm(
    AlarmName='ApplicationDown',
    AlarmRule='''
    ALARM(HighCPUUtilization) OR
    ALARM(HighMemory) OR
    ALARM(HighNetworkErrors)
    ''',
    AlarmActions=['arn:aws:sns:us-east-1:123456789012:critical-topic']
)

# Anomaly detection alarm
cloudwatch.put_metric_alarm(
    AlarmName='UnusualLatency',
    Metrics=[
        {
            'Id': 'm1',
            'ReturnData': True,
            'MetricStat': {
                'Metric': {
                    'Namespace': 'MyApplication',
                    'MetricName': 'Latency'
                },
                'Period': 300,
                'Stat': 'Average'
            }
        },
        {
            'Id': 'ad1',
            'Expression': 'ANOMALY_DETECTION_BAND(m1, 2)',
            'ReturnData': True
        }
    ],
    EvaluationPeriods=1,
    Threshold=0,
    ComparisonOperator='LessThanLowerOrGreaterThanUpperThreshold'
)
```

## Log Groups & Insights

### Log Group Configuration

```python
logs = boto3.client('logs')

# Create log group with retention
logs.create_log_group(logGroupName='/aws/lambda/api-handler')

logs.put_retention_policy(
    logGroupName='/aws/lambda/api-handler',
    retentionInDays=30
)

# Create subscription filter for alerts
logs.put_subscription_filter(
    logGroupName='/aws/lambda/api-handler',
    filterName='error-filter',
    filterPattern='[time, request_id, level = ERROR*, ...]',
    destinationArn='arn:aws:lambda:us-east-1:123456789012:function:error-handler'
)

# Enable log insights
logs.put_query_definition(
    name='error-analysis',
    logGroupNames=['/aws/lambda/api-handler'],
    queryString='''
    fields @timestamp, @message, @duration, @memoryUsed
    | filter @message like /ERROR/
    | stats avg(@duration) as avg_duration, max(@memoryUsed) as max_memory by @message
    | sort avg_duration desc
    '''
)
```

### CloudWatch Insights Queries

```python
# Complex query for performance analysis
query = '''
fields @timestamp, @duration, @memoryUsed, @initDuration, @billedDuration
| filter ispresent(@duration)
| stats avg(@duration) as avg_duration,
        pct(@duration, 99) as p99_duration,
        pct(@memoryUsed, 95) as p95_memory
        by bin(5m)
'''

# Error rate analysis
error_query = '''
fields @timestamp, @message, @requestId, @userId
| filter @message like /ERROR|EXCEPTION/
| stats count() as error_count,
        count(distinct @userId) as affected_users
        by @message
| sort error_count desc
'''

# Cost analysis
cost_query = '''
fields @billedDuration, @memoryUsed
| stats avg(@billedDuration * @memoryUsed / 1024 / 1024 / 1000000) as avg_cost
'''
```

## Anomaly Detection

### Intelligent Anomaly Detection

```python
# Detect anomalies in custom metric
cloudwatch.put_anomaly_detector(
    Namespace='MyApplication',
    MetricName='RequestLatency',
    Stat='Average',
    Dimensions=[
        {'Name': 'Environment', 'Value': 'prod'}
    ]
)

# Query anomaly detector
anomalies = cloudwatch.describe_anomaly_detectors(
    Namespace='MyApplication',
    MetricName='RequestLatency'
)

# Get metric with anomaly band
response = cloudwatch.get_metric_statistics(
    Namespace='MyApplication',
    MetricName='RequestLatency',
    Dimensions=[{'Name': 'Environment', 'Value': 'prod'}],
    StartTime=datetime.utcnow() - timedelta(days=7),
    EndTime=datetime.utcnow(),
    Period=300,
    Statistics=['Average'],
    ExtendedStatistics=['ANOMALY_DETECTOR']
)
```

## Event-Driven Actions

### EventBridge Integration

```python
events = boto3.client('events')

# Create rule that triggers on alarm state change
events.put_rule(
    Name='alarm-state-change',
    EventPattern=json.dumps({
        'source': ['aws.cloudwatch'],
        'detail-type': ['CloudWatch Alarm State Change'],
        'detail': {
            'state': {'value': ['ALARM']}
        }
    })
)

# Add SNS target
events.put_targets(
    Rule='alarm-state-change',
    Targets=[
        {
            'Id': '1',
            'Arn': 'arn:aws:sns:us-east-1:123456789012:alert-topic',
            'RoleArn': 'arn:aws:iam::123456789012:role/EventBridgeRole'
        }
    ]
)

# Create rule for metric changes
events.put_rule(
    Name='high-error-rate',
    EventPattern=json.dumps({
        'source': ['custom.app'],
        'detail-type': ['Metric Change'],
        'detail': {
            'metric_value': [{'numeric': ['>', 100]}]
        }
    })
)
```

## Monitoring Best Practices

```python
class ApplicationMonitoring:
    def __init__(self):
        self.cw = boto3.client('cloudwatch')
        self.namespace = 'MyApplication'

    def record_request(self, duration, status_code, endpoint):
        """Record request metrics"""
        self.cw.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    'MetricName': 'RequestDuration',
                    'Value': duration,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': endpoint},
                        {'Name': 'StatusCode', 'Value': str(status_code)}
                    ]
                },
                {
                    'MetricName': 'RequestCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': endpoint},
                        {'Name': 'StatusCode', 'Value': str(status_code)}
                    ]
                }
            ]
        )

    def record_error(self, error_type, context):
        """Record errors with context"""
        self.cw.put_metric_data(
            Namespace=self.namespace,
            MetricData=[{
                'MetricName': 'Errors',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'ErrorType', 'Value': error_type},
                    {'Name': 'Context', 'Value': context}
                ]
            }]
        )
```

## Production Checklist

- [ ] Define key metrics for all critical services
- [ ] Set appropriate alarm thresholds
- [ ] Create dashboards for operations team
- [ ] Enable log retention based on compliance needs
- [ ] Use CloudWatch Insights for troubleshooting
- [ ] Monitor application-specific metrics
- [ ] Set up anomaly detection for baseline changes
- [ ] Route critical alarms to on-call engineer
- [ ] Test alarm notifications regularly
- [ ] Document what each alarm means and how to respond
