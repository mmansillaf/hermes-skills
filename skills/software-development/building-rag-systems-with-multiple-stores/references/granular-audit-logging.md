# Granular Audit Logging for Python Web Services

## When to use this pattern

You need a persistent, queryable audit trail of every significant operation in your application. The `query_history` table (last N queries) isn't enough — you need event types, categories, timestamps, success/failure, and structured detail for each operation.

## Architecture

A single SQLite table `audit_log` with indexes + helper methods on your storage class + REST endpoints for querying.

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    event_type TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    detail TEXT DEFAULT '',
    user TEXT DEFAULT 'local',
    ip_address TEXT DEFAULT '127.0.0.1',
    doc_id TEXT DEFAULT '',
    doc_name TEXT DEFAULT '',
    provider TEXT DEFAULT '',
    elapsed_ms INTEGER DEFAULT 0,
    success INTEGER DEFAULT 1,
    error_msg TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_log(event_type);
```

## Event Type Taxonomy

Categorize events so you can filter and aggregate. Use event_type for the action, category for the domain:

| event_type | category | When |
|---|---|---|
| `query` | consulta | Every RAG query |
| `query_stream` | consulta | Streaming query |
| `query_export` | consulta | Export to TXT/PDF |
| `history_export` | consulta | Export history entry |
| `ingest` | documento | Single document uploaded |
| `ingest_batch` | documento | Batch upload |
| `document_delete` | documento | Document deleted |
| `document_pin` | documento | Pin/unpin document |
| `document_categoria` | documento | Category changed |
| `settings_llm` | configuracion | Provider/model changed |
| `settings_api_key` | configuracion | API key updated |
| `settings_preferences` | configuracion | User preferences saved |
| `settings_test` | configuracion | Connection test |
| `server_start` | sistema | Application started |
| `server_stop` | sistema | Application stopped |
| `backup` | sistema | Backup ran |
| `error` | sistema | Unhandled error |

## Python Implementation

### Storage Class Methods

```python
def add_audit_entry(
    self,
    event_type: str,
    category: str = "general",
    detail: str = "",
    doc_id: str = "",
    doc_name: str = "",
    provider: str = "",
    elapsed_ms: int = 0,
    success: bool = True,
    error_msg: str = "",
    user: str = "local",
    ip_address: str = "127.0.0.1",
):
    conn = self._get_sqlite()
    conn.execute(
        """INSERT INTO audit_log
           (event_type, category, detail, user, ip_address,
            doc_id, doc_name, provider, elapsed_ms, success, error_msg)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (event_type, category, detail[:500], user, ip_address,
         doc_id, doc_name, provider, elapsed_ms, int(success), error_msg[:500]),
    )
    conn.commit()
    conn.close()
```

### Querying with Filters

```python
def get_audit_log(
    self,
    limit: int = 100,
    event_type: str = None,
    category: str = None,
    doc_id: str = None,
    since: str = None,
    success_only: bool = None,
) -> List[Dict]:
    conn = self._get_sqlite()
    where, params = [], []
    if event_type:
        where.append("event_type = ?"); params.append(event_type)
    if category:
        where.append("category = ?"); params.append(category)
    if doc_id:
        where.append("doc_id = ?"); params.append(doc_id)
    if since:
        where.append("timestamp >= ?"); params.append(since)
    if success_only is not None:
        where.append("success = ?"); params.append(1 if success_only else 0)
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    cursor = conn.execute(
        f"SELECT * FROM audit_log {where_sql} ORDER BY timestamp DESC LIMIT ?",
        params + [limit],
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
```

### Statistics

```python
def get_audit_stats(self) -> Dict:
    conn = self._get_sqlite()
    stats = {}
    cursor = conn.execute("SELECT COUNT(*) as c FROM audit_log")
    stats["total_events"] = cursor.fetchone()["c"]
    cursor = conn.execute(
        "SELECT event_type, COUNT(*) as c FROM audit_log GROUP BY event_type ORDER BY c DESC"
    )
    stats["by_type"] = {row["event_type"]: row["c"] for row in cursor.fetchall()}
    cursor = conn.execute(
        "SELECT category, COUNT(*) as c FROM audit_log GROUP BY category ORDER BY c DESC"
    )
    stats["by_category"] = {row["category"]: row["c"] for row in cursor.fetchall()}
    cursor = conn.execute(
        "SELECT DATE(timestamp) as d, COUNT(*) as c FROM audit_log GROUP BY d ORDER BY d DESC LIMIT 7"
    )
    stats["last_7_days"] = {row["d"]: row["c"] for row in cursor.fetchall()}
    conn.close()
    return stats
```

## REST Endpoints

Expose audit data via the API so operators can inspect it without direct DB access:

```python
@app.get("/audit")
async def get_audit_log(limit=100, event_type=None, category=None, doc_id=None, since=None, success_only=None):
    rows = store.get_audit_log(limit=limit, event_type=event_type, category=category,
                                doc_id=doc_id, since=since, success_only=success_only)
    return {"audit_log": rows}

@app.get("/audit/stats")
async def get_audit_stats():
    return store.get_audit_stats()

@app.get("/audit/types")
async def get_audit_event_types():
    return {"event_types": [
        "query", "query_stream", "query_export", "history_export",
        "ingest", "ingest_batch", "document_delete", "document_pin",
        "document_categoria", "settings_llm", "settings_api_key",
        "settings_preferences", "settings_test", "server_start",
        "server_stop", "backup", "error",
    ]}
```

## Integration Points

Wire audit calls into existing API handlers with try/except so failures never break the primary operation:

```python
@app.post("/ingest")
async def ingest_document(file, categoria="General"):
    result = process_document(...)
    store.add_chunks(result["chunks"], embeddings)

    # Audit — never let logging failure break the response
    try:
        store.add_audit_entry(
            event_type="ingest", category="documento",
            detail=f"Ingestado: {result['doc_name']} ({result['num_chunks']} chunks)",
            doc_id=result["doc_id"], doc_name=result["doc_name"],
        )
    except Exception as e:
        logger.warning(f"Error audit: {e}")

    return {"status": "ok", ...}
```

## Common Pitfalls

- **Never let audit-logging failures propagate** — wrap in try/except. A broken audit trail should not break the actual operation.
- **Truncate `detail` and `error_msg`** to 500 chars to keep rows small and queries fast.
- **Add indexes on timestamp and event_type** — the table grows unboundedly.
- **Make it optional at the config level** (AUDIT_ENABLED=1) so it can be disabled for performance testing.
- **Don't store full responses** in audit — the `query_history` table handles that. Audit is for events, not content.
