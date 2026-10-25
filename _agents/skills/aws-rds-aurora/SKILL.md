---
skill_name: aws-rds-aurora
description: RDS and Aurora patterns for parameter groups, read replicas, Serverless, backup strategies, and proxy
category: Cloud & DevOps
version: 1.0.0
---

# AWS RDS and Aurora

## RDS Instance Types

Choose instance types based on workload characteristics.

### Compute Optimized (c-family)
High CPU, low memory ratio. Good for OLTP, batch processing.

```bash
aws rds create-db-instance \
  --db-instance-identifier prod-mysql \
  --db-instance-class db.c5.2xlarge \
  --engine mysql \
  --allocated-storage 100 \
  --storage-type gp3 \
  --master-username admin \
  --master-user-password $(openssl rand -base64 32) \
  --enable-iam-database-authentication \
  --backup-retention-period 30
```

### Memory Optimized (r-family)
High memory for caching large datasets. Good for data warehouses.

```bash
aws rds create-db-instance \
  --db-instance-class db.r5.4xlarge \
  --engine postgres
```

### Burstable (t-family)
Low baseline with burst capacity. Good for dev/test.

```bash
aws rds create-db-instance \
  --db-instance-class db.t3.medium \
  --engine mysql
```

## Parameter Groups

Customize database configuration without modifying files.

### Create Custom Parameter Group
```bash
# Create parameter group for MySQL 8.0
aws rds create-db-parameter-group \
  --db-parameter-group-name mysql8-custom \
  --db-parameter-group-family mysql8.0 \
  --description "Custom parameters for MySQL 8.0"

# Modify parameters
aws rds modify-db-parameter-group \
  --db-parameter-group-name mysql8-custom \
  --parameters \
    ParameterName=max_connections,ParameterValue=1000,ApplyMethod=pending-reboot \
    ParameterName=slow_query_log,ParameterValue=1,ApplyMethod=immediate \
    ParameterName=long_query_time,ParameterValue=2,ApplyMethod=immediate

# View modified parameters
aws rds describe-db-parameters \
  --db-parameter-group-name mysql8-custom \
  --filters Name=isModified,Values=true
```

### Performance Tuning Parameters
```bash
# MySQL 8.0 optimized for performance
aws rds modify-db-parameter-group \
  --db-parameter-group-name mysql8-custom \
  --parameters \
    ParameterName=innodb_buffer_pool_size,ParameterValue='{DBInstanceClassMemory*3/4}' \
    ParameterName=innodb_log_file_size,ParameterValue=512M \
    ParameterName=query_cache_type,ParameterValue=1 \
    ParameterName=query_cache_size,ParameterValue=67108864
```

## Read Replicas

Scale read capacity with asynchronous replication.

### Create Read Replica (Same Region)
```bash
aws rds create-db-instance-read-replica \
  --db-instance-identifier prod-mysql-replica \
  --source-db-instance-identifier prod-mysql
```

### Create Read Replica (Different Region)
```bash
aws rds create-db-instance-read-replica \
  --db-instance-identifier prod-mysql-replica-eu \
  --source-db-instance-identifier arn:aws:rds:us-east-1:123456789012:db:prod-mysql \
  --region eu-west-1 \
  --db-instance-class db.r5.large
```

### Promote Replica to Standalone
```bash
aws rds promote-read-replica \
  --db-instance-identifier prod-mysql-replica
```

### Monitor Replica Lag
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name ReplicaLag \
  --dimensions Name=DBInstanceIdentifier,Value=prod-mysql-replica \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Average,Maximum
```

## Aurora Serverless

Auto-scaling database without managing capacity.

### Create Aurora Serverless Cluster
```bash
aws rds create-db-cluster \
  --db-cluster-identifier aurora-serverless-prod \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.02.0 \
  --database-name mydb \
  --master-username admin \
  --master-user-password $(openssl rand -base64 32) \
  --db-cluster-parameter-group-name default.aurora-mysql8.0 \
  --engine-mode serverless \
  --scaling-configuration \
    MinCapacity=0.5 \
    MaxCapacity=1 \
    AutoPause=true \
    AutoPauseSeconds=300

# Add endpoint for application connection
aws rds describe-db-clusters \
  --db-cluster-identifier aurora-serverless-prod \
  --query 'DBClusters[0].Endpoint'
```

### Aurora Provisioned Cluster
```bash
# Cluster with read replicas
aws rds create-db-cluster \
  --db-cluster-identifier aurora-prod \
  --engine aurora-postgresql \
  --master-username admin \
  --master-user-password $(openssl rand -base64 32)

