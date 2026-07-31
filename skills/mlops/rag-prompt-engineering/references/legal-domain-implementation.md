# Legal RAG Implementation Reference

## HTML Metadata Extraction Patterns (Peruvian Jurisprudence)

```python
# Tribunal Fiscal
m = re.search(r'RTF\s*N[°º]?\s*([\d\-]+)', header)
if m:
    result["identificador"] = f'RTF N° {m.group(1)}'
    result["organo"] = 'Tribunal Fiscal'
    result["tipo"] = 'Resolucion TF'

# Corte Suprema - Casacion
m = re.search(r'(?:CAS|Cas)[\.\s]*(?:LAB[\.\s]*)?N[°º]?\s*'
              r'([\d\-]+\s*[\-\w]*\s*[\w]*)', header)

# Tribunal Constitucional
m = re.search(r'EXP[\.\s]*N[°º]?\s*\n?\s*'
              r'([\d]+(?:-[\d]+)*(?:/[A-Za-z0-9]+)*)', header)

# Casación (with accent)
m = re.search(r'Casaci[oó]n\s*N[°º]?\s*([\d\-]+\-[\w]+)', header)

# Resolucion N°
m = re.search(r'RESOLUCION\s*N[°º]?\s*\n?\s*([\d\-]+)', header)
```

## Multi-Provider .env Template

```ini
# --- PROVEEDOR (elegir uno) ---
PROVEEDOR=groq
API_KEY=gsk_...       # https://console.groq.com/keys
MODELO=llama-3.3-70b-versatile
# API_BASE_URL=       # opcional, auto-detectado por PROVEEDOR

# --- OPCIONES ALTERNATIVAS ---
# OpenRouter: PROVEEDOR=openrouter  API_KEY=sk-or-...  MODELO=meta-llama/llama-3.3-70b-instruct
# DeepSeek:   PROVEEDOR=deepseek    API_KEY=sk-...      MODELO=deepseek-v4-flash
# Together:   PROVEEDOR=together    API_KEY=...         MODELO=meta-llama/Llama-3.3-70B-Instruct-Turbo
# OpenAI:     PROVEEDOR=openai      API_KEY=sk-...      MODELO=gpt-4o-mini
```

## DeepSeek V4 Pricing (Provider Cost Reference)

When deploying legal RAG for colleagues or clients, provider cost matters — especially for batch testing and multi-user use.

| Model | Context | Input (cache miss) | Input (cache hit) | Output |
|---|---|---|---|---|
| `deepseek-v4-flash` | 1M | $0.14/1M | **$0.0028/1M** | $0.28/1M |
| `deepseek-v4-pro` | 1M | $0.435/1M | $0.0036/1M | $0.87/1M |
| `deepseek-chat` (deprecated 2026/07/24) | 64K | $0.27/1M | $0.07/1M | $1.10/1M |
| `deepseek-reasoner` (deprecated 2026/07/24) | 64K | $0.55/1M | $0.14/1M | $2.19/1M |

**Key takeaway**: v4-flash at $0.28/1M output is **10x cheaper** than the deprecated deepseek-reasoner. Context caching (50x cheaper) makes repetitive system prompts in agent sessions nearly free.

DeepSeek V4 features relevant to legal RAG:
- **Tool calls** (function calling) — for structured retrieval workflows
- **JSON output** — guaranteed structured responses
- **1M context** — can fit entire codebases or large document collections
- **Thinking mode** — on by default for v4-flash, can be disabled for speed
- **FIM completion** — code fill-in-the-middle (non-thinking mode only)

Hermes Agent is officially listed as a supported DeepSeek integration. Configure in `config.yaml`:
```yaml
default_provider: deepseek
default_model: deepseek-v4-flash
```

## GitIgnore Pattern for Legal RAG

```gitignore
# Block huge source data
Jurisprudencia/
data_raw/

# Block large alternate indices
data/indices/*_pro.*

# Allow essential runtime data
!data/indices/faiss_index.bin
!data/indices/faiss_meta.pkl
!data/indices/graph_juris.pkl
!data/metadata_docs.json

# Block generated files
consultas_guardadas/
resultados_benchmark/
logs/
.env
.env.bak
```

