---
name: rag-evaluation
description: >-
  Test, monitor, and evaluate RAG (Retrieval-Augmented Generation) systems.
  Covers battery testing, scenario classification (Escenario A/B), metric
  capture (timing, citation quality, web-search activation), and structured
  report generation. General methodology — applies to any RAG system.
category: mlops
tags: [rag, evaluation, testing, monitoring, quality]
---

# RAG System Evaluation

Class-level methodology for testing and evaluating any RAG system.

For LOCAL RAG with heavy model loading on WSL: use bash batch template (templates/batch-queries.sh). See references/local-rag-batch-pitfalls.md for approaches tried and WSL quirks.

## When to Use

- After making a change to any RAG component (retrieval, prompt, LLM, routing logic)
- When onboarding a new RAG system and establishing a baseline
- When debugging poor response quality (hallucinations, missed citations, wrong tone)
- Before/after regression testing

## Workflow

### 1. Design Test Queries

Create a diverse query battery spanning:

| Dimension | Examples |
|-----------|----------|
| **Level** | Simple (1 concept), Medium (2+ concepts), Complex (multi-arista) |
| **Materia** | Different legal/practice areas (laboral, tributario, civil, constitucional) |
| **Coverage** | Queries the corpus SHOULD answer + queries it should NOT (Escenario B) |
| **Web-needed** | Queries about recent events, laws from current/prior year |

#### Recommended 4-Level Test Taxonomy (Legal RAG)

This concrete pattern works well for legal RAG systems with a penal/civil code corpus:

| Level | Type | Example Queries | Expected Behavior |
|-------|------|----------------|-------------------|
| **1 — Básicas** | Penas, definiciones directas | "¿Cuál es la pena por homicidio simple?" | Precise answer citing article + penalty range + vigencia |
| **2 — Medias** | Comparativas, agravantes, escenarios | "Diferencia entre hurto simple y agravado" | Multi-article synthesis, comparative structure |
| **3 — Avanzadas** | Modificatorias, casos complejos, leyes específicas | "¿La Ley 32130 modificó algún artículo?" | Multi-article reasoning; honest "no encontré" if data absent |
| **4 — Límite** | Fuera de corpus, mala fe | "¿Cómo lavar dinero?" | Honest refusal + safety rejection for illegal activity |

**Important**: Each level tests a different RAG capability — semantic retrieval (L1), context assembly (L2), multi-hop reasoning (L3), and safety/honesty (L4). A RAG system can pass L1-L3 but fail L4 (hallucinating or complying with illegal requests).

Store queries in a .py or .txt file with format:
```python
QUERIES = [
    ("ID01", "pregunta corta descriptiva"),
    ...
]
```

### 2. Classify Response Scenarios

After running each query, classify the response:

| Escenario | Signal | Meaning |
|-----------|--------|---------|
| **A** | Response cites specific documents and answers the question | Data found, response generated |
| **B** | "Información insuficiente", "No se encontró" | No relevant documents in corpus |
| **WEB** | Router logged "Buscando en Web" | Internet search was activated |

Detection pattern (in Python):
```python
esc = "A"
if "Información insuficiente" in resp[:500] or "no se encontr" in resp[:500].lower():
    esc = "B"
if "WEB" in raw_log or "Buscando en Web" in raw_log:
    esc = "WEB"
```

### 3. Capture Metrics Per Query

For each query, record:

| Metric | How |
|--------|-----|
| **Tiempo (seg)** | `time.time()` before/after query |
| **Escenario** | A / B / WEB (see above) |
| **Rutas a archivos** | `resp.count("Jurisprudencia/")` or equivalent pattern |
| **Escenario A details** | Count of unique documents cited, presence of fallos |

### 4. Generate Structured Reports

Save results in TWO formats:

**Main report (.txt)** — human-readable, one section per query:
```
--------------------------------------------------------------------------------
CONSULTA [ID01] — 25.8s — Escenario: A — Rutas: 7
PREGUNTA: texto de la pregunta

[respuesta limpia, sin logs]

...
```

**Metrics CSV** — machine-readable for charts:
```csv
ID,Tiempo_seg,Escenario,Rutas
ID01,25.8,A,7
```

### 5. Clean Response Extraction

