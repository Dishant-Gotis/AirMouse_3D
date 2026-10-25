---
name: ads-ctv
version: 1.0.0
description: "CTV/OTT advertising strategy and operations using MNTN Performance TV. Use when the user says 'CTV,' 'connected TV,' 'OTT,' 'MNTN,' 'streaming ads,' 'TV advertising,' or 'performance TV.' Covers pixel setup, audience building, creative management, campaign launch, reporting, and integrations."
---

# CTV Advertising Operations — MNTN Performance TV Skill

## 1. Platform Overview

### CTV vs OTT Terminology
- **Connected TV (CTV)**: The hardware — Smart TVs (Samsung, LG, Vizio), streaming devices (Roku, Fire TV, Apple TV), gaming consoles
- **Over-the-Top (OTT)**: The delivery method — content streamed over the internet, bypassing traditional cable/satellite
- Together: CTV advertising = ads served to Smart TV hardware via OTT delivery

### MNTN Differentiators
- **Living Room Quality Inventory**: Strictly premium episodic content (shows like HBO, Netflix originals), non-skippable 15-30s placements
- **Verified Visits Attribution**: Household-level cross-device tracking — viewer sees ad on TV → tracks when that household visits your site on ANY device (phone, desktop, tablet)
- **Dynamic CPM Pricing**: dCPM model optimizes bids based on predicted conversion likelihood, not just impression count
- **The Flywheel**: Scale ad spend → access better inventory rates → improve ROAS → justify larger budgets → repeat

### MNTN vs Competitors
- Traditional TV: High CPM ($30-60), slow attribution, limited targeting
- Programmatic (The Trade Desk, Roku): Broader inventory (including user-generated content), lower quality guarantee, individual-level tracking
- MNTN: Premium+measured, household-level attribution, AI-powered audience targeting, higher CPM ($15-25) justified by quality

---

## 2. Pixel Setup & Verification

### Two-Pixel Architecture (BOTH Required)

**Tracking Pixel (Site-wide)**
- Fires on every page of your site
- Initializes household tracking
- Sends site visitor data to MNTN for retargeting audiences
- Status: Must be Active before launching campaigns

**Conversion Pixel (Confirmation Pages Only)**
- Fires only on post-conversion pages (thank you, purchase confirmation, demo booked, whitepaper download)
- Sends conversion events to MNTN for attribution and reporting
- Key events: purchase, lead, app install, content download

### Installation Methods (Priority Order)

1. **Google Tag Manager (Preferred)**
   - Create Custom HTML tag with MNTN tracking code
   - Trigger: All Pages (Tracking), Specific Pages (Conversion)
   - No vendor script required, works cross-domain

2. **Shopify App**
   - MNTN app available in Shopify Store, one-click install
   - Auto-installs both pixels, no code needed

3. **Adobe Experience Platform Launch**
   - Custom code extension, upload MNTN pixel script
   - Requires Adobe account

4. **Manual HTML**
   - Paste `<script>` directly into page HTML
   - Site-wide in header (Tracking), conversion pages only (Conversion)
   - Last resort if no tag manager available

### Installation Checklist

- [ ] Tracking Pixel → site header, all pages, firing on initial page load
- [ ] Conversion Pixel → post-conversion page only (thank you/confirmation)
- [ ] CSP (Content Security Policy) whitelisted: `*.mountain.com`
- [ ] No iFrames: Pixels must fire in parent window context
- [ ] Geographic: US traffic only (MNTN US-only platform)

### Verification in Chrome DevTools

1. Open site in browser, open DevTools (F12 → Network tab)
2. Filter requests: type `mountain` in search box
3. Look for two request patterns:
   - `spx?dxver=` (Tracking Pixel)
   - `st?ga_tracking_id=` (Conversion Pixel on conversion page)
4. Both should show 200 status, fired within 1s of page load

### Pixel Status Tracking

| Status | Meaning | Action |
|--------|---------|--------|
| Active | Firing correctly, ready to use | None |
| Pending Review | MNTN reviewing, typically 24-48 hrs | Wait, check dashboard daily |
| Not Installed | Not detected on site | Re-install, verify CSP, test in DevTools |
| Deprecated | Old pixel, phased out | Use new pixel ID |

---

## 3. Audience Strategy

### Prospecting vs Retargeting (Immutable at Creation)

