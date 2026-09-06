"""
Database Layer
Handles persistent storage and retrieval of financial state.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from calculations import (
    Account, IncomeStream, Obligation, Transaction, Goal, 
    FinancialFloor, Frequency
)


class Database:
    """SQLite-backed persistent financial state."""
    
    def __init__(self, db_path: str = "finance.db"):
        self.db_path = db_path
        self.conn = None
        self.init_db()
    
    def init_db(self):
        """Initialize database connection and create schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        # Load and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                self.conn.executescript(f.read())
            self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    # ACCOUNT OPERATIONS
    def add_account(self, account: Account):
        """Add a new account."""
        self.conn.execute("""
            INSERT INTO accounts 
            (account_id, account_name, account_type, current_balance, 
             available_balance, include_in_liquidity, last_updated, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account.account_id,
            account.name,
            account.account_type,
            account.balance,
            account.available_balance,
            1 if account.include_in_liquidity else 0,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
        ))
        self.conn.commit()
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """Retrieve an account."""
        row = self.conn.execute(
            "SELECT * FROM accounts WHERE account_id = ?",
            (account_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return Account(
            account_id=row['account_id'],
            name=row['account_name'],
            account_type=row['account_type'],
            balance=row['current_balance'],
            available_balance=row['available_balance'],
            include_in_liquidity=bool(row['include_in_liquidity']),
        )
    
    def get_all_accounts(self) -> List[Account]:
        """Retrieve all accounts."""
        rows = self.conn.execute(
            "SELECT * FROM accounts ORDER BY created_at"
        ).fetchall()
        
        return [
            Account(
                account_id=row['account_id'],
                name=row['account_name'],
                account_type=row['account_type'],
                balance=row['current_balance'],
                available_balance=row['available_balance'],
                include_in_liquidity=bool(row['include_in_liquidity']),
            )
            for row in rows
        ]
    
    def update_account_balance(self, account_id: str, new_balance: float):
        """Update account balance."""
        self.conn.execute("""
            UPDATE accounts 
            SET current_balance = ?, last_updated = ?
            WHERE account_id = ?
        """, (new_balance, datetime.now().isoformat(), account_id))
        self.conn.commit()
    
    # INCOME OPERATIONS
    def add_income_stream(self, income: IncomeStream):
        """Add an income stream."""
        self.conn.execute("""
            INSERT INTO income
            (income_id, source, amount, frequency, next_expected_date, 
             confidence, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            income.income_id,
            income.source,
            income.amount,
            income.frequency.value,
            income.next_expected_date,
            income.confidence,
            1 if income.is_active else 0,
            datetime.now().isoformat(),
        ))
        self.conn.commit()
    
    def get_all_active_income(self) -> List[IncomeStream]:
        """Get all active income streams."""
        rows = self.conn.execute(
            "SELECT * FROM income WHERE is_active = 1 ORDER BY next_expected_date"
        ).fetchall()
        
        return [
            IncomeStream(
                income_id=row['income_id'],
                source=row['source'],
                amount=row['amount'],
                frequency=Frequency(row['frequency']),
                next_expected_date=row['next_expected_date'],
                is_active=bool(row['is_active']),
                confidence=row['confidence'],
            )
            for row in rows
        ]
    
    # OBLIGATION OPERATIONS
    def add_obligation(self, obligation: Obligation):
        """Add a recurring obligation."""
        self.conn.execute("""
            INSERT INTO obligations
            (obligation_id, name, category, amount, due_date, frequency,
             autopay, account_paid_from, priority, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            obligation.obligation_id,
            obligation.name,
            obligation.category,
            obligation.amount,
            obligation.due_date,
            obligation.frequency.value,
            1 if obligation.autopay else 0,
            obligation.account_paid_from,
            obligation.priority,
            1 if obligation.is_active else 0,
            datetime.now().isoformat(),
        ))
        self.conn.commit()
    
    def get_all_active_obligations(self) -> List[Obligation]:
        """Get all active obligations."""
        rows = self.conn.execute(
            "SELECT * FROM obligations WHERE is_active = 1 ORDER BY due_date"
        ).fetchall()
        
        return [
            Obligation(
                obligation_id=row['obligation_id'],
                name=row['name'],
                category=row['category'],
                amount=row['amount'],
                due_date=row['due_date'],
                frequency=Frequency(row['frequency']),
                priority=row['priority'],
                is_active=bool(row['is_active']),
                autopay=bool(row['autopay']),
                account_paid_from=row['account_paid_from'],
            )
            for row in rows
        ]
    
    # TRANSACTION OPERATIONS
    def add_transaction(self, transaction: Transaction):
        """Record a transaction."""
        self.conn.execute("""
            INSERT INTO transactions
            (transaction_id, date, description, merchant, amount, 
             transaction_type, category, subcategory, account, 
             essentiality, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction.transaction_id,
            transaction.date,
            transaction.description,
            transaction.merchant,
            transaction.amount,
            transaction.transaction_type,
            transaction.category,
            transaction.subcategory,
            transaction.account,
            transaction.essentiality,
            transaction.source,
            datetime.now().isoformat(),
        ))
        self.conn.commit()
    
    def get_transactions_in_range(
        self,
        start_date: str,
        end_date: str,
        transaction_type: Optional[str] = None,
    ) -> List[Transaction]:
        """Get transactions in a date range."""
        query = """
            SELECT * FROM transactions
            WHERE date >= ? AND date <= ?
        """
        params = [start_date, end_date]
        
        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type)
        
        query += " ORDER BY date DESC"
        rows = self.conn.execute(query, params).fetchall()
        
        return [
            Transaction(
                transaction_id=row['transaction_id'],
                date=row['date'],
                description=row['description'],
                amount=row['amount'],
                transaction_type=row['transaction_type'],
                category=row['category'],
                account=row['account'],
                essentiality=row['essentiality'],
                merchant=row['merchant'],
            )
            for row in rows
        ]
    
    # GOAL OPERATIONS
    def add_goal(self, goal: Goal):
        """Add a financial goal."""
        self.conn.execute("""
            INSERT INTO goals
            (goal_id, goal_name, goal_type, target_amount, current_amount,
             target_date, monthly_contribution_target, priority, 
             protected, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal.goal_id,
            goal.name,
            goal.goal_type,
            goal.target_amount,
            goal.current_amount,
            goal.target_date,
            goal.monthly_contribution_target,
            goal.priority,
            1 if goal.protected else 0,
            1,
            datetime.now().isoformat(),
        ))
        self.conn.commit()
    
    def get_all_active_goals(self) -> List[Goal]:
        """Get all active goals."""
        rows = self.conn.execute(
            "SELECT * FROM goals WHERE is_active = 1 ORDER BY priority DESC"
        ).fetchall()
        
        return [
            Goal(
                goal_id=row['goal_id'],
                name=row['goal_name'],
                goal_type=row['goal_type'],
                target_amount=row['target_amount'],
                current_amount=row['current_amount'],
                target_date=row['target_date'],
                monthly_contribution_target=row['monthly_contribution_target'],
                priority=row['priority'],
                protected=bool(row['protected']),
            )
            for row in rows
        ]
    
    # SETTINGS OPERATIONS
    def set_financial_floor(self, emergency_reserve: float, operating_buffer: float):
        """Set the financial floor."""
        self.conn.execute(
            "DELETE FROM financial_settings WHERE setting_key IN (?, ?)",
            ("emergency_reserve", "operating_buffer")
        )
        self.conn.execute("""
            INSERT INTO financial_settings (setting_key, setting_value, data_type, updated_at)
            VALUES (?, ?, ?, ?)
        """, ("emergency_reserve", str(emergency_reserve), "float", datetime.now().isoformat()))
        self.conn.execute("""
            INSERT INTO financial_settings (setting_key, setting_value, data_type, updated_at)
            VALUES (?, ?, ?, ?)
        """, ("operating_buffer", str(operating_buffer), "float", datetime.now().isoformat()))
        self.conn.commit()
    
    def get_financial_floor(self) -> FinancialFloor:
        """Get the financial floor."""
        emergency = self.conn.execute(
            "SELECT setting_value FROM financial_settings WHERE setting_key = 'emergency_reserve'"
        ).fetchone()
        operating = self.conn.execute(
            "SELECT setting_value FROM financial_settings WHERE setting_key = 'operating_buffer'"
        ).fetchone()
        
        return FinancialFloor(
            emergency_reserve=float(emergency['setting_value']) if emergency else 3000,
            operating_buffer=float(operating['setting_value']) if operating else 1000,
        )
    
    def log_decision(
        self,
        decision_id: str,
        decision: str,
        amount: Optional[float],
        recommendation: str,
        reason: str,
    ):
        """Log a financial decision."""
        self.conn.execute("""
            INSERT INTO decision_log
            (decision_id, date, decision, amount, recommendation, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            decision_id,
            datetime.now().isoformat(),
            decision,
            amount,
            recommendation,
            reason,
            datetime.now().isoformat(),
        ))
        self.conn.commit()
