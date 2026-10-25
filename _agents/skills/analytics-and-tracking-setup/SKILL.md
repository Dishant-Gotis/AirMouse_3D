---
skill_name: analytics-and-tracking-setup
description: Master GA4 setup, Google Tag Manager, UTM parameters, funnel analysis, cohort analysis, and measurement planning
category: Analytics & Automation
version: 1.0.0
---

# Analytics and Tracking Setup: From Data Collection to Insights

This skill teaches how to set up proper analytics tracking, Google Tag Manager, UTM conventions, and turn raw data into actionable insights.

## Part 1: GA4 Fundamentals

### GA4 vs. Universal Analytics (UA)

```markdown
## Why GA4?

Google deprecated Universal Analytics (UA) in July 2023.
All sites MUST use GA4.

### Key Differences

UA (Old):
- Session-based (pageview → bounce)
- Limited event tracking
- User ID tracking complex

GA4 (New):
- Event-based (all actions are events)
- Unlimited event tracking
- Better cross-device tracking
- Better privacy-compliant (no cookies required)

### Mindset Shift

UA: "What pages did users view?"
GA4: "What did users do? When did they convert?"
```

## Part 2: GA4 Setup

### Step 1: Create GA4 Property

```markdown
## GA4 Property Setup

1. Go to: https://analytics.google.com
2. Click "Create" → Create account
3. Account name: "Your Business Name"
4. Property name: "Your Website"
5. Reporting timezone: Your timezone (not UTC)
6. Industry: Pick your industry
7. Business objectives: Select relevant goals

8. Install tracking:
   - Copy Measurement ID: G-XXXXXXXXXX
   - Add to website header (Google Tag Manager, or direct)

## Verification

In GA4:
- Select property
- Reports → Realtime
- Visit your website
- Should see visitor data appearing in realtime
```

### Step 2: Configure Key Settings

```markdown
## GA4 Configuration

### Data Streams
- Web: Track website visitors
- Mobile: Track app installs (if applicable)
- Both: Track cross-platform

Your site may have:
- www.example.com → One stream
- app.example.com → Separate stream (different domain)

### User ID Tracking (Optional but recommended)

After user logs in, send their user ID:

```javascript
gtag('config', 'G-XXXXXXXXXX', {
  'user_id': user_id_value
});
```

This allows GA4 to:
- Track same user across sessions
- See complete user journey
- Build user segments (logged-in users, etc.)

### Data Retention

- Advertising: 14 months (default)
- Google Signals: 26 months

Keep at 14 months minimum (7 months is minimum).
```

## Part 3: Event Tracking in GA4

### Built-in Events (Automatic)

```markdown
## GA4 Tracks These Automatically

- page_view: User loads a page
- scroll: User scrolls 90% of page
- click: User clicks on links
- video_start: Video starts playing
- form_start: User starts filling form
- form_submit: User submits form
- purchase: User completes purchase

## You Don't Need to Set These Up!

GA4 tracks them without any code.
Just install the measurement ID.
```

### Custom Events (You Define)

```markdown
## Common Custom Events to Track

E-commerce:
- add_to_cart: User adds product
- remove_from_cart: User removes product
- view_item: User views product detail
- purchase: Complete transaction

SaaS:
- sign_up: User creates account
- login: User logs in
- start_trial: User starts free trial
- upgrade: User upgrades to paid

Content:
- newsletter_signup: Subscribe to newsletter
- download_pdf: Download resource
- watch_video: Watch specific video
- share_content: User shares article

## How to Send Custom Events

Use JavaScript:

```javascript
// Track newsletter signup
gtag('event', 'newsletter_signup', {
  'email': user_email
});

// Track download
gtag('event', 'download_pdf', {
  'pdf_name': 'SEO-Guide-2024'
});

// Track video view
gtag('event', 'video_complete', {
  'video_name': 'How to Use Our App'
});
```

Via Google Tag Manager: Easy setup without code (see Part 4)
```

## Part 4: Google Tag Manager (GTM)

### Why Use GTM?

```markdown
## Problem
- Every event needs code added to website
- Non-technical team can't add tracking
- Changes require developer time

## Solution: Google Tag Manager
- Visual interface (no code needed)
- Manage tags, triggers, variables
- Publish changes instantly
- See data immediately

## Typical Setup

Website → GTM Container → GA4 property
              ↓
              Tags (what to track)
              Triggers (when to track)
              Variables (what data to send)
```

### GTM Basic Setup

```markdown
## Install GTM Container

1. Create GTM account: tagmanager.google.com
2. Create container for your website
3. Copy container code

Add to website (before closing </head> tag):

```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->
```

4. Add noscript tag before closing </body>:

```html
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager -->
```

5. Verify in GA4: Reports → Realtime (should see data)
```

### Track Button Clicks (Example)

