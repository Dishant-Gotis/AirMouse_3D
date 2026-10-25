---
skill_name: AWS Well-Architected Framework
description: Apply 6 pillars (operational excellence, security, reliability, performance, cost, sustainability) to AWS workloads
category: DevOps & SRE
version: 1.0.0
---

# AWS Well-Architected Framework

## Overview
The Well-Architected Framework provides best practices across 6 pillars. Learn the review process and remediation patterns.

## Six Pillars Overview

### Pillar 1: Operational Excellence

```python
class OperationalExcellence:
    def __init__(self):
        self.principles = []

    def design_principles(self):
        """Operational excellence practices"""
        return {
            'infrastructure_as_code': 'CloudFormation, Terraform, CDK',
            'annotate_documentation': 'Why decisions were made',
            'monitor_and_alert': 'CloudWatch, X-Ray, EventBridge',
            'improve_procedures': 'Run books, game days, feedback loops',
            'anticipate_failure': 'Design for worst case scenarios'
        }

    def aws_services(self):
        """Key services"""
        return [
            'CloudFormation (IaC)',
            'Systems Manager (automation)',
            'CloudWatch (monitoring)',
            'AWS X-Ray (tracing)',
            'Config (compliance)',
            'CloudTrail (audit)'
        ]

    def maturity_model(self):
        """Progression levels"""
        return {
            'reactive': 'Respond to issues as they occur',
            'proactive': 'Monitor and prevent issues',
            'automated': 'Self-healing systems',
            'optimized': 'Continuous improvement built-in'
        }

# Usage
oe = OperationalExcellence()
print(f"Services: {oe.aws_services()}")
```

### Pillar 2: Security

```python
class Security:
    def __init__(self):
        self.controls = []

    def design_principles(self):
        """Security best practices"""
        return {
            'least_privilege': 'IAM roles with minimal permissions',
            'defense_in_depth': 'Multiple layers (VPC, SG, WAF, etc)',
            'encryption': 'Data at rest and in transit',
            'logging': 'CloudTrail, VPC Flow Logs, ALB Logs',
            'incident_response': 'Automated and manual procedures'
        }

    def aws_services(self):
        """Security services"""
        return [
            'IAM (identity)',
            'KMS (encryption)',
            'Secrets Manager (secrets)',
            'VPC (network isolation)',
            'Security Groups (firewall)',
            'WAF (web firewall)',
            'GuardDuty (threat detection)',
            'Config (compliance)',
            'SSM Parameter Store'
        ]

    def security_controls(self):
        """Control types"""
        return {
            'preventive': 'Stop bad things from happening (IAM deny)',
            'detective': 'Detect when bad things happen (GuardDuty)',
            'responsive': 'Respond to incidents (Lambda auto-remediation)',
            'preventative': 'Prevent recurrence (AWS Config rules)'
        }

# Usage
sec = Security()
print(f"Principles: {sec.design_principles()}")
```

### Pillar 3: Reliability

```python
class Reliability:
    def __init__(self):
        self.practices = []

    def design_principles(self):
        """High availability and disaster recovery"""
        return {
            'fault_isolation': 'Use multiple AZs and regions',
            'auto_recovery': 'Auto Scaling, health checks',
            'capacity_planning': 'Monitor and scale proactively',
            'change_management': 'Gradual deployments, canary releases',
            'failure_management': 'Chaos engineering, game days'
        }

    def rpo_rto(self):
        """Recovery objectives"""
        return {
            'rto_minutes': {
                'critical': 15,
                'high': 60,
                'medium': 240,
                'low': 1440
            },
            'rpo_minutes': {
                'critical': 5,
                'high': 30,
                'medium': 60,
                'low': 480
            }
        }

    def aws_services(self):
        """Reliability services"""
        return [
            'EC2 Auto Scaling',
            'Application Load Balancer',
            'Route 53 (health checks)',
            'RDS Multi-AZ',
            'DynamoDB DAX',
            'S3 Cross-Region Replication',
            'Backup (automated snapshots)',
            'SNS/SQS (decoupling)'
        ]

# Usage
rel = Reliability()
targets = rel.rpo_rto()
print(f"Critical RTO: {targets['rto_minutes']['critical']} min")
```

### Pillar 4: Performance Efficiency

```python
class PerformanceEfficiency:
    def __init__(self):
        self.patterns = []

    def design_principles(self):
        """Optimal resource utilization"""
        return {
            'use_managed_services': 'Lambda, DynamoDB vs self-managed',
            'serverless': 'Pay per use, no capacity planning',
            'caching': 'CloudFront, ElastiCache, DAX',
            'select_right_tool': 'RDS vs NoSQL, EBS vs EFS',
            'go_global': 'Multi-region, CDN distribution'
        }

    def scaling_patterns(self):
        """Horizontal and vertical scaling"""
        return {
            'horizontal': 'Add more instances (Auto Scaling)',
            'vertical': 'Larger instances (RDS upgrade)',
            'caching': 'Cache frequently accessed data',
            'read_replicas': 'Scale read workloads separately'
        }

    def aws_services(self):
        """Performance services"""
        return [
            'CloudFront (CDN)',
            'ElastiCache (in-memory cache)',
            'DynamoDB DAX',
            'RDS Read Replicas',
            'Lambda (serverless)',
            'CloudFront Lambda@Edge',
            'S3 Transfer Acceleration',
            'AWS Glue (ETL optimization)'
        ]

# Usage
perf = PerformanceEfficiency()
print(f"Services: {perf.aws_services()}")
```

