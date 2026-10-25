---
name: accounts-receivable-guide
description: >
  Accounts receivable management covering invoicing best practices, payment terms,
  collection strategies, and aging analysis. Optimizes cash flow and reduces
  bad debt.
category: finance
version: 1.0.0
---

# Accounts Receivable Guide

## Invoicing Best Practices

### Invoice Components
- **Invoice number**: Sequential (001, 002, etc) for tracking
- **Issue date**: When invoice sent
- **Due date**: When payment expected (typically 30 days)
- **Company info**: Name, address, phone, email, tax ID
- **Client info**: Name, address, contact person
- **Itemized charges**: Description, quantity, unit price, line total
- **Terms**: Net 30, Net 60, 2/10 Net 30, etc
- **Payment instructions**: Where to send payment (bank details, check address)
- **Late fee policy**: If applicable (e.g., 1.5% per month on overdue balance)

### Invoice Template
```
INVOICE

Invoice #: 001
Date: January 15, 2024
Due: February 14, 2024

FROM:
Your Company LLC
123 Main Street
City, State 12345
tax-id@company.com

TO:
ABC Corporation
456 Oak Avenue
City, State 67890
Attention: John Doe

SERVICES:
Web design consulting (10 hrs @ $150/hr)  $1,500
Copywriting (5 hrs @ $100/hr)             $500
Design revisions (3 hrs @ $100/hr)        $300

Subtotal:                                 $2,300
Tax (8%):                                 $184
TOTAL DUE:                                $2,484

PAYMENT TERMS: Net 30
Late fee: 1.5% per month on unpaid balance

Payment options:
Bank transfer: [routing, account, swift code]
Check: Mail to above address
Credit card: [link to payment portal]

Thank you for your business!
```

### Invoicing Frequency
- **Upfront**: Full payment before starting (consulting, retainers)
- **Milestone-based**: Payment upon completion of phases
- **Monthly**: Standard for recurring services
- **Upon completion**: After project done (small projects)

## Payment Terms Strategy

### Standard Terms by Industry

| Industry | Standard Terms | Reasoning |
|----------|---------------|-----------|
| Consulting | Net 30, 50% deposit | Cash flow, project-based |
| Software/SaaS | Net 30 | Monthly recurring revenue |
| E-commerce B2B | Net 30-60 | Industry standard |
| Government contracts | Net 60-90 | Slow payment cycles |
| International | Sight draft, 50% upfront | Currency risk, distance |
| Services | Net 15-30 | Immediate cash need |

### Payment Terms Definitions
- **Net 30**: Full payment due 30 days from invoice date
- **2/10 Net 30**: 2% discount if paid within 10 days, otherwise due in 30
- **Deposit + balance**: 30% upfront, 70% upon completion
- **Monthly invoicing**: Invoice on 1st, due by 30th (retainers)
- **Sight draft**: Payment before receiving goods (international trade)

### Cash Flow Consideration
```
Project cost: $10,000
Monthly burn rate: $5,000

Net 30 terms: Payment received at day 30
  Day 0: Spend $10,000 on project
  Day 1-30: Burn $10,000 in operating costs
  Day 30: Receive payment
  Gap: Company needs $20,000 cash runway

Deposit option: 50% deposit ($5,000), 50% on completion
  Day 0: Receive $5,000 deposit
  Day 0: Spend $10,000 (have $5k down payment)
  Day 1-30: Burn $5,000 more (from deposit)
  Day 30: Complete, receive $5,000
  Gap: Only need $5,000 cash runway

Better terms: Deposits, shorter terms improve cash flow
```

## Collection Strategies

### Aging Analysis
Track how long invoices are outstanding:

```
Current (0-30 days): $15,000    (good)
31-60 days:         $8,000     (warning)
61-90 days:         $3,000     (past due)
90+ days:           $1,500     (likely bad debt)
Total AR:           $27,500
```

**Key metric**: Days Sales Outstanding (DSO)
- Formula: (Accounts Receivable ÷ Daily Revenue) × Days
- Example: $27,500 AR ÷ $1,000 daily revenue = 27.5 days DSO
- Benchmark: 30 days DSO is healthy, > 60 days is concerning

### Collection Timeline

**Day 15 (Before due date)**:
- Reminder email: "Payment due in 15 days"
- Attach invoice link or PDF
- Mention payment options

**Day 30 (Due date)**:
- Automatic invoice marked as "Due today"
- System flag in accounting software
- No action needed yet

**Day 35-45 (First follow-up)**:
- Friendly email: "We haven't received payment for invoice #123"
- Reiterate due date, payment methods
- Offer payment plan if needed
- "Please let us know if you've already sent payment"

**Day 60-75 (Second follow-up)**:
- Phone call or formal letter
- More urgent tone: "Account is 30 days overdue"
- Request payment in next 5 business days
- Mention late fees accruing

**Day 90-120 (Final notice)**:
- Certified letter or formal notice
- "Final demand before legal action"
- Offer payment plan (last chance)
- State consequences (legal action, collections agency)

