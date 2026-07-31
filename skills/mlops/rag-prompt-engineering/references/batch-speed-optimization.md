# Batch Query Speed Optimization for RAG Systems

## Problem

Running multiple RAG queries via subprocess (e.g., `subprocess.run([python, 'graphrag.py', '--query', q])`) reloads the entire model stack per query:
- Sentence-Transformer model download + load (~80s with unauthenticated HF Hub)
- FAISS index load from disk (~1s)
- LLM client initialization (~1s)

For a 15-query battery: **36 minutes total**, with ~20 minutes wasted on redundant model loading.

## Solution: Direct Function Call (Model Shared)

Import the query function directly and call it in a loop within a single Python process.

```python
import sys
sys.path.insert(0, "/path/to/project")
from graphrag_pro import run_console_query

async def run_batch(queries):
    results = []
    for q in queries:
        respuesta, follow_ups, _ = await run_console_query(q)
        results.append((respuesta, follow_ups))
    return results

asyncio.run(run_batch(queries))
```

## Key: Stdout Handling with Async Generators

`run_console_query()` is an async generator that yields streaming chunks AND prints to stdout. When called in batch mode, the prints can fill the pipe buffer and block. Two approaches:

### ❌ Broken: `contextlib.redirect_stdout`
```python
with contextlib.redirect_stdout(io.StringIO()):
    respuesta, follow_ups, _ = await run_console_query(q)
```
**Why it fails:** The async generator inside `run_console_query` gets blocked because the redirected stdout changes the event loop behavior. The generator hangs.

### ❌ Broken: `NullWriter` class
```python
class NullWriter:
    def write(self, s): pass
    def flush(self): pass

sys.stdout = NullWriter()
respuesta, follow_ups, _ = await run_console_query(q)
sys.stdout = old_stdout
```
**Why it fails:** Same issue — the async generator's `print()` calls interact with the replaced stdout in a way that blocks the event loop.

### ✅ Works: Let prints flow freely
```python
# Don't suppress stdout at all. The prints go to the pipe,
# but the return value (respuesta, follow_ups, history) is what matters.
respuesta, follow_ups, _ = await asyncio.wait_for(
    run_console_query(q),
    timeout=300
)
```
**Trade-off:** Log output fills the background pipe, but it's bounded (~5-10KB per query × 15 queries = ~150KB — well below the default 64KB pipe buffer, which flushes as the parent reads). For foreground runs, the prints render normally.

## Results

| Metric | Subprocess (per query) | Direct call (shared model) |
|--------|----------------------|---------------------------|
| Model load | 80s × 15 = 20 min | 80s × 1 = 1.3 min |
| Query processing | 45s × 15 = 11 min | 27s × 15 = 6.7 min |
| **Total** | **36 min 55 sec** | **6 min 39 sec** |
| Speedup | — | **5.5×** |

## HF_TOKEN for Faster Model Downloads

Add a HuggingFace token to `.env` to authenticate downloads. Without it, the `sentence-transformers` library downloads unauthenticated at ~1-2 MB/s with rate limiting. With a free Read token, speeds increase to ~10-20 MB/s.

```bash
# .env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxx
```

The `huggingface_hub` library auto-discovers `HF_TOKEN` from the environment. The `load_dotenv()` call in `core/config.py` loads it.

Token permissions needed: **Read access to contents of all public gated repos** (minimal). No write, inference, or billing access required.

## Pitfalls

- **Async generator + stdout suppression don't mix** — if `run_console_query` uses `yield` + `print()`, redirecting stdout in any form (contextlib, NullWriter, `os.dup2`) will hang the event loop. Let prints flow freely.
- **Pipe buffer overflow is not a concern** for typical batch sizes (15 queries × 10KB = 150KB, pipe buffer = 64KB but flushed continuously).
- **File writes are safe** — the batch script can write response files while prints stream to stdout concurrently.
