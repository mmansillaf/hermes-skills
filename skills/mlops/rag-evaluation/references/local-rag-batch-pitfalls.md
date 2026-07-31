# Local RAG batch testing — pitfalls and patterns

## Approaches tried (2026-06-05, Lex RAG + DeepSeek)

### 1. Subprocess per query (Python) — works, slow
- Each subprocess loads model from scratch (~90s model + ~30s query)
- 15 queries × 120s = 30 min
- stdout buffering: background processes lose print() output
- Use `PYTHONUNBUFFERED=1` env var
- Parse stdout for respuesta + follow_ups

### 2. Direct async import — failed
- `from graphrag_pro import run_console_query` + `asyncio.run()`
- Problem: `contextlib.redirect_stdout` + async generator interaction
- Process hung indefinitely with no output
- Not recommended for streaming generators

### 3. Bash script with timeout — MOST RELIABLE
- `timeout 300 $VENV $SCRIPT --query "$Q" > "$OUTFILE" 2>&1`
- No Python buffering, no async issues
- Each query writes complete output to file
- Simple progress tracking by checking file sizes

## Dependency chain (Lex RAG example)
openai → rank-bm25 → transformers → torch + CUDA → scikit-learn
Install one at a time, retry the import to isolate the next missing dep.

## WSL /mnt/d specifics
- /mnt/d is slow for pip installs and model downloads
- Use background=true + notify_on_complete=true with long timeouts
- SentenceTransformer models download from HF Hub unfettered (no HF_TOKEN)
- Model: distiluse-base-multilingual-cased-v2 (~500MB)

## Health check pattern
Verify before batch testing:
1. API keys (GROQ_API_KEY, DEEPSEEK_API_KEY)
2. Indices (FAISS .bin, BM25 .pkl, Graph .pkl)
3. Metadata (metadata_docs.json, doc_entities.json)
4. Model loads without error
5. Single test query succeeds
