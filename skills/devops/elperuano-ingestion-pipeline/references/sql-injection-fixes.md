# SQL Injection Fixes — api_rest.py

Fixed 02-may-2026. 5 critical SQL injection vulnerabilities found and fixed.

## Pattern: Always use parameterized queries

**BAD (vulnerable):**
```python
# String interpolation — DO NOT USE
db.execute(f"SELECT 1 FROM normas WHERE sumilla LIKE '%{word}%'")
db.execute(f"SELECT ... FROM normas WHERE numero LIKE '%{num}%' LIMIT 1")
```

**GOOD (safe):**
```python
# Parameterized query with placeholders
db.execute("SELECT 1 FROM normas WHERE sumilla LIKE ?", (f"%{word}%",))
db.execute("SELECT ... FROM normas WHERE numero LIKE ? LIMIT 1", (f"%{num}%",))
```

## Locations fixed in api_rest.py

| # | Location | Line (pre-fix) | Pattern |
|---|----------|---------------|---------|
| 1 | Capa 5 coexistence | ~613 | `f"sumilla LIKE '%{w}%'"` → `sumilla LIKE ?` + params |
| 2 | FASE 2 leyes | ~768 | `f"sumilla LIKE '%{w}%'"` → `sumilla LIKE ?` + params |
| 3 | Fallback LIKE | ~1009 | `f"sumilla LIKE '%{t}%'"` → `sumilla LIKE ?` + params |
| 4 | Number override | ~1456 | `f"numero LIKE '%{num}%'"` → `numero LIKE ?` + tuple |
| 5 | Date clauses | ~761 | Dates from controlled regex — lower risk but also fixed with params |

## Also fixed: Bug de indentación

Line ~1748: `return` was INSIDE the `for r in unique_results:` loop (same indentation as `r.pop()`).
Only the first result was cleaned of internal fields (`blend_score`, `_qdrant_score`, `_neo4j_signal`).
Fix: dedent `return` by 4 spaces to be OUTSIDE the for loop.

## Score pattern

For LIKE with multiple conditions:

```python
words = list(meaningful_words)[:4]
conditions = " AND ".join(["(sumilla LIKE ? OR titulo LIKE ?)" for _ in words])
params = []
for w in words:
    params.extend([f"%{w}%", f"%{w}%"])
row = db.execute(f"SELECT 1 FROM normas WHERE {conditions} LIMIT 1", params).fetchone()
```

Note: the `{conditions}` part uses f-string for the SQL structure (number of placeholders), but ALL user data goes through `params`.
