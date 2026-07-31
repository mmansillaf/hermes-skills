# Stale Credential Detective Pattern

## Problem

A RAG system's search endpoints fail with `password authentication failed`, but the RAG pipeline (`/api/query`) works fine. Both should use the same database, but one component authenticates and the other doesn't.

## Root Cause Pattern

The `.env` file has a **stale password** for PostgreSQL — it was correct when the project was first deployed but was later changed in the DB. A secondary build/test script has the **correct password** hardcoded because someone updated it there but forgot to update `.env`.

## Detective Technique

When the database connection fails:

1. **Search ALL files for the database user** — not just `.env`:
   ```bash
   grep -r "user_alg33" /opt/project/ --include="*.py" --include="*.env" --include="*.yaml" --include="*.yml" --include="*.conf" --include="*.sh" --include="*.cfg"
   ```

2. **Compare passwords across files** — the build/test scripts often have the current password because they're actively used for maintenance:
   - `file_a.env`: `DATABASE_URL=postgresql://user:stale_password@localhost:5432/db`
   - `file_b.py`: `PG_DSN = 'postgresql://user:correct_password@localhost:5432/db'`

3. **Verify directly with psql** before trusting any file:
   ```bash
   PGPASSWORD=candidate_password psql -h localhost -U dbuser -d dbname -c 'SELECT 1'
   ```

4. **Update .env and restart** — once verified, sync all files and restart the service.

## Why This Happens

| Scenario | Why `.env` gets stale | Why build script has correct password |
|----------|----------------------|--------------------------------------|
| Password rotation | Someone changed PG password but only updated the script they were running at the time | The build script was actively used to rebuild FAISS and needed creds to work |
| Multi-developer | Different devs use different credential files | A script committed to git has the "working" password |
| Deployment migration | `.env` was copied from an old deployment | Build scripts were written fresh for the new environment |

## Prevention

Add a startup health check that tests both DB connections and logs a warning if they differ:

```python
# At app startup
import os
from urllib.parse import urlparse

def check_db_credentials():
    url = os.getenv("DATABASE_URL")
    parsed = urlparse(url)
    # Test connection
    try:
        with create_engine(url).connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.critical(f"DB connection failed: {e}")
        # Don't crash — the app may work in degraded mode
```

## See Also

- `rag-prompt-engineering` skill — the RAG pipeline patterns that depend on a working DB connection
