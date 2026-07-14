
# RAG Performance Optimization — Groq Streaming, Parallel Search & Model Selection

## Pipeline Timing Breakdown (El Peruano RAG, measured 2026-05-01)

```
Component          Time      % of total
─────────────────────────────────────────
Groq API call      3-5s      94%  ← dominant
Neo4j traversal    200ms     5%
SQLite FTS5        80ms      2%
Qdrant search      50ms      1%
Merge + scoring    <10ms     <1%
Embedding (MiniLM) 10-20ms   <1%
─────────────────────────────────────────
Total (sequential) ~4.0s
```

Takeaway: the only bottleneck worth addressing is Groq's network latency. Local operations are sub-200ms.

## 1. Streaming SSE (Server-Sent Events)

### Problem
Current: `requests.post()` blocking call. User waits 3-5s in silence.

### Solution
Groq library v1.1.2 supports `stream=True` + `AsyncGroq` natively. FastAPI `StreamingResponse` with `text/event-stream`.

### Pattern
```python
from fastapi.responses import StreamingResponse
from groq import AsyncGroq
import json

async def generate_sse(question, profile, results):
    # 1. Emit metadata event
    yield f"data: {json.dumps({'event': 'start', 'count': len(results)})}\n\n"
    
    # 2. Stream from Groq
    client = AsyncGroq()
    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        stream=True, max_tokens=800, temperature=0.3
    )
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield f"data: {json.dumps({'event': 'token', 'text': chunk.choices[0].delta.content})}\n\n"
    
    # 3. Done event with confidence
    yield f"data: {json.dumps({'event': 'done', 'confidence': 0.85})}\n\n"

@app.post("/query")
async def query(req: QueryRequest):
    if req.stream:
        return StreamingResponse(
            generate_sse(req.question, req.profile, results),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
```

### Impact
- TTFT (Time To First Token): 3-5s → **0.34s** (transformational UX improvement)
- Total latency unchanged, but user sees tokens immediately
- Searchers must run BEFORE stream starts → TTFT = search_time + 0.34s

### Pitfall: Cold searches before streaming
Run FTS5 + Qdrant + Neo4j BEFORE starting the stream. If searches are sequential (330ms), real TTFT is 330ms + 340ms = 0.67s. Parallelize first (see section 3).

## 2. Groq Model Benchmarks (2026-05-01)

| Model | Params | TTFT | Total 200t | t/s | Legal Quality |
|---|---|---|---|---|---|
| llama-3.1-8b-instant | 8B | 0.30s | 0.57s | 350 | Low |
| allam-2-7b | 7B | 0.40s | 0.54s | 370 | None (Arabic) |
| qwen/qwen3-32b | 32B | 0.29s | 0.70s | 285 | Good |
| llama-3.3-70b-versatile | 70B | 0.34s | 0.94s | 213 | **Excellent** (CURRENT) |
| llama-4-scout-17b | 17B | 1.89s | 1.99s | 25 | Very good (slower) |

**Benchmark conditions**: 200 output tokens, temperature=0.3, streaming, Spanish legal text.

### Recommended 2-level strategy

- **PRIMARY** (unchanged): `llama-3.3-70b-versatile` — best quality/speed balance for Spanish legal text
- **FAST for BASIC queries**: `llama-3.1-8b-instant` — 1.6x faster (0.57s vs 0.94s). Use when router classifies as `BASICO` + confidence > 0.85 (~40% of queries)
- **DO NOT USE**: allam-2-7b (Arabic), llama-4-scout (slow, possibly rate-limited)

### Available models (verified via Groq API, 2026-05-01)
To discover current models:
```bash
curl -s --http1.1 -X GET "https://api.groq.com/openai/v1/models" \
  -H "Authorization: Bearer $GROQ_API_KEY" | python3 -c "
import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]
"
```

## 3. Parallel Search with asyncio.gather