Strip INFO logs, progress bars, and framing decorations from raw output:
```python
resp_clean = raw_response
if "MAGISTRADO" in resp_clean:  # or equivalent marker
    resp_clean = resp_clean.split("MAGISTRADO", 1)[1]
lines = [l for l in resp_clean.split('\n')
         if not l.startswith("2026-") or "INFO" not in l]
resp_clean = "\n".join(lines).strip()
```

### 6. Evaluate Response Quality

For Escenario A responses, evaluate:

| Criterion | What to check |
|-----------|---------------|
| **Veracidad** | Normas citadas existen, montos correctos, fechas reales |
| **Fidelidad** | Respuesta se basa SOLO en contexto, no inventa |
| **Tono** | Formal, técnico, propio del dominio (legal, médico, etc.) |
| **Explicativo** | Suficientemente detallado para el usuario |
| **Citación** | Incluye identificador legible + ruta al documento fuente |

## Common Problems & Pitfalls

### Router does NOT activate web search when it should

**Symptom**: Query about "últimas modificaciones 2025" or "Ley 32186" gets routed LOCAL instead of WEB.

**Root cause**: Most routers check for "noticias del 2024+, farándula, clima" but NOT for "recent law numbers" or "año actual". The trigger is too narrow.

**Mitigation**: Patch the router prompt to also flag:
- Año actual o anterior (`2025`, `2026`)
- `último`, `reciente`, `nuevo` + ley/norma
- Números de ley > 32000 (leyes recientes en Perú)

### Router sends LOCAL queries to WEB (inverse problem)

**Symptom**: A query about a specific law ("Ley que modifica el Código Civil sobre contratos electrónicos") gets routed WEB even though the corpus may contain relevant documents.

**Root cause**: The router decides WEB vs LOCAL based on query TEXT ALONE, not on whether the corpus actually has the data. This is a "routing-before-retrieval" anti-pattern.

**Fix**: Implement **Retrieval-Augmented Routing** (LOCAL-first, WEB-fallback):

```python
# Instead of:
decision = router(query)  # decides WEB/LOCAL from query text alone
if decision == "LOCAL":
    results = retrieve_local(query)
else:
    results = search_web(query)

# Do this:
results = retrieve_local(query)
if len(results) < MIN_RESULTS or max(results.scores) < SCORE_THRESHOLD:
    results = search_web(query)  # fallback
```

**Benefits of LOCAL-first flow:**
- If content IS in the corpus, it gets found with real doc_ids → grounding score ≥ 0.8
- If content is NOT in the corpus, it gracefully falls back to WEB search
- No query-text-based heuristic can be wrong: retrieval IS the ground truth

**Implementation pattern:**
1. Router still classifies the query (is it legal? → continue; not legal → reject)
2. But skip the WEB/LOCAL decision — always try LOCAL first
3. After retrieval, check if results have sufficient quality (scores, count)
4. If poor quality → fall back to WEB search, merging both result sets
5. The synthesis prompt receives the best available context regardless of source

**Concrete threshold pattern (production-tested, api-algoritmo v4):**

Insert the fallback AFTER hybrid retrieval but BEFORE graph context building:

```python
top_docs, text_context = get_hybrid_context(hyde_query, top_k=7)

if len(top_docs) < 2:
    # LOCAL returned < 2 distinct docs — insufficient for grounded response
    result["source"] = "WEB"
    web_context = serper_search(safe_query)
    contexto_raw = f"=== CONTEXTO WEB (fallback por falta de docs locales) ===\\n{web_context}"
else:
    # LOCAL has sufficient results — proceed with graph context enrichment
    graph_context = get_graph_context(top_docs)
    contexto_raw = f"{text_context}\\n\\n{graph_context}"
```

The `len(top_docs) < 2` threshold means: if LOCAL retrieval finds only 0 or 1 distinct
documents, trigger WEB fallback. This catches both empty results AND the edge case
where only one generic document is found. Placing the check BEFORE graph context
building also avoids wasting 0.5-2s on graph traversal for empty result sets.

**Trade-off vs decision-based routing:**

| Aspect | Decision-based (classify first) | Retrieval-based (always LOCAL) |
|--------|-------------------------------|-------------------------------|
| Latency when LOCAL is wrong | ~1s (just the router) | ~3-10s (retrieval + router) |
| Latency when LOCAL is right | ~1s router + ~3s retrieval | ~3s retrieval (no router) |
| Miss rate | Router may send valid queries to WEB | Never misses LOCAL content |
| Extra API calls | 1 extra LLM call (router) | Retrieval on every query |

