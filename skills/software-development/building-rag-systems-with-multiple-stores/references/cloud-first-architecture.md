# Cloud-First RAG Architecture

Pattern developed for building RAG systems on low-RAM machines (8-16GB) without GPU. Local embeddings + cloud LLM. Ideal when the user has limited hardware but wants decent quality.

## Core Principle

Index everything locally (free, one-time cost). Generate answers via cloud API (cents per query). This avoids the RAM bottleneck of running local LLMs while keeping document privacy (vectors never leave the machine).

## Stack

| Layer | Local or Cloud | Tool | Cost |
|-------|:---:|------|------|
| Extraction | Local | MarkItDown (★118k) | $0 |
| Chunking | Local | Regex/article-based | $0 |
| Embeddings | Local CPU | BAAI/bge-m3 (1024-dim) | $0 |
| Vector DB | Local | Qdrant file mode | $0 |
| Keyword DB | Local | SQLite FTS5 | $0 |
| LLM Primary | Cloud | DeepSeek API | ~$1/mo |
| LLM Fallback | Cloud | Groq API (free tier) | $0 |
| Web Fallback | Cloud | Serper API (100 free/mo) | $0 |
| UI | Local | Streamlit | $0 |

## Why This Pattern

- **8GB RAM:** Fits bge-m3 (~2GB), Qdrant, and Python. Cannot fit a decent local LLM.
- **No GPU:** bge-m3 runs on CPU (~10 chunks/sec). Cloud LLM handles the heavy inference.
- **$1-3/month:** DeepSeek at $0.14/1M tokens. 50 queries/day ≈ $0.60/month.
- **Privacy:** Document text and vectors never leave the machine. Only anonymized prompts hit the cloud API.

## Architecture Split

### Ingestion (standalone script, runs once)

```
15k docs → MarkItDown → legal chunks → bge-m3 → Qdrant + SQLite
                              ↑
                         Regex article/clause splitting
                         (NOT fixed-token chunking)
```

### Queries (via skill or API)

```
Question → SQLite FTS5 (exact terms) ─┐
         → Qdrant (semantic) ─────────┤
         → Serper (web fallback) ──────┤
                                       ▼
                              Merge + Dedup + Confidence
                                       │
                              ┌────────▼────────┐
                              │ DeepSeek API    │ (primary)
                              │ Groq API        │ (fallback)
                              └────────┬────────┘
                                       ▼
                              Answer with [Source: file, section]
```

## Key Decisions

### MarkItDown over Unstructured
MarkItDown (Microsoft, ★118k) handles docx + pdf in one library. Simpler dependency tree. Active maintenance.

### bge-m3 over OpenAI Embeddings
bge-m3 (19M downloads) is free, runs locally, 1024-dim. For 100k chunks, OpenAI embeddings would cost ~$0.50-2 (one-time) but adds cloud dependency. Local is better for privacy and $0 cost.

### Qdrant file mode over Docker
`QdrantClient(path=".")` creates a file-based database. No Docker, no server. Perfect for single-user Windows.

### DeepSeek over GPT-4o-mini
Same price tier ($0.14-0.15/1M tokens) but DeepSeek consistently better on legal Spanish text. Groq free tier as fallback for when DeepSeek is down.

### Streamlit over Open WebUI for non-technical users
Streamlit creates a simple search page (search box + results + sources). Open WebUI creates a ChatGPT-like chat. For lawyers searching legal documents, the search pattern is more natural than chat. Streamlit also requires zero configuration beyond `pip install streamlit`.

## Cost Calculator

```
Monthly cost = (queries/day × 30) × (avg_tokens_per_query × cost_per_token)

DeepSeek: $0.14/1M input + $0.28/1M output
Per query (~1000 input + 500 output): $0.00028
50 queries/day: $0.42/month

Groq llama-3.1-8b: $0.05/1M input + $0.08/1M output
Per query: $0.00009
50 queries/day: $0.14/month
```

## User-Facing Deliverables

When building this for non-technical users (lawyers, analysts):

1. **Streamlit app** (`app.py`) — single command: `streamlit run app.py`
2. **Windows .bat file** — double-click to launch: `RAG-Legal.bat`
3. **GitHub Pages** — professional docs at `{user}.github.io/{repo}/`
4. **Zero terminal after setup** — everything via browser

## Reference Implementation

See `github.com/mmansillaf/rag-legal-local` for a complete implementation of this pattern for legal documents (Word + PDF, 15k+ docs, Spanish).
