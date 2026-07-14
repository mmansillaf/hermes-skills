# KAG Patterns Implementation — KG-Enhanced RAG

Implementation date: 2026-05-06
Source modules: `src/kag_patterns/` (560 lines)
Patches to: `api_rest.py` (+72 lines, 6 points)

## Architecture

Three independent phases, each toggleable via environment flag:

| Phase | Flag | Module | What it does |
|-------|------|--------|-------------|
| A | KAG_MUTUAL_INDEX | mutual_index.py | Links Neo4j entities to exact text offsets |
| B | KAG_SCHEMA | ontologia_legal.py | 7 entity types + 10 semantic relations |
| C | KAG_PLANNING | query_planner.py | Multi-hop detection + step decomposition |

Default: all ON. Disable with `KAG_PLANNING=0`, etc.

## Phase A: Mutual Indexing

`find_in_text(texto, entidad)` — Returns {offset_start, offset_end, contexto, encontrada} or None.
- Searches entity name in full text (case-insensitive)
- Falls back to first-name match for compound entities
- Returns surrounding context (±120 chars)

`enrich_with_citations(results, db_getter)` — Adds `_citas` field to results.
- For each result with entities, looks up texto_completo from SQLite
- Finds each entity position, extracts citation snippet
- Marks exact vs partial matches

Integration point in api_rest.py: after expand_graph(), before confidence:
```python
if KAG_MUTUAL_INDEX:
    from kag_patterns.mutual_index import enrich_with_citations
    unique_results = enrich_with_citations(unique_results, get_sqlite)
```

_build_context() already handles _citas display.

## Phase B: Schema-Constrained Extraction

`ENTITY_TYPES`: Persona, Organismo, NormaLegal, Monto, Lugar, Articulo, FechaEvento

`SEMANTIC_RELATIONS`: DESIGNA, CESA, AUTORIZA_VIAJE, APRUEBA, MODIFICA, DEROGA, TRANSFIERE, SANCIONA, DECLARA_EMERGENCIA, REGULADA_POR

Each relation has: sujeto type, objeto type, propiedades, palabras_clave (for detection)

`infer_role_from_sumilla(sumilla, position)` → "designado"|"cesado"|"viajero"|"firmante"|None
- Position 0 = firmante (signer)
- Position 1+ = subject role based on sumilla keywords

`classify_entity(entity_name)` → ("Persona"|"Organismo", siglas)
- Handles ALL-CAPS names (Neo4j storage format) vs Title Case
- Distinguishes short acronyms (MINSA) from person names (PEDRO LOPEZ MARTINEZ)

Integration: replaces inline role inference in `_enrich_entities()` with ontologia_legal version, fallback to original if import fails.

## Phase C: Planning Operator

`is_multi_hop(question)` → bool
- Tests 6 regex patterns, requires ≥2 matches OR complexity ≥3
- Conservative by design: avoids false positives on simple queries

`decompose(question)` → list[Step] or None
- Step 1: SQL query (tipo_norma + emisor + fecha filters)
- Step 2: FTS5/keyword filter (topic extraction)
- Step 3: Action verification (modifica/deroga/designa keywords)

Each Step: {step, description, store, query_sql, params, filter_keywords, field, expected}

Integration in api_rest.py: after classifier, before cache check. If steps exist, executes step 1 SQL directly on sqlite, then filters results through steps 2+ using keyword matching. Plan results prepended to unique_results.

Helper extractors: `_extract_tipo_norma()`, `_extract_emisor()`, `_extract_temporal()`, `_extract_accion()`, `_extract_tema()`

## Test Results (2026-05-06)

- Unit tests: 10/10 PASS
- 100-question battery: 100/100 queries executed (0 errors)
  - OK: ~85 (85%), WARN: ~15 (15%)
  - Avg confidence: 0.62, Avg time: 2515ms
  - Multi-hop detected: 1/100 (query 16: "RM MINSA modificaron medicamentos")
  - Web fallback: 29%, Cache hits: 20%

## Key Design Decisions

1. **NOT GraphRAG**: Microsoft GraphRAG uses community detection + LLM summarization. Our approach is KG-Enhanced RAG with formal ontology. Better for factual legal queries. Zero additional cost.

2. **Conservative multi-hop**: Requiring ≥2 pattern matches prevents false positives on queries that only happen to contain "modifica" or a year.

3. **Plan fallback**: If plan execution fails (SQL error, 0 results), the pipeline falls through to normal search_sqlite + Qdrant + Neo4j.

4. **Zero new dependencies**: Everything uses stdlib + existing stores. No pip install needed.

## Files

```
src/kag_patterns/
├── __init__.py          (3 lines)
├── mutual_index.py      (80 lines, Phase A)
├── ontologia_legal.py   (200 lines, Phase B)
└── query_planner.py     (280 lines, Phase C)
```
