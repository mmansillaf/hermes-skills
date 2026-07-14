---
name: rag-data-ingestion
description: "Ingest bulk document collections into a RAG system: PDF/DOC extraction, LLM batch processing (Groq/OpenAI Batch API), JSON repair, model benchmarking, and FAISS+BM25+Graph indexing."
version: 1.3.0
category: software-development
tags:
  - rag
  - ingestion
  - batch-api
  - groq
  - pdf-extraction
  - document-processing
  - faiss
  - bm25
  - networkx
  - evaluation
created: 2026-06-07
---

# RAG Data Ingestion Pipeline

Ingest large document collections (100K+) into a RAG system (FAISS + BM25 + NetworkX) using LLM batch APIs for structured content extraction. Covers the full pipeline: raw documents → text extraction → LLM batch processing → JSON repair → RAG indexing → evaluation.

## When to Use

- You have 10K+ PDF/DOC documents that need structured extraction (hechos, fallo, entidades)
- You want to use Groq/OpenAI Batch API for cost-effective bulk processing (~50% discount)
- You need to compare LLM models for extraction quality before committing to one
- You're building a RAG over legal/medical/academic documents with entity extraction

## Prerequisites

- **API Key**: Groq (`GROQ_API_KEY`) or OpenAI (`OPENAI_API_KEY`) with Batch API access
- **Text extraction**: `pdftotext` (poppler-utils), `catdoc`/`antiword` (for DOC files), `python-docx` (for DOCX)
- **RAG stack**: `faiss-cpu`, `sentence-transformers`, `rank-bm25`, `networkx`, `tqdm`
- **Storage**: ~200 MB free per 25,000 documents for JSONL files (temp), plus index storage

## Pipeline Overview

```
Raw PDFs/DOCs
    │
    ▼
1. TEXT EXTRACTION  ─── pdftotext (PDF), catdoc (DOC), python-docx (DOCX)
    │                 Truncate to 30K chars for Groq (128K context window)
    ▼
2. JSONL PREP       ─── Build JSONL with custom_id + request body
    │                 Max 200 MB per file, ~25K docs per file
    ▼
3. BATCH UPLOAD     ─── POST /v1/files → POST /v1/batches (Python requests)
│                 completion_window: "24h"
│
▼
4. MONITOR (+ CRON) ─── Hermes cronjob polling every 30 min
│                 **CRITICAL SETTINGS:**
│                 - Use `schedule: "every 30m"` (recurring), NOT `once in 30m` with `repeat: once`
│                   **One-shot cronjobs with past timestamps NEVER fire** if the scheduler wasn't
│                   active at that exact time. Always use recurring schedules for batch monitoring.
│                 - Set `deliver: origin` — `deliver: local` means output is invisible to the user
│                 - Set `workdir: /project/root` — scripts that need PYTHONPATH/core imports require it
│                 - Set `enabled_toolsets: ["terminal", "file"]` to minimize token usage
│                 0 fallos expected with max_tokens=1024
│                 See `references/groq-batch-monitoring.md` for curl commands, download workflow, and typical timing.
│                 See `references/batch-processing-stats.md` for real-world completion timing, yield, dedup, and cost data.
    ▼
5. **DOWNLOAD + PARSE** ─── GET /v1/files/{output_file_id}/content
    │                 Run `python3 scripts/analyze_batch_results.py output.jsonl --errors errors.jsonl`
    │                 Convert: `python3 scripts/convert_batch_outputs.py *.jsonl --output data_raw/rag_listo_batch_N.json`
    │                 
    │                 **ALTERNATIVE (manual mapping):** Some projects use a hardcoded `convertir_outputs.py`
    │                 with a `conversions` list. After each completed batch, add a new entry:
    │                 ```python
    │                 conversions = [
    │                     ('lote1a_12K_output.jsonl', 'rag_listo_batch_groq_12453.json'),
    │                     ('lote1b_12K_output.jsonl', 'rag_listo_batch_groq_12418.json'),
    │                 ]
    │                 ```
    │                 Run: `python3 convertir_outputs.py` — it handles dedup and field mapping.
    │                 See `references/groq-batch-monitoring.md` for details.
    │                 See `references/workflow-sequencing.md` for the full 8-phase sequence
    ▼
6. RAG INDEX        ─── FAISS (vector), BM25 (lexical), NetworkX (graph)
    │                 
    ▼
7. EVALUATE         ─── Query RAG, measure relevance, fallo concreto, leyes
```

