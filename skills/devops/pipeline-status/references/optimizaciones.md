# Optimizaciones aplicadas — 02-may-2026

## 1. Neo4j Graph Traversal (activación)

**Archivo**: `api_rest.py:1540-1580`, `src/core/query_classifier.py:170-210`

**Antes**: `use_graph_traversal: False` en tipos B, D, E. Solo F y G lo tenían. Resultado: 0% activación.

**Fix**: Cambiar a `True` en tipos B (Semántica), D (Emisor+Acción), E (Acrónimo). Resultado: 78% activación.

**Bugs corregidos**:
- `seen_ids` no definido → inicializar `seen_ids = set()`
- `top_ids` no definido si `unique_results` vacío → inicializar `top_ids = []`
- Indentación rota (20 espacios en vez de 16) en `neo = get_neo4j()`

## 2. System Prompt Anti-derrotista

**Archivo**: `api_rest.py:1357-1363`, `src/orchestrators/orchestrator_rag_v3.py:816-833`

**Antes**: "Si no hay normas relevantes, dilo honestamente" → LLM respondía "no se encontró información" y paraba.

**Fix**: Reemplazar con "SIEMPRE intenta responder con la información disponible" + lista de 10 frases PROHIBIDAS + fórmulas constructivas ("Según los datos disponibles...").

**Resultado**: 13 → 4 frases prohibidas en test de 100 queries.

## 3. Floor de Confianza 0.75 → 0.60

**Archivo**: `api_rest.py:607`

**Antes**: `weighted = 0.75` como floor mínimo cuando hay solapamiento léxico.

**Fix**: `0.75 → 0.60`. Resultado: 5/6 FP adversariales corregidos.

## 4. Filtro Temporal Año+Mes

**Archivo**: `api_rest.py:814-838`

**Fix**: Detectar año (`\b20\d{2}\b`) y mes (enero→01, etc.) en la pregunta. Insertar `AND n.fecha_publicacion LIKE 'YYYY-MM%'` en la query FTS5.

**Resultado**: "normas 2010" → 0.60→0.10 (FP eliminado). "normas setiembre 2024" → 18,104→1,193 resultados (15x más preciso).

**Pitfall**: `_strategy` es un string, no un dict. No usar `_strategy.get()`. Detectar año directamente con regex.

## 5. Neo4j Limpieza de Entidades

32,675 → 16,077 entidades (-51%). Eliminados verbos genéricos ("Aprueban", "Autorizan"), nombres cortos (<5 chars), y entidades con 1 sola mención.

## 6. SQLite Índices

```sql
CREATE INDEX idx_normas_id ON normas(id);
CREATE INDEX idx_normas_numero ON normas(numero);
CREATE INDEX idx_normas_fecha ON normas(fecha_publicacion);
CREATE INDEX idx_normas_tipo ON normas(tipo_norma);
```
