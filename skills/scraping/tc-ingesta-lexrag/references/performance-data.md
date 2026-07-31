# Performance Data — TC Ingesta LexRAG

## Benchmarks Reales (T470p, WSL Ubuntu, Jun 2026)

### Hardware
- CPU: Intel i7-7820HQ
- RAM: 16 GB
- GPU: None (CPU-only)
- Storage: SSD NVMe (WSL en D:)

### Carga de Índices (1ra vez, desde frio)

| Componente | Tiempo | % | Tamaño en disco |
|-----------|:------:|:-:|:---------------:|
| Carga BM25 (pickle) | ~9s | 40% | 175 MB |
| Carga modelo embeddings | ~2s | 9% | ~500 MB (RAM) |
| Carga FAISS | ~0.1s | <1% | 129 MB |
| Carga grafo | ~0.2s | 1% | 46 MB |
| Carga metadata JSON | ~0.3s | 1% | 11 MB |
| **Total carga inicial** | **~11-22s** | — | — |

La variacion (11-22s) depende de si el modelo de embeddings esta cacheados en RAM.

### Búsqueda Híbrida (FAISS + BM25 + RRF)

| Fase | Tiempo |
|------|:------:|
| Embedding de query | ~0.5s |
| FAISS search (top-21, 65K vectores) | ~2ms |
| BM25 search (65K chunks) | ~65-112ms |
| RRF fusion + ensamble contexto | ~0.3s |
| **Total busqueda** | **0.8-3.2s** |

### LLM Groq (síntesis)

| Modelo | Tiempo promedio | Notas |
|--------|:--------------:|-------|
| llama-3.3-70b-versatile | 1.7-2.5s | Varia segun cola de Groq |
| llama-3.1-8b-instant | ~0.5s | Solo router |

### Pipeline de Ingesta

#### Extraccion de texto (PyMuPDF, 8 workers)

| Lote | PDFs | Tiempo | Velocidad |
|------|:----:|:------:|:---------:|
| 2024-2026 (recientes) | 5,000 | ~17 min | ~5 PDFs/s |
| 2018-2023 (antiguos) | 1,436 | ~4.5 min | ~5.3 PDFs/s |

Los PDFs mas antiguos (2018-2019) son ligeramente mas lentos porque son archivos mas grandes (escaneos).

#### Groq Batch API

| Modelo | Docs | Tiempo | Throughput |
|--------|:----:|:------:|:----------:|
| 8B (cortos) | 255 | ~5 min | ~51 docs/min |
| 70B (largos) | 4,500 | ~1h45min | ~43 docs/min |
| 70B (largos) | 1,348 | ~30 min | ~45 docs/min |

El 70B tiene una cola de espera inicial de ~10-15 min antes de empezar a procesar.

#### Indexacion (embeddings + FAISS + BM25 + grafo)

| Documentos | Tiempo | Velocidad |
|:----------:|:------:|:---------:|
| 4,944 TC | ~9 min | ~10.5 docs/s |
| 1,397 TC | ~2 min | ~10.9 docs/s |

### Costos Reales (Groq API)

| Lote | PDFs | Docs OK | Costo |
|:----:|:----:|:-------:|:-----:|
| 2024-2026 (5K batch) | 5,000 | 4,944 | ~$8.90 |
| 2018-2023 (1.4K batch) | 1,436 | 1,397 | ~$6.77 |
| **Total** | **~6,800** | **6,341** | **~$15.67** |

### Tiempos de Respuesta (consulta.py, indices en memoria)

| Consulta | Busqueda | Sintesis LLM | Total |
|----------|:--------:|:------------:|:-----:|
| Amparo contra resoluciones judiciales | 2.3s | 2.1s | 4.4s |
| Despido arbitrario | 0.9s | 2.2s | 3.1s |
| Control difuso | 0.8s | 2.3s | 3.1s |
| Derecho a pension | 0.9s | 1.7s | 2.6s |
| Habeas corpus | 1.0s | 1.7s | 2.7s |

### Documentos en el Sistema (post-ingesta)

| Fuente | Cantidad |
|--------|:--------:|
| Originales (HTML) | 59,571 |
| TC SEDETC (PDF) | 6,354 |
| **Total** | **65,925** |
| Grafo nodos | 213,426 |
| Grafo aristas | 481,943 |
