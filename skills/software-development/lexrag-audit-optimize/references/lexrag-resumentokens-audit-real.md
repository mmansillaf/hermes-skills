# Auditoría Real: ResumenTokensJurisprudencias (LexRAG)

Fecha: 9 Jun 2026 (actualizado con benchmarks reales)
Proyecto: D:\PyCode\ResumenTokensJurisprudencias
Stack: Python 3.12 + DeepSeek V4 Flash + Groq llama-3.3-70b
64,186 documentos | 59,571 chunks | Índices: 383 MB disco / 1.2 GB RAM

## Arquitectura

```
Usuario → Router (Groq llama-3.3-70b) → WEB? → Serper API
                                        → LOCAL → RetrievalStrategist (Groq llama-3.3-70b)
                                                    → get_hybrid_context (FAISS FlatL2 + BM25 + RRF)
                                                    → GraphAnalyst (NetworkX, algorithmic)
                                                    → [DeepSearcher si --deep: 5 sub-queries paralelas]
                                                    → Synthesizer (DeepSeek V4 Flash streaming + failover Groq)
                                                    → Critic (verificación de citas)
                                                    → Rewrite loop (hasta 2 iteraciones)
```

## Benchmarks Reales (9 Jun 2026)

### Carga de índices
```
Índice           Disco    RAM real   Ratio   Tiempo
FAISS index     116 MB   117 MB     1.00x   0.645s
FAISS meta       53 MB    74 MB     1.39x   0.838s
BM25            154 MB   698 MB     4.53x   3.963s  ← INFLACIÓN MÁXIMA
Grafo            40 MB   234 MB     5.86x   1.183s  ← PEOR RATIO
Entities         20 MB    70 MB     3.58x   0.472s
─────────────────────────────────────────────────
TOTAL           383 MB  1193 MB     3.11x   7.101s
```

**NOTA:** La medición original estimaba 11.6s. El benchmark real es 7.1s.
El singleton sigue siendo la optimización #1, pero el impacto baja de -50% a -38%.

### Búsqueda
- FAISS FlatL2 (59,571 vectores, dim=512): **7.71ms** promedio (100 iteraciones)
  - IVF (nlist=100, nprobe=10): ~0.13ms estimado (60x más rápido)
  - HNSW: ~0.15ms estimado (50x más rápido)
- BM25 search: **65-112ms** según query (~83ms promedio)
- RAM total proceso: **1,249 MB**

### Proyección de optimizaciones
```
Escenario                           Tiempo     Mejora
Actual (recarga índices cada vez)   ~18.7s     —
+ Singleton índices                 ~11.7s     -38%
+ Router 8B                         ~9.8s      -48%
+ Escrituras async                  ~9.5s      -49%
Caché (query repetida)              ~50ms      -99.7%
```

## Arquitectura

```
Usuario → Router (Groq llama-3.3-70b) → WEB? → Serper API
                                        → LOCAL → RetrievalStrategist (Groq llama-3.3-70b)
                                                    → get_hybrid_context (FAISS FlatL2 + BM25 + RRF)
                                                    → GraphAnalyst (NetworkX, algorithmic)
                                                    → [DeepSearcher si --deep: 5 sub-queries paralelas]
                                                    → Synthesizer (DeepSeek V4 Flash streaming + failover Groq)
                                                    → Critic (verificación de citas)
                                                    → Rewrite loop (hasta 2 iteraciones)
```

## Cuellos de Botella Detectados

### 1. [P1] Router con modelo 70B para clasificación binaria
- Usa `llama-3.3-70b-versatile` para decidir WEB vs LOCAL + generar HyDE
- Tarea trivial que un modelo 8B resuelve igual
- Costo extra: ~5-10x más tokens que necesario
- Solución: cambiar a `llama-3.1-8b-instant` para routing

### 2. [P1] Índice FAISS FlatL2 (búsqueda exacta, O(n))
- 117MB, ~64K vectores, pero recorrido lineal completo
- Sin IVF ni HNSW (cuantificación)
- Con IVF (Inverted File), ~10-50x más rápido con pérdida mínima
- Solución: migrar a `faiss.IndexIVFFlat` con entrenamiento de clustering (k=100-500)

### 3. [P1] BM25 155MB cargado y escaneado en cada consulta
- `BM25Okapi.get_scores()` itera sobre TODOS los documentos cada vez
- Sin caché de resultados
- Solución: implementar caché TTL de resultados de retrieval + limitar corpus BM25

### 4. [P1] Grafo 40MB deserializado y recorrido en cada consulta
- `pickle.load()` del grafo NetworkX completo (~40MB) cada consulta
- Traversal BFS de vecinos para cada documento recuperado
- Solución: implementar singleton (lazy loading con cache en memoria)
- Mejora adicional: precomputar estadísticas de entidades (jueces, leyes, actores más frecuentes)

