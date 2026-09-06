"""
Personal CFO - REST API
Simple Flask API for Railway deployment.
"""

import json
import os
from datetime import datetime
from flask import Flask, jsonify, request
from cfo import PersonalCFO

app = Flask(__name__)

# Use Railway's database path if available
db_path = os.getenv('DATABASE_PATH', os.path.expanduser('~/.personal-cfo/finance.db'))

def get_cfo():
    """Create a new CFO instance per request (thread-safe for SQLite)."""
    return PersonalCFO(db_path)

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

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API documentation."""
    return jsonify({
        "service": "Personal CFO API",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "GET /api/status": "Get current financial status",
            "POST /api/setup": "Initialize financial data",
            "POST /api/purchase": "Evaluate purchase decision",
            "POST /api/transaction": "Record a transaction",
        },
        "example_setup": {
            "accounts": [
                {"name": "Checking", "account_type": "checking", "balance": 5000}
            ],
            "income": [
                {"source": "Salary", "amount": 4200, "frequency": "biweekly", "next_expected_date": "2026-09-18"}
            ],
            "obligations": [
                {"name": "Rent", "category": "housing", "amount": 2000, "due_date": 1, "frequency": "monthly", "priority": "essential"}
            ],
            "goals": [
                {"name": "Emergency Fund", "goal_type": "emergency_fund", "target_amount": 20000, "current_amount": 10000}
            ],
            "financial_floor": {
                "emergency_reserve": 3500,
                "operating_buffer": 1500
            }
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# PLAID INTEGRATION ENDPOINTS
@app.route('/api/plaid/link-token', methods=['POST'])
def plaid_link_token():
    """Generate a Plaid Link token for the frontend."""
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
    """Exchange Plaid's public_token for access_token and store it."""
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
        
        # Store in database
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
    """Sync accounts and transactions from Plaid."""
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

# CLAUDE AI INTEGRATION ENDPOINTS
@app.route('/api/claude/query', methods=['POST'])
def claude_query():
    """
    Ask Claude a financial question.
    Claude sees your current financial state and reasons about it.
    """
    try:
        import anthropic
        
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({"error": "question required"}), 400
        
        # Get current financial state
        cfo = get_cfo()
        status = cfo.get_status()
        cfo.close()
        
        # Prepare context for Claude
        context = f"""
You are a personal financial advisor. The user has shared their financial state with you.

CURRENT FINANCIAL POSITION:
- Liquid Cash: ${status['liquid_cash']:,.2f}
- Financial Floor: ${status['financial_floor']['total']:,.2f}
- Safe to Spend: ${status['safe_to_spend']['total']:,.2f}
- Upcoming Obligations (30 days): ${status['upcoming_obligations_30d']:,.2f}
- Number of Active Goals: {status['active_income_streams']}
- Number of Active Income Streams: {status['active_income_streams']}

BREAKDOWN OF SAFE TO SPEND:
{json.dumps(status['safe_to_spend']['breakdown'], indent=2)}

USER QUESTION: {question}

Answer the user's question directly and helpfully. Refer to their specific numbers.
Be concise but thorough. If they're asking about affordability, be clear about whether something is safe.
"""
        
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": context}
            ]
        )
        
        return jsonify({
            "answer": message.content[0].text,
            "financial_context": status,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