```markdown
## Track "Sign Up" Button Clicks

In GTM:

1. Create Trigger:
   - Name: "Sign Up Button Click"
   - Type: Click - Element
   - Click Text: Contains "Sign Up"

2. Create Tag:
   - Name: "GA4 - Sign Up"
   - Type: Google Analytics - GA4 Event
   - Measurement ID: G-XXXXXXXX
   - Event Name: "sign_up"

3. Connect: Trigger → Tag

4. Publish

Now GA4 will track every "Sign Up" click automatically!
```

## Part 5: UTM Parameters & URL Tracking

### What Are UTM Parameters?

```markdown
## UTM Structure

URL + UTM Parameters = Trackable link

Original: https://example.com/
Tracked: https://example.com/?utm_source=email&utm_medium=newsletter&utm_campaign=january

## 5 Main Parameters

utm_source: Where the click came from
- google, facebook, email, newsletter, sponsor

utm_medium: Type of channel
- cpc (paid search), organic, social, email, referral

utm_campaign: Specific campaign name
- january_sale, product_launch, webinar_followup

utm_content: Specific variation (optional)
- image_v1, video_v2 (for A/B testing ads)

utm_term: Keyword (optional, mainly for PPC)
- expensive_keywords, cheap_keywords
```

### UTM Naming Convention

```markdown
## Standard Convention (Pick One, Use Consistently)

Format: utm_source=X & utm_medium=Y & utm_campaign=Z

### Email Campaign
utm_source=email
utm_medium=newsletter
utm_campaign=march_2024_launch
Full URL: https://example.com/?utm_source=email&utm_medium=newsletter&utm_campaign=march_2024_launch

### Paid Social
utm_source=facebook
utm_medium=cpc
utm_campaign=spring_sale_leads
utm_content=carousel_v1

### Blog Post
utm_source=blog
utm_medium=organic
utm_campaign=seo_guide

### Partner Referral
utm_source=partner_name
utm_medium=referral
utm_campaign=affiliate_program

## Naming Rules
- Use lowercase only
- Use underscores (not spaces): march_2024_launch
- Be specific: "sale" is bad, "spring_sale_2024" is good
- Keep consistent across channels
```

### UTM Parameter Generator Tool

```markdown
## Build UTMs Without Manual Typing

URL: https://ga-dev-tools.google/campaign-url-builder/

1. Enter website URL
2. Fill in UTM fields
3. Copy generated URL
4. Use in emails, ads, etc.

Alternative tools:
- Bitly (shortens + tracks)
- Branch.io
- Rebrandly
```

## Part 6: Funnel Analysis

### Setting Up Funnels in GA4

```markdown
## Create Funnel Report

GA4 → Reports → Funnel exploration

Create funnel:
- Step 1: page_view (all pages)
- Step 2: form_start (user sees form)
- Step 3: form_submit (user submits)
- Step 4: purchase (user buys)

GA4 shows:
- Users at each step
- Drop-off between steps
- Conversion rate (step 1 → step 4)

Example:
Step 1: 1,000 page views
Step 2: 500 form starts (50% drop)
Step 3: 250 form submits (50% drop)
Step 4: 50 purchases (20% drop)

Overall funnel conversion: 5%
```

### Identifying Drop-Off Points

```markdown
## Funnel Analysis

Total steps: 4
Total conversion: 5%

Biggest drop: Form start → Form submit (50% drop)
→ Form is hard to fill

Questions to investigate:
1. Is form too long? (test shorter form)
2. Are fields unclear? (test better labels)
3. Is form validation confusing? (test error messages)
4. Is trust low? (test adding testimonials above form)

Second drop: Purchase step (20% from submit)
→ Maybe checkout friction

Test:
- Remove unnecessary fields
- Add guarantees (30-day refund, no credit card)
- Test different payment methods
```

## Part 7: Cohort Analysis

### What is a Cohort?

```markdown
## Cohort = Group of users with something in common

Cohort Examples:
- Users who signed up in March 2024
- Users from USA
- Users aged 25-34
- Users who clicked on Ad Variant A

Cohort Analysis = Compare how different cohorts behave

Example Cohort Report:
- Cohort: Sign-up month
- Retention: % who return after 1 week, 2 weeks, month

March Cohort: 40% return after 1 week
April Cohort: 35% return after 1 week
→ April campaign quality lower (maybe cheaper traffic)
```

### Creating Cohorts in GA4

```markdown
## Build Cohort Comparison

GA4 → Reports → Cohort Exploration

Cohort definition:
- Cohort type: Date (when user first engaged)
- Cohort date range: Mar 2024 - May 2024

Metrics to compare:
- Retention (do they come back?)
- Engagement (how much do they use?)
- Conversion (do they upgrade?)

Example output:
| Cohort    | 1-Day Return | 7-Day Return | 30-Day Return |
|-----------|--------------|--------------|---------------|
| Mar Signup| 25%          | 15%          | 8%            |
| Apr Signup| 28%          | 18%          | 10%           |
| May Signup| 32%          | 20%          | 12%           |

Insight: Each month's cohort retains better
→ Product is improving OR onboarding is better
```

## Part 8: Measurement Plan Template

