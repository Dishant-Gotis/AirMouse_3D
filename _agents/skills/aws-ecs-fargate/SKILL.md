---
skill_name: aws-ecs-fargate
description: ECS Fargate deployment patterns for task definitions, service discovery, scaling, and monitoring
category: Cloud & DevOps
version: 1.0.0
---

# AWS ECS Fargate

## Task Definitions

Task definitions are blueprints for Docker containers in ECS.

### Minimal Task Definition
```json
{
  "family": "my-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "my-container",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/my-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ]
    }
  ]
}
```

### Task Definition with Health Checks
```json
{
  "containerDefinitions": [
    {
      "name": "my-container",
      "image": "my-app:latest",
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Secrets and Environment Variables
```json
{
  "containerDefinitions": [
    {
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-password:password::"
        }
      ],
      "environment": [
        {
          "name": "DB_HOST",
          "value": "db.example.com"
        }
      ]
    }
  ]
}
```

## Service Configuration

Services manage the desired number of tasks.

### ECS Service Definition
```bash
aws ecs create-service \
  --cluster my-cluster \
  --service-name my-service \
  --task-definition my-app:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-app/1234567890,containerName=my-container,containerPort=8080"
```

### Service with Health Check Grace Period
```json
{
  "deploymentConfiguration": {
    "maximumPercent": 200,
    "minimumHealthyPercent": 100,
    "deploymentCircuitBreaker": {
      "enable": true,
      "rollback": true
    }
  },
  "healthCheckGracePeriodSeconds": 60
}
```

## Service Discovery

Internal DNS for task-to-task communication.

### AWS Cloud Map Service Discovery
```bash
# Create namespace
aws servicediscovery create-private-dns-namespace \
  --name my-app.local \
  --vpc vpc-12345

# Create service
aws servicediscovery create-service \
  --name api \
  --namespace-id ns-12345 \
  --dns-config "NamespaceId=ns-12345,DnsRecords=[{Type=A,TTL=10}]"

# Register task instances automatically via ECS
aws ecs create-service \
  --cluster my-cluster \
  --service-name api-service \
  --task-definition my-app:1 \
  --desired-count 3 \
  --service-registries "registryArn=arn:aws:servicediscovery:us-east-1:123456789012:service/ns-12345/srv-12345"
```

### In-Container DNS Resolution
```bash
# Inside container, resolve other services
nslookup api.my-app.local
# Returns IP addresses of all healthy tasks
```

## Auto Scaling

Scale services based on metrics.

### Target Tracking Scaling
```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    TargetValue=70.0,\
PredefinedMetricSpecification='{PredefinedMetricType=ECSServiceAverageCPUUtilization}'
```

### Custom Metric Scaling
```python
import boto3

asg_client = boto3.client('application-autoscaling')

asg_client.put_scaling_policy(
    PolicyName='custom-memory-scaling',
    ServiceNamespace='ecs',
    ResourceId='service/my-cluster/my-service',
    ScalableDimension='ecs:service:DesiredCount',
    PolicyType='TargetTrackingScaling',
    TargetTrackingScalingPolicyConfiguration={
        'TargetValue': 80.0,
        'CustomizedMetricSpecification': {
            'MetricName': 'MemoryUtilization',
            'Namespace': 'AWS/ECS',
            'Statistic': 'Average',
            'Unit': 'Percent',
            'Dimensions': [
                {'Name': 'ServiceName', 'Value': 'my-service'},
                {'Name': 'ClusterName', 'Value': 'my-cluster'}
            ]
        },
        'ScaleOutCooldown': 60,
        'ScaleInCooldown': 300
    }
)
```

## Container Insights

Monitor tasks and services.

### Enable Container Insights
```bash
aws ecs create-cluster \
  --cluster-name my-cluster \
  --cluster-settings name=containerInsights,value=enabled
```

### CloudWatch Logs Configuration
```json
{
  "logConfiguration": {
    "logDriver": "awslogs",
    "options": {
      "awslogs-group": "/ecs/my-app",
      "awslogs-region": "us-east-1",
      "awslogs-stream-prefix": "ecs"
    }
  }
}
```

### Query Container Insights
```bash
aws logs filter-log-events \
  --log-group-name /ecs/my-app \
  --start-time 1609459200000 \
  --filter-pattern "ERROR"
```

## Networking and Security

### Security Group Configuration
```bash
# Allow inbound on application port
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345 \
  --protocol tcp \
  --port 8080 \
  --source-security-group-id sg-67890  # ALB security group

# Allow outbound to RDS
aws ec2 authorize-security-group-egress \
  --group-id sg-12345 \
  --protocol tcp \
  --port 3306 \
  --destination-security-group-id sg-rds
```

### VPC Networking
Use `awsvpc` network mode for Fargate:
- Each task gets its own ENI (Elastic Network Interface)
- Full VPC networking capabilities
- Requires subnet and security group specification

```bash
aws ecs create-service \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-12345,subnet-67890,subnet-abcde],
    securityGroups=[sg-12345],
    assignPublicIp=ENABLED
  }"
```

## Deployment Strategies

### Blue-Green Deployment
```bash
# Version 1 (Blue)
aws ecs create-service \
  --cluster my-cluster \
  --service-name my-service-blue \
  --task-definition my-app:1 \
  --desired-count 3

# Version 2 (Green) — running in parallel
aws ecs create-service \
  --cluster my-cluster \
  --service-name my-service-green \
  --task-definition my-app:2 \
  --desired-count 3

# Switch ALB to green
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-app/1234567890 \
  --target-group my-service-green

# Decommission blue
aws ecs delete-service \
  --cluster my-cluster \
  --service my-service-blue \
  --force
```

### Rolling Deployment
```json
{
  "deploymentConfiguration": {
    "maximumPercent": 200,
    "minimumHealthyPercent": 50
  }
}
```

This allows up to 2x desired count (100% existing + 100% new) while maintaining at least 50% healthy.

## Capacity Providers

Manage cluster capacity (Fargate, Fargate Spot, or EC2).

```bash
aws ecs create-capacity-provider \
  --name my-capacity-provider \
  --auto-scaling-group-provider \
    autoScalingGroupArn=arn:aws:autoscaling:us-east-1:123456789012:autoScalingGroup:12345678-1234-1234-1234-123456789012:autoScalingGroupName/my-asg

aws ecs put-cluster-capacity-providers \
  --cluster my-cluster \
  --capacity-providers my-capacity-provider FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1,base=1 \
    capacityProvider=FARGATE_SPOT,weight=4
```

## Cost Optimization Tips

1. **Use Fargate Spot**: 70% cheaper, good for stateless workloads
2. **Right-size tasks**: Monitor CPU/memory utilization, adjust task size
3. **Use smaller images**: Multi-stage builds, alpine base images
4. **Batch similar workloads**: Share cluster, reduce per-task overhead
5. **Enable autoscaling**: Scale down during off-hours

## Best Practices Summary

1. **Always use awsvpc**: Required for Fargate, better security
2. **Health checks**: Define both task and service health checks
3. **Logging**: Use CloudWatch Logs with long retention for debugging
4. **Updates**: Use deployment circuit breaker with automatic rollback
5. **Monitoring**: Enable Container Insights for visibility
6. **Secrets**: Use Secrets Manager, not environment variables
7. **Gradual rollouts**: Deploy new versions to canary first
