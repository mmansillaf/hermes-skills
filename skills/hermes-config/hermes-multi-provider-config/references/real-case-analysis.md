# Real Case: El Peruano RAG — Multi-Provider Audit & Implementation (2026-05-04)

## Context

Single developer building a legal RAG SaaS (El Peruano). One Linux laptop + one Ubuntu VM for deployment testing. Hermes Agent v0.12.0 running in CLI mode. Main project: `GRegElPeruano_v5.1` (Python/FastAPI/SQLite/Qdrant/Neo4j/Groq).

## Pre-Implementation State Discovered

### Provider Config
- Primary: DeepSeek V4-Pro (deepseek-v4-pro)
- Fallback: DeepSeek Chat (SAME PROVIDER — false safety net)
- All 9 auxiliary tasks: `provider: auto` → silently routing to DeepSeek V4-Pro
- max_context_tokens: 16000 (capped, DeepSeek supports 1M)
- prompt_caching.cache_ttl: 5m (too short for dev sessions)

### Critical Finding #1: Auxiliary Token Waste
Every session_search, compression, title_generation, and curator call was consuming DeepSeek V4-Pro tokens. Estimated 30% of total token spend was on mechanical tasks solvable with free Google Gemini 2.5 Flash.

### Critical Finding #2: False Fallback
Config showed only `deepseek-chat` as fallback. If DeepSeek API went down entirely, Hermes had no alternative provider.

### Critical Finding #3: Context Cap
16K context cap meant sessions exceeding ~25 messages would trigger compression even though DeepSeek V4-Pro supports 1M tokens.

### Critical Finding #4: Groq Context Mismatch
User reported Groq failing with "context limit" errors. Root cause: small-context Groq models (gemma-4-9b = 8K, mixtral-8x7b = 32K) can't handle accumulated context in long dev sessions.

### Critical Finding #5: Env Vars Missing
`.hermes/.env` only had DEEPSEEK_API_KEY and KIMI_API_KEY. Missing: GOOGLE_AI_STUDIO_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, NVIDIA_BUILD_API_KEY.

## Implementation Applied (2026-05-04)

### 1. Backup
```
cp ~/.hermes/config.yaml ~/hermes_config_backup_20260504.yaml
Created state document: ~/hermes_backup_20260504.md
```

### 2. Env Vars Added
GROQ_API_KEY, GOOGLE_AI_STUDIO_API_KEY, OPENROUTER_API_KEY, NVIDIA_BUILD_API_KEY, TAVILY_API_KEY, SCRAPEGRAPHAI_API_KEY all added to ~/.hermes/.env.

### 3. Auxiliary Models Configured
```bash
hermes config set auxiliary.compression.provider google_ai_studio
hermes config set auxiliary.compression.model gemini-2.5-flash
hermes config set auxiliary.session_search.provider google_ai_studio
hermes config set auxiliary.session_search.model gemini-2.5-flash
hermes config set auxiliary.title_generation.provider google_ai_studio
hermes config set auxiliary.title_generation.model gemini-2.5-flash
hermes config set auxiliary.curator.provider google_ai_studio
hermes config set auxiliary.curator.model gemini-2.5-flash
```

### 4. Fallback Chain
kimi/kimi-k2.6 → google/gemini-2.5-flash → groq/llama-3.3-70b-versatile

### 5. Cache
hermes config set prompt_caching.cache_ttl 30m

### 6. Verification
hermes doctor: DeepSeek OK, Kimi OK, OpenRouter OK. Google AI Studio and Groq pending first-use verification.

## Final State

| Role | Provider | Model | Context | Cost |
|------|----------|-------|---------|------|
| Primary | DeepSeek | deepseek-v4-pro | 1M | Paid |
| Auxiliary | Google AI Studio | gemini-2.5-flash | 1M | $0 |
| Fallback #1 | Kimi | kimi-k2.6 | 256K | Paid |
| Fallback #2 | Google AI Studio | gemini-2.5-flash | 1M | $0 |
| Fallback #3 | Groq | llama-3.3-70b-versatile | 128K | $0 |

**Estimated savings: 30-40% token reduction** by offloading mechanical tasks to free models.

## Key Lessons

1. **Always audit auxiliary.*.provider first** — the "auto" default wastes tokens
2. **Same-provider fallback is not a fallback** — always include Google AI Studio (free, reliable)
3. **hermes config set beats manual YAML editing** — no syntax errors, idempotent
4. **Backup before config changes** — 5 min, infinite rollback safety
5. **Google AI Studio model names**: use `gemini-2.5-flash` not `gemini-3.1-flash` (doesn't exist)
6. **Groq fallback**: only `llama-3.3-70b-versatile` (128K) has enough context. Never gemma-4-9b (8K) or mixtral (32K)
7. **Never paste API keys in commands** — use env vars from .env file
