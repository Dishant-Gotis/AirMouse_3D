---
skill_name: Architecture Review Process
description: Establish RFC process, design review criteria, decision governance, and architectural decision records
category: Developer Experience
version: 1.0.0
---

# Architecture Review Process

## RFC & Review

```python
class ArchitectureReview:
    def rfc_criteria(self):
        return {
            'scope': 'Affects multiple teams or major systems',
            'reversibility': 'Hard to undo (data schema changes)',
            'risk': 'High-risk decisions',
            'cost': 'Significant resource investment'
        }

    def review_board(self):
        return {
            'tech_lead': 'Architectural expertise',
            'ic_lead': 'Implementation perspective',
            'product': 'User and business impact',
            'security': 'Security implications',
            'ops': 'Operational burden'
        }

    def decision_criteria(self):
        return {
            'scalability': 'Can this scale?',
            'maintainability': 'Can others understand this?',
            'simplicity': 'Is this the simplest solution?',
            'risk': 'What could go wrong?',
            'cost': 'Infrastructure and dev time costs',
            'deadline': 'Can we afford the timeline?'
        }

    def adr_template(self):
        """Architecture Decision Record"""
        return {
            'title': 'Short decision title',
            'status': 'Proposed | Accepted | Deprecated | Superseded',
            'context': 'What situation prompted this?',
            'decision': 'What did we decide and why?',
            'consequences': 'What are the implications?',
            'alternatives': 'What else did we consider?'
        }
```

## Production Checklist

- [ ] Establish RFC process
- [ ] Create review board
- [ ] Document decision criteria
- [ ] Create ADR template
- [ ] Store ADRs in version control
- [ ] Link ADRs from code
- [ ] Review major decisions in this process
- [ ] Keep ADRs updated
- [ ] Reference ADRs in documentation
