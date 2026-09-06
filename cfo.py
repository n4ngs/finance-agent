"""
Personal CFO Application
Main orchestrator that uses calculation engine and database.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from database import Database
from calculations import (
    CalculationEngine, Account, IncomeStream, Obligation, Transaction,
    Goal, FinancialFloor, SafeToSpend, Forecast, Frequency
)


class PersonalCFO:
    """The Personal CFO application."""
    
    def __init__(self, db_path: str = "finance.db"):
        self.db = Database(db_path)
        self.calc = CalculationEngine()
    
    def close(self):
        """Close the application."""
        self.db.close()
    
    # INITIALIZATION PHASE 1: CURRENT POSITION
    def set_current_position(
        self,
        accounts: List[Dict[str, Any]],
    ):
        """
        Onboarding Step 1: Set current account balances.
        
        Each account dict should have:
        - name: str
        - account_type: checking, savings, credit_card, etc.
        - balance: float
        - include_in_liquidity: bool (default True)
        """
        for account_data in accounts:
            account = Account(
                account_id=str(uuid.uuid4()),
                name=account_data['name'],
                account_type=account_data['account_type'],
                balance=account_data['balance'],
                include_in_liquidity=account_data.get('include_in_liquidity', True),
            )
            self.db.add_account(account)
    
    # INITIALIZATION PHASE 2: INCOME
    def set_income_streams(
        self,
        income_streams: List[Dict[str, Any]],
    ):
        """
        Onboarding Step 2: Set up income.
        
        Each income dict should have:
        - source: str
        - amount: float
        - frequency: weekly, biweekly, semimonthly, monthly, etc.
        - next_expected_date: YYYY-MM-DD
        """
        for income_data in income_streams:
            income = IncomeStream(
                income_id=str(uuid.uuid4()),
                source=income_data['source'],
                amount=income_data['amount'],
                frequency=Frequency(income_data['frequency']),
                next_expected_date=income_data['next_expected_date'],
            )
            self.db.add_income_stream(income)
    
    # INITIALIZATION PHASE 3: RECURRING OBLIGATIONS
    def set_obligations(
        self,
        obligations: List[Dict[str, Any]],
    ):
        """
        Onboarding Step 3: Set recurring obligations.
        
        Each obligation dict should have:
        - name: str
        - category: housing, car, insurance, etc.
        - amount: float
        - due_date: day of month (1-31)
        - frequency: monthly, biweekly, etc.
        - priority: essential, important, optional
        """
        for ob_data in obligations:
            obligation = Obligation(
                obligation_id=str(uuid.uuid4()),
                name=ob_data['name'],
                category=ob_data['category'],
                amount=ob_data['amount'],
                due_date=ob_data['due_date'],
                frequency=Frequency(ob_data['frequency']),
                priority=ob_data['priority'],
            )
            self.db.add_obligation(obligation)
    
    # INITIALIZATION PHASE 4: GOALS
    def set_goals(
        self,
        goals: List[Dict[str, Any]],
    ):
        """
        Onboarding Step 4: Set financial goals.
        
        Each goal dict should have:
        - name: str
        - goal_type: emergency_fund, investment, major_purchase, etc.
        - target_amount: float
        - target_date: YYYY-MM-DD (optional)
        - monthly_contribution_target: float (optional)
        """
        for goal_data in goals:
            goal = Goal(
                goal_id=str(uuid.uuid4()),
                name=goal_data['name'],
                goal_type=goal_data['goal_type'],
                target_amount=goal_data['target_amount'],
                current_amount=goal_data.get('current_amount', 0),
                target_date=goal_data.get('target_date'),
                monthly_contribution_target=goal_data.get('monthly_contribution_target'),
            )
            self.db.add_goal(goal)
    
    # INITIALIZATION PHASE 5: FINANCIAL FLOOR
    def set_financial_floor(
        self,
        emergency_reserve: float,
        operating_buffer: float,
    ):
        """
        Onboarding Step 5: Set the financial floor.
        
        This is the minimum liquid cash that should normally never be crossed.
        """
        self.db.set_financial_floor(emergency_reserve, operating_buffer)
    
    # STATUS QUERIES
    def get_status(self) -> Dict[str, Any]:
        """
        Return current financial status.
        Answers: Where am I?
        """
        accounts = self.db.get_all_accounts()
        obligations = self.db.get_all_active_obligations()
        income_streams = self.db.get_all_active_income()
        goals = self.db.get_all_active_goals()
        floor = self.db.get_financial_floor()
        
        # Calculate liquidity
        liquid_cash = self.calc.calculate_liquidity(accounts)
        
        # Calculate upcoming obligations (next 30 days)
        upcoming_30d, _ = self.calc.calculate_daily_obligations_30d(
            obligations,
            datetime.now().isoformat()[:10]
        )
        
        # Calculate safe to spend
        # For now, simple estimate
        savings_target = sum(g.monthly_contribution_target for g in goals if g.monthly_contribution_target)
        
        safe_to_spend = self.calc.calculate_safe_to_spend(
            liquid_cash=liquid_cash,
            upcoming_obligations_30d=upcoming_30d,
            card_balances=self._calculate_credit_card_balance(accounts),
            savings_target_monthly=savings_target or 0,
            investment_target_monthly=0,  # TODO: extract from goals
            financial_floor=floor,
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "liquid_cash": liquid_cash,
            "financial_floor": {
                "emergency_reserve": floor.emergency_reserve,
                "operating_buffer": floor.operating_buffer,
                "total": floor.total,
            },
            "safe_to_spend": {
                "total": safe_to_spend.total_safe_to_spend,
                "breakdown": safe_to_spend.breakdown(),
            },
            "accounts": [
                {
                    "name": acc.name,
                    "type": acc.account_type,
                    "balance": acc.balance,
                }
                for acc in accounts
            ],
            "upcoming_obligations_30d": upcoming_30d,
            "active_income_streams": len([s for s in income_streams if s.is_active]),
            "active_goals": len(goals),
        }
    
    def evaluate_purchase(
        self,
        amount: float,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Can I buy this?
        Answers: What happens if I do X?
        """
        accounts = self.db.get_all_accounts()
        obligations = self.db.get_all_active_obligations()
        goals = self.db.get_all_active_goals()
        floor = self.db.get_financial_floor()
        
        liquid_cash = self.calc.calculate_liquidity(accounts)
        upcoming_30d, _ = self.calc.calculate_daily_obligations_30d(
            obligations,
            datetime.now().isoformat()[:10]
        )
        
        savings_target = sum(g.monthly_contribution_target for g in goals if g.monthly_contribution_target)
        
        safe_to_spend = self.calc.calculate_safe_to_spend(
            liquid_cash=liquid_cash,
            upcoming_obligations_30d=upcoming_30d,
            card_balances=self._calculate_credit_card_balance(accounts),
            savings_target_monthly=savings_target or 0,
            investment_target_monthly=0,
            financial_floor=floor,
        )
        
        # Generate a simple 30-day forecast
        forecast = self.calc.forecast_cash_flow(
            starting_balance=liquid_cash,
            income_streams=self.db.get_all_active_income(),
            obligations=obligations,
            expected_spending_daily=50,  # TODO: calculate from history
            from_date=datetime.now().isoformat()[:10],
            days_ahead=30,
        )
        
        result = self.calc.evaluate_purchase(
            purchase_amount=amount,
            current_safe_to_spend=safe_to_spend.total_safe_to_spend,
            current_liquid_balance=liquid_cash,
            forecast_30d=forecast,
            financial_floor=floor,
        )
        
        result['description'] = description
        result['timestamp'] = datetime.now().isoformat()
        
        return result
    
    def record_transaction(
        self,
        date: str,
        description: str,
        amount: float,
        transaction_type: str,
        category: str,
        account: str,
        merchant: Optional[str] = None,
    ):
        """
        Record a transaction.
        """
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            date=date,
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            account=account,
            merchant=merchant,
        )
        self.db.add_transaction(transaction)
    
    def sync_plaid_accounts_and_transactions(self, plaid_connector) -> Dict[str, Any]:
        """
        Sync all Plaid-linked bank accounts and transactions.

        This is called periodically to:
        1. Fetch all accounts from all Plaid connections
        2. Update balances
        3. Fetch new/updated transactions
        4. Import them into our database
        """
        if not plaid_connector.is_configured():
            return {"error": "Plaid not configured"}

        plaid_items = self.db.get_all_plaid_items()
        if not plaid_items:
            return {"accounts_synced": 0, "transactions_synced": 0}

        total_accounts = 0
        total_transactions = 0

        for item in plaid_items:
            access_token = item['access_token']

            # Sync accounts and balances
            accounts = plaid_connector.fetch_accounts(access_token)
            for acc in accounts:
                self.db.upsert_plaid_account(
                    plaid_account_id=acc['plaid_account_id'],
                    plaid_item_id=item['item_id'],
                    name=acc['name'],
                    account_type=acc['account_type'],
                    balance=acc['balance'],
                    available_balance=acc['available_balance'],
                )
                total_accounts += 1

            # Sync transactions incrementally
            cursor = item.get('sync_cursor')
            result = plaid_connector.fetch_transactions(access_token, cursor)

            for txn in result['added'] + result['modified']:
                transaction = Transaction(
                    transaction_id=str(uuid.uuid4()),
                    date=txn['date'],
                    description=txn['description'],
                    amount=txn['amount'],
                    transaction_type=txn['transaction_type'],
                    category=txn['category'],
                    account=txn['plaid_account_id'],
                    merchant=txn.get('merchant'),
                )
                self.db.upsert_plaid_transaction(
                    transaction,
                    plaid_transaction_id=txn['plaid_transaction_id'],
                    pending=txn.get('pending', False),
                )
                total_transactions += 1

            # Update sync cursor
            if result.get('next_cursor'):
                self.db.update_plaid_cursor(item['item_id'], result['next_cursor'])

        return {
            "accounts_synced": total_accounts,
            "transactions_synced": total_transactions,
        }

    def _calculate_credit_card_balance(self, accounts: List[Account]) -> float:
        """Calculate total credit card debt."""
        return sum(
            acc.balance
            for acc in accounts
            if acc.account_type == "credit_card" and acc.balance > 0
        )


