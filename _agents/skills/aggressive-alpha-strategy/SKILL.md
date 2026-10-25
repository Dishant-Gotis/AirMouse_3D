# Aggressive Alpha Strategy

The master trading strategy for Trevor's play money portfolio. **Risk-on, high-conviction, concentrated bets** — designed to maximize returns on capital you can afford to lose.

Philosophy: "Play money with serious edge." We use the full 162-skill arsenal to find asymmetric bets where the upside is 3-10x the downside. We're not diversifying for safety — we're concentrating for alpha.

## Activation

This skill activates when the user:
- Says "aggressive strategy", "play money strategy", "high conviction trades"
- Says "what should I trade", "give me a play", "find me alpha"
- Says "YOLO trade" (we still use stops, but we size up)
- Says "deploy capital", "put money to work", "aggressive allocation"
- Uses `/aggressive` or `/alpha-play` command

## Risk Profile: AGGRESSIVE

```
Capital at Risk:      100% of allocated play money (NOT life savings)
Max Single Position:  25% of portfolio (vs normal 5-10%)
Max Sector:           50% of portfolio
Max Correlated:       60% of portfolio
Use of Leverage:      YES — options, margin (up to 1.5x)
Short Selling:        YES — when conviction is high
Options:              YES — directional calls/puts, NOT naked selling
Crypto:               YES — up to 20% of portfolio
Stop Losses:          MANDATORY — every position gets a stop
Position Sizing:      Kelly Criterion (half-Kelly for safety)
```

## The Aggressive Edge Framework

### Edge Sources (Ranked by Alpha Potential)

```
TIER 1 — HIGHEST ALPHA (act fast, size up)
═══════════════════════════════════════════════════════════════
1. Insider Cluster Buys + Options Flow Confirmation
   - 3+ insiders buying within 2 weeks (insider-tracker)
   - Unusual call buying confirms (options-flow-scanner)
   - Historical hit rate: 72% win, avg +18% in 90 days
   - Position size: FULL (20-25% of portfolio)
   - Vehicle: Stock + OTM calls (30-60 DTE)

2. Post-Earnings Drift (PEAD) + Revision Momentum
   - Earnings beat >10% + upward analyst revisions (pead-screener + earnings-revisions)
   - Stock hasn't fully priced in the beat yet
   - Historical hit rate: 65% win, avg +12% in 60 days
   - Position size: STANDARD (15-20% of portfolio)
   - Vehicle: Stock or ATM calls

3. Short Squeeze Setup + Catalyst
   - Short interest >20%, days to cover >5 (short-squeeze-scanner)
   - Identifiable catalyst within 30 days (earnings, product launch, FDA)
   - Historical hit rate: 55% win, but avg winner is +40%
   - Position size: MODERATE (10-15% of portfolio)
   - Vehicle: Stock (calls too expensive when SI is high)

TIER 2 — HIGH ALPHA (validate, then act)
═══════════════════════════════════════════════════════════════
4. Technical Breakout + Volume + Trend Alignment
   - VCP or cup-and-handle breakout (chart-patterns + vcp-screener)
   - Volume >2x average on breakout day
   - Sector in relative uptrend (sector-rotation)
   - Position size: STANDARD (15-20%)
   - Vehicle: Stock with tight stop at pivot point

5. Guru Consensus + Undervalued
   - 3+ top investors own same stock (guru-tracker)
   - Trading below intrinsic value (fundamentals)
   - Catalyst within 90 days
   - Position size: STANDARD (15-20%)
   - Vehicle: Stock or LEAPS (12+ month calls)

6. Macro Regime Shift Play
   - Regime changing (regime-adaptive-strategy)
   - Sector rotation signal (sector-rotation)
   - Early mover advantage in new regime leaders
   - Position size: MODERATE (10-15%)
   - Vehicle: Sector ETFs or top 2-3 names in sector

TIER 3 — MODERATE ALPHA (steady compounders)
═══════════════════════════════════════════════════════════════
7. Dividend Growth + Buyback + Insider
   - Dividend aristocrat with active buyback (dividend-calendar + corporate-actions-calendar)
   - Insider buying on pullback (insider-tracker)
   - Position size: BASE (10-15%)
   - Vehicle: Stock with covered call overlay

8. Crypto Momentum
   - BTC or top alt breaking key technical level (crypto-trading-advisor)
   - On-chain metrics bullish, macro supportive (macro-dashboard)
   - Position size: SPECULATIVE (5-10%)
   - Vehicle: Direct crypto via Alpaca

9. Event-Driven (Spinoffs, M&A, Splits)
   - Upcoming corporate action creating mispricing (corporate-actions-calendar)
   - Forced selling creates opportunity (spinoff from index)
   - Position size: MODERATE (10-15%)
   - Vehicle: Stock
```

