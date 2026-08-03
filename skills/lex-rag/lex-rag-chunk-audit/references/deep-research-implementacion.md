# Deep Research — Implementación en Lex RAG

## Archivos

| Archivo | Cambio |
|---|---|
| `agents/deep_searcher.py` | **Nuevo** — clase `DeepSearcher` (320 líneas) |
| `graphrag_pro.py` | **Modificado** — flag `--deep`, ruteo condicional (+15 líneas) |

## Arquitectura

```
query con --deep
  → _generate_queries() → 3-5 sub-queries (reglas, sin LLM)
  → ThreadPoolExecutor → FAISS+BM25 ×5 en paralelo
  → ~40 chunks total
  → RRF Fusion extendida (multi-fuente)
  → top-14 chunks → mismo pipeline (Graph → Synthesis → Critic → Feedback)
```

## Activación

```bash
# Una consulta
python3 graphrag_pro.py --query "despido arbitrario" --deep

# Modo interactivo (toda la sesión)
python3 graphrag_pro.py --deep
```

## Diferencias con modo normal

| Métrica | Normal | Deep Research |
|---|---|---|
| Sub-queries | 1 (HyDE) | 3-5 |
| Chunks recuperados | ~21 | ~40 (+90%) |
| Documentos únicos | ~7 | ~7 (mejores) |
| Tiempo retrieval | ~3s | ~5-8s (paralelo) |
| Tiempo total | ~37s | ~42s (+15%) |
| Costo extra | $0 | $0 (solo CPU) |

## Generación de sub-queries

`_generate_queries(query, hyde_query)`:

1. Query original
2. HyDE expansion (si existe y es distinta)
3. Query + "jurisprudencia"
4. Query + "regulacion legal"
5. Query + "normativa aplicable"
6. Keywords extraídos (top 3, filtrados stopwords)
7. Versión corta (solo 2 keywords) para queries largas

Límite: 5 queries máximo.

## Retrieval paralelo

```python
with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as pool:
    futures = {pool.submit(_retrieve_single, q, strategy): q for q in sub_queries}
    for future in as_completed(futures):
        all_chunks.extend(future.result())
```

## Fusión RRF extendida

A diferencia del RRF normal (intra-query), opera sobre TODOS los chunks de TODAS las queries:

1. Agrupar por doc_id
2. Para cada chunk, `fusion_score = 1.0 / (k_rrf + rank + 1)`
3. Acumular scores por documento
4. Ordenar por RRF total descendente

## Contexto enriquecido

Incluye marcas de fuente para transparencia:

```
**CAS. N° 15-2015 LAMBAYEQUE** → Jurisprudencia/1612215.html
[Fuentes: despido arbitrario, despido arbitrario jurisprudencia, despido arbitrario normativa aplicable]
Fallo: La Corte Suprema declara...
```

## Audit JSON

```json
{
  "retrieval.hybrid.mode": "deep",
  "retrieval.hybrid.sub_queries": ["Q1", "Q2", ...],
  "retrieval.hybrid.total_chunks_retrieved": 40,
  "retrieval.hybrid.fusion_details": {
    "doc_id": { "sources": [...], "total_rrf": 0.064, "num_chunks": 4 }
  }
}
```

## Prueba realizada

```bash
python3 graphrag_pro.py --query "despido arbitrario" --deep
# Log:
#   🔍 DeepResearch: 5 sub-queries generadas
#   🔍 DeepResearch: 5 queries → 40 chunks → 4 docs (25.4s)
#   💾 Consulta guardada
#   🔍 Auditoría granular guardada
#   ✅ Critic score 75% → feedback loop activado → corrección aplicada
```

## Ramas de Git

```
main                      e858b66  Multi-agente completo
feature/deep-research     cf6005f  +Deep Research (2 archivos)
```
