# LexRAG Corpus Audit — Jun 2026

Measured from `/mnt/d/PyCode/LexRAG-Optimizado/data/` (the optimized copy).

## Index Dimensions

| Index | Type | Entries | Size on Disk | Details |
|-------|------|---------|-------------|---------|
| FAISS | IndexFlatL2 | 59,571 vectors | 117 MB | dim=512, FlatL2 (not IVF/HNSW) |
| FAISS meta | pickle[dict] | 59,571 | 54 MB | keys: `doc_id`, `text` |
| BM25 | BM25Okapi | 59,571 chunks | 155 MB | 3 keys: bm25, meta[], corpus[] |
| NetworkX Graph | nx.Graph | 191,871 nodes / 419,504 edges | 40 MB | pickle |
| Metadata | JSON dict | 64,186 docs | ~10 MB | 449K lines in metadata_docs.json |
| Graph stats | JSON | precomputed | 8.8 KB | top 30 jueces, top 20 leyes/actores |
| Entities | JSON | per-doc entities | 20 MB | doc_entities.json |

## Graph Node Types

| Type | Count |
|------|-------|
| Documento | 59,571 |
| Ley | 49,312 |
| Demandado | 37,613 |
| Actor | 35,738 |
| Juez | 9,637 |

## Corpus Distribution by Organo

| Organo | Count |
|--------|-------|
| (sin órgano) | 18,919 |
| Corte Suprema | 13,886 |
| Tribunal Constitucional | 12,819 |
| Corte Suprema - Sala Civil | 4,741 |
| Corte Suprema - Sala Constitucional | 4,268 |
| Corte Superior | 3,481 |
| Tribunal Fiscal | 2,701 |
| Poder Judicial | 2,199 |
| Tribunal | 954 |
| Corte Suprema - Sala Laboral | 218 |

## Corpus by Document Type

| Tipo | Count |
|------|-------|
| Documento | 40,515 |
| Expediente | 10,234 |
| Casacion | 7,879 |
| Sentencia TC | 2,554 |
| Resolucion | 1,584 |
| Resolucion TF | 1,420 |

Total: 64,186 documents in metadata (59,571 have both FAISS + BM25 indexing)

## Performance Benchmarks

### Index load times (cold start, first call)
- FAISS index (116 MB): 0.645s
- FAISS meta (53 MB): 0.838s
- BM25 (154 MB): 3.963s
- Graph (40 MB): 1.183s
- Entities (20 MB): 0.472s
- **Total: 7.101s, 1,193 MB RAM**

### Search times
- FAISS FlatL2 search (60K vectors): 7.71ms avg
- BM25 search (2-5 token query): 65-112ms

### Battery 10 queries (Jun 9, 2026)
- Total: 178s
- Average: 17.8s/query
- Range: 11.5s — 27.4s
- Citations (FUENTE:): **0 across all 10 queries** — see SKILL.md for fix
- Cache: 0 hits (cold start, all different queries)

## Missing Modules (Optimized Copy Trap)

The `LexRAG-Optimizado` project at `/mnt/d/PyCode/LexRAG-Optimizado/` is missing:

| Required import | Missing file | Purpose |
|----------------|-------------|---------|
| `from retrieval.hybrid_search import get_hybrid_context` | `retrieval/hybrid_search.py` | FAISS+BM25+RRF |
| `from utils.query_cache import query_cache` | `utils/query_cache.py` | Exact MD5 cache |
| `from utils.semantic_cache import semantic_cache` | `utils/semantic_cache.py` | Semantic vector cache |
| `from utils.metrics import metrics` | `utils/metrics.py` | Phase timing metrics |

The `retrieval/` directory exists but is **empty**. The `utils/` directory does not exist
at all. Original source project was `/mnt/d/PyCode/ResumenTokensJurisprudencias/`
(which also doesn't exist on this machine — may need to check backup or git).
