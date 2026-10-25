---
skill_name: Ad Creative Frameworks
description: Master hook formulas, body copy patterns, CTA structures, UGC, and testimonial ads for high-performing creative
category: Paid Advertising
version: 1.0.0
---

# Ad Creative Frameworks

## Overview
Creative makes or breaks campaigns. Master proven hook formulas, copy patterns, and ad structures to create ads that stop the scroll.

## Hook Frameworks

### Proven Attention-Grabbers

```yaml
The Problem Hook:
  Format: "Are you [struggling with problem]?"
  Mechanism: Speaks to pain point directly
  Examples:
    - "Are you wasting 10 hours per week on email?"
    - "Tired of low conversion rates on your landing pages?"
    - "Is your team struggling with project management?"
  When to use: Direct problem solutions (software, services)

The Curiosity Gap Hook:
  Format: "This one [thing] will change how you [benefit]"
  Mechanism: Creates desire to learn more
  Examples:
    - "This one metric will transform your marketing"
    - "This 5-minute habit saved me $10,000/year"
    - "This simple trick increased our sales by 40%"
  When to use: When you have a surprising insight
  Warning: Avoid clickbait (must deliver on promise)

The Question Hook:
  Format: "[Specific question related to benefit]?"
  Mechanism: Engages user to think about their situation
  Examples:
    - "What if you could save 20 hours per week?"
    - "Wouldn't you like to know the #1 mistake in SEO?"
    - "Do you know why most landing pages fail?"
  When to use: Educational content, thought leadership

The Visual Shock Hook:
  Format: Unexpected visual, headline follows
  Mechanism: Visual stops scroll, copy explains
  Examples:
    - "Before/after image" (transformation)
    - "This product did what?!" (unexpected result)
    - "Never use [method] again" (against common practice)
  When to use: Transformation, product benefits

The Social Proof Hook:
  Format: "[Number of] people are [result]"
  Mechanism: FOMO + proof of effectiveness
  Examples:
    - "10,000+ companies saved $1M using this"
    - "50,000+ students passed the exam with us"
    - "Join the 100K+ people who quit their jobs using this"
  When to use: When you have impressive numbers

The Contradiction Hook:
  Format: "You've been doing [wrong thing] your whole life"
  Mechanism: Challenges belief, curiosity to learn correct way
  Examples:
    - "Everything you know about dieting is wrong"
    - "Your morning routine is killing your productivity"
    - "Most marketers waste 70% of their ad budget"
  When to use: Contrarian positioning, habit change
  Warning: Must be true, not exaggerated

The Benefit Hook:
  Format: "[Direct benefit] without [pain point]"
  Mechanism: Promise of pain relief
  Examples:
    - "Get fit without going to the gym"
    - "Make $100K/year without leaving your house"
    - "Learn Chinese without boring textbooks"
  When to use: Direct, benefit-focused selling

The Story Hook:
  Format: Start with scenario, reveal solution
  Mechanism: Relatability, narrative engagement
  Examples:
    - "Last week I had $2 in my bank account..."
    - "My boss said I wasn't management material..."
    - "I tried 47 diets before discovering this..."
  When to use: Personal transformation, emotional appeal
```

## Body Copy Patterns

### Building on the Hook

```python
class BodyCopyStructure:
    def __init__(self):
        self.patterns = {}

    def aida_formula(self):
        """Classic advertising framework"""
        return {
            "attention": "Hook (above)",
            "interest": "Why this matters (1-2 sentences)",
            "desire": "Benefits and unique value (what makes this special)",
            "action": "Clear CTA (tell them what to do)"
        }

    def problem_agitate_solve(self):
        """PAS framework"""
        return {
            "problem": "State specific problem (resonance)",
            "agitate": "Make problem feel worse (emotional trigger)",
            "solve": "Show how product solves it",
            "example": {
                "problem": "You spend 2 hours daily on email",
                "agitate": "That's 500 hours per year you'll never get back",
                "solve": "Our AI automates 80% of emails, saving you 25 hours/month",
                "cta": "Try free for 14 days"
            }
        }

    def before_after_bridge(self):
        """Compare old way vs new way"""
        return {
            "before": "Describe old situation (relatable pain)",
            "after": "Describe transformed situation (aspirational)",
            "bridge": "How they get from before to after",
            "example": {
                "before": "Struggling with scattered data across 10 tools",
                "after": "All data in one dashboard, decisions in minutes",
                "bridge": "Our unified platform integrates everything",
                "cta": "See demo"
            }
        }

    def feature_benefit_pattern(self):
        """Translate features to benefits"""
        return {
            "feature": "What the product is/does (technical)",
            "benefit": "What the user gains (emotional, practical)",
            "examples": [
                ("Feature", "Benefit"),
                ("Mobile app", "Access anywhere, anytime"),
                ("AI-powered", "Saves you 10 hours per week"),
                ("Integrates with 500+ tools", "Works with tools you already use"),
                ("24/7 support", "Help when you need it, never feel alone")
            ]
        }

    def short_form_body_copy(self):
        """For mobile ads, social ads (2-3 sentence max)"""
        return {
            "length": "2-3 sentences or 50-100 characters",
            "structure": "Hook + benefit + CTA",
            "example": "Stop wasting 10 hours on email. Our AI does it for you. Free 14-day trial.",
            "platform": "Facebook, Instagram, TikTok, Twitter"
        }

    def long_form_body_copy(self):
        """For landing pages, email, detailed ads"""
        return {
            "length": "150-300 words ideal",
            "structure": "Problem → Agitate → Solve → Social Proof → CTA",
            "tactics": [
                "Specific numbers (not 'many people', say '87% of marketers')",
                "Real examples (story-based)",
                "Objection handling ('You might be thinking...')",
                "Urgency (limited time, scarcity)"
            ],
            "platform": "Landing pages, Google Ads, long-form ads"
        }
```