### 5. [P2] 3 escrituras a disco síncronas por consulta
- `save_query_log()` escribe .md + .txt
- `save_chunk_audit()` escribe _audit.json
- Síncronas, en el hot path de la respuesta
- Solución: mover a async IO o escribir en batch (cada N consultas)

### 6. [P2] Sin caché de consultas
- Consultas idénticas o muy similares re-ejecutan todo el pipeline
- Comun en RAG legal: usuarios preguntan variaciones de lo mismo
- Solución: caché simple (dict con hash de query + TTL)
- Mejora estimada: 30-50% de queries servidas desde caché

### 7. [P2] Embeddings en CPU
- `device='cpu'` en sentence-transformers
- 64K+ vectores procesados en CPU en indexación (lento)
- En consulta: 1 embedding por query (menos crítico)
- Solución: cambiar a GPU si disponible, o mantener CPU (solo 1 embedding/query)

### 8. [P2] DeepSearcher duplica carga de índices
- Cada sub-query llama a `get_hybrid_context()` que recarga FAISS y BM25
- 5 sub-queries = 5 cargas redundantes de índices
- Solución: refactorizar para cargar índices una vez y reusarlos

### 9. [P3] Feedback loop (Critic + Rewrite) añade 1-2 LLM calls
- CriticAgent + rewrite con llama-3.1-8b
- Añade ~2-5 segundos y ~500-1000 tokens por consulta
- Pero: atrapa alucinaciones → trade-off aceptable para RAG legal
- Solución: mantener pero hacer rewrite opcional (solo si critic detecta problemas reales)

### 10. [P3] Fallback chain excesiva en synthesizer
- 1 fallback DPK + 4 fallbacks Groq = 5 intentos máximo
- Cada fallback toma ~2-5 segundos en timeout
- Solución: reducir a 2 fallbacks (DPK → llama-3.3-70b → mixtral)

### 11. [P3] FAISS tipo de índice no es bottleneck
- FlatL2 tarda ~7.71ms para 60K vectores. Con ~9s de tiempo total de consulta, optimizar FAISS no mejora la experiencia de usuario.
- HNSW probado: 12x más rápido pero 94.8% recall. La ganancia real es ~7ms — irrelevante.
- No optimizar FAISS hasta que el corpus supere 500K documentos.

## Errores de Código

1. **`print()` en lugar de logging** en el feedback loop (líneas 158-213 de graphrag_pro.py)
2. **Excepción silenciosa** en parseo de streaming (línea 125: `except: pass`)
3. **`_doc_header()` carga metadata y entities cada llamada** — overhead innecesario
4. **Chunk text: word-based split** — no respeta límites semánticos, podría usar tiktoken

## Infraestructura Recomendada

### Mínima (funciona hoy — WSL/Laptop)
- RAM: 8GB (índices 403MB caben, sobra para SO)
- CPU: 4+ cores (ThreadPoolExecutor usado en varias partes)
- Disco: SSD (pickle carga ~0.5s en SSD, ~2-3s en HDD)
- GPU: No requerida (embeddings en CPU, API calls remotas)
- Costo API: ~$0.001-0.003/consulta (DeepSeek barato)

### Recomendada (costo/beneficio óptimo)
- RAM: 16GB (permite tener índices cacheados + margen)
- CPU: 8 cores (paralelismo real en DeepSearcher + indexación)
- GPU: T4 16GB o similar (embeddings 10x más rápido, batch processing)
- Disco: SSD NVMe
- Caché: Redis o SQLite en memoria para resultados frecuentes
- Proveedor: Vultr/DO $40-60/mes o GPU instance spot en GCP/AWS

### Escalada (crecimiento >500K docs y >100 queries/día)
- RAM: 32GB
- CPU: 16 cores
- GPU: L4/A10 24GB+ (modelos locales opcionales)
- Índices: FAISS con IVF+HNSW + BM25 fragmentado por materia/año
- Cache: Redis cluster
- Proveedor: GCP/AWS con GPU instances reservadas

## Resumen: Prioridades de Acción

| Prioridad | Acción | Esfuerzo | Impacto |
|-----------|--------|----------|---------|
| P1 | Singleton para índices (FAISS/BM25/grafo no recargarse) | 2-3h | -38% latencia |
| P1 | Caché de consultas | 2h | -30-50% queries |
| P1 | Router con modelo 8B | 15min | -50% costo API router |
| P2 | FAISS IVF (índice aproximado) | 3h | -90% tiempo FAISS |
| P2 | Escrituras async + batch | 2h | -10% latencia |
| P2 | DeepSearcher reusar índices | 1h | -50% tiempo deep |
| P3 | Reducir fallback chain | 15min | -10% timeouts |
