# Personal CFO - Architecture Guide

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Natural Language Interface (CLI)               │
│                      router.py / cli.py                      │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            Decision & Orchestration Layer                   │
│                        cfo.py                                │
│  - Coordinates calculations and state management            │
│  - Handles purchase evaluations                             │
│  - Manages scenario simulations                             │
└─────────────────────────────────────────────────────────────┘
           ▲                                      ▲
           │                                      │
           ▼                                      ▼
┌──────────────────────────┐      ┌───────────────────────────┐
│  Calculation Engine      │      │   Database Layer          │
│   (calculations.py)      │      │   (database.py)           │
│                          │      │                           │
│ • SafeToSpend            │      │ • Accounts                │
│ • Forecasting            │      │ • Income                  │
│ • Purchase Evaluation    │      │ • Obligations             │
│ • Anomaly Detection      │      │ • Transactions            │
│                          │      │ • Goals                   │
│ DETERMINISTIC & AUDITABLE│      │ • Settings                │
└──────────────────────────┘      └───────────────────────────┘
                                           ▲
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │   SQLite DB     │
                                  │  (finance.db)   │
                                  └─────────────────┘
```

## Module Breakdown

### `calculations.py` - The Math Engine
**Purpose:** Deterministic financial calculations

**Key Classes:**
- `CalculationEngine`: All financial math lives here
  - `calculate_liquidity()` → Total available funds
  - `calculate_safe_to_spend()` → Core metric
  - `calculate_daily_obligations_30d()` → What's due soon
  - `forecast_cash_flow()` → Project future balances
  - `evaluate_purchase()` → Should I buy this?

**Philosophy:**
- Zero tolerance for floating-point surprises
- Every calculation is reproducible
- All math is testable and auditable

**Example:**
```python
engine = CalculationEngine()
safe_to_spend = engine.calculate_safe_to_spend(
    liquid_cash=10000,
    upcoming_obligations_30d=2000,
    card_balances=1000,
    savings_target_monthly=500,
    investment_target_monthly=500,
    financial_floor=FinancialFloor(3000, 1000),
)
# Returns: SafeToSpend with breakdown
```

### `database.py` - Persistent State
**Purpose:** Store and retrieve financial data

**Key Classes:**
- `Database`: SQLite interface
  - `add_account()`, `get_account()`, `get_all_accounts()`
  - `add_income_stream()`, `get_all_active_income()`
  - `add_obligation()`, `get_all_active_obligations()`
  - `add_transaction()`, `get_transactions_in_range()`
  - `add_goal()`, `get_all_active_goals()`

**Schema (schema.sql):**
- `accounts` - Bank/credit accounts
- `income` - Paychecks and other income
- `obligations` - Bills and recurring expenses
- `transactions` - Spending history
- `goals` - Financial targets
- `financial_settings` - User preferences
- `decision_log` - Audit trail

**Philosophy:**
- Single source of truth
- No secrets stored (no passwords, PINs, full card numbers)
- Data confidence tracking (confirmed vs. estimated)

### `cfo.py` - The Orchestrator
**Purpose:** Tie calculation engine and database together

**Key Classes:**
- `PersonalCFO`: Main application class
  - `set_current_position()` - Step 1: Account balances
  - `set_income_streams()` - Step 2: Paychecks
  - `set_obligations()` - Step 3: Bills
  - `set_goals()` - Step 4: Targets
  - `set_financial_floor()` - Step 5: Safety level
  - `get_status()` - Current financial snapshot
  - `evaluate_purchase()` - Buy/don't buy decisions
  - `record_transaction()` - Log spending

**Five-Phase Onboarding:**
```
Phase 1: Current Position (account balances)
Phase 2: Income (paycheck amount & frequency)
Phase 3: Obligations (rent, bills, subscriptions)
Phase 4: Goals (emergency fund, investments)
Phase 5: Financial Floor (safety net)
```

### `router.py` - Natural Language Router
**Purpose:** Understand user intent and extract parameters

**Key Classes:**
- `ConversationRouter`: Classify and route requests
  - Detects request type (buy, spend, status, etc.)
  - Extracts dollar amounts
  - Identifies merchants
  - Parses transaction lists

**Request Types:**
- `STATUS` - How am I doing?
- `SPEND` - How much can I spend?
- `BUY` - Should I buy this?
- `PAYDAY` - Allocate paycheck
- `SPENDING_UPDATE` - Record expenses
- `SCENARIO` - What if I do X?
- `FORECAST` - Project ahead
- `MONTHLY_REVIEW` - Summary

### `cli.py` - Interactive Interface
**Purpose:** User-friendly command-line experience

**Key Classes:**
- `CFOCLI`: Command-line interface
  - Onboarding flow
  - Request handling
  - Result formatting
  - Help system

**Features:**
- Five-step guided setup
- Natural language parsing
- Formatted output
- Command-based shortcuts (/status, /buy, etc.)

### `scenarios.py` - What-If Simulation
**Purpose:** Compare financial decisions

**Key Classes:**
- `ScenarioSimulator`: Run scenarios
  - `compare_scenarios()` - Compare multiple futures
  - `rank_scenarios()` - Order by feasibility
  - `evaluate_scenario()` - Impact calculation

### `main.py` - Entry Point
**Purpose:** Start the application

```bash
python3 main.py
```

## Data Flow Examples

### Example 1: User Asks "Can I spend $500?"

```
User Input: "Can I spend $500?"
        ↓
    Router detects: SPEND request
        ↓
    CFO.get_status() retrieves:
    • Accounts from DB
    • Obligations (next 30d) from DB
    • Goals from DB
        ↓
    Engine.calculate_liquidity(accounts)
    Engine.calculate_daily_obligations_30d(obligations)
    Engine.calculate_safe_to_spend(...)
        ↓
    Return: "$500 is within your $2,100 safe-to-spend capacity"
