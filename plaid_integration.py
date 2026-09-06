"""
Plaid Integration
Handles bank account linking and automatic transaction/balance sync.

Flow:
1. Frontend calls /api/plaid/link-token to get a link_token
2. Frontend opens Plaid Link with that token
3. User selects bank, logs in via Plaid's secure UI (we never see credentials)
4. Plaid returns a public_token to the frontend
5. Frontend sends public_token to /api/plaid/exchange
6. Backend exchanges it for a permanent access_token, stores it
7. Backend can now fetch accounts/transactions/balances anytime
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

try:
    import plaid
    from plaid.api import plaid_api
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
    from plaid.model.accounts_get_request import AccountsGetRequest
    from plaid.model.transactions_sync_request import TransactionsSyncRequest
    PLAID_AVAILABLE = True
except ImportError:
    PLAID_AVAILABLE = False


class PlaidConnector:
    """Connect to Plaid for automatic bank data sync."""

    def __init__(self, client_id: Optional[str] = None, secret: Optional[str] = None, env: str = "sandbox"):
        self.client_id = client_id or os.getenv("PLAID_CLIENT_ID")
        self.secret = secret or os.getenv("PLAID_SECRET")
        self.env = env or os.getenv("PLAID_ENV", "sandbox")

        if not PLAID_AVAILABLE:
            self.client = None
            return

        if not self.client_id or not self.secret:
            self.client = None
            return

        host_map = {
            "sandbox": plaid.Environment.Sandbox,
            "development": plaid.Environment.Development,
            "production": plaid.Environment.Production,
        }

        configuration = plaid.Configuration(
            host=host_map.get(self.env, plaid.Environment.Sandbox),
            api_key={
                "clientId": self.client_id,
                "secret": self.secret,
            },
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def is_configured(self) -> bool:
        """Check if Plaid credentials are set up."""
        return self.client is not None

    def create_link_token(self, user_id: str) -> Dict[str, Any]:
        """
        Generate a Plaid Link token for the frontend to open the Link UI.
        This is step 1 of the OAuth-like flow.
        """
        if not self.is_configured():
            return {"error": "Plaid not configured. Set PLAID_CLIENT_ID and PLAID_SECRET."}

        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Personal CFO",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
        )
        response = self.client.link_token_create(request)
        return {"link_token": response["link_token"]}

    def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """
        Exchange the temporary public_token (from Plaid Link) for a
        permanent access_token used for all future API calls.
        """
        if not self.is_configured():
            return {"error": "Plaid not configured."}

        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        return {
            "access_token": response["access_token"],
            "item_id": response["item_id"],
        }

    def fetch_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Fetch all accounts linked under this access_token."""
        if not self.is_configured():
            return []

        request = AccountsGetRequest(access_token=access_token)
        response = self.client.accounts_get(request)

        accounts = []
        for acct in response["accounts"]:
            accounts.append({
                "plaid_account_id": acct["account_id"],
                "name": acct["name"],
                "official_name": acct.get("official_name"),
                "account_type": self._map_account_type(acct["type"], acct["subtype"]),
                "balance": acct["balances"]["current"],
                "available_balance": acct["balances"]["available"],
                "currency": acct["balances"]["iso_currency_code"],
            })
        return accounts

    def fetch_transactions(self, access_token: str, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch new/updated/removed transactions since the last cursor.
        Uses Plaid's incremental sync endpoint (recommended over /transactions/get).
        """
        if not self.is_configured():
            return {"added": [], "modified": [], "removed": [], "next_cursor": cursor}

        # The Plaid SDK requires cursor to be omitted (not None) on the
        # first sync. Passing cursor=None raises a validation error.
        if cursor:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor,
            )
        else:
            request = TransactionsSyncRequest(
                access_token=access_token,
            )
        response = self.client.transactions_sync(request)

        added = [self._map_transaction(t) for t in response["added"]]
        modified = [self._map_transaction(t) for t in response["modified"]]
        removed = [t["transaction_id"] for t in response["removed"]]

        return {
            "added": added,
            "modified": modified,
            "removed": removed,
            "next_cursor": response["next_cursor"],
            "has_more": response["has_more"],
        }

    def sync_all_transactions(self, access_token: str, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Page through all available transactions until has_more is False."""
        all_added = []
        all_modified = []
        all_removed = []

        while True:
            result = self.fetch_transactions(access_token, cursor)
            all_added.extend(result["added"])
            all_modified.extend(result["modified"])
            all_removed.extend(result["removed"])
            cursor = result["next_cursor"]

            if not result.get("has_more"):
                break

        return {
            "added": all_added,
            "modified": all_modified,
            "removed": all_removed,
            "next_cursor": cursor,
        }

    def _map_account_type(self, plaid_type: str, plaid_subtype: str) -> str:
        """Map Plaid's account type/subtype to our internal account_type."""
        mapping = {
            "depository": {
                "checking": "checking",
                "savings": "savings",
            },
            "credit": {
                "credit card": "credit_card",
            },
            "loan": {
                "default": "loan",
            },
            "investment": {
                "default": "investment",
            },
        }
        type_str = str(plaid_type)
        subtype_str = str(plaid_subtype)
        return mapping.get(type_str, {}).get(subtype_str, mapping.get(type_str, {}).get("default", "other"))

    def _map_transaction(self, plaid_txn) -> Dict[str, Any]:
        """Map a Plaid transaction to our internal transaction format."""
        # Plaid uses positive amount = money out, negative = money in
        amount = plaid_txn["amount"]
        txn_type = "expense" if amount > 0 else "income"

        category = "other"
        if plaid_txn.get("personal_finance_category"):
            category = plaid_txn["personal_finance_category"]["primary"].lower()
        elif plaid_txn.get("category"):
            category = plaid_txn["category"][0].lower() if plaid_txn["category"] else "other"

        return {
            "plaid_transaction_id": plaid_txn["transaction_id"],
            "date": str(plaid_txn["date"]),
            "description": plaid_txn["name"],
            "merchant": plaid_txn.get("merchant_name"),
            "amount": abs(amount),
            "transaction_type": txn_type,
            "category": category,
            "plaid_account_id": plaid_txn["account_id"],
            "pending": plaid_txn.get("pending", False),
        }
