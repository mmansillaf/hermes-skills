# Groq Models — Verified Availability (Jun 2026)

Verified via `GET https://api.groq.com/openai/v1/models` with proper auth headers.

## LLMs for chat

| Model ID | Use | Status |
|----------|-----|:------:|
| `llama-3.3-70b-versatile` | Synthesis (ask_tc, narrar_tc) | ✅ Active |
| `llama-3.1-8b-instant` | Router (clasificación LEGAL/NO_LEGAL) | ✅ Active |
| `qwen/qwen3-32b` | Synthesis alternative | ✅ Active |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Alternative | ✅ Active |

## Decommissioned

| Model ID | Former use | Replaced by |
|----------|-----------|-------------|
| `mixtral-8x7b-32768` | General chat | `llama-3.3-70b-versatile` |

## Pipeline models

| Model | Use |
|-------|-----|
| `whisper-large-v3` | Speech-to-text |
| `whisper-large-v3-turbo` | Speech-to-text (faster) |
| `meta-llama/llama-prompt-guard-2-22m` | Prompt injection guard |
| `meta-llama/llama-prompt-guard-2-86m` | Prompt injection guard |

## API access quirks

- **Cloudflare block**: Python's `urllib` default User-Agent (`Python-urllib/3.x`) returns HTTP 403 error code 1010. Workaround: use the `groq` library (httpx-based, sets correct headers) or set `User-Agent: Mozilla/5.0...` explicitly.
- **Model list endpoint**: `GET https://api.groq.com/openai/v1/models` with `Authorization: Bearer <key>` header.
- **Error codes**: 401 = invalid/expired key, 403 = Cloudflare/region block, 400 = bad request (e.g., decommissioned model).
- **Response time variance**: llama-3.3-70b can take 2s to 74s depending on context size and Groq queue depth.

## Cost reference (per 1M tokens)

| Model | Input | Output |
|-------|:----:|:------:|
| llama-3.3-70b-versatile | $0.59 | $0.79 |
| llama-3.1-8b-instant | $0.05 | $0.08 |
