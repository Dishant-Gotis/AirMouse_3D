---
skill_name: aws-waf-security
description: AWS WAF configuration for managed rules, rate limiting, geographic blocks, custom rules, and logging
category: Cloud & DevOps
version: 1.0.0
---

# AWS WAF (Web Application Firewall)

## Create Web ACL

```bash
# Create Web ACL with managed rules
aws wafv2 create-web-acl \
  --name app-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules file://rules.json \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=app-waf
```

### rules.json

```json
[
  {
    "Name": "AWSManagedRulesCommonRuleSet",
    "Priority": 0,
    "OverrideAction": {
      "None": {}
    },
    "Statement": {
      "ManagedRuleGroupStatement": {
        "VendorName": "AWS",
        "Name": "AWSManagedRulesCommonRuleSet",
        "ExcludedRules": [
          {
            "Name": "SizeRestrictions_BODY"
          }
        ]
      }
    },
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "CommonRuleSet"
    }
  },
  {
    "Name": "AWSManagedRulesKnownBadInputsRuleSet",
    "Priority": 1,
    "OverrideAction": {
      "None": {}
    },
    "Statement": {
      "ManagedRuleGroupStatement": {
        "VendorName": "AWS",
        "Name": "AWSManagedRulesKnownBadInputsRuleSet"
      }
    },
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "KnownBadInputs"
    }
  }
]
```

## Rate Limiting

```json
{
  "Name": "RateLimitRule",
  "Priority": 2,
  "Action": {
    "Block": {
      "CustomResponse": {
        "ResponseCode": 429,
        "CustomResponseBodyKey": "rate-limit-exceeded"
      }
    }
  },
  "Statement": {
    "RateBasedStatement": {
      "Limit": 2000,
      "AggregateKeyType": "IP"
    }
  },
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "RateLimit"
  }
}
```

## Geo-Blocking

```json
{
  "Name": "GeoBlockingRule",
  "Priority": 3,
  "Action": {
    "Block": {}
  },
  "Statement": {
    "GeoMatchStatement": {
      "CountryCodes": [
        "CN",
        "RU",
        "KP"
      ]
    }
  },
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "GeoBlock"
  }
}
```

## Custom Rules

```json
{
  "Name": "IPReputationListRule",
  "Priority": 4,
  "Action": {
    "Block": {}
  },
  "Statement": {
    "IPSetReferenceStatement": {
      "Arn": "arn:aws:wafv2:us-east-1:123456789012:regional/ipset/malicious-ips/a1234567-b890-c123-d456-e78901234567"
    }
  },
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "IPReputation"
  }
}
```

## Bot Control

```json
{
  "Name": "AWSManagedRulesBotControlRuleSet",
  "Priority": 5,
  "OverrideAction": {
    "None": {}
  },
  "Statement": {
    "ManagedRuleGroupStatement": {
      "VendorName": "AWS",
      "Name": "AWSManagedRulesBotControlRuleSet"
    }
  },
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "BotControl"
  }
}
```

## Logging Configuration

```bash
aws wafv2 put-logging-configuration \
  --logging-configuration ResourceArn=arn:aws:wafv2:us-east-1:123456789012:regional/web-acl/app-waf/a1234567-b890-c123-d456-e78901234567,\
LogDestinationConfigs=arn:aws:logs:us-east-1:123456789012:log-group:/aws/waf/app-waf,\
RedactedFields=UriPath={},\
LoggingFilter=BehaviorFilter=MATCHED,RequiredFields=MATCH_TYPE,\
MetricName=WAFLogging
```

## Monitoring

```bash
# View sampled requests
aws wafv2 get-sampled-requests \
  --web-acl-arn arn:aws:wafv2:us-east-1:123456789012:regional/web-acl/app-waf/a1234567-b890-c123-d456-e78901234567 \
  --rule-metric-name CommonRuleSet \
  --scope REGIONAL \
  --time-window StartTime=1609459200,EndTime=1609545600 \
  --max-items 100

# Get metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name AllowedRequests \
  --dimensions Name=WebACL,Value=app-waf \
  --start-time 2021-01-01T00:00:00Z \
  --end-time 2021-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Terraform Configuration

```hcl
resource "aws_wafv2_web_acl" "main" {
  name  = "app-waf"
  scope = "REGIONAL"

  default_action {
    allow {
      custom_request_handling {
        insert_headers {
          name  = "X-Processed-By"
          value = "WAF"
        }
      }
    }
  }

  rule {
    name     = "RateLimit"
    priority = 1

    action {
      block {
        custom_response {
          response_code = 429
        }
      }
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "app-waf"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  resource_arn            = aws_wafv2_web_acl.main.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]

  redacted_fields {
    uri_path {}
  }

  logging_filter {
    default_behavior = "KEPT"

    filter {
      behavior   = "MATCHED"
      condition  = "EXCLUDES"
      requirement = "MEETS_ALL"

      condition_block {
        action      = "BLOCK"
        logic_operator = "OR"

        action_condition {
          action = "BLOCK"
        }
      }
    }
  }
}
```

## Best Practices

1. **Managed rules**: Use AWS Managed Rules as baseline
2. **Rate limiting**: Prevent abuse with token buckets
3. **Geo-blocking**: Restrict traffic by location
4. **Logging**: Enable detailed WAF logging
5. **Testing**: Test rules in "Count" mode first
6. **Alerting**: CloudWatch alarms on thresholds
7. **IP reputation**: Block known malicious IPs
8. **Bot control**: Detect and block bots
9. **Regex matching**: Use cautiously (CPU intensive)
10. **Regular updates**: Keep managed rules updated