## Portfolio Construction: The Aggressive Model

```
╔══════════════════════════════════════════════════════════════╗
║              AGGRESSIVE PORTFOLIO MODEL                      ║
╚══════════════════════════════════════════════════════════════╝

TARGET ALLOCATION
═══════════════════════════════════════════════════════════════
Sleeve              │ Allocation │ Positions │ Strategy
────────────────────┼────────────┼───────────┼────────────────
High Conviction     │ 40-50%     │ 2-3       │ Tier 1 edge plays
Core Momentum       │ 20-30%     │ 3-5       │ Tier 2 trend followers
Asymmetric Bets     │ 10-20%     │ 2-4       │ Options, squeeze plays
Crypto Allocation   │ 5-15%     │ 1-3       │ BTC + 1-2 alts
Cash Reserve        │ 10-15%    │ —         │ Dry powder for drops

Total Positions: 8-15 (concentrated, not diversified)
Portfolio Turnover: Monthly rebalance, tactical trades as needed
═══════════════════════════════════════════════════════════════
```

## Position Sizing: Half-Kelly with Conviction Scaling

```
POSITION SIZING FORMULA
═══════════════════════════════════════════════════════════════

Base Size = Portfolio Value × Kelly Fraction × 0.5 (half-Kelly)

Kelly Fraction = (Win% × Avg_Win/Avg_Loss - Loss%) / (Avg_Win/Avg_Loss)

Conviction Multiplier:
  Alpha Score 80-100:  1.5x base (STRONG conviction → size up)
  Alpha Score 60-79:   1.0x base (standard)
  Alpha Score 40-59:   0.5x base (lower conviction → smaller)
  Alpha Score < 40:    NO TRADE (insufficient edge)

Volatility Adjustment:
  ATR% < 2%:   1.2x (low vol → can size up)
  ATR% 2-4%:   1.0x (normal)
  ATR% 4-6%:   0.7x (high vol → reduce size)
  ATR% > 6%:   0.5x (very high vol → small position)

Example: $100K portfolio
  Win rate: 60%, Avg win: $3K, Avg loss: $1.5K
  Kelly = (0.60 × 2.0 - 0.40) / 2.0 = 0.40 (40%)
  Half-Kelly = 20%
  Alpha Score 85 → 20% × 1.5 = 30% → capped at 25% max
  Position size: $25,000

═══════════════════════════════════════════════════════════════
```

## Stop Loss Framework: "We're Aggressive, Not Stupid"

```
STOP LOSS RULES (NON-NEGOTIABLE)
═══════════════════════════════════════════════════════════════

Every position gets a stop. No exceptions. Period.

Type          │ Stop Level    │ When to Use
──────────────┼───────────────┼─────────────────────────────
Technical     │ Below support │ Default — use nearest support level
ATR-based     │ 2× ATR below │ When support is unclear
Percentage    │ -8% from entry│ Maximum loss per position (hard stop)
Trailing      │ 3× ATR trail │ After position is +10% profitable
Time-based    │ 30 days       │ Exit if thesis hasn't played out

STOP ESCALATION:
  Entry → -8% hard stop (worst case)
  +5% gain → move stop to breakeven
  +10% gain → activate 3× ATR trailing stop
  +20% gain → tighten to 2× ATR trailing stop
  +50% gain → take 50% profit, trail rest with 1.5× ATR

NEVER:
  ✗ Remove a stop loss
  ✗ Average down without re-evaluating thesis
  ✗ Hold through earnings without intention (reduce or hedge)
  ✗ Let a winner become a loser (breakeven stop after +5%)
═══════════════════════════════════════════════════════════════
```

## Daily Aggressive Trading Routine

```
DAILY WORKFLOW
═══════════════════════════════════════════════════════════════

PRE-MARKET (8:00 AM CT)
1. /morning-brief → market pulse, overnight developments
2. /risk-monitor → check portfolio risk, stop levels
3. /scan-market → find today's opportunities
4. Check alpha-signal-aggregator on watchlist stocks
5. Review any triggered alerts from watchlist-manager

MARKET OPEN (8:30 AM CT)
6. Execute pre-planned trades (entries staged night before)
7. Adjust stops on existing positions
8. Monitor unusual options flow (/options-flow-scanner)

MID-DAY (12:00 PM CT)
9. Quick portfolio check — any stops hit?
10. Scan for afternoon setups (breakouts, squeezes)

MARKET CLOSE (3:00 PM CT)
11. Review day's trades → /trade-journal
12. Update signals → /signal-tracker
13. Prepare tomorrow's trade plan

WEEKLY (Sunday Evening)
14. Full portfolio review → /risk-monitor
15. Strategy performance review → /trade-journal analytics
16. Watchlist refresh → add/remove based on scans
17. Regime check → /macro-dashboard
═══════════════════════════════════════════════════════════════
```