## Choosing an Extraction Model

### Groq Batch API — Recommended Models

| Model | TPS | Cost Input/M | Cost Output/M | JSON Validity | Quality | Status |
|-------|:---:|:-----------:|:------------:|:-------------:|:-------:|:------:|
| **Llama 3.1 8B Instant** | 560 | $0.05 | $0.08 | **99-100%** | Good | **Production** |
| Llama 4 Scout 17Bx16E | 750 | $0.11 | $0.34 | 97-99% | Better | Preview |
| Llama 3.3 70B | 280 | $0.59 | $0.79 | 93-100% | Best | Production |
| Qwen3 32B | 400 | $0.29 | $0.59 | 0% (format issue) | N/A | Preview |

**Recommendation for bulk extraction: Llama 3.1 8B Instant** with `max_tokens=1024`:
- Cheapest ($51 for 562K docs via Batch API)
- 99-100% JSON validity with max_tokens=1024
- 8,000 docs/hr effective throughput

### max_tokens=1024 Fix

**Critical:** Set `max_tokens=1024` in the request body. With the default 512:

| max_tokens | JSON Validity | Reason |
|:----------:|:-------------:|--------|
| 512 | ~89% | Responses of ~550 tokens get truncated mid-JSON |
| 640 | ~99% | Most responses fit |
| **1024** | **99+%** | Max observed was 658 tokens; 1024 gives ample margin |

Cost is NOT affected — you only pay for tokens actually generated (~406 avg).

### capacity_exhausted Errors

**`capacity_exhausted`** is NOT a JSON quality error — it's Groq running out of capacity for that specific request. Expect **~0.3–4% failure rate** on large batches (no capacity guarantee from Batch API). Track separately from JSON parse failures:

```
Lote 1 (25K docs):   930/25000 = 3.7% → 24,070 útiles   (busy period)
Lote 2 (8K docs):    267/7935  = 3.4% → 7,668 útiles     (busy period)
Modern runs (2026-06): 150/57,934 = 0.3% → 57,784 útiles  (best observed)
```

Failed requests are **not retryable** within the same batch — they appear in `request_counts.failed`. Strategy: plan for ~96% yield per batch, process fail-later via a retry batch if coverage matters.

### Batch Overlap Dedup

**Critical: When you submit multiple Groq batches from overlapping source documents, the dedup rate against existing `processed_ids` can be extremely high (94%+).** This is NOT an error — it's expected when covering the same corpus across experimental runs or different batch configurations.

Example from a real campaign:
| Batch | Docs submitted | New after dedup | Dedup rate | Reason |
|:------|:-------------:|:---------------:|:----------:|:-------|
| Lote 1a | 12,500 | 12,443 | 0.4% | Fresh docs |
| Lote 2 | 25,000 | 935 | **96.3%** | Same source corpus as earlier batches |
| Lote 3 | 7,935 | 270 | **96.6%** | Same source corpus as earlier batches |

