# Groq Batch API Implementation Details

Reference for implementing batch document processing via Groq API.

## API Endpoints

| Step | Method | URL |
|------|--------|-----|
| Upload JSONL | POST | `https://api.groq.com/openai/v1/files` |
| Create batch | POST | `https://api.groq.com/openai/v1/batches` |
| Check status | GET | `https://api.groq.com/openai/v1/batches/{batch_id}` |
| Download results | GET | `https://api.groq.com/openai/v1/files/{file_id}/content` |
| List batches | GET | `https://api.groq.com/openai/v1/batches` |

## Rate Limits (Developer Plan)

- 1,000 RPM (requests per minute)
- 300K TPM (tokens per minute)
- Max file size: **200 MB** per uploaded file
- Max completion window: 24h (minimum)

### File Size Limit: Splitting Large JSONLs

Files over 200 MB **must** be split before upload. Use `split` — it's fast, handles any size, and produces clean output:

```bash
# Split a 300MB, 25K-line JSONL into 2 parts of ~12.5K lines each
split -l 12500 -d --additional-suffix=.jsonl batch_jsonl/lote_1_LABORAL.jsonl batch_jsonl/lote_1a_LABORAL_

# Result: lote_1a_LABORAL_00.jsonl + lote_1a_LABORAL_01.jsonl (~150MB each, safely under 200 MB)
```

The `-l` flag splits by line count (calculate with `wc -l`). The `-d` flag uses numeric suffixes. `--additional-suffix` preserves the `.jsonl` extension for Groq format detection.

## Batch Response Format

Each line in the output file is:
```json
{
  "custom_id": "LABORAL_000001",
  "response": {
    "status_code": 200,
    "body": {
      "choices": [{"message": {"content": "..."}}],
      "usage": {"prompt_tokens": 1700, "completion_tokens": 406}
    }
  }
}
```

## Known Error Codes

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid_api_key` | Bad API key | Check env var |
| `file_too_large` | >200 MB | Split JSONL into smaller files |
| `invalid_jsonl` | Malformed line | Validate each request is valid JSON |
| `model_not_found` | Deprecated model | Check console.groq.com/docs/models |
| `capacity_exhausted` | Groq out of capacity for that request | **Not actionable per-request.** Expect ~3-4% per batch. Plan retry batch or accept yield. |

## Model IDs (current as of June 2026)

Production:
- `llama-3.1-8b-instant` — 560 TPS, $0.05/$0.08 per 1M
- `llama-3.3-70b-versatile` — 280 TPS, $0.59/$0.79 per 1M
- `openai/gpt-oss-20b` — 1000 TPS, $0.075/$0.30 per 1M
- `openai/gpt-oss-120b` — 500 TPS, $0.15/$0.60 per 1M

Preview:
- `meta-llama/llama-4-scout-17b-16e-instruct` — 750 TPS, $0.11/$0.34 per 1M
- `qwen/qwen3-32b` — 400 TPS, $0.29/$0.59 per 1M (incompatible with JSON extraction via Batch)

## Cost Calculation

```
cost_normal = total_input_tokens / 1_000_000 * price_in +
              total_output_tokens / 1_000_000 * price_out
cost_batch = cost_normal * 0.50  # 50% discount for Batch API
```

## Upload: Python requests > curl

**Prefer Python's `requests` library over `curl -F` for multipart uploads.** The `-F` flag with `@file` paths has quoting issues — especially when the filename contains special characters or the variable is sourced via subshell. Python handles multipart forms reliably:

```python
import requests

API_KEY = "gsk_..."
headers = {"Authorization": f"Bearer {API_KEY}"}
base = "https://api.groq.com/openai/v1"

# 1. Upload file
with open("batch_jsonl/lote_1.jsonl", "rb") as f:
    resp = requests.post(
        f"{base}/files",
        headers=headers,
        files={"file": ("lote_1.jsonl", f, "application/jsonl")},
        data={"purpose": "batch"},
        timeout=300
    )
file_id = resp.json()["id"]

# 2. Create batch
resp2 = requests.post(
    f"{base}/batches",
    headers={**headers, "Content-Type": "application/json"},
    json={"input_file_id": file_id, "endpoint": "/v1/chat/completions", "completion_window": "24h"},
    timeout=30
)
batch_id = resp2.json()["id"]
print(f"Batch ID: {batch_id}")
```

### Standalone Upload Script Pattern

When submitting **multiple batches** (3+), write a self-contained Python script instead of chaining curl commands:

```python
# subir_batches.py
import requests, json, os

API_KEY = "gsk_..."
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
BASE = "https://api.groq.com/openai/v1"

BATCHES = [
    ("batch_jsonl/lote_1a.jsonl", "Lote 1a (LAB 12.5K)"),
    ("batch_jsonl/lote_1b.jsonl", "Lote 1b (LAB 12.5K)"),
    ("batch_jsonl/lote_2.jsonl", "Lote 2 (LAB 25K)"),
]

for filepath, label in BATCHES:
    with open(filepath, "rb") as f:
        resp = requests.post(f"{BASE}/files", headers=HEADERS,
            files={"file": (os.path.basename(filepath), f, "application/jsonl")},
            data={"purpose": "batch"}, timeout=300)
    file_id = resp.json()["id"]

    resp2 = requests.post(f"{BASE}/batches", headers={**HEADERS, "Content-Type": "application/json"},
        json={"input_file_id": file_id, "endpoint": "/v1/chat/completions", "completion_window": "24h"},
        timeout=30)
    batch_id = resp2.json()["id"]
    print(f"{label}: {batch_id}")
