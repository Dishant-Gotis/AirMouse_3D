---
skill_name: aws-route53-dns
description: Route53 patterns for hosted zones, record types, health checks, and routing policies
category: Cloud & DevOps
version: 1.0.0
---

# AWS Route53 DNS

## Hosted Zones

Create and manage DNS records for your domains.

### Create Hosted Zone
```bash
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference unique-id-$(date +%s) \
  --hosted-zone-config Comment="Production zone"

# Get hosted zone details
zone_id=$(aws route53 list-hosted-zones-by-name \
  --dns-name example.com \
  --query 'HostedZones[0].Id' \
  --output text | cut -d'/' -f3)

echo "Zone ID: $zone_id"
```

### Update Nameservers at Registrar
```bash
# Get Route53 nameservers
aws route53 get-hosted-zone --id $zone_id \
  --query 'DelegationSet.NameServers' \
  --output table
```

Update your domain registrar to use these 4 nameservers.

## Record Types

### A Record (IPv4)
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.1"}]
      }
    }]
  }'
```

### AAAA Record (IPv6)
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "AAAA",
        "TTL": 300,
        "ResourceRecords": [{"Value": "2001:0db8:85a3:0000:0000:8a2e:0370:7334"}]
      }
    }]
  }'
```

### CNAME Record (Alias)
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "www.example.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "example.com"}]
      }
    }]
  }'
```

### Alias Record (AWS Resources)
No TTL or charges for queries:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "d111111abcdef8.cloudfront.net",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

### MX Record (Mail)
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "MX",
        "TTL": 300,
        "ResourceRecords": [
          {"Value": "10 mail1.example.com"},
          {"Value": "20 mail2.example.com"}
        ]
      }
    }]
  }'
```

### TXT Record (DKIM, SPF)
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "_dmarc.example.com",
        "Type": "TXT",
        "TTL": 300,
        "ResourceRecords": [{"Value": "\"v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com\""}]
      }
    }]
  }'
```

## Routing Policies

Route traffic based on different criteria.

### Simple Routing
Routes all traffic to a single resource:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.1"}]
      }
    }]
  }'
```

### Weighted Routing
Distribute traffic by percentage:

```bash
# 70% to primary
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "Primary",
        "Weight": 70,
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.1"}]
      }
    }]
  }'

# 30% to secondary
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "Secondary",
        "Weight": 30,
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.2"}]
      }
    }]
  }'
```

### Latency-Based Routing
Route to nearest region:

```bash
# US region
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "US-East",
        "Region": "us-east-1",
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.1"}]
      }
    }]
  }'

# Europe region
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "EU-West",
        "Region": "eu-west-1",
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.2"}]
      }
    }]
  }'
```

### Failover Routing
Active-passive failover:

```bash
# Primary
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "Primary",
        "Failover": "PRIMARY",
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.1"}],
        "HealthCheckId": "abcd1234-1234-1234-1234-123456789012"
      }
    }]
  }'

# Secondary (passive)
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "Secondary",
        "Failover": "SECONDARY",
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.2"}]
      }
    }]
  }'
```

### Geolocation Routing
Route by user location:

```bash
# Default (all other countries)
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "A",
        "SetIdentifier": "Default",
        "GeoLocation": {"CountryCode": "*"},
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.1"}]
      }
    }]
  }'

# US only
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "A",
        "SetIdentifier": "US",
        "GeoLocation": {"CountryCode": "US"},
        "TTL": 300,
        "ResourceRecords": [{"Value": "192.0.2.2"}]
      }
    }]
  }'
```

## Health Checks

Monitor endpoint health for failover.

### HTTP Health Check
```bash
aws route53 create-health-check \
  --health-check-config \
    IPAddress=192.0.2.1 \
    Port=80 \
    Type=HTTP \
    ResourcePath=/health \
    FullyQualifiedDomainName=api.example.com \
    RequestInterval=30 \
    FailureThreshold=3

# Get health check ID
health_check_id=$(aws route53 list-health-checks \
  --query 'HealthChecks[0].Id' \
  --output text)
```

### CloudWatch Health Check
Monitor custom metrics:

```bash
aws route53 create-health-check \
  --health-check-config \
    Type=CLOUDWATCH_METRIC \
    AlarmIdentifier='{Region=us-east-1,Name=api-latency-alarm}' \
    InsufficientDataHealthStatus=Healthy
```

### Calculated Health Check
Combine multiple health checks:

```bash
aws route53 create-health-check \
  --health-check-config \
    Type=CALCULATED \
    ChildHealthChecks=[check1,check2,check3] \
    HealthThreshold=2  # At least 2 must be healthy
```

## Monitoring and Logging

### Query Logging
Log all DNS queries:

```bash
aws route53 create-query-logging-config \
  --hosted-zone-id $zone_id \
  --cloud-watch-logs-log-group-arn arn:aws:logs:us-east-1:123456789012:log-group:/aws/route53/example.com

# View logs
aws logs tail /aws/route53/example.com --follow
```

### Health Check Monitoring
```bash
# Get health check status
aws route53 get-health-check-status \
  --health-check-id $health_check_id

# Watch health check metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Route53 \
  --metric-name HealthCheckStatus \
  --dimensions Name=HealthCheckId,Value=$health_check_id \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Average
```

## Batch Updates

Update multiple records efficiently:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id $zone_id \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "TTL": 300,
          "ResourceRecords": [{"Value": "192.0.2.1"}]
        }
      },
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "www.example.com",
          "Type": "A",
          "TTL": 300,
          "ResourceRecords": [{"Value": "192.0.2.2"}]
        }
      },
      {
        "Action": "DELETE",
        "ResourceRecordSet": {
          "Name": "old.example.com",
          "Type": "A",
          "TTL": 300,
          "ResourceRecords": [{"Value": "192.0.2.99"}]
        }
      }
    ]
  }'
```

## Best Practices

1. **Use Alias records**: No query charges, health check support
2. **Enable query logging**: Audit DNS changes and troubleshoot
3. **Health checks**: Monitor all critical endpoints
4. **TTL strategy**: Short TTL (300s) for frequently changing records, long TTL (3600s) for static records
5. **Separate zones**: Use subdomains for different environments
6. **Failover**: Always have a secondary endpoint
7. **Latency routing**: Improve performance with region-based routing
8. **Geolocation**: Comply with regulations (GDPR, CCPA)
