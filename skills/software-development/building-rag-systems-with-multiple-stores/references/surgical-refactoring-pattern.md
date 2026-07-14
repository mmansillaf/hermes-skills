# Surgical Refactoring: Monolithic Functions → Composable Helpers

## When to apply
You have a Python function >300 lines in a production RAG system that has been heavily patched
(9+ fixes) and tested to 99-100% accuracy. You need to make it maintainable without breaking
any behavior. The function works correctly — the goal is structural clarity only.

## Core principle: BYTE-FOR-BYTE IDENTITY
The refactored code MUST produce identical outputs for ALL inputs. Not "similar" — identical.
Test with real queries BEFORE and AFTER each extraction.

## The pattern (6 steps)

### 1. Identify logical layers
Read the entire function. Annotate each block with its responsibility. Example from
`confidence_score()`:

```
Lines 348-467:  Capa 0 - Exact ID detection (patterns, hyphenated numbers, boost/penalty)
Lines 469-484:  Capa 0b - Year penalty
Lines 486-527:  Score calculation (semantic quality, SQLite, count, neo4j, base)
Lines 541-554:  Capa 1b - Jailbreak detection
Lines 557-630:  Capas 2+4+5 - Semantic overlap + existence + coexistence
Lines 632-647:  Capa 6 - Temporal anomaly
Lines 649-687:  Penalty application + debug + floor
```

### 2. Extract into helpers (one per layer)
Place helpers ABOVE the main function. Each helper:
- Takes explicit inputs (results, question, etc.)
- Returns a clean tuple/dict
- NEVER references external scope variables
- Has a one-line docstring in Spanish

```python
def _detect_exact_id(results, question, sqlite_source_count):
    """Capa 0: Detecta IDs exactos de normas en la pregunta."""
    # ... original logic, byte-for-byte identical ...
    return has_exact_id, sqlite_exact_boost, exact_id_penalty
```

### 3. Replace blocks with calls
Replace each extracted block in the main function with a single call:

```python
# BEFORE:
has_exact_id = ...
sqlite_exact_boost = 0.0
# ... 120 lines of exact ID logic ...

# AFTER:
has_exact_id, sqlite_exact_boost, exact_id_penalty = _detect_exact_id(results, question, sqlite_source_count)
```

### 4. Eliminate code duplication
Look for repeated patterns across helpers:
- Result dict construction (5+ times) → `_make_result()` factory
- Dedup+blend logic (40+ lines in one function) → `_dedup_and_blend()`
- Filler word lists → move to module-level constant

### 5. Test after EACH extraction
NEVER extract multiple layers without testing. After each extraction:

```python
# Quick test - 3 queries with different complexity levels
tests = [
    ("Ley 32108", "exact_id"),
    ("ley de contrataciones del estado", "broad"),
    ("dictamen sobre constitucionalidad", "avanzado"),
]
for q, label in tests:
    resp = query_api(q)
    assert resp["confidence"] >= 0 and "Error" not in resp.get("answer", "")
```

### 6. Commit after each extraction
One commit per layer extraction. This enables `git revert` of individual layers
if a bug is discovered later.

```bash
git add api_rest.py
git commit -m "refactor: extract _detect_exact_id from confidence_score"
git push origin main
```

## What to extract vs keep inline

| Situation | Action |
|-----------|--------|
| Independent block with clear input/output | EXTRACT to helper |
| Repeated pattern (dict construction, dedup) | EXTRACT to factory |
| Tightly coupled scoring with many intermediate locals | KEEP inline |
| Simple 3-5 line calculation used once | KEEP inline |
| Block with side effects (modifying results in place) | EXTRACT carefully, document mutation |

## Real-world results (El Peruano RAG, 2026-05-01)

```
BEFORE:
  confidence_score(): 354 lines, 6 layers intermixed
  search_sqlite():    468 lines, 40-line dedup block inline
  query_endpoint():   359 lines

AFTER:
  confidence_score():  80 lines (orchestrator) + 6 helpers
  _detect_exact_id(), _calc_year_penalty(), _detect_jailbreak(),
  _calc_semantic_defense(), _calc_temporal_anomaly(), _query_len_factor()
  _make_result() factory (replaced 5+ repeated dict constructions)
  _dedup_and_blend() (replaced 40-line inline dedup)

Tests: 10/10 queries passed, 0 regressions
  - exact_id, broad, exact_ds, count, fallback, avanzado, basico,
    basico_directo, precisa, procedimental
  - SQLi test (' OR '1'='1') handled correctly
```

## Pitfalls

### DON'T change logic during extraction
The single biggest risk: "while I'm here, let me fix this threshold." DON'T.
Extract FIRST, fix LATER. Mixing extraction with logic changes makes it impossible
to know which change caused a regression.

### DON'T change variable names
Keep `_has_real_overlap`, `_has_zero_match`, `_hyphenated_found` exactly as they are.
Renaming variables introduces subtle bugs if the same name is used elsewhere.

### DO initialize all variables at function top
Python's scoping rules bite hard when extracting blocks. Always initialize defaults:

```python
def _calc_semantic_defense(question, results):
    ratio = 1.0       # default: perfect overlap
    db_ratio = 1.0    # default: all words exist
    _has_zero_match = False
    _has_real_overlap = False
    # ... then conditionally overwrite inside if blocks ...
```

### DO use `.get()` for dict access across helpers
When extracting blocks that access results dicts, NEVER assume a key exists:

```python
# WRONG: crashes if key missing
r["relevance"]

# RIGHT: safe with default
r.get("relevance", 0)
r.get("_qdrant_score", 0.0)
r.get("_qdrant_contributed")
```

## User preferences encoded
- Código simple y fácil de entender y mantener (keep it simple)
- Pruebas conformes avanzas (test after every change)
- Snapshots antes de cambios (git tag + backup + checksum)
- Informes en MD + HTML + TXT con dark theme
