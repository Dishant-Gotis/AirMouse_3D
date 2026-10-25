---
skill_name: aws-step-functions
description: Step Functions patterns for Express vs Standard, error handling, parallel execution, and Map states
category: Cloud & DevOps
version: 1.0.0
---

# AWS Step Functions

## Express vs Standard

### Standard State Machine
Synchronous execution, at-most-once semantics, up to 1 year execution.

```json
{
  "Comment": "Order processing workflow",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:validate-order",
      "Next": "ProcessPayment",
      "Catch": [{
        "ErrorEquals": ["ValidationError"],
        "Next": "InvalidOrderPath"
      }]
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:process-payment",
      "Next": "FulfillOrder"
    },
    "FulfillOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:fulfill-order",
      "End": true
    },
    "InvalidOrderPath": {
      "Type": "Fail",
      "Error": "InvalidOrder",
      "Cause": "Order validation failed"
    }
  }
}
```

### Express State Machine
Asynchronous, at-least-once semantics, up to 5 minute execution.

```json
{
  "Comment": "Real-time event processing",
  "StartAt": "ProcessEvent",
  "States": {
    "ProcessEvent": {
      "Type": "Task",
      "Resource": "arn:aws:states:::events:putEvents",
      "Parameters": {
        "Entries": [{
          "Source": "custom.events",
          "DetailType": "ProcessedEvent",
          "Detail.$": "$"
        }]
      },
      "End": true
    }
  }
}
```

## Error Handling and Retries

### Retry Configuration
```json
{
  "States": {
    "CallExternalAPI": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:call-api",
      "Retry": [
        {
          "ErrorEquals": ["ThrottlingException"],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2.0
        },
        {
          "ErrorEquals": ["ServiceUnavailable"],
          "IntervalSeconds": 15,
          "MaxAttempts": 2,
          "BackoffRate": 1.0
        }
      ],
      "Catch": [{
        "ErrorEquals": ["States.TaskFailed"],
        "Next": "HandleFailure",
        "ResultPath": "$.error"
      }],
      "Next": "Success"
    },
    "HandleFailure": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:handle-error",
      "Next": "Success"
    },
    "Success": {
      "Type": "Pass",
      "End": true
    }
  }
}
```

**Exponential Backoff**: 2 + 4 + 8 + 16 + 32 + 64 = 126 second delay max.

## Parallel States

Execute multiple tasks concurrently.

```json
{
  "States": {
    "ParallelProcessing": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "ProcessInventory",
          "States": {
            "ProcessInventory": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:us-east-1:123456789012:function:process-inventory",
              "End": true
            }
          }
        },
        {
          "StartAt": "ProcessShipping",
          "States": {
            "ProcessShipping": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:us-east-1:123456789012:function:process-shipping",
              "End": true
            }
          }
        },
        {
          "StartAt": "ProcessBilling",
          "States": {
            "ProcessBilling": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:us-east-1:123456789012:function:process-billing",
              "End": true
            }
          }
        }
      ],
      "Next": "CombineResults"
    },
    "CombineResults": {
      "Type": "Pass",
      "End": true
    }
  }
}
```

Results are combined into array:
```json
[
  {"inventory_result": "..."},
  {"shipping_result": "..."},
  {"billing_result": "..."}
]
```

## Map States

Iterate over arrays dynamically.

```json
{
  "States": {
    "ProcessOrders": {
      "Type": "Map",
      "ItemsPath": "$.orders",
      "MaxConcurrency": 5,
      "Iterator": {
        "StartAt": "ProcessOrder",
        "States": {
          "ProcessOrder": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789012:function:process-order",
            "End": true
          }
        }
      },
      "Next": "AllOrdersProcessed"
    },
    "AllOrdersProcessed": {
      "Type": "Pass",
      "End": true
    }
  }
}
```

Input:
```json
{
  "orders": [
    {"id": "order-1", "total": 100},
    {"id": "order-2", "total": 200},
    {"id": "order-3", "total": 300}
  ]
}
```

Output (array of results):
```json
[
  {"order_id": "order-1", "status": "processed"},
  {"order_id": "order-2", "status": "processed"},
  {"order_id": "order-3", "status": "processed"}
]
```

