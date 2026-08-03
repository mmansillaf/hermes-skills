---
name: lex-rag
description: LexRAG operational patterns — citation quality, batch testing, performance optimization, and dependency management for the ResumenTokensJurisprudencias project.
category: lex-rag
---

# LexRAG — Operational Patterns

Project: `/mnt/d/PyCode/LexRAG-Optimizado/`
Main entry point: `graphrag_pro.py` (CLI) or `api.py` (FastAPI server)
Venv: `venv/` (Windows Python 3.14, created from WSL using `/mnt/c/Python314/python.exe -m venv venv`)

## Trigger conditions

Load this skill when the user asks you to:
- Run queries against LexRAG (`graphrag_pro.py --query "..."`)
- Run batch tests or evaluations on the jurisprudential corpus
- Debug LexRAG output quality, citations, or performance
- Modify LexRAG's retrieval, synthesis, or agent pipeline
- Troubleshoot missing dependencies or venv issues
- **Design or build a new RAG system for legal documents** — also load `lexrag-audit-optimize` for sizing decisions (what components to include/exclude based on corpus size). See `references/lightweight-legal-search.md` for patterns on small-to-medium corpuses (<20K self-contained docs).
- **Evaluate a new document corpus for ingestion compatibility** — assess format, text extractability, metadata coverage, volume, and cost before modifying the pipeline. See "Adding new document sources" below.
- **Create a conversational/narrative legal query system** — where the audience is end-users, not lawyers. See `references/narrative-legal-rag.md` for the prompt pattern, tone guidelines, and full example interactions. The narrative mode produces responses with analogies, practical advice, and plain-language explanations — distinct from the formal legal analysis mode.
- **Extract structured metadata (materia, jueces, fechas) from legal documents** — use the hybrid regex+Groq pattern. See `references/lightweight-legal-search.md` section "Hybrid metadata extraction" and the SDD skill's "Hybrid Metadata Extraction Pattern".
- **Research citation validation rates and techniques** — load `lex-rag-chunk-audit`'s `references/citation-validation-research.md` for empirical rates (17-33% hallucination in commercial tools, FCR < 0.2% with advanced pipeline) and the 4-stage programmatic verification pattern. The indeterminate citations bypass in the CriticAgent feedback loop is documented there with the concrete fix.
- **Migrate or upgrade the embedding model** (e.g. distiluse → BGE-M3) — see `references/bge-m3-migration.md` for the full study. Also load `tc-searchrag` for a reference implementation of FAISS+BM25+RRF with lazy loading.
- **Evaluate whether to fine-tune embeddings** — see `references/embedding-finetuning-decision.md` for the baseline-first framework: upgrade to SOTA base model, add hybrid search and reranker, measure recall@10, only fine-tune if below 80%. Correct order is baseline-first, THEN measure, THEN decide — NOT fine-tune-first.
- **Diagnose which version of a project is current** when the user has multiple copies (e.g. LexRAG-Optimizado vs LexRAG-v2 vs lexrag-optimizacion). Use this exact workflow:
  1. `find /path/to/version1 -type f -name "*.py" ... | sort` on both directories
  2. Compare file sets: which has agents/, core/, retrieval/, pipeline/, utils/, tests/, data/?
  3. Check last-modified dates of module directories
  4. Diff specific files side by side: compare critic.py, graphrag_pro.py, core/config.py
  5. Confirm data presence: metadata_docs.json, data/indices/, number of saved queries
  6. Look for unique additions in each version (e.g. reranker.py, benchmark files)
  7. Recommendation: the version with complete data (metadata, indices, benchmarks) is production. The version without data but with new modules is experimental -- extract the new modules into production.

This skill covers the LexRAG project specifically. For general legal-RAG architecture decisions
(corpus sizing, when to include/exclude graph/critic/deep research, hybrid metadata extraction),
also load `lexrag-audit-optimize` which has the class-level patterns.

## Architecture quick reference (post-optimization, completed Jun 2026)

```
graphrag_pro.py          → CLI entry point, async query loop
api.py                   → FastAPI REST (POST /query, GET /health, GET /metrics)
agents/
  router.py              → HyDE query expansion + routing (WEB vs LOCAL)
  synthesizer.py         → LLM synthesis prompt + streaming + follow-ups
  critic.py              → Citation hallucination detection
  retrieval_strategist.py → Adaptive retrieval strategy (simple/media/compleja)
  graph_analyst.py       → NetworkX graph analysis for precedents
  deep_searcher.py       → Multi-query parallel search
retrieval/               ← CREATED Jun 2026 (was empty directory)
  hybrid_search.py       → FAISS + BM25 + RRF fusion + chunk formatting
  web_search.py          → Serper API web search
core/
  embedding.py           → Sentence-Transformer (distiluse-base-multilingual-cased-v2)
                         → Advanced: BAAI/bge-m3 via FlagEmbedding (see references/bge-m3-migration.md)
  llm_clients.py         → DeepSeek (primary) + Groq (fallback)
  config.py              → Paths, env vars, logging
  index_manager.py       → Singleton thread-safe (FAISS + BM25 + Grafo + metadata)
pipeline/                ← CREATED Jun 2026 (was missing entirely)
  indexer.py             → Ingestion: Jurisprudencia/*.html → FAISS + BM25 + NetworkX
utils/                   ← CREATED Jun 2026 (was missing entirely)
  query_cache.py         → MemoryCache con normalización de queries y TTL
  semantic_cache.py      → SemanticCache por similitud de embeddings (2 niveles)
  metrics.py             → MetricsCollector singleton (tiempos por fase, hit rate)
  logger_utils.py        → save_query_log + save_chunk_audit
```

**Modules created to close the "Optimized Copy Trap":** `retrieval/__init__.py`,
`retrieval/hybrid_search.py`, `retrieval/web_search.py`, `utils/__init__.py`,
`utils/query_cache.py`, `utils/semantic_cache.py`, `utils/metrics.py`,
`utils/logger_utils.py`, `pipeline/__init__.py`, `pipeline/indexer.py`.

