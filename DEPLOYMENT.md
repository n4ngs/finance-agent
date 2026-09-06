# Personal CFO - Deployment Guide (Railway)

## Quick Start on Railway

### Step 1: Prepare Repository

```bash
# Initialize git if needed
git init
git add .
git commit -m "Initial Personal CFO commit"

# Create GitHub repository
# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/finance-agent.git
git push -u origin main
```

### Step 2: Deploy to Railway

1. Go to https://railway.app
2. Click "New Project"
3. Connect your GitHub account
4. Select this repository
5. Railway auto-detects Python
6. Configure environment variables (if using Plaid):
   ```
   PLAID_CLIENT_ID=your_client_id
   PLAID_SECRET=your_secret
   DATABASE_URL=postgresql://...  (Railway provides)
   ```
7. Deploy

### Step 3: Running on Railway

**Option A: Command-Line Interface (Recommended for Phase 1)**

```bash
# SSH into Railway environment
railway shell

# Run CLI
python3 main.py
```

**Option B: Web API (For Phase 2+)**

See `api.py` (to be built) for REST endpoints.

## Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (none for Phase 1)
pip install -r requirements.txt

# Run locally
python3 main.py
```

## Database on Railway

### Option 1: SQLite (Current - Phase 1)
- Simplest for initial development
- Stored as Railway volume
- Good for single user

### Option 2: PostgreSQL (Future - Phase 2+)
Railway provides free PostgreSQL. When ready:

1. Add PostgreSQL to Railway project
2. Update `database.py` to use `psycopg2`
3. Migrate schema with `migrate_to_postgres.py` (TBD)

## Environment Variables

Create `.env` file locally (don't commit):

```
DATABASE_PATH=~/.personal-cfo/finance.db
PLAID_CLIENT_ID=
PLAID_SECRET=
ENVIRONMENT=development
```

Railway UI will have fields for these.

## Monitoring & Logs

On Railway:
- View logs in Dashboard
- Errors appear in real-time
- Can tail logs from CLI:

```bash
railway logs
```

## Backups

### Daily Backup (Manual)

```bash
# From Railway shell
cp ~/.personal-cfo/finance.db ~/backups/finance.db.$(date +%Y%m%d)
```

### Automated Backup (Future)

```bash
# Set up cron job to upload to S3
# (Phase 3+)
```

## Scaling Considerations

| Metric | Phase 1 | Phase 2 | Phase 3+ |
|--------|---------|---------|----------|
| Users | 1 (you) | 1-10 | 100+ |
| Transactions/month | 100 | 500 | 10k+ |
| Database | SQLite | SQLite/PG | PostgreSQL |
| Memory | ~50MB | ~100MB | ~500MB |
| Concurrency | Sequential | Sequential | Handled by PG |

## Common Issues

### Issue: Database locked
**Cause:** SQLite doesn't handle concurrent writes
**Solution:** Upgrade to PostgreSQL when needed

### Issue: Railway can't find finance.db
**Cause:** Path doesn't exist
**Solution:** Run setup first time with Railway shell

### Issue: Plaid OAuth failing
**Cause:** Redirect URI doesn't match
**Solution:** Add Railway URL to Plaid dashboard settings

## Rollback

If something breaks:

```bash
# Railway stores deployment history
# Click "Previous Deployment" in dashboard
```

## Next Steps

1. Deploy Phase 1 to Railway (CLI only)
2. Test with your actual financial data
3. Build Phase 2 (Web API)
4. Add Plaid integration
5. Migrate to PostgreSQL (if needed)
