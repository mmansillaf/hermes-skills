---
name: hermes-multi-provider-config
description: "Configure Hermes Agent with multiple LLM providers — smart routing, auxiliary models, semantic caching, fallback chains, context compression, budget tracking, and cost optimization. Covers the full multi-provider architecture: routing matrices, tier-based fallback, slash commands for development workflows, and provider-specific tactics."
category: software-development
tags: [hermes, multi-provider, routing, caching, cost-optimization, llm, config]
version: 1.0
---

# Hermes Multi-Provider Configuration

## When to Use

When configuring Hermes Agent to use multiple LLM providers intelligently — routing tasks to the right model, reducing token costs, enabling fallbacks, and optimizing session performance. Use this when:

- Setting up a new Hermes instance with 2+ LLM providers
- Optimizing token costs (target: 50-70% reduction)
- Enabling automatic failover when a provider hits rate limits
- Configuring smart routing by task type
- Setting up semantic caching for iterative development sessions
- Adding auxiliary models for mechanical tasks (compression, formatting, evaluation)

## Core Architecture

Hermes with multi-provider uses a tiered architecture:

```
User Query
    │
    ▼
┌──────────────────┐
│  Smart Router     │  ← Regex-based intent classification (local, free)
│  (classifier)     │
└──────┬───────────┘
       │
       ├── "refactor|arquitectura|debug" → TIER 1: DeepSeek V4-Pro (reasoning)
       ├── "genera|código|implementa"    → TIER 2: Kimi K2.6 (coding)
       ├── "proto|script|poc"           → TIER 3: Groq/Gemini Flash (fast)
       └── "formatea|lint|json|yaml"    → TIER 4: Groq gemma-4-9b (ultra-cheap)
                    │
                    ▼ (on failure)
            Fallback Chain (cascading)
                    │
                    ▼
         ┌──────────────────┐
         │  Semantic Cache   │  ← 90% discount on cache hits (DeepSeek)
         │  (sim ≥ 0.94)     │
         └──────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  Auxiliary Models │  ← Compression, evaluation, formatting
         │  (cheap/free)     │     at ~3% the cost of frontier models
         └──────────────────┘
```

## 1. Smart Routing Matrix

Which provider/model for which task, with justification:

