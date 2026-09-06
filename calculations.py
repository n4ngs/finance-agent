"""
Financial Calculation Engine
All money math lives here. Deterministic, auditable, reproducible.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum


class Frequency(Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    IRREGULAR = "irregular"
    ONE_TIME = "one_time"


@dataclass
class Account:
    account_id: str
    name: str
    account_type: str
    balance: float
    available_balance: Optional[float] = None
    include_in_liquidity: bool = True
    
    def liquid_amount(self) -> float:
        """Amount available for spending calculations."""
        if self.available_balance is not None:
            return self.available_balance
        return self.balance


@dataclass
class IncomeStream:
    income_id: str
    source: str
    amount: float
    frequency: Frequency
    next_expected_date: str  # ISO format YYYY-MM-DD
    is_active: bool = True
    confidence: str = "expected"  # expected, received, irregular


@dataclass
class Obligation:
    obligation_id: str
    name: str
    category: str
    amount: float
    due_date: int  # Day of month (1-31)
    frequency: Frequency
    priority: str  # essential, important, optional
    is_active: bool = True
    autopay: bool = False
    account_paid_from: Optional[str] = None


@dataclass
class Transaction:
    transaction_id: str
    date: str  # ISO format YYYY-MM-DD
    description: str
    amount: float
    transaction_type: str  # expense, income, transfer, refund, investment, debt_payment
    category: str
    account: str
    essentiality: Optional[str] = None
    merchant: Optional[str] = None


@dataclass
class Goal:
    goal_id: str
    name: str
    goal_type: str
    target_amount: float
    current_amount: float
    target_date: Optional[str] = None
    monthly_contribution_target: Optional[float] = None
    priority: str = "important"
    protected: bool = False


@dataclass
class FinancialFloor:
    """The minimum cash that should normally never be crossed."""
    emergency_reserve: float
    operating_buffer: float
    
    @property
    def total(self) -> float:
        return self.emergency_reserve + self.operating_buffer


@dataclass
class SafeToSpend:
    """Breakdown of safe spending capacity."""
    liquid_cash: float
    committed_obligations: float
    card_obligations: float
    savings_commitment: float
    investment_commitment: float
    protected_buffer: float
    planned_purchases: float
    
    @property
    def total_safe_to_spend(self) -> float:
        """Total amount safely available to spend."""
        reserved = (
            self.committed_obligations +
            self.card_obligations +
            self.savings_commitment +
            self.investment_commitment +
            self.protected_buffer +
            self.planned_purchases
        )
        return max(0, self.liquid_cash - reserved)
    
    def breakdown(self) -> Dict[str, float]:
        """Return component breakdown for transparency."""
        return {
            "liquid_cash": self.liquid_cash,
            "reserved_upcoming_bills": -self.committed_obligations,
            "reserved_card_obligations": -self.card_obligations,
            "reserved_savings": -self.savings_commitment,
            "reserved_investments": -self.investment_commitment,
            "reserved_financial_floor": -self.protected_buffer,
            "reserved_planned_purchases": -self.planned_purchases,
            "safe_to_spend": self.total_safe_to_spend,
        }


@dataclass
class ForecastPoint:
    """Single point in a cash-flow forecast."""
    date: str  # ISO format
    projected_balance: float
    income_in: float = 0
    obligations_out: float = 0
    spending_out: float = 0
    savings_out: float = 0
    investments_out: float = 0


@dataclass
class Forecast:
    """Cash flow forecast over a period."""
    points: List[ForecastPoint]
    lowest_balance: Optional[float] = None
    lowest_balance_date: Optional[str] = None
    scenarios: Optional[Dict[str, float]] = None
    assumptions: Optional[Dict[str, any]] = None
    def __post_init__(self):
        if self.points:
            min_point = min(self.points, key=lambda p: p.projected_balance)
            self.lowest_balance = min_point.projected_balance
            self.lowest_balance_date = min_point.date


class CalculationEngine:
    """Core financial calculations."""
    
    def __init__(self):
        pass
    
    def calculate_liquidity(
        self, 
        accounts: List[Account]
    ) -> float:
        """Total liquid cash from all liquid accounts."""
        return sum(
            acc.liquid_amount() 
            for acc in accounts 
            if acc.include_in_liquidity
        )
    
    def calculate_safe_to_spend(
        self,
        liquid_cash: float,
        upcoming_obligations_30d: float,
        card_balances: float,
        savings_target_monthly: float,
        investment_target_monthly: float,
        financial_floor: FinancialFloor,
        planned_purchases: float = 0,
    ) -> SafeToSpend:
        """
        Calculate SAFE TO SPEND.
        
        This is the most important calculation. It shows how much can be
        safely spent without:
        - Violating financial obligations
        - Breaking the financial floor
        - Abandoning savings/investment targets
        """
        return SafeToSpend(
            liquid_cash=liquid_cash,
            committed_obligations=upcoming_obligations_30d,
            card_obligations=card_balances,
            savings_commitment=savings_target_monthly,
            investment_commitment=investment_target_monthly,
            protected_buffer=financial_floor.total,
            planned_purchases=planned_purchases,
        )
    
    def calculate_daily_obligations_30d(
        self,
        obligations: List[Obligation],
        from_date: str,
    ) -> Tuple[float, List[Obligation]]:
        """
        Sum obligations due within 30 days from from_date.
        Returns (total_amount, list_of_obligations).
        """
        from_dt = datetime.fromisoformat(from_date)
        end_dt = from_dt + timedelta(days=30)
        
        due_obligations = []
        total = 0
        
        for ob in obligations:
            if not ob.is_active:
                continue
            
            # Calculate next due date for this obligation
            next_due = self._next_occurrence_this_month(
                ob.due_date,
                ob.frequency,
                from_date
            )
            
            if next_due and datetime.fromisoformat(next_due) <= end_dt:
                due_obligations.append(ob)
                total += ob.amount
        
        return total, due_obligations
    
    def calculate_spending_30d(
        self,
        transactions: List[Transaction],
        from_date: str,
        category_filter: Optional[str] = None,
    ) -> float:
        """Sum all spending transactions in the past 30 days."""
        from_dt = datetime.fromisoformat(from_date)
        start_dt = from_dt - timedelta(days=30)
        
        total = 0
        for txn in transactions:
            if txn.transaction_type != "expense":
                continue
            if category_filter and txn.category != category_filter:
                continue
            
            txn_dt = datetime.fromisoformat(txn.date)
            if start_dt <= txn_dt <= from_dt:
                total += txn.amount
        
        return total
    
    def forecast_cash_flow(
        self,
        starting_balance: float,
        income_streams: List[IncomeStream],
        obligations: List[Obligation],
        expected_spending_daily: float,
        from_date: str,
        days_ahead: int,
        savings_daily: float = 0,
        investments_daily: float = 0,
    ) -> Forecast:
        """
        Forecast cash position over days_ahead.
        
        Most important use: find the lowest projected balance in the
        forecast window.
        """
        points = []
        current_date = datetime.fromisoformat(from_date)
        current_balance = starting_balance
        
        for day in range(days_ahead + 1):
            date_str = current_date.isoformat()
            
            # Income for this day
            daily_income = self._income_for_date(
                income_streams, 
                current_date
            )
            current_balance += daily_income
            
            # Obligations for this day
            daily_obligations = self._obligations_for_date(
                obligations,
                current_date.day,
            )
            current_balance -= daily_obligations
            
            # Regular spending
            current_balance -= expected_spending_daily
            current_balance -= savings_daily
            current_balance -= investments_daily
            
            point = ForecastPoint(
                date=date_str,
                projected_balance=current_balance,
                income_in=daily_income,
                obligations_out=daily_obligations,
                spending_out=expected_spending_daily,
                savings_out=savings_daily,
                investments_out=investments_daily,
            )
            points.append(point)
            
            current_date += timedelta(days=1)
        
        return Forecast(points=points)
    
    def evaluate_purchase(
        self,
        purchase_amount: float,
        current_safe_to_spend: float,
        current_liquid_balance: float,
        forecast_30d: Forecast,
        financial_floor: FinancialFloor,
    ) -> Dict:
        """
        Evaluate whether a purchase is affordable/wise.
        
        Returns:
        - affordability: high/moderate/low
        - timing: optimal/acceptable/poor
        - impact: minimal/moderate/significant
        - recommendation: buy/buy_but_wait/buy_if/wait/skip
        """
        
        # Basic affordability
        after_purchase_safe_to_spend = current_safe_to_spend - purchase_amount
        after_purchase_balance = current_liquid_balance - purchase_amount
        
        # Impact on forecast
        min_balance = forecast_30d.lowest_balance
        min_after_purchase = min_balance - purchase_amount
        headroom_before = min_balance - financial_floor.total
        headroom_after = min_after_purchase - financial_floor.total
        
        # Determine recommendation
        if purchase_amount > current_safe_to_spend:
            recommendation = "SKIP"
            affordability = "low"
        elif min_after_purchase < financial_floor.total:
            recommendation = "WAIT"
            affordability = "low"
        elif after_purchase_balance < 0:
            recommendation = "SKIP"
            affordability = "low"
        elif headroom_after < (financial_floor.total * 0.25):
            recommendation = "BUY_BUT_WAIT"
            affordability = "moderate"
        else:
            recommendation = "BUY"
            affordability = "high"
        
        return {
            "purchase_amount": purchase_amount,
            "current_safe_to_spend": current_safe_to_spend,
            "after_purchase_safe_to_spend": max(0, after_purchase_safe_to_spend),
            "current_liquid_balance": current_liquid_balance,
            "after_purchase_balance": after_purchase_balance,
            "current_30d_minimum": min_balance,
            "after_purchase_30d_minimum": min_after_purchase,
            "financial_floor": financial_floor.total,
            "headroom_before_purchase": max(0, headroom_before),
            "headroom_after_purchase": max(0, headroom_after),
            "affordability": affordability,
            "recommendation": recommendation,
        }
    
    def _next_occurrence_this_month(
        self,
        day_of_month: int,
        frequency: Frequency,
        from_date: str,
    ) -> Optional[str]:
        """
        Calculate next occurrence of a monthly obligation.
        """
        from_dt = datetime.fromisoformat(from_date)
        
        # For simplicity, assume monthly for now
        if frequency == Frequency.MONTHLY:
            if day_of_month >= from_dt.day:
                # This month
                try:
                    next_date = from_dt.replace(day=day_of_month)
                    return next_date.isoformat()
                except ValueError:
                    # Day doesn't exist (e.g., Feb 31)
                    return None
            else:
                # Next month
                if from_dt.month == 12:
                    next_date = from_dt.replace(year=from_dt.year + 1, month=1, day=day_of_month)
                else:
                    next_date = from_dt.replace(month=from_dt.month + 1, day=day_of_month)
                return next_date.isoformat()
        
        return None
    
    def _income_for_date(
        self,
        income_streams: List[IncomeStream],
        date: datetime,
    ) -> float:
        """Calculate expected income for a specific date."""
        total = 0
        for stream in income_streams:
            if not stream.is_active:
                continue
            
            expected_dt = datetime.fromisoformat(stream.next_expected_date)
            if expected_dt.date() == date.date():
                total += stream.amount
        
        return total
    
    def _obligations_for_date(
        self,
        obligations: List[Obligation],
        day_of_month: int,
    ) -> float:
        """Calculate obligations due on a specific day of month."""
        total = 0
        for ob in obligations:
            if not ob.is_active:
                continue
            
            if ob.due_date == day_of_month and ob.frequency == Frequency.MONTHLY:
                total += ob.amount
        
        return total


class AnomalyDetector:
    """Detect unusual spending patterns."""
    
    @staticmethod
    def detect_spending_anomalies(
        transactions: List[Transaction],
        baseline_daily: float,
        baseline_period_days: int = 30,
    ) -> List[Dict]:
        """
        Detect unusual spending patterns.
        Returns list of anomalies with explanations.
        """
        anomalies = []
        
        # Calculate recent spending velocity
        if not transactions:
            return anomalies
        
        recent_cutoff = (
            datetime.fromisoformat(transactions[-1].date) - timedelta(days=baseline_period_days)
        )
        recent = [t for t in transactions if datetime.fromisoformat(t.date) > recent_cutoff]
        
        if not recent:
            return anomalies
        
        recent_daily = sum(t.amount for t in recent) / baseline_period_days
        
        if recent_daily > baseline_daily * 1.3:
            anomalies.append({
                "type": "elevated_spending_velocity",
                "baseline_daily": baseline_daily,
                "recent_daily": recent_daily,
                "increase_percent": ((recent_daily - baseline_daily) / baseline_daily) * 100,
                "severity": "moderate" if recent_daily < baseline_daily * 1.5 else "high",
            })
        
        return anomalies