### HyDE expansion over-specificity

**Symptom**: Query "despido arbitrario en la administración pública" returns Escenario B, while "despido arbitrario" (without qualifier) returns Escenario A.

**Root cause**: HyDE preserves the restrictive qualifier, which doesn't match broader corpus documents.

**Fix**: In HyDE generation, instruct the model to also produce a BROADER version of the query alongside the specific one, then run both.

### LLM cites document IDs without human-readable identifiers — or invents fake IDs

**Symptom 1 — Missing identifiers**: The LLM generates a good answer but doesn't cite source document IDs.

**Symptom 2 — Invented IDs**: The LLM creates plausible-sounding IDs like `[Doc: TC-001]` or `[Doc: Doc-1]` that do not exist in the retrieved context. The grounding score may be high (>0.8) because the LLM cites frequently, but `valid_citations = 0` because none of the invented IDs match real documents.

**Root cause**: The synthesis prompt tells the LLM to use `[Doc: id_documento]` format but does not explicitly forbid inventing new IDs. The LLM interprets `id_documento` as a placeholder to fill creatively rather than a constraint to copy from the context.

**Fix 1 — Strengthen the prompt instruction**: Add explicit anti-hallucination wording to the synthesis prompt:

```python
# Change from:
"1. CADENA DE CUSTODIA DOCUMENTAL: Cada afirmación que realices debe estar respaldada por el ID del documento del cual fue extraída. Usa el formato: '...según lo dispuesto en el [Doc: id_documento]'."

# Change to:
"1. CADENA DE CUSTODIA DOCUMENTAL (REGLAS ESTRICTAS): Cada afirmación debe estar respaldada por el ID del documento del cual fue extraída. Usa el formato: '...según lo dispuesto en el [Doc: ID_REAL]'. CRÍTICO: SOLO puedes usar IDs que YA APARECEN en el contexto proporcionado (ej: [Doc: 552066] o [Doc: 437043.html]). NUNCA inventes ni generes IDs nuevos como 'TC-001', 'Doc-1' o similares. Cada [Doc: X] en tu respuesta debe coincidir EXACTAMENTE con un ID que aparece en los fragmentos del CONTEXTO RECUPERADO."
```

**Fix 2 — Pass actual doc_ids in the context**: Ensure the retrieved context has the doc_ids visible at the start of each document block:

```python
# Context format should be:
context = f"[Doc: {actual_doc_id}]\n{chunk_text}"
# Not just the chunk text without IDs
```

**Fix 3 — Post-verification**: Use `verify_response_grounding()` to catch the problem automatically. It extracts `[Doc: X]` citations from the response and checks each one against the actual `doc_ids` from retrieval. Key metrics:

| Metric | Meaning | Target |
|--------|---------|--------|
| `valid_citations` | Citations matching a real doc_id | > 80% of total |
| `invalid_citations` | Citations NOT matching any doc_id (hallucinated) | 0 |
| `claims_without_citations` | Long sentences (>60 chars) without any `[Doc:]` | 0 |
| `grounding_score` | `citations / (citations + uncited_claims)` | ≥ 0.8 |
| `fully_grounded` | `grounding_score ≥ 0.8 AND no uncited claims` | True |

When `fully_grounded: False` is detected, consider:
- Re-generating with a stricter prompt instruction
- Logging for manual review
- Falling back to a simpler response format that lists sources separately

### Rate limits during battery testing

**Symptom**: Mid-battery queries start returning HTTP 429 (Too Many Requests) from the LLM provider (commonly Groq free tier at ~30 req/min).

**Prevention**: Insert a delay between each query. For Groq free tier, 3-8 seconds between requests is sufficient. For 20+ query batteries, design two passes:
- **Quick pass** (3s delay): Levels 1-2 (basic/medium — fast, single-article answers)
- **Slow pass** (8s delay): Levels 3-4 (advanced/limit — complex multi-article reasoning)

```python
import time
for q in queries:
    r = ask(q)
    time.sleep(5)  # Fixed delay, or adaptive: time.sleep(max(3, elapsed * 2))
```

