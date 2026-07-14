# Code Refactoring Methodology (api_rest.py)

## The problem

api_rest.py grew to 1959 lines with 3 monolithic functions:
- `confidence_score()` — 354 lines, 6 defense layers
- `search_sqlite()` — 468 lines, 4 search sources + dedup + blend
- `query_endpoint()` — 359 lines, router + validation + negation check

## The approach: Extract helpers, keep behavior, test between steps

### Step 1: Identify logical boundaries

Read each function and mark where one logical concern ends and another begins. For `confidence_score()`:
1. Exact ID detection (~130 lines)
2. Year penalty (~15 lines)
3. Semantic quality calculation (~40 lines)
4. Jailbreak detection (~15 lines)
5. Semantic defense (overlap + existence + coexistence, ~80 lines)
6. Temporal anomaly (~15 lines)
7. Penalty application + debug + floor (~40 lines)

### Step 2: Extract one helper at a time

For each logical block:
1. Copy the EXACT code into a new function `_helper_name(params)`
2. Add clear docstring explaining what it does
3. Replace the inline block with a call to the helper
4. Test IMMEDIATELY — run 2-3 queries to verify same output

**Golden rule:** Keep the extracted code IDENTICAL. No cleanup yet. Move first, optimize later.

### Step 3: After all helpers are extracted, simplify the orchestrator

The main function now reads like a recipe:
```python
def confidence_score(results, question, sqlite_source_count):
    has_exact_id, boost, penalty = _detect_exact_id(results, question, ...)
    year_penalty = _calc_year_penalty(question, results)
    # ... semantic quality ...
    if _detect_jailbreak(question): fp_penalty += 0.50
    semantic_fp, debug = _calc_semantic_defense(question, results)
    fp_penalty += _calc_temporal_anomaly(question, results)
    # ... apply penalties, floor, return ...
```

### Step 4: Test with real queries

Run 10 queries covering all complexity levels. Verify:
- Same results count
- Same confidence scores
- Same debug_internal fields
- No regressions

### Result: 354 lines → 80 lines orchestrator, 6 helpers

Each helper is independently testable and readable.

## Factory function pattern

When the same dict construction appears 5+ times, extract a factory:

```python
def _make_result(row, source, relevance=0.0, **extra):
    """Factory for result dicts — eliminates repeated constructions."""
    result = {
        "id": row.get("id", ""),
        "tipo": row.get("tipo", row.get("tipo_norma", "")),
        "numero": row.get("numero", ""),
        "fecha": row.get("fecha", row.get("fecha_publicacion", "")),
        "emisor": row.get("emisor", ""),
        "sumilla": row.get("sumilla", ""),
        "source": source,
        "relevance": relevance,
    }
    for k, v in extra.items():
        if v is not None: result[k] = v
    return result
```

## Dedup + blend extraction

The dedup-and-blend logic (47 lines) was repeated nowhere but was a well-defined concern:

```python
def _dedup_and_blend(results, top_k):
    """Deduplica por numero de norma, aplica blend scoring, ordena."""
    seen_nums = set()
    blended = []
    for r in results:
        num = r.get("numero", "")
        if num and num not in seen_nums:
            seen_nums.add(num)
            r["blend_score"] = round(0.50 * r.get("relevance", 0) + ...)
            blended.append(r)
        elif num and num in seen_nums:
            # Merge: take max scores across sources
            for existing in blended:
                if existing.get("numero") == num:
                    existing["relevance"] = max(...)
                    ...
    return sorted(blended, key=lambda x: x.get("blend_score"), reverse=True)[:top_k * 2]
```

## Anti-patterns avoided

1. **Don't rewrite while extracting.** Move code first, optimize later. Rewriting while extracting creates subtle bugs.
2. **Don't skip tests between steps.** Test after EVERY extraction. One bug after 6 extractions means undoing all 6.
3. **Don't change function signatures without need.** Keep the same parameters even if some seem redundant.
4. **Don't remove comments during extraction.** The FIX comments document past bugs and their fixes. They're valuable.
