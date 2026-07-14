# Cloud-First RAG for Low-RAM Windows (8-16GB, CPU-only)

## When to use this architecture
Building RAG on Windows with 8-16GB RAM and no GPU. Local LLMs (even 7B) don't fit or produce poor legal-quality answers. Cloud APIs give better quality at lower cost than any model that fits in 8GB RAM.

## Key Insight: Embeddings Local, LLM Cloud
- Embeddings run on CPU (bge-m3, 2GB) — one-time cost, free
- Vector search is local (Qdrant file mode, SQLite FTS5) — instant, free
- Answer generation is cloud (DeepSeek + Groq) — pay-per-use, ~$1-3/month

## Hardware Fit

| RAM | What fits |
|-----|-----------|
| 8GB | bge-m3 (2GB) + Qdrant + SQLite + Python. NO Ollama. |
| 16GB | Above + Ollama with 7-8B model as offline fallback |

## Provider Selection

| API | Model | Cost/1M tok | Speed | Legal Quality |
|-----|-------|-------------|-------|:---:|
| DeepSeek | deepseek-chat | $0.14 in / $0.28 out | ★★★★☆ | ★★★★★ |
| Groq | llama-3.1-8b | $0.05 / $0.08 | ★★★★★ | ★★★☆☆ |
| OpenAI | gpt-4o-mini | $0.15 / $0.60 | ★★★★☆ | ★★★★☆ |

**Recommendation:** DeepSeek primary + Groq fallback. Total ~$0.60/month for 50 queries/day.

## Cost Scale

50 queries/day × 1500 tokens each = 75k tokens/day = 2.25M tokens/month

| Scenario | Cost/month |
|----------|-----------|
| DeepSeek only | ~$0.60 |
| Groq only | ~$0.15 |
| DeepSeek + Groq fallback | ~$1.00 |

## Architecture Diagram

```
PC Windows (8GB)                  CLOUD APIs
┌──────────────────────┐         ┌─────────────────┐
│ MarkItDown → texto   │         │ DeepSeek API    │
│ bge-m3 → embeddings  │         │ ($0.14/1M tok)  │
│ Qdrant → vectores    │         └─────────────────┘
│ SQLite → keywords    │         ┌─────────────────┐
│ Hermes Agent → query │◄────────│ Groq API        │
└──────────────────────┘         │ (free tier)     │
                                 └─────────────────┘
```

## Pitfalls

1. **bge-m3 download**: First run downloads ~2GB. Warn user.
2. **DeepSeek rate limiting**: 50 req/min free tier. Add retry with backoff.
3. **Groq HTTP/2 bug**: Must use `requests` library (HTTP/1.1), never `urllib.request` (HTTP/2 breaks Groq).
4. **8GB RAM pressure**: During ingestion, close other apps. Use `--batch-size 50`.
5. **API key storage**: Use Windows env vars (sysdm.cpl), never hardcode.

## Reference Implementation

https://github.com/mmansillaf/rag-legal-local — Complete project:
- `ingestion_pipeline.py` — batch document processing
- `query_pipeline.py` — CLI query interface
- `app.py` — Streamlit web UI for non-technical users
- `RAG-Legal.bat` — desktop shortcut (double-click to launch)
