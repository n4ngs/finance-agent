"""
Scenario Simulator
Simulate different financial decisions and their consequences.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from calculations import CalculationEngine, Forecast, FinancialFloor


@dataclass
class ScenarioAction:
    """A single action in a scenario."""
    date: str  # ISO YYYY-MM-DD
    action_type: str  # "purchase", "income_increase", "expense_increase"
    amount: float
    description: str


@dataclass
class ScenarioResult:
    """Results from simulating a scenario."""
    scenario_name: str
    actions: List[ScenarioAction]
    forecast_7d: Forecast
    forecast_30d: Forecast
    forecast_90d: Forecast
    ending_balance_30d: float
    lowest_balance_30d: float
    lowest_balance_date_30d: str
    financial_floor: FinancialFloor
    headroom_30d: float
    feasible: bool


class ScenarioSimulator:
    """Simulate different financial scenarios."""
    
    def __init__(self, calc: CalculationEngine):
        self.calc = calc
    
    def compare_scenarios(
        self,
        base_forecast_30d: Forecast,
        base_forecast_90d: Forecast,
        scenarios: List[Dict[str, Any]],
        financial_floor: FinancialFloor,
    ) -> List[ScenarioResult]:
        """
        Compare multiple scenarios.
        
        Each scenario is a dict with:
        - name: str
        - actions: list of {"date", "type", "amount", "description"}
        """
        results = []
        
        for scenario_data in scenarios:
            result = self._simulate_scenario(
                scenario_data['name'],
                scenario_data['actions'],
                base_forecast_30d,
                base_forecast_90d,
                financial_floor,
            )
            results.append(result)
        
        return results
    
    def _simulate_scenario(
        self,
        scenario_name: str,
        actions: List[Dict[str, Any]],
        base_forecast_30d: Forecast,
        base_forecast_90d: Forecast,
        financial_floor: FinancialFloor,
    ) -> ScenarioResult:
        """Simulate a single scenario by modifying forecasts with actions."""
        
        # For now, simple impact calculation
        # In production, would rebuild full forecasts
        total_impact = sum(
            -action['amount'] if action['type'] == 'purchase' else action['amount']
            for action in actions
        )
        
        adjusted_lowest_30d = base_forecast_30d.lowest_balance + total_impact
        adjusted_ending_30d = base_forecast_30d.points[-1].projected_balance + total_impact if base_forecast_30d.points else 0
        
        feasible = adjusted_lowest_30d >= financial_floor.total
        
        headroom = max(0, adjusted_lowest_30d - financial_floor.total)
        
        scenario_actions = [
            ScenarioAction(
                date=action['date'],
                action_type=action['type'],
                amount=action['amount'],
                description=action['description'],
            )
            for action in actions
        ]
        
        return ScenarioResult(
            scenario_name=scenario_name,
            actions=scenario_actions,
            forecast_7d=base_forecast_30d,  # Simplified
            forecast_30d=base_forecast_30d,
            forecast_90d=base_forecast_90d,
            ending_balance_30d=adjusted_ending_30d,
            lowest_balance_30d=adjusted_lowest_30d,
            lowest_balance_date_30d=base_forecast_30d.lowest_balance_date or "unknown",
            financial_floor=financial_floor,
            headroom_30d=headroom,
            feasible=feasible,
        )
    
    def rank_scenarios(
        self,
        results: List[ScenarioResult],
    ) -> List[ScenarioResult]:
        """Rank scenarios by feasibility and headroom."""
        feasible = [r for r in results if r.feasible]
        infeasible = [r for r in results if not r.feasible]
        
        # Sort feasible by headroom (descending)
        feasible.sort(key=lambda r: r.headroom_30d, reverse=True)
        
        # Sort infeasible by how close to feasible
        infeasible.sort(key=lambda r: r.lowest_balance_30d, reverse=True)
        
        return feasible + infeasible
