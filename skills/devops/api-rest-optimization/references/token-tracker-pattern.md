# Token Tracker Integration Pattern

## Problem
Need to track LLM token consumption (prompt + completion) per API call with cost estimation, without breaking the main flow or adding latency.

## Solution
Python singleton `TokenTracker` class backed by SQLite, injected via monkey-patch with 3-4 lines per call site.

## Architecture

```
generate_answer() / generate_answer_stream()
    │
    ├── t0 = time.time()                          ← 1 line
    ├── resp = requests.post(groq_api, ...)        ← existing
    ├── data = resp.json()                          ← existing
    └── _track_groq_call(model, data["usage"], ...) ← 1 line
               │
               ▼
        TokenTracker.log()
            │
            ▼
        SQLite (data/tokens.db)
```

## Key design decisions

1. **Optional**: If `TokenTracker` fails to init (no write perms, bad path), `_enabled = False` and all operations are no-ops. No exceptions propagate.
2. **Fail-silently**: `_track_groq_call()` wraps everything in try/except with `pass`. Never breaks main flow.
3. **Singleton**: `get_tracker(db_path)` returns cached instance. Connection is thread-safe via SQLite WAL.
4. **Endpoint**: `GET /token-stats?granularity=diario|mensual|total` exposes aggregated data with USD cost estimates.

## SQLite schema

```sql
CREATE TABLE IF NOT EXISTS token_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    modelo TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    endpoint TEXT DEFAULT 'chat/completions',
    question_preview TEXT,
    profile TEXT DEFAULT 'abogado',
    duracion_ms INTEGER,
    cache_hit INTEGER DEFAULT 0
);
```

## Groq pricing (May 2026)

```python
GROQ_PRICING = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant":    {"input": 0.05, "output": 0.08},
}
```

## Integration example

```python
# In generate_answer():
t0_groq = time.time()
resp = _rq.post(url, json=payload, timeout=45)
resp.raise_for_status()
data = resp.json()
_track_groq_call(
    model=model,
    usage=data.get("usage", {}),
    endpoint="chat/completions",
    question=question[:60],
    profile=profile,
    duracion_ms=int((time.time() - t0_groq) * 1000),
    cache_hit=False,
)
return data["choices"][0]["message"]["content"].strip()
```

## Verification

```bash
# Check tracking is working
curl http://localhost:8000/token-stats?granularity=total
# Expected: {"costo_total_acumulado_usd": 0.063, "data": [...]}

# Check daily breakdown
curl http://localhost:8000/token-stats?granularity=diario&days=7
```
