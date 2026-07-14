# Query Classifier + Selective Routing for Multi-Store RAG

## When to use

You have a RAG system with multiple data stores (SQLite, Qdrant/vector, Neo4j/graph) and all queries hit ALL stores regardless of type. This causes:
- Unnecessary latency (1.4s→1.7s per extra store)
- Noise from irrelevant stores polluting results
- Count/aggregation queries failing because text search can't count

## Pattern

### 1. Query Classifier (taxonomy of 7+1 types)

```python
def classify_query(question: str) -> dict:
    """Returns query_type 'A'-'H', strategy dict with store flags."""
    # A: ID Exacto — "Ley 32108", "DS 005-2024"
    # B: Semantica — conceptos legales sin ID
    # C: Temporal — meses, años, "cuantas", "promedio"
    # D: Emisor+Accion — "designaciones MINSA"
    # E: Acronimo — "OSCE", "SUNAT" sin expansion
    # F: Narrativa — queries largas (>10 palabras)
    # G: Modificaciones — "modifica", "deroga"
    # H: Adversarial — IDs falsos, temas inexistentes, jailbreaks
```

### 2. Strategy per type (store selectivity)

```python
STRATEGIES = {
    'A': {'stores': {'sqlite': 1.0}, 'use_qdrant': False, 'use_neo4j': False},
    'B': {'stores': {'qdrant': 0.7, 'sqlite': 0.3}, 'use_qdrant': True, 'use_neo4j': True},
    'C': {'stores': {'sqlite': 0.5, 'qdrant': 0.5}, 'use_neo4j': False},
    'G': {'stores': {'neo4j': 1.0}, 'use_qdrant': False},
    'H': {'stores': {'web': 1.0}, 'use_qdrant': False, 'use_neo4j': False},
    # ... etc
}
```

### 3. Apply flags in retrieval pipeline

```python
_strategy = classification.get('strategy', {})

# Qdrant conditional
if _strategy and not _strategy.get('use_qdrant', True):
    sources["qdrant"] = {"count": 0, "method": "disabled_by_strategy"}
else:
    # ... normal Qdrant search ...

# Neo4j conditional  
if _strategy and not _strategy.get('use_neo4j', True):
    sources["neo4j"] = {"count": 0, "method": "disabled_by_strategy"}
else:
    # ... normal Neo4j search ...
```

## Pitfalls

- **Indentation breaks**: When wrapping existing try/except blocks with if/else, the inner code needs +4 spaces. Use a Python script to fix indentation programmatically — manual patching of nested try/except is error-prone.
- **Neo4j entity vs graph traversal**: These are separate flags. Entity search (MENCIONA relations) should be controlled separately from 2-degree graph traversal.
- **SQLite is always needed**: Even for type H, SQLite provides context for the LLM. Only skip vector stores, not the text store.
- **Adversarial override**: When classifier detects type H, force confidence ≤ 0.15 regardless of what the retrieval returns. Real terms in adversarial queries (e.g., "presupuesto" in "ministerio de magia") can match real data and inflate confidence.
- **Conjugations in ACCIONES_LEGALES**: Include past tense forms (`modificaron`, `modificaban`, `derogaron`, `derogaba`) not just the infinitive/present. Queries like "que normas modificaron el regimen laboral" will be classified as G (MODIFICACIONES) instead of falling through to C (TEMPORAL).
- **MODIFICACION_PATTERNS must mirror ACCIONES_LEGALES**: The pattern `r'\b(?:normas?\s+modificaron|modificaron\s+(?:el|la|las|los))\b'` catches queries where "modificaron" appears as a standalone verb, not just in the regex group.
- **Emisor name mapping**: Add a dictionary `EMISOR_NAME_MAP` that maps full entity names to acronyms (e.g., "ministerio de salud" → "MINSA"). This lets the classifier detect emitters even when users write full names. Check names in the DB first — some entities appear as acronyms in the emisor column (e.g., "MINSA") while others appear as full names (e.g., "Ministerio de Salud").

## Measured impact

- Qdrant usage: 100% → 47% (-53%)
- Neo4j graph: 100% → 17% (-83%)
- Type A latency: 70ms → 32ms (only SQLite)
- Adversarial precision: 80% → 100% (0 false positives)