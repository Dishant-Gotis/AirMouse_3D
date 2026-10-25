---
name: bookkeeping-setup-guide
description: >
  Complete bookkeeping setup covering chart of accounts, accrual vs cash basis,
  bank reconciliation, and financial reporting. Establishes foundation for
  accurate business accounting and decision-making.
category: finance
version: 1.0.0
---

# Bookkeeping Setup Guide

## Chart of Accounts (CoA) Structure

### Standard Format
```
1000-1999: Assets
  1000-1099: Cash
    1010: Checking Account
    1020: Savings Account
    1030: PayPal/Stripe
  1100-1199: Accounts Receivable
    1110: Customer invoices (unpaid)
    1120: Allowance for doubtful accounts
  1200-1299: Inventory
    1200: Raw materials
    1250: Work in progress
    1300-1399: Fixed Assets
    1300: Equipment
    1310: Accumulated depreciation - equipment

2000-2999: Liabilities
  2000-2099: Accounts Payable
    2010: Supplier invoices (unpaid)
  2100-2199: Credit Cards
    2110: Business credit card
    2120: Corporate card
  2200-2299: Short-term debt
    2200: Line of credit
  2300-2399: Payroll liabilities
    2310: Salaries payable
    2320: Payroll taxes payable

3000-3999: Equity
  3000: Owner capital
  3100: Retained earnings
  3200: Distributions

4000-4999: Revenue
  4000-4099: Product sales
    4010: Online store sales
    4020: Wholesale
  4100-4199: Service revenue
    4110: Consulting services
  4200-4299: Other income
    4210: Interest income

5000-5999: Cost of Goods Sold
  5000: Product costs
  5100: Materials
  5200: Direct labor

6000-6999: Operating Expenses
  6000-6099: Salaries & wages
    6010: Employee salaries
    6020: Contractor payments
  6100-6199: Office & supplies
    6110: Office supplies
    6120: Software subscriptions
  6200-6299: Marketing
    6210: Paid advertising
    6220: Content creation
  6300-6399: Rent & utilities
    6310: Office rent
    6320: Utilities
  6400-6499: Insurance & taxes
    6410: Business insurance
    6420: Property taxes
  6500-6599: Professional fees
    6510: Accounting fees
    6520: Legal fees
  6600-6699: Other expenses
    6610: Travel
    6620: Meals & entertainment
```

### Custom Categories (By Industry)
**E-commerce**: Inventory, shipping, returns processing
**SaaS**: Cloud infrastructure, customer support, onboarding
**Services**: Subcontractors, equipment, licensing
**Real Estate**: Mortgage, maintenance, property taxes

## Accrual vs Cash Basis

### Cash Basis
- **Recognition**: Income when cash received, expenses when cash paid
- **Example**:
  - Invoice customer in Dec, payment received Jan → Recognize revenue in Jan
  - Bill received in Dec, paid in Jan → Recognize expense in Jan
- **Simplicity**: Easy to understand, reconciles with bank statement
- **For**: Very small businesses, service providers
- **IRS rule**: Can use if < $25M annual revenue (pass-through entities, most small businesses)

### Accrual Basis
- **Recognition**: Income when earned, expenses when incurred
- **Example**:
  - Invoice in Dec, payment in Jan → Recognize revenue in Dec
  - Bill received in Dec, paid in Jan → Recognize expense in Dec
- **Accuracy**: Better reflects business performance in specific period
- **For**: Growing businesses, manufacturing, multi-period contracts
- **Inventory**: Required if > $25M revenue or manufacturing

### Hybrid Approach
- **Revenue**: Accrual (recognize when sold/invoiced)
- **Expenses**: Cash (recognize when paid)
- **Common for service businesses**: SaaS, consulting, freelance

### Accrual Journal Entries

**Invoice issued (revenue accrual)**:
```
Dr. Accounts Receivable 1110     $1,000
   Cr. Product Sales 4010                  $1,000
Description: Customer ABC invoice #12345
```

