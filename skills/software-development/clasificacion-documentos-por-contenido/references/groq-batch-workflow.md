# Groq Batch API Workflow for Legal Document Extraction

## Overview

Groq Batch API allows processing thousands of legal documents asynchronously at 50% discount. The pipeline:
1. Prepare JSONL with requests → Upload to Files API → Create batch job → Monitor → Download results → Convert to indexer format

## Batch API Limits (from Groq docs, Jun 2026)

- Max 50,000 lines per JSONL file (reduced to 25,000 for 30K char docs)
- Max 200MB per file
- Completion window: 24h to 7d (recommend 7d)
- Rate limits separate from synchronous API
- Supported models for Batch: llama-3.1-8b-instant, meta-llama/llama-4-scout-17b-16e-instruct, llama-3.3-70b-versatile, openai/gpt-oss-20b, openai/gpt-oss-120b

## JSONL Format

Each line is a single request:

```json
{"custom_id": "doc_00001", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.1-8b-instant", "messages": [...], "temperature": 0.1, "max_tokens": 640}}
```

## Critical Finding: max_tokens=640

Increasing max_tokens from 512 to 640 raised JSON validity from 89% to **99%** for Llama 3.1 8B. The 8% failure rate at 512 was entirely due to truncated JSON output (Unterminated string, missing closing braces). The extra 128 tokens give the model room to complete responses.

## API Endpoints

1. **Upload file**: `POST /v1/files` with multipart form (purpose=batch)
2. **Create batch**: `POST /v1/batches` with input_file_id, endpoint, completion_window
3. **Check status**: `GET /v1/batches/{batch_id}`
4. **Download results**: `GET /v1/files/{output_file_id}/content`
5. **List batches**: `GET /v1/batches`

## JSON Repair Strategy (3-tier)

For responses that fail direct json.loads():

1. **Extract from ``` blocks**: Find the largest JSON between markdown fences
2. **Regex search**: Find all `{...}` patterns, sort by length, try each
3. **Recursive trim**: Chop from last `}` backward up to 20 attempts

## Model Comparison (100 docs LABORAL, same prompt, Batch API)

| Model | JSON directo | JSON final | Con leyes | Fallo concreto | Costo Batch/100 | Costo 562K Batch |
|-------|:-----------:|:---------:|:---------:|:--------------:|:---------------:|:----------------:|
| Llama 3.1 8B (max_tokens=512) | 89% | 89% | 87% | 99% | $0.009 | $51 |
| Llama 3.1 8B (max_tokens=640) | **99%** | **99%** | 87% | 99% | $0.010 | **$55** |
| Llama 4 Scout 17B (640) | 97% | 97% | 86% | 87% | $0.021 | $117 |
| Llama 3.3 70B (640) | 93% | 93% | 85% | 94% | $0.105 | $592 |
| Qwen3 32B | 0% | 0% | N/A | N/A | $0.028 | $158 |

Note: Qwen3 32B returned 0% valid JSON — output format incompatible with current parsing.

## Winner: Llama 3.1 8B Instant with max_tokens=640
- 99% JSON validity, 87% with laws cited, 99% with concrete ruling
- $55 for 562K docs via Batch API
- 1.2s per doc synchronous, ~3 min for 100 docs via Batch

## Scripts

- `batch_groq.py` — Full pipeline: prepare, upload, monitor, download, convert
- `test_modelos_comparativo.py` — Multi-model comparison runner
