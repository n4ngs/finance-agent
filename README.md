# Personal CFO - Financial Operating System

A deterministic, auditable personal finance system built on structured state and code-based calculations.

## Philosophy

**Safe to Spend is the central metric.**

```
Liquid Cash
- Upcoming Obligations
- Credit Card Balances  
- Savings/Investment Targets
- Financial Floor
- Planned Purchases
= SAFE TO SPEND
```

This answers: Given everything I know about my finances, what can I safely do with my money?

## Architecture

```
Financial State → Calculation Engine → Decision Engine
                  + Database          + Claude Reasoning
                  + Forecasting       + Natural Language Router
                  + Scenarios         + CLI Interface
```

**Key principle:** Code for math, Claude for judgment.

## Core Components

### `calculations.py`
- **Deterministic financial calculations**
- SAFE_TO_SPEND calculation
- 30/90-day cash flow forecasting
- Purchase evaluation
- Anomaly detection
- All calculations are reproducible and auditable

### `database.py`
- SQLite-backed persistent state
- Accounts, income, obligations, transactions, goals
- Clean separation of state from logic

### `cfo.py`
- Main orchestrator
- Five-phase onboarding
- Status queries
- Purchase evaluation
- Scenario simulation

### `router.py`
- Natural language request classification
- Extracts amounts, merchants, dates
- Routes to appropriate handlers

### `cli.py`
- Interactive command-line interface
- Handles onboarding
- Processes user requests
- Formats output

## Getting Started

### Phase 1: Run the Demo

```bash
python3 cfo.py
```

This initializes with synthetic data:
- Checking: $6,820
- Savings: $1,000
- Credit Card: $1,040
- Obligations: Rent, utilities
- Next payday: 12 days out

Evaluates two purchases:
- "$2,749 Laptop" → Should you buy it?
- "$500 Weekend" → Is this safe?

### Phase 2: Interactive CLI

```bash
python3 cli.py
```

Walk through five-step onboarding:
1. Current account balances
2. Income (paycheck amount, frequency)
3. Recurring obligations (rent, bills, etc.)
4. Financial goals (emergency fund target)
5. Financial floor (minimum cash to maintain)

Then ask:
- "How am I doing?"
- "Can I spend $500 this weekend?"
- "Buy a $2,749 laptop"
- "What if I also take a $1,500 trip?"

## Features - Phase 1

✓ Persistent financial state (SQLite)
✓ Deterministic safe-to-spend calculation
✓ 30/90-day cash flow forecasting
✓ Purchase evaluation ("Buy", "Buy but Wait", "Wait", "Skip")
✓ Financial floor protection
✓ Natural language request routing
✓ Interactive CLI with onboarding
✓ Transaction logging
✓ Decision auditing

## Design Decisions

### Time as First-Class Concept
Forecasts calculate the **lowest projected balance** in the forecast window, not just today's balance. This is critical because:
- "I have $7,000 today" doesn't tell you if you're safe if rent is due in 5 days and payday is day 12
- The minimum balance point is what matters

### No Double-Counting
Credit card payments aren't counted twice (once as expense, once as payment). The system tracks which transactions reduce which balance.

### Materiality
Small purchases don't trigger the same analysis depth as large ones. Analysis scales by:
- Purchase ÷ monthly income
- Purchase ÷ safe-to-spend
- Impact on financial floor

### Not Needlessly Frugal
If you can afford something safely, the system says so. It doesn't manufacture guilt. Its job is to protect financial security while maximizing your ability to enjoy money.

## Future Phases

Phase 2-5: Detailed specifications in the original brief
- Advanced forecasting with spending variance
- Scenario simulation engine
- Spending intelligence & anomaly detection
- Subscription auditor
- Debt payoff strategies
- Goal trajectory tracking
- Monthly/quarterly reviews

## Testing

```bash
cd /Users/cmanlongat/Documents/Claude\ Code/finance-agent
python3 cfo.py        # Run demo
python3 router.py     # Test natural language router
# python3 cli.py      # Interactive (requires user input)
```

## Data Storage

All data lives in `finance.db` (SQLite).

The database is designed to:
- Never require storing passwords, PINs, or full card numbers
- Support arbitrary account types and custom categories
- Track data confidence (confirmed vs. estimated vs. stale)
- Enable auditability (when calculated, why, what assumptions)

## Auditability

Every calculated number is reproducible. Ask "Why?" and get the formula:

```
Safe to Spend = $4,710

Breakdown:
  Liquid Cash:                  $7,820
  - Upcoming Bills (30d):      -$2,310
  - Card Obligations:          -$1,040
  - Savings Commitment:          -$750
  - Investment Commitment:       -$500
  - Financial Floor:           -$1,500
  = Safe to Spend:              $4,710
```

## Next Steps

1. Run `python3 cfo.py` to see the demo
2. Run `python3 cli.py` for interactive mode
3. Extend with:
   - CSV transaction import
   - Receipt parsing
   - Bank statement import
   - Real Claude integration for reasoning layer
