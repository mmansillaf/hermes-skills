# Refactoring Patterns for api_rest.py

## The _make_result() Factory

**Problem**: Result dicts were constructed 5+ times with identical fields. Changes to the schema required editing 5 places.

**Solution**: Single factory function.

```python
def _make_result(row, source, relevance=0.0, **extra):
    result = {
        "id": row.get("id", ""), "tipo": row.get("tipo", row.get("tipo_norma", "")),
        "numero": row.get("numero", ""), "fecha": row.get("fecha", row.get("fecha_publicacion", "")),
        "emisor": row.get("emisor", ""), "sumilla": row.get("sumilla", ""),
        "source": source, "relevance": relevance,
    }
    for k, v in extra.items():
        if v is not None: result[k] = v
    return result
```

## Extract Monolithic Functions into Named Helpers

**Before**: `confidence_score()` was 354 lines with 6 interleaved defense layers.

**After**: 
- `confidence_score()` orchestrates (80 lines)
- `_detect_exact_id()` — Capa 0: exact norm ID detection
- `_calc_year_penalty()` — Penalize wrong-year results
- `_detect_jailbreak()` — Capa 1b: adversarial prompt patterns
- `_calc_semantic_defense()` — Capas 2+4+5: overlap + existence + coexistence
- `_calc_temporal_anomaly()` — Capa 6: temporal gap penalty
- `_query_len_factor()` — Reduce penalties for long analytical queries

Each helper is independently testable. The orchestrator is readable at a glance.

## Cache LRU: Order Matters (PITFALL)

**Bug**: Cache check was placed AFTER search_sqlite(), so the expensive search ran before checking if the answer was already cached.

**Fix**: Cache check MUST be at the very start of query_endpoint(), BEFORE any search. When returning cached data, update timing_ms and add cached=True flag.

## ThreadPoolExecutor for Parallel Qdrant+Neo4j

Inside search_sqlite(), after FTS5 completes, Qdrant and Neo4j are independent. Use ThreadPoolExecutor(max_workers=2) to run them concurrently. Speedup: 330ms → 200ms (1.65x).