## Legacy vs modern scripts (CRITICAL PITFALL)

The project has TWO query entry points. Using the wrong one gives wrong results:

| Script | Indices | TC docs? | Velocidad | Uso |
|--------|---------|:--------:|:---------:|-----|
| `graphrag_console.py` | `faiss_index.bin` (8.8 MB, old) | No | Lenta (legacy) | **NO USAR** |
| `consulta.py` | `faiss_index_pro.bin` (129 MB) | Si | Rapida (moderna) | **Recomendada** |
| `graphrag_pro.py` | PRO (via IndexManager) | Si | Rapida + historial | **Recomendada** |

`graphrag_console.py` es legacy: carga indices viejos (sin TC), no tiene BM25, y tiene su propio logging que NO silencia los HTTP requests de HuggingFace (mostrando los mensajes `307 Temporary Redirect`). Usar siempre `consulta.py` o `graphrag_pro.py`.

Los mensajes `HTTP Request: HEAD https://huggingface.co/...` aparecen SOLO en scripts legacy que no importan `core.config`. El logging en `core/config.py` ya silencia `httpx`, `httpcore`, `huggingface_hub` y `sentence_transformers`.

## Document citations: TC metadata mapping

La funcion `_doc_header()` en `retrieval/hybrid_search.py` busca identificadores en `data/metadata_docs.json` (HTML docs). Los TC PDFs tienen `doc_id` como `tc_00364-2022-AA.pdf` que no existen en ese archivo.

**Fix aplicado (Jun 2026):**

1. Creado `data/indices/tc_docs_metadata.json` — mapea `tc_NOMBRE.pdf` a `EXP. N.° XXXX-YYYY-ZZ/TC`. Generado desde `metadata.csv` del scraper (9,997 entries) + parseo de filename (1,223), cubriendo los 11,220 PDFs.

2. Modificado `_doc_header()` — agregado `_load_tc_metadata()` como fallback. Si el metadata principal no tiene el `doc_id`, revisa TC metadata antes de caer al filename raw.

**Antes:** `tc_00364-2022-AA.pdf` → cita muestra `**tc_00364-2022-AA.pdf**`
**Despues:** `tc_00364-2022-AA.pdf` → cita muestra `**EXP. N.° 00364-2022-AA/TC** | Tribunal Constitucional`

## Output format: saving query results

Preferencia del usuario: guardar resultados en **tres formatos simultaneamente**:

| Formato | Proposito |
|---------|-----------|
| `.json` | Datos estructurados reutilizables (campos: consulta, docs recuperados, tiempos, respuesta) |
| `.md` | Lectura formateada (Markdown con encabezados, separadores, citas) |
| `.txt` | Compatibilidad Windows / Notepad / script minimo (texto plano) |

Todos en `consultas_guardadas/` con timestamp unico: `prueba_N_consultas_<YYYYMMDD_HHMMSS>.{json,md,txt}`.

Usar siempre el script `scripts/run_N_consultas.py` que genera los 3 formatos automaticamente.

## Citation quality standard (USER REQUIREMENT)

**Every citation in a response MUST include the source filename as a verifiable path.**

Format expected by the user:
```
**EXP. N° 05591-2016** | Tribunal Constitucional | 📄 Jurisprudencia/440426.html
```

Do NOT accept citations that identify the case but omit the filename. The user wants to click/review the original document.

The synthesizer prompt (line 38 of `agents/synthesizer.py`) already says "Siempre incluye también la ruta al archivo fuente" but the LLM is inconsistent. The fix involves:
1. Making the source path more prominent in chunk headers (e.g., `📄 FUENTE: Jurisprudencia/XXXXX.html` on its own line in `retrieval/hybrid_search.py` line 210)
2. Hardening the synthesizer prompt with mandatory format requirement
3. Consider post-processing to inject missing paths by looking up in `metadata_docs.json`

## Batch testing workflow

When the user asks to run multiple test queries:

1. Use the `--query` flag for non-interactive mode
2. Save each response to `consultas_guardadas/<timestamp>_<id>_<nivel>.txt`
3. Generate a JSON resume with metadata per query
4. Use 3 difficulty levels: `simple` (factual), `medio` (interpretative), `complejo` (multi-part analysis)

**Performance pitfall**: Running via subprocess (one per query) reloads the Sentence-Transformer model each time (~80s/query). Total for 15 queries ≈ 36-45 minutes, of which ~20 minutes is just model reloading.

**Preferred approach**: Call `run_console_query()` directly in a shared Python process so the model loads once. The async generator output can be captured by monkey-patching `sys.stdout` instead of `contextlib.redirect_stdout` (which has compatibility issues with async generators).

**Battery test script pattern** (scripts/bateria_N_preguntas.py):
- Import components directly (NOT import graphrag_pro which triggers full model loading)
- Use `RetrievalStrategist`, `GraphAnalyst`, `DeepSearcher`, `CriticAgent` as module-level singletons
- Wrap the async pipeline in `async def ejecutar_consulta()` that calls components directly
- Track timing with `MetricsCollector`
- Save per-query responses + consolidated JSON report
- Use `python -u` flag or `flush=True` in prints when running background (Python buffers stdout without TTY)

**Quick speed-up**: Add `HF_TOKEN` to `.env` to avoid HuggingFace rate limiting on unauthenticated downloads.
```python
from core.index_manager import index_manager
from agents.router import route_query_and_hyde
from agents.synthesizer import generate_rag_synthesis
from retrieval.hybrid_search import get_hybrid_context
from agents.graph_analyst import GraphAnalyst
from agents.retrieval_strategist import RetrievalStrategist
from agents.deep_searcher import DeepSearcher

# Luego usar asyncio.run() con tu propia función que llama estos componentes
# NO usar run_console_query() que viene de graphrag_pro
```

