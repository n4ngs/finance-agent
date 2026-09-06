# Personal CFO - Phase 2 Setup Guide

## What You Have

✅ **Deployed on Railway:**
- Web dashboard at: https://finance-agent-production-694c.up.railway.app
- Flask API backend (auto-synced to your GitHub)
- SQLite database (persistent volume on Railway)

✅ **Core Features:**
- Financial calculations & forecasting
- Plaid bank integration (not activated yet)
- Claude AI reasoning (not activated yet)
- Web dashboard with charts & chat

## To Get It Fully Working

You need 2 API keys. Both are free to start.

### 1. Plaid API Key

**What it does:** Lets you link your bank account securely. Plaid handles the OAuth, you never type your password into our app.

**Get it:**
1. Go to https://dashboard.plaid.com/signup
2. Sign up (free tier available)
3. Go to Settings → Keys
4. Copy your `client_id` and `secret`

**Add to Railway:**
1. Go to your Railway project dashboard
2. Click "Variables"
3. Add:
   - `PLAID_CLIENT_ID` = (paste your client_id)
   - `PLAID_SECRET` = (paste your secret)
   - `PLAID_ENV` = `sandbox` (for testing) or `production`
4. Save and wait for redeploy (~1 min)

### 2. Anthropic API Key

**What it does:** Powers the Claude chat. Lets you ask questions like "Can I afford a $2,000 purchase?"

**Get it:**
1. Go to https://console.anthropic.com
2. Sign up (free credits or paid)
3. Go to Settings → API Keys
4. Click "Create Key"
5. Copy it

**Add to Railway:**
1. In Railway Variables, add:
   - `ANTHROPIC_API_KEY` = (paste your key)
2. Save and wait for redeploy

### After Setup

Once both keys are set:

1. Open: https://finance-agent-production-694c.up.railway.app
2. **Set up your finances:**
   - Manually enter your current balances
   - Set your income (paycheck amount & frequency)
   - List your obligations (rent, bills, etc.)
   - Set your financial floor (safety net)
3. **Connect your bank:**
   - Click "Connect Bank" button
   - Plaid Link will open
   - Choose your bank
   - Log in via your bank (Plaid handles it securely)
   - Approve access
4. **Ask Claude questions:**
   - "How much can I spend this weekend?"
   - "Can I afford a $2,500 laptop?"
   - "What if I take a $1,500 trip AND buy the laptop?"

## How It Works

```
You open dashboard
    ↓
Your browser talks to Railway API
    ↓
API reads your database (SQLite on Railway)
    ↓
If you ask Claude → API sends your financial state to Claude
    ↓
Claude reasons about it and returns natural language answer
    ↓
If you connect bank → API talks to Plaid OAuth
    ↓
Plaid returns your accounts/transactions securely
    ↓
API stores in database
    ↓
Dashboard shows live financial state
```

## Important Notes

**Plaid:** Uses sandbox mode by default. Once tested, switch to `production` in Railway variables.

**Security:** 
- We never store your bank password (Plaid handles that)
- We never ask for full credit card numbers
- We never ask for SSN
- All data lives on Railway's secure servers

**Database:** Persists on Railway volume. Your data survives restarts.

**Cost:**
- Railway: Free tier covers this
- Plaid: Free tier (up to 100 transactions/month)
- Anthropic: ~$0.03 per question at current pricing

## Troubleshooting

**Dashboard shows "Loading..."**
- Wait 30 seconds for Railway to redeploy
- Refresh the page
- Check Railway logs: `railway logs --service finance-agent`

**"Plaid not configured"**
- You haven't set PLAID_CLIENT_ID and PLAID_SECRET in Railway yet
- Follow step 1 above

**"Error: ANTHROPIC_API_KEY"**
- You haven't set ANTHROPIC_API_KEY in Railway yet
- Follow step 2 above
- Make sure it's a valid API key (starts with `sk-ant-`)

**Chat says "Error: Plaid not available"**
- pip install hadn't finished. Wait 2 minutes and refresh.

## Local Development (Optional)

To run locally instead:

```bash
# Set env vars
export PLAID_CLIENT_ID=your_id
export PLAID_SECRET=your_secret
export ANTHROPIC_API_KEY=your_key

# Run
python3 api.py

# Open
http://localhost:5000
```

## Next Steps

1. ✅ Get both API keys (5 minutes)
2. ✅ Add to Railway environment variables (1 minute)
3. ✅ Refresh dashboard (should auto-redeploy)
4. ✅ Set up your financial data (5 minutes)
5. ✅ Connect your bank (2 minutes)
6. ✅ Ask Claude questions

You're done! The system is now live and reasoning about your actual financial position.

---

**Questions?** Check the logs in Railway dashboard or see DEPLOYMENT.md
