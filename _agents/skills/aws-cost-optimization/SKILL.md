---
skill_name: aws-cost-optimization
description: AWS cost optimization with Reserved Instances, Savings Plans, Spot instances, and rightsizing
category: DevOps & Infrastructure
version: 1.0.0
---

# AWS Cost Optimization

Reduce AWS spending through intelligent resource management and purchasing strategies.

## Purchase Options

| Option | Discount | Commitment | Best For |
|--------|----------|-----------|----------|
| On-Demand | 0% | None | Flexible workloads |
| Reserved Instance | 40-75% | 1-3 years | Predictable workloads |
| Savings Plans | 30-72% | 1-3 years | Compute across services |
| Spot Instances | 70-90% | Interruptible | Fault-tolerant workloads |

## EC2 Rightsizing

```bash
# Identify underutilized instances
aws ec2 describe-instances --query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name]'

# Monitor CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/EC2 \
    --metric-name CPUUtilization \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-31T23:59:59Z \
    --period 3600 \
    --statistics Average
```

## Reserved Instances

```python
import boto3

ec2 = boto3.client('ec2')

# Purchase Reserved Instances
response = ec2.purchase_reserved_instances_offering(
    InstanceCount=2,
    ReservedInstancesOfferingId='0123456789abcdef0',
    LimitPrice=0.15
)

# Check Reserved Instance utilization
reservations = ec2.describe_reserved_instances()
for reservation in reservations['ReservedInstances']:
    print(f"{reservation['InstanceType']}: {reservation['State']}")
```

## Spot Instances

```javascript
// Launch Spot instance with fallback to On-Demand
const params = {
    ImageId: 'ami-12345678',
    InstanceType: 't3.medium',
    SpotPrice: '0.05',  // Max price
    KeyName: 'my-key',
    TagSpecifications: [{
        ResourceType: 'instance',
        Tags: [{ Key: 'Name', Value: 'spot-worker' }],
    }],
};

const ec2 = new AWS.EC2();
const result = await ec2.requestSpotInstances(params).promise();
console.log(`Spot request: ${result.SpotInstanceRequests[0].SpotInstanceRequestId}`);
```

## S3 Lifecycle Policies

```json
{
    "Rules": [
        {
            "Id": "Archive Old Objects",
            "Filter": { "Prefix": "logs/" },
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": { "Days": 365 }
        }
    ]
}
```

## Cost Monitoring

```bash
# Use Cost Explorer API
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE

# Set up budget alerts
aws budgets create-budget \
    --account-id 123456789012 \
    --budget BudgetName=Monthly-Limit,BudgetLimit=Type=MONTHLY,Amount=5000
```

## Best Practices

- Use AWS Compute Optimizer recommendations
- Implement tagging for cost allocation
- Consolidate under AWS Organizations for volume discounts
- Use Savings Plans instead of RIs for flexibility
- Review AWS Trusted Advisor recommendations
- Enable unused resource discovery
- Set up CloudWatch alarms for cost spikes
