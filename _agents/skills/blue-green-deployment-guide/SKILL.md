---
skill_name: Blue-Green Deployment Strategy
description: Implement zero-downtime deployments with load balancer switching, database migration, and instant rollback
category: DevOps & SRE
version: 1.0.0
---

# Blue-Green Deployment Strategy

## Overview
Blue-Green deployments run two identical production environments. Switch traffic instantly with zero downtime and immediate rollback capability.

## Architecture Overview

### Blue-Green Setup

```python
class BlueGreenArchitecture:
    def __init__(self, service_name):
        self.service = service_name
        self.blue_env = {}
        self.green_env = {}
        self.load_balancer = None

    def environment_structure(self):
        """Identical environments"""
        return {
            'blue': {
                'instances': 3,
                'version': 'v1.2.3',
                'status': 'active',
                'traffic_percent': 100
            },
            'green': {
                'instances': 3,
                'version': 'v1.3.0',
                'status': 'standby',
                'traffic_percent': 0
            },
            'load_balancer': 'Directs traffic based on active env',
            'database': 'Shared (requires migration strategy)'
        }

    def traffic_switching(self):
        """Route all traffic to new version"""
        return {
            'method_1_dns': 'Update CNAME to point to new environment',
            'method_2_lb': 'Update load balancer target group',
            'method_3_router': 'Update application router configuration',
            'switch_time': '< 1 second',
            'impact': 'Instant, all users switched simultaneously'
        }

    def cost_consideration(self):
        """Double infrastructure during deployment"""
        return {
            'during_deployment': '2x normal cost (both envs running)',
            'typical_duration': '5-30 minutes',
            'additional_cost': 'Small percentage of infrastructure spend',
            'benefit': 'Zero downtime, instant rollback justifies cost'
        }

# Usage
architecture = BlueGreenArchitecture("payment-service")
print(f"Traffic switch time: {architecture.traffic_switching()['switch_time']}")
```

### Pre-Deployment Checklist

```python
class PreDeploymentChecklist:
    def __init__(self):
        self.checks = []

    def validation_steps(self):
        """Before switching traffic"""
        return {
            'smoke_tests': [
                'Health check endpoints return 200',
                'Critical business flows work',
                'Database queries execute',
                'External APIs respond'
            ],
            'performance_baseline': [
                'Response times acceptable',
                'CPU/memory utilization normal',
                'No error rate increase',
                'Throughput matches Blue'
            ],
            'security_checks': [
                'SSL certificate valid',
                'Security headers present',
                'No sensitive data leaks',
                'Firewall rules correct'
            ],
            'database_ready': [
                'All migrations executed',
                'Data consistency verified',
                'Rollback plan documented',
                'Backups taken'
            ]
        }

    def canary_testing(self):
        """Test Green with real traffic first"""
        return {
            'method': 'Send small % of traffic to Green',
            'percent_range': '1-10% initially',
            'duration': '5-30 minutes',
            'monitoring': 'Error rates, latency, business metrics',
            'decision': 'If good -> increase; if bad -> rollback'
        }

    def load_test(self):
        """Verify Green handles production load"""
        return {
            'approach': 'Replay production traffic to Green',
            'duration': '10-30 minutes',
            'metrics': 'p50, p95, p99 latency, error rate',
            'pass_criteria': 'Match or improve Blue performance'
        }

# Usage
checklist = PreDeploymentChecklist()
print(f"Canary: {checklist.canary_testing()}")
```

## Database Migration Strategy

### Stateless vs Stateful Apps

```python
class DatabaseMigration:
    def __init__(self, app_type='stateless'):
        self.app_type = app_type

    def stateless_migration(self):
        """Application doesn't hold state (standard)"""
        return {
            'advantage': 'Single database shared across Blue/Green',
            'process': [
                '1. Run schema migrations on shared DB',
                '2. Deploy Green with new code',
                '3. Run smoke tests against shared DB',
                '4. Switch traffic to Green',
                '5. Verify no errors'
            ],
            'rollback': 'Switch traffic back to Blue',
            'rollback_risk': 'Low if migrations were backward compatible'
        }

    def stateful_migration(self):
        """Database changes need careful coordination"""
        return {
            'challenge': 'New schema may break old code version',
            'approach': [
                '1. Expand schema (add new columns, not remove old)',
                '2. Deploy Green that writes new columns',
                '3. Verify Green works with old Blue writing old columns',
                '4. Switch traffic to Green',
                '5. Deploy cleanup job to migrate old data'
            ],
            'example': 'Adding required column with default value',
            'dangerous': 'Removing column while Blue still needs it'
        }

    def zero_downtime_migration(self):
        """Expand-then-contract pattern"""
        return {
            'phase_1_expand': {
                'step': 'Add new column, trigger, or table',
                'backward_compatible': True,
                'old_code_works': True,
                'new_code_works': True
            },
            'phase_2_deploy': {
                'step': 'Deploy new code that uses new column',
                'can_rollback': True,
                'switch_traffic': True
            },
            'phase_3_cleanup': {
                'step': 'Remove old column in future deploy',
                'only_after': 'All old code retired',
                'low_risk': True
            }
        }

# Usage
migration = DatabaseMigration('stateless')
print(f"Process: {migration.stateless_migration()['process']}")
```

### Example: User Table Migration