**Day 120+ (Default)**:
- Send to collections agency (3% of amount recovered)
- Stop future service
- Report to credit bureaus (damages client credit)
- Consider lawsuit (if large amount > $5,000)

### Collection Calls Strategy
1. **Be professional**: "Hi John, I'm following up on invoice #123"
2. **Confirm received**: "Did you receive the invoice on [date]?"
3. **Identify issue**: "Is there a problem with the invoice or service?"
4. **Offer solution**: "Would a payment plan work?" or "Can you pay [amount] today?"
5. **Get commitment**: "I'll send payment instructions. Can you confirm you'll send by [date]?"
6. **Document**: Note call date, outcome, next action in CRM

## Early Payment Discounts

### Formula
**2/10 Net 30 means**:
- Pay within 10 days = 2% discount
- Otherwise pay within 30 days

**Example**:
- Invoice amount: $10,000
- 2/10: $10,000 × 0.98 = $9,800 (if paid by day 10)
- Standard: $10,000 (if paid by day 30)

### When to Offer
- Cash flow is strong (don't need discount)
- Client has excellent payment history
- Invoice amount is large ($5,000+)
- Want to accelerate cash for working capital

### Cost of Discount
```
2% discount = 36% annual cost
Calculation: 2% discount × (365 days ÷ 20 days) = 36% annualized

If you could borrow at 10% to wait 30 days, discount is bad deal
If you're at 5% opportunity cost, discount is good deal
```

## Bad Debt Management

### Reserves
- **Estimate** uncollectible amount: Typically 1-5% of AR
- **Journal entry**:
```
Dr. Bad debt expense 6800    $500
   Cr. Allowance for doubtful accounts 1120    $500
Description: Monthly bad debt reserve
```

### Write-Off
When customer bankruptcy or no collection possible:
```
Dr. Allowance for doubtful accounts 1120    $500
   Cr. Accounts receivable 1110    $500
Description: Write-off of invoice #456 (customer bankruptcy)
```

### Collections Agency
- **Cost**: 25-50% of amount collected (or fixed fee)
- **Process**: Agency pursues client legally, you get remainder
- **Timing**: Take 3-6 months to collect
- **Credit impact**: Damages client credit score (caution: may lose future business)

## AR Best Practices

### Upfront Qualification
1. **Credit check**: Request D&B report, check credit history
2. **References**: Ask for bank and trade references
3. **Terms justified**: Don't offer Net 60 to unknown startup
4. **Deposit**: Large clients should provide security deposit

### Contract Language
- **Payment terms clearly stated**: "Net 30 from invoice date"
- **Late fees**: "1.5% per month on balance past due"
- **Interest**: "Interest accrues at maximum legal rate"
- **Collection costs**: "Client liable for attorney, collection agency fees"
- **Dispute notice**: "Disputes must be noted within 10 days or invoice deemed accepted"

### Technology & Automation
- **Automated reminders**: Email at day 15, 30, 45
- **Online payment portal**: QuickBooks, FreshBooks, Square
- **ACH auto-pay**: Ask client for permission to auto-charge account
- **Dashboard**: Monitor aging by client in real-time

### Client Communication
- **Invoice wording**: Use friendly tone, makes payment easy
- **Multiple payment methods**: Bank transfer, credit card, check, PayPal
- **Clear contact info**: Phone + email for payment questions
- **Proactive outreach**: "Can we help with any questions about the invoice?"

## Sample Collection Email Templates

**Day 15 reminder**:
```
Subject: Friendly reminder - Payment due on Invoice #123 in 15 days

Hi [Name],

This is a friendly reminder that payment for Invoice #123 is due on [date].

Invoice details:
- Amount: $2,500
- Due date: [date]

Payment options:
- Bank transfer: [details]
- Credit card: [link]
- Check: Mail to [address]

Please let me know if you have any questions.

Best regards,
[Your name]
```

**Day 45 follow-up**:
```
Subject: Payment needed - Invoice #123 is now overdue

Hi [Name],

I'm following up on Invoice #123, which is now 15 days overdue (due [original date]).

If you've already sent payment, please disregard this email. Otherwise, please send payment by [new date] to avoid late fees.

Late fees are accruing at 1.5% per month.

Let me know if you have any questions or if you need a payment plan.

Best regards,
[Your name]
```

## Key Metrics

- **DSO (Days Sales Outstanding)**: AR ÷ (Annual revenue ÷ 365)
- **Collection effectiveness**: On-time payments ÷ Total invoices
- **Bad debt ratio**: Bad debt expense ÷ Revenue
- **AR turnover**: Revenue ÷ Average AR (higher is better)

## Red Flags

- Client consistently paying 30+ days late
- Requests for payment plans (cash flow issues)
- Invoice disputes suddenly increase
- Inability to reach decision-maker
- Unfamiliar business address or phone changes
- Requesting unusual payment methods (gift cards, crypto)
