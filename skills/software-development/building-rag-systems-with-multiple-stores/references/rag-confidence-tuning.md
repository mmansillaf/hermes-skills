# RAG Confidence Scoring Diagnostics & Tuning

## When to Use
- Functional queries get confidence < 0.50 and fall back to web unnecessarily
- Multiple stores return results but confidence floor is 0.20
- Test battery shows good retrieval but poor scoring
- Qdrant returns results but confidence scoring ignores them

## Step 1: Run Test Battery
Use the project's test battery (e.g., `tests/run_test_20_v25.py`) to establish baseline.
Key metrics: functional PASS%, adversarial PASS%, web fallback count, artifact usage per store.

## Step 2: Check Debug Internals
Hit `/query` endpoint and inspect `debug_internal` field:
```python
debug = response.get('debug_internal', {})
```
Key fields to check:
- `base_weighted`: raw score before penalties (should be 0.70+ for good results)
- `fp_penalty`: accumulated penalty from all capas (should be < 0.30 for functional)
- `_has_real_overlap`: boolean — if False with good Qdrant scores, overlap scope is too narrow
- `_has_zero_match`: if True for functional query, Capa 2 gate is too strict
- `meaningful_words`: filtered query terms — verify filler_words set isn't too aggressive

## Step 3: Trace the Penalty Chain
In `confidence_score()` function, penalties accumulate from 6 capas:
- **Capa 2** (line ~483): Semantic overlap check — checks if meaningful_words appear in result text
- **Capa 3** (line ~499): SQLite distinctiveness — penalizes when SQLite returns too many filler matches
- **Capa 4** (line ~519): DB existence check — penalizes if terms don't exist in DB at all
- **Capa 5** (line ~550): Term coexistence — penalizes if terms exist but never together in one document
- **Capa 6** (line ~620): Filler query penalty — for queries with no meaningful words

## Common Bugs Found

### Bug 1: Overlap Scope Too Narrow
**Symptom**: `_has_real_overlap=False` but Qdrant returns good scores.
**Cause**: Overlap check only inspects `results[:3]` or `results[:5]`. SQLite results (added first) dominate these positions. Qdrant results with actual semantic matches are at positions 15+.
**Fix**: Change `results[:N]` to `results` (all) in overlap text concatenation (lines ~449 and ~654).

### Bug 2: Qdrant Score Ignored in Overlap Signal
**Symptom**: Qdrant gives scores > 0.80 but `_has_real_overlap` still False.
**Cause**: Only text overlap matters; Qdrant semantic score is not used as a signal.
**Fix**: Add OR condition: `_has_real_overlap = (text condition) or (qdrant_scores and max_qdrant >= 0.70)`

### Bug 3: Penalty Threshold Too Strict
**Symptom**: `_has_real_overlap=True` but floor is still 0.20.
**Cause**: Condition `fp_penalty < 0.50` (line ~665) rejects queries with legitimate Capa5+Capa3 penalties. Terms spread across multiple norms trigger 0.30+0.25 = 0.55 penalty.
**Fix**: Relax threshold to `fp_penalty < 0.80`.

### Bug 4: Capa 5 Over-penalizes with Qdrant Confirmation
**Symptom**: Capa 5 adds 0.30 penalty even when Qdrant found good semantic matches.
**Cause**: "Terminos no coexisten" penalty is flat 0.30 regardless of Qdrant score.
**Fix**: When `max_qdrant >= 0.70`, reduce Capa 5 penalty from 0.30 to 0.10.

### Bug 6: Floor Protects Temporal False Positives
**Symptom**: Temporal query outside DB range ("normas peruanas del ano 2020") gets conf=0.75, no web fallback. Capa 6 applies penalties but floor `max(weighted, 0.75)` blocks them.
**Cause**: `sqlite_count >= 1` unconditionally activates floor, even when results are filler-word matches with zero temporal relevance.
**Fix**: Condition floor on actual relevance signals, not just count:
```python
# ANTES:
if sqlite_count >= 1:
    weighted = max(weighted, 0.75)

# DESPUÉS:
if sqlite_count >= 3 and max_sqlite_score > 0.5 and db_ratio >= 0.50:
    weighted = max(weighted, 0.75)
```
**Effect**: J1 ("normas del ano 2020") drops from 0.75 to ~0.30, activating web fallback. Valid queries with real relevance still get floor protection.

## Step 4: Verify Fixes
Rerun the test battery after each fix. Minimum target: functional PASS >= 80%, adversarial PASS = 100%.
Track: confidence values (aim for 0.70+), web fallback reduction, artifact usage diversity.

## Pitfalls
- Don't lower the adversarial floor (0.15 for type H) — that's for security
- Don't remove Capa 2 entirely — it catches genuine FPs
- The dedup at line ~1174 merges Qdrant results into SQLite, losing Qdrant-specific sumillas. The overlap check MUST use scores, not just text
- `results` list order: SQLite first (pos 0-14), Qdrant (15-19), Neo4j entity (20-24), Neo4j graph (25+). Any `results[:N]` slice with N<15 will miss Qdrant