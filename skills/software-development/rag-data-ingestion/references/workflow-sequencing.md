# Batch Exhaustion Workflow — Sequencing Reference

Full sequence for taking a document collection through Groq Batch API to indexed RAG, based on processing ~90K legal documents (LABORAL + COMERCIAL).

## Phase 1: Preparation

### 1a. Count remaining documents

Before submitting new batches, tally what's already processed to avoid double work:

```python
# Count by materia from existing batch output files
from collections import Counter
processed = Counter()
for fname in ["batch_results/old_batch.jsonl", "batch_results/new_batch.jsonl"]:
    for line in open(fname):
        d = json.loads(line)
        cid = d.get("custom_id", "")
        if cid and "_" in cid:
            processed[cid.rsplit("_", 1)[0]] += 1
```

### 1b. Prepare JSONL input files

Each JSONL line is a complete Groq request (see `references/groq-batch-api.md`). Key parameters:

- **max_tokens=1024** — Critical for JSON completeness (avg output ~400, but some hit 658)
- **temperature=0.1** — Low for deterministic extraction
- **Truncate text to 28K-30K chars** — Enough for any resolution; Groq 8B has 128K context

File size limit: **200 MB** per uploaded file. At ~7 KB/line, max ~28,000 lines per file. Split with:

```bash
split -l 12500 -d --additional-suffix=.jsonl input.jsonl output_prefix_
```

## Phase 2: Upload & Create Batches

Use Python `requests`, not curl. A standalone script (`subir_batches.py`):

```python
import requests, json, os

API_KEY = "gsk_..."
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
BASE = "https://api.groq.com/openai/v1"

BATCHES = [
    ("batch_jsonl/lote_1a.jsonl", "Lote 1a (LAB 12.5K)"),
    # ...
]

for filepath, label in BATCHES:
    with open(filepath, "rb") as f:
        resp = requests.post(f"{BASE}/files", headers=HEADERS,
            files={"file": (os.path.basename(filepath), f, "application/jsonl")},
            data={"purpose": "batch"}, timeout=300)
    file_id = resp.json()["id"]

    resp2 = requests.post(f"{BASE}/batches",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"input_file_id": file_id, "endpoint": "/v1/chat/completions",
              "completion_window": "24h"}, timeout=30)
    batch_id = resp2.json()["id"]
    print(f"{label}: {batch_id}")
```

**PITFALL: curl `-F file=@path` fails** with quoting issues in shell scripts. Always use Python requests for Groq file upload.

## Phase 3: Monitor with Hermes Cronjob

Instead of polling manually, set up a Hermes cronjob that polls every 30 min and auto-downloads:

```python
# Via cronjob tool (not shell crontab):
# action='create', schedule='30m'
# prompt: "Monitorear estado de N batches de Groq Batch API..."
# enabled_toolsets: ["terminal", "file"]
```

The cronjob should:
1. Check each batch ID via `GET /v1/batches/{id}`
2. Report current status, completed/total/failed
3. If status=`completed` and output not yet downloaded:
   - Download output: `GET /v1/files/{output_file_id}/content`
   - Download errors: `GET /v1/files/{error_file_id}/content`
   - Save as `batch_results/batch_PREFIJO_output.jsonl`
4. If all completed, auto-deactivate the cronjob

Expected yield per batch: **~96%** (3-4% `capacity_exhausted` failures).

## Phase 4: Download Results

Once status=`completed`:

```bash
curl -s -H "Authorization: Bearer $GROQ_API_KEY" \
  "https://api.groq.com/openai/v1/files/{output_file_id}/content" \
  -o batch_results/batch_label_output.jsonl

curl -s -H "Authorization: Bearer $GROQ_API_KEY" \
  "https://api.groq.com/openai/v1/files/{error_file_id}/content" \
  -o batch_results/batch_label_errors.jsonl
```

## Phase 5: Quality Check

Run analysis on each output file:

```bash
python3 scripts/analyze_batch_results.py batch_results/batch_label_output.jsonl \
  --errors batch_results/batch_label_errors.jsonl
```

Expected healthy batch:
- JSON válido: **99+%**
- finish_reason=stop: **99+%**
- Content length avg: **~1,000 chars**
- Errors: 100% `capacity_exhausted` (not JSON quality issues)

## Phase 6: Convert to Indexer Format

```bash
# Combine all batch output files into a single rag_listo JSON
python3 scripts/convert_batch_outputs.py \
    batch_results/batch_lote1_output.jsonl batch_results/batch_lote2_output.jsonl \
    --output data_raw/rag_listo_batch_groq_N.json
```

The script deduplicates against existing files in `data_raw/` automatically.

## Phase 7: Run Indexer

**Must set PYTHONPATH first**, otherwise `from core.config` fails:

```bash
cd /project_root
PYTHONPATH=. python3 pipeline/indexer.py
```

For large collections (50K+ docs), run in background:

```bash
cd /project_root
PYTHONPATH=. nohup python3 -u pipeline/indexer.py > indexer_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

Monitor with `tail -f indexer_*.log` — expected ~33 docs/s on 6C/12T CPU.

## Phase 8: Verify Indexes

After indexing completes:

```bash
ls -lh data/indices/
python3 -c "
import pickle, faiss
# FAISS vector count
index = faiss.read_index('data/indices/faiss_index_pro.bin')
print(f'FAISS vectors: {index.ntotal}')
# Graph nodes
with open('data/indices/graph_juris_pro.pkl', 'rb') as f:
    G = pickle.load(f)
print(f'Graph nodes: {G.number_of_nodes()}, edges: {G.number_of_edges()}')
# BM25
with open('data/indices/bm25_index_pro.pkl', 'rb') as f:
    bm25_data = pickle.load(f)
print(f'BM25 chunks: {len(bm25_data.get(\"corpus\", []))}')
"
```

## Batch Result Patterns Observed

| Metric | Lote 1 (25K LAB) | Lote 2 (8K LAB+COM) | Notes |
|--------|:----------------:|:-------------------:|-------|
| Total | 25,000 | 7,935 | |
| Completed | 24,070 | 7,668 | |
| Failed | 930 (3.7%) | 267 (3.4%) | 100% `capacity_exhausted` |
| JSON válido | 100% | 99.9% | max_tokens=1024 |
| finish_reason=stop | 100% | 100% | |
| Avg chars | 1,090 | 1,044 | | | Min chars | 441 | 494 | |
| Max chars | 4,682 | 3,567 | |

### Real-World Timing (from June 2026 production run)

| Batch | Docs | Created | Completed | Duration |
|:-----:|:----:|:-------:|:---------:|:--------:|
| L1 (25K LAB) | 25,000 | 08:40 | 11:38 | **~3h** |
| L2 (8K LAB+COM) | 7,935 | 08:45 | 13:03 | **~4h 18m** |
| L1a (12.5K LAB) | 12,500 | ~08:30 | ~10:30* | **~2h** (est.) |
| L1b (12.5K LAB) | 12,500 | ~08:30 | ~10:30* | **~2h** (est.) |
| L2 (25K LAB) | 25,000 | ~08:30 | ~11:30* | **~3h** (est.) |
| L3 (8K COM+LAB) | 7,935 | ~08:35 | ~12:35* | **~4h** (est.) |

*Estimated. Timing is unpredictable — Groq's 24h window means batches complete whenever capacity frees up. Smaller batches can take longer than larger ones due to scheduler behavior.