**Prospecting Audiences**
- New users who haven't visited your site before
- Goal: Build awareness among cold audience
- Audience types: MNTN Matched, Interest-Based, Location
- Attribution window: 14 days default
- Budget: Typically higher (more inventory available)

**Retargeting Audiences**
- Users who have visited your site (tracked by Tracking Pixel)
- Goal: Convert warm leads, reduce bounce
- Minimum households: 1,000 unique visitors with pixel data
- Attribution window: 7 days default
- Budget: Lower CPM, higher conversion rate
- **CRITICAL**: Cannot switch from Prospecting → Retargeting after campaign creation. Plan upfront.

### Audience Types Detail

#### MNTN Matched (AI-Powered, Prospecting Only)
- Seed keyword phrases → MNTN AI identifies 99% of US households matching intent
- 3 Intensity Levels (cumulative):
  - **High**: Core audience (strictest match)
  - **Medium**: High + adjacent interests (~2x reach)
  - **Maximum**: Medium + lookalikes (~4x reach, lower quality)
- Best for: Scale, brand awareness
- Avoid: Too broad without location filter

#### Interest-Based (3rd Party, Prospecting Only)
- Sourced from LiveRamp data partnerships
- Pre-built categories: Home/Garden, Auto, Finance, Health, etc.
- Stacking rule: Use AND logic only (all must match), avoid OR logic
- Don't mix: Demographics alone perform poorly; combine with intent
- Typical stack: Interest A AND Interest B AND NOT Excluded Interest

#### Site Visitor Segments (Retargeting Only)
- Based on Tracking Pixel data
- Sub-segments available:
  - **All Visitors**: Anyone who hit any page
  - **Specific Pages**: Filter by URL pattern (e.g., `/pricing`)
  - **2+ Pages**: More engaged (filtered segment)
  - **Cart Abandoners**: /cart or /checkout visited, no conversion (7-14d window)
  - **Past Purchasers**: Converted within 30-90d window
- Minimum: 1,000 households to activate

#### CRM Audiences (Prospect or Retarget)
- Upload: Email addresses, phone numbers, IP addresses
- Format: Hashed (SHA256) or plaintext (MNTN hashes server-side)
- Minimum records: 1,000
- Processing time: Up to 10 business days
- Match rate: Typically 60-75% of uploaded records matched to households

### Location Targeting

- **National**: Recommended (all US), best inventory access
- **Regional**: States, DMAs (Designated Market Areas), ZIPs, cities available
- **Stacking rule**: All location filters use AND logic (must match ALL)
- **Minimum geo audience**: 50,000+ households (smaller targets may throttle)

---

## 4. Creative Management

### Video Specifications (EXACT)

**Format Requirements**
- Resolution: 1920x1080p minimum (16:9 aspect ratio required)
- Duration: Exactly 15 seconds OR exactly 30 seconds (no 6s, no 45s)
- File types: .mp4 or .mov
- Maximum file size: 4GB
- Frame rate: Constant (23.98 fps, 25 fps, or 29.97 fps ONLY; no variable frame rate)
- Bitrate: 15-30 MBPS
- Codec: H.264 video, AAC audio
- Audio: Required (never silent), stereo or mono

**Creative Development**
- Open rate (non-skippable): Designed as "native" to content
- Call-to-action: Text overlay or voiceover in final 3-5 seconds
- Branding: Logo placement top-right or bottom-right, 10% of screen minimum
- Color grading: Match OTT platform's color space (broadcast-safe recommended)

### Multi-Touch Creative (Display + Video Combo)

**Activation Rule**: Decide at campaign creation — immutable after launch

**Requirements**
- Minimum 3 sizes (300x250 required), up to 6 recommended
- Each file: Static image .jpg/.png or animated .gif, max 200KB
- Aspect ratios: 300x250, 728x90, 160x600, 320x50, 970x250, 320x480
- Refresh: Different creative serves on each new device visit (prevents ad fatigue)

**Best Practice Stack** (6 sizes)
1. 300x250 (Medium Rectangle) — anchors desktop engagement
2. 728x90 (Leaderboard) — top-of-page, high-visibility
3. 970x250 (Billboard) — large desktop, premium
4. 160x600 (Wide Skyscraper) — sidebar anchor
5. 320x50 (Mobile Banner) — mobile-first
6. 320x480 (Mobile Interstitial) — mobile full-width