| Task Type | Primary | Fallback | Why | Relative Cost |
|-----------|---------|----------|-----|---------------|
| Architecture, design, trade-offs | DeepSeek V4-Pro | OpenRouter → Claude Opus 4.7 | Deep reasoning, MoE efficient | High |
| Requirements, user stories | Kimi K2.6 | OpenRouter → GPT-5.4 | Long-horizon planning, sub-agents | High |
| Complex code generation | Kimi K2.6/K2.5 Turbo | Groq → llama-3.3-70b | Best Coding Index (47.1), 85 tok/s | Medium |
| Boilerplate, CRUD, scaffolding | Google Gemini 3.1 Flash | Groq → mixtral-8x7b | Speed, multimodal, 1M context | Low |
| Autocomplete, tab-complete | Groq llama-3.3-70b | NVIDIA → Nemotron 3 | <200ms latency | Very Low |
| Stack trace analysis | DeepSeek V4-Pro | OpenRouter → Claude | Causal reasoning, race conditions | High |
| Visual debug (screenshots) | Google Gemini 3.1 Pro | Kimi → K2.6 | Agentic Vision, reduces hallucinations | Medium |
| Common errors (quick fixes) | NVIDIA Build / Groq gemma | Groq → Llama 3.3 70B | Instant response | Very Low |
| Architectural code review | DeepSeek V4-Pro | OpenRouter → Claude | Anti-pattern detection, invariants | High |
| Style/lint review | Kimi K2.6 | Google → Gemini 3.1 Flash | Consistency, code smells | Medium |
| Security review (OWASP) | OpenRouter Claude Opus 4.7 | DeepSeek → V4-Pro | 45% of AI code has vulns; Claude leads security | High |
| Multi-file refactor | Kimi K2.6 | OpenRouter → Claude Sonnet | Multi-file editing, 256K context | High |
| Single function/class refactor | Groq llama-3.3-70b | Google → Gemini 3.1 Flash | Surgical, low latency | Low |
| Simplification (Karpathy rule #2) | DeepSeek V4-Pro | Kimi → K2.6 | "If 200 lines could be 50, rewrite it" | Medium |
| Proto/PoC (throwaway) | Google Gemini 3.1 Pro (Build Mode) | Kimi → K2.5 Turbo | Live preview, 2 clicks to deploy | Low |
| Script (one-off, data analysis) | NVIDIA Nemotron 3 | Groq → mixtral-8x7b | GPU-optimized local | Very Low |
| Terraform/Pulumi (IaC) | DeepSeek V4-Pro | OpenRouter → GPT-5.4 | Resource dependency reasoning | Medium |
| Docker, nginx, systemd | Google Gemini 3.1 Pro | Groq → llama-3.3-70b | Multimodal: reads configs, logs, diagrams | Medium |
| CI/CD pipelines (YAML) | OpenRouter → Claude Sonnet | Kimi K2.6 | Complex matrices, conditionals, secrets | Medium |
| Monitoring (Grafana/PromQL) | Google Gemini 3.1 Flash | Groq → mixtral-8x7b | Dashboard config, queries | Low |
| History compression | Google Gemini 2.5 Flash | Groq → gemma-4-9b | Mechanical task, 1M context, ~3% frontier cost | Minimal |
| Benchmark/evaluation | Google Gemini 2.5 Flash | NVIDIA → Nemotron 3 | Code evaluation, metrics, reports | Minimal |

## 2. Decision Tree (Mental Algorithm)

```
Is this a deep reasoning or architectural task?
├─ YES → DeepSeek V4-Pro (fallback: OpenRouter → Claude Opus 4.7)
└─ NO → Is this complex or multi-file code?
    ├─ YES → Kimi K2.6 (fallback: OpenRouter → Claude Sonnet 4.6)
    └─ NO → Is this visual or multimodal?
        ├─ YES → Google AI Studio Gemini 3.1 Pro
        └─ NO → Is this low-latency or repetitive?
            ├─ YES → Groq llama-3.3-70b (ultra-fast)
            └─ NO → Is this local/GPU-optimized?
                ├─ YES → NVIDIA Build Nemotron 3
                └─ NO → OpenRouter (best available model)
```

## 3. Auxiliary Models (Critical Cost Saver)

Three auxiliary models handle mechanical tasks at minimum cost, keeping the primary model focused on reasoning.

### Preferred Configuration Method: `hermes config set`

The YAML examples below show the equivalent config. The recommended way to apply them is via CLI — avoids YAML syntax errors and preserves file structure:

```bash
# Apply auxiliary model overrides (replace "auto" with free providers)
hermes config set auxiliary.compression.provider google_ai_studio
hermes config set auxiliary.compression.model gemini-2.5-flash
hermes config set auxiliary.session_search.provider google_ai_studio
hermes config set auxiliary.session_search.model gemini-2.5-flash
hermes config set auxiliary.title_generation.provider google_ai_studio
hermes config set auxiliary.title_generation.model gemini-2.5-flash
hermes config set auxiliary.curator.provider google_ai_studio
hermes config set auxiliary.curator.model gemini-2.5-flash

# Verify: all auxiliary tasks should now show explicit providers
hermes config show | grep -A2 "auxiliary\."
```

The resulting YAML:

```yaml
auxiliary:
  compression:
    provider: google_ai_studio
    model: gemini-2.5-flash
    temperature: 0.0
    max_tokens: 4096
    # MUST have context window ≥ 128k

  evaluation:
    provider: google_ai_studio
    model: gemini-2.5-flash
    temperature: 0.0
    # For code evaluation, tests, benchmarks

  # Also override these auto→auto fields:
  session_search:
    provider: google_ai_studio
    model: gemini-2.5-flash
  title_generation:
    provider: google_ai_studio
    model: gemini-2.5-flash
  curator:
    provider: google_ai_studio
    model: gemini-2.5-flash
```

### Google AI Studio Model Names (CORRECT as of May 2026)

The free tier exposes these models. Use exact names — the user-facing product names differ from API model IDs:

| User-Facing Name | API model ID | Context | Cost | Use For |
|-----------------|-------------|---------|------|---------|
| Gemini 2.5 Flash | `gemini-2.5-flash` | 1M | Free tier | Compression, session search, titles, mechanical tasks |
| Gemini 2.5 Pro | `gemini-2.5-pro` | 1M | Free tier (limited) | Complex reasoning fallback |

**⚠️ Common naming mistakes to avoid:**
- `gemini-3.1-flash` → DOES NOT EXIST. Use `gemini-2.5-flash`.
- `gemini-pro` → Too generic. Use `gemini-2.5-pro`.
- `gemini-flash` → Too generic. Use `gemini-2.5-flash`.

**Impact:** ~30% of all LLM calls are mechanical (compression, formatting, evaluation). Offloading these to free/cheap models saves 30-50% of total token spend.

## 4. Semantic Caching

Cache responses by semantic similarity, not exact match:

```yaml
cache:
  enabled: true
  strategy: semantic
  similarity_threshold: 0.94    # High threshold to avoid false positives
  ttl: 7200                      # 2 hours (development context window)
  max_size: 200MB
  warmup: true                   # Preload common prompts at startup
  warmup_prompts:
    - "Review this Python function for security vulnerabilities and code smells"
    - "Refactor this function to reduce cyclomatic complexity"
    - "Generate a FastAPI endpoint with SQLAlchemy ORM and Pydantic schemas"
    - "Debug this Python traceback and suggest fixes"
    - "Write unit tests for this function using pytest with fixtures and mocks"
```

**Provider-specific cache discounts:**
| Provider | Cache Discount | Tactic |
|----------|---------------|--------|
| DeepSeek | 90% on cache hits | Keep AGENTS.md, KARPATHY_RULES.md, SOUL.md stable. Never change mid-session |
| Kimi | Automatic (Fireworks) | Reuse scaffolding/boilerplate prompts. Cache is transparent |
| Google AI Studio | Free tier | Use for static analysis, docs, visual debug |
| Groq | N/A (ultra-fast) | Use for tab-complete, common errors, simple queries |
| OpenRouter | Depends on upstream | Inherits upstream cache (e.g., DeepSeek via OpenRouter = 90%) |
| NVIDIA Build | Local (no API cost) | Use for scripts, data analysis, local-only tasks |

### Semantic Cache — Domain-Specific Threshold Tuning

The optimal `similarity_threshold` depends on your domain. For legal/professional domains where semantically similar queries have juristically opposite meanings, use 0.96 (not the default 0.94). For pure dev environments, 0.94 is safe. See `references/semantic-cache-domain-tuning.md` for the full decision framework, TTL trade-offs, and the 0.97 trap.

### Domain-Specific Threshold Tuning

The default 0.94 threshold assumes general-purpose conversations. For domains with high precision requirements:

| Domain | Recommended Threshold | TTL | Hit Rate | Rationale |
|--------|----------------------|-----|----------|-----------|
| General development | 0.94 | 7200 (2h) | 20-25% | Default — good balance |
| Regulated (legal, medical, financial) | 0.96 | 3600 (1h) | 12-18% | Prevents false positives from near-miss semantics |
| Extreme precision | 0.97 | 1800 (30m) | 5-8% | Rarely worth the overhead (~$0.04/session) |

**Mitigation for RAG-based applications:** If your prompts inject document chunks that change between sessions, the cache naturally misses even at 0.94 because the injected context changes the full prompt embedding. The risk is highest for pure-reasoning questions without injected context.

## 5. Context Compression

Prevent context bloat in long development sessions:

```yaml
context_compression:
  enabled: true
  trigger:
    token_count: 45000          # Compress at 45K tokens
    message_count: 25            # Or after 25 messages
  strategy: semantic_summary
  preserve:
    - "architectural decisions"
    - "database schemas"
    - "API contracts (OpenAPI/GraphQL)"
    - "critical errors resolved"
    - "final approved configurations"
    - "Karpathy rules applied"
  discard:
    - "failed code attempts"
    - "intermediate debug reasoning (already resolved)"
    - "successful terminal outputs without historical value"
    - "successful lint command outputs"
```

**Impact:** 50-70% reduction in input tokens for sessions exceeding 50 messages. Also improves response quality by keeping context focused.

## 6. Budget and Cost Optimization

```yaml
budget:
  monthly_limit_usd: 150.00
  daily_limit_usd: 8.00
  auto_optimize:
    enabled: true
    threshold: 0.85             # At 85% of daily limit, downgrade
    downgrade_tier:
      from: tier_2_coding
      to: tier_3_fast
  emergency_downgrade:
    threshold: 0.95
    to: tier_4_ultra_cheap

cost_tracking:
  enabled: true
  breakdown_by_provider: true
  breakdown_by_model: true
  breakdown_by_task_type: true
  alert_threshold_daily_usd: 8.00
  alert_threshold_monthly_usd: 120.00

# Budget allocation by task type
allocation:
  reasoning_critical:   35%    # DeepSeek V4-Pro, Claude Opus
  coding_complex:       25%    # Kimi K2.6
  coding_fast:          15%    # Groq, Gemini Flash
  infra_cloud:          10%    # DeepSeek, Gemini Pro
  compression_batch:    8%     # Gemini Flash, Groq small
  emergency_reserve:    7%     # LLM Council or unexpected critical debug
```

### Token Budgeting by Session Type

| Session Type | Input Budget | Output Budget | Primary Model | Strategy |
|-------------|-------------|---------------|---------------|----------|
| Critical bug debug | 50K | 10K | DeepSeek V4-Pro | Single focused chat |
| New feature (medium) | 30K | 15K | Kimi K2.6 | 1-2 sessions if needed |
| Multi-file refactor | 40K | 20K | Kimi K2.6 | Use /compress between files |
| PR review | 10K | 5K | Kimi K2.6 or Gemini Flash | Scope limited to diff |
| Proto/PoC | 15K | 10K | Google AI Studio Flash | Free or very cheap |
| Infra Terraform | 20K | 10K | DeepSeek V4-Pro | Generate once, iterate locally |

## 7. Slash Commands for Development Workflows

### /debug — Multi-Level Intelligent Debugging

```
/debug [level: quick|deep|root_cause]

quick:   Groq llama-3.3-70b (<300ms) — fix this error quickly
deep:    DeepSeek V4-Pro — 3 most likely root causes with probabilities
root_cause: DeepSeek V4-Pro — 5-Whys analysis to systemic cause
```

### /review — Code Review with Karpathy Rules + OWASP

```
/review [scope: diff|file|module|pr] [security: basic|standard|paranoid]

Steps:
1. Kimi K2.6 → style, complexity, Karpathy compliance
2. Claude Opus 4.7 → OWASP Top 10, secrets, injection risks
3. Gemini 2.5 Flash → dead code, unused imports, doc gaps
```

### /refactor — Safe Refactoring

```
/refactor <target> [strategy: extract_method|rename|simplify|decouple|modernize]

3-step workflow:
1. DeepSeek V4-Pro → analyze dependencies, backward compat, rollback plan
2. Kimi K2.6 → apply surgical changes only
3. Gemini 2.5 Flash → verify behavior preservation
```

### /simplify — Forced Simplification (Karpathy Mode)

```
/simplify

Rules (non-negotiable):
- Max 50 lines per function
- No abstractions used only once
- No error handling for impossible scenarios
- Must be understandable in 30 seconds
- "If 200 lines could be 50, rewrite it"
```

### /proto — Rapid Prototyping

```
/proto <description> [tech: python_script|react_fastapi|cli_tool|data_viz|api_mock]

Rules:
- This is THROWAWAY code
- Use hardcoded data for speed
- Skip error handling for non-critical paths
- After validation: rewrite with discipline for production
```

### /cost — Cost Monitoring

```
/cost

Analyzes usage data and suggests:
1. Overused providers/models
2. Cache/batch opportunities
3. Tasks that could downgrade to cheaper models
4. Projected monthly cost
5. Actionable recommendations
```

## 8. Security Pipeline for AI-Generated Code

**45% of AI-generated code introduces known OWASP vulnerabilities (Veracode 2025).**

```
Developer writes/requests code
    ↓
[1. Local regex: obvious secrets]
    ↓ PASS
[2. Gemini 2.5 Flash: basic security scan]
    ↓ PASS
[3. Kimi K2.6: Karpathy rules review]
    ↓ PASS
[4. Claude Opus 4.7: deep security scan]  ← via OpenRouter
    ↓ PASS
[5. Automated tests: pytest + coverage]
    ↓ PASS
[6. Bandit: static OWASP scan]
    ↓ PASS
[7. Commit allowed]
```

**Code requiring mandatory human approval (no auto-commit):**
- Auth/auth changes
- Payment/financial data handling
- Production infrastructure changes
- New external dependencies
- PII/sensitive data handling
- Code bypassing existing validations

## 9. Provider-Specific Tactics

### DeepSeek
- Best for: reasoning, architecture, debug, simplification
- **Context Caching (automatic, no code changes):** DeepSeek has disk-based context caching that gives **50x discount** on cache hits:
  - Cache miss (normal input): **$0.14/1M tokens**
  - Cache hit: **$0.0028/1M tokens** (2% of miss price)
  - Output: **$0.28/1M tokens** (no caching on output)
  - Users save **>50% on average** without any optimization
- **How cache hits work:** Only **prefix matching** from token 0. The system caches prefix units at request boundaries and detected common prefixes. A subsequent request must match the prefix **fully** from the start. Partial mid-string matches do NOT trigger cache hits. Cache persistence is best-effort (minutes to days after last use).
- **Maximizing cache hits:**
  - Keep SOUL.md, system prompt, and config **stable across turns** (don't change mid-session)
  - Maintain **long sessions** instead of frequent `/new` — cache accumulates turn to turn
  - Put **static context first**, variable content last in user messages
  - Avoid timestamps or dynamic values at the start of messages
  - First token latency drops from 13s to 500ms on a 128K cached prefix
- **Pricing summary:** | Type | Price/1M | vs List |
  | Cache miss | $0.14 | 100% |
  | Cache hit | $0.0028 | **2%** |
  | Output | $0.28 | — |
- Cache system uses 64-token storage units; content under 64 tokens isn't cached. No concurrency or rate limits on the API.
- Pitfall: `reasoning_content` field crash — use `reasoning_effort: none` or thinking-toggle
- Rate limit: 1.5M TPD (organization-level), resets at UTC midnight

### Kimi
- Best for: complex coding, multi-file editing, planning
- Strength: 300 sub-agents, 256K context, 85 tok/s
- Cache: Automatic via Fireworks, transparent to user

### Google AI Studio
- Best for: prototypes, visual debug, static analysis, documentation
- Strength: Generous free tier, 1M context, multimodal
- Models: Gemini 3.1 Pro (complex), Flash (fast/cheap), 2.5 Flash (mechanical)

### Groq
- Best for: low-latency tasks, autocomplete, common errors, tab-complete
- Strength: <200ms TTFT, free tier
- Models: llama-3.3-70b (general fast), mixtral-8x7b (even faster), gemma-4-9b (ultra-cheap mechanical)

### OpenRouter
- Best for: model comparison, security reviews, fallback aggregator
- Strength: Access to Claude, GPT, Gemini, DeepSeek, Kimi, Qwen in one API
- Use for: A/B testing models, security deep scans (Claude Opus leads security benchmarks)

### NVIDIA Build
- Best for: cloud API with 120+ models (Kimi, DeepSeek, Llama, Nemotron, Mistral, Qwen), data analysis, fast fallback
- **NVIDIA Build is a cloud API** — accessible at `https://integrate.api.nvidia.com/v1`. Does NOT require a local GPU. The API key works from any machine.
- Key advantage: routes to Kimi K2.6 (`moonshotai/kimi-k2.6`), DeepSeek V4-Pro (`deepseek-ai/deepseek-v4-pro`), Llama 3.3 70B (`meta/llama-3.3-70b-instruct`), and Nemotron Super (`nvidia/llama-3.3-nemotron-super-49b-v1`) through a single API key
- **Critical workaround**: when direct Kimi API key returns 401 (expired/invalid), route Kimi through NVIDIA Build using model ID `moonshotai/kimi-k2.6`
- **Correct model names** (verified May 2026): `nvidia/llama-3.3-nemotron-super-49b-v1` (NOT `nvidia/nemotron-3-super`), `moonshotai/kimi-k2.6`, `deepseek-ai/deepseek-v4-pro`, `meta/llama-3.3-70b-instruct`
- List available models: `curl -H "Authorization: Bearer $NVIDIA_BUILD_API_KEY" https://integrate.api.nvidia.com/v1/models`

## 10. Implementation Checklist

### Phase 0 — Backup (5 min, mandatory before any change)
- [ ] `cp ~/.hermes/config.yaml ~/hermes_config_backup_$(date +%Y%m%d).yaml`
- [ ] Document current state: provider, model, auxiliary settings, memory usage, session count
- [ ] Run `hermes doctor` to verify baseline health
- [ ] Save state document to `~/hermes_backup_YYYYMMDD.md`

### Phase 1 — Immediate (30 min, $0, highest ROI)
- [ ] Add missing API keys to `~/.hermes/.env`:
  ```bash
  # Required keys for auxiliary models and fallback:
  GOOGLE_AI_STUDIO_API_KEY=<key>    # Free tier — for compression, sessions, titles
  GROQ_API_KEY=<key>                # Free tier — for fast fallback
  OPENROUTER_API_KEY=<key>          # Free tier — for security reviews
  # Optional: KIMI_API_KEY, NVIDIA_BUILD_API_KEY, TAVILY_API_KEY
  ```
- [ ] Apply auxiliary model overrides (all 9 services — 4 core + 5 often overlooked):
  ```bash
  # Core 4 (most critical):
  hermes config set auxiliary.compression.provider google_ai_studio
  hermes config set auxiliary.compression.model gemini-2.5-flash
  hermes config set auxiliary.session_search.provider google_ai_studio
  hermes config set auxiliary.session_search.model gemini-2.5-flash
  hermes config set auxiliary.title_generation.provider google_ai_studio
  hermes config set auxiliary.title_generation.model gemini-2.5-flash
  hermes config set auxiliary.curator.provider google_ai_studio
  hermes config set auxiliary.curator.model gemini-2.5-flash
  
  # Remaining 5 (often left as "auto" → wastes DeepSeek tokens):
  hermes config set auxiliary.vision.provider google_ai_studio
  hermes config set auxiliary.vision.model gemini-2.5-flash
  hermes config set auxiliary.web_extract.provider google_ai_studio
  hermes config set auxiliary.web_extract.model gemini-2.5-flash
  hermes config set auxiliary.skills_hub.provider google_ai_studio
  hermes config set auxiliary.skills_hub.model gemini-2.5-flash
  hermes config set auxiliary.approval.provider google_ai_studio
  hermes config set auxiliary.approval.model gemini-2.5-flash
  hermes config set auxiliary.mcp.provider google_ai_studio
  hermes config set auxiliary.mcp.model gemini-2.5-flash
  ```
- [ ] Configure real multi-provider fallback chain:
  ```bash
  hermes config set fallback_providers '[{"provider":"kimi","model":"kimi-k2.6","base_url":"https://api.moonshot.ai/v1","temperature":1,"max_tokens":8192},{"provider":"google_ai_studio","model":"gemini-2.5-flash","base_url":"https://generativelanguage.googleapis.com/v1beta","temperature":0.05,"max_tokens":4096},{"provider":"groq","model":"llama-3.3-70b-versatile","base_url":"https://api.groq.com/openai/v1","temperature":0.1,"max_tokens":8192}]'
  ```
- [ ] Raise cache TTL: `hermes config set prompt_caching.cache_ttl 30m`
- [ ] Verify: `hermes doctor` — confirm DeepSeek, Kimi, OpenRouter APIs all pass
- [ ] Manual connectivity test for new providers (use env vars, never paste keys in commands)

### Phase 2 — Short-term (1-2 hrs)
- [ ] Activate pending API keys and add to fallback chain
- [ ] Configure `smart_routing` rules
- [ ] Enable semantic caching
- [ ] Set up budget tracking with alerts

### Phase 3 — As needed
- [ ] Implement LLM Council for architectural decisions (2-3/month max)
- [ ] Configure slash commands (/debug, /review, /refactor, /simplify, /proto, /cost)
- [ ] Run internal benchmark: 20 prompts across 4 models via OpenRouter

## Pitfalls

- **Config changes require Hermes restart** — kill old processes first
- **.env keys NOT loaded if added after Hermes startup** — Hermes reads `~/.hermes/.env` ONLY at process start. If you add API keys after Hermes is already running, they will NOT be available to the running process. Classic symptom: auxiliary tasks fail with "Provider X is set in config.yaml but no API key was found" even though the key exists in `.env`. Diagnosis: run `python -c "import os; print(os.environ.get('GOOGLE_AI_STUDIO_API_KEY', 'NOT SET'))"` — if it prints 'NOT SET' but the key is in `.env`, Hermes started before the key was added. Fix: kill and restart Hermes. This affects ALL env vars, not just API keys — `hermes config set` changes are live, but `.env` changes require restart.
- **DeepSeek `reasoning_content` crash** — non-retryable, use `reasoning_effort: none` or toggle
- **Multiple Hermes instances share rate limit pool** — two sessions = faster exhaustion
- **Semantic cache threshold too low (<0.90)** — risk of false cache hits returning wrong answers
- **Semantic cache in regulated domains (legal, medical, financial)** — The default threshold of 0.94 works well for general development but may produce false positives in domains where small wording differences carry large semantic consequences (e.g., "Ley de contrataciones del Estado" vs "Ley de contrataciones laborales" are juridically opposite but semantically close). For legal/medical/financial use cases, raise threshold to 0.96 and reduce TTL to 3600 (1 hour). At 0.96, only near-identical paraphrases collide — the false-positive window is extremely narrow. At 0.97, the hit rate drops to 5-8% (essentially useless: ~$0.04 savings per 50-request session). Note: the semantic cache only intercepts Hermes-to-LLM calls, not external RAG applications. If your RAG injects changing document chunks into prompts, the varied context naturally prevents false hits even at lower thresholds.
- **NVIDIA Build is a cloud API — NO GPU REQUIRED** — The API is at `https://integrate.api.nvidia.com/v1` and works from any machine with an API key. The name is misleading: it's a cloud-hosted inference API with access to 120+ models (Kimi, DeepSeek, Llama, Nemotron, Mistral, Qwen, GPT-OSS). It does NOT need a local NVIDIA GPU in any way. However, it adds ~500ms routing overhead vs direct provider APIs.
- **OpenRouter adds latency** — ~500ms overhead vs direct provider. Only use for fallback/security, not primary
- **Legal-domain semantic cache calibration** — When mixing legal queries with dev tasks, the semantic cache threshold needs special attention. Legal queries can be semantically close but juridically opposite ("Ley de contrataciones del Estado" vs "Ley de contrataciones laborales"). Threshold 0.96 with TTL 1h provides a safe balance: ~12-18% hit rate in dev sessions, near-zero false positives in legal queries. Raise to 0.97 if any false positive is observed — but hit rate drops to 5-8% making it nearly useless. The alternative is to accept the tradeoff or disable semantic caching entirely for legal workloads. Threshold 0.94 is too lax for legal domains.
- **Budget auto-optimize can surprise you** — if you hit 85% of daily limit mid-session, responses silently downgrade to cheaper models. Check costs regularly.
- **CRITICAL: auxiliary models default to "auto"** — Hermes v0.12's default config sets ALL auxiliary tasks (compression, session_search, title_generation, vision, web_extract, etc.) to `provider: auto`. This silently routes them to the primary provider (e.g., DeepSeek V4-Pro), wasting ~30% of tokens on mechanical tasks that could run on free models. Always explicitly configure `auxiliary.compression.provider`, `auxiliary.session_search.provider`, and `auxiliary.title_generation.provider` to cheap/free alternatives BEFORE doing anything else. This is the single highest-ROI config change.
- **User preference: "mayor contexto + mejor razonamiento"** — When the user says "siempre procura usar el que tenga mayor contexto y sea mejor en razonamiento", interpret this as: prioritize models with the largest context window and best reasoning capability. Default ranking: DeepSeek V4-Pro (1M ctx, elite reasoning) > Kimi K2.6 (256K ctx, coding index 47.1) > Google Gemini 2.5 Pro (1M ctx) > Groq Llama 3.3 70B (128K ctx) > Google Gemini 2.5 Flash (1M ctx, mechanical only). Flash is large-context but NOT reasoning-focused — reserve for auxiliary tasks.
- **Groq + small-context models = silent failures** — Groq's free tier models have widely varying context windows: llama-3.3-70b (128K), mixtral-8x7b (32K), gemma-4-9b (8K). If you configure Groq as a fallback with a small-context model, long development sessions (50+ messages) will exceed the window and fail silently or with cryptic errors. Only use `llama-3.3-70b-versatile` for Groq fallback; use `gemma-4-9b` ONLY for single-shot formatting tasks.
- **max_context_tokens cap defeats large-context providers** — Hermes defaults to `max_context_tokens: 16000`. DeepSeek V4-Pro supports 1M tokens, but Hermes will compress/truncate at 16K UNLESS you raise this value. For deep reasoning sessions, set this to at least 48000. Balance against cost: larger context = more input tokens = higher per-request cost.
- **Same-provider fallback is a false safety net** — Configuring `fallback_providers` with the same provider but a different model (e.g., DeepSeek V4-Pro → DeepSeek Chat) fails if the provider itself is down or rate-limited. Always include at least one fallback from a different provider (Google AI Studio is ideal: free, reliable, 1M context). If Kimi direct API fails (401), route `moonshotai/kimi-k2.6` through NVIDIA Build as a workaround.
- **Always backup config before changes** — Run `cp ~/.hermes/config.yaml ~/hermes_config_backup_$(date +%Y%m%d).yaml` and create a state document before modifying. Rollback is a single `cp` away.
- **Always verify connectivity after config changes** — Run provider-specific tests for each configured provider using the methodology in `references/provider-testing.md`. Test each provider with a minimal query that exercises its intended role (reasoning for primary, summarization for auxiliary, simple response for fallback). Do NOT assume API keys work just because they're in `.env` — test them.
- **Groq + Cloudflare 1010 blocking** — Groq's API is behind Cloudflare protection. Requests from datacenter/sandbox IPs (including Hermes sandbox) get HTTP 403 with `error code: 1010`. The keys ARE valid — they work from residential/local machine IPs. When testing Groq from Hermes code execution sandbox, expect block. Test from the host machine directly instead.
- **Kimi direct API 401 workaround** — If Kimi API key returns 401 Invalid Authentication, check the endpoint first: `api.moonshot.ai` (correct) vs `api.moonshot.cn` (wrong). If `.ai` also fails, route Kimi K2.6 through NVIDIA Build: set fallback provider to `nvidia_build` with model `moonshotai/kimi-k2.6`. This requires `NVIDIA_BUILD_API_KEY` in `.env`.
- **Kimi K2.6 temperature constraint** — Kimi K2.6 ONLY accepts `temperature: 1`. Any other value causes HTTP 400 `"invalid temperature: only 1 is allowed for this model"`. Always set `temperature: 1` in Kimi fallback config.
- **NVIDIA Build is a cloud API, not local GPU** — The API is at `https://integrate.api.nvidia.com/v1` and works from any machine with an API key. No GPU required. However, it adds ~500ms routing overhead vs direct provider APIs.
- **NVIDIA model name mismatch** — `nvidia/nemotron-3-super` does NOT exist. Use `nvidia/llama-3.3-nemotron-super-49b-v1`. Always fetch the current model list from `https://integrate.api.nvidia.com/v1/models` before configuring NVIDIA models — the catalog rotates.

## References

- `references/comparativa-modelos-coding.md` — DeepSeek V4 Flash vs Gemini 2.5 Flash vs Groq para código (experiencia real del usuario)
- `references/provider-routing-matrix.md` — Full routing table with model versions and cost estimates
- `references/real-case-analysis.md` — Analysis of this document applied to El Peruano RAG project context
- `references/provider-testing.md` — Methodology for testing provider connectivity, real test results (May 2026), common failure patterns and fixes
- `references/hermes-token-tracker.md` — Tracking Hermes Agent's own token consumption (subagentes + conversación) via SQLite
- `references/cache-legal-domain.md` — Semantic cache threshold selection for legal domains (0.96 recommended vs default 0.94)
