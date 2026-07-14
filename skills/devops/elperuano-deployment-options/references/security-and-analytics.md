# Production Security & User Analytics — El Peruano RAG

**Date:** 2026-05-01
**Status:** Design complete, awaiting implementation

## Security Checklist

| Item | Priority | Status |
|------|----------|--------|
| Rate limiting per IP | HIGH | Not implemented |
| Rate limiting per user | HIGH | Not implemented |
| JWT authentication | HIGH | Not implemented |
| Password hashing (bcrypt) | HIGH | Not implemented |
| SQLite input sanitization | MEDIUM | Not implemented |
| Prompt injection sanitization | MEDIUM | Not implemented |
| Restrictive CORS | MEDIUM | Currently `*` |
| HTTPS (Cloudflare Tunnel) | HIGH | Planned |
| `.env` in `.gitignore` | HIGH | Done |

## Dependencies

```
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
slowapi>=0.1.9
geoip2>=4.8.0                # MaxMind GeoLite2 free DB
```

## Rate Limiting Strategy

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/query")
@limiter.limit("10/minute")     # Per IP (visitor)
@limiter.limit("30/minute")     # Per authenticated user
@limiter.limit("200/hour")      # Global cap (protect Groq budget)
```

## JWT Authentication Flow

```
POST /auth/register  → email, password, nombre, telefono?
  → bcrypt hash password
  → INSERT INTO usuarios
  → return user_id

POST /auth/login     → email, password
  → verify bcrypt hash
  → generate JWT (24h expiry)
  → return {"access_token": "..."}

POST /query          → Authorization: Bearer <jwt>
  → decode JWT
  → attach user_id to query_log
  → apply user rate limit
```

## Database Schema (new tables)

```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    telefono TEXT,
    especialidad TEXT,          -- penal, civil, tributario, etc.
    firma_estudio TEXT,
    ciudad TEXT,
    registro_fecha TEXT DEFAULT (datetime('now')),
    ultimo_login TEXT,
    consultas_totales INTEGER DEFAULT 0,
    consultas_hoy INTEGER DEFAULT 0,
    plan TEXT DEFAULT 'gratuito',
    activo BOOLEAN DEFAULT 1
);

CREATE TABLE query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES usuarios(id),
    session_id TEXT,             -- UUID from frontend localStorage
    question TEXT NOT NULL,
    answer_preview TEXT,         -- first 200 chars
    confidence REAL,
    router_level TEXT,           -- BASICO/INTERMEDIO/AVANZADO
    sources_used TEXT,           -- JSON: {"sqlite":5, "qdrant":3}
    response_time_ms INTEGER,
    cache_hit BOOLEAN DEFAULT 0,
    ip_address TEXT,
    user_agent TEXT,
    referer TEXT,
    geo_country TEXT,            -- from MaxMind GeoLite2
    geo_city TEXT,
    consulta_timestamp TEXT DEFAULT (datetime('now')),
    feedback TEXT                -- util/no_util
);

CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    ip_address TEXT,
    user_agent TEXT,
    consultas_count INTEGER DEFAULT 0
);

-- Indices
CREATE INDEX idx_query_log_user ON query_log(user_id);
CREATE INDEX idx_query_log_time ON query_log(consulta_timestamp);
CREATE INDEX idx_query_log_session ON query_log(session_id);
```

## User History (last 20 queries)

```python
@app.get("/user/history")
async def get_history(token=Depends(security), limit: int = 20):
    user_id = decode_jwt(token)
    rows = db.execute(
        "SELECT question, answer_preview, consulta_timestamp, router_level "
        "FROM query_log WHERE user_id=? ORDER BY consulta_timestamp DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    return [dict(r) for r in rows]
```

## Visitor → Registered Flow

```
Visitor (no login):
  - session_id generated in frontend (localStorage)
  - query_log stores session_id + IP + User-Agent + GeoIP
  - Max 5 queries/day without registration
  - At 5th query: modal "Register for unlimited queries"

Registration:
  - POST /auth/register
  - Previous queries from session_id are linked to new user_id
  - Optional welcome email

Registered User:
  - Login with JWT (24h validity)
  - 30 queries/day (free plan)
  - Full history at /user/history
```

## Marketing Data Capture

**Without login:** IP → country/city, device type, traffic source, hour of day, search terms

**With login:** email, name, phone, legal specialty, firm/office, query frequency, norm types consulted, feedback

**Highest value for legal SaaS:**
- **Legal specialty** → segment campaigns
- **Usage frequency** → identify power users for upsell
- **Norm types** → targeted content
- **Email** → newsletter with relevant new norms

## Admin Dashboard

```python
@app.get("/admin/stats")
async def admin_stats(api_key: str):
    # Verify ADMIN_API_KEY
    return {
        "consultas_hoy": count_today(),
        "usuarios_activos": active_users(),
        "top_terms": top_search_terms(10),
        "cache_hit_rate": cache_hit_pct(),
        "avg_response_time_ms": avg_response_time(),
        "router_distribution": router_stats(),
        "gasto_groq_estimado": estimate_groq_cost(),
    }
```