Reference: `scripts/bateria_20_preguntas.py` for a complete standalone batch test.

### Metrics per query
- `num`, `nivel`, `pregunta`
- `tiempo_seg` (tiempo total)
- `palabras` (word count of response)
- `citas` (FUENTE: count)
- `critic.score` (1.0 = perfect, lower = more hallucination risk)
- `critic.hallucinated` (count of fabricated citations detected)

### Cache is not persistent between processes
The in-memory cache (`MemoryCache`, `SemanticCache`) resets on every Python restart.
Batch tests in separate processes start with 0 cached entries. For persistent caching,
implement the SQLite level-2 cache (see `utils/query_cache.py:SQLiteCache` which exists
but is not yet wired into the pipeline).

## Adding new document sources (corpus compatibility evaluation)

When the user asks to ingest a new set of documents into an existing legal RAG pipeline (LexRAG or similar), follow this evaluation methodology before modifying any code:

### 1. Format assessment

| Original pipeline expects | Check if new corpus matches |
|--------------------------|-----------------------------|
| HTML files → BeautifulSoup text extraction | PDF → needs PyMuPDF or marker-pdf |
| Filename as doc_id (e.g. `1014870.html`) | Descriptive filenames OK but need normalization |
| Plain text in `<body>` with minimal artifacts | PDFs may have headers/footers, page numbers, OCR garbage |

**Key questions:**
- Is the text extractable? (scanned == OCR needed, digital == direct extraction)
- What artifacts does the format introduce? (PDF: bars, repeated digits, watermark text)
- Does existing `requirements.txt` already have the needed library? (pymupdf is usually present in LexRAG projects)

### 2. Metadata inventory

| Field | Where it comes from | Critical? |
|-------|-------------------|-----------|
| Identificador legible (EXP/CAS/RTF) | Extracted from document content (regex) or pre-existing metadata | Yes—citations |
| Órgano / Sala | Document header or external API | Yes—filtering |
| Fecha | Document header or external metadata | Yes—temporal queries |
| Materia / Tipo | External metadata or LLM extraction | Nice-to-have |
| Demandante / Demandado | Pre-existing metadata or LLM extraction | Nice-to-have |

If the new corpus already has structured metadata (CSV, JSON, API), **convert it directly** instead of re-extracting with regex from documents. This is more accurate and avoids an unnecessary processing step.

### 3. Volume and cost estimation

```python
# Estimation formula for Groq Batch API
total_docs = 11224
avg_chars_short = 3000    # docs under threshold
avg_chars_long = 15000    # docs over threshold

# Hybrid strategy (same as original pipeline)
# ≤1000 tokens → Llama-3.1-8B ($0.0002/request avg)
# >1000 tokens → Llama-3.3-70B ($0.0011/request avg)

short_docs = total_docs * 0.2   # estimate 20% short
long_docs = total_docs * 0.8    # estimate 80% long

cost = short_docs * 0.0002 + long_docs * 0.0011  # ~$10 for 11K docs
time_hours = total_docs / 3000   # Groq Batch ~3000 docs/hour
```

**Real benchmarks (Jun 2026):** ~$0.0005/doc average, ~3000 docs/hour throughput.

### 4. What changes vs what stays (decision matrix)