if __name__ == "__main__":
    # Demo: Initialize with synthetic data
    cfo = PersonalCFO()
    
    # Phase 1: Current position
    cfo.set_current_position([
        {
            "name": "Checking",
            "account_type": "checking",
            "balance": 6820,
            "include_in_liquidity": True,
        },
        {
            "name": "Savings",
            "account_type": "savings",
            "balance": 1000,
            "include_in_liquidity": True,
        },
        {
            "name": "Credit Card",
            "account_type": "credit_card",
            "balance": 1040,
        },
    ])
    
    # Phase 2: Income
    today = datetime.now()
    next_payday = today + timedelta(days=12)
    
    cfo.set_income_streams([
        {
            "source": "Salary",
            "amount": 4200,
            "frequency": "biweekly",
            "next_expected_date": next_payday.isoformat()[:10],
        }
    ])
    
    # Phase 3: Obligations
    cfo.set_obligations([
        {
            "name": "Rent",
            "category": "housing",
            "amount": 2000,
            "due_date": 1,
            "frequency": "monthly",
            "priority": "essential",
        },
        {
            "name": "Electricity",
            "category": "utilities",
            "amount": 140,
            "due_date": 15,
            "frequency": "monthly",
            "priority": "essential",
        },
        {
            "name": "Internet",
            "category": "utilities",
            "amount": 75,
            "due_date": 20,
            "frequency": "monthly",
            "priority": "important",
        },
    ])
    
    # Phase 4: Goals
    cfo.set_goals([
        {
            "name": "Emergency Fund",
            "goal_type": "emergency_fund",
            "target_amount": 20000,
            "current_amount": 14500,
            "monthly_contribution_target": 750,
        }
    ])
    
    # Phase 5: Financial floor
    cfo.set_financial_floor(emergency_reserve=3500, operating_buffer=1500)
    
    # Query status
    status = cfo.get_status()
    print("\n=== FINANCIAL STATUS ===")
    print(f"Liquid Cash: ${status['liquid_cash']:,.2f}")
    print(f"Financial Floor: ${status['financial_floor']['total']:,.2f}")
    print(f"Safe to Spend: ${status['safe_to_spend']['total']:,.2f}")
    
    # Test purchase evaluation
    print("\n=== PURCHASE EVALUATION: $2,749 Laptop ===")
    result = cfo.evaluate_purchase(2749, "MacBook Pro")
    print(f"Current Safe to Spend: ${result['current_safe_to_spend']:,.2f}")
    print(f"After Purchase: ${result['after_purchase_safe_to_spend']:,.2f}")
    print(f"30-day Minimum: ${result['current_30d_minimum']:,.2f}")
    print(f"Recommendation: {result['recommendation']}")
    
    print("\n=== PURCHASE EVALUATION: $500 Weekend ===")
    result = cfo.evaluate_purchase(500, "Weekend spending")
    print(f"Current Safe to Spend: ${result['current_safe_to_spend']:,.2f}")
    print(f"After Purchase: ${result['after_purchase_safe_to_spend']:,.2f}")
    print(f"Recommendation: {result['recommendation']}")
    
    cfo.close()
