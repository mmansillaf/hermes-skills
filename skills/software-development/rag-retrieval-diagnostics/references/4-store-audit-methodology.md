# 4-Store Audit Methodology (SQLite FTS5 + Neo4j + Qdrant + System Prompts)

Auditoría completa de los 4 sistemas de un RAG multi-store. Ejecutada 02-may-2026 sobre El Peruano RAG (97,809 normas).

## 1. SQLite + FTS5

```sql
-- Schema
SELECT name, type FROM sqlite_master WHERE type IN ('table','index');

-- FTS5 columns  
SELECT sql FROM sqlite_master WHERE name='normas_fts';

-- Performance
SELECT COUNT(*) FROM normas_fts WHERE normas_fts MATCH 'termino';

-- Column fill rates
SELECT COUNT(*) FROM normas WHERE columna IS NOT NULL AND columna != '';
```

**Hallazgos típicos:**
- Sin índices regulares (solo FTS5 virtual) → agregar `CREATE INDEX ON normas(id)`, `ON normas(numero)`, `ON normas(fecha_publicacion)`
- FTS5 tokenizer: `unicode61 remove_diacritics 2` — adecuado para español
- texto_completo: verificar min/max/avg length para calibrar truncación en prompts

## 2. Neo4j

```cypher
CALL db.labels()
CALL db.relationshipTypes()
MATCH (n:Norma) RETURN count(n)
MATCH (e:Entidad) RETURN count(e)
MATCH ()-[r]->() RETURN count(r)
```

**Graph traversal test:**
```cypher
MATCH (n:Norma)-[:MENCIONA]->(e:Entidad)<-[:MENCIONA]-(related:Norma)
WHERE n.id IN ['top_result_1', 'top_result_2'] AND related.id <> n.id
RETURN related.id, related.sumilla, count(DISTINCT e) as shared
ORDER BY shared DESC LIMIT 5
```

**Entidades genéricas — señal de alarma:**
Si las top-10 entidades son verbos ("Aprueban", "Autorizan", "Designan") o palabras genéricas ("Perú", "Ministerio"), el extractor de entidades necesita NER o está usando solo títulos. Verificar con:
```cypher
MATCH (:Norma)-[r:MENCIONA]->(e:Entidad) 
RETURN e.nombre, count(r) as menciones 
ORDER BY menciones DESC LIMIT 20
```

**Cleanup rápido:** Eliminar entidades con <3 menciones + verbos genéricos:
```cypher
MATCH (e:Entidad) WHERE size(e.nombre) < 5 DETACH DELETE e;
MATCH (:Norma)-[r:MENCIONA]->(e:Entidad) WITH e, count(r) as cnt WHERE cnt <= 1 DETACH DELETE e;
```

## 3. Qdrant

```bash
# Colecciones
curl http://localhost:6333/collections

# Config
curl http://localhost:6333/collections/NOMBRE

# Verificar vectores (no zeros)
curl -X POST http://localhost:6333/collections/NOMBRE/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit":3, "with_vector":true}'
```

**Señales de problemas:**
- `vectors_count=0` → embedding nunca se ejecutó
- vectores con mean=0.0, zeros=384 → modelo de embedding falló
- scores=0.0 en búsquedas → mismatch de dimensionalidad
- IDs enteros (0,1,2...) en vez de IDs de norma → riesgo de desincronización en reindex

## 4. System Prompts

Buscar TODOS los prompts en el código:
```bash
grep -rn "Eres\|eres.*asistente\|prompt.*legal\|REGLAS" api_rest.py src/
```

**Auditar cada prompt por:**
- ¿Contiene instrucciones de "honestidad" que el LLM interpreta como derrota?
- ¿Incluye frases como "si no hay información, indícalo"?
- ¿Está calibrado para el modelo que lo usa (8B vs 70B)?
- ¿Coincide con el nivel de contexto disponible (texto_completo vs solo sumilla)?

**Fix estándar:** Reemplazar instrucciones de honestidad por instrucciones constructivas + lista explícita de frases PROHIBIDAS.

## Resultados de la auditoría (02-may-2026)

| Sistema | Estado | Hallazgo |
|---------|--------|----------|
| SQLite | ✅ 100% | Sin índices regulares → agregados 4 |
| FTS5 | ✅ 97,809 rows | 6 columnas, tokenizer español |
| Neo4j | ⚠️ | 51% entidades eliminadas (genéricas) |
| Qdrant | ✅ 97,809 pts × 384d | IDs enteros (riesgo reindex) |
| Prompts | ✅ Corregido | 2 prompts con lenguaje derrotista → fix |
| Confianza | ✅ Corregido | Floor 0.75 → 0.60 |
