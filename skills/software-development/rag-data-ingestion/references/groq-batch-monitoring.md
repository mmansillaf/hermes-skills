# Groq Batch API — Monitoring & Download Workflow

Quick-reference for querying batch status, downloading results, and converting to indexer format.

## Check Batch Status (curl)

```bash
API_KEY="gsk_..."
BATCH_ID="batch_01ktkpp2rae82t9efcsmnt6jq6"

curl -s -H "Authorization: Bearer $API_KEY" \
  https://api.groq.com/openai/v1/batches/$BATCH_ID | jq
```

Key fields in response:
- `status`: one of `validating`, `in_progress`, `finalizing`, `completed`, `failed`, `cancelled`
- `request_counts.completed` / `.total` / `.failed` — progress summary
- `output_file_id` — only present when status is `completed`
- `error_file_id` — errors file (may exist even on completed batches)
- `completed_at` / `in_progress_at` / `created_at` — timestamps

## Download Results

```bash
API_KEY="gsk_..."
FILE_ID="file_01ktky1m04f95atw5gr1fjwjck"
OUT_DIR="/path/to/batch_results"

# Download output
curl -s -H "Authorization: Bearer $API_KEY" \
  https://api.groq.com/openai/v1/files/$FILE_ID/content \
  -o $OUT_DIR/lote1a_12K_output.jsonl

# Count lines
wc -l $OUT_DIR/lote1a_12K_output.jsonl
```

## Convert JSONL → rag_listo format

The project's `convertir_outputs.py` script converts Groq JSONL output to `rag_listo_batch_*.json` format:

1. Add a new entry in the `conversions` list:
   ```python
   ('lote1a_12K_output.jsonl', 'rag_listo_batch_groq_12453.json'),
   ```
2. Run: `python3 convertir_outputs.py`
3. Verify with: `wc -l data_raw/rag_listo_batch_*.json`

The script:
- Skips already-processed doc IDs across all existing `rag_listo_batch_*.json` files
- Maps `resumen_hechos` → `contenido_a_vectorizar.hechos`, etc.
- Generates deterministic doc IDs via MD5 hash of `custom_id`

## Index After Conversion

```bash
cd /project/root
PYTHONPATH=. python3 pipeline/indexer.py          # incremental (resume)
PYTHONPATH=. python3 pipeline/indexer.py --force   # full rebuild
```

**If `--force` is interrupted mid-way**, restart WITHOUT `--force` to continue from the partial checkpoint. Do NOT re-run `--force`.

## Typical States Over Time

| Time | Batch 1a (12.5K) | Batch 1b (12.5K) | Batch 2 (25K) | Batch 3 (8K) |
|------|:-----------------:|:-----------------:|:--------------:|:-------------:|
| T+0min | `validating` | `validating` | `validating` | `validating` |
| T+5min | `in_progress` (0%) | `in_progress` (0%) | `queued` | `queued` |
| T+2h | `completed` | `in_progress` (90%) | `in_progress` (0%) | `in_progress` (0%) |
| T+8h | ✅ | ✅ | ✅ | ✅ |

Batches are processed **sequentially by Groq**, not in parallel. Batch 2 (25K) waits until 1a and 1b finish.
