# Multi-Agent GraphRAG — Reference Architecture

**Project:** KGraphResolucionesV3 (Lex RAG Pro)
**Corpus:** 64,186 resoluciones peruanas (Tribunal Fiscal, Corte Suprema, Tribunal Constitucional)
**Stack:** FAISS + BM25 + NetworkX + DeepSeek V4 Flash + Groq

This is a reference example of a production-grade multi-agent GraphRAG system for legal document retrieval. Useful for comparing architectures or understanding how agents decompose the RAG pipeline.

## Agent Breakdown

| Agent | Role | LLM? | Trigger |
|-------|------|------|---------|
| **Router** | Classifies query as LOCAL (jurisprudence) or WEB (news) | Yes (Groq) | Every query |
| **Retrieval Strategist** | Sets top_k, retrieval mode, graph depth | Yes (Groq llama-3.1-8b) on ambiguity; hard rules otherwise | Every LOCAL query |
| **Graph Analyst** | Counts frequencies, builds precedent chains | No (pure NetworkX) | Every LOCAL query |
| **Critic** | Verifies citations against corpus, detects hallucinations | No (regex + metadata index) | After generation (up to 2 feedback loops) |
| **Synthesizer** | Generates final response + follow-up questions | Yes (DeepSeek V4 Flash, fallback Groq) | After retrieval |

## Pipeline Flow

```
User Query
  └─ Router → LOCAL or WEB
       ├─ WEB:  Serper API → raw context
       └─ LOCAL:
            ├─ Strategist → top_k, mode, graph_depth
            ├─ HyDE Expansion
            ├─ FAISS (semantic) + BM25 (lexical) → RRF fusion → top docs
            ├─ Graph Analyst → entity counts, precedent chains
            └─ LLM (DeepSeek V4 Flash → Groq fallback chain)
                 ├─ Synthesizer → streaming dictamen
                 └─ Critic → feedback loop (up to 2x re-write on hallucination)
```

## Key Design Decisions

- **Hybrid search (FAISS+BM25)** with RRF fusion for balanced recall. FAISS handles semantic similarity, BM25 catches exact keyword matches (critical for legal article/code references).
- **No LLM in Graph Analyst** — all counts and frequencies are algorithmic. The graph traversal is purely NetworkX; the LLM only reads the formatted output.
- **Critic is regex-based, not LLM-based** — citation verification uses 6 regex patterns (EXP, CAS, RTF, doc_id paths, bare HTML filenames, 6-7 digit numbers) against a metadata index. This avoids the cost and latency of an LLM call for verification.
- **Provider fallback chain**: DeepSeek V4 Flash → Groq llama-3.3-70b → kimi-k2 → mixtral → llama-3.1-8b. Each fallback is a separate try block with retry.
- **Router uses Groq (not DeepSeek)** because routing decisions need low latency and the llama-3.1-8b is sufficient for binary classification.

## Ingestion Pipeline (Design)

The ingestion step converts raw HTML resolutions into searchable indices. In the KGraphResolucionesV3 codebase, ingestion exists in two variants:

**Variant A (simple, `graphrag_console.py`):**
1. Source: `data_raw/rag_listo_batch_*.json` — produced by a separate Groq Batch API pipeline that parsed each HTML into structured fields (hechos, problema, fallo, jueces, leyes, partes)
2. Chunking: 512 words with 50 overlap
3. Embedding: `sentence-transformers/distiluse-base-multilingual-cased-v2` (CPU)
4. FAISS: `IndexFlatL2` with L2 normalization
5. NetworkX graph: builds nodes (Documento, Juez, Actor, Demandado, Ley) and edges (JUZGADO_POR, DEMANDADO_POR, DEMANDA_A, CITA_LEY)
6. Outputs: `faiss_index.bin` (8.8 MB, ~4,500 vectors), `faiss_meta.pkl` (4.6 MB, chunk metadata), `graph_juris.pkl` (6.0 MB, ~21,732 nodes)

**Variant B (Pro, `graphrag_pro.py` — incomplete in this repo):**
- Expects `pipeline/indexer.py` module which didn't exist on disk — the import was broken
- Expects an additional BM25 index (`bm25_index_pro.pkl`) for hybrid search
- This is a common recovery pattern: one entry point works (console), a more advanced one (Pro) has missing modules from a previous iteration

## Recovery Pattern: Repo with Missing Components

This repo exhibited a classic "advanced version has broken imports" pattern:
- `graphrag_console.py` (simple version) → fully functional with real indices on disk
- `graphrag_pro.py` (modular version with 4 agents) → imports `pipeline.indexer` which doesn't exist
- `core/config.py` references `bm25_index_pro.pkl` which doesn't exist on disk
- README references `scripts/data_prep/` which doesn't exist

The structured recovery approach (documented in Phase 3.75 of the `project-audit-and-reporting` skill) involves: tracing each broken import, cross-referencing expected vs actual index files, checking referenced-but-empty directories, assigning recovery priorities, and producing a searchable recovery file (ARCHIVOS_A_BUSCAR.txt).

- Understanding multi-agent RAG decomposition patterns
- Comparing retrieval strategies (hybrid vs semantic-only vs lexical-only)
- Architecture for legal/regulatory document retrieval
- Implementing citation validation without LLM costs
- Designing provider failover chains

## Related Skills

- `hermes-multi-model-routing` — configuring multiple LLM providers with failover
- `building-rag-systems-with-multiple-stores` — similar multi-index RAG architecture