### Common Rejection Reasons & Fixes

| Rejection | Cause | Fix |
|-----------|-------|-----|
| Broken frames | Corrupted video data | Re-export from source file |
| Missing audio | Silent video submitted | Add voiceover or music track |
| Variable frame rate | Mixed fps during edit | Force constant 29.97fps in export settings |
| Wrong duration | 16s or 29s submitted | Re-trim to exactly 15s or 30s |
| Bitrate out of range | <15 or >30 MBPS | Adjust encoder settings in export |
| Low resolution | 1280x720 or less | Re-render at 1920x1080 minimum |

### Creative Refresh Strategy

- **Evergreen campaigns**: Rotate creative every 2-3 months (avoid ad fatigue on long-running awareness)
- **Seasonal campaigns**: Rotate every 10-20 days (fresh creative improves click-through on limited window)
- **A/B testing**: 2-3 creative variants, compare CTR/Conversion Rate after 2 weeks, pause underperformers
- **Frequency cap recommendation**: 3-5 impressions per household per week

### Creative-as-a-Service (CaaS)

- **QuickFrame partnership**: MNTN partner provides rapid video production
- **Requirements**: Minimum annual spend commitment (typically $50K-100K)
- **Turnaround**: 5-7 business days per video
- **Pricing**: Typically $2,000-5,000 per video depending on complexity

---

## 5. Campaign Launch

### Immutable Objectives (Select Once)

- **Awareness**: Drive brand recognition, no conversion tracking required
- **Sales**: E-commerce transactions, requires conversion pixel on purchase confirmation
- **Traffic**: Drive website visits, conversion pixel on any landing page
- **Leads**: Form submissions, phone calls, requires conversion pixel on thank-you page
- **App Promotion**: Mobile app installs, requires app event tracking

**Goal** (changeable post-launch): CPV, CPCV, CPA, ROAS

### Budget Types

**Monthly Budget**
- Fixed daily spend rate (Budget ÷ days of month)
- Auto-resets on 1st of next month
- No rollover — unused daily budget is lost
- Best for: Ongoing awareness, consistent brand presence

**Flighted Budget**
- Custom date range: minimum 3 days, maximum as needed
- Spend concentrated in date range only
- Best for: Seasonal campaigns, product launches, event-based promotions

### Pre-Launch Verification Checklist

- [ ] Tracking Pixel: Active status, verified in DevTools
- [ ] Conversion Pixel: Active status (if Sales/Leads/Traffic objective)
- [ ] Email verified: Login email confirmed in MNTN account
- [ ] Logo uploaded: Brand logo added to account (used in platform UI)
- [ ] Creative approved: All videos/display ads cleared by MNTN review (24-48 hrs)
- [ ] Audience applied: Prospecting type selected AND size showing (min 1M households)
- [ ] Budget allocated: Monthly or Flighted budget set, minimum $500/day recommended
- [ ] Billing method: Credit card on file, verified

### Launch Workflow

1. **Campaign Setup**
   - Name: Use consistent naming (Brand-Objective-Month, e.g., "Acme-Sales-Mar2026")
   - Objective & Goal (immutable): Select carefully
   - Budget type: Monthly or Flighted

2. **Audience Configuration**
   - Prospecting or Retargeting (immutable)
   - Audience type: MNTN Matched, Interest, Site Visitor, CRM
   - Location filter (AND logic)
   - Frequency cap (optional, default 3-5/week)

3. **Creative Allocation**
   - Video: 15s or 30s, all specs validated
   - Multi-Touch (if enabled): 3-6 display sizes
   - Rotation: Even rotation across creatives

4. **Tracking & Integrations**
   - Conversion pixel: Link to Objective (Sales/Leads/Traffic)
   - UTM parameters: Include utm_source=mntn, utm_medium=ctv in landing URL
   - GA4 integration: Enable for real-time reporting (optional but recommended)

5. **Review & Launch**
   - Double-check all fields
   - Set start date (today or future)
   - Click "Launch Campaign"

### Common Launch Gotchas

**Monthly Budget Timing Issue**
- If campaign launches on day 25 of month, system calculates: (remaining budget) × (full month days)
- Result: System attempts to deliver full month's budget in 6 days → throttle
- **Fix**: For mid-month launches, use Flighted budget instead, or manually reduce monthly budget