```

### Example 2: User Asks "Buy a $2,749 laptop"

```
User Input: "Buy a $2,749 MacBook"
        ↓
    Router detects: BUY request, amount=$2,749
        ↓
    CFO.evaluate_purchase(2749)
        ↓
    Engine retrieves/calculates:
    • Current liquidity
    • 30-day obligations forecast
    • 30/90-day cash flow projection
    • Impact on financial floor
        ↓
    Engine.evaluate_purchase() determines:
    • Affordability: HIGH/MODERATE/LOW
    • Recommendation: BUY/WAIT/SKIP
    • Reason: "After purchase, headroom is $1,200"
        ↓
    Return: "BUY - You have comfortable capacity"
```

### Example 3: Scenario Simulation

```
User: "What if I buy the laptop AND take a $1,500 trip?"
        ↓
    Router detects: SCENARIO request
        ↓
    Simulator compares:
    • BASELINE (no changes)
    • LAPTOP ONLY (-$2,749)
    • TRIP ONLY (-$1,500)
    • LAPTOP + TRIP (-$4,249)
        ↓
    For each scenario:
    • Project 30/90-day cash flow
    • Calculate minimum balance
    • Check against financial floor
    • Calculate goal delays
        ↓
    Return ranked scenarios:
    "BASELINE: Comfortable"
    "TRIP ONLY: Still comfortable"
    "LAPTOP ONLY: Tight but OK"
    "BOTH: Stress, consider waiting"
```

## Integration Points (Future)

### Plaid Integration (Coming Soon)
```
Plaid API
    ↓
Auto-fetch accounts, balances, transactions
    ↓
Update Database
    ↓
Recalculate Safe-to-Spend automatically
```

### CSV Import
```
Bank export (CSV/OFX)
    ↓
Parse transactions
    ↓
Categorize automatically (ML later)
    ↓
Populate history
```

### Claude AI Integration
```
Chat interface
    ↓
Send financials + question to Claude
    ↓
Claude reasons about tradeoffs
    ↓
Return natural explanations
```

## Key Design Decisions

### 1. Separation of Concerns
- **Calculations** (math) separate from **State** (database)
- **Routing** (input) separate from **Logic** (decisions)
- **CLI** (presentation) separate from **CFO** (orchestration)

### 2. Time is First-Class
- Forecasts compute lowest balance point, not just today
- Obligations are dated (when due, not just "monthly")
- Decisions account for timing ("wait until payday")

### 3. No Double-Counting
- Credit card balance represents obligation, not separate from card transactions
- Transfers between own accounts don't count as spending
- Income is "expected" vs "received"

### 4. Materiality
- $50 and $5,000 purchases get different levels of analysis
- Spending drift detection is normalized (31% increase vs actual baseline)
- Obligations are tiered by priority

### 5. Auditability
- Every number has a formula
- Data includes confidence levels
- Decision log tracks all major choices
- Calculations can be reproduced

## Testing Strategy

```
tests.py includes:
✓ Liquidity calculations
✓ Safe-to-spend edge cases (zero, negative, large purchases)
✓ Obligation forecasting
✓ Purchase evaluation (affordable, breaks floor, etc.)
✓ Double-counting prevention
✓ Data integrity
```

Run: `python3 tests.py`

## Performance Characteristics

**Current Phase 1:**
- Sub-millisecond calculations
- SQLite queries <1ms for typical datasets
- Full status refresh: ~10ms
- Scales to 10+ years of transaction history

**Bottleneck (if any):** Forecasting with ML-based spending predictions (Phase 3+)

## Security Considerations

**What we DON'T store:**
- Banking passwords
- PINs
- Full credit card numbers
- SSN
- API keys (for Plaid, etc.)

**What we DO encrypt (future):**
- Sensitive field values at rest
- Database connection

**What we AUDIT:**
- All financial decisions
- Who accessed what
- When state changed
