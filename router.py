"""
Natural Language Router
Classifies user requests and routes to appropriate handlers.
"""

import re
from typing import Tuple, Dict, Any, Optional
from enum import Enum


class RequestType(Enum):
    """Types of financial requests."""
    STATUS = "status"
    SPEND = "spend"
    BUY = "buy"
    PAYDAY = "payday"
    SPENDING_UPDATE = "spending_update"
    ACCOUNT_UPDATE = "account_update"
    GOAL_UPDATE = "goal_update"
    FORECAST = "forecast"
    SCENARIO = "scenario"
    MONTHLY_REVIEW = "monthly_review"
    DEBT_QUERY = "debt_query"
    GOAL_QUERY = "goal_query"
    SUBSCRIPTION_AUDIT = "subscription_audit"
    GENERAL_QUERY = "general_query"


class ConversationRouter:
    """Routes natural language requests to appropriate handlers."""
    
    # Keywords for each request type
    STATUS_KEYWORDS = [
        "status", "how am i", "where am i", "current position",
        "financial position", "balance", "how much", "what do i have",
    ]
    
    SPEND_KEYWORDS = [
        "can i spend", "can i buy", "afford", "how much can i spend",
        "spending capacity", "discretionary", "available to spend",
    ]
    
    BUY_KEYWORDS = [
        "buy", "purchase", "should i buy", "want to buy", "thinking of",
        "considering buying", "get a", "want to get",
    ]
    
    PAYDAY_KEYWORDS = [
        "payday", "paycheck", "income", "got paid", "received",
        "allocate", "how should i spend",
    ]
    
    SPENDING_UPDATE_KEYWORDS = [
        "spent", "expense", "cost", "paid", "charged", "transaction",
        "update spending", "record",
    ]
    
    ACCOUNT_KEYWORDS = [
        "account", "balance", "updated", "add account", "new account",
        "checking", "savings", "credit card",
    ]
    
    FORECAST_KEYWORDS = [
        "forecast", "projection", "ahead", "coming up", "next month",
        "will i have", "cash flow",
    ]
    
    SCENARIO_KEYWORDS = [
        "what if", "scenario", "combined", "both", "and also",
        "in addition",
    ]
    
    MONTHLY_REVIEW_KEYWORDS = [
        "month", "monthly", "review", "summary", "report",
    ]
    
    DEBT_KEYWORDS = [
        "debt", "loan", "owe", "payment plan", "payoff",
    ]
    
    GOAL_KEYWORDS = [
        "goal", "target", "save for", "want to", "dream",
    ]
    
    SUBSCRIPTION_KEYWORDS = [
        "subscription", "recurring", "membership", "auto-pay",
    ]
    
    def route(self, user_input: str) -> Tuple[RequestType, Dict[str, Any]]:
        """
        Route a user request.
        Returns (request_type, extracted_params).
        """
        user_input_lower = user_input.lower().strip()
        
        # Extract numeric amounts
        amounts = self._extract_amounts(user_input)
        
        # Try exact command matches first
        if user_input_lower.startswith("/"):
            command = user_input_lower.split()[0].lstrip("/")
            if command == "status":
                return RequestType.STATUS, {}
            elif command == "spend":
                return RequestType.SPEND, {}
            elif command == "buy" and amounts:
                return RequestType.BUY, {"amount": amounts[0], "description": user_input}
            elif command == "payday" and amounts:
                return RequestType.PAYDAY, {"amount": amounts[0]}
            elif command == "scenario":
                return RequestType.SCENARIO, {"description": user_input}
            elif command == "month":
                return RequestType.MONTHLY_REVIEW, {}
            elif command == "debt":
                return RequestType.DEBT_QUERY, {}
            elif command == "goals":
                return RequestType.GOAL_QUERY, {}
            elif command == "subscriptions":
                return RequestType.SUBSCRIPTION_AUDIT, {}
        
        # Natural language detection
        request_type = self._detect_request_type(user_input_lower)
        
        # Extract relevant information
        params = {}
        
        if request_type == RequestType.BUY:
            params["amount"] = amounts[0] if amounts else None
            params["description"] = user_input
            params["merchant"] = self._extract_merchant(user_input)
        elif request_type == RequestType.PAYDAY:
            params["amount"] = amounts[0] if amounts else None
        elif request_type == RequestType.SPENDING_UPDATE:
            params["transactions"] = self._parse_spending_list(user_input)
        elif request_type == RequestType.SCENARIO:
            params["description"] = user_input
        
        return request_type, params
    
    def _detect_request_type(self, user_input_lower: str) -> RequestType:
        """Detect the type of request."""
        
        # Check keywords in order of specificity
        if any(kw in user_input_lower for kw in self.BUY_KEYWORDS):
            return RequestType.BUY
        
        if any(kw in user_input_lower for kw in self.SCENARIO_KEYWORDS):
            return RequestType.SCENARIO
        
        if any(kw in user_input_lower for kw in self.PAYDAY_KEYWORDS):
            return RequestType.PAYDAY
        
        if any(kw in user_input_lower for kw in self.SPEND_KEYWORDS):
            return RequestType.SPEND
        
        if any(kw in user_input_lower for kw in self.SPENDING_UPDATE_KEYWORDS):
            return RequestType.SPENDING_UPDATE
        
        if any(kw in user_input_lower for kw in self.ACCOUNT_KEYWORDS):
            return RequestType.ACCOUNT_UPDATE
        
        if any(kw in user_input_lower for kw in self.GOAL_KEYWORDS):
            return RequestType.GOAL_UPDATE
        
        if any(kw in user_input_lower for kw in self.FORECAST_KEYWORDS):
            return RequestType.FORECAST
        
        if any(kw in user_input_lower for kw in self.MONTHLY_REVIEW_KEYWORDS):
            return RequestType.MONTHLY_REVIEW
        
        if any(kw in user_input_lower for kw in self.DEBT_KEYWORDS):
            return RequestType.DEBT_QUERY
        
        if any(kw in user_input_lower for kw in self.SUBSCRIPTION_KEYWORDS):
            return RequestType.SUBSCRIPTION_AUDIT
        
        if any(kw in user_input_lower for kw in self.STATUS_KEYWORDS):
            return RequestType.STATUS
        
        return RequestType.GENERAL_QUERY
    
    def _extract_amounts(self, user_input: str) -> list:
        """Extract dollar amounts from text."""
        # Match patterns like $1,234 or $1234 or 1234
        patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?(?:\s*(?:dollars|bucks|USD|$))',
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, user_input)
            for match in matches:
                # Clean up and convert to float
                cleaned = match.replace('$', '').replace(',', '').lower()
                for suffix in ['dollars', 'bucks', 'usd']:
                    cleaned = cleaned.replace(suffix, '')
                try:
                    amount = float(cleaned.strip())
                    amounts.append(amount)
                except ValueError:
                    pass
        
        return amounts
    
    def _extract_merchant(self, user_input: str) -> Optional[str]:
        """Try to extract merchant/store name."""
        # Look for common patterns like "at Store" or "for Item"
        at_pattern = r'at\s+([A-Z][a-zA-Z\s]+)'
        for_pattern = r'for\s+(?:a\s+)?([A-Z][a-zA-Z\s]+)'
        
        at_match = re.search(at_pattern, user_input)
        if at_match:
            return at_match.group(1).strip()
        
        for_match = re.search(for_pattern, user_input)
        if for_match:
            return for_match.group(1).strip()
        
        return None
    
    def _parse_spending_list(self, user_input: str) -> list:
        """Parse a list of spending transactions."""
        transactions = []
        
        # Match patterns like "category amount"
        # e.g., "restaurants 327" or "groceries 184"
        pattern = r'(\w+)\s*([\d,]+(?:\.\d{2})?)'
        matches = re.findall(pattern, user_input)
        
        for category, amount in matches:
            try:
                amount_float = float(amount.replace(',', ''))
                transactions.append({
                    "category": category.lower(),
                    "amount": amount_float,
                })
            except ValueError:
                pass
        
        return transactions


if __name__ == "__main__":
    router = ConversationRouter()
    
    test_queries = [
        "Can I spend $500 this weekend?",
        "/buy $2749",
        "Buy a $2,749 MacBook Pro",
        "I spent $90 at Costco and $46 on dinner",
        "What if I buy the laptop and also take a $1500 trip?",
        "/status",
        "How am I doing?",
        "restaurants 327\ngroceries 184\namazon 212",
    ]
    
    for query in test_queries:
        request_type, params = router.route(query)
        print(f"\nQuery: {query}")
        print(f"Type: {request_type.value}")
        print(f"Params: {params}")