### Nested Map with Concurrency Limits
```json
{
  "Type": "Map",
  "ItemsPath": "$.batches",
  "MaxConcurrency": 2,  // Process max 2 batches concurrently
  "Iterator": {
    "StartAt": "ProcessBatch",
    "States": {
      "ProcessBatch": {
        "Type": "Map",
        "ItemsPath": "$.items",
        "MaxConcurrency": 10,  // Within each batch, process 10 items at once
        "Iterator": {
          "StartAt": "ProcessItem",
          "States": {
            "ProcessItem": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:us-east-1:123456789012:function:process-item",
              "End": true
            }
          }
        },
        "End": true
      }
    }
  },
  "End": true
}
```

## Choice States

Conditional branching based on input.

```json
{
  "States": {
    "CheckOrderAmount": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.total",
          "NumericGreaterThan": 1000,
          "Next": "HighValueOrder"
        },
        {
          "Variable": "$.total",
          "NumericGreaterThan": 100,
          "Next": "MediumValueOrder"
        },
        {
          "Variable": "$.customer_type",
          "StringEquals": "premium",
          "Next": "PremiumOrder"
        }
      ],
      "Default": "StandardOrder"
    },
    "HighValueOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:handle-high-value",
      "Next": "Complete"
    },
    "MediumValueOrder": {
      "Type": "Pass",
      "Next": "Complete"
    },
    "PremiumOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:handle-premium",
      "Next": "Complete"
    },
    "StandardOrder": {
      "Type": "Pass",
      "Next": "Complete"
    },
    "Complete": {
      "Type": "Pass",
      "End": true
    }
  }
}
```

## Wait States

Pause execution for a duration or until a timestamp.

```json
{
  "States": {
    "DelayProcessing": {
      "Type": "Wait",
      "Seconds": 3600,  // Wait 1 hour
      "Next": "ResumeProcessing"
    },
    "ScheduledProcessing": {
      "Type": "Wait",
      "Timestamp": "2024-12-31T23:59:59Z",  // Wait until date
      "Next": "DoWork"
    },
    "ResumeProcessing": {
      "Type": "Pass",
      "End": true
    }
  }
}
```

## Create and Execute State Machine

### Create State Machine
```bash
# Create IAM role
role=$(aws iam create-role \
  --role-name sfn-execution-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "states.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --query 'Role.Arn' \
  --output text)

# Attach policy to invoke Lambda
aws iam put-role-policy \
  --role-name sfn-execution-role \
  --policy-name invoke-lambda \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:*"
    }]
  }'

# Create state machine
sfn_arn=$(aws stepfunctions create-state-machine \
  --name order-processing \
  --definition file://state-machine.json \
  --role-arn $role \
  --query 'stateMachineArn' \
  --output text)

echo "State Machine ARN: $sfn_arn"
```

### Execute State Machine
```bash
# Start execution
exec_arn=$(aws stepfunctions start-execution \
  --state-machine-arn $sfn_arn \
  --name order-123 \
  --input '{
    "order_id": "12345",
    "total": 500,
    "customer_type": "standard"
  }' \
  --query 'executionArn' \
  --output text)

# Check execution status
aws stepfunctions describe-execution --execution-arn $exec_arn

# Get execution history
aws stepfunctions get-execution-history \
  --execution-arn $exec_arn \
  --query 'events[].{Type:type,Timestamp:timestamp,Details:stateExitedEventDetails}'
```

## Best Practices

1. **Express for real-time**: Use for high-frequency events
2. **Standard for workflows**: Use for long-running business processes
3. **Error handling**: Always add Catch and Retry blocks
4. **Timeouts**: Set ResultPath to preserve input on errors
5. **Monitoring**: Enable X-Ray tracing
6. **Cost optimization**: Use Map with MaxConcurrency to control parallelization
7. **Input/Output filtering**: Use InputPath, OutputPath to transform data
8. **Dead letter queues**: Route failures to SQS for replay
9. **State machine limits**: 25,000 state history events per hour
10. **Testing**: Simulate with AWS Console or offline tools
