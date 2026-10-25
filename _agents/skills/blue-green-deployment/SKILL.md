---
skill_name: blue-green-deployment
description: Blue-green deployment patterns for traffic switching, database migrations, rollback strategies, and canary
category: Cloud & DevOps
version: 1.0.0
---

# Blue-Green Deployments

## AWS ELB Blue-Green

```bash
#!/bin/bash

# Define versions
BLUE_ASG="app-asg-blue"
GREEN_ASG="app-asg-green"
TARGET_GROUP="app-targets"

# 1. Deploy GREEN version
echo "Launching GREEN environment..."
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name $GREEN_ASG \
  --launch-configuration app-lc-v2 \
  --min-size 3 \
  --max-size 10 \
  --desired-capacity 3 \
  --health-check-type ELB \
  --health-check-grace-period 300

# 2. Register GREEN targets
INSTANCE_IDS=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names $GREEN_ASG \
  --query 'AutoScalingGroups[0].Instances[*].InstanceId' \
  --output text)

for instance in $INSTANCE_IDS; do
  aws elbv2 register-targets \
    --target-group-arn $TARGET_GROUP \
    --targets Id=$instance Port=8080
done

# 3. Health check GREEN
echo "Waiting for GREEN to become healthy..."
sleep 60
HEALTHY=$(aws elbv2 describe-target-health \
  --target-group-arn $TARGET_GROUP \
  --query 'TargetHealthDescriptions[?TargetHealth.State==`healthy`] | length(@)')

if [ "$HEALTHY" -ge 3 ]; then
  echo "GREEN is healthy, switching traffic..."

  # 4. Switch traffic from BLUE to GREEN
  aws elbv2 modify-target-group \
    --target-group-arn $TARGET_GROUP \
    --health-check-interval-seconds 30

  # 5. Deregister BLUE targets
  BLUE_INSTANCES=$(aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names $BLUE_ASG \
    --query 'AutoScalingGroups[0].Instances[*].InstanceId' \
    --output text)

  for instance in $BLUE_INSTANCES; do
    aws elbv2 deregister-targets \
      --target-group-arn $TARGET_GROUP \
      --targets Id=$instance
  done

  echo "Deployment successful"
else
  echo "GREEN failed health checks, rolling back"
  aws autoscaling delete-auto-scaling-group \
    --auto-scaling-group-name $GREEN_ASG \
    --force-delete
  exit 1
fi
```

## Kubernetes Blue-Green

```yaml
---
# Blue Deployment (current)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
      version: blue
  template:
    metadata:
      labels:
        app: web
        version: blue
    spec:
      containers:
      - name: web
        image: myapp:v1.0.0
        ports:
        - containerPort: 8080

---
# Service pointing to BLUE
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: web
    version: blue  # Points to blue
  ports:
  - port: 80
    targetPort: 8080

---
# Green Deployment (new)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
      version: green
  template:
    metadata:
      labels:
        app: web
        version: green
    spec:
      containers:
      - name: web
        image: myapp:v2.0.0
        ports:
        - containerPort: 8080
```

### Switching Traffic

```bash
# Test GREEN before switching
kubectl port-forward svc/app-service-green 8080:80
curl http://localhost:8080/health

# Switch service to GREEN
kubectl patch service app-service -p '{"spec":{"selector":{"version":"green"}}}'

# Monitor for errors
kubectl logs -f deployment/app-green

# If issues detected, rollback
kubectl patch service app-service -p '{"spec":{"selector":{"version":"blue"}}}'
```

## Database Migrations

### Zero-Downtime Migration

```sql
-- 1. Create new column with default value
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;

-- 2. Backfill data in batches (non-blocking)
UPDATE users SET email_verified = true
WHERE email_verified_at IS NOT NULL
LIMIT 1000;

-- 3. Add constraint after backfill complete
ALTER TABLE users ADD CONSTRAINT check_email_verified
  CHECK (email_verified = true OR email_verified = false);

-- 4. Make column NOT NULL (if needed)
ALTER TABLE users MODIFY email_verified BOOLEAN NOT NULL;

-- 5. Drop old column after confirming data is correct
ALTER TABLE users DROP COLUMN email_verified_at;
```

### Dual-Write Pattern

```python
# During transition period, write to both databases
def update_user(user_id, email):
    # Write to old system
    old_db.users.update(user_id, {'email': email})

    # Write to new system
    new_db.users.update(user_id, {'email': email})

    return user_id
```

## Monitoring & Rollback

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: deployment-health
spec:
  groups:
  - name: deployment-metrics
    interval: 30s
    rules:
    - alert: HighErrorRateOnNewVersion
      expr: |
        rate(http_requests_total{version="green",status=~"5.."}[5m]) > 0.05
      for: 5m
      annotations:
        summary: "Green version has high error rate"
        action: "Rollback to blue"
```

### Automatic Rollback Script

```bash
#!/bin/bash

ERROR_THRESHOLD=0.05
WINDOW=300  # 5 minutes

while true; do
  # Get error rate for GREEN
  ERROR_RATE=$(kubectl get pods -l version=green -o json | \
    jq '.items | length' | xargs -I {} kubectl top pods -l version=green --sort-by=memory)

  if (( $(echo "$ERROR_RATE > $ERROR_THRESHOLD" | bc -l) )); then
    echo "Error rate $ERROR_RATE exceeds $ERROR_THRESHOLD"
    kubectl patch service app-service -p '{"spec":{"selector":{"version":"blue"}}}'
    echo "Rolled back to BLUE"
    exit 0
  fi

  sleep 30
done
```

## Best Practices

1. **Health checks**: Comprehensive health checks before switching
2. **Gradual traffic shift**: Use weighted routing if supported
3. **Database compatibility**: Ensure schema works with both versions
4. **Monitoring**: Real-time error rate tracking
5. **Automated rollback**: Trigger on metrics threshold
6. **Database migration**: Use dual-write during transition
7. **Parallel testing**: Test green thoroughly before switch
8. **Documentation**: Rollback procedures well-documented
9. **Timing**: Deploy during low-traffic windows
10. **Validation**: Sanity checks after switching
