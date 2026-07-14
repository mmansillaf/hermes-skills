# KAG Patterns Integration — El Peruano RAG

## Overview

Three KAG-inspired patterns integrated into the El Peruano RAG pipeline via
surgical, flag-gated additions to `api_rest.py`. Each phase is independent
and reversible.

## Files

```
src/kag_patterns/
├── __init__.py
├── mutual_index.py      # Fase A: find_in_text(), enrich_with_citations()
├── ontologia_legal.py   # Fase B: entity types, semantic relations, role inference
└── query_planner.py     # Fase C: is_multi_hop(), decompose()
```

## Integration Points (5 faltas in api_rest.py)

1. **Flags** (line 21): `KAG_PLANNING`, `KAG_MUTUAL_INDEX`, `KAG_SCHEMA` — env vars, default ON
2. **Multi-hop detection** (after classifier): `is_multi_hop()` + `decompose()` with try/except
3. **Plan execution** (after search_sqlite): executes step 1 SQL, filters steps 2+ via keywords
4. **Citation enrichment** (after graph expansion): `enrich_with_citations()` adds `_citas` field
5. **Role inference** (in `_enrich_entities`): replaces ad-hoc role detection with `infer_role_from_sumilla()`

All additions wrapped in `try/except ImportError` — never breaks the pipeline.

## Flag Usage

```bash
# Default: all ON
export KAG_PLANNING=0       # disable multi-hop detection
export KAG_MUTUAL_INDEX=0   # disable citation enrichment
export KAG_SCHEMA=0         # disable ontology-based role inference
```

## Testing Approach

1. Unit tests first: `python3 -c "from kag_patterns.xxx import ..."` — verify each module standalone
2. Integration on live API: 3-5 queries after each integration point
3. Full battery: 20 questions multi-level + 10 CLI simulation
4. Stress test: 100 questions, monitor DBs every 20 queries

## Pitfalls

- **stdout buffering**: Python print() is block-buffered in background processes. Use `execute_code` or `python3 -u` for scripts that produce real-time output.
- **Column name extraction**: `rows[0].__class__.__dict__.get('_mapping', {}).items()` is fragile. When querying SQLite directly in plan execution, consider using `row_factory = sqlite3.Row` or hardcoding expected columns.
- **Multi-hop thresholds**: Current detector requires >=2 pattern matches OR complexity >=3. Conservative by design to avoid false positives. For legal domain, consider adding domain-specific patterns.
- **imgur blocking**: imgur.com blocks automated access. For user-shared screenshots, ask user to describe the content or use a different image host.

## Relationship to GraphRAG and KAG

This is NOT GraphRAG (Microsoft). GraphRAG uses community detection + LLM summarization.
This is KG-Enhanced RAG inspired by KAG (OpenSPG): schema-constrained knowledge graph +
logical planning + mutual indexing. More precise for factual legal queries, cheaper to run
(no batch pre-processing).

## Test Results (2026-05-06)

- Unit tests: 10/10
- 20-question battery: 20/20 (100%)
- CLI simulation: 10/10
- 100-question battery: 100/100 responded, 0 errors
- Confidence avg: 0.62 (low because target norms not in DB)
- DB health: no degradation after 100 queries
