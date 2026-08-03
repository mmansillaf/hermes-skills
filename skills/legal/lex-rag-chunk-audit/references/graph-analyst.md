# Graph Analyst Agent — Implementación

**Archivo:** `agents/graph_analyst.py` (326 líneas)
**Creado:** 2026-05-20

## Estructura del grafo

- 191,871 nodos: Documento (59,571), Ley (49,312), Demandado (37,613), Actor (35,738), Juez (9,637)
- 419,504 aristas: JUZGADO_POR (167K), CITA_LEY (144K), DEMANDA_A (59K), DEMANDADO_POR (50K)
- Atributos de nodo: `tipo`, `fallo` (solo Documento), `nombre` (entidades)

## Arquitectura

```
analyze(doc_ids, query)
  ├── _load() → lazy: pickle ~/data/indices/graph_juris_pro.pkl
  ├── ThreadPoolExecutor(max_workers=2)
  │   ├── _collect_entities()  → por cada doc, jueces/leyes/actores/demandados
  │   └── _compute_global_stats() → docs totales compartiendo entidades
  ├── _compute_local_stats()   → Counter de frecuencias en docs recuperados
  ├── _find_chains()           → docs que comparten leyes = precedentes
  └── _format()                → texto narrativo + audit JSON
```

## API

```python
analyst = GraphAnalyst()
narrative, audit = analyst.analyze(doc_ids, query)
# Compatible con get_graph_context() - mismo contrato (text, dict)
```

## Paralelización

`_collect_entities` y `_compute_global_stats` corren en paralelo. Son independientes: una trabaja sobre los doc_ids, la otra sobre el grafo completo.

## Audit JSON

```json
{
  "top_jueces": [["Juez: Arévalo Vela", 3], ...],
  "top_leyes": [["Ley: Código Civil", 5], ...],
  "top_actores": [...],
  "top_demandados": [...],
  "chains_encontradas": 5,
  "total_entities_per_doc": {"1308950.html": {"jueces": 2, "leyes": 4}}
}
```

## Cache

- `self._G = None` → lazy load en primera llamada
- `self._G = False` si falla carga (cache negativo)
- ~100MB en memoria
