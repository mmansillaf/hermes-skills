# TC SearchRAG — Benchmarks y Datos de Rendimiento

## Indexación
1,511 PDFs (2005, escaneados): 8.3 min
11,483 PDFs total (force): 2h 25min (WSL /mnt/d/ overhead)
Embedding individual: 0.736s | Batch 50: 0.555s (50x mas rapido)

## Carga de índices (cold start)
| Índice | Disco | Tiempo carga | % acum |
|--------|:-----:|:------------:|:------:|
| bm25_index.pkl | 265 MB | 9.29s | 84% |
| documents.pkl | 161 MB | 1.65s | 99% |
| metadata.jsonl | 7.8 MB | 0.29s | 99.9% |
| faiss_index.bin | 22 MB | 0.12s | 100% |
| **Total** | **457 MB** | **11.06s** | 100% |

BM25 es por mucho el cuello de botella (84%). Los índices se cargan cada vez que se ejecuta un script.

## Búsqueda
FAISS FlatL2 search (top-100): **1.77ms** (500 iteraciones)
FAISS + BM25 + RRF: **~1.5-1.8s** (incluye encoding de query)
Filtros metadata (sin texto): **5-12ms**
Modelo: `distiluse-base-multilingual-cased-v2`, dim=512, cpu

## Bateria 10 Consultas (DeepSeek)
10 preguntas variadas: 84s total, 8.4s promedio
Rango: 7.7s - 9.5s por consulta

## Tiempos LLM (Groq-only desde Jun 2026)
Groq llama-3.3-70b: **25-32s** (~$0.0043/query)
Groq llama-3.1-8b (router): **~1-2s** (~$0.0001/query)
DeepSeek V4 Flash: **12-13s** (~$0.0016/query) — *retirado, solo referencia histórica*

## Optimizaciones proyectadas
| Optimización | Ahorro por consulta |
|-------------|:-------------------:|
| Servidor persistente (app.py) | ~11s (carga índices) |
| Caché exacto (hash MD5) | ~13-32s (consulta repetida) |
| Caché semántico (coseno) | ~1.4s (consulta similar) |
| Saltar BM25 si solo filtros | ~9s |
| FAISS HNSW | ~1.71ms |

Ver `references/optimization-plan.md` para plan detallado.

## Costos (Groq-only desde Jun 2026)
Indexacion: $0 (CPU local)
Groq clasificacion (router): ~$0.0001/query
Groq 70b (sintesis): ~$0.0043/query
Groq 8b (router, 10,965 llamadas): ~$0.16 total
100 q/dia (Groq): ~$13.20/mes