**Cash received later**:
```
Dr. Cash 1010                    $1,000
   Cr. Accounts Receivable 1110           $1,000
Description: Payment from Customer ABC
```

**Bill received (expense accrual)**:
```
Dr. Supplies Expense 6110        $500
   Cr. Accounts Payable 2010              $500
Description: Office supplies invoice #99
```

**Bill paid later**:
```
Dr. Accounts Payable 2010        $500
   Cr. Cash 1010                         $500
Description: Payment for invoice #99
```

## Bank Reconciliation

### Monthly Process (Essential)
1. **Gather statements**: Bank statement + credit card statements
2. **List transactions**: In accounting software, confirm all posted
3. **Identify discrepancies**: Outstanding checks, pending deposits
4. **Adjust as needed**: Mark cleared items, reconcile differences
5. **Investigate**: Any unexplained differences

### Reconciliation Worksheet
```
Bank statement balance:          $10,500
Add: Deposits in transit
  Deposit 5/31 from customer XYZ   $2,000
                                  $12,500

Less: Outstanding checks
  Check #1023 to supplier            $300
  Check #1024 to contractor          $800
                                    ($1,100)

Reconciled bank balance:         $11,400

Accounting system balance:       $11,400 ✓ Match!
```

### Common Reconciliation Issues
- **Timing**: Check clears 2-3 days after written
- **Fees**: Bank charges fees not in accounting software yet
- **Interest**: Bank interest earned added to statement
- **Duplicate**: Transaction recorded twice (delete one)
- **Reversal**: ACH payment reversed (refund must clear)

### Software Automation
- Most accounting software (QuickBooks, Xero) auto-matches transactions
- Bank connectivity via Plaid API
- Manual review still required (10-15 min per account/month)

## Fixed Assets & Depreciation

### Capitalization vs Expensing
- **Capitalize**: Asset with life > 1 year and cost > $2,500 (IRS Section 179)
- **Expense**: Supplies, software under $2,500, short-term costs

### Depreciation Methods

**Straight-line** (most common):
- Formula: (Cost - Salvage Value) ÷ Useful Life
- Example: Laptop $1,500, useful life 5 years
- Annual depreciation: $1,500 ÷ 5 = $300/year

**Accelerated (MACRS)**:
- Deduct more in early years, less in later years
- IRS schedules by asset class (5-year property, 7-year property, etc)
- Benefits: Higher early deductions, better cash flow

**Units of production**:
- Depreciation based on usage (equipment running hours)
- Formula: (Cost × Hours Used This Year) ÷ Total Estimated Hours

### Depreciation Journal Entry
```
Dr. Depreciation Expense 6600    $300
   Cr. Accumulated Depreciation - Equipment 1310    $300
Description: Monthly depreciation on laptop (5-year asset)
```

### Asset Disposal
When selling/retiring asset:
```
Sold laptop for $400 (original cost $1,500, accumulated depreciation $1,200)

Dr. Cash 1010                    $400
Dr. Accumulated Depreciation 1310 $1,200
   Cr. Equipment 1300                      $1,500
   Cr. Gain on sale 4210                    $100
Description: Sold office laptop #ABC123
```

## Financial Statements

### Income Statement (P&L)
Shows profitability over period (month, quarter, year)

**Format**:
```
Revenue:
  Product sales:        $50,000
  Service revenue:      $20,000
Total revenue:                     $70,000

Cost of goods sold:               ($15,000)
Gross profit:                      $55,000

Operating expenses:
  Salaries:            ($25,000)
  Marketing:            ($8,000)
  Rent:                 ($3,000)
  Other:                ($2,000)
Total operating:                  ($38,000)

Operating income:                  $17,000

Other income/expenses:
  Interest income:        $100
  Interest expense:      ($500)
Net income:                        $16,600
```

### Balance Sheet
Shows financial position at specific date

