# Local LLM Comparison for Legal Tasks (Jun 2026)

Research on which models can run on 16GB RAM PCs for legal document search,
drafting, and analysis tasks.

## Models that fit in 16GB RAM (with Ollama)

| Model | Size | Quant | RAM real | tok/s (CPU) | Español legal | Veredicto |
|-------|:----:|:-----:|:--------:|:-----------:|:-------------:|:---------:|
| Qwen3 8B | 8B | Q4_K_M | ~6 GB | 15-25 | ✅ Bueno | **✅ Mejor opción** |
| Llama 3.1 8B | 8B | Q4_K_M | ~6 GB | 15-25 | ✅ Bueno | **✅ Alternativa** |
| Qwen3 14B | 14B | Q4_K_M | ~10 GB | 5-10 | ✅ Bueno | ✅ Si sobra RAM |
| DeepSeek R1 14B | 14B | Q4_K_M | ~10 GB | 4-8 | ✅ Bueno | ✅ Razonamiento |
| Gemma 3 12B | 12B | Q4_K_M | ~9 GB | 8-12 | ⚠️ Regular | Limitado español |
| Phi-4 14B | 14B | Q4_K_M | ~10 GB | 5-8 | ⚠️ Poco español | Solo si es técnico |
| Mistral 7B | 7B | Q4_K_M | ~5 GB | 20-30 | ✅ Bueno | ✅ Ligero |
| Gemma 4 26B MoE | 26B | Q4_K_M | ~12 GB | 2-5 | ❓ Desconocido | ❌ Lento en CPU |

## Modelos que NO corren en 16GB

| Modelo | RAM necesaria | Razón |
|--------|:-------------:|-------|
| Llama 3.3 70B | ~40 GB | Muy grande |
| DeepSeek V3 | ~80 GB | Muy grande |
| Gemma 4 31B Dense | ~22 GB | No cabe cuantizado |
| Qwen3 122B MoE | ~70 GB | Muy grande |

## Stack completo para 16GB

```
Ollama (Qwen3 8B Q4_K_M)     → ~6 GB
FAISS index (11K vectors)    → ~0.1 GB  
BM25 + metadata + textos      → ~3 GB
Embeddings cache              → ~1 GB
Sistema operativo             → ~4 GB
─────────────────────────────────
Total                         → ~14 GB  (✅ ~2 GB libres)
```

## Costos: API vs Local

| Escenario | 10 q/día | 50 q/día | 100 q/día | 500 q/día |
|-----------|:--------:|:--------:|:---------:|:---------:|
| DeepSeek API | $0.48/mes | $2.40/mes | $4.80/mes | $24/mes |
| Groq 70b API | $1.29/mes | $6.46/mes | $12.91/mes | $64.55/mes |
| **Local (Qwen3 8B)** | **$0** | **$0** | **$0** | **$0** |

El costo de API para DeepSeek es bajo. La ventaja de local es:
- Sin conexión a internet
- Sin límite de rate (Groq free tier tiene 30 TPM)
- Privacidad de datos (los documentos no salen de la PC)
- Sin dependencia de terceros

## LightRAG vs Hybrid RAG para legales

LightRAG (HKU, v1.5.2, Jun 2026) construye un grafo de conocimiento extrayendo
entidades y relaciones con un LLM durante la indexación.

| Aspecto | Hybrid RAG (TC_SearchRAG) | LightRAG |
|---------|:------------------------:|:--------:|
| Indexación | ~10 min ($0) | 2-4h (~$1-3 en LLM) |
| RAM durante consulta | ~3 GB | ~7-10 GB |
| Búsqueda por tema | ✅ FAISS semántico | ✅ Grafo + vector |
| Búsqueda por entidad | ✅ Filtros metadata | ✅ Navegación de grafo |
| "Qué otros casos de este juez?" | ✅ Filtro --juez | ✅ Grafo traversal |
| "Qué leyes conectan estos casos?" | ❌ No | ✅ Relaciones en grafo |
| Complejidad | Baja | Media-Alta |
| Ideal para | <50K docs independientes | >10K docs con relaciones |

**Conclusión:** Para jurisprudencia del TC (casos independientes), Hybrid RAG es
más eficiente. LightRAG tiene sentido cuando los documentos se refieren unos a otros
(expedientes vinculados, contratos con remisiones, leyes que modifican otras leyes).