## CTA Frameworks

### Calls to Action That Convert

```yaml
CTA Types:

Learn More / Discover:
  - Copy: "Learn how", "See how", "Discover the trick"
  - Best for: Awareness, education
  - Risk: Vague, low conversion

Try Now / Test Drive:
  - Copy: "Try free for 30 days", "Start my free trial"
  - Best for: SaaS, freemium services
  - Conversion: High (low barrier)

Buy Now / Get Instant Access:
  - Copy: "Buy now", "Get instant access", "Claim your copy"
  - Best for: Products, courses
  - Conversion: Medium-high

Sign Up / Join:
  - Copy: "Join 50,000+", "Sign up free", "Create account"
  - Best for: Communities, apps, email lists
  - Conversion: High (free, low commitment)

Get My [Resource]:
  - Copy: "Get my checklist", "Download the guide"
  - Best for: Guides, templates, lead magnets
  - Conversion: Very high (free, valuable)

Schedule a Demo / Consultation:
  - Copy: "Schedule a 20-min demo", "Book your free consultation"
  - Best for: B2B sales, services
  - Conversion: Low-medium (high commitment)

Shop Now / Browse:
  - Copy: "Shop now", "Browse collection"
  - Best for: E-commerce
  - Conversion: Medium (product-dependent)

CTA Button Best Practices:
  - Action verb (not "Submit" or "Continue")
  - Benefit-driven when possible
  - Create urgency if appropriate ("Get Your Free Trial Today")
  - But avoid false urgency (damages trust)
```

## User-Generated Content (UGC) Ads

### Authentic Customer Content

```python
class UGCAdStrategy:
    def __init__(self):
        self.ugc = {}

    def ugc_benefits(self):
        return {
            "authenticity": "Feels real, not corporate",
            "relatability": "Customer looks like your audience",
            "trust": "Peer recommendation (more credible than brand)",
            "performance": "UGC often 2-3x better CTR than polished ads"
        }

    def ugc_sources(self):
        return {
            "customer_testimonials": "Ask satisfied customers for video",
            "user_reviews": "Compile customer reviews as video slides",
            "social_media": "Repost customer posts (with permission)",
            "branded_hashtag": "Encourage users to share with #yourbrand",
            "ugc_platforms": "Capture, Billo, Hashtag Paid (find creators)"
        }

    def ugc_format(self):
        return {
            "video_testimonial": {
                "length": "15-60 seconds",
                "camera": "Phone camera (authentic look)",
                "setting": "Home, office, natural environment",
                "content": "Customer explains problem, how product helped, result",
                "compensation": "$100-500 per video typical"
            },
            "review_montage": {
                "format": "3-5 customer review snippets",
                "length": "10-20 seconds each",
                "visual": "Text overlay of review",
                "audio": "Customer saying their own review"
            },
            "unboxing_review": {
                "format": "Customer unboxes product, reacts",
                "length": "30-60 seconds",
                "content": "First impressions, features, recommendation",
                "authenticity": "No script (or loose script)"
            }
        }

    def ugc_content_brief(self):
        return {
            "problem": "What was customer struggling with?",
            "solution": "How did product solve it?",
            "result": "Specific outcome (metric if possible)",
            "tone": "Authentic, conversational, honest",
            "dos": ["Be specific", "Show emotion", "Mention actual results"],
            "donts": ["Sound scripted", "Too polished", "Generic praise"]
        }
```

## Testimonial Ad Framework

### Leveraging Customer Success

```yaml
Testimonial Ad Structure:

Ideal Testimonial Elements:
  - Customer name + photo (credibility)
  - Job title + company (context)
  - Specific metric/result (proof)
  - Quote (emotional resonance)
  - Before/after comparison (transformation)

Testimonial Format:
  Text Only:
    - Quote format
    - 1-3 sentences max
    - Display photo and name
    - Include company/title

  Video Testimonial:
    - 15-30 second video
    - Customer on camera (authentic)
    - Talk to camera (direct)
    - Share specific result
    - Show genuine emotion

  Case Study Ad:
    - Company logo
    - Challenge → Solution → Result
    - Specific metrics
    - Customer quote
    - Link to full case study

High-Converting Testimonials Include:

Specificity:
  - Bad: "This product is amazing"
  - Good: "Saved 15 hours per week and increased revenue 40%"

Relatability:
  - Speaks to pain point of target audience
  - Uses language audience uses
  - Real person, real situation

Social Proof Elements:
  - Specific metric (time saved, revenue increase, etc.)
  - Unexpected result (bigger than expected)
  - Honest limitation (builds credibility)
    - "Takes 10 minutes to set up, but worth it"
    - "Pricey, but ROI is worth it"

Emotional Element:
  - How did it make you feel?
  - Relief, excitement, confidence?
  - Customer authenticity
```

## Monthly Creative Testing Checklist

- [ ] Review top 3 performing ads (what hook is working?)
- [ ] Pause bottom 20% of ads (low CTR)
- [ ] Test new hook formula (try 2-3 new hooks)
- [ ] A/B test CTA copy (Get Started vs Try Free)
- [ ] Test UGC ad format (vs polished ads)
- [ ] Analyze by platform (what works where?)
- [ ] Review copy length (long vs short form)
- [ ] Test benefit-focused headline vs problem-focused
- [ ] Create 5 new ad variations
- [ ] Monitor CTR trends (are old ads fatiguing?)
- [ ] Test social proof element (testimonial vs stats)
- [ ] Refresh underperforming creative
