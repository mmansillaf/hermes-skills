# API Performance Optimization — El Peruano RAG

**Date:** 2026-05-01
**Status:** Benchmark completed, awaiting implementation

## Pipeline Latency Breakdown

```
Current (sequential):
  search_sqlite()    80ms  ← FTS5 over SQLite (already C, no Rust needed)
  search_qdrant()    50ms  ← REST to localhost:6333
  Neo4j traversal   200ms  ← Bolt to localhost
  confidence_score   15ms  ← Python dict ops
  generate_answer() 940ms  ← Groq llama-3.3-70b HTTP POST (blocking)
  ─────────────────────
  TOTAL            1.3s   (user sees nothing for 3-5s with network)
```

## Groq Streaming Benchmarks (2026-05-01)

Tested against Groq API with 200 tokens, temperature=0.3, streaming:

| Model | TTFT | Total 200 tok | t/s | Legal Quality |
|---|---|---|---|---|
| llama-3.1-8b-instant | 0.30s | 0.57s | ~350 | Low |
| allam-2-7b | 0.40s | 0.54s | ~370 | None (Arabic) |
| qwen/qwen3-32b | 0.29s | 0.70s | ~285 | Good |
| llama-3.3-70b-versatile | 0.34s | 0.94s | ~213 | Excellent (CURRENT) |
| llama-4-scout-17b | 1.89s | 1.99s | ~25 | Very good (slow) |

**16 models active on Groq** (verified via API listing).

## Priority 1: Streaming SSE (2-3 days, TTFT: 3-5s → 0.34s)

**Stack:** FastAPI StreamingResponse + groq.AsyncGroq + stream=True

**Pattern:**
1. Run searches (FTS5+Qdrant+Neo4j) BEFORE starting stream
2. Emit SSE events: `start` (metadata) → `token` (each chunk) → `done` (confidence)
3. Detect via `?stream=true` or `Accept: text/event-stream` header
4. Keep non-streaming endpoint unchanged (backward compatible)

**Dependencies:** `groq>=1.1.2`, `sse-starlette>=2.0` (optional)

## Priority 1: Parallel Search (1-2 days, 330ms → 200ms)

Replace sequential calls with `asyncio.TaskGroup`:

```python
async with asyncio.TaskGroup() as tg:
    t1 = tg.create_task(search_sqlite_async(q, k))
    t2 = tg.create_task(search_qdrant_async(q, k))
    t3 = tg.create_task(search_neo4j_async(q, k))
```

**Requirements:**
- SQLite: `asyncio.to_thread()` wrapper (no native async driver)
- Qdrant: `httpx.AsyncClient` instead of `requests`
- Neo4j: `AsyncDriver` (already in `neo4j` library)
- Ensure `PRAGMA journal_mode=WAL` on SQLite

## Priority 2: Response Cache (0.5 days, 3-5s → 5ms on hit)

`functools.lru_cache(maxsize=500)` with TTL 1 hour.
Key: `hash(question + profile + top_k)`.
Invalidate on DB reingestion.
Estimated hit rate: 15-25% (legal queries repeat).

## Priority 2: Dual Model Router (0.5 days)

| Query Level | Model | Latency |
|---|---|---|
| BASICO + confidence > 0.85 | llama-3.1-8b-instant | 0.57s |
| Everything else | llama-3.3-70b-versatile | 0.94s |

~40% of queries can use the 8B model. Average LLM latency drops from 0.94s to ~0.72s.

## Priority 3: Qdrant gRPC (0.5 days, ~10-20ms savings)

Switch from REST (`localhost:6333`) to gRPC (`localhost:6334`).
Use `QdrantClient(prefer_grpc=True)`.
Verify "Broken pipe" bug is resolved in current qdrant-client.

## Rust/PyO3 — DO NOT USE

FTS5 is already C, Qdrant/Neo4j are I/O-bound, embedding is 10-20ms ONNX.
95% of latency is Groq (external network). Rust cannot help here.
2-3 weeks of development would save <10ms (<0.3% of total).
Zero return on investment.

## Projected Results

| Scenario | Pre-LLM | LLM | Total | TTFT |
|---|---|---|---|---|
| Current | 330ms | 940ms | 1.3s | 3-5s |
| Optimized (no cache) | 200ms | 940ms | 1.1s | 0.54s |
| Optimized (cache hit) | — | — | 5ms | 5ms |
| Optimized (BASICA query) | 200ms | 570ms | 0.77s | 0.44s |

## Implementation Cost: 5-7 days total
