# Large-Scale Battery Testing for El Peruano RAG

Technique developed 2026-05-06 for running 100+ question batteries efficiently.

## Problem

Background `terminal` processes buffer Python stdout when not connected to a TTY.
`python3 -u` doesn't always flush. Sub-agents have 300s timeout limits.
Direct `execute_code` blocks work but have a 300s limit.
100 queries × ~2.5s each = ~250s, which fits in execute_code but must be split for safety.

## Solution

Split the battery into batches of 25 questions, run each via `execute_code`.

### Batch Script Structure

```python
import sys, json, time, requests

API = "http://localhost:8000"
TIMEOUT = 90

QUESTIONS = [
    (1, "query text", "abogado", "BASICO"),
    ...
]

for idx, q, perfil, nivel in QUESTIONS:
    t0 = time.time()
    try:
        resp = requests.post(f"{API}/query",
            json={"question": q, "profile": perfil, "top_k": 5},
            timeout=TIMEOUT)
        ms = round((time.time()-t0)*1000)
        d = resp.json()
        results.append({...})
    except requests.exceptions.Timeout:
        results.append({"quality": "TIMEOUT"})
```

### Monitoring

```bash
curl -s --max-time 5 http://localhost:8000/health
```

Track: SQLite count, Qdrant broken pipe, Neo4j timeouts, Groq latency variance.

### Results Aggregation

```python
all_results = []
for lot in [1,2,3,4]:
    with open(f"reports/bateria_100q_lote{lot}.json") as f:
        data = json.load(f)
    if isinstance(data, dict):
        all_results.extend(data.get('results', []))
    else:
        all_results.extend(data)
```

### Report Format

TXT with: summary, by-level breakdown, low-confidence analysis, web fallback analysis, DB health, observations.

## CRITICAL PITFALL: Answer Truncation

**Symptom:** Answers cut mid-sentence: `"...de fecha 20 de octubre de 2025. En e"`

**Root cause:** Test script saves `"answer": answer[:250]` (250 chars max).

**Users HATE this.** They want full answers in reports.

**Fix:** Change `answer[:250]` → `answer` in test script. Re-run.

## CRITICAL PITFALL: Synchronous `generate_answer` Blocks Event Loop

**Symptom:** Query #1 passes, then ALL subsequent queries return `TIMEOUT | >90s`. `/health` hangs. API unresponsive.

**Root cause:** `generate_answer()` is a synchronous `def` using `requests.post(timeout=45)`. Called from the async `/query` endpoint, it **blocks the entire uvicorn event loop**. While waiting for Groq (up to 45s), no other request can be served.

**Diagnosis:** Run `curl -s --max-time 3 http://localhost:8000/health` in another terminal during battery. If it hangs, this pitfall is active.

**Fix (3 changes):**

1. Make `generate_answer()` async with thread pool:
```python
async def generate_answer(question, profile, results, sources):
    def _do_groq():
        r = requests.post(..., timeout=45)
        return r.json()["choices"][0]["message"]["content"].strip()
    answer = await asyncio.wait_for(
        asyncio.to_thread(_do_groq),
        timeout=50
    )
    return answer
```

2. Make `route_response()` in `src/core/router.py` async — `await` every `generate_answer()` call (4 call sites).

3. `await route_response(...)` in the `/query` handler.

**Result:** `/health` responds instantly during battery. 100 queries in ~5 min, 0 timeouts.

**Prevention:** Always wrap blocking I/O in async when serving with uvicorn.

## CRITICAL PITFALL: Lote 2 Uses Different JSON Schema

**Symptom:** Questions #026-#050 show `Q: ?`, `conf=0.00`, `0ms`.

**Root cause:** Lote 2 uses `question`/`status`/`confidence`/`timing_ms` instead of `q`/`quality`/`conf`/`ms`.

**Fix:** Normalize before aggregation (check both field names).

## Common Findings

1. WARNs ≠ bugs — mostly "norma not in DB", system reports honestly
2. Low confidence on specific norms → missing from index, conf <0.30 is CORRECT
3. Web fallback 20-30% — reduce by ingesting missing norms
4. Multi-hop rarely triggered on legal analysis queries
5. Cache: 20% hits on repeated queries, <500ms response
