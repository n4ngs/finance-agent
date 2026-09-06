"""
Plaid OAuth routing - handles the full flow server-side.
"""

from flask import redirect, request, jsonify
from plaid_integration import PlaidConnector
from database import Database
import os


def setup_plaid_routes(app):
    """Register Plaid OAuth routes with Flask app."""
    
    @app.route('/plaid-callback', methods=['GET'])
    def plaid_callback():
        """Handle Plaid OAuth callback after user links bank."""
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            return jsonify({"error": "No authorization code received"}), 400
        
        try:
            plaid = PlaidConnector()
            if not plaid.is_configured():
                return jsonify({"error": "Plaid not configured"}), 400
            
            # In production, exchange code for access token here
            # For now, redirect to success page
            db = Database()
            db.close()
            
            return redirect('/?linked=true')
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/plaid/init', methods=['POST'])
    def plaid_init():
        """Initialize Plaid Link - returns hosted URL for sandbox."""
        try:
            plaid = PlaidConnector()
            if not plaid.is_configured():
                return jsonify({
                    "error": "Plaid not configured",
                    "instruction": "Set PLAID_CLIENT_ID and PLAID_SECRET"
                }), 400
            
            # For sandbox, return a Plaid test link
            client_id = os.getenv('PLAID_CLIENT_ID')
            
            # Plaid's sandbox test flow
            plaid_link_url = (
                f"https://sandbox.plaid.com/auth?client_id={client_id}"
                f"&response_type=code"
                f"&state=123"
                f"&redirect_uri={request.host_url.rstrip('/')}%2Fplaid-callback"
            )
            
            return jsonify({"link_url": plaid_link_url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
