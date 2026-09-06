-- Personal CFO Database Schema

-- Accounts
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    account_name TEXT NOT NULL,
    account_type TEXT NOT NULL,
    current_balance REAL NOT NULL,
    available_balance REAL,
    include_in_liquidity INTEGER DEFAULT 1,
    last_updated TEXT NOT NULL,
    created_at TEXT NOT NULL,
    notes TEXT
);

-- Income streams
CREATE TABLE IF NOT EXISTS income (
    income_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    amount REAL NOT NULL,
    frequency TEXT NOT NULL,
    next_expected_date TEXT NOT NULL,
    confidence TEXT DEFAULT 'expected',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    notes TEXT
);

-- Recurring obligations
CREATE TABLE IF NOT EXISTS obligations (
    obligation_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date INTEGER NOT NULL,
    frequency TEXT NOT NULL,
    autopay INTEGER DEFAULT 0,
    account_paid_from TEXT,
    priority TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    notes TEXT
);

-- Transactions ledger
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    merchant TEXT,
    amount REAL NOT NULL,
    transaction_type TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    account TEXT NOT NULL,
    essentiality TEXT,
    source TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

-- Financial goals
CREATE TABLE IF NOT EXISTS goals (
    goal_id TEXT PRIMARY KEY,
    goal_name TEXT NOT NULL,
    goal_type TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0,
    target_date TEXT,
    monthly_contribution_target REAL,
    priority TEXT,
    protected INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    notes TEXT
);

-- Financial settings
CREATE TABLE IF NOT EXISTS financial_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL,
    data_type TEXT,
    updated_at TEXT NOT NULL
);

-- Decision log
CREATE TABLE IF NOT EXISTS decision_log (
    decision_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    decision TEXT NOT NULL,
    amount REAL,
    recommendation TEXT,
    reason TEXT,
    actual_action TEXT,
    follow_up TEXT,
    created_at TEXT NOT NULL
);

-- Data quality tracking
CREATE TABLE IF NOT EXISTS data_quality (
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    value TEXT,
    confidence TEXT,
    last_updated TEXT NOT NULL,
    PRIMARY KEY (entity_type, entity_id, field_name)
);

-- Create indices for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_obligations_due_date ON obligations(due_date);
CREATE INDEX IF NOT EXISTS idx_income_next_expected ON income(next_expected_date);
