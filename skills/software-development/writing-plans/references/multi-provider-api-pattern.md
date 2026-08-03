# Multi-Provider API Integration Pattern

## Problem
A system needs to support multiple LLM/API providers (OpenAI, Groq, DeepSeek, Anthropic) without duplicating integration code. Users want to switch providers by changing config, not code.

## Solution: OpenAI-compatible client pattern

All major providers (OpenAI, Groq, DeepSeek, Together AI, OpenRouter) support the **OpenAI-compatible API format**. This means the same `openai` Python library works for all — only `base_url`, `model`, and `api_key` differ.

### Architecture

```
config.yaml → llm.base_url + llm.model
.env        → LLM_API_KEY

code:
  from openai import OpenAI
  client = OpenAI(api_key=key, base_url=url)
  resp = client.chat.completions.create(model=model, messages=[...])
```

### Provider reference table

| Provider | base_url | Model example | Pricing (input/output per M tok) |
|----------|---------|---------------|----------------------------------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini | $0.15/$0.60 |
| DeepSeek | https://api.deepseek.com | deepseek-chat | $0.14/$0.28 |
| Groq | https://api.groq.com/openai/v1 | llama-3.3-70b-versatile | $0.59/$0.79 |
| OpenRouter | https://openrouter.ai/api/v1 | deepseek/deepseek-chat | model + 10-20% |
| Google Gemini | https://generativelanguage.googleapis.com/v1beta/openai/ | gemini-2.0-flash | $0.10/$0.40 |
| Together AI | https://api.together.xyz/v1 | meta-llama/Llama-3.3-70B | ~$0.90/$0.90 |

### Transcription (Whisper) pattern

Same pattern applies to `client.audio.transcriptions.create()`:

| Provider | base_url | Model |
|----------|---------|-------|
| OpenAI | https://api.openai.com/v1 | whisper-1 |
| Groq | https://api.groq.com/openai/v1 | whisper-large-v3 (gratis) |

### Implementation pattern

```python
def detect_provider(model: str, base_url: Optional[str] = None) -> tuple[str, str]:
    """Auto-detect provider from model name if base_url not given."""
    if base_url:
        return base_url, api_key
    if 'whisper-large' in model:
        return 'https://api.groq.com/openai/v1', os.getenv('GROQ_API_KEY')
    # fallback
    return 'https://api.openai.com/v1', os.getenv('OPENAI_API_KEY')
```

### Config in YAML

```yaml
llm:
  provider: deepseek    # label only, not used in code
  model: deepseek-chat  # used directly
  base_url: https://api.deepseek.com  # used directly
```

### Key insight
No need for adapter classes or provider abstractions. The OpenAI client IS the abstraction. Just change `base_url` + `model` + `api_key` at the call site.

### Pitfalls
- `threading.Lock` is NOT reentrant. `save_verification()` calling `update_speaker_score()` causes deadlock. Use `threading.RLock()`.
- Not all providers support `response_format={"type": "json_object"}`. Test before assuming.
- Groq Whisper accepts the same parameters as OpenAI Whisper API. Drop-in replacement.
- yt-dlp installed via pip may not create a CLI wrapper in every venv. Use `sys.executable, '-m', 'yt_dlp'` instead of `'yt-dlp'`.
- `duckduckgo_search` v8+ is deprecated in favor of `ddgs` package. Same API, different import.
