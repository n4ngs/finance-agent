"""
Validation Tests for Personal CFO
Tests critical financial calculations and edge cases.
"""

import unittest
from datetime import datetime, timedelta
from calculations import (
    CalculationEngine, Account, IncomeStream, Obligation, Transaction,
    FinancialFloor, Frequency
)


class TestCalculationEngine(unittest.TestCase):
    """Test the financial calculation engine."""
    
    def setUp(self):
        self.calc = CalculationEngine()
    
    def test_liquidity_calculation(self):
        """Test liquid cash calculation."""
        accounts = [
            Account("c1", "Checking", "checking", 1000, include_in_liquidity=True),
            Account("s1", "Savings", "savings", 2000, include_in_liquidity=True),
            Account("cc1", "CC", "credit_card", 500, include_in_liquidity=False),
        ]
        
        liquidity = self.calc.calculate_liquidity(accounts)
        self.assertEqual(liquidity, 3000)
    
    def test_available_balance_precedence(self):
        """Test that available_balance takes precedence."""
        account = Account("c1", "Checking", "checking", 5000, available_balance=3000)
        self.assertEqual(account.liquid_amount(), 3000)
    
    def test_safe_to_spend_basic(self):
        """Test basic safe-to-spend calculation."""
        floor = FinancialFloor(3000, 1000)
        
        safe = self.calc.calculate_safe_to_spend(
            liquid_cash=10000,
            upcoming_obligations_30d=2000,
            card_balances=1000,
            savings_target_monthly=500,
            investment_target_monthly=500,
            financial_floor=floor,
        )
        
        # 10000 - 2000 - 1000 - 500 - 500 - 4000 = 2000
        self.assertEqual(safe.total_safe_to_spend, 2000)
    
    def test_safe_to_spend_negative_becomes_zero(self):
        """Test that negative safe to spend becomes 0."""
        floor = FinancialFloor(5000, 2000)
        
        safe = self.calc.calculate_safe_to_spend(
            liquid_cash=2000,
            upcoming_obligations_30d=1000,
            card_balances=500,
            savings_target_monthly=500,
            investment_target_monthly=500,
            financial_floor=floor,
        )
        
        self.assertEqual(safe.total_safe_to_spend, 0)
    
    def test_daily_obligations_calculation(self):
        """Test upcoming obligations calculation."""
        obligations = [
            Obligation("r1", "Rent", "housing", 2000, due_date=1, frequency=Frequency.MONTHLY, priority="essential"),
            Obligation("u1", "Utilities", "utilities", 200, due_date=15, frequency=Frequency.MONTHLY, priority="essential"),
            Obligation("o1", "Optional", "other", 100, due_date=25, frequency=Frequency.MONTHLY, priority="optional", is_active=False),
        ]
        
        # Assuming we're testing from around day 10
        total, obs = self.calc.calculate_daily_obligations_30d(
            obligations,
            "2024-09-10",  # Mid-month
        )
        
        # Should only count active obligations due within 30 days
        self.assertEqual(len(obs), 1)  # Only utilities on day 15
    
    def test_purchase_evaluation_affordable(self):
        """Test purchase evaluation for affordable item."""
        floor = FinancialFloor(3000, 1000)
        
        # Create a dummy forecast
        from calculations import ForecastPoint, Forecast
        points = [ForecastPoint(date="2024-09-10", projected_balance=10000)]
        forecast = Forecast(points=points)
        
        result = self.calc.evaluate_purchase(
            purchase_amount=500,
            current_safe_to_spend=2000,
            current_liquid_balance=8000,
            forecast_30d=forecast,
            financial_floor=floor,
        )
        
        self.assertEqual(result['recommendation'], 'BUY')
        self.assertEqual(result['affordability'], 'high')
    
    def test_purchase_evaluation_exceeds_safe_to_spend(self):
        """Test purchase that exceeds safe-to-spend."""
        floor = FinancialFloor(3000, 1000)
        
        from calculations import ForecastPoint, Forecast
        points = [ForecastPoint(date="2024-09-10", projected_balance=5000)]
        forecast = Forecast(points=points)
        
        result = self.calc.evaluate_purchase(
            purchase_amount=2500,
            current_safe_to_spend=1000,
            current_liquid_balance=5000,
            forecast_30d=forecast,
            financial_floor=floor,
        )
        
        self.assertEqual(result['recommendation'], 'SKIP')
        self.assertEqual(result['affordability'], 'low')
    
    def test_purchase_evaluation_breaks_floor(self):
        """Test purchase that would break financial floor."""
        floor = FinancialFloor(3000, 1000)
        
        from calculations import ForecastPoint, Forecast
        points = [ForecastPoint(date="2024-09-10", projected_balance=4500)]
        forecast = Forecast(points=points)
        
        result = self.calc.evaluate_purchase(
            purchase_amount=1500,
            current_safe_to_spend=1000,
            current_liquid_balance=5000,
            forecast_30d=forecast,
            financial_floor=floor,
        )
        
        # Should recommend WAIT
        self.assertIn(result['recommendation'], ['WAIT', 'BUY_BUT_WAIT'])
    
    def test_spending_30d_calculation(self):
        """Test 30-day spending sum."""
        today = datetime.now()
        transactions = [
            Transaction(
                "t1",
                (today - timedelta(days=5)).isoformat()[:10],
                "Grocery",
                100,
                "expense",
                "groceries",
                "checking"
            ),
            Transaction(
                "t2",
                (today - timedelta(days=1)).isoformat()[:10],
                "Restaurant",
                50,
                "expense",
                "restaurants",
                "checking"
            ),
            Transaction(
                "t3",
                (today - timedelta(days=40)).isoformat()[:10],
                "Old expense",
                200,
                "expense",
                "other",
                "checking"
            ),
        ]
        
        total = self.calc.calculate_spending_30d(transactions, today.isoformat()[:10])
        self.assertEqual(total, 150)  # Only the two recent expenses


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and unusual scenarios."""
    
    def setUp(self):
        self.calc = CalculationEngine()
    
    def test_zero_income(self):
        """Handle zero income scenario."""
        floor = FinancialFloor(1000, 500)
        
        safe = self.calc.calculate_safe_to_spend(
            liquid_cash=2000,
            upcoming_obligations_30d=1000,
            card_balances=0,
            savings_target_monthly=0,
            investment_target_monthly=0,
            financial_floor=floor,
        )
        
        # Should still calculate: 2000 - 1000 - 1500 = -500, clamped to 0
        self.assertEqual(safe.total_safe_to_spend, 0)
    
    def test_large_purchase(self):
        """Handle purchase larger than liquid cash."""
        floor = FinancialFloor(3000, 1000)
        
        from calculations import ForecastPoint, Forecast
        points = [ForecastPoint(date="2024-09-10", projected_balance=3000)]
        forecast = Forecast(points=points)
        
        result = self.calc.evaluate_purchase(
            purchase_amount=10000,
            current_safe_to_spend=1000,
            current_liquid_balance=3000,
            forecast_30d=forecast,
            financial_floor=floor,
        )
        
        self.assertEqual(result['recommendation'], 'SKIP')


class TestDataIntegrity(unittest.TestCase):
    """Test that calculations prevent double-counting."""
    
    def test_credit_card_payment_not_double_counted(self):
        """Verify CC payments aren't counted twice."""
        # This is a critical test
        # If someone has:
        # - CC balance: $1000
        # - CC transaction: $1000 (the thing they bought)
        # 
        # The system should NOT count both
        # Only the balance matters for obligation calculation
        
        calc = CalculationEngine()
        
        # CC has $1000 balance
        # This represents spending already done and recorded
        card_balance = 1000
        
        # When calculating upcoming obligations,
        # we use the balance, not the transaction history
        floor = FinancialFloor(2000, 1000)
        
        safe = calc.calculate_safe_to_spend(
            liquid_cash=5000,
            upcoming_obligations_30d=500,  # Regular bills
            card_balances=card_balance,    # Credit card debt
            savings_target_monthly=0,
            investment_target_monthly=0,
            financial_floor=floor,
        )
        
        # Should be: 5000 - 500 - 1000 - 3000 = 500
        self.assertEqual(safe.total_safe_to_spend, 500)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