Estimate yield by checking `processed_ids` count before submitting batches. The dedup saves cost (you don't pay for re-processing) but means the time-to-value for additional batches diminishes quickly.

## JSONL Preparation

Each line is a complete request:

```json
{
  "custom_id": "LABORAL_000001",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "llama-3.1-8b-instant",
    "messages": [
      {"role": "system", "content": "Eres un asistente legal experto..."},
      {"role": "user", "content": "Analiza esta resolucion..."}
    ],
    "temperature": 0.1,
    "max_tokens": 1024
  }
}
```

**PITFALL: File size limit.** Groq accepts up to 200 MB per file. At ~7 KB per line (30K chars input), 25,000 docs = ~175 MB. Split into 25K-doc chunks.

### Extraction Prompt

The prompt must be explicit about JSON structure. Minimal prompt causes invalid JSONs:

```python
PROMPT_TPL = """Analiza esta resolucion judicial y genera un JSON con la siguiente estructura exacta:
{json_schema}

REGLAS:
- Extrae los hechos del CASO (lo que paso), no los fundamentos legales
- El problema es la CUESTION JURIDICA CENTRAL a resolver
- El fallo es la DECISION FINAL del tribunal (parte resolutiva)
- Si una entidad no existe en el texto, usa arreglo vacio []
- Normaliza nombres: quita tratamientos (Dr., Sr., etc.)
- Responde SOLO con el JSON, sin explicaciones ni bloques de codigo

TEXTO DE LA RESOLUCION:
{texto}"""
```

## JSON Repair (3 Strategies)

Not all LLM outputs parse cleanly. Use this fallback chain:

1. **Code block extraction** — If response contains ```json ... ```, extract the JSON block
2. **Regex find largest JSON** — Find all `{...}` substrings, pick the one with `resumen_fallo` key
3. **Truncate from last `}`** — Recursively trim from the last closing brace, try up to 20 attempts

```python
def reparar_json(raw):
    """3-strategy fallback JSON repair."""
    # Strategy 1: code blocks
    if "```" in raw:
        # Extract JSON from ``` blocks
        ...
    # Strategy 2: regex find valid JSON with fallo key
    matches = re.findall(r'\{[^{}]*\}', fixed)
    for c in sorted(matches, key=len, reverse=True)[:10]:
        try:
            p = json.loads(c)
            if "resumen_fallo" in p:
                return p
        except: pass
    # Strategy 3: truncate from last }
    for _ in range(20):
        lb = fixed.rfind('}')
        if lb > 0:
            try:
                return json.loads(fixed[:lb+1])
            except:
                fixed = fixed[:lb]
```

## Post-Completion: Convert Groq Output → Indexer Format

Once batch results are downloaded, convert the Groq output JSONL to the `rag_listo_batch_*.json` format the indexer expects. Use the bundled script:

```bash
python3 scripts/convert_batch_outputs.py \
    batch_results/batch_lote1_output.jsonl batch_results/batch_lote2_output.jsonl \
    --output data_raw/rag_listo_batch_groq_N.json
```

The script handles:
- **Field mapping**: Extracts `resumen_hechos`, `resumen_problema`, `resumen_fallo`, `entidades_clave.*` from the Groq response body
- **Deduplication**: Skips `id_documento` values already present in `data_raw/rag_listo_batch_*.json`
- **ID generation**: Uses MD5 hash of `custom_id` for deterministic, collision-free doc IDs
- **Graceful error handling**: Tracks parse errors, empty responses, and duplicates separately

**PITFALL: Don't use the raw custom_id as doc_id.** The indexer expects a hex string. Hash it with MD5 for a clean, deterministic ID.

### RAG Indexing

**IMPORTANT: Must set PYTHONPATH when running the indexer** because it imports from `core.config` and `core.embedding`:

```bash
cd /project_root
PYTHONPATH=. python3 pipeline/indexer.py             # incremental (resume from existing)
PYTHONPATH=. python3 pipeline/indexer.py --force      # fresh rebuild from scratch
```

**PITFALL: Indexer recovery after interrupted `--force`.** If you run `--force` and it's killed mid-way (timeout, power loss), the partial checkpoint (~3,000 docs per 600s with sentence-transformers) IS usable. Just restart WITHOUT `--force`:
```bash
PYTHONPATH=. python3 pipeline/indexer.py
```
This loads the existing checkpoint, skips already-processed doc IDs, and continues from where it left off. Do NOT re-run `--force` again — that discards all progress and starts from zero.

For large collections (50K+ docs), the indexer runs **~3h** and **must execute as a background process** to avoid timeout. Two patterns:

**Pattern A: Hermes background (recommended)**
```bash
# Via terminal tool with background=true + notify_on_complete=true:
terminal(command="cd /repo && PYTHONPATH=. python3 -u pipeline/indexer.py", background=true, notify_on_complete=true, timeout=7200)
```
Hermes alerts you when it finishes. Monitor intermediate progress with `process(action='poll', session_id='<id>')`.

**Pattern B: nohup (terminal-only)**
```bash
cd /project_root && PYTHONPATH=. nohup python3 -u pipeline/indexer.py > indexer_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Monitor progress periodically:
tail -f indexer_*.log        # watch live throughput (look for "doc/s" rate)
grep "✅" indexer_*.log       # check for completion message
```

Expected throughput: **~5 docs/s** with `distiluse-base-multilingual-cased-v2` (512d embeddings) on a consumer desktop. A 12K-doc batch takes ~40 min. For 50K docs, budget ~3h.

**PITFALL: Without `PYTHONPATH=.`, the import `from core.config import ...` fails with `ModuleNotFoundError: No module named 'core'`.**

### Data Format for Indexer

Each document after extraction must match this structure:

```json
{
  "id_documento": "md5_hash_16chars",
  "ruta_local": "/path/to/original.pdf",
  "contenido_a_vectorizar": {
    "hechos": "Sintesis objetiva...",
    "problema": "Cuestion juridica central...",
    "fallo": "Decision final del tribunal..."
  },
  "metadatos_graphrag": {
    "jueces_magistrados": ["Nombre del juez"],
    "demandantes_accionantes": ["Nombre del demandante"],
    "demandados_accionados": ["Nombre del demandado"],
    "leyes_y_articulos_citados": ["Ley X, Art. Y"],
    "conceptos_legales_clave": ["Concepto juridico"]
  }
}
```

Commands:
```bash
cd /repo && PYTHONPATH=. python3 pipeline/indexer.py --force
```

### Index Info

| Index | File | Purpose |
|-------|------|---------|
| FAISS | `data/indices/faiss_index_pro.bin` | Vector similarity search |
| BM25 | `data/indices/bm25_index_pro.pkl` | Lexical keyword search |
| NetworkX | `data/indices/graph_juris_pro.pkl` | Entity relationships (jueces, leyes, partes) |

## RAG Query Evaluation

After indexing, evaluate the query pipeline with a structured test. Two evaluation scripts are bundled:

### Option A: evaluate_rag_queries.py (quick, N questions)

Measures response time, citation rate, legal references, entity extraction, and follow-up generation:

```bash
cd /repo && PYTHONPATH=. python3 scripts/evaluate_rag_queries.py
```

Key metrics from a real run (10 questions, Llama 3.3 70B + Reranker MiniLM):
- Average time: **14.0s** per query
- Citations: **9/10 (90%)**
- Legal references: **10/10 (100%)**
- Follow-ups generated: **30/30 (100%)**

### Option B: templates/test_20_preguntas.py (deep, 20 questions + scoring)

A comprehensive evaluation that tests 20 questions across multiple legal areas (Laboral, Comercial, Civil) with per-question scoring on 8 quality dimensions. Each response is scored 0-10 based on:

| Criterion | Points | What it checks |
|-----------|:------:|----------------|
| Respuesta directa | 2 | First phrase answers the question, no intro generica |
| Citas de jurisprudencia (CAS., EXP., RTF) | 2 | Response cites actual case identifiers |
| Sin jerga tecnica | 1 | No "grafos, nodos, topologia, FAISS, BM25" |
| Longitud adecuada (100-600 palabras) | 1 | Not too short or too long |
| Seccion "Jurisprudencia citada:" | 1 | Has the required closing section |
| Respuesta sustantiva | 1 | Contentful response, not "informacion insuficiente" |
| Tiempo < 30s | 1 | Fast enough synthesis |
| Tono profesional | 1 | Not excessively markdown-heavy |

Configure the preguntas list at the top of the script to match your domain. Usage:

```bash
cd /repo && PYTHONPATH=. python3 templates/test_20_preguntas.py
```

Produces three reports:
- reports/test_N_preguntas_resumen.txt
- reports/test_N_preguntas_respuestas_completas.txt
- reports/test_N_preguntas_raw.json

**Real-world results** (77K documents, Llama 3.3 70B synthesis):
| Metric | Result |
|:-------|:------:|
| Overall score | 171/200 (85.5%) |
| Respuesta directa | 20/20 (100%) |
| Sin jerga tecnica | 20/20 (100%) |
| Con citas CAS./EXP./RTF | 7/20 (35%) — weakest metric |
| Tiempo promedio | 6.1s |

**PITFALL: Low citation rate is expected when documents lack identifiers.** If data_raw/ documents use hash-based doc_ids instead of real identifiers (CAS. N, EXP. N), the model has nothing to cite. Populate identificador in metadata_docs.json or include a CAS./EXP. field in the source data.

## Model Benchmarking Methodology

Compare models for extraction quality using Groq Batch API:

```
1. Prepare IDENTICAL JSONL for each model (same 100 documents)
2. Send all batches simultaneously
3. Download results, measure per model:
   - JSON validity rate (raw parse + after repair)
   - Tokens input/output actual vs estimated
   - Cost (real token counts × pricing)
   - Quality: % with concrete fallo, % with cited leyes
   - Latency (batch completion time)
```

Key quality metrics:
- **JSON directo** — % that parse without repair
- **JSON final** — % after repair strategies
- **Fallo concreto** — % where fallo is specific (>20 chars, not "No se proporciona")
- **Con leyes** — % that cite laws/statutes in entidades_clave.leyes

## Corpus Inventory & Cost Projection

Before starting a new extraction run, inventory the document collection to know exactly what remains. See `references/corpus-inventory.md` for:

- **Document type distribution** by folder (Sentencia, Resolución, Notificación, etc.)
- **Materia detection by filename pattern** (`-LA-` for LABORAL, `-CI-` for CIVIL, `-CO-` for COMERCIAL, `-FT-` for FAMILIA)
- **Processing priority** (LABORAL > COMERCIAL > FAMILIA > CIVIL > sin materia)
- **Cost projection** by materia using Groq Batch Llama 3.1 8B ($0.000088/doc)
- **Real batch timing data** (~3h for 25K docs)

Key technique: count `custom_id` prefixes in existing batch output files to track what's been processed per materia, then compare against the filesystem inventory to get exact remaining counts.

## Upload Script

Use `scripts/subir_batches.py` for reliable multi-file uploads via Python requests (avoiding shell curl quoting issues):

```bash
GROQ_API_KEY=gsk_... python3 scripts/subir_batches.py \
    batch_jsonl/lote_1a.jsonl batch_jsonl/lote_1b.jsonl \
    --labels "Lote 1a (LAB 12K)" "Lote 1b (LAB 12K)"
```

## Pitfalls

1. **JSON truncation at 512 tokens** — Always set `max_tokens=1024`. Observed max is 658 tokens.
2. **Prompt brevity causes failures** — Don't shorten the extraction prompt to save tokens. A shorter prompt produces more invalid JSONs.
3. **Batch API latency is unpredictable** — Groq Batch has a 24h window. Actual processing can be 2 min or 4 hours depending on load. Design for async.
4. **File handles leak** — PDF extraction with `pdftotext` per document is slow (~0.1s/doc). For 25K docs, budget ~40 min of preparation time.
5. **Model deprecation** — Preview models (Llama 4 Scout, Qwen3) can be removed without notice. Pin the model ID in config and check deprecation status: `console.groq.com/docs/deprecations`
6. **Cost estimation drift** — Actual tokens may differ from estimates by 30-50%. Base projections on real batch runs, not theoretical token counts.
8. **capacity_exhausted ~3-4%** — Groq Batch does not guarantee capacity for every request. On a 25K batch, expect ~900 failures. These are NOT JSON quality issues — track them separately. Plan to submit a retry batch or accept ~96% yield.
9. **Qwen3 32B via Groq Batch** — Returns responses in an incompatible format. Avoid for JSON extraction tasks.
10. **Symlinks vs actual docs** — Classification may create symlinks to PDFs in external drives. If the drive unmounts, symlinks break.
11. **Upload via shell curl `-F` quoting breaks** — The shell quoting issues with `-F file=@path` are severe enough to warrant using Python `requests` exclusively for file uploads. See `references/groq-batch-api.md` for the standalone upload script pattern.
12. **`PYTHONPATH` not set when running indexer** — The indexer imports from `core/` which requires `PYTHONPATH=.`. Without it, `ModuleNotFoundError: No module named 'core'` crashes immediately. Always prefix with `PYTHONPATH=.`.
13. **Prompt template matters for JSON validity** — The exact prompt template (`PROMPT_TPL`) with explicit JSON schema display and rules like \"no explicaciones ni bloques de codigo\" produces 99-100% JSON validity. A minimal prompt (\"extrae en JSON\") drops validity to ~70%. The critical elements are: (a) show the full JSON schema inline, (b) include the \"responde SOLO con el JSON\" instruction, (c) set `max_tokens=1024` even though average output is ~400 tokens. Template reference:
    ```python
    PROMPT_TPL = \"\"\"Analiza esta resolucion judicial y genera un JSON con la siguiente estructura exacta:
    {json_schema}
    REGLAS:
    - Extrae los hechos del CASO (lo que paso), no los fundamentos legales
    - El problema es la CUESTION JURIDICA CENTRAL a resolver
    - El fallo es la DECISION FINAL del tribunal (parte resolutiva)
    - Si una entidad no existe en el texto, usa arreglo vacio []
    - Normaliza nombres: quita tratamientos (Dr., Sr., etc.)
    - Responde SOLO con el JSON, sin explicaciones ni bloques de codigo
    TEXTO DE LA RESOLUCION:
    {texto}\"\"\"
    ```

## Chunking Strategies for Legal Documents

When processing legal documents (sentencias, resoluciones), the naive truncation-by-position loses critical content — typically the **fallo (parte resolutiva)** at the end. Three strategies, from simplest to most complete:

### Strategy 1: Priorizar Fallo (single-pass, fast index)
Toma los **últimos párrafos** primero (donde está el fallo) y completa con el inicio del documento. Pierde los fundamentos del medio.

```
[inicio] [fundamentos...] → [RESUELVE] [S.S.] ✓
[contexto inicial]        → [RESUELVE] [S.S.] ✓
         [fundamentos medios...] ✗
```

Use when: you only need the case outcome + basic context for indexing, and throughput matters more than completeness.

### Strategy 2: Multi-pasada con Overlap (recommended for RAG)
Divide el documento en chunks de tamaño fijo (~4,000 chars) que **se solapan en ~500 chars**. Cada chunk se procesa por separado. El último chunk siempre contiene el fallo.

```
Chunk 1: [inicio...              ...fundamento 1...]
Chunk 2:           [...fundamento 1...  ...fundamento 2...]
Chunk 3:                                 [...fundamento 2...  ...RESUELVE...]
```

Benefits:
- No pierde información entre chunks
- El overlap evita cortar ideas en los bordes
- Documentos de cualquier tamaño producen N chunks
- Cada chunk se indexa independientemente en FAISS/BM25

### Strategy 3: Chunking Semántico por Párrafos
Detecta marcadores estructurales (RESUELVE, CONSIDERANDO, S.S., EXPEDIENTE, VISTOS) y **nunca parte un párrafo a la mitad**. Los chunks se alinean con la estructura natural del documento.

Implementation in `chunking_demo.py` (see `references/chunking-strategies.md`):
```python
def chunk_by_paragraphs(text, max_chars=4000, overlap=500):
    paragraphs = re.split(r'\n\n+', text)
    chunks, current, current_len = [], [], 0
    for p in paragraphs:
        p_len = len(p) + 1  # +1 for newline
        if current_len + p_len > max_chars and current:
            # Add overlap from previous chunk's tail
            chunks.append('\n\n'.join(current))
            overlap_text = current[-2:] if len(current) > 2 else current
            # New chunk starts with overlap
            current = list(overlap_text)
            current_len = sum(len(x) + 1 for x in current)
        current.append(p)
        current_len += p_len
    if current:
        chunks.append('\n\n'.join(current))
    return chunks
```

**PITFALL:** Legal PDFs extracted with `pdftotext -layout` often have irregular line breaks. Multi-line paragraphs may be split into separate lines. The regex `r'\n\n+'` detects paragraph boundaries in well-formatted text, but for court documents you may need section headers as boundaries instead.

## Reranker Integration (Cross-Encoder Post-Retrieval)

After hybrid retrieval (FAISS + BM25 → RRF fusion), add a **cross-encoder reranker** to eliminate false positives and re-rank candidates by actual query relevance. This is a local model (no API cost) that significantly improves response quality.

### Implementation Pattern

Insert after RRF fusion, before final doc selection:

```python
from sentence_transformers import CrossEncoder

# Lazy-loaded singleton
_RERANKER = None
def _get_reranker():
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _RERANKER

# In retrieval function: after RRF fusion, before final selection
if len(all_unique_docs) > top_k:
    reranker = _get_reranker()
    # Prepare pairs for reranker: (query, doc_text) for each candidate
    pairs = [[query, text[:1000]] for text in candidate_texts]
    scores = reranker.predict(pairs)
    
    # Re-rank by cross-encoder score
    scored = list(zip(doc_ids, scores))
    seen = set()
    unique_scored = []
    for did, sc in scored:
        if did not in seen:
            seen.add(did)
            unique_scored.append((did, sc))
    unique_scored.sort(key=lambda x: x[1], reverse=True)
    final_top_docs = [d for d, _ in unique_scored[:top_k]]
```

### Model Choice

| Model | Params | Language | Speed (GPU) | Quality |
|-------|:------:|:--------:|:-----------:|:-------:|
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | 22.7M | English | ~0.1s/batch | Good |
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | 44.9M | English | ~0.2s/batch | Better |
| `microsoft/Multilingual-MiniLM-L12-H384` | 22.7M | **Multilingual** | ~0.2s/batch | Best for Spanish |

**PITFALL:** The MS MARCO models are English-only. For Spanish legal text, a multilingual cross-encoder performs better, but any cross-encoder that ranks query-document relevance is still useful — the comparative ranking (docs A > B > C) is language-agnostic for the same query.

### Cost

Zero — runs locally on GPU (Quadro T1000 4GB handles MiniLM-L-6 easily). Adds ~0.5-2s per query depending on candidate count.

## Section Coverage Reporting

After each batch completes and is indexed, report **section/stage completeness** — not just raw doc counts. The user asks "qué secciones están completas con esto" and expects a breakdown by materia/tipo.

Source the info from how the batch was labelled when created:

| Batch Label | Materia | Docs | Status |
|:------------|:--------:|:----:|:------:|
| Lote 1a (LAB 12.5K) | LABORAL | 12,443 | ✅ Indexed |
| Lote 1b (LAB 12.5K) | LABORAL | 12,418 | ✅ Indexed |
| Lote 2 (LAB 25K) | LABORAL | 25,000 | ⏳ In progress |
| Lote 3 (COM+LAB 8K) | COMERCIAL+LABORAL | 7,935 | ⏳ Queued |

**Tri-level accounting**: When the user asks "cuántos documentos tenemos", distinguish three numbers:

1. **Docs in data_raw** (extraction outputs) — the register count from `convertir_outputs.py`
2. **Unique documents** (deduplicated across batches) — from `processed_ids` set
3. **Vectors indexed** (FAISS chunks) — from `index.ntotal` after chunking

These differ because: (a) batches overlap, so unique < raw total; (b) each document is chunked, so vectors > unique docs.

Example from a real campaign:
```
data_raw/ unique IDs: 63,859
New docs added this batch: 26,066
Total FAISS vectors after indexing: 76,302
NetworkX nodes: 123,519 (docs + extracted entities)
```

Structure the report as: **what's complete** (materia), **what remains**, and **total accumulated docs** after this batch.

### Example

```
LABORAL: ~49K docs indexados (Lotes 1a + 1b + previos)
COMERCIAL: ~8K docs (solo del batch original, falta Lote 3)
TOTAL: ~64K documentos únicos en FAISS + BM25 + Grafo
```

Use the batch naming convention (LAB, COM, etc.) to derive materia coverage without looking at individual documents.

When the user asks "how much and how long", use this estimation framework:

### Unit Cost (Llama 3.1 8B via Groq Batch API)

| Model | Input /1K tok | Output /1K tok | Avg input/doc | Avg output/doc | **Cost/doc** |
|-------|:------------:|:-------------:|:------------:|:-------------:|:-----------:|
| Llama 3.1 8B Instant | $0.00005 | $0.00008 | ~1,257 tok | ~322 tok | **$0.000088** |
| Llama 4 Scout 17B | $0.00011 | $0.00034 | ~1,257 tok | ~400 tok | **$0.00028** |
| Llama 3.3 70B | $0.00059 | $0.00079 | ~500 tok* | ~800 tok* | **$0.00093** |

*70B is used for query synthesis, not batch extraction. Different workload.

### Batch Throughput

- **Groq Batch effective rate**: ~135 docs/min (varies with load, 24h max window)
- **Typical completion**: 8-12h for 25K doc batch
- **capacity_exhausted rate**: ~3-4% (expect ~900 failures per 25K batch)
- **Useful yield**: ~96% (account for this in projections)

### Time Projection Formula

```
prep_time = docs * 0.1s/doc (PDF text extraction)
groq_time = docs / 135 / 60 (minutes, typically 8-12h real)
index_time = docs / 33 (seconds, ~25 min per 50K docs)
total_elapsed = max(8h, groq_time)  # dominated by batch window
```

### Cost Projection Formula

```
cost = docs * 0.000088  # for Llama 3.1 8B
cost_estimate_high = cost * 1.3  # 30% buffer for token variance
```

### Corpus-Level Estimation Example

| Corpus | Docs | Cost | Time | Batches |
|--------|:----:|:----:|:----:|:-------:|
| Single materia (50K) | 50,000 | $4.40 | ~10h | 2 |
| LAB+COM+FAM (79K) | 79,000 | $6.95 | ~15h | 4 |
| Full Sent+Res (435K) | 435,000 | $38.28 | ~3d | 18 |
| Complete corpus (558K) | 558,000 | $49.10 | ~4d | 24 |

## Vector Store Format

Each document is chunked at 512 tokens with 50-token overlap. The vector store index maps:
- `metadata_docs.json` — Original HTML documents (if migrating from HTML corpus)
- `rag_listo_batch_groq_N.json` — New documents processed via Groq Batch (N = count)

When running indexer with `--force`, only files in `data_raw/` are ingested. Keep archives in `data_raw_old/`.