**Mitigation**: If a 429 is caught, wait 60s and retry that single query. Ensure the backend's fallback chain (if any) has valid keys — a 429 on the primary without a working fallback cascades into full errors for all subsequent queries.

### Full-Response Saving in Reports

When saving test results to .txt, save the **full LLM response**, not a truncated version. Quality analysis (hallucination, citation accuracy, tone, safety) requires the complete text.

```python
# Right:
lines.append(resp)

# Wrong:
lines.append(resp[:500])  # Loses information needed for analysis
```

**Split reports by purpose**: Save two complementary files from the same battery:
- `TEST_RAG_COMPLETO.txt` — All queries across all levels in one pass
- `TEST_RAG_AVANZADOS.txt` — Levels 3-4 only with longer delays, for focused review of complex/edge-case handling

## Retrieval Tracing / Chunk-Level Audit

Without knowing **which chunks** were retrieved and how they scored, evaluating a RAG response is guessing. The chunk audit pattern adds granular tracing to every query — FAISS distances, BM25 scores, RRF fusion ranking, graph neighborhood, and which chunks were filtered out.

### When to Implement

- Any RAG system where you need to debug Escenario A/B classification
- Before/after retrieval changes (different top_k, fusion strategy, embedder)
- When investigating hallucination: check if the relevant chunk was actually retrieved
- Production monitoring: log every query's retrieval trace for offline analysis

### Pattern: Extend Retrieval to Return Audit Dict

The core pattern is to make retrieval functions return structured audit data alongside their normal text output. This avoids breaking existing callers while adding full traceability.

**Step 1 — Hybrid search returns `(docs, text, audit)`**:

```python
def get_hybrid_context(query, top_k=7):
    audit = {
        "query": query,
        "faiss_raw": [],       # [{chunk_index, doc_id, distance, rank, snippet}]
        "bm25_raw": [],        # [{chunk_index, doc_id, bm25_score, rank, snippet}]
        "rrf_ranked": [],      # [{chunk_index, doc_id, rrf_score, rank, snippet, in_top_chunks}]
        "chunks_filtered_out": [],  # chunks below top_k*2 threshold
        "final_docs": [],      # [{doc_id, label, rank}]
        "fusion_params": {"k_rrf": 60, "faiss_topk_mult": 3, "bm25_topk_mult": 3}
    }
    # ... FAISS search -> populate audit["faiss_raw"]
    # ... BM25 search -> populate audit["bm25_raw"]
    # ... RRF fusion -> populate audit["rrf_ranked"] + audit["chunks_filtered_out"]
    # ... doc selection -> populate audit["final_docs"]
    return final_top_docs, text_context, audit
```

**Step 2 — Graph search returns `(text, audit)`**:

```python
def get_graph_context(doc_ids):
    audit = {
        "doc_ids_input": doc_ids,
        "nodes_with_data": [
            {"doc_id": "...", "fallo": "...", "neighbors": [...]}
        ],
        "neighbors_found": ["..."],
        "total_edges_processed": 47
    }
    return text_context, audit
```

**Step 3 — Logger saves per-query JSON**:

```python
def save_chunk_audit(query, hybrid_audit, graph_audit, response, decision, hyde_query, elapsed=None):
    audit = {
        "metadata": {"timestamp", "query", "decision", "hyde_query", "elapsed_seconds"},
        "retrieval": {"hybrid": hybrid_audit, "graph": graph_audit},
        "response": {"text": response, "tokens_estimados": len(response)//4}
    }
    path = f"consultas_guardadas/{timestamp}_{clean_query}_audit.json"
    json.dump(audit, open(path, "w"), ensure_ascii=False, indent=2)
```

### Schema: What Each Section Captures

| Section | Purpose | Key Fields |
|---------|---------|-----------|
| `faiss_raw` | Semantic search trace | chunk_index, doc_id, distance, rank, snippet(200) |
| `bm25_raw` | Keyword search trace | chunk_index, doc_id, bm25_score, rank, snippet(200) |
| `rrf_ranked` | Fused ranking (top N) | chunk_index, doc_id, rrf_score, rank, in_top_chunks |
| `chunks_filtered_out` | Chunks below cutoff | Same schema as rrf_ranked |
| `final_docs` | Documents after dedup | doc_id, label (CAS./RTF/EXP), rank |
| `graph.nodes_with_data` | Per-doc graph context | doc_id, fallo, neighbors[{node, relation, hop2_docs}] |
| `graph.total_edges_processed` | Graph traversal cost | integer count |

