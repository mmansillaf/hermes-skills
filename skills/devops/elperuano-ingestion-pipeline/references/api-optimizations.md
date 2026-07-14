# API Optimization Patterns — El Peruano RAG

Patterns implemented on api_rest.py (May 2026). Reusable for any FastAPI + Groq backend.

## 1. Streaming SSE with AsyncGroq

**Problem:** Sync `requests.post()` blocks for 3-5s, user sees nothing.

**Solution:** `StreamingResponse` with Server-Sent Events.

```python
from fastapi.responses import StreamingResponse
from groq import AsyncGroq

async def generate_answer_stream(question, profile, results, sources):
    """Async generator yielding SSE events."""
    yield f"data: {json.dumps({'event': 'start', 'results_count': len(results)})}\n\n"
    
    client = AsyncGroq(api_key=api_key)
    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        stream=True, max_tokens=800, temperature=0.3
    )
    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield f"data: {json.dumps({'event': 'token', 'text': content})}\n\n"
    yield f"data: {json.dumps({'event': 'done'})}\n\n"

# In endpoint:
class QueryRequest(BaseModel):
    stream: bool = False  # NEW FIELD

async def query_endpoint(req: QueryRequest):
    if req.stream:
        return StreamingResponse(
            generate_answer_stream(...),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    # ... normal non-streaming path
```

**Key details:**
- TTFT drops from 3-5s to ~0.34s (measured with llama-3.3-70b-versatile)
- Endpoint MUST be `async def` to use AsyncGroq
- `stream=True` in Groq API call
- SSE format: `data: {json}\n\n` per event
- Events: `start`, `token`, `done`, `error`
- `X-Accel-Buffering: no` header for nginx proxies

## 2. Parallel Search with ThreadPoolExecutor

**Problem:** FTS5 (80ms) → Qdrant (50ms) → Neo4j (200ms) = 330ms sequential.

**Solution:** Run Qdrant and Neo4j in parallel via `concurrent.futures`.

```python
import concurrent.futures

def _run_qdrant():
    # Qdrant search logic
    return results, source_info

def _run_neo4j():
    # Neo4j graph traversal logic
    return results, source_info

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    future_q = executor.submit(_run_qdrant)
    future_n = executor.submit(_run_neo4j)
    qdrant_results, qdrant_src = future_q.result()
    neo4j_results, neo4j_src = future_n.result()

results.extend(qdrant_results)
results.extend(neo4j_results)
```

**Key details:**
- Speedup: 330ms → 200ms (1.65x)
- FTS5 runs first (needed for entity detection in Neo4j)
- Qdrant and Neo4j are independent → parallelizable
- ThreadPoolExecutor works in async endpoints (FastAPI handles thread pool)

## 3. Response Cache LRU with TTL

**Problem:** Identical queries re-execute the full pipeline.

**Solution:** Dict-based cache with TTL, checked BEFORE search_sqlite.

```python
_response_cache = {}
CACHE_TTL = 3600  # 1 hour

def _get_cached(question, profile, top_k):
    key = f"{question}|{profile}|{top_k}"
    entry = _response_cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None

def _set_cache(question, profile, top_k, data):
    key = f"{question}|{profile}|{top_k}"
    _response_cache[key] = {"data": data, "ts": time.time()}
    if len(_response_cache) > 500:
        # Evict oldest 100 entries
        oldest = sorted(_response_cache.items(), key=lambda x: x[1]["ts"])[:100]
        for k, _ in oldest: del _response_cache[k]

# In endpoint:
cached = _get_cached(question, req.profile, top_k)
if cached:
    cached["timing_ms"] = round((time.time() - t0) * 1000)  # Real timing
    cached["cached"] = True
    return cached

# ... full pipeline ...

result = {...}
_set_cache(question, req.profile, top_k, result)
return result
```

**Key details:**
- Cache hit: 2115ms → 1ms (2000x speedup)
- Cache key includes question + profile + top_k
- Auto-evicts oldest entries when >500
- Update `timing_ms` on cache hit to show real retrieval time
- Add `cached: True` flag so clients can detect it
- Do NOT cache streaming responses (TTL too short to matter)

## 4. Model Router (2-tier)

**Problem:** All queries use llama-3.3-70b-versatile, even simple ones.

**Solution:** Use llama-3.1-8b-instant for BASICO queries (1.6x faster).

```python
def _model_for_level(router_level):
    if router_level == "BASICO":
        return "llama-3.1-8b-instant"  # 0.57s vs 0.94s
    return "llama-3.3-70b-versatile"

# In generate_answer:
model = _model_for_level(sources.get("router", {}).get("nivel", "INTERMEDIO"))
resp = requests.post("https://api.groq.com/...", json={"model": model, ...})
```

**Key details:**
- BASICO queries: ~40% of traffic, 1.6x faster
- Same prompt, just different model
- 8b instant handles factual lookups well (¿cuál es la ley X?, ¿quién es el ministro?)
- 70b versatile for INTERMEDIO/AVANZADO (análisis, dictámenes)

## Combined Speedup

| Pipeline Stage | Before | After |
|---|---|---|
| Search (FTS5+Qdrant+Neo4j) | 330ms seq | 200ms parallel |
| LLM Generation | 940ms (70b) | 570ms (8b, 40% q) / 940ms (70b, 60% q) |
| Cache Hit | N/A | 1ms |
| **TTFT (streaming)** | 3-5s | 0.34s |
| **Total (no cache)** | ~1.3s | ~0.9s avg |
| **Total (cache hit)** | ~1.3s | ~1ms |

## 5. User Preference: Code Simplicity

El usuario prefiere código simple, legible y mantenible. Patrones aplicados:

- **Funciones pequeñas**: cada helper hace UNA cosa (≤50 líneas ideal)
- **Nombres descriptivos**: `_detect_exact_id()`, `_dedup_and_blend()`, `_model_for_level()`
- **Factory functions**: `_make_result()` elimina 5+ construcciones duplicadas
- **Sin sobre-ingeniería**: ThreadPoolExecutor en vez de asyncio complejo para paralelismo simple
- **Cambios quirúrgicos**: modificar 1 archivo, 1 función a la vez, commiteando cada paso
- **Backward compatible**: agregar `stream: bool = False` sin romper el endpoint existente
