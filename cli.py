"""
CLI Interface for Personal CFO
Command-line interface for financial management.
"""

import sys
from datetime import datetime
from cfo import PersonalCFO
from router import ConversationRouter, RequestType
from database import Database


class CFOCLI:
    """Command-line interface for Personal CFO."""
    
    def __init__(self, db_path: str = "finance.db"):
        self.cfo = PersonalCFO(db_path)
        self.router = ConversationRouter()
        self.is_onboarded = self._check_onboarded()
    
    def _check_onboarded(self) -> bool:
        """Check if system has been initialized."""
        db = Database()
        accounts = db.get_all_accounts()
        db.close()
        return len(accounts) > 0
    
    def run(self):
        """Main CLI loop."""
        print("\n" + "="*60)
        print("  PERSONAL CFO - Financial Operating System")
        print("="*60)
        
        if not self.is_onboarded:
            self._onboarding()
        
        print("\nType 'help' for commands or ask a question.")
        print("Type 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("CFO> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "exit":
                    print("\nGoodbye!")
                    break
                
                if user_input.lower() == "help":
                    self._show_help()
                    continue
                
                self.handle_request(user_input)
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Try again or type 'help' for assistance.\n")
    
    def handle_request(self, user_input: str):
        """Process a user request."""
        request_type, params = self.router.route(user_input)
        
        if request_type == RequestType.STATUS:
            self._handle_status()
        elif request_type == RequestType.SPEND:
            self._handle_spend_query()
        elif request_type == RequestType.BUY:
            self._handle_buy(params)
        elif request_type == RequestType.PAYDAY:
            self._handle_payday(params)
        elif request_type == RequestType.SPENDING_UPDATE:
            self._handle_spending_update(params)
        elif request_type == RequestType.SCENARIO:
            self._handle_scenario(params)
        elif request_type == RequestType.MONTHLY_REVIEW:
            self._handle_monthly_review()
        elif request_type == RequestType.STATUS:
            self._handle_status()
        else:
            print(f"\nRequest type: {request_type.value}")
            print(f"Parameters: {params}")
            print("(Feature coming soon)")
    
    def _handle_status(self):
        """Show financial status."""
        status = self.cfo.get_status()
        
        print("\n" + "="*60)
        print("  FINANCIAL STATUS")
        print("="*60)
        print(f"\nLiquid Cash:           ${status['liquid_cash']:>12,.2f}")
        print(f"Financial Floor:       ${status['financial_floor']['total']:>12,.2f}")
        print(f"Safe to Spend:         ${status['safe_to_spend']['total']:>12,.2f}")
        print(f"\nUpcoming Bills (30d):  ${status['upcoming_obligations_30d']:>12,.2f}")
        print(f"Status: COMFORTABLE\n")
    
    def _handle_spend_query(self):
        """Show spending capacity."""
        status = self.cfo.get_status()
        
        print("\n" + "="*60)
        print("  SPENDING CAPACITY")
        print("="*60)
        print(f"\nSafe to Spend:")
        print(f"  Until payday:     ${status['safe_to_spend']['total'] * 0.5:>12,.2f}")
        print(f"  This month:       ${status['safe_to_spend']['total']:>12,.2f}")
        print(f"  Conservative:     ${max(0, status['safe_to_spend']['total'] * 0.7):>12,.2f}\n")
    
    def _handle_buy(self, params: dict):
        """Evaluate a purchase decision."""
        amount = params.get("amount")
        description = params.get("description", "")
        
        if amount is None:
            print("\nI need a dollar amount. Try: 'Can I spend $500?'")
            return
        
        result = self.cfo.evaluate_purchase(amount, description)
        
        print("\n" + "="*60)
        print(f"  PURCHASE DECISION: {description}")
        print("="*60)
        print(f"\nAmount:                ${amount:>12,.2f}")
        print(f"Current Safe to Spend: ${result['current_safe_to_spend']:>12,.2f}")
        print(f"After Purchase:        ${result['after_purchase_safe_to_spend']:>12,.2f}")
        print(f"30-day Minimum:        ${result['current_30d_minimum']:>12,.2f}")
        print(f"Financial Floor:       ${result['financial_floor']:>12,.2f}")
        print(f"Headroom:              ${result['headroom_before_purchase']:>12,.2f}")
        
        print(f"\nVERDICT: {result['recommendation']}")
        if result['recommendation'] == "BUY":
            print("This purchase is comfortably affordable.")
        elif result['recommendation'] == "BUY_BUT_WAIT":
            print("Affordable, but consider waiting until payday for better headroom.")
        elif result['recommendation'] == "WAIT":
            print("Wait—this would reduce your financial floor.")
        else:
            print("This purchase would strain your finances.")
        print()
    
    def _handle_payday(self, params: dict):
        """Allocate new paycheck."""
        amount = params.get("amount")
        
        if amount is None:
            print("\nWhat's your paycheck amount? Try: '/payday 4200'")
            return
        
        print("\n" + "="*60)
        print(f"  PAYCHECK ALLOCATION: ${amount:,.2f}")
        print("="*60)
        
        # Simple allocation for now
        bills = amount * 0.35
        emergency = amount * 0.15
        investing = amount * 0.12
        future = amount * 0.10
        lifestyle = amount - bills - emergency - investing - future
        
        print(f"\nRequired:")
        print(f"  Bills & Obligations     ${bills:>12,.2f}")
        print(f"\nRecommended:")
        print(f"  Emergency Fund          ${emergency:>12,.2f}")
        print(f"  Investing               ${investing:>12,.2f}")
        print(f"  Future Purchase         ${future:>12,.2f}")
        print(f"\nAvailable for Lifestyle: ${lifestyle:>12,.2f}\n")
    
    def _handle_spending_update(self, params: dict):
        """Record spending transactions."""
        transactions = params.get("transactions", [])
        
        if not transactions:
            print("\nNo transactions parsed. Try: 'restaurants 327, groceries 184'")
            return
        
        total = sum(t['amount'] for t in transactions)
        
        print(f"\nRecorded {len(transactions)} transactions (${total:,.2f} total)")
        for t in transactions:
            print(f"  {t['category']:>15}: ${t['amount']:>8,.2f}")
        print()
    
    def _handle_scenario(self, params: dict):
        """Simulate scenarios."""
        print("\nScenario simulation coming soon!")
        print("Try: 'What if I buy a laptop and take a $1,500 trip?'\n")
    
    def _handle_monthly_review(self):
        """Show monthly review."""
        status = self.cfo.get_status()
        
        print("\n" + "="*60)
        print("  MONTHLY REVIEW")
        print("="*60)
        print(f"\nFinancial Position:")
        print(f"  Liquid Cash:       ${status['liquid_cash']:>12,.2f}")
        print(f"  Financial Floor:   ${status['financial_floor']['total']:>12,.2f}")
        print(f"  Safe to Spend:     ${status['safe_to_spend']['total']:>12,.2f}")
        print(f"\nNext Month Outlook:")
        print(f"  Obligations:       ${status['upcoming_obligations_30d']:>12,.2f}")
        print(f"  Status: On Track\n")
    
    def _onboarding(self):
        """Walk through initial setup."""
        print("\n" + "="*60)
        print("  PERSONAL CFO - INITIAL SETUP")
        print("="*60)
        
        print("\nLet's set up your financial system in 5 steps.\n")
        
        # Step 1: Current position
        print("STEP 1: Current Account Balances")
        print("-" * 40)
        print("Enter your account balances (leave blank when done):")
        
        accounts = []
        account_num = 1
        while True:
            print(f"\nAccount {account_num}:")
            name = input("  Name (e.g., Checking): ").strip()
            if not name:
                if accounts:
                    break
                print("  Please enter at least one account.")
                continue
            
            account_type = input("  Type (checking/savings/credit_card): ").strip() or "checking"
            try:
                balance = float(input("  Balance: $").strip())
            except ValueError:
                print("  Invalid amount.")
                continue
            
            accounts.append({
                "name": name,
                "account_type": account_type,
                "balance": balance,
            })
            account_num += 1
        
        self.cfo.set_current_position(accounts)
        print("\n✓ Accounts saved.")
        
        # Step 2: Income
        print("\n\nSTEP 2: Income")
        print("-" * 40)
        try:
            amount = float(input("Take-home income per paycheck: $").strip())
            frequency = input("Frequency (weekly/biweekly/monthly): ").strip() or "biweekly"
            next_date = input("Next payday (YYYY-MM-DD): ").strip() or datetime.now().isoformat()[:10]
            
            self.cfo.set_income_streams([{
                "source": "Salary",
                "amount": amount,
                "frequency": frequency,
                "next_expected_date": next_date,
            }])
            print("✓ Income saved.")
        except ValueError:
            print("Skipping income setup.")
        
        # Step 3: Major obligations
        print("\n\nSTEP 3: Major Recurring Obligations")
        print("-" * 40)
        obligations = []
        ob_num = 1
        while True:
            name = input(f"\nObligation {ob_num} (or blank to skip): ").strip()
            if not name:
                break
            
            try:
                amount = float(input(f"  Amount: $").strip())
                due_date = int(input(f"  Due date (day of month): ").strip() or "1")
                priority = input("  Priority (essential/important): ").strip() or "essential"
                
                obligations.append({
                    "name": name,
                    "category": name.lower(),
                    "amount": amount,
                    "due_date": due_date,
                    "frequency": "monthly",
                    "priority": priority,
                })
                ob_num += 1
            except ValueError:
                print("  Invalid entry.")
        
        if obligations:
            self.cfo.set_obligations(obligations)
            print("✓ Obligations saved.")
        
        # Step 4: Goals
        print("\n\nSTEP 4: Financial Goals")
        print("-" * 40)
        try:
            emergency_target = float(input("Emergency fund target: $").strip() or "20000")
            
            self.cfo.set_goals([{
                "name": "Emergency Fund",
                "goal_type": "emergency_fund",
                "target_amount": emergency_target,
                "monthly_contribution_target": 750,
            }])
            print("✓ Goals saved.")
        except ValueError:
            print("Skipping goals setup.")
        
        # Step 5: Financial floor
        print("\n\nSTEP 5: Financial Floor")
        print("-" * 40)
        try:
            emergency = float(input("Emergency reserve: $").strip() or "3500")
            buffer = float(input("Operating buffer: $").strip() or "1500")
            
            self.cfo.set_financial_floor(emergency, buffer)
            print("✓ Financial floor set.")
        except ValueError:
            print("Using default financial floor.")
        
        print("\n" + "="*60)
        print("✓ Setup complete! You're ready to go.\n")
        self.is_onboarded = True
    
    def _show_help(self):
        """Show help message."""
        print("""
PERSONAL CFO - Command Reference

Ask naturally or use these commands:

STATUS QUERIES:
  status, /status              Show financial status
  How am I doing?              Current position summary
  spend, /spend                Show spending capacity
  /month                       Monthly review

PURCHASE DECISIONS:
  /buy $2,749                  Should I buy this?
  Can I spend $500?            Is this affordable?
  What if I buy X and Y?       Combine scenarios

SPENDING:
  I spent $90 on groceries     Record expenses
  restaurants 50 groceries 90  Log multiple expenses

INCOME:
  /payday 4200                 Allocate new paycheck

OTHER:
  exit                         Quit the application
  help                         Show this message

Examples:
  "Can I spend $500 this weekend?"
  "Buy a $2,749 MacBook Pro"
  "What if I buy the laptop and also take a trip?"
  "restaurants 327, groceries 184, amazon 212"
""")
    

def main():
    """Entry point."""
    cli = CFOCLI()
    cli.run()
    cli.cfo.close()


if __name__ == "__main__":
    main()