**Format**:
```
ASSETS
Current:
  Cash:               $25,000
  Accounts receivable: $10,000
  Inventory:          $15,000
Total current:                    $50,000

Fixed:
  Equipment:         $10,000
  Less: Depreciation:  (3,000)
Total fixed:                       $7,000

TOTAL ASSETS:                     $57,000

LIABILITIES & EQUITY
Current liabilities:
  Accounts payable:    $5,000
  Credit card balance: $8,000
Total current:                    $13,000

Equity:
  Capital:           $30,000
  Retained earnings: $14,000
Total equity:                     $44,000

TOTAL LIABILITIES & EQUITY:      $57,000
```

### Cash Flow Statement
Shows movement of cash (critical for business health)

**Format**:
```
Operating activities:
  Net income:                $16,600
  Add back: Depreciation:    $1,000
  Less: Increase in AR:     ($5,000)
  Add: Increase in AP:       $2,000
Net cash from operations:         $14,600

Investing activities:
  Equipment purchase:       ($8,000)
Net cash from investing:          ($8,000)

Financing activities:
  Loan repayment:           ($2,000)
  Owner distributions:      ($5,000)
Net cash from financing:          ($7,000)

Net change in cash:               ($400)
Beginning cash:                 $25,400
Ending cash:                    $25,000
```

## Bookkeeping Tools

### Spreadsheet (DIY, < 100 transactions/month)
- Google Sheets, Excel
- Manual data entry
- Free but time-consuming
- Risk of errors

### Cloud Accounting (DIY, < $500/month revenue)
- **Wave** (free): Simple, invoice + basic accounting
- **Zoho Books**: Budget-friendly, integrations
- **Square Invoices**: Simple invoicing + payments

### Professional Software (> $500/month revenue)
- **QuickBooks Online**: Industry standard, $30-200/month
- **Xero**: International, 20+ currencies
- **FreshBooks**: Service-based, project tracking
- **Stripe/PayPal integration**: Auto-reconciliation of payments

### Professional Bookkeeper (>$5k/month revenue)
- **Cost**: $300-1,000/month
- **Services**: Data entry, reconciliation, reports, tax prep
- **Find**: Upwork, local accounting firms, referrals
- **Virtual bookkeeper platforms**: Bench, BookKeep, Zoho Books

## Monthly Bookkeeping Checklist

- [ ] Record all transactions (invoices issued, bills received, cash payments)
- [ ] Bank reconciliation (cash accounts, credit cards)
- [ ] AR aging (invoices outstanding, follow up on past due)
- [ ] AP aging (bills coming due, plan cash for payments)
- [ ] Payroll processing (if applicable)
- [ ] Quarterly estimated taxes (Jan 15, Apr 15, June 15, Sept 15)
- [ ] Review P&L (compare to budget, identify variances)
- [ ] Check cash balance (enough to cover next 30 days?)

## Common Bookkeeping Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| No reconciliation | Wrong balance, fraud undetected | Reconcile monthly, automate if possible |
| Personal/business mixed | Tax issues, audit risk | Separate bank accounts + clear categorization |
| No invoices recorded | Revenue underreported, cash unclear | Record when issued (accrual), track status |
| Uncategorized expenses | Can't analyze spending, deductions missed | Standardize categories, train team |
| No backup | Data loss in system failure | Cloud backup (automated in QuickBooks, Xero) |

## Getting Help

- **Bookkeeper**: Handles transactions, reconciliation
- **CPA/Accountant**: Tax strategy, financial planning
- **Business accountant**: Non-CPAs who do accounting (cheaper than CPA for bookkeeping-only)
- **Cost estimate**: Bookkeeper $300-600/month, CPA annual tax $1,500-3,000+

## Key Metrics to Monitor

- **Gross profit margin**: (Revenue - COGS) ÷ Revenue
- **Operating margin**: Operating income ÷ Revenue
- **Net profit margin**: Net income ÷ Revenue
- **Current ratio**: Current assets ÷ Current liabilities (liquidity)
- **Debt-to-equity**: Total debt ÷ Total equity (leverage)
