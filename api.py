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

# Initialize CFO
cfo = PersonalCFO(db_path)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current financial status."""
    try:
        status = cfo.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/setup', methods=['POST'])
def setup():
    """Initialize financial data (onboarding)."""
    try:
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
        
        return jsonify({"status": "Setup complete"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/purchase', methods=['POST'])
def evaluate_purchase():
    """Evaluate a purchase decision."""
    try:
        data = request.json
        amount = data.get('amount')
        description = data.get('description', '')
        
        if not amount:
            return jsonify({"error": "Amount required"}), 400
        
        result = cfo.evaluate_purchase(amount, description)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/transaction', methods=['POST'])
def record_transaction():
    """Record a spending transaction."""
    try:
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
