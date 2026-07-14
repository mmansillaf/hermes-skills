# Multi-Agent RAG Query Pipeline

Reference for the Router → Strategist → Search → Synthesizer → Critic pipeline.

## Agent Architecture

```
User Question
    │
    ▼
1. ROUTER (call router.py)
   Model: llama-3.3-70b-versatile (primary), 
          meta-llama/llama-4-scout-17b-16e-instruct (fallback)
   Task: Classify query as LOCAL (jurisprudence) or WEB (news/current events)
   Output: decision (LOCAL/WEB) + hyde (expanded query)
    │
    ▼
2. RETRIEVAL STRATEGIST (call retrieval_strategist.py)
   Task: Set adaptive retrieval parameters:
   - top_k: 3-15 (dynamic based on complexity)
   - mode: hybrid, semantic, lexical, or web
   - graph_depth: 0-3
   - hyde: enabled for complex queries
   Fallback: rule-based for simple queries, LLM for ambiguous ones
    │
    ▼
3. HYBRID SEARCH (FAISS + BM25)
   Task: Retrieve top-k documents from vector + lexical indices
   Parameters from Strategist
    │
    ▼
4. GRAPH ANALYST (graph_analyst.py, no LLM)
   Task: Traverse NetworkX graph for entity connections
   Finds: jueces, leyes, demandantes, demandados relationships
   Output: "=== ANALISIS DE PRECEDENTES Y CONEXIONES ===" narrative
    │
    ▼
5. SYNTHESIZER (synthesizer.py)
   Model: llama-3.3-70b-versatile (primary, via Groq)
          llama-4-scout-17b-16e-instruct (fallback)
          llama-3.1-8b-instant (last resort)
          deepseek-chat (secondary fallback via DeepSeek API)
   Task: Generate "Magistrado" response with citations
   Output: Structured legal analysis in Markdown
    │
    ▼
6. CRITIC (critic.py)
   Task: Verify every citation exists in the corpus
   Data sources: metadata_docs.json (HTMLs) + data_raw/rag_listo_batch_*.json (new docs)
   If hallucination detected → re-write response (up to 2 iterations)
    │
    ▼
7. RESPONSE + FOLLOW-UP QUESTIONS
```

## Configuration

### .env file
```
GROQ_API_KEY="gsk_..."
SERPER_API_KEY="..."       # For WEB queries (optional)
DEEPSEEK_API_KEY="sk_..."  # For fallback (optional)
```

### Model Priority
**Router:** 70B production first, Scout preview fallback
**Synthesizer:** Groq 70B → Groq Scout → Groq 8B → DeepSeek

### Citation Verification
The Critic loads from TWO sources:
1. `data/metadata_docs.json` (original HTML corpus, ~64K docs)
2. `data_raw/rag_listo_batch_groq_*.json` (new Groq-extracted docs, ~20K+)

## Running

```bash
cd /repo && PYTHONPATH=. python3 graphrag_pro.py
# Interactive mode: type queries, get responses with citations
```

For one-shot:
```bash
cd /repo && PYTHONPATH=. python3 graphrag_pro.py --query "mi consulta legal?"
```

## Pitfalls

1. **Router model deprecation** — The original router used `moonshotai/kimi-k2-instruct-0905` which was deprecated. Always check production models first.
2. **Critic metadata mismatch** — If the Critic can't find document IDs, it marks valid citations as "sospechosas". Make sure critic.py loads both old metadata and new JSONs.
3. **Synthesizer streaming** — The response is streamed character-by-character. If a model in the priority chain fails mid-stream, the fallback starts from scratch.
4. **Historial trimming** — Only the last 4 exchanges are kept (~8 messages). Long conversations lose early context.
5. **Top_k default** — Changed from 7 to 5 for faster responses. The Strategist can override this dynamically.