**Missing Conversion Pixel**
- Launching Sales objective without conversion pixel → zero conversions tracked
- **Fix**: Verify pixel fires on thank-you page before launch

**Audience Too Broad**
- MNTN Matched on "Maximum" intensity + no location filter → massive audience, budget spent inefficiently
- **Fix**: Apply location filter (state or DMA), or use "High" intensity instead

---

## 6. Integrations

### GA4 (Outbound, Real-Time)

**What flows**: Campaign impressions, clicks, conversions (Verified Visits)
**Latency**: Real-time (within 15 minutes)
**Setup**: Dashboard → Integrations → Google Analytics 4 → Connect GA4 property
**Data flow**: MNTN → GA4 custom events (mntn_impression, mntn_conversion)
**UTM auto-population**: utm_source=mntn, utm_medium=ctv, utm_campaign={campaign_name}

### HubSpot (Inbound, Daily)

**What flows**: Leads from MNTN conversion pixels sync to HubSpot contacts
**Latency**: Daily, by 9 AM PT
**Setup**: Dashboard → Integrations → HubSpot → OAuth connect
**Requirements**: HubSpot account, user must have lead creation permission
**Data**: Email (if available), conversion data, MNTN campaign source
**Automation**: Create workflows triggered by MNTN leads, auto-assign to sales

### CallRail (Inbound, Real-Time)

**What flows**: Phone calls generated from MNTN campaigns tracked as conversions
**Latency**: Real-time
**Setup**: Dashboard → Integrations → CallRail → API key
**Requirements**: CallRail account with phone tracking enabled
**Call attribution**: CallRail tags calls with MNTN campaign source, links to ad impression

### Approved Data Methods (Priority)

1. **Impression-based tracking (RECOMMENDED)**
   - MNTN records household impression, household visits site within attribution window
   - Accuracy: Very high (Verified Visits proprietary data)
   - Best for: CTV-specific reporting

2. **API Export**
   - Daily JSON export via MNTN API 3.0
   - Endpoint: `api3.mountain.com/v3/reports/{advertiser_id}`
   - Authentication: API key (Advertiser Settings → API Keys)
   - Data: Campaign, daily metrics, audience breakdown
   - Processing: By 9 AM PT daily

3. **File Export (CSV)**
   - Manual download from Dashboard → Reports
   - Frequency: Daily, weekly, custom date range
   - Formats: Campaign summary, creative performance, audience segment detail

4. **UTM Parameters (NOT RECOMMENDED)**
   - MNTN adds utm_source, utm_medium, utm_campaign automatically
   - Limitation: Misses Verified Visits attribution (cross-device tracking lost at click)
   - Use only as fallback if GA4/API unavailable

### MNTN API 3.0 (Programmatic Access)

**Base URL**: `https://api3.mountain.com`
**Authentication**: Header `Authorization: Bearer {API_KEY}`
**Rate limit**: 1,000 requests/hour
**Key endpoints**:
- `/v3/campaigns` — List all campaigns, status, budget
- `/v3/campaigns/{id}/daily-metrics` — Daily impressions, visits, conversions
- `/v3/audiences` — Audience size, type, segment breakdown
- `/v3/creatives` — Creative status, specs, approval date

---

## 7. Reporting & Measurement

### Verified Visits Attribution Model

**Flow**: Household sees CTV ad → MNTN records impression + household ID → household visits your site within window on any device → MNTN matches visit to impression → counts as conversion

**Windows** (customizable per campaign)
- **Retargeting**: 7 days default (can extend to 30d)
- **Prospecting**: 14 days default (can extend to 30d)
- **Conversion**: 30 days default (separate from impression window)

**Cross-device tracking**
- Sees ad on Roku → visits site on iPhone 3 days later
- MNTN matches iPhone traffic to Roku household ID → attributed

### Key Performance Metrics

| Metric | Definition | Use Case |
|--------|-----------|----------|
| Impressions | CTV ad delivered to household | Scale measurement |
| Unique Households | Distinct households seeing ad (deduplicated) | Reach analysis |
| Visit Rate | (Verified Visits ÷ Impressions) × 100 | Traffic impact |
| Conversion Rate | (Conversions ÷ Verified Visits) × 100 | Quality assessment |
| CPV | Cost Per Visit | Efficiency vs other channels |
| CPA | Cost Per Acquisition | ROI for sales/leads objective |
| ROAS | Revenue ÷ Ad Spend | Profitability (Sales objective only) |
| Frequency | Avg impressions per household | Ad fatigue indicator |

