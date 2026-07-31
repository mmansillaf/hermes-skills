---
name: python-dev-workflow
description: "End-to-end Python development: scaffold, lint, test, type-check, security"
tags: [python, development, testing, linting, debugging, fastapi, web]
category: development
---

## ⚠️ MANDATORIO: SDD+TDD para todo desarrollo

**POR ORDEN DEL USUARIO (29 Jul 2026):**
Todo trabajo de programación — sin excepción — debe seguir SDD+TDD:
1. **SDD**: Escribir la especificación (spec) ANTES de tocar código
2. **TDD**: Escribir el test fallido (RED) ANTES de escribir código
3. Solo después de spec aprobada → test fallido verificado → implementar (GREEN)
4. Refactor (REFACTOR) manteniendo tests verdes

**Excepciones:** Solo si el usuario lo autoriza explícitamente.
**Para proyectos ya iniciados sin SDD/TDD:** Escribir spec post-hoc y tests ahora.
Ver skill `spec-driven-development` para el flujo completo.

## When to Use
User wants to create, refactor, test, debug, or review Python code — especially FastAPI web applications with SQLAlchemy backends.

## Procedure

### 1. Linting & Formatting
```bash
ruff format .
ruff check . --fix
mypy src/ --strict
```

### 2. Testing
```bash
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

### 3. Security Scan
```bash
bandit -r src/ -f json -o bandit-report.json || true
safety check --json --output safety-report.json || true
```

## Debugging Python Web Apps

### Trace User-Reported Errors Through the Request Pipeline

When a user reports an error from the browser/frontend:
1. **Test the API directly via curl** — bypass frontend JS issues
2. Get the full Python traceback from the API response or server logs
3. **Trace the variable name** from the error back to its definition site
4. Check if the variable is supposed to come from a helper function

### Pattern: NameError from Missing Helper Call

**Symptom:** `NameError: name 'X' is not defined` in a function that uses `X` in f-strings.

**Common in:** FastAPI backends where a helper function was extracted to return column names or table names, but some call sites were never updated.

**Diagnosis:**
- Find a sibling function that works — compare its variable setup
- The broken function references `X` but never calls the helper that sets `X`
- Example: function uses `content_col`, `summary_col`, `table_name` but never calls `_get_columns(source)`

**Fix:**
```python
# Add the missing helper call
table_name, content_col, summary_col, tipo_col = _get_columns(source)
```

### Pattern: Parameter Not Propagated

**Symptom:** A function has a parameter with a sensible default, but callers use the default when they should pass a real value.

**Diagnosis:**
```bash
grep -rn "function_name(" src/ --include="*.py"
```

**Fix:** Add the missing parameter at each call site.

### Pattern: Adding a RAG Chat Tab to a Search Frontend

When the user wants a conversational AI answer alongside document search results:

1. Search frontends typically show document results (scores, sumillas, metadata)
2. Add a third tab "Consultar" that calls the RAG pipeline endpoint (`/api/query`)
3. The RAG tab needs: a textarea for questions, a "Consultar" button, and a response area
4. Response format: source badge, timing, 1-2 paragraphs with `[Doc: ID]` citations, grounding score
5. Key JS pattern:
```javascript
const res = await fetch(API + '/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
  body: JSON.stringify({ query })
});
```
6. Format the response as a styled card with grounding bar
7. Fresh queries (not cached) include grounding verification; cached responses return `grounding: null`

### Frontend State Hygiene
- Date inputs should start empty (`value=""`) — avoids stale browser autofill
- When switching tabs, hide results from the previous tab
- Test login + search visually after every backend change

### Frontend Error Handling for FastAPI Backends

**Problem:** FastAPI returns Pydantic validation errors as `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` — an **array**, not a string. If the frontend does `throw new Error(data.detail)`, the message becomes `"[object Object]"`.

**Fix — parse detail before throwing:**
```javascript
if (!res.ok) {
  const d = data.detail;
  let detail = 'Error (' + res.status + ')';
  if (typeof d === 'string') detail = d;
  else if (Array.isArray(d)) detail = d.map(x => x.msg || JSON.stringify(x)).join('; ');
  else if (d && typeof d === 'object') detail = JSON.stringify(d);
  throw new Error(detail);
}
```

**Also handle non-JSON error responses** (res.json() may fail):
```javascript
let data;
try {
  data = await res.json();
} catch (_) {
  const text = await res.text();
  throw new Error(text.slice(0, 200) || 'Error ' + res.status);
}
```

### Date Format Normalization

**Problem:** `<input type="date">` in some browsers/locales sends dates in DD/MM/YYYY or DD.MM.YYYY instead of ISO (YYYY-MM-DD). FastAPI rejects these with "invalid character in year".

**Fix — normalize before sending:**
```javascript
function parseDate(val) {
  if (!val) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(val)) return val;  // already ISO
  const m = val.match(/^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})$/);  // DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
  if (m) return `${m[3]}-${m[2].padStart(2,'0')}-${m[1].padStart(2,'0')}`;
  return val;
}
```

Then apply:
```javascript
const from = parseDate(document.getElementById('search-from').value);
const to = parseDate(document.getElementById('search-to').value);
```

### Error Display Helper
```javascript
function errToStr(e) {
  if (!e) return 'Error desconocido';
  if (typeof e === 'string') return e;
  if (e.message && typeof e.message === 'string') return e.message;
  try { return JSON.stringify(e); } catch(_) { return String(e); }
}
```

## Pitfalls
- Don't run tests in production environment
- Don't ignore mypy errors in new code
- Don't skip security scans before PRs
- **When a user reports a frontend error, test the API directly first** — the browser may mask the real error
- **Don't assume cached query responses have grounding data** — cache returns `grounding: null`
- **Parameter propagation bugs** are common after refactoring — always check all callers of a refactored function pass new parameters
- A function that has a `source` parameter defaulting to `"normas"` will silently return wrong results if the caller doesn't pass `source=source`

## Verification
- All tests pass: pytest exit code 0
- No lint errors: ruff check exit code 0
- Type-safe: mypy exit code 0
- No critical/high bandit findings
- Frontend login + search work end-to-end via browser tool
