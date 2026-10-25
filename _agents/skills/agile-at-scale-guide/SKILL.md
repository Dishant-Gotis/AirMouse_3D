---
skill_name: Agile At Scale Guide
description: Scale agile methods using SAFe, LeSS, Spotify model, and choosing the right framework
category: Operations & Process
version: 1.0.0
---

# Agile At Scale Guide

## Scaling Frameworks

```python
class AgileScaling:
    def frameworks(self):
        return {
            'safe': {
                'name': 'Scaled Agile Framework',
                'for': '100+ people with high dependencies',
                'cadence': 'Program Increment (PI) every 8 weeks',
                'structure': 'Teams → Programs → Portfolio'
            },
            'less': {
                'name': 'Large-Scale Scrum',
                'for': 'Simpler at larger scale (avoid SAFe complexity)',
                'emphasis': 'Keep scrum practices, scale minimally',
                'teams': '6-9 teams max working on same product'
            },
            'spotify_model': {
                'name': 'Squad-based organization',
                'for': '50-200 people, product-based teams',
                'structure': 'Squads → Tribes → Chapters → Guilds',
                'autonomy': 'High autonomy, loose coupling'
            },
            'base_agile': {
                'for': '< 50 people',
                'note': 'Scrum works fine, don\'t over-complicate'
            }
        }

    def choosing_framework(self):
        return {
            'size': 'Company size and growth trajectory',
            'dependencies': 'How much cross-team coordination needed?',
            'culture': 'Does org embrace agile?',
            'maturity': 'Do teams understand agile?',
            'caution': 'Don\'t adopt prematurely'
        }
```

## Production Checklist

- [ ] Assess company size and needs
- [ ] Choose appropriate framework
- [ ] Train leadership on framework
- [ ] Train teams on framework
- [ ] Implement incrementally
- [ ] Measure effectiveness
- [ ] Adjust approach based on results
- [ ] Don\'t over-complicate processes