### Pillar 5: Cost Optimization

```python
class CostOptimization:
    def __init__(self):
        self.strategies = []

    def design_principles(self):
        """Cost efficiency"""
        return {
            'right_sizing': 'Match instance size to workload',
            'pricing_models': 'On-demand, Reserved, Spot instances',
            'managed_services': 'Pay per use vs self-managed overhead',
            'monitor_usage': 'CloudWatch, Cost Explorer, Trusted Advisor',
            'shared_resources': 'Consolidate non-critical workloads'
        }

    def cost_reduction_strategies(self):
        """Techniques to reduce spend"""
        return {
            'ri_savings': 'Reserved instances: 40% discount, 1-3 yr commitment',
            'spot_instances': 'Up to 90% discount, interruptible',
            'savings_plans': 'Flexible commitment across services',
            'right_size': 'Monitor and downsize over-provisioned resources',
            'terminate': 'Kill unused resources (unused RDS, old EBS)'
        }

    def aws_services(self):
        """Cost visibility"""
        return [
            'Cost Explorer',
            'Budgets (alerts)',
            'Trusted Advisor',
            'AWS Compute Optimizer',
            'Reserved Instance Marketplace',
            'Spot Instance Advisor'
        ]

# Usage
cost = CostOptimization()
print(f"RI savings: {cost.cost_reduction_strategies()['ri_savings']}")
```

### Pillar 6: Sustainability

```python
class Sustainability:
    def __init__(self):
        self.practices = []

    def design_principles(self):
        """Environmental responsibility"""
        return {
            'energy_efficiency': 'Use managed services, reduce idle compute',
            'cloud_efficiency': 'Consolidate workloads, shared infrastructure',
            'right_sizing': 'Avoid over-provisioning and waste',
            'managed_services': 'AWS reduces physical infrastructure overhead',
            'monitoring': 'Track carbon footprint'
        }

    def aws_services(self):
        """Sustainability services"""
        return [
            'AWS Sustainability Center',
            'Compute Optimizer (recommend right-size)',
            'Lambda (inherently efficient)',
            'EBS (optimize snapshots)',
            'CloudFront (cache reduces origin traffic)'
        ]

# Usage
sustainability = Sustainability()
print(f"Principles: {sustainability.design_principles()}")
```

## Well-Architected Review Process

### Review Framework

```python
class WellArchitectedReview:
    def __init__(self, workload_name):
        self.workload = workload_name
        self.findings = []
        self.risk_level = {}

    def assessment(self, pillar, question, current_state):
        """Assess against best practice"""
        return {
            'pillar': pillar,
            'question': question,
            'current_state': current_state,
            'best_practice': 'documented_approach',
            'gap': 'difference between current and best',
            'risk_level': 'High/Medium/Low',
            'recommendation': 'specific_action'
        }

    def prioritize_findings(self):
        """Order by impact and effort"""
        return sorted(
            self.findings,
            key=lambda x: (
                -self._risk_score(x['risk_level']),  # Higher risk first
                x.get('effort', 3)  # Lower effort preferred
            )
        )

    def _risk_score(self, level):
        """Convert risk level to score"""
        return {'High': 3, 'Medium': 2, 'Low': 1}.get(level, 0)

# Usage
review = WellArchitectedReview("e-commerce-platform")
```

## Remediation Patterns

### Common Fixes by Pillar

```python
class RemediationPatterns:
    def __init__(self):
        self.patterns = {}

    def operational_excellence_fixes(self):
        """Common operational issues"""
        return {
            'no_iac': 'Migrate to CloudFormation/CDK',
            'manual_processes': 'Automate with Systems Manager/Lambda',
            'no_monitoring': 'Implement CloudWatch dashboards/alarms',
            'no_logging': 'Enable CloudTrail, VPC Flow Logs'
        }

    def security_fixes(self):
        """Common security issues"""
        return {
            'too_permissive': 'Apply least privilege IAM policies',
            'no_encryption': 'Enable KMS encryption at rest',
            'no_ssl': 'Require HTTPS, use ACM certificates',
            'exposed_secrets': 'Use Secrets Manager instead of env vars'
        }

    def reliability_fixes(self):
        """Common reliability issues"""
        return {
            'single_az': 'Deploy to multiple AZs',
            'no_backup': 'Enable automated backups',
            'no_health_checks': 'Add health check endpoints',
            'manual_failover': 'Implement Route 53 health checks'
        }

# Usage
patterns = RemediationPatterns()
print(f"Ops fixes: {patterns.operational_excellence_fixes()}")
```

## Production Checklist

- [ ] Conduct Well-Architected Review annually
- [ ] Implement all High-risk recommendations
- [ ] Track Medium-risk items in backlog
- [ ] Enable AWS Trusted Advisor checks
- [ ] Set up CloudWatch dashboards for monitoring
- [ ] Document architectural decisions
- [ ] Implement cost optimization tagging
- [ ] Enable multi-AZ deployment for critical workloads
- [ ] Encrypt data at rest and in transit
- [ ] Implement automated backup/restore procedures
- [ ] Use Infrastructure as Code for all resources
- [ ] Conduct quarterly reviews of recommendations
