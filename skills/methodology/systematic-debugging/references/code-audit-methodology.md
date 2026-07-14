# Code Audit Methodology (Static Analysis Extension)

Extends `systematic-debugging` Phase 1 to whole-codebase audits. Use when the task is "review this code for issues" rather than "fix this specific bug."

## When to Use

- User asks "revisa el código", "audita esto", "¿qué problemas tiene?"
- Before major refactoring or optimization work
- Before deploying to production
- After accumulating many patches/fixes (check for accumulated technical debt)

## Audit Process

### Step 1: Get Metrics

```bash
wc -l api_rest.py       # total lines
grep -c "^def " api_rest.py  # function count
grep -c "^import " api_rest.py  # import count
```

### Step 2: Read in Blocks

For files >500 lines, use `delegate_task` subagent with `read_file` in blocks of 500 lines. This ensures complete coverage.

```
delegate_task(
    goal="Auditar api_rest.py — identificar problemas",
    context="Lee en bloques de 500 líneas con read_file. Clasifica por severidad.",
    toolsets=["file"]
)
```

### Step 3: Classify by Severity

| Severity | Criteria | Action |
|----------|----------|--------|
| **CRÍTICO** | Security hole, data loss, incorrect results | Fix before deploy |
| **ALTO** | Maintainability blocker, race condition, wrong behavior in edge case | Fix before new features |
| **MEDIO** | Code smell, duplication, inconsistent patterns | Refactor progressively |
| **BAJO** | Dead code, style issues, unused imports | Clean when convenient |

### Step 4: Categorize Patterns

Common patterns to look for (PeruanoSearchEngine02 findings as template):

- **SQL Injection**: String interpolation in SQL queries (5 found)
- **Monolithic functions**: >300 lines (3 found: 354, 468, 359)
- **Duplicate code**: Same logic in 2+ places (overlap calc, dict construction)
- **Error handling**: `except: pass` without logging (10+ found)
- **Thread safety**: `global` singletons in async context (4 found)
- **Dead code**: Unused imports, variables, functions (~30 lines found)
- **Import hygiene**: `import re` repeated 10 times, `import sqlite3` 4 times

### Step 5: Prioritize Recommendations

1. CRÍTICO fixes first (security, bugs)
2. Structural refactoring (split monoliths)
3. Feature additions (only on clean code)
4. Cleanup (dead code, style)

## Real-World Example

PeruanoSearchEngine02 `api_rest.py` (1959 lines) audit found:
- 5 CRÍTICO (4 SQL injection, 1 bug indentación)
- 13 ALTO (monolithic functions, thread safety, duplicate code)
- 16 MEDIO
- 8 BAJO

Recommendation: fix CRÍTICOs before deploying, split monoliths before adding streaming/parallel features.

## Snapshot-Before-Changes Workflow

BEFORE applying any fix, create a 3-layer rollback safety net:

```bash
# 1. Git tag (immutable, push to remote)
git tag -a "v4.0-pre-fix-YYYYMMDD" -m "Snapshot pre-fix: descripcion"
git push origin v4.0-pre-fix-YYYYMMDD

# 2. File backup (local, quick recovery)
cp archivo.py backups/archivo_v4.0_pre_fix.py

# 3. Checksum (verify integrity)
sha256sum archivo.py > backups/archivo_v4.0.sha256
```

Rollback options:
```bash
git checkout v4.0-pre-fix-YYYYMMDD           # Full repo rollback
cp backups/archivo_v4.0_pre_fix.py archivo.py  # Single file rollback
sha256sum -c backups/archivo_v4.0.sha256       # Verify backup matches original
```

## SQL Injection Fix Pattern (Python sqlite3)

Python's `sqlite3` module supports `?` placeholders. For LIKE queries, put `%` in the parameter, not in the SQL:

```python
# ❌ SQL INJECTION (user input interpolated)
db.execute(f"SELECT * FROM normas WHERE sumilla LIKE '%{word}%'")

# ✅ PARAMETERIZED (safe)
db.execute("SELECT * FROM normas WHERE sumilla LIKE ?", (f"%{word}%",))

# ✅ MULTI-WORD (with dynamic conditions)
words = ["transporte", "contrataciones"]
conditions = " AND ".join(["(sumilla LIKE ? OR titulo LIKE ?)" for _ in words])
params = []
for w in words:
    params.extend([f"%{w}%", f"%{w}%"])
db.execute(f"SELECT * FROM normas WHERE {conditions}", params)
```

The `%` wildcards go in the PARAMETER tuple, never in the SQL string. This prevents attackers from injecting `' OR 1=1 --` through user queries.