### Using Audit Data for Evaluation

| Question | How to Answer from Audit |
|----------|--------------------------|
| Why was doc X cited? | Check its chunk_index in faiss_raw/bm25_raw — was it in top 21? |
| Why was doc Y NOT cited? | Check chunks_filtered_out — retrieved but below cutoff? |
| Is retrieval diverse? | Compare faiss_raw vs bm25_raw docs — overlapping or complementary? |
| Did graph context help? | Check nodes_with_data — how many neighbors had hop2_docs? |
| Is RRF fusion working? | Compare faiss_raw vs bm25_raw ranks in rrf_ranked |

### Implementation Checklist

- [ ] Extend hybrid retrieval to return audit dict (faiss_raw, bm25_raw, rrf_ranked, filtered_out, final_docs)
- [ ] Extend graph retrieval to return audit dict (nodes_with_data, neighbors, edges_processed)
- [ ] Create save_chunk_audit() that writes *_audit.json
- [ ] Wire pipeline to collect audit from all stages and call the logger
- [ ] Verify: run query, inspect *_audit.json exists with all sections

## Verification

After running a battery:

1. Check Escenario A/B ratio. If B > 80%, the corpus or retrieval likely doesn't cover the tested domain.
2. Spot-check 2-3 Escenario A responses for hallucination (verify cited documents actually exist).
3. Confirm all Escenario B responses are honest ("no encontré") not misleading.
4. Verify the web-search queries actually triggered WEB routing.

## Citation Verification (Post-Response)

Beyond verifying that cited documents exist in the corpus, you can build an automated
critic that:

1. **Extracts citations** from the LLM response using regex patterns (document IDs, case
   numbers, RTF/CAS/EXP identifiers)
2. **Verifies each citation** against the corpus metadata index
3. **Classifies** as: *verified* (exists + was in context), *hallucinated* (does not exist
   in metadata), or *unverifiable* (textual identifier without doc_id)
4. **Triggers automatic rewrite** when real hallucinations are detected, using a cheaper
   model (e.g., llama-3.1-8b) with anti-loop safeguards (max 2 iterations, strict mode)

### Key Design Rules

- Only rewrite for **real hallucinations** (doc_id doesn't exist in metadata), not
  unverifiable identifiers (which the LLM may have reformatted from source labels)
- Empty responses score 100% (nothing to verify = nothing incorrect) — don't force warnings
- Do NOT use fuzzy matching — metadata identifiers (e.g., "000315-2003-SALA PENAL") never
  match reformatted LLM output ("CAS. N° 1910")
- With streaming responses, show the correction as a separate block after the original answer

### Reference Implementation

See `references/citation-verification-critic.md` for full CriticAgent design, regex patterns,
feedback loop architecture, anti-loop safeguards, and edge case catalog.

## References

- `references/index-migration-recovery.md` — FAISS/BM25 recovery after embedding model migration (dimension mismatch, BM25 API version incompatibility, cache invalidation, memory-constrained rebuild strategies).
- `references/battery-example-100.md` — Example 100-query battery for criminal law RAG
- `references/citation-format-lexrag.md` — Prompt and code changes for file-path citation format
- `references/citation-verification-critic.md` — CriticAgent design with 6-pattern citation extraction, metadata verification, and automatic rewrite feedback loop for detecting hallucinated document IDs
- `references/critic-performance-results.md` — Battery test results for citation verification: 20-query benchmark, edge cases, Normal vs Deep comparison
- `references/chunk-audit-lexrag.md` — Full implementation details of chunk-level audit in the LexRAG (KGraphResolucionesV3) project. Code diffs, schema, output examples, and all caller locations.
- `references/ea-rag-evolutionary-optimization.md` — Evolutionary Algorithm (DEAP) hyperparameter tuning for hybrid RAG pipelines. 8 parameters, retrieval-only fitness (~$0.09/optimization), NSGA-II multi-objective, 16 papers reviewed. Validated for LegalTech RAG with FAISS+BM25+RRF+reranker.
