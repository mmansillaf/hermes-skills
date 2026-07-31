# Chunk-Level Audit — LexRAG Implementation (KGraphResolucionesV3)

Implementation session: 2026-05-19. Added granular retrieval tracing to the LexRAG modular pipeline.

## Files Modified

| File | Change Summary |
|------|---------------|
| `retrieval/hybrid_search.py` | `get_hybrid_context()` returns `(top_docs, text_context, audit_dict)`. Captures faiss_raw (21 chunks with distance), bm25_raw (21 chunks with bm25_score), rrf_ranked (top_k*2 fused chunks), chunks_filtered_out (rest), final_docs. |
| `retrieval/graph_search.py` | `get_graph_context()` returns `(text, audit_dict)`. Captures nodes_with_data (doc_id, fallo, neighbors with hop2_docs), neighbors_found, total_edges_processed. |
| `utils/logger_utils.py` | New `save_chunk_audit()` writes `*_audit.json` with metadata, retrieval (hybrid + graph), and response. |
| `agents/synthesizer.py` | Imports `save_chunk_audit`, calls it after `save_query_log` when audit data is present. |
| `graphrag_pro.py` | `run_console_query()` collects hybrid_audit + graph_audit, calculates elapsed, passes to `generate_rag_synthesis`. |
| `api.py` | Same pipeline changes for FastAPI endpoint. |

## Output Files

Each query generates in `consultas_guardadas/`:
```
YYYYMMDD_HHMMSS_queryname.md          # query + respuesta + contexto truncado
YYYYMMDD_HHMMSS_queryname.txt         # query + respuesta + contexto completo
YYYYMMDD_HHMMSS_queryname_audit.json  # structured audit (NEW)
```

## Key Design Decisions

1. **Audit as separate return value, not side-effect**: Each retrieval function returns its audit dict alongside normal output. This keeps the audit data accessible to callers without forcing side-effects deep in the stack.

2. **Audit saved at the synthesizer layer**: `save_chunk_audit()` is called from `generate_rag_synthesis()` after the LLM responds, so the audit includes the final response text alongside retrieval trace.

3. **Conditional audit** (`if hybrid_audit is not None`): WEB-routed queries skip hybrid + graph retrieval, so their audit fields are None. The logger only saves audit JSON when structured data exists.

4. **No BC break**: Existing callers of `get_hybrid_context()` that don't destructure the third element will get a tuple unpacking error. Update ALL callers or use `*_` pattern.

## Snapshot of Generated Audit JSON

```json
{
  "metadata": {
    "timestamp": "20260519_180330",
    "query": "despido arbitrario",
    "decision": "LOCAL",
    "hyde_query": "El usuario solicita información...",
    "elapsed_seconds": 8.39
  },
  "retrieval": {
    "hybrid": {
      "faiss_raw": [
        {"chunk_index": 7706, "doc_id": "850792.html", "distance": 0.746, "rank": 1,
         "snippet": "HECHOS: La demandante... (200 chars)"}
      ],
      "bm25_raw": [
        {"chunk_index": 20537, "doc_id": "437227.html", "bm25_score": 52.92, "rank": 1,
         "snippet": "HECHOS: El demandante... (200 chars)"}
      ],
      "rrf_ranked": [...],
      "chunks_filtered_out": [...],
      "final_docs": [{"doc_id": "850792.html", "label": "", "rank": 1}, ...]
    },
    "graph": {
      "nodes_with_data": [...],
      "neighbors_found": ["Juez: Landa Arroyo", ...],
      "total_edges_processed": 47
    }
  },
  "response": {
    "text": "## Dictamen...",
    "tokens_estimados": 1461
  }
}
```

## All Callers of Modified Functions

| Function | Caller Files |
|----------|-------------|
| `get_hybrid_context()` | graphrag_pro.py, api.py, Unidad_D/graphrag_pro.py, Unidad_D/graphrag_pro_v2.py, Unidad_D/api.py, export_cambios_rutas/hybrid_search.py |
| `get_graph_context()` | graphrag_pro.py, api.py, Unidad_D/graphrag_pro.py, Unidad_D/graphrag_pro_v2.py, Unidad_D/api.py, export_cambios_rutas/graph_search.py |

**Note**: Only `graphrag_pro.py` and `api.py` were updated in this session. The Unidad_D/ and export_cambios_rutas/ variants still use the old 2-value return and will error if called without updating.