### Problem
Searches run sequentially: FTS5 (80ms) → Qdrant (50ms) → Neo4j (200ms) = **330ms total**

### Solution
Execute all three in parallel — total time = slowest (Neo4j, 200ms)

### Pattern
```python
import asyncio

async def search_parallel(question, top_k):
    async with asyncio.TaskGroup() as tg:
        fts5_task = tg.create_task(search_sqlite_async(question, top_k))
        qdrant_task = tg.create_task(search_qdrant_async(question, top_k))
        neo4j_task = tg.create_task(search_neo4j_async(question, top_k))
    return {
        "sqlite": fts5_task.result(),
        "qdrant": qdrant_task.result(),
        "neo4j": neo4j_task.result()
    }
```

### Requirements
- Replace `requests` with `httpx.AsyncClient` (Qdrant REST)
- Use `sqlite3` with `asyncio.to_thread()` (no native async driver)
- Use `Neo4j AsyncDriver` (available in `neo4j` library)
- SQLite must be in WAL mode: `PRAGMA journal_mode=WAL;`

### Impact
- Speedup: **1.65x** (330ms → 200ms)
- Combined TTFT with streaming: 200ms + 340ms = **0.54s** (vs 0.67s without parallel)

## 4. Rust with Python (PyO3/maturin) — NOT WORTH IT

### Analysis per component

| Component | Can Rust help? | Reason |
|---|---|---|
| FTS5 SQLite | NO | Already C. PyO3 overhead would erase gains |
| Qdrant search | NO | HTTP to localhost. Network bottleneck, not CPU |
| Neo4j traversal | NO | Bolt protocol, Rust can't accelerate the graph |
| Embedding (MiniLM) | MARGINAL | ONNX Runtime already fast. 5-10ms max |
| Blend scoring | NO | Simple dict operations on <100 items |
| Groq API call | NO | External network. Nothing Rust can do |

**Conclusion**: 95% of latency is Groq's external network call. No component is CPU-bound enough to justify 2-3 weeks of Rust development for <10ms gain (<0.3% of total).

## 5. Other Quick Wins

### LRU Response Cache (HIGH IMPACT)
- Legal queries are repetitive ("Ley 32108" asked many times)
- `functools.lru_cache` with TTL of 1 hour
- Cache hit: 3-5s → **5ms**
- Estimated hit rate: 15-25%

### Connection Pooling (MEDIUM)
- Use `httpx.AsyncClient` with keep-alive
- Eliminates TCP+TLS handshake per query
- Saving: ~50-100ms

### Qdrant gRPC (LOW)
- Current: REST to localhost:6333
- gRPC (protobuf binary) supported by qdrant-client
- Saving: ~10-20ms

## Projected Latency After All Optimizations

```
Current:                 330ms searches + 940ms LLM = 1.3s  (TTFT: 3-5s)
Optimized (no cache):    200ms searches + 940ms LLM = 1.1s  (TTFT: 0.34s) ★
Optimized (cache hit):   5ms = instant                          ★
Optimized (BASIC query): 200ms searches + 570ms LLM = 0.77s (TTFT: 0.30s)
```

## Implementation Effort

| Priority | Intervention | Effort | Impact |
|---|---|---|---|
| P1 | Streaming SSE | 2-3 days | TTFT 3-5s → 0.34s |
| P1 | Parallel searches (asyncio) | 1-2 days | 330ms → 200ms |
| P2 | LRU cache | 0.5 days | 3-5s → 5ms (hits) |
| P2 | 2-level model routing | 0.5 days | 40% queries faster |
| P3 | httpx pooling | included in P1 | ~50-100ms |
| P3 | Qdrant gRPC | 0.5 days | ~10-20ms |
| — | Rust/PyO3 | 2-3 weeks | <10ms — NOT WORTH IT |

**Total: 5-7 days for all P1-P2 interventions. Skip Rust entirely.**