```

This avoids all shell quoting issues, gives clear error messages, and handles large files reliably.

## Multi-Batch Status Checking

When you have multiple concurrent batches, check all at once:

```bash
curl -s -H "Authorization: Bearer $GROQ_API_KEY" \
  "https://api.groq.com/openai/v1/batches/batch_ID1"
curl -s -H "Authorization: Bearer $GROQ_API_KEY" \
  "https://api.groq.com/openai/v1/batches/batch_ID2"
```

Parse with Python:

```python
import json
for label, raw in [('Lote 1', output1), ('Lote 2', output2)]:
    d = json.loads(raw)
    c = d.get('request_counts', {})
    print('%s: Status=%s | %d/%d (%.1f%%) | %d fallos' % (
        label, d.get('status','?'),
        c.get('completed',0), c.get('total',0),
        c.get('completed',0)/c.get('total',1)*100,
        c.get('failed',0)))
```

## Automated Monitoring with Hermes Cronjob

When submitting 3+ batches (24h window), **set up a Hermes cronjob** to poll every 30 min and auto-download on completion. This avoids busy-waiting and manual checking.

```yaml
# Via Hermes CLI or cronjob tool:
schedule: "30m"                          # poll every 30 minutes
prompt: |
  Monitorea el estado de N batches de Groq Batch API.
  Para cada batch, consulta GET /v1/batches/{id}.
  Si status='completed' y aun no se ha descargado:
    - Descargar output: GET /v1/files/{output_file_id}/content
    - Descargar errors: GET /v1/files/{error_file_id}/content
    - Guardar en batch_results/batch_PREFIJO_output.jsonl
  Reporte final: resumen de todos los batches.
  Si todos completaron, desactiva este cronjob.
```

PITFALL: The job needs a restricted toolset for efficiency — use `enabled_toolsets: ["terminal", "file"]` to avoid loading the full browser/vision/search stack.

## Post-Completion: Download Results

Once status=`completed`, download output + errors:

```bash
curl -s -H "Authorization: Bearer $GROQ_API_KEY" \
  "https://api.groq.com/openai/v1/files/{output_file_id}/content" \
  -o batch_results/batch_label_output.jsonl

curl -s -H "Authorization: Bearer $GROQ_API_KEY" \
  "https://api.groq.com/openai/v1/files/{error_file_id}/content" \
  -o batch_results/batch_label_errors.jsonl
```

## Post-Completion: Quality Metrics

### 1. Count by materia (from custom_id prefix)

```python
from collections import Counter
materias = Counter()
for line in open(output_jsonl):
    d = json.loads(line)
    cid = d.get('custom_id','')
    if cid and '_' in cid:
        materias[cid.rsplit('_', 1)[0]] += 1
```

### 2. JSON validity + finish stats

```python
total = valid_json = stop_reason = 0
min_len, max_len = 999999, 0
total_len = 0

for line in open(output_jsonl):
    d = json.loads(line)
    body = d['response']['body']
    choice = body['choices'][0]
    msg = choice['message']['content']
    reason = choice.get('finish_reason','')
    total += 1; total_len += len(msg)
    min_len = min(min_len, len(msg))
    max_len = max(max_len, len(msg))
    if reason == 'stop': stop_reason += 1
    try:
        json.loads(msg)
        valid_json += 1
    except: pass

print('JSON valido: %d/%d (%.1f%%)' % (valid_json, total, valid_json/total*100))
print('finish_reason=stop: %d/%d' % (stop_reason, total))
print('Chars: min=%d | max=%d | avg=%.0f' % (min_len, max_len, total_len/total))
```

Expected healthy batch: **99+% JSON valido**, **99+% finish_reason=stop**, **~1,000 avg chars**.

### 3. Error analysis

```python
for line in open(errors_jsonl):
    d = json.loads(line)
    print('%s: code=%s' % (d.get('custom_id','?'), d.get('error',{}).get('code','?')))
```

If all errors are `capacity_exhausted`, the JSONL and prompt are fine.

## Post-Completion: Convert to Indexer Format

The indexer expects `rag_listo_batch_groq_N.json` in `data_raw/`. Each Groq output line nests the extraction inside `response.body.choices[0].message.content`:

```python
output_lines = []
for line in open('batch_lote_output.jsonl'):
    d = json.loads(line)
    content = d['response']['body']['choices'][0]['message']['content']
    extracted = json.loads(content)

    output_lines.append({
        "id_documento": d['custom_id'],
        "contenido_a_vectorizar": {
            "hechos": extracted.get('resumen_hechos', ''),
            "problema": extracted.get('resumen_problema', ''),
            "fallo": extracted.get('resumen_fallo', '')
        },
        "metadatos_graphrag": extracted.get('entidades_clave', {})
    })

with open('data_raw/rag_listo_batch_groq_N.json', 'w') as f:
    json.dump(output_lines, f, ensure_ascii=False)
```

Then index:
```bash
cd /repo && PYTHONPATH=. python3 pipeline/indexer.py
cd /repo && PYTHONPATH=. python3 pipeline/indexer.py --force  # fresh rebuild
```
