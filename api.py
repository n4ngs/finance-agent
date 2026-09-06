"""
Personal CFO - REST API
Flask API with web dashboard, Plaid integration, and Claude AI reasoning.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request
from cfo import PersonalCFO

app = Flask(__name__, static_folder=None)

# Use Railway's database path if available
db_path = os.getenv('DATABASE_PATH', os.path.expanduser('~/.personal-cfo/finance.db'))

def get_cfo():
    """Create a new CFO instance per request (thread-safe for SQLite)."""
    return PersonalCFO(db_path)

# WEB DASHBOARD (Root)
@app.route('/', methods=['GET'])
def dashboard():
    """Serve the web dashboard."""
    dashboard_path = Path(__file__).parent / 'frontend.html'
    if dashboard_path.exists():
        with open(dashboard_path, 'r') as f:
            return f.read()
    return jsonify({"error": "Dashboard not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current financial status."""
    try:
        cfo = get_cfo()
        status = cfo.get_status()
        cfo.close()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/setup', methods=['POST'])
def setup():
    """Initialize financial data (onboarding)."""
    try:
        cfo = get_cfo()
        data = request.json

        if 'accounts' in data:
            cfo.set_current_position(data['accounts'])

        if 'income' in data:
            cfo.set_income_streams(data['income'])

        if 'obligations' in data:
            cfo.set_obligations(data['obligations'])

        if 'goals' in data:
            cfo.set_goals(data['goals'])

        if 'financial_floor' in data:
            floor = data['financial_floor']
            cfo.set_financial_floor(
                floor.get('emergency_reserve', 3500),
                floor.get('operating_buffer', 1500)
            )

        cfo.close()
        return jsonify({"status": "Setup complete"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/purchase', methods=['POST'])
def evaluate_purchase():
    """Evaluate a purchase decision."""
    try:
        cfo = get_cfo()
        data = request.json
        amount = data.get('amount')
        description = data.get('description', '')

        if not amount:
            return jsonify({"error": "Amount required"}), 400

        result = cfo.evaluate_purchase(amount, description)
        cfo.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transaction', methods=['POST'])
def record_transaction():
    """Record a spending transaction."""
    try:
        cfo = get_cfo()
        data = request.json
        cfo.record_transaction(
            date=data.get('date', datetime.now().isoformat()[:10]),
            description=data.get('description', ''),
            amount=data.get('amount'),
            transaction_type=data.get('transaction_type', 'expense'),
            category=data.get('category', 'other'),
            account=data.get('account', 'checking'),
            merchant=data.get('merchant'),
        )
        cfo.close()
        return jsonify({"status": "Transaction recorded"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# PLAID INTEGRATION
@app.route('/api/plaid/link-token', methods=['POST'])
def plaid_link_token():
    """Generate a Plaid Link token for OAuth flow."""
    try:
        from plaid_integration import PlaidConnector
        
        plaid = PlaidConnector()
        if not plaid.is_configured():
            return jsonify({"error": "Plaid not configured. Set PLAID_CLIENT_ID and PLAID_SECRET.", "link_token": None}), 200
        
        data = request.json
        user_id = data.get('user_id', 'user_1')
        
        result = plaid.create_link_token(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/plaid/exchange', methods=['POST'])
def plaid_exchange():
    """Exchange public_token for access_token."""
    try:
        from plaid_integration import PlaidConnector
        
        plaid = PlaidConnector()
        if not plaid.is_configured():
            return jsonify({"error": "Plaid not configured"}), 400
        
        data = request.json
        public_token = data.get('public_token')
        
        if not public_token:
            return jsonify({"error": "public_token required"}), 400
        
        result = plaid.exchange_public_token(public_token)
        
        if 'error' in result:
            return jsonify(result), 400
        
        cfo = get_cfo()
        cfo.db.save_plaid_item(
            item_id=result['item_id'],
            access_token=result['access_token'],
        )
        cfo.close()
        
        return jsonify({"status": "Bank linked successfully", "item_id": result['item_id']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/plaid/sync', methods=['POST'])
def plaid_sync():
    """Sync accounts and transactions from all Plaid connections."""
    try:
        from plaid_integration import PlaidConnector
        
        plaid = PlaidConnector()
        if not plaid.is_configured():
            return jsonify({"error": "Plaid not configured"}), 400
        
        cfo = get_cfo()
        result = cfo.sync_plaid_accounts_and_transactions(plaid)
        cfo.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# CLAUDE AI INTEGRATION
@app.route('/api/claude/query', methods=['POST'])
def claude_query():
    """Ask Claude a financial question with full financial context."""
    try:
        import anthropic
        
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({"error": "question required"}), 400
        
        cfo = get_cfo()
        status = cfo.get_status()
        cfo.close()
        
        context = f"""
You are a personal financial advisor. The user has shared their complete financial state.

FINANCIAL POSITION:
- Liquid Cash: ${status['liquid_cash']:,.2f}
- Safe to Spend: ${status['safe_to_spend']['total']:,.2f}
- Financial Floor: ${status['financial_floor']['total']:,.2f}
- Upcoming Obligations (30d): ${status['upcoming_obligations_30d']:,.2f}

BREAKDOWN:
{json.dumps(status['safe_to_spend']['breakdown'], indent=2)}

USER QUESTION: {question}

Answer directly and concisely. Refer to their specific numbers.
"""
        
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": context}]
        )
        
        return jsonify({
            "answer": message.content[0].text,
            "financial_context": status,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# PLAID CALLBACK
@app.route('/plaid-callback', methods=['GET'])
def plaid_callback():
    """Handle Plaid OAuth callback."""
    code = request.args.get('code')

    if not code:
        return jsonify({"error": "No authorization code"}), 400

    try:
        from plaid_integration import PlaidConnector
        plaid = PlaidConnector()

        # For sandbox testing - in production you'd exchange code for access token
        cfo = get_cfo()
        cfo.db.save_plaid_item(
            item_id='sandbox_' + code[:8],
            access_token='sandbox_token',
            institution_name='Sandbox Bank'
        )
        cfo.close()

        return '''
        <html>
            <head>
                <title>Bank Linked</title>
                <script>
                    window.opener.location.reload();
                    window.close();
                </script>
            </head>
            <body>
                <h2>✓ Bank linked successfully!</h2>
                <p>Closing this window...</p>
            </body>
        </html>
        '''
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