## Batch Test Script Skeleton

```bash
#!/bin/bash
QUERIES=(
    "P01|SIMPLE|desnaturalizacion de contratos de trabajo"
    "P02|MEDIUM|maltrato psicologico como violencia familiar"
    "P03|COMPLEX|cuales son los requisitos para reposicion de trabajador..."
)

for ENTRY in "${QUERIES[@]}"; do
    IFS='|' read -r ID LEVEL QUERY <<< "$ENTRY"
    python graphrag_console.py --query "$QUERY" > /tmp/output.txt
    # Extract metrics: scenario, fallo_count, label_count, word_count
done
```

## Streaming (Multi-Provider OpenAI-Compatible)

```python
for chunk in llm_client.chat.completions.create(
    messages=[...],
    model=MODELO,
    stream=True,
):
    if chunk.choices[0].delta.content:
        palabra = chunk.choices[0].delta.content
        print(palabra, end="", flush=True)
```

## Distributable Package Structure

When sharing with a colleague so they can test immediately:

```
LexRAG_v3/
|-- graphrag_console.py          # Self-contained, multi-provider
|-- README.md                    # Install steps + provider guide
|-- requirements.txt
|-- .env.example                 # 5 documented provider options
|-- data/
|   |-- indices/*
|   |-- metadata_docs.json
```

The colleague needs: `pip install -r requirements.txt` + their own API key. No source files, no ingestion scripts, no HTMLs required.

## Parallel Processing for 64K Files

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(process_file, f): f for f in all_files}
    for future in as_completed(futures):
        result = future.result()
```

Pattern: submit all files, process results as they complete, report progress every N items. Avoids loading all results into memory at once.

## 15-Question Lawyer-Oriented Test Battery

Three levels of complexity tested automatically via a batch script:

| Level | Query Length | Example |
|-------|-------------|---------|
| Simple | 3-6 words | "indemnizacion por despido arbitrario" |
| Medium | 6-12 words | "maltrato psicologico como violencia familiar" |
| Complex | 15+ words | "requisitos reposicion trabajador servicio especifico..." |

### Structure per Query

Each record in the batch uses pipe-delimited format:

```bash
QUERIES=(
    "P01|SIMPLE|desnaturalizacion de contratos de trabajo"
    "P02|MEDIUM|maltrato psicologico como violencia familiar"
    "P03|COMPLEX|cuales son los requisitos para reposicion de trabajador..."
)
```

### Report Output per Query

The batch script produces a structured `.txt` report per query with these metrics:

- **Scenario detected**: Escenario A (relevant) or B (not relevant)
- **Fallos cited**: count and verbatim text of each ruling
- **Document labels shown**: human-readable IDs vs. internal filenames
- **Docs found**: number of documents retrieved
- **Word count**: response length (key for B conciseness check)
- **Graph nodes used**: when present, which entities were referenced

### Three Verification Paths

1. **Relevant path (A)**: Check that all 4 structural sections are present (Synthesys → Evidence → Graph → Conclusion) and every cited document includes its "fallo"
2. **Negative path (B)**: Verify response is ≤4 paragraphs, explicitly declares no relevant docs, and still shows what was found with their rulings
3. **Label correctness**: Confirm that no `408739.html`-style internal filenames appear; all document references use human-readable IDs

## Verification Checklist (Pre-Deployment)

- [ ] Escenario A: 4-part structure with fallos cited using legible labels
- [ ] Escenario B: concise (≤4 paragraphs), shows all retrieved docs with fallos
- [ ] Labels show "RTF N° 09457-5-2004 | Tribunal Fiscal" not "Doc: 408739.html"
- [ ] `--stream` produces real-time token-by-token output
- [ ] Batch test suite produces structured reports per query
- [ ] Ingestion scripts kept separate from query engine
- [ ] `.gitignore` blocks large source data and experimental indices, allows runtime indices
- [ ] `.env.example` documents at least 3 provider options with registration links
