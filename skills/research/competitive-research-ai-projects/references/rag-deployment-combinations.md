# RAG Deployment Combinations — May 2026 Research Session

> Condensed findings from multi-source research on GitHub + Cloudflare + HuggingFace for RAG apps with HTML/PDF, SQLite, Qdrant, Neo4j.

## Key GitHub Repos Found

| Repo | Stars | Stack | Relevance |
|------|-------|-------|-----------|
| khuzama98/rag-ingestion-pipeline | 0 | Node.js, Ollama, Qdrant, Neo4j, OpenRouter | Ingesta PDFs → chunks → Qdrant+Neo4j, parallel search |
| guerinjeanmarc/pdf2neo4j-italian-tax | 0 | Python, Neo4j Aura, OpenAI | PDF → Neo4j jerárquico (Docs→Secciones→Chunks), legal entities |
| dannwaneri/vectorize-mcp-worker | 5 | Cloudflare Workers, D1, Vectorize, MCP | Production RAG on CF, $5/mes, hybrid search BM25+vector |
| ronit22203/ingestion-layer-graphrag | 0 | Python, Surya OCR, Qdrant, Docker | 5-stage PDF pipeline, full traceability |
| Sebuliba-Adrian/ResearcherAI | 0 | Python, Neo4j, Qdrant, Docker | Multi-agent RAG, 7 data sources, conversation memory |
| dead8309/ai-rag-crawler | 34 | Cloudflare Workers, Hono, Workflows | Automated web scraping → embeddings → Vectorize |
| RihanArfan/chat-with-pdf | 105 | NuxtHub, Cloudflare Workers | Chat with PDF deployed on CF |
| gnanaprakashmanikanti/DocMind | 0 | LangGraph, Qdrant, FastAPI, SSE | Agentic RAG with multi-hop reasoning |

## Cloudflare Pricing (app RAG ~50GB docs, ~100 queries/day)

| Service | Cost/mo |
|---------|--------|
| Workers Paid (base) | $5.00 |
| R2 50GB | $0.75 |
| Vectorize (~500K vectors, 3K queries) | ~$3.84 |
| Workers AI (embeddings + LLM) | ~$0.39 |
| D1 (metadata) | $0.00 |
| **TOTAL** | **~$9.98** |

Limitations: Workers 128MB RAM, 5min CPU, no Neo4j native, Vectorize max 1536d.

## HuggingFace Spaces Hardware

| Hardware | RAM | VRAM | $/h | $/mo (24/7) |
|----------|-----|------|-----|-------------|
| CPU Basic | 16GB | - | FREE | $0 |
| CPU Upgrade | 32GB | - | $0.03 | $21.90 |
| T4-small | 15GB | 16GB | $0.40 | $288 |
| L4 | 30GB | 24GB | $0.80 | $576 |
| A10G-large | 46GB | 24GB | $1.50 | $1,080 |

Limitations: 50GB disk non-persistent on free, no Neo4j/Qdrant local, Streamlit deprecated as built-in.

## Best Combination Strategy (lowest cost)

```
GitHub:       Code + CI/CD + Pages (docs)
Cloudflare:   Workers (API) + D1 (SQL) + R2 (PDFs) + Vectorize
              Total: ~$5-10/mo
HuggingFace:  Spaces Gradio (UI, free CPU)
Qdrant Cloud: Free tier (1GB, enough for ~21K 384d points)
Neo4j AuraDB: Free tier (200K nodes, 400K relationships)
Groq:         LLM via Batch API (~$5/mo)
              ─────────────────────────
              TOTAL: ~$10-15/mo
```

No Docker, no GPU, no servers needed. All cloud free tiers.