```python
class UserTableMigration:
    def __init__(self):
        self.migration_steps = []

    def scenario(self):
        """Rename 'password_hash' to 'password_hashed'"""
        return {
            'old_schema': {
                'id': 'INT',
                'email': 'VARCHAR',
                'password_hash': 'VARCHAR'
            },
            'new_schema': {
                'id': 'INT',
                'email': 'VARCHAR',
                'password_hash': 'VARCHAR (deprecated)',
                'password_hashed': 'VARCHAR (new)'
            }
        }

    def migration_plan(self):
        """Safe rename procedure"""
        return {
            'step_1': {
                'action': 'Add new column password_hashed',
                'sql': 'ALTER TABLE users ADD COLUMN password_hashed VARCHAR',
                'time': 'Pre-deployment',
                'risk': 'Low (additive)'
            },
            'step_2': {
                'action': 'Deploy Green code',
                'code': 'Read/write to password_hashed only',
                'fallback': 'Falls back to password_hash if needed',
                'risk': 'Medium (dual-write logic)'
            },
            'step_3': {
                'action': 'Backfill existing data',
                'sql': 'UPDATE users SET password_hashed = password_hash',
                'duration': 'Depending on table size',
                'time': 'During or after traffic switch'
            },
            'step_4': {
                'action': 'Drop old column',
                'sql': 'ALTER TABLE users DROP COLUMN password_hash',
                'time': 'After all old code retired',
                'risk': 'Low (Blue already switched off)'
            }
        }

# Usage
migration = UserTableMigration()
print(f"Scenario: {migration.scenario()}")
```

## Traffic Switching Implementation

### Load Balancer Configuration

```python
# AWS Application Load Balancer example
class LoadBalancerSwitch:
    def __init__(self):
        self.target_groups = {}

    def alb_target_groups(self):
        """ALB routes to target groups"""
        return {
            'blue_tg': {
                'name': 'app-blue',
                'targets': ['i-0123456789', 'i-0987654321', 'i-1111111111'],
                'health_check': '/health'
            },
            'green_tg': {
                'name': 'app-green',
                'targets': ['i-2222222222', 'i-3333333333', 'i-4444444444'],
                'health_check': '/health'
            },
            'listener_rule': {
                'condition': 'Host: api.example.com',
                'forward_to': 'blue_tg (initially)'
            }
        }

    def switch_procedure(self):
        """Change active target group"""
        return {
            'method': 'Update listener rule to point to green_tg',
            'command': 'Update ALB rule Target Group',
            'time': '< 1 second',
            'verification': 'Send test requests, verify routing'
        }

    def dns_based_switch(self):
        """DNS approach (simpler but slower propagation)"""
        return {
            'blue_dns': 'blue.api.example.com -> Blue IP',
            'green_dns': 'green.api.example.com -> Green IP',
            'main_dns': 'api.example.com -> blue.api.example.com (CNAME)',
            'switch': 'Change CNAME to point to green.api.example.com',
            'time': 'DNS TTL (5 min to 24 hours)',
            'disadvantage': 'Slower than load balancer'
        }

# Usage
lb = LoadBalancerSwitch()
print(f"Switch time: {lb.switch_procedure()['time']}")
```

## Rollback Strategy

### Instant Rollback

```python
class RollbackStrategy:
    def __init__(self):
        self.decision_criteria = []

    def automatic_rollback_triggers(self):
        """Conditions that trigger automatic rollback"""
        return {
            'error_rate': {
                'threshold': 'Error rate > 1% (vs Blue baseline)',
                'duration': '1 minute of sustained high errors',
                'action': 'Switch traffic back to Blue'
            },
            'latency': {
                'threshold': 'p95 latency > 150% of Blue p95',
                'duration': '2 minutes sustained',
                'action': 'Switch back to Blue'
            },
            'business_metric': {
                'threshold': 'Conversion rate down >5% vs baseline',
                'duration': '5 minute check',
                'action': 'Manual review, likely rollback'
            },
            'dependency': {
                'threshold': 'Critical dependency fails',
                'duration': 'Immediate',
                'action': 'Rollback to Blue'
            }
        }

    def manual_rollback(self):
        """Human-initiated rollback"""
        return {
            'trigger': 'Incident commander decides to rollback',
            'procedure': [
                '1. Assess severity',
                '2. Open incident channel',
                '3. Update listener rule to Blue',
                '4. Verify traffic on Blue',
                '5. Notify stakeholders',
                '6. Disable Green to prevent accidental switch'
            ],
            'time': '< 5 minutes total',
            'impact': 'Users on Green resume Blue behavior'
        }

    def post_rollback(self):
        """After rollback decision"""
        return {
            'investigation': 'Root cause analysis on failed Green',
            'fix': 'Fix bug and redeploy',
            'retest': 'Extended smoke/load tests before retry',
            'communication': 'Post-incident review with full team'
        }

# Usage
rollback = RollbackStrategy()
print(f"Auto rollback triggers: {rollback.automatic_rollback_triggers()}")
```

## Production Checklist

- [ ] Maintain two identical production environments (Blue/Green)
- [ ] Version all application code and database schema
- [ ] Automate database schema migrations with rollback
- [ ] Use backward-compatible migration patterns
- [ ] Implement comprehensive health checks for smoke testing
- [ ] Load test Green environment before traffic switch
- [ ] Set up automated rollback triggers (error rate, latency)
- [ ] Document traffic switching procedure step-by-step
- [ ] Create runbook for manual rollback scenarios
- [ ] Monitor Green for first 5 minutes post-switch
- [ ] Keep Blue running for at least 30 minutes after switch
- [ ] Review and document all Blue-Green deployments
