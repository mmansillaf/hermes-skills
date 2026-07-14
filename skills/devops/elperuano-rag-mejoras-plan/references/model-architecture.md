# Arquitectura de Modelos — El Peruano RAG

**Última verificación:** 1-may-2026 | **Archivos:** `api_rest.py`, `02_groq_batch_pipeline.py`

## Resumen: 3 modelos para 3 funciones distintas

| Función | Modelo | Provider | Costo | Ubicación |
|---------|--------|----------|-------|-----------|
| **Responder queries** | `llama-3.3-70b-versatile` | Groq API sync | ~$0.0008/query | `api_rest.py:1272` |
| **Ingesta/extracción** | `llama-3.1-8b-instant` | Groq Batch API | ~$0.0015/doc | `02_groq_batch_pipeline.py:148` |
| **Embeddings vectoriales** | `paraphrase-multilingual-MiniLM-L12-v2` | Local CPU | $0 | `api_rest.py:86` |

## Detalle por modelo

### Respuesta — llama-3.3-70b-versatile

- Llamada síncrona vía `/v1/chat/completions`
- 800 tokens max, temperatura 0.3, timeout 45s
- Se usa en `generate_answer()` dentro de `api_rest.py`
- Usa `requests` library (NO `urllib` — Groq rechaza HTTP/2)
- ~1500-3000ms por query (incluye cold start)

### Ingesta — llama-3.1-8b-instant

- Procesamiento asíncrono por lotes (batch) de 500 docs
- Temperatura 0.0, `response_format: json_object`
- Extrae: tipo_norma, numero, fecha, emisor, sumilla, materia, funcionarios, entidades, base_legal, montos, normas_citadas
- ~24h máximo para completar (completion_window)
- No usar el modelo 70B para ingesta — cuesta ~10x más sin beneficio en extracción estructurada

### Embeddings — MiniLM 384d

- Corre local en CPU (sin GPU)
- 384 dimensiones, ~130ms por encoding después de warmup
- 4.7x mejor discriminación que E5-large 1024d en corpus legal español (test 30-abr-2026)
- **NO migrar** — benchmark demostró que MiniLM es superior para este corpus

## Pitfalls

- **HTTP/2 con Groq:** Python `urllib` usa HTTP/2 por defecto, Groq lo rechaza. Usar siempre `requests`.
- **Modelos descontinuados:** `llama3-70b-8192` y `mixtral-8x7b-32768` ya no existen en Groq.
- **Cold start:** Primera llamada a Groq puede tardar >30s. Timeout mínimo recomendado: 45s.
- **Confusion ingesta/respuesta:** Si se usa el 70B para ingesta, el costo se dispara sin ganancia de calidad. El 8B con temp=0 es suficiente para extracción estructurada.
