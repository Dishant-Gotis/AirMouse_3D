---
skill_name: Board Deck Template & Presentation
description: Financial summary, strategic update, decisions needed, metrics review
category: Specialized Finance
version: 1.0.0
---

# Board Deck Template & Presentation

## Overview
Board meetings require focused narratives. Master structure and storytelling.

## Deck Structure

```python
class BoardDeck:
    def __init__(self):
        self.slides = []

    def standard_structure(self):
        """15-20 slides"""
        return {
            'slide_1': 'Cover: Company, date, agenda',
            'slide_2': 'Financial summary: Revenue, burn, runway',
            'slide_3': 'Key metrics dashboard',
            'slide_4': 'Strategic narrative: Where we are',
            'slide_5': 'Market opportunity',
            'slide_6': 'Product roadmap',
            'slide_7': 'Customer traction / case studies',
            'slide_8': 'Team highlights',
            'slide_9': 'Financials (detailed)',
            'slide_10': 'Fundraising ask (if applicable)',
            'slide_11': 'Decisions needed from board',
            'slide_12': 'Q&A'
        }

# Usage
deck = BoardDeck()
structure = deck.standard_structure()
print(f"Typical deck: {len(structure)} slides")
```

## Production Checklist

- [ ] Create quarterly board deck
- [ ] Include financial metrics
- [ ] Report on strategic initiatives
- [ ] Highlight customer wins
- [ ] Share team updates
- [ ] Request board decisions
- [ ] Practice presentation
- [ ] Address known concerns