# Add writer instance
aws rds create-db-instance \
  --db-instance-identifier aurora-writer \
  --db-cluster-identifier aurora-prod \
  --db-instance-class db.r5.2xlarge \
  --engine aurora-postgresql

# Add reader instances (for load distribution)
aws rds create-db-instance \
  --db-instance-identifier aurora-reader-1 \
  --db-cluster-identifier aurora-prod \
  --db-instance-class db.r5.2xlarge \
  --engine aurora-postgresql

aws rds create-db-instance \
  --db-instance-identifier aurora-reader-2 \
  --db-cluster-identifier aurora-prod \
  --db-instance-class db.r5.2xlarge \
  --engine aurora-postgresql
```

## RDS Proxy

Connection pooling for better resource utilization.

### Create Proxy
```bash
aws rds create-db-proxy \
  --db-proxy-name mysql-proxy \
  --engine-family MYSQL \
  --role-arn arn:aws:iam::123456789012:role/rds-proxy-role \
  --database-user admin \
  --database-secret-arn arn:aws:secretsmanager:us-east-1:123456789012:secret:db-password \
  --auth-scheme SECRETS \
  --max-connections 100 \
  --session-pinning-filters EXCLUDE_VARIABLE_SETS

# Get proxy endpoint
proxy_endpoint=$(aws rds describe-db-proxies \
  --db-proxy-name mysql-proxy \
  --query 'DBProxies[0].Endpoint' \
  --output text)

echo "Connect using: $proxy_endpoint"
```

### Connection Pooling Modes
- **Session mode**: Persistent connections, higher latency
- **Transaction mode**: Connections returned after transaction commit, lower overhead

```python
import pymysql
import os

# Use proxy endpoint instead of direct database endpoint
connection = pymysql.connect(
    host=os.environ['DB_PROXY_ENDPOINT'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASS'],
    database='mydb'
)

cursor = connection.cursor()
cursor.execute("SELECT * FROM users LIMIT 10")
results = cursor.fetchall()
connection.close()
```

## Backup and Recovery

### Automated Backups
```bash
aws rds modify-db-instance \
  --db-instance-identifier prod-mysql \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --apply-immediately
```

### Manual Snapshots
```bash
# Create snapshot
snapshot_id=$(aws rds create-db-snapshot \
  --db-instance-identifier prod-mysql \
  --db-snapshot-identifier prod-mysql-backup-2024-01-01 \
  --query 'DBSnapshot.DBSnapshotIdentifier' \
  --output text)

echo "Snapshot ID: $snapshot_id"

# List snapshots
aws rds describe-db-snapshots --db-instance-identifier prod-mysql

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier prod-mysql-restored \
  --db-snapshot-identifier prod-mysql-backup-2024-01-01
```

### Point-in-Time Recovery
```bash
# Restore to specific point in time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier prod-mysql \
  --target-db-instance-identifier prod-mysql-pitr \
  --restore-time 2024-01-01T12:30:00Z \
  --use-latest-restorable-time
```

## High Availability

### Multi-AZ Deployment
```bash
aws rds modify-db-instance \
  --db-instance-identifier prod-mysql \
  --multi-az \
  --apply-immediately
```

RDS automatically creates a standby replica in a different AZ. Failover is automatic on primary failure.

### Enhanced Monitoring
```bash
aws rds modify-db-instance \
  --db-instance-identifier prod-mysql \
  --enable-cloudwatch-logs-exports error,general,slowquery \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::123456789012:role/rds-monitoring-role
```

## Performance Insights

Monitor database performance in real-time.

```bash
# Enable Performance Insights
aws rds modify-db-instance \
  --db-instance-identifier prod-mysql \
  --enable-performance-insights \
  --performance-insights-retention-period 7

# Query Performance Insights
aws pi get-resource-metrics \
  --service-type RDS \
  --identifier db-instance \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period-in-seconds 60 \
  --metric-queries \
    '[{"Metric":"db.load.avg"}]'
```

## Best Practices

1. **Use Serverless for variable workloads**: No capacity management
2. **Read replicas for scaling**: Distribute read traffic
3. **RDS Proxy for connection pooling**: Reduce database overhead
4. **Multi-AZ for production**: Automatic failover
5. **Automated backups**: 30-day retention minimum
6. **Parameter groups**: Version-controlled database configuration
7. **Enhanced monitoring**: CloudWatch Logs for slow queries
8. **Performance Insights**: Identify bottlenecks
9. **Cost optimization**: Use compute-optimized for OLTP, memory-optimized for analytics
10. **Security**: Enable IAM authentication, encryption at rest/transit
