# Provider Connectivity Testing — Real Results (May 2026)

## Testing Methodology

For each provider, test with a minimal query (max_tokens=30-80) that exercises its intended role:

1. Primary (reasoning): ask a definition question
2. Auxiliary (compression): ask a summarization task
3. Fallback (coding/fast): ask a simple "say OK" query

Use Python `urllib` (NOT `curl` subprocess) to avoid JSON encoding issues. Source API keys from `~/.hermes/.env` using `os.environ` or file read — never hardcode keys.

Test each provider for:
- Authentication (correct key format?)
- Endpoint reachability (correct URL?)
- Model name validity (exists in provider catalog?)
- Parameter constraints (temperature limits, token limits)

## Real Test Results — 2026-05-04

### Environment
- Hermes v0.12.0
- Python 3.11.15
- Testing from: Hermes code execution sandbox (datacenter IP)
- Timeout: 15-20s per provider

### Results

| Provider | Model | Endpoint | Result | Latency | Tokens | Notes |
|----------|-------|----------|--------|---------|--------|-------|
| DeepSeek | deepseek-v4-pro | api.deepseek.com/v1 | ✅ PASS | 3236ms | 92 | Primary — flawless |
| Google AI Studio | gemini-2.5-flash | generativelanguage.googleapis.com/v1beta | ✅ PASS | 5507ms | ? | Auxiliary — free, reliable |
| OpenRouter | google/gemini-2.5-flash-lite | openrouter.ai/api/v1 | ✅ PASS | 819ms | 11 | Aggregator — works (response in Indonesian, but functional) |
| Kimi (direct, .cn) | kimi-k2.6 | api.moonshot.cn/v1 | ❌ FAIL | 1740ms | — | 401 Invalid Authentication |
| Kimi (direct, .ai) | kimi-k2.6 | api.moonshot.ai/v1 | ✅ PASS | 2604ms | 65 | **Correct endpoint** |
| Kimi (via OpenRouter) | moonshotai/kimi-k2.6 | openrouter.ai/api/v1 | ✅ PASS | 46410ms | ? | Works but high latency |
| Kimi (via NVIDIA) | moonshotai/kimi-k2.6 | integrate.api.nvidia.com/v1 | ✅ PASS | 3657ms | 43 | Reliable workaround |
| NVIDIA Nemotron | nvidia/llama-3.3-nemotron-super-49b-v1 | integrate.api.nvidia.com/v1 | ✅ PASS | 1652ms | 74 | Correct model name |
| NVIDIA Llama 3.3 | meta/llama-3.3-70b-instruct | integrate.api.nvidia.com/v1 | ✅ PASS | 679ms | 51 | Ultra fast |
| Groq | llama-3.3-70b-versatile | api.groq.com/openai/v1 | ⚠️ BLOCKED | 36ms | — | Cloudflare 1010 from sandbox IP |
| Groq (key 2) | llama-3.3-70b-versatile | api.groq.com/openai/v1 | ⚠️ BLOCKED | 36ms | — | Same Cloudflare block |

### Key Discoveries

1. **Kimi correct endpoint is `api.moonshot.ai` (NOT `.cn`)** — The skill originally documented `api.moonshot.cn`. This endpoint returns 401 for valid keys. Switch to `.ai` and Kimi works perfectly.

2. **Kimi K2.6 requires `temperature: 1`** — Unlike most models that accept 0.0-2.0, Kimi K2.6 rejects any temperature except `1`. Setting `temperature: 0.05` in the fallback config causes HTTP 400.

3. **Groq blocked from sandbox IPs (Cloudflare 1010)** — Both Groq API keys (different accounts) return HTTP 403 `error code: 1010` from the Hermes code execution sandbox. The keys ARE valid — they work from residential/local machine IPs. When testing Groq, always test from the host machine directly, not from `execute_code`.

4. **NVIDIA Build has 120+ models** — Including Kimi K2.6 (`moonshotai/kimi-k2.6`), DeepSeek V4-Pro (`deepseek-ai/deepseek-v4-pro`), Llama 3.3 70B (`meta/llama-3.3-70b-instruct`), and Nemotron Super (`nvidia/llama-3.3-nemotron-super-49b-v1`), and even GPT-OSS-120B (`openai/gpt-oss-120b`). A single API key gives access to all.

5. **Model name `nvidia/nemotron-3-super` does NOT exist** — Use `nvidia/llama-3.3-nemotron-super-49b-v1`. Always fetch the current model list before configuring.

6. **Hermes doctor only checks 3 providers** — It verifies DeepSeek, Kimi, and OpenRouter. It does NOT check Google AI Studio, Groq, or NVIDIA. Manual testing is essential for those.

7. **OpenRouter adds 500ms+ latency** — Routing through OpenRouter adds overhead. Use direct provider APIs for primary and fallback; use OpenRouter only for security reviews (Claude Opus) and model comparison.

8. **NVIDIA model timeout variability (May 2026)** — `meta/llama-3.3-70b-instruct` times out consistently at 60s+ from sandbox, but `nvidia/llama-3.3-nemotron-super-49b-v1` responds in ~1.9s. The NVIDIA catalog rotates models; some models may be overloaded or rate-limited. Always test with multiple models and prefer the one that responds. Use `https://integrate.api.nvidia.com/v1/models` to list currently available models.

### Testing Script Template

```python
import json, urllib.request, urllib.error, time, os

# Load keys from .env
env_vars = {}
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env_vars[k] = v

def test_provider(name, endpoint, key, model, body, timeout=15):
    start = time.time()
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read())
            elapsed = (time.time() - start) * 1000
            text = result["choices"][0]["message"]["content"][:80]
            tokens = result.get("usage", {}).get("total_tokens", "?")
            return f"PASS {elapsed:.0f}ms {tokens}tok → {text}"
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        err = json.loads(e.read())
        return f"FAIL HTTP {e.code} {elapsed:.0f}ms → {str(err.get('error', err))[:150]}"
    except Exception as e:
        return f"ERROR → {str(e)[:150]}"

# Example tests
print(test_provider("DeepSeek", "https://api.deepseek.com/v1/chat/completions",
    env_vars["DEEPSEEK_API_KEY"], "deepseek-v4-pro",
    {"model": "deepseek-v4-pro", "max_tokens": 50, "temperature": 0.05,
     "messages": [{"role": "user", "content": "Define RAG in 1 line."}]}))
```