## Options Strategies for Aggressive Accounts

```
OPTIONS PLAYBOOK (AGGRESSIVE)
═══════════════════════════════════════════════════════════════

1. DIRECTIONAL CALLS (Primary weapon)
   When: High conviction bullish, Alpha Score >70
   Structure: Buy ATM or slightly OTM calls, 30-60 DTE
   Size: 3-5% of portfolio in premium (controls 3-5× more stock)
   Risk: Limited to premium paid
   Target: 100-300% return on premium

2. PUT SPREADS (Bearish with defined risk)
   When: Short thesis, earnings risk, or hedge
   Structure: Buy ATM put, sell OTM put (define risk)
   Size: 2-3% of portfolio in spread cost
   Risk: Limited to spread width minus premium received
   Target: 50-200% return on risk

3. RISK REVERSALS (Leveraged directional)
   When: Very high conviction, Alpha Score >85
   Structure: Sell OTM put to finance OTM call
   Size: Notional = 15-20% of portfolio
   Risk: Assigned on put = buying stock at discount
   Target: Call side 200-500% if thesis plays out

4. LEAPS (Long-term conviction)
   When: Great company at good price, 12+ month thesis
   Structure: Buy deep ITM calls, 12-24 month expiry
   Size: 10-15% of portfolio (acts like leveraged stock)
   Risk: Premium paid, but deep ITM = high delta = stock-like
   Target: 50-150% return over 12 months

5. STRADDLES/STRANGLES (Pre-event volatility plays)
   When: Big catalyst upcoming, vol is cheap (IV Rank <30)
   Structure: Buy ATM straddle or OTM strangle
   Size: 2-3% of portfolio in premium
   Risk: Limited to premium; need big move to profit
   Target: Works if move > implied move (breakeven)

AVOID:
  ✗ Naked short calls (unlimited risk)
  ✗ Naked short puts on stocks you don't want to own
  ✗ Weekly options (too much gamma risk, bid-ask spread kills)
  ✗ Options on illiquid underlyings (>$0.10 spread)
═══════════════════════════════════════════════════════════════
```

## Crypto Playbook

```
CRYPTO STRATEGY (AGGRESSIVE)
═══════════════════════════════════════════════════════════════

Allocation: 5-15% of portfolio (scale up in bull regime)

Core Holdings (70% of crypto sleeve):
  BTC: 50% — digital gold, macro hedge, institutional adoption
  ETH: 20% — DeFi/smart contract platform

Satellite (30% of crypto sleeve):
  SOL, AVAX, or top alt by momentum — rotate quarterly

Entry Rules:
  - Buy BTC on -15% pullbacks from ATH (DCA over 3 days)
  - Buy ETH on -20% pullbacks
  - Alts only in bull regime (BTC above 200MA)

Exit Rules:
  - Trail 25% below local high (crypto is volatile)
  - Reduce 50% if BTC breaks 200MA
  - Exit alts entirely in bear regime

Sizing:
  Bull regime: 15% of portfolio in crypto
  Neutral regime: 10% of portfolio
  Bear regime: 5% of portfolio (BTC only)

Data: CoinGecko MCP for prices, crypto-trading-advisor for analysis
Execution: Alpaca paper account (crypto enabled)
═══════════════════════════════════════════════════════════════
```

## Performance Tracking & Accountability

```
PERFORMANCE METRICS (Updated via trade-journal)
═══════════════════════════════════════════════════════════════

Track These Weekly:
  - Total Return (vs SPY benchmark)
  - Win Rate (target: >55%)
  - Profit Factor (target: >2.0)
  - Average Winner / Average Loser (target: >2.0)
  - Max Drawdown (circuit breaker at -15%)
  - Sharpe Ratio (target: >1.5)
  - Best/Worst trade of the week
  - Lessons learned (what worked, what didn't)

Monthly Review:
  - Strategy attribution (which edge sources are working?)
  - Regime alignment (are we in the right mode?)
  - Position sizing accuracy (are we sized right?)
  - Stop discipline (did we honor all stops?)
  - Opportunity cost (what did we miss?)

Quarterly Audit:
  - Full strategy backtest validation
  - Compare live results to backtest expectations
  - Adjust strategy parameters if needed
  - Update edge source weights based on actual results
═══════════════════════════════════════════════════════════════
```

