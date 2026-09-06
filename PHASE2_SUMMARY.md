# Personal CFO - Phase 2 Complete

## What's Been Built

### Web Dashboard
- Clean, responsive interface (desktop & mobile)
- Real-time financial status cards
  - Liquid Cash
  - Safe to Spend
  - Financial Floor
  - Upcoming Obligations (30d)
- Status indicator (Comfortable / Tight / Constrained)

### Chat with Claude
- Natural language financial questions
- Claude sees your complete financial state
- Examples:
  - "How much can I spend this weekend?"
  - "Can I afford a $2,500 MacBook?"
  - "What if I buy the laptop AND take a $1,500 trip?"
- Claude reasons about affordability, timing, goals, and consequences

### Plaid Bank Integration
- OAuth flow for secure bank linking
- Auto-sync accounts and balances
- Auto-sync transactions
- Transaction deduplication (won't import duplicates on re-sync)
- Multi-bank support (link multiple banks)
- Incremental sync using cursors (efficient)

### Claude AI Reasoning
- Financial context automatically sent to Claude
- Claude receives:
  - Your liquid cash
  - Your safe-to-spend amount
  - Your financial floor
  - Your upcoming obligations
  - Complete breakdown of reserves
- Claude reasons about:
  - Whether you can afford something
  - Whether the timing is good
  - Impact on goals
  - Opportunity costs
  - Alternative strategies

## Technology Stack

**Frontend:**
- HTML/CSS/JavaScript (no frameworks, vanilla DOM)
- Responsive design
- Zero build step

**Backend:**
- Python Flask
- SQLite (persistent database)
- Thread-safe (new connection per request)

**Integrations:**
- Plaid Python SDK (bank data)
- Anthropic Python SDK (Claude API)

**Deployment:**
- Docker on Railway
- Auto-deploy from GitHub
- Environment variables for secrets

## How to Activate

See **PHASE2_SETUP.md** for complete instructions, but summary:

1. **Get Plaid credentials:**
   - https://dashboard.plaid.com/signup
   - Copy client_id and secret
   - Add to Railway environment variables

2. **Get Anthropic API key:**
   - https://console.anthropic.com
   - Create API key
   - Add to Railway environment variables

3. **Railway redeploys automatically**

4. **Open dashboard:**
   - https://finance-agent-production-694c.up.railway.app
   - Set up your finances (balances, income, obligations, goals)
   - Connect your bank (Plaid)
   - Start asking Claude questions

## Live URLs

**Dashboard:** https://finance-agent-production-694c.up.railway.app

**API Endpoints:**
- `GET /health` — Health check
- `GET /api/status` — Your financial status
- `POST /api/setup` — Initial setup (or manual entry)
- `POST /api/purchase` — Evaluate a purchase
- `POST /api/transaction` — Record spending
- `POST /api/plaid/link-token` — Start Plaid OAuth
- `POST /api/plaid/exchange` — Complete Plaid OAuth
- `POST /api/plaid/sync` — Manual sync from Plaid
- `POST /api/claude/query` — Ask Claude a question

## Security

✓ Bank passwords: Never stored (Plaid handles OAuth)
✓ Full card numbers: Never asked for
✓ SSN/government IDs: Never asked for
✓ Credentials: Stored securely on Railway
✓ Database: Encrypted at rest (Railway feature)
✓ API: HTTPS only
✓ Keys: Environment variables (not in code)

## Cost

- **Railway:** Free tier (covers this workload)
- **Plaid:** Free tier (100 transactions/month)
- **Anthropic:** ~$0.03 per question
- **Total:** Free to start, ~$3/month if you ask 100 questions

## Architecture Diagram

```
┌─────────────────────┐
│   Your Browser      │
│  (Web Dashboard)    │
└──────────┬──────────┘
           │ HTTPS
           ↓
┌─────────────────────────────┐
│   Railway (Cloud)           │
│                             │
│  ┌─────────────────────┐   │
│  │  Flask API          │   │
│  ├─────────────────────┤   │
│  │ /api/status         │   │
│  │ /api/purchase       │   │
│  │ /api/plaid/*        │   │
│  │ /api/claude/query   │   │
│  └─────────────────────┘   │
│           │                 │
│  ┌────────┴────────┬────────┐
│  │                 │        │
│  ↓                 ↓        ↓
│ SQLite DB       Plaid API  Claude API
│ (your data)  (bank sync)  (reasoning)
│
└─────────────────────────────┘
```

## What's Next (Phase 3+)

- Mobile app
- Advanced anomaly detection
- Subscription auditor
- Investment tracking
- Tax planning
- Multi-user/household budgets
- Export to CSV/PDF
- Savings goal visualizations

## Files

**Core:**
- `api.py` — Flask API (root serves dashboard)
- `frontend.html` — Web dashboard
- `cfo.py` — Financial orchestrator
- `calculations.py` — Deterministic math
- `database.py` — SQLite persistence
- `plaid_integration.py` — Plaid OAuth & sync
- `router.py` — Natural language routing

**Config:**
- `requirements.txt` — Python dependencies
- `Dockerfile` — Container for Railway
- `railway.json` — Railway config
- `schema.sql` — Database schema

**Docs:**
- `README.md` — Quick start
- `ARCHITECTURE.md` — System design
- `DEPLOYMENT.md` — Railway deployment
- `PHASE1_SUMMARY.md` — Phase 1 recap
- `PHASE2_SUMMARY.md` — This file
- `PHASE2_SETUP.md` — Setup instructions

## Status

✅ Phase 1: Core calculations & CLI → COMPLETE
✅ Phase 2: Web dashboard + Plaid + Claude → COMPLETE
🔄 Deployment: Live on Railway, waiting for your API keys

**Next action:** Follow PHASE2_SETUP.md to activate Plaid and Claude.

---

Your Personal CFO is live and ready to help you make better financial decisions.