```markdown
# Measurement Plan: [Product/Website]

## Business Goals
1. Goal: Increase free trial signups
   Target: 100 signups/month
   Success metric: sign_up event

2. Goal: Improve trial → paid conversion
   Target: 25% conversion rate
   Success metric: upgrade event

3. Goal: Reduce churn
   Target: <5% monthly churn
   Success metric: Cohort retention analysis

## Tracking Events

### Signup Journey
- form_start: User sees signup form
- form_submit: User submits form
- sign_up: Account created (triggered by form_submit)

### Activation Journey
- feature_tour_start: User sees onboarding
- feature_tour_complete: User completes onboarding
- first_successful_use: User completes first task

### Monetization Journey
- upgrade_click: User clicks upgrade button
- upgrade_form_start: Payment form shown
- upgrade_complete: Payment successful
- upgrade_fail: Payment failed

### Retention Journey
- login: User logs back in
- create_content: User creates something
- share_content: User shares result
- invite_friend: User refers friend

## UTM Tracking

All external traffic uses UTM parameters:
- Email campaigns: utm_source=email
- Paid ads: utm_source=google/facebook
- Partnerships: utm_source=partner_name

## Data Collection Timeline

Week 1: Verify all events firing in realtime
Week 2: Check data quality in reports
Week 3: Create dashboards for key metrics
Week 4: Start optimization based on data

## Success Metrics Dashboard

Monthly review:
- Signups: [Goal vs Actual]
- Trial to paid: [Goal vs Actual]
- Feature adoption: [Which features used most]
- Churn rate: [Monthly trend]
```

## Part 9: Common GA4 Mistakes

```markdown
## Mistake 1: Not Installing GTM Properly
❌ Missing noscript tag (40% of users on slow connections don't track)
✅ Install both script and noscript tags

## Mistake 2: Too Many Custom Events
❌ Track everything (data overload, slow site)
✅ Track only key business metrics (sign-up, purchase, key features)

## Mistake 3: No Event Parameters
❌ Send event with no details
  gtag('event', 'purchase');
✅ Send event with value
  gtag('event', 'purchase', { value: 99.99, currency: 'USD' });

## Mistake 4: Not Excluding Internal Traffic
❌ Your own team visiting inflates metrics
✅ Exclude your IP address (Admin → Data Streams → exclude internal traffic)

## Mistake 5: Wrong Timezone
❌ Report timezone different from business timezone
  (Reports say 10K visitors, but daily reports don't match)
✅ Set timezone to your timezone in property settings

## Mistake 6: No UTM Parameters
❌ Traffic from campaigns unmarked
  (Can't tell if Google Ads or organic)
✅ All external links use UTM (especially ads, emails)

## Mistake 7: Not Setting Up Conversions
❌ GA4 set up, but no goal tracking
✅ Mark key events as conversions (Admin → Conversions)
```

## Part 10: Reporting Template

```markdown
# Monthly Analytics Report: [Month]

## KPI Summary

| Metric | Target | Actual | vs. Last Month | Status |
|--------|--------|--------|----------------|--------|
| Visitors | 10,000 | 8,500 | -15% | ⚠️ |
| Signups | 100 | 85 | -15% | ⚠️ |
| Trial to Paid | 25% | 22% | -3pp | ⚠️ |
| MRR | $10K | $8.9K | -11% | ⚠️ |

**Status**: Down from last month, needs investigation

## Traffic Breakdown

| Source | Sessions | Signups | Conversion |
|--------|----------|---------|------------|
| Google Organic | 4,000 | 50 | 1.25% |
| Paid Ads | 2,500 | 25 | 1% |
| Email | 1,200 | 8 | 0.67% |
| Referral | 800 | 2 | 0.25% |

Insight: Organic traffic highest quality

## Feature Adoption

| Feature | Users | % of Active Users |
|---------|-------|------------------|
| Dashboard | 2,100 | 100% |
| Reports | 1,800 | 86% |
| Integrations | 420 | 20% |
| Advanced Filter | 210 | 10% |

Insight: Integrations underused, needs documentation

## User Cohorts

| Cohort | 1-Week Return | 30-Day Return | Upgraded |
|--------|---------------|---------------|----------|
| Jan Signup | 45% | 15% | 8% |
| Feb Signup | 48% | 18% | 10% |
| Mar Signup | 50% | 20% | 12% |

Insight: Retention improving, onboarding working better

## Recommendations

1. Traffic declining → Audit paid ads, increase organic push
2. Integrations unused → Create tutorials, feature homepage
3. March cohort better → Analyze what changed, apply to April
```

---

## Checklist: Analytics Setup Ready

- ✓ GA4 property created and verified
- ✓ Measurement ID added to website
- ✓ GTM container installed (if applicable)
- ✓ Key business events defined
- ✓ UTM naming convention established
- ✓ Email/ad campaigns using UTM parameters
- ✓ Conversion goals configured in GA4
- ✓ IP exclusion set (internal traffic)
- ✓ Timezone correct in property settings
- ✓ Monthly reporting template created

Start tracking today. You can't optimize what you don't measure.
