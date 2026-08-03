# Batch JSONL Format (Groq / OpenAI Batch API)

Reference for the JSONL format used when sending batch extraction jobs to Groq's Batch API.

## Request format

Each line in the JSONL file is one batch request:

```json
{
  "custom_id": "tc_00004-2025-AI.pdf",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "llama-3.3-70b-versatile",
    "messages": [
      {"role": "system", "content": "Eres un asistente legal experto..."},
      {"role": "user", "content": "Realiza el análisis..."}
    ],
    "temperature": 0.1,
    "max_tokens": 1024
  }
}
```

### Fields

| Field | Required | Description |
|-------|:--------:|-------------|
| `custom_id` | ✅ | Unique identifier. Pattern: `tc_{filename}` for TC docs |
| `method` | ✅ | Always `"POST"` |
| `url` | ✅ | Always `"/v1/chat/completions"` |
| `body.model` | ✅ | `"llama-3.1-8b-instant"` or `"llama-3.3-70b-versatile"` |
| `body.messages` | ✅ | Array: system prompt + user message |
| `body.temperature` | ❌ | Default 0.1 for deterministic extraction |
| `body.max_tokens` | ❌ | Default 1024 (enough for summary JSON) |

## Response format (batch output)

Groq returns a JSONL where each line corresponds to a request:

```json
{
  "id": "batch_req_abc123",
  "custom_id": "tc_00004-2025-AI.pdf",
  "response": {
    "status_code": 200,
    "request_id": "req_xyz789",
    "body": {
      "id": "chatcmpl-...",
      "choices": [{
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "{\n  \"resumen_hechos\": \"...\",\n  \"resumen_problema\": \"...\",\n  \"resumen_fallo\": \"...\",\n  \"entidades_clave\": { ... }\n}"
        }
      }]
    }
  }
}
```

## Converting batch output to indexer format

The indexer (`pipeline/indexer.py`) expects `rag_listo_batch_*.json` files in this format:

```json
[
  {
    "id_documento": "00004-2025-AI.pdf",
    "ruta_local": "/TC_SEDETC_Scraper/pdfs/2025/00004-2025-AI.pdf",
    "contenido_a_vectorizar": {
      "hechos": "...",
      "problema": "...",
      "fallo": "..."
    },
    "metadatos_graphrag": {
      "jueces_magistrados": ["...", "..."],
      "demandantes_accionantes": ["..."],
      "demandados_accionados": ["..."],
      "leyes_y_articulos_citados": ["..."],
      "conceptos_legales_clave": ["..."]
    }
  }
]
```

### JSON parsing edge cases (LLM output)

The LLM rarely returns pure JSON. Observed patterns and their handling:

| Pattern | Example | Fix |
|---------|---------|-----|
| Markdown code block | ````json\n{"resumen_hechos": "..."}\n```` | Strip lines between ``` markers |
| Text before/after JSON | `Here's the analysis:\n{"hechos": "..."}\nEnd.` | Regex `{.*}` with DOTALL |
| Trailing comma | `{"hechos": "...",}` | `json.loads()` with `strict=False` or regex fix |
| Escaped quotes | `\"hechos\": \"El caso...\"` | Normal JSON parser handles this |
| Array as string | `"jueces": "Nugent, Acosta"` instead of array | Fallback: split by comma |
| Truncated JSON | `{"hechos": "El caso...` | Detect and reject (incomplete) |
| Null values | `"demandantes": null` or `"demandantes": ""` | Treat as empty list |

Conversion pipeline:
1. Parse Groq batch output (JSONL) → group by `custom_id`
2. Parse `content` field as JSON (the LLM's structured output)
3. Map `resumen_hechos` → `contenido_a_vectorizar.hechos`, etc.  
4. Map `entidades_clave` → `metadatos_graphrag`
5. Look up PDF path from mapping file to populate `ruta_local`
6. Write as JSON array to `rag_listo_batch_tc_*.json`

**Reference implementation**: `scripts/data_prep/enviar_batch_tc.py` function `convert_to_indexer_format()`.

## Hybrid model selection

| Condition | Model | Cost/doc (Jun 2026) |
|-----------|-------|:-------------------:|
| ≤1000 tokens estimated | `llama-3.1-8b-instant` | ~$0.00009 |
| >1000 tokens estimated | `llama-3.3-70b-versatile` | ~$0.0011 |

Token estimation: `math.ceil(word_count / 0.75)`

## File naming convention

```
# 8B batches (short docs)
batch_tc_8B_pt{001..N}_{timestamp}.jsonl

# 70B batches (long docs)
batch_tc_70B_pt{001..N}_{timestamp}.jsonl

# Mapping file (custom_id → PDF path + metadata)
mapping_{timestamp}.json

# Indexer-ready output
rag_listo_batch_tc_{groq_batch_id}.json
```

## Implementation notes

- Each JSONL file capped at 4,500 lines (Groq batch file size limits)
- Always validate with `validate_batch_request()` before uploading
- Delete files from Groq after processing: `client.files.delete(file_id)`
- The mapping file is critical — without it you can't reconstruct `ruta_local`