| Pipeline step | Stays? | Change needed |
|--------------|:------:|--------------|
| Text extraction | ❌ | Replace BeautifulSoup(HTML) → PyMuPDF(fitz) |
| Batch JSONL generation | ❌ | New script or adapted function |
| Groq Batch processing | ✅ | Same API, same JSONL format |
| LLM prompt for extraction | ⚠️ | Adjust for document type (TC, Corte Suprema) |
| JSON result format | ✅ | Same schema (hechos, problema, fallo, entidades) |
| pipeline/indexer.py | ✅ | No changes needed |
| Metadata → metadata_docs.json | ⚠️ | Convert CSV/API data, not regex from docs |
| IndexManager | ✅ | No changes needed |
| retrieval/*.py | ✅ | No changes needed |

### 5. Local LLM vs API decision

When the user asks whether to run the extraction phase locally instead of API:

| Hardware | Local feasible? | Throughput | Verdict |
|----------|:--------------:|:-----------:|:-------:|
| CPU-only, 16GB RAM (T470p) | ❌ | ~1-2 tok/s with 8B model | Weeks for 11K docs |
| GPU 12GB+ (RTX 3060+) | ⚠️ | ~15-30 tok/s with 7-8B | Days |
| API (Groq) | ✅ | ~3000 docs/hour | Hours, ~$10 |

**Hybrid recommendation**: Use Groq Batch API for the extraction phase ($10/11K docs), keep everything else local. The extraction cost is a one-time expense — the resulting indices are perpetual.

### 6. PDF text extraction performance (PyMuPDF)

⚠️ **Critical pitfall: PyMuPDF is slow for mass extraction.** Opening each PDF individually has significant per-file overhead. Real benchmark (Jun 2026, T470p, 6 workers):

| Volume | Time | Throughput |
|--------|:----:|:----------:|
| 100 PDFs | ~20s | 5 PDFs/s |
| 1,000 PDFs | ~3 min | 5.5 PDFs/s |
| 5,000 PDFs | ~15-20 min | 5-6 PDFs/s |
| 11,224 PDFs | ~35-40 min | 5-6 PDFs/s |

**Mitigations:**
- For dry-run estimates: use a sample (100-200 PDFs) — do NOT run full extraction just for estimation
- For the actual batch: accept the extraction time and run in background (15-20 min for 5K is acceptable)
- **Do NOT use the same script for both estimation and production** — create a fast scanning function for estimates and the full extraction for the actual batch
- Consider filtering by year (2024-2026 = 9,788 PDFs) to reduce volume while keeping the most relevant content

### 7. PDF-specific text cleaning

PDFs from judicial portals (especialmente TC Perú) have characteristic artifacts. The regex patterns from `scripts/data_prep/preparar_batch_tc.py`:

```python
def clean_pdf_text(text: str) -> str:
    # Barras de números repetidos (artefacto de firma digital)
    text = re.sub(r'[1I]\s*[1I]\s*[1I][1I\sI]+', '', text)
    # Barras de caracteres especiales repetidos
    text = re.sub(r'[■●►▪□○◇※★]+', '', text)
    # Líneas de guiones/guiones bajos repetidos (separadores de página)
    text = re.sub(r'[_\-=]{5,}', '', text)
    # Múltiples espacios
    text = re.sub(r' {3,}', ' ', text)
    # Múltiples saltos de línea
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Números de página aislados (1-2 dígitos en línea propia)
    text = re.sub(r'\n\d{1,2}\n(?=[A-ZÁÉÍÓÚ])', '\n', text)
    return text.strip()
```

These patterns were developed from the TC SEDETC PDF corpus (11,224 PDFs) where ~98% had real text but with significant artifacts from the digital signature/PDF generation process.

### 8. Groq Batch API client workflow

The Groq Python client (`groq>=1.0.0`) supports the full OpenAI-compatible Batch API:

```python
from groq import Groq
client = Groq(api_key="...")

# 1. Upload JSONL file
with open("batch.jsonl", "rb") as f:
    file = client.files.create(file=f, purpose="batch")

# 2. Create batch job
batch = client.batches.create(
    input_file_id=file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h",  # Groq processes these async
)

# 3. Poll for completion
import time
while True:
    status = client.batches.retrieve(batch.id)
    if status.status == "completed":
        break
    time.sleep(30)

# 4. Download results
result = client.files.content(status.output_file_id)
results_text = result.text
```

Available client methods:
- `client.files.create()` — upload JSONL
- `client.files.content()` — download results
- `client.files.list()` — list uploaded files (clean up old ones)
- `client.batches.create()` — start batch job
- `client.batches.retrieve()` — poll status
- `client.batches.list()` — list all batch jobs
- `client.batches.cancel()` — cancel running job

The JSONL format matches OpenAI Batch API exactly (see `references/batch-jsonl-format.md` for full schema).

Throughput: ~3,000 docs/hour for mixed 8B/70B workloads. Cost: ~$0.0005/doc average.

See `references/corpus-compatibility-evaluation.md` for the detailed evaluation framework used in this session's TC SEDETC PDF assessment.
See `references/batch-jsonl-format.md` for the Groq Batch API JSONL request/response format, conversion pipeline to indexer input, and file naming conventions.

### Working example: TC SEDETC PDF ingestion (creado Jun 2026)

The scripts below were created for this specific corpus evaluation and serve as a reference implementation of the methodology above:

- `scripts/data_prep/preparar_batch_tc.py` — Full pipeline: scan PDFs → PyMuPDF extraction → clean artifacts → classify 8B/70B → generate JSONL batch files. Usage: `python scripts/data_prep/preparar_batch_tc.py --max 5000 --workers 8`.
- `scripts/data_prep/enviar_batch_tc.py` — Upload JSONL files → create Groq Batch jobs → poll → download results → convert to `rag_listo_batch_tc_*.json` format for `pipeline/indexer.py`. Usage: `python scripts/data_prep/enviar_batch_tc.py`.

Key implementation details in `preparar_batch_tc.py`:
- `TOKEN_THRESHOLD=1000` separates 8B from 70B (same as original pipeline)
- `smart_truncate(max_words=3000)` prevents context overflow
- `clean_pdf_text()` removes PDF artifacts (see Section 7 above for regex patterns)
- Outputs JSONL capped at 4,500 lines per file (Groq file size limit)

### Router model ordering bug (CORREGIDO en optimize/singleton-cache-router)

The router in `agents/router.py` iterates through `models_to_try` and uses the first Groq client call that succeeds. The BROKEN ordering was:

```python
models_to_try = [
    "moonshotai/kimi-k2-instruct-0905",  # ← OpenRouter model, NOT Groq!
    "llama-3.3-70b-versatile"            # ← actual Groq model
]
```

`moonshotai/kimi-k2-instruct-0905` is an OpenRouter model — it will **always fail** when called via `groq_client.chat.completions.create()`. The `except: continue` in the loop catches it and tries the next model, but each failed attempt costs **2-5 seconds** (network timeout). The effective first-try model becomes `llama-3.3-70b-versatile`.

**Fix applied**: Reordered to put a real Groq model first:
```python
models_to_try = [
    "llama-3.1-8b-instant",               # Groq, ~$0.0002/request
    "llama-3.3-70b-versatile"             # fallback
]
```

### `_doc_header()` loads metadata per-chunk

In `retrieval/hybrid_search.py`, the `_doc_header()` function calls `_load_docs_metadata()` and `_load_docs_entities()` for every chunk formatted. Each call checks and conditionally loads the full JSON from disk. For 7 retrieved documents, that's 14 I/O-triggering checks.

**Fix**: Load `_docs_metadata` and `_docs_entities` once at module level, or in a single init function called when the module is imported. The lazy-load pattern in the current code re-executes the guard check on every call.

### CriticAgent: indeterminate citations bypass feedback loop

In `agents/critic.py`, when a citation has only a textual identifier (EXP. N°, CAS. N°, RTF N°)
and no matching doc_id is found via `_normalize_id()`, the code sets
`c.exists_in_corpus = None` and crucially `c.hallucinated = False`.

The feedback loop in `graphrag_pro.py:_needs_rewrite()` only checks `hallucinated > 0`:

```python
def _needs_rewrite(critic_verdict):
    vd = critic_verdict.to_dict()
    return vd.get("hallucinated", 0) > 0
```

This means **citations with textual identifiers that don't match any document in the corpus
are silently accepted**. A completely fabricated "CAS. N° 99999-9999" would NOT trigger a
rewrite because it's categorized as "indeterminate" (exists_in_corpus = None → hallucinated = False).

**Impact**: The feedback loop only catches ~40-60% of hallucinated citations (those with
a concrete `doc_id` like `1612215.html`). The rest — pure LLM fabrications using well-formed
EXP./CAS./RTF numbers — pass through undetected.

**Fix**: Add indeterminate/unverifiable citations to the rewrite trigger:
```python
def _needs_rewrite(critic_verdict):
    vd = critic_verdict.to_dict()
    return vd.get("hallucinated", 0) > 0 or vd.get("unverifiable", 0) > 0
```

**Caveat**: Setting `unverifiable > 0` as a rewrite trigger may cause false positives
for citations that are correctly formatted but slightly reformatted by the LLM (e.g.,
"EXP. N.° 000315-2003" vs "EXP. N° 315-2003"). Test with historical benchmark data
before enabling.

## CitationExtractor and IndeterminateDetector modules (Jul 2026)

Two new modules to close the indeterminate citation bypass in critic.py, created via SDD+TDD (27 tests, all passing):

**`retrieval/citation_extractor.py`** — 10 regex patterns for Peruvian legal citations:
| Pattern | Format | Example |
|---------|--------|---------|
| Ley | `Ley N° XXXX`, `L. N° XXXX` | Ley N° 30478 |
| Decreto Supremo | `DS N° XXX-YYYY-ZZ` | DS N° 015-2026-PCM |
| Decreto Legislativo | `DL N° XXXX` | DL N° 1500 |
| Casacion | `Casacion N° XXXX-YYYY` | Casacion N° 15-2015 |
| Expediente TC | `EXP. N° XXXX-YYYY-ZZ/TC` | EXP. N° 00364-2022-AA/TC |
| STC | `STC N° XXXX-YYYY` | STC N° 045-2017 |
| RTF | `RTF N° XXXX-YYYY` | RTF N° 12345-2024 |
| Articulo | `Articulo X del Codigo/Ley Y` | Articulo 205 del Codigo Penal |
| Constitucion | `Constitucion Politica Art. X` | Constitucion Politica, Art. 2.24 |
| Acuerdo Plenario | `Acuerdo Plenario N° X/YYYY` | Acuerdo Plenario N° 2-2020 |

**`retrieval/indeterminate_detector.py`** — DEREK-style detector (arXiv:2507.15863):
- Verifies citations against metadata_docs.json, tc_metadata.json
- Heuristics: numbers >60000, repeated digits (11111, 99999), round numbers for laws
- Year range filtering (numbers 1000-2999 skipped as non-suspicious)
- Range checking per document type (laws 1-33000, casaciones 1-50000, etc.)
- Returns `(es_determinada: bool, fuente: Optional[str])`

**TDD test structure** (follow SPEC-002):
```python
# test_citation_extractor.py — 15 tests
def test_extrae_ley_normal():
    citas = extractor.extraer_todas("conforme a la Ley N° 30478")
    assert citas[0].tipo == "ley" and "30478" in citas[0].identificador

def test_multiples_citas_en_un_texto():
    # Multiple citation types in one text — all must be extracted

def test_texto_sin_citas():
    # No legal content — empty list returned

# test_indeterminate_detector.py — 12 tests
def test_detecta_ley_inexistente():
    es_det, fuente = detector.verificar("Ley 99999", tipo="ley")
    assert es_det == False  # No existe en ninguna fuente

def test_detecta_ley_existente():
    es_det, fuente = detector_con_metadata.verificar("Ley 30478", tipo="ley")
    assert es_det == True and fuente == "metadata_docs"

def test_digitos_repetidos():
    assert detector._es_sospechosa("Cas. 11111", "casacion") == True

def test_numero_real_no_sospechoso():
    assert detector._es_sospechosa("Ley 30478", "ley") == False
```

## Reranker module (from LexRAG-v2)

LexRAG-v2 has a cross-encoder reranker at `retrieval/reranker.py` that LexRAG-Optimizado (production) lacks. Uses `BAAI/bge-reranker-v2-m3` (state-of-the-art multilingual cross-encoder). Integration:

```python
from retrieval.reranker import rerank
docs_reranked = rerank(query, docs, top_k=5)
# Returns top_k docs with 'rerank_score' field added
# Falls back to top_k from input if model not available
```

Call after RRF fusion in `retrieval/hybrid_search.py`, replacing the final top-k selection step.

## Parche vs Rewrite decision framework

When deciding whether to patch existing LexRAG or rewrite from scratch (applies to any mature codebase with production data):

```text
REGLA: PARCHAR siempre que el sistema existente tenga:
  - Indices funcionales (FAISS, BM25) con datos reales
  - Metadatos extraídos (metadata_docs.json)
  - Consultas guardadas que sirven como benchmark
  - Pipeline de ingesta ya validado

Matriz de decisión ponderada (5 dimensiones):
  - Preservación de activos (peso 25%):  Parche=10, Rewrite=1
  - Tiempo de implementación  (peso 20%): Parche=9,  Rewrite=3
  - Riesgo técnico           (peso 20%): Parche=8,  Rewrite=3
  - Calidad metodológica     (peso 15%): Parche=5,  Rewrite=9
  - Flexibilidad futura      (peso 10%): Parche=6,  Rewrite=9
  TOTAL: Parche 8.15/10 vs Rewrite 3.90/10

EXCEPCION: Si el recall post-BGE-M3 + reranker sigue <80% y el código
existente es inmantenible (acoplamiento excesivo), considerar rewrite
con el golden dataset existente como referencia.
```

## SDD v2 + TDD for parching existing codebases (Jul 2026)

When applying SDD to an EXISTING codebase (not greenfield), the workflow adapts to incremental changes:

| Fase SDD | Actividad para parches | Output |
|----------|----------------------|--------|
| SPECIFY | Read existing SPEC for the module; if none exists, write a spec scoped to the change | spec.md |
| PLAN | Define atomic tasks, each with its RED→GREEN test structure | tasks.md |
| TASKS | Write TDD test first (RED — must fail), then implement minimal code (GREEN), then refactor | test_*.py + code |
| IMPLEMENT | Apply patch to the real codebase, run regression tests to verify nothing broke | Cambio en vivo |

TDD cycle for each atomic change:
```
# 1. RED: write failing test that captures the bug/feature
pytest tests/test_feature.py -v  # test fails as expected

# 2. GREEN: implement minimal code to make test pass
# Edit the source file
pytest tests/test_feature.py -v  # test passes now

# 3. REFACTOR: clean up while keeping tests green
pytest tests/ -v  # all tests still pass
```

Key differences from greenfield SDD:
- Tests import the EXISTING codebase, not mocked interfaces
- The spec only describes the delta, not the whole system
- Regression tests exist before the change — run them after EVERY patch
- Each atomic change has ONE test file with 3-5 focused tests

## Debugging Python NameError in search interfaces

When the user shows a screenshot with `NameError: name 'XXX' is not defined` in a search interface:

1. The variable name is the key clue — `content_col` in the error means a column reference is undefined
2. Common causes:
   - SQL query result accessed by column index that was renamed or removed
   - Migration from dict-style cursor to tuple-style cursor (or vice versa)
   - Typo: `content_col` vs `content_column` vs `col_content`
3. Search strategy: `grep -rn "VAR_NAME" /project/path/ --include="*.py"` — if not found, search more broadly
4. If the variable is not in any checked project, ask the user for the exact file path
5. Fix pattern: define the missing variable before use, or fix the column reference

### Follow-up questions block the [DONE] signal

In `agents/synthesizer.py`, the follow-up question generation happens INLINE 
before yielding `[DONE]`:

```python
# ... follow-up API call BLOCKING here ...
yield {"data": "[DONE]"}
```

If the Groq API is slow (5-15s) for the follow-up generation, the terminal or SSE
stream **hangs** after the last word of the response. The user sees no [DONE],
no prompt for follow-up questions — just a frozen terminal.

**Fix options** (ordered by practicality):
1. **Pre-generate with last synthesis chunk**: Add a flag `generate_followups=true` to the
   synthesis prompt and parse a JSON block from the response text itself — zero extra API calls.
2. **Deferred via asyncio**: Send `[DONE]` immediately after the response text, then
   generate follow-ups as a background task and cache them for the next user interaction.
3. **Timeout wrapper**: Wrap the follow-up call in `asyncio.wait_for(..., timeout=5.0)`
   and skip if it doesn't respond in time.

### Synthesizer produces 0 FUENTE: citations (confirmed in benchmarks)

Benchmarks from `resultados_benchmark/bateria_10_opt/` (Jun 2026) show **0 FUENTE:
citations across all 10 queries** despite the synthesizer prompt instructing 
"Siempre incluye también la ruta al archivo fuente."

The instruction is buried at position ~35 of a ~60-line prompt, after dense legal
instructions about reasoning, tone, and structure. When combined with 5K-15K tokens
of context (hybrid + graph), the LLM loses this signal.

**Empirical evidence**: 0/10 benchmark responses had any `FUENTE:` or `Jurisprudencia/`
path. Yet 7/10 queries had relevant documents retrieved. The citation instruction is
being silently dropped.

**Fix approaches** (tested, in order of effectiveness):
1. **Put citation format as FIRST instruction** (before reasoning/tone/structure).
   Example: `"REGLAS DE CITACIÓN (OBLIGATORIO): Toda cita DEBE terminar con 
   (Jurisprudencia/XXXXX.html). Citas sin archivo fuente serán eliminadas."`
2. **Post-processing injection**: After synthesis, inject `(Jurisprudencia/{doc_id}.html)`
   by scanning the response for doc_id mentions and cross-referencing against top_docs.
3. **Template enforcement**: In `get_hybrid_context()`, put the `📄 FUENTE: 
   Jurisprudencia/XXXXX.html` on its own bold line at the START of each chunk section,
   not buried in the chunk text. The LLM tends to repeat what it sees at the top.
4. **Critic enhancement**: Make the CriticAgent's score_verdict() include a check that
   every document used in context has a corresponding FUENTE in the response, and flag
   missing ones as errors.

**When to escalate**: If after implementing all fixes, benchmarks still show 0 citations,
post-process every response by looking up `metadata_docs.json` and appending
`(Jurisprudencia/{doc_id}.html)` to every identifiable case number in the text.

## Dependency troubleshooting

### API keys

When APIs return 401/403, test each one directly with curl before debugging the code:

```bash
# DeepSeek
curl -s https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $KEY"
# Expected: 200, returns model list

# Groq
curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $KEY"
# Expected: 200

# Serper
curl -s https://google.serper.dev/search \
  -H "X-API-KEY: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"q":"test","gl":"pe","hl":"es","num":1}'
# Expected: 200, returns searchParameters
```

Common failure modes:
- DeepSeek 401: key expired/invalid. Regenerate at platform.deepseek.com.
- Groq 401: key expired (this user's Groq keys have been consistently invalid since Jun 2026). Regenerate at console.groq.com.
- Serper 403/400: out of credits (400 with "Not enough credits") or key expired (403). Top up at serper.dev.
- The `.env` file is NOT readable via read_file (secret guard) but CAN be written via terminal. Backup first: `cp .env .env.backup`

The `venv_linux/` often has missing packages. When `graphrag_pro.py` fails with `ModuleNotFoundError`:

1. Check which package is missing and install via `venv_linux/bin/pip install <pkg>`
2. Heavy dependencies (torch ~3GB, sentence-transformers) may take 5+ minutes on `/mnt/d/` due to WSL filesystem overhead
3. Use background installs with `notify_on_complete=true` for large packages
4. Key dependencies: `openai`, `groq`, `rank-bm25`, `transformers`, `torch`, `sentence-transformers`, `scikit-learn`, `python-dotenv`, `faiss-cpu`, `networkx`
5. For API server: also `pip install fastapi uvicorn sse-starlette`

### Background process pitfalls

When running LexRAG scripts in the background (via `terminal(background=true)` or cron):

1. **Python stdout buffering**: Without a TTY, Python buffers stdout. Output may not appear in logs for 60s+. Use:
   - `python -u script.py` flag (unbuffered)
   - `PYTHONUNBUFFERED=1` env var (set globally: `echo 'export PYTHONUNBUFFERED=1' >> ~/.bashrc`)
   - `print(..., flush=True)` in Python code
   **Without this, the script appears "colgado" (hung) when it's actually running fine but silent.**

2. **source activate in background**: `source venv/bin/activate && python script.py` may appear to hang because the shell loads `.bashrc`/`.profile` which can be slow in non-interactive contexts. Use the direct venv python path instead: `venv_linux/bin/python script.py`.
3. **sentence-transformers first load**: Takes 30-60s to download/cache the model. The first import of any module that triggers `from core.embedding import embedding_model` will appear frozen. This is normal — wait for it.
4. **MemoryCache is per-process**: Cache resets when the Python process ends. Between-process caching requires SQLite or Redis.

These are NOT bugs — they are Python/environment behaviors that look like hangs.
5. For FastAPI: additionally `pip install fastapi uvicorn sse-starlette`

## Output conventions

- The user prefers **clean terminal output** — suppress HTTP request logs, use acronyms (DPK = DeepSeek, GRQ = Groq)
- **Suppress tqdm/progress bars in scripts** — when running long tasks in background, use `tqdm(... disable=not sys.stderr.isatty())` or add `--quiet` flag. Progress bars clutter the terminal for this user.
- **Background process output must be unbuffered** — use `PYTHONUNBUFFERED=1` or `python -u` flag. Without this, stdout is buffered when not on a TTY, and the script appears hung when it's actually running fine but silent.
- When showing citations, always include the `Jurisprudencia/XXXXX.html` path
- The user likes `problema → análisis → opciones → acción` format for decision proposals

## Windows execution (venv created from WSL)

The project runs on Windows (D: drive), with a Windows-native venv that was created
from WSL using the Windows Python binary directly:

```bash
# From WSL, create Windows venv on D: drive
/mnt/c/Python314/python.exe -m venv /mnt/d/PyCode/LexRAG-Optimizado/venv

# Install deps (runs Windows pip from WSL)
/mnt/d/PyCode/LexRAG-Optimizado/venv/Scripts/python.exe -m pip install -r requirements.txt
```

**Critical: always use `-X utf8` flag** when running with the Windows Python from WSL,
because Windows uses cp1252 encoding by default and the code uses Unicode emoji/accents:

```bash
# Correct
/d/PyCode/LexRAG-Optimizado/venv/Scripts/python.exe -X utf8 script.py

# Wrong — will crash with UnicodeEncodeError on emoji
/d/PyCode/LexRAG-Optimizado/venv/Scripts/python.exe script.py
```

The flag `-X utf8` works consistently from CMD, PowerShell, AND WSL calling Windows Python.
The env var `PYTHONIOENCODING=utf-8` only works from CMD, not from WSL.

**Convenience batch files:**
- `setup.bat` — creates venv + installs deps (run once on Windows)
- `start_api.bat` — runs `api.py` FastAPI server on :8000
- `query.bat` — runs `graphrag_pro.py --query <text>` from cmdline

**Verification script pattern (for testing from WSL):**
```python
# Always include at top of verification scripts
import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Avoid emoji in print() calls, use % formatting instead of f-strings
print('Loader indices OK (%.1fs)' % elapsed)
# NOT: print(f"Indices cargados en {elapsed:.1f}s") — emoji in core code will still fail
```

**Note on Python version:** The Windows Python is 3.14 (installed at C:\Python314).
The `venv/Scripts/python.exe` is a symlink to this. Do NOT try to use WSL's python3
to create the Windows venv — it creates a Linux-style venv without `Scripts/activate.bat`.

## Windows/PowerShell troubleshooting

The project runs from PowerShell on Windows (venv is Windows-native Python). Two recurrent issues:

### 1. UnicodeEncodeError with cp1252

PowerShell's default encoding is `cp1252`. If `graphrag_pro.py` (or any script) uses unicode box-drawing chars (╗║╚▄█), printing them crashes with:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2557' in position ...
```

**Fix**: Force UTF-8 on stdout at the top of the script:
```python
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
```

### 2. SentenceTransformer API changes across versions

`sentence-transformers` has renamed methods across versions. The `get_embedding_dimension()` method was renamed to `get_sentence_embedding_dimension()` in v5.x.

If `core/embedding.py` imports fail with `AttributeError: 'SentenceTransformer' object has no attribute 'get_embedding_dimension'`:

1. Check installed version: `python -c "import sentence_transformers; print(sentence_transformers.__version__)"`
2. Inspect available methods: `python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('...'); print([a for a in dir(m) if 'dimension' in a.lower()])\"`
3. Use the version-appropriate method — prefer `get_sentence_embedding_dimension()` which works across v3.0+.

See `references/sentence-transformers-api-notes.md` for more details.

### 3. distiluse deprecation warning (confirmed Jul 2026)

`sentence-transformers` v5.x renamed `get_sentence_embedding_dimension()` to `get_embedding_dimension()`. The current LexRAG `core/embedding.py` line 10 calls the old name, producing:

```
FutureWarning: The `get_sentence_embedding_dimension` method has been renamed to `get_embedding_dimension`.
```

**Fix**: Update `core/embedding.py` to use the new name, and check compatibility with the existing `get_sentence_embedding_dimension` for v3.x fallback:
```python
try:
    emb_dim = embedding_model.get_embedding_dimension()
except AttributeError:
    emb_dim = embedding_model.get_sentence_embedding_dimension()  # fallback for v3.x
```

## SDD workflow for optimization projects

When the user asks to plan or implement optimizations, use **Spec-Driven Development (SDD)**:

1. **Constitution** — Write `specs/CONSTITUTION.md` with principles: no modify originals, spec-first, data-driven decisions, backward compatibility.
2. **Specs** — For each optimization, write a spec (`SPEC-NNN-name.md`) with: Context, Given/When/Then behavior, Obligatorio/Prohibido, Concrete example, Acceptance criteria, Files affected, Risks, Verification tests.
3. **Review** — User reviews and approves specs before implementation begins.
4. **Plan** — Per spec: technical plan in `plans/PLAN-NNN-name.md`.
5. **Implement** — Create new code + patches. Never modify originals during planning phase.
6. **Verify** — Test against acceptance criteria. All criteria must pass.

See `spec-driven-development` skill for full template details.

### Work directory convention
- **Planning**: work in `D:\\PyCode\\lexrag-optimizacion\\` (specs, plans, patches, new code)
- **Apply**: once user approves, copy new files + apply patches to the real project
- **Orphan**: the plan folder becomes documentation-only once applied

## Performance optimization patterns (implemented Jun 2026)

### 1. Singleton de índices (core/index_manager.py)
- FAISS, BM25, Grafo y metadata se cargan UNA VEZ al arrancar
- Patrón double-checked locking para thread-safety
- Benchmarks reales: 7.0-7.2s primera carga, 0.0000s re-carga
- Verificación: `index_manager.initialize()` 2 veces debe dar ~0s en 2da llamada

### 2. Caché de 2 niveles (exacto → semántico)
- Nivel 1: `utils/query_cache.py` — hash MD5 de query normalizada (minúsculas, sin acentos, sin puntuación)
- Nivel 2: `utils/semantic_cache.py` — similitud de coseno entre embeddings (threshold configurable, default 0.92)
- Pipeline: exacto (~1ms) → semántico (~150ms) → pipeline completo (~9s)
- Guardar en ambos: `query_cache.set()` + `semantic_cache.set()` en tándem

### 3. Escrituras asíncronas (agents/synthesizer.py)
- `save_query_log()` y `save_chunk_audit()` movidos a `asyncio.to_thread()` + `functools.partial`
- No bloquea el hot path (~300ms eliminados del tiempo de respuesta)
- Si falla la escritura, se loggea warning pero la respuesta se entrega igual

### 4. except:pass específico (graphrag_pro.py streaming)
- ANTES: `except Exception: pass` silenciaba errores reales y [DONE]
- DESPUÉS: `if chunk_str["data"] == "[DONE]": break` antes del try/except
- Errores reales: `except json.JSONDecodeError: logger.debug(...)` + `continue`

### 5. Monitoreo (utils/metrics.py)
- MetricsCollector singleton: registro de tiempos por fase (router, retrieval, graph, synthesis)
- Conteo de queries, hit rate de caché, errores por tipo
- Endpoint GET /metrics en api.py
- Sin overhead medible (~0.01ms por registro)

### 6. Graph stats precompute
- `scripts/precompute_graph_stats.py` genera data/indices/graph_stats.json
- Precomputa top 30 jueces/leyes + top 20 actores/demandados
- 8.8 KB, ~0.4s de cómputo
- Cargado vía IndexManager.get_graph_stats()

### 7. FAISS HNSW (diferido — no es bottleneck)
- `scripts/migrate_faiss_hnsw.py` convierte FlatL2 a HNSW
- Probado: 12x speedup, 94.8% recall para 60K vectores
- **No aplicar**: FlatL2 tarda ~0.9ms. El bottleneck real son las APIs LLM (~9s).
  La ganancia de ~0.8ms es irrelevante. Revisar solo cuando el corpus supere 500K docs.

## Reference files

- `references/jun2026-corpus-audit.md` — Detailed corpus measurements from Jun 2026: 59,571 FAISS vectors, 64K metadata docs, 191K graph nodes, node type distribution, benchmark times (17.8s avg, 0 citations issue), and the "Optimized Copy Trap" missing-modules list.
- `references/batch-testing-workflow.md` — batch testing script patterns and metrics
- `references/performance-diagnosis.md` — per-step timing breakdown and optimization options
- `references/sentence-transformers-api-notes.md` — method names, gotchas, and version quirks
- `references/lightweight-legal-search.md` — Patterns for small-to-medium legal search systems (<20K docs): corpus-sizing decisions, hybrid metadata extraction (regex+Groq), batch embeddings, multi-source indexing, filter-based search, and narrative/conversational responses. Reference project: TC_SearchRAG (11,483 TC docs).
- `references/legal-search-state-of-the-art-2026.md` — Compendio de 18 papers con DOI verificados sobre estado del arte en búsqueda jurídica: embeddings (BGE-M3, multilingual-e5), cross-encoders, validación de citas (hallucination rate 17-33% en Lexis+AI), chunking (sentence split 512/200), evaluación RAG (RAGAS, HyPA-RAG, NitiBench), filtrado temporal (SAT-Graph RAG), y stack recomendado por fase (FAISS→PGVector→Milvus+Neo4j).
- **Citation validation research (Jul 2026)** — See `lex-rag-chunk-audit`'s `references/citation-validation-research.md` for 6 new papers with DOIs: Dahl 2025 (17-33% hallucination, arXiv:2405.20362), DEREK Module (arXiv:2507.15863), Reliability by Design (FCR < 0.2%, arXiv:2601.15476), Citation Grounding (13-21%, arXiv:2606.00898), Who Checks Citations (91.2% recall programmatic, arXiv:2606.21155), and From Judgments to Issues (arXiv:2607.03325).
- `references/legal-search-engine-research-2026.md` — Compendio de 18 papers, técnicas (MRL, LCS, MKD, TSDAE+GPL), y stack recomendado para búsqueda jurídica peruana. Incluye: ecosistema SAT-Graph (7 papers), validación de citas (5 papers con DOI), hallazgos del bypass de indeterminadas en CriticAgent, y regla de decisión para fine-tuning de embeddings.
