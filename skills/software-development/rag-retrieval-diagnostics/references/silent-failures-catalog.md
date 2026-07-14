# Catálogo de Fallos Silenciosos — El Peruano RAG

Fallos que NO producen errores visibles (health check OK, sin excepciones, API responde) pero degradan el sistema.

## 1. `db` no inicializado → Capa 4 muerta
- **Síntoma:** db_ratio=0.0 en todas las queries
- **Causa:** `confidence_score()` usa `db.execute(...)` pero `db` nunca se inicializa
- **Silenciado por:** `except: pass`
- **Fix:** `db = get_sqlite()` antes del loop
- **Fecha:** 01-may-2026

## 2. Qdrant source perdido en merge → semantic_quality=0
- **Síntoma:** qdrant_scores=[] siempre, health OK
- **Causa:** Dedup por numero mantiene source="sqlite", Qdrant nunca matchea
- **Fix:** Flag `_qdrant_contributed` + usar `_qdrant_score` en confidence_score
- **Fecha:** 01-may-2026

## 3. Neo4j entity filter excluye acrónimos
- **Síntoma:** neo4j.count=0 en 95% queries, health OK
- **Causa:** `len(t) > 4` excluye MTC(3), ONPE(4), UIT(3), CAP(3)
- **Fix:** `len(t) >= 3`, top 5→8 tokens
- **Fecha:** 01-may-2026 (el fix de terms→_q_tokens de 27-abr SÍ seguía en pie)

## 4. Post-hoc negation bypass en conf=0.75
- **Síntoma:** Respuestas "no se encontró" con conf=0.75 (falso positivo)
- **Causa:** `confidence < 0.75` (estricto) no captura conf=0.75 exacto
- **Fix:** `<= 0.75` + starts-negation check (primeros 80 chars)
- **Fecha:** 01-may-2026

## 5. Health checks no verifican funcionalidad
- **SQLite health:** `SELECT COUNT(*)` → OK siempre
- **Qdrant health:** ping HTTP → no verifica source tags
- **Neo4j health:** `MATCH (n) RETURN count(n)` → no verifica entity_terms
- **Regla:** NUNCA confiar en health checks. Siempre trazar 1 query.

## 6. `except: pass` silencia bugs críticos
- Capa 4 muerta por 4+ semanas (NameError silenciado)
- `_has_zero_match` nunca se poblaba
- **Regla:** Siempre `logger.warning()` en bloques except

## 7. debug_conf nunca poblado
- **Síntoma:** debug_internal={} en todas las respuestas
- **Causa:** debug_conf se crea como {} pero nunca se asignan valores
- **Fix:** Poblar con base_weighted, fp_penalty, weighted_pre_floor, ratio, db_ratio, semantic_quality, sqlite_quality, qdrant_contrib
- **Fecha:** 01-may-2026

## 8. FTS5 snippet() índice de columna incorrecto
- **Síntoma:** Snippet muestra path del archivo en vez de texto
- **Causa:** `snippet(fts_table, 0, ...)` usa columna 0 (path)
- **Fix:** `snippet(fts_table, 2, ...)` para columna de texto
- **Fecha:** 01-may-2026