### Dashboard Views

1. **Campaign Summary**
   - Overall metrics: Impressions, Visits, Conversions, Spend, ROAS

2. **Daily Performance**
   - Day-by-day breakdown: Identify spikes, underperformance days

3. **Geographic (DMA/State/City)**
   - Performance by region: Identify high-ROI markets

4. **Audience Segment**
   - Breakdown by audience type: MNTN Matched vs Interest-Based vs Site Visitor

5. **Creative Performance**
   - Per-video metrics: Which creatives drive highest CTR, CPA

6. **TV Network**
   - Breakdown by inventory source (HULU, Paramount+, etc.): Identify premium placements

---

## 8. New Client CTV Onboarding (Step-by-Step)

### Week 1: Foundation

**Day 1-2: Discovery Call**
- Business goal: Awareness, traffic, leads, or sales?
- Website & funnel: Current traffic, conversion rates, pixel readiness
- Budget: Monthly spend ceiling, test vs scale phase
- Attribution needs: GA4 integration? Existing CRM?
- Audience: In-house list (CRM) or cold prospecting?

**Day 3-4: Technical Setup**
- Create MNTN account (Advertiser role)
- Verify email ownership (auto-verify button in dashboard)
- Generate Tracking Pixel → install on site (GTM preferred)
- Verify in Chrome DevTools
- Generate Conversion Pixel → install on thank-you page
- QA: Test both pixels firing correctly
- CSP whitelist: Add *.mountain.com to Content Security Policy

**Day 5: Account Configuration**
- Upload brand logo
- Set up GA4 integration (if using)
- Add billing method (credit card)
- Create API key (if using API export)
- Set up Slack or Email alerts for low-performing campaigns

### Week 2-3: Campaign Preparation

**Creative Development**
- Define 2-3 video concepts (15s and 30s variants)
- Production timeline: In-house vs agency (2-3 weeks typical)
- Multi-Touch (display ads) decision: Yes or No?
- If yes, design 3-6 display ad sizes (outsource to designer if needed)
- Submit all creatives for MNTN review (24-48 hr turnaround)

**Audience Planning**
- If prospecting: MNTN Matched keywords or Interest-Based categories?
- If retargeting: Gather email list or wait for pixel data (2-4 weeks)
- Location targeting: National or state/DMA focus?
- Frequency cap preference: 3, 5, or 7 per household/week?

**Tracking & UTM Setup**
- Landing page URL finalized
- UTM parameters locked: utm_source=mntn, utm_medium=ctv, utm_campaign={name}
- GA4 goals/conversions defined: Form submission, purchase, content download?
- CRM integration ready (HubSpot, CallRail)?

### Week 4: Launch

**Pre-Launch Checklist (Day 1-2)**
- [ ] Both pixels Active & verified
- [ ] Email confirmed
- [ ] Logo uploaded
- [ ] Creatives approved by MNTN
- [ ] Audience size showing (min 500K households)
- [ ] Budget allocated ($500-2,000/day recommended for test)
- [ ] Landing pages live & UTMs correct
- [ ] GA4 connected
- [ ] Team trained on dashboard navigation

**Campaign Creation (Day 3)**
- Campaign name: e.g., "Acme-Sales-Mar2026"
- Objective: Sales (for e-commerce) or Leads (for B2B)
- Goal: ROAS or CPA
- Budget: Monthly or Flighted?
- Audience: Prospecting type + MNTN Matched (High or Medium intensity)
- Location: National or state-focused?
- Creatives: Assign videos + multi-touch (if enabled)
- UTM landing URL: Paste full URL with parameters
- Launch date: Tomorrow at 12 AM PT (overnight delivery window)

**Post-Launch (Day 4-7)**
- Monitor daily: Budget pacing, CPV trend
- Check GA4: Incoming traffic, conversion rate
- Verify CreativeRotation: Different videos serving across refreshes
- Team notification: Campaign live, setting expectations for 72-hr ramp

---

## 9. Audience Testing Loop (Post-72-Hour)

