# Groq Batch API — Patterns & Pitfalls

## Quick Reference
- **Model**: `llama-3.1-8b-instant` (cheapest batch model)
- **Cost**: $0.025/M input tokens, $0.04/M output tokens (batch pricing, 50% off real-time)
- **Batch size**: max 500 requests per file
- **completion_window**: "24h" (generous, batch usually completes in minutes to hours)
- **Rate limit**: `sleep(3)` between file uploads

## Critical Pitfall: `response_format: json_object`

When using `response_format={"type": "json_object"}`, the API requires that **the word "json" or "JSON" appears somewhere in the messages**. If it doesn't, you get:

```
Error code: 400 - 'messages' must contain the word 'json' in some form
```

**Fix**: Include "JSON" in the system prompt. Example:

```python
# WRONG — triggers error
system = "Responde con un objeto."
response_format = {"type": "json_object"}

# RIGHT — includes "JSON"
system = "Responde con un objeto JSON: {\"sumilla\": \"...\"}"
response_format = {"type": "json_object"}
```

## Batch API Flow

```
generate JSONL → upload file → create batch → poll status → download results
```

### JSONL Format
Each line is a complete request object:
```json
{"custom_id": "2021-01-01/1916174-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.1-8b-instant", "messages": [...], "response_format": {"type": "json_object"}, "temperature": 0.0, "max_tokens": 150}}
```

### Upload & Batch Creation
```python
# 1. Upload file
uploaded = client.files.create(file=open("batch.jsonl", "rb"), purpose="batch")

# 2. Create batch
batch = client.batches.create(
    input_file_id=uploaded.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)
```

### Status Check
```python
job = client.batches.retrieve(batch_id)
print(job.status)  # validating → in_progress → finalizing → completed
print(job.request_counts)  # completed/total
```

### Download Results
```python
response = client.files.content(job.output_file_id)
content = response.read().decode('utf-8')
# Each line: {"custom_id": "...", "response": {"status_code": 200, "body": {...}}}
```

## State Tracking (Resume-Safe)

Use a tracking JSON file to survive power outages:
```json
{
  "batch_001.jsonl": {
    "file_id": "file_abc123",
    "batch_id": "batch_xyz789",
    "status": "completed",
    "downloaded": true,
    "updated": 500,
    "errors": 0
  }
}
```

## Token & Cost Estimation
- **Avg texto_completo**: 8,591 chars → ~2,148 tokens
- **Truncation**: 8,000 chars → ~2,000 tokens (saves ~7% cost)
- **Output**: sumilla ~150 chars → ~50 tokens
- **33,255 normas × 2,000 tokens**: ~66.5M input → **~$1.66**
- **33,255 × 50 tokens output**: ~1.66M → **~$0.07**
- **Total**: ~$1.73 for full sumilla generation

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `json_validate_failed` / `max completion tokens reached` | `max_tokens` too low to complete JSON | Increase to 150-200 |
| `no such column: normas_fts` in Python | FTS5 virtual table accessed wrong | Use `JOIN normas_fts ON n.rowid = normas_fts.rowid` |
| FTS5 parsing numbers as columns | Unquoted terms like `158-2025` | Use double quotes: `'"158-2025"'` |
| Ambiguous column `sumilla` | Both `normas` and `normas_fts` have it | Use `n.sumilla` alias |