## Wealth Milestones (Play Money Growth Targets)

```
MILESTONE TRACKER
═══════════════════════════════════════════════════════════════

Starting Capital: $[USER_AMOUNT]

Target Growth Rate: 30-50% annually (aggressive, but achievable with edge)

Milestones:
  □ First profitable month
  □ First 10% total return
  □ First $1,000 profit
  □ Beat SPY by 10% (YTD)
  □ First $5,000 profit
  □ Double initial capital
  □ First $10,000 profit
  □ Triple initial capital
  □ First $25,000 profit
  □ "Play money" becomes "real money" moment

Each milestone logged to trade-journal.json with date and strategy attribution.
═══════════════════════════════════════════════════════════════
```

## Output Format

When running `/aggressive` or asking for trade ideas:

```
╔══════════════════════════════════════════════════════════════╗
║           AGGRESSIVE ALPHA — TODAY'S TOP PLAYS               ║
║           Portfolio: $XX,XXX | Cash: XX% | Regime: XXXX      ║
╚══════════════════════════════════════════════════════════════╝

REGIME: [BULL/BEAR/SIDEWAYS/VOLATILE]
Strategy Mode: [Momentum/Defensive/Mean Reversion/Tail Risk]

TOP PLAYS (Ranked by Alpha Score)
═══════════════════════════════════════════════════════════════
#  │ Ticker │ Score │ Edge Source       │ Entry  │ Stop   │ Target │ R:R  │ Size
───┼────────┼───────┼───────────────────┼────────┼────────┼────────┼──────┼──────
1  │ NVDA   │ 87    │ Insider+Options   │ $880   │ $810   │ $1050  │ 2.4  │ 25%
2  │ PLTR   │ 78    │ PEAD+Revisions    │ $82    │ $75    │ $105   │ 3.3  │ 18%
3  │ COIN   │ 72    │ Squeeze+Crypto    │ $245   │ $220   │ $320   │ 3.0  │ 12%
4  │ BTC    │ 68    │ Macro+Technical   │ $58K   │ $52K   │ $72K   │ 2.3  │ 10%

CURRENT PORTFOLIO
═══════════════════════════════════════════════════════════════
Position │ Entry   │ Current │ P&L    │ Stop    │ Status
─────────┼─────────┼─────────┼────────┼─────────┼────────
[Current positions from Alpaca]

RISK DASHBOARD
═══════════════════════════════════════════════════════════════
Daily P&L: +/- $XXX (X.X%)
Weekly P&L: +/- $X,XXX (X.X%)
Max Position: XX% (limit: 25%)
Portfolio Beta: X.X (limit: 2.0)
Win Streak: X trades
═══════════════════════════════════════════════════════════════
```

## Integration Points

- `alpha-signal-aggregator` — composite scoring for every trade candidate
- `autonomous-scanner` — find opportunities matching aggressive criteria
- `risk-engine` — pre-trade validation (aggressive limits applied)
- `execution-agent` — place trades with aggressive position sizing
- `trade-journal` — log all trades with strategy attribution
- `signal-tracker` — track thesis evolution for each position
- `regime-adaptive-strategy` — adjust strategy mode automatically
- `portfolio-optimizer` — rebalance aggressive portfolio
- `guru-tracker` — validate against smart money positioning
- `morning-brief` — daily brief with aggressive focus
- `watchlist-manager` — maintain aggressive watchlist with alerts

## Rules

1. EVERY trade needs a thesis written BEFORE entry — log to signal-tracker
2. EVERY position gets a stop loss — no exceptions
3. NEVER risk more than 25% on a single position (even with max conviction)
4. ALWAYS check risk-engine before entering a trade
5. ALWAYS log trades to trade-journal (entries AND exits)
6. If 3 consecutive losses → pause 48 hours, review what's wrong
7. If portfolio drawdown hits -15% → go to 50% cash, full strategy review
8. If portfolio drawdown hits -25% → go to 90% cash, reset strategy
9. Re-evaluate strategy monthly — kill what's not working, double down on what is
10. "Play money" doesn't mean "no discipline" — we're aggressive, not reckless
11. Size up on conviction, NOT on hope
12. Cut losers fast, let winners run — this is the #1 rule of aggressive trading
