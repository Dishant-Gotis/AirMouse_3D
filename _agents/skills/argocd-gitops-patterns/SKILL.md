---
skill_name: argocd-gitops-patterns
description: argocd-gitops implementation patterns
category: DevOps & Infrastructure
version: 1.0.0
---

# argocd-gitops Patterns

Master argocd-gitops for production deployments.

## Configuration

```yaml
# Basic argocd-gitops configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-gitops-config
data:
  config.yaml: |
    enabled: true
    monitoring: enabled
```

## Implementation

```bash
# Deploy and configure
kubectl apply -f argocd-gitops-config.yaml

# Verify deployment
kubectl get pods -l app=argocd-gitops

# Check logs
kubectl logs -f deployment/argocd-gitops
```

## Monitoring

Monitor argocd-gitops health and performance:

- Setup metrics collection
- Configure alerting thresholds
- Create dashboards
- Track error rates
- Monitor resource usage

## Best Practices

- Use declarative configurations
- Implement RBAC properly
- Monitor all deployments
- Set resource limits
- Enable security policies
- Automate deployments
- Test before production
- Document configurations

