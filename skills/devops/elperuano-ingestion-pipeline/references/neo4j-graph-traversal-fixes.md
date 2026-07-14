# Neo4j Entity Cleanup & Graph Traversal Activation

## Entity Quality Problem

Neo4j had 32,675 entity nodes extracted from norm titles. Top entities were all generic:
- "Aprueban" (10,720 menciones), "Autorizan" (8,544), "Designacion" (6,306)
- 15,487 entities had only 1 mention (pure noise)

This made graph traversal return irrelevant results - normas sharing "Aprueban" as entity, not meaningful connections.

## Cleanup Commands (Neo4j Cypher)

```cypher
// 1. Delete generic verb/noun entities
MATCH (e:Entidad) WHERE e.nombre IN [
  'Aprueban','Autorizan','Designacion','Nombramiento','Ministerio',
  'Peru','Viajes','Republica','Reglamento','Estado','Designan',
  'Modifican','Justicia','Declaran','Prorrogan','Aprueba','Creacion',
  'Gobierno','Nacional','Crean','Salud','Educacion','LEY','Sistema'
] DETACH DELETE e;

// 2. Delete entities with short names
MATCH (e:Entidad) WHERE size(e.nombre) < 5 DETACH DELETE e;

// 3. Delete single-mention noise
MATCH (:Norma)-[r:MENCIONA]->(e:Entidad)
WITH e, count(r) as cnt WHERE cnt <= 1 DETACH DELETE e;
```

Results: 32,675 -> 16,077 entities (51% reduction), 436,989 -> 336,041 relations (23% reduction)

## Graph Traversal Bug Fixes

Three bugs fixed in `api_rest.py`:

**Bug 1: `seen_ids` not defined** (line 1564)
```python
# ADD before try block:
seen_ids = set()  # track IDs to avoid duplicates
```

**Bug 2: `top_ids` not defined if unique_results empty** (line 1545)
```python
# ADD before if block:
top_ids = []
```

**Bug 3: Broken indentation** (line 1551)
```python
# FIXED: neo = get_neo4j() was indented 20 spaces, should be 16
```

## Strategy Expansion

Enabled `use_graph_traversal: True` for types B (Semantica), D (Emisor+Accion), E (Acronimo) in `src/core/query_classifier.py`. Previously only F (Narrativa) and G (Modificaciones) had it.

Result: graph traversal active in 78% of queries (was 0%).