### The Problem: Cold start
- New campaigns take 72 hours to accumulate impressions and optimize
- First 48 hours: System learning, higher CPM, lower conversion rate
- Hour 48-72: MNTN algorithm starts optimizing targeting
- Hour 72+: Conversion rate stabilizes, CPV drops 15-30%

### Post-72-Hour Audit (Day 4 of Campaign)

**Metrics to Review**
1. Impressions: Target 50K+ by day 3 (indicates healthy pacing)
2. CPV: Should be within 30% of projected (if overperforming, audience is hot)
3. Conversion Rate: Compare day 1-3 vs industry benchmark (2-5% typical)
4. Frequency: Check if households are seeing repeats (indicates audience saturation)
5. Geographic distribution: Is spend distributed across regions or concentrated?

**Decision Framework**

| Metric | Healthy Range | Action If Underperforming |
|--------|--------------|--------------------------|
| Impressions | 40K-100K by day 3 | Increase budget 50%, loosen audience targeting |
| CPV | Within 30% of projection | Check audience quality, confirm landing page loads |
| Conversion Rate | 2-5% baseline | Test new landing page, adjust audience intent |
| Frequency | 3-5 per household/week | Reduce frequency cap or pause audience |
| CTR (if tracking clicks) | >0.5% | Creative underperforming, refresh and test new variant |

### Optimization Actions

**High-Performing Audience** (Conversion Rate > 5%, ROAS > 3:1)
- Action: Increase budget 25-50% immediately
- Expand: Loosen intensity (High → Medium) to reach adjacent audience
- Test: Clone campaign with different creative, run parallel

**Medium-Performing** (Conversion Rate 2-5%, ROAS 1.5-3:1)
- Action: Maintain budget, optimize creatives
- Test: New video variant (different CTA, hook, or visuals)
- Duration: Let run for 2 full weeks before pause decision

**Underperforming** (Conversion Rate <2%, ROAS <1.5:1)
- Action: Audit landing page (UX, load speed, mobile responsiveness)
- Audience audit: Is targeting too broad? Try High intensity instead of Maximum
- Creative audit: Test new video variant (different angle, hook, CTA timing)
- Location audit: Is spend concentrated in low-ROI region? Add state filter
- Decision timeline: If no improvement by day 14, pause and reallocate budget

### Creative Rotation Testing

**Methodology** (A/B test two creatives)
- Campaign 1: Creative A (15s video)
- Campaign 2: Creative B (15s video)
- Same audience, location, budget
- Run parallel for 14 days
- Compare: CTR, Conversion Rate, CPA
- Winner: Increase to 70-30 split, pause loser

**Refresh Cadence**
- Winning creative: Run for 3-4 months (evergreen)
- Refresh frequency: Every 2 months with new variant
- Test window: 2-week minimum per variant (accumulate 100+ conversions)

---

## 10. Troubleshooting Common Issues

### "Audience is too small" (< 100K households)
- MNTN Matched: Broaden keywords or increase intensity (High → Medium → Maximum)
- Interest-Based: Add additional interest category (use AND logic)
- Location: Expand from state to region or national
- Solution typically increases reach 2-4x

### "Campaign not delivering" (0 impressions after 6 hours)
- Check: Pixel approval status (Pending Review will block delivery)
- Check: Budget not entered or insufficient credit card
- Check: Landing page down or returning 404 (MNTN validates URLs)
- Check: Audience size showing in UI (if not, audience is empty)
- Fix: Resolve blockers, manually restart campaign delivery

### "Conversion rate dropped 50% overnight"
- Frequency fatigue: Household seeing ad too many times
- Solution: Reduce frequency cap or pause audience segment
- Seasonal: External event affecting conversions (competitor promo, holiday)
- Landing page change: Confirm URL still valid, UX not degraded
- Attribution window: Did you change conversion window? May hide conversions

### "GA4 not showing MNTN traffic"
- UTM parameters: Verify utm_source=mntn appears in GA4 (check acquisition report)
- GA4 integration: Reconnect OAuth in MNTN dashboard
- Delay: MNTN data syncs with 15-min delay; wait 30 min before troubleshooting
- Pixel mismatch: Ensure conversion pixel on thank-you page matches GA4 goal definition

---

## Quick Reference Links

- **Video Specs**: See `references/video-specs.md`
- **MNTN Dashboard**: https://platform.mountain.com
- **API Documentation**: https://api.mountain.com/docs
- **Support**: support@mountain.com or in-app chat
