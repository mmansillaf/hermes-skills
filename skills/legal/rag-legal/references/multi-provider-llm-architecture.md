# Multi-Provider LLM Architecture (KRagLocal)

## Overview

Unified interface for 4 LLM providers in a lightweight legal RAG system. The user selects the provider at runtime via `.env` — no code changes needed.

## Provider Matrix

| Provider | Env var | Default model | Key needed? | Cost |
|----------|---------|---------------|-------------|------|
| **groq** | `GROQ_API_KEY` | `llama-3.3-70b-versatile` | Yes | Free tier |
| **openai** | `OPENAI_API_KEY` | `gpt-4o-mini` | Yes | ~$0.15/M tokens |
| **gemini** | `GEMINI_API_KEY` | `gemini-2.0-flash` | Yes | Free tier |
| **ollama** | *(none)* | `llama3.2:3b` | No | Local only |

## .env Configuration

```env
# Provider selection
LLM_PROVIDER=groq          # groq | openai | gemini | ollama

# Groq (default)
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile

# OpenAI (ChatGPT)
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
# OPENAI_BASE_URL=https://api.openai.com/v1

# Google Gemini
# GEMINI_API_KEY=...
# GEMINI_MODEL=gemini-2.0-flash

# Ollama (local)
# OLLAMA_MODEL=llama3.2:3b
# OLLAMA_HOST=http://127.0.0.1:11434
```

## Architecture

```python
class LLMClient:
    """Unified multi-provider client."""

    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "groq")

    def generate(self, system_prompt, user_prompt, temperature=0.3,
                 max_tokens=2048, prefer_cloud=False) -> str:
        """Route to the active provider."""
        if prefer_cloud and self.provider == "ollama":
            self.provider = "groq"  # fallback

        if self.provider == "groq":
            return self._generate_groq(...)
        elif self.provider == "openai":
            return self._generate_openai(...)
        elif self.provider == "gemini":
            return self._generate_gemini(...)
        else:
            return self._generate_ollama(...)
```

## Provider Implementations

### Groq (primary)

```python
def _generate_groq(self, system, user, temperature, max_tokens):
    from groq import Groq
    key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=key)
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
```

### OpenAI

```python
def _generate_openai(self, system, user, temperature, max_tokens):
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    client = OpenAI(api_key=key, base_url=base)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
```

### Gemini

```python
def _generate_gemini(self, system, user, temperature, max_tokens):
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        system_instruction=system,
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        },
    )
    response = model.generate_content(user)
    return response.text
```

### Ollama (local)

```python
def _generate_ollama(self, system, user, temperature, max_tokens):
    import ollama
    client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    response = client.chat(
        model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        options={"temperature": temperature, "num_predict": max_tokens},
    )
    return response["message"]["content"]
```

## Error Handling

Each provider has its own error path:

1. **ollama** — Falls back to Groq if model not found (user has Groq API key)
2. **groq** — No fallback, returns `[Error Groq: {msg}]`
3. **openai** — No fallback, returns `[Error OpenAI: {msg}]`
4. **gemini** — No fallback, returns `[Error Gemini: {msg}]`

All return descriptive error messages so the user knows which key to fix.

## Dependencies

```txt
# requirements.txt additions for multi-provider
groq>=0.9.0           # Always needed (fallback)
openai>=1.0.0         # Only if using OpenAI
google-generativeai>=0.8.0  # Only if using Gemini
ollama>=0.4.0         # Only if using Ollama
```

## Switching Providers at Runtime

Change `.env` and restart:

```bash
# From Groq to OpenAI
sed -i 's/LLM_PROVIDER=groq/LLM_PROVIDER=openai/' .env
# Add OPENAI_API_KEY=sk-... to .env
# Then:
python3 -m src.api
```

## UI Integration

The web UI at `http://127.0.0.1:8765` shows the current provider in the health endpoint:

```json
{"status":"ok","documents":4,"total_chunks":58,"provider":"groq"}
```

The checkbox "Modo cloud" forces Groq even when provider is set to `ollama` (for users who want local retrieval + cloud generation).

## Validation with Multi-Provider

The citation validation agent accepts 4 regex patterns regardless of which LLM generated the response. The same validation runs for Groq, OpenAI, Gemini, and Ollama outputs. See `kraglocal-multiagent-pipeline.md` → Agent 5: Citation Validator.
