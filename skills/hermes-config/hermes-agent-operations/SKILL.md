---
name: hermes-agent-operations
title: "Hermes Agent Operations — Diagnostics, Recovery, Optimization, and Config"
description: "Class-level umbrella for all Hermes Agent operational concerns — config provider errors, stuck CLI recovery, performance optimization, thinking mode management, and session resilience. Covers diagnosing and fixing common Hermes failures without manual config editing."
category: software-development
tags: [hermes, operations, diagnostics, recovery, optimization, config, thinking-mode]
---

# Hermes Agent Operations

## When to Use

When Hermes Agent itself is malfunctioning — config errors, frozen CLI, slow responses, thinking-mode crashes, provider authentication issues.

## 1. Config & Provider Errors

### Pattern A: Flat vs Nested Config (Version Mismatch)
Config format evolves. Version v22+ expects `model:` as a nested section. Flat keys at root level cause "Unknown provider" errors.

**Diagnose:** `hermes doctor 2>&1` — look for "Stale root-level config keys."

**Fix:** Move `provider:`, `model:`, `api_key` fields under a `model:` section in `~/.hermes/config.yaml`.

### Pattern B: Gateway Provider Detection
The CLI auto-detects DeepSeek from `openai_base_url: https://api.deepseek.com` even with `provider: openai`. The gateway does NOT auto-detect — it strictly validates the provider name. Always use `provider: deepseek` when the backend is DeepSeek, regardless of API compatibility.

### Pattern D: `finish_reason='length'` — Response Truncation

Subagent responses or long documents truncated mid-output with `⚠️ Response truncated (finish_reason='length') - model hit max output tokens`.

**Root cause:** The model has no explicit `max_tokens` set, so the provider's default output limit applies. DeepSeek V4 Flash defaults to ~4K output tokens; Gemini 2.5 Flash defaults to ~8K. A 34KB markdown report exceeds any of these.

**Diagnose:**
```bash
grep max_tokens ~/.hermes/config.yaml
# If missing → model is using provider default
```

**Fix:**
```bash
hermes config set model.max_tokens 8192
```
Recommended values per provider:
| Provider | Recommended max_tokens | Notes |
|---|---|---|
| DeepSeek V4 Flash | 8192 | Balance speed vs. capacity |
| DeepSeek V4 Pro | 16384 | Larger context, slower TTFT |
| Gemini 2.5 Flash | 8192 | Default is already 8K; increase for reports |
| Gemini 2.5 Pro | 32768 | Long-document generation |

After setting, kill old Hermes processes and restart — config changes are not hot-reloaded.

**Workaround for large documents (>15KB):**
Even with `max_tokens=8192`, generating a 34KB report inline risks truncation. The subagent should:
1. **Write the file first** via `write_file()` — this is a tool call, not output tokens
2. **Respond with a short summary** (~3 paragraphs) + the file path
3. This guarantees delivery regardless of output token limits

### Pattern C: DeepSeek `reasoning_content` Crash\nDeepSeek thinking mode generates `reasoning_content` in responses. On next turn, DeepSeek requires this field in every assistant message. If session serialization loses it, HTTP 400 crashes the agent (non-retryable).\n\n**Fix:** Add to config.yaml:\n```yaml\nagent:\n  reasoning_effort: none\n```\nThis disables thinking tokens entirely. Values: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`.\n\n**Verification:** Kill old processes (they hold config in memory), restart Hermes, check logs: `grep reasoning_content ~/.hermes/logs/agent.log`.\n\n### Pattern E: Auxiliary Provider Credential Mismatch\n\nAll 10+ auxiliary services (vision, web_extract, compression, skills_hub, approval, mcp, title_generation, curator, session_search, etc.) can be explicitly set to a provider whose API key exists in `.env` but isn't detected by Hermes' auxiliary credential system. This causes silent failures: `web_extract` returns nothing, title_generation fails, session_search summaries don't generate.\n\n**Symptom:** Warning at session start: `⚠ Auxiliary title generation failed: Provider 'X' is set in config.yaml but no API key was found.`\n\n**Diagnose:**\n```bash\nhermes config get auxiliary.vision.provider\nhermes config get auxiliary.title_generation.provider\nhermes config get auxiliary.web_extract.provider\n# If any show 'google_ai_studio' or another provider not in active use: MISMATCH\n```\n\n**Fix — switch all to `auto` (inherits main provider):**\n```bash\nfor svc in vision web_extract compression skills_hub approval mcp \\\n           title_generation curator session_search tts_audio_tags \\\n           triage_specifier kanban_decomposer profile_describer \\\n           monitor background_review; do\n  hermes config set auxiliary.$svc.provider auto\n  hermes config set auxiliary.$svc.model \"\"\ndone\n\n# If you have free API keys, offload title_generation from your main provider:\n#   Option A (recommended, no env var): provider=google_ai_studio model=gemini-2.5-flash\n#   Option B (only if GROQ_API_KEY is set): provider=groq model=llama-3.3-70b-versatile\n# PITFALL: Do NOT set to Groq without verifying GROQ_API_KEY exists - provider=auto is always safe\n```\n\n**IMPORTANT:** Always use `hermes config set` — direct `patch` calls to `~/.hermes/config.yaml` are blocked by a safety guard (`Refusing to write to Hermes config file`). Discover this constraint BEFORE trying to edit the file.\n\n### Pattern F: MCP Server Config Changes Require Process Restart\n\nMCP server config (env vars, wrapper scripts, provider priority) is loaded when the watchdog spawns the process. Changing the wrapper script or provider keys does NOT hot-reload.\n\n**Fix:** Kill old MCP processes — the watchdog respawns them automatically:\n```bash\npkill -f "kindly-web-search"\nsleep 2\nhermes mcp test kindly-web-search   # Verify respawn\n```\n\nIf watchdog doesn't respawn after 5 seconds, kill ALL Hermes-related processes and start a new session. The MCP server is re-initialized on gateway startup.\n\n**Known case:** The kindly-web-search MCP wrapper originally only exported `SERPER_API_KEY`. After adding `TAVILY_API_KEY` export and swapping the provider priority in `search/__init__.py`, old processes continued serving with the old config until killed.\n\n## 2. CLI Diagnostics & Recovery (Stuck/Frozen Instance)

Use when Ctrl+C/D/Z don't work, Hermes shows "procesando..." indefinitely.

**Diagnosis sequence:**
```bash
# 1. Find all Hermes processes
ps aux | grep -i hermes | grep -v grep

# 2. Check process state
cat /proc/PID/status | grep -E "^(Name|State|Threads)"

# 3. Check PTY foreground processes
ls -la /proc/PID/fd/0
ps -t pts/X -o pid,stat,cmd --no-headers

# 4. Check signal handlers
cat /proc/PID/status | grep "^Sig"

# 5. Examine session data
ls -lt ~/.hermes/sessions/
python3 -c "
import json
with open('~/.hermes/sessions/session_TIMESTAMP.json') as f:
    msgs = json.load(f).get('messages', [])
for i, m in enumerate(msgs[-5:]):
    print(f'MSG {i}: [{m.get(\"role\",\"?\")}]')
"

# 6. Check logs
tail -30 ~/.hermes/logs/agent.log
tail -30 ~/.hermes/logs/errors.log
```

**Key states:**
- `S (sleeping)` + `ep_poll` = normal idle
- `S (sleeping)` + ESTABLISHED TCP + repeated log errors = **rate-limit loop** (see below)
- `D (disk sleep)` = I/O blocked, probably unrecoverable
- `R (running)` = actually working, wait or interrupt

### Rate-Limit Loop Diagnosis (Provider 429)

Session appears hung but is actually stuck in a retry loop: auxiliary LLM calls (session_search summaries, title generation) hit provider rate limits and keep retrying with fallbacks that also fail.

**Symptoms:**
- Process state is `S (sleeping)` but CPU ~5% and running for 5+ minutes
- `ss -tnp | grep PID` shows ESTABLISHED connection to API endpoint
- `tail -f ~/.hermes/logs/agent.log` shows repeated patterns:
  ```
  Auxiliary session_search: connection error on auto (Request timed out.)
  falling back to api-key (kimi-k2-turbo-preview)
  RateLimitError: Error code: 429
  Session summarization failed after 3 attempts
  ```
- The cycle repeats indefinitely (3 attempts per auxiliary call, then restarts)

**Diagnosis commands:**
```bash
# Find all Hermes processes and their connections
ps aux | grep hermes | grep -v grep
ss -tnp | grep <PID>

# Check what the process is stuck on
tail -30 ~/.hermes/logs/agent.log | grep -E "429|RateLimit|fallback|failed after"
```

**Root causes by provider:**
| Provider | Limit | Reset | Error pattern |
|---|---|---|---|
| DeepSeek | 1.5M TPD (org-level) | UTC midnight (most likely) | `429: organization TPD rate limit reached` |
| Kimi | Unknown | Unknown | Timeouts when used as fallback |

**Recovery options:**
1. **Wait** — if near UTC midnight, rate limits reset automatically (~19 min in observed case)
2. **Kill and restart with different provider** — `kill PID` then restart with `--model` flag or config change
3. **Let it recover** — the loop is non-destructive; session will resume when limits reset

**Note:** Multiple Hermes instances share the same provider API key and therefore the same rate limit pool. Two sessions running simultaneously can exhaust limits faster.

**Recovery:**
```bash
# Kill children first, then SIGTERM, then SIGKILL
ps --ppid PID -o pid --no-headers | xargs kill 2>/dev/null
kill PID
sleep 2 && kill -9 PID 2>/dev/null
```

Session data persists in `~/.hermes/sessions/` — no work is lost.

### Multiple Instances (VSCode + Terminal)
3+ Hermes instances + VSCode extensions + api_rest.py can cause unresponsive UI. Check:
```bash
ps aux | grep hermes | grep -v grep
# Kill stale dashboard processes
# Check Pylance (544MB+), Python extension (483MB+)
```

### api_rest.py Memory Bloat
If RSS > 1GB (expected: ~400MB for sentence-transformers), model was loaded multiple times:
```bash
kill <API_PID> && sleep 2 && python3 api_rest.py &
```

## 3. Performance Optimization

### Root Causes (ordered by impact)
1. System prompt bloat — memory + profile + tools can reach 18K+ tokens
2. Heavy model — large models have 3-5s TTFT
3. Memory saturation — >90% full with obsolete entries
4. Excess tool definitions — ~30 when only 8 needed
5. Session accumulation — 100+ sessions slow session_search

### Optimization Steps

**SOUL.md — Agent Identity (5 min, high impact):**
Replace `~/.hermes/SOUL.md` with an identity that sets behavioral rules for your domain. The SOUL.md is loaded as Layer 1 of the system prompt. For software development, use: Karpathy rules (think before coding, minimum code, surgical changes, goal-driven), type hints, error handling, docstrings, Spanish response with English technical terms. Target: ~1KB.

**.hermes.md — Project Context (15 min per project, high impact):**
Create `.hermes.md` in the root of each project directory. Hermes auto-loads it when working in that directory. Include: stack (languages, frameworks, DB), conventions (style, type hints, testing), key commands (make test, make lint), domain-specific rules. The file walks parents up to git root, so one file covers the whole repo.

See `references/systematic-optimization-audit.md` for the full 5-step workflow covering SOUL.md, .hermes.md, memory, and skill podding as a coordinated optimization operation.

**Memory Cleanup:** See `references/memory-audit.md` for the full 4-step methodology (identify ephemeral data, deduplicate stores, compact verbosity, execute). Key principle: facts that will be stale within 2 sessions do NOT belong in memory — use `session_search` to recover session-specific progress.

**User Profile Deduplication:** Consolidate to one comprehensive entry.

**Enable toolsets whitelist** in config.yaml (~6K tokens saved):
```yaml
enabled_toolsets:
  - terminal
  - file
  - search
  - web
  - session_search
  - skills
  - todo
  - delegation
```

**Delegation parallelism tuning:**
```yaml
delegation:
  max_concurrent_children: 5    # Default: 3. Increase for parallel subagent work (indexing, refactoring)
  max_async_children: 5         # Match above
```
For users with good rate limits (DeepSeek, Gemini), 5 is safe. Beyond 5 starts risking rate limits on most providers.

**DeepSeek context caching (automatic, 50x discount):**
DeepSeek V4 Flash has automatic disk-based context caching. No config needed:
- **Cache miss:** $0.14/1M tokens (standard price)
- **Cache hit:** $0.0028/1M tokens (2% — **50x cheaper**)
- **How it works:** If a request's prefix matches a prior request, the matching portion is served from cache. Cache persists "hours to days".
- **Maximizing hits:** Keep sessions long (the prefix builds across turns). Avoid timestamps at the start of messages. System prompt + SOUL.md + prior conversation history are automatically cached after the first turn.
- **Real stats:** Users save >50% on average without any optimization.

Reference: https://api-docs.deepseek.com/guides/kv_cache

**Dual-model setup** for fast default + deep reasoning fallback:
```yaml
# config.yaml (default fast)
provider: openai
model: deepseek-chat
openai_base_url: https://api.deepseek.com/v1

fallback_providers:
  - provider: openai
    model: deepseek-v4-pro
    openai_base_url: https://api.deepseek.com/v1
```

**Disk cleanup:**
```bash
rm -rf ~/.hermes/sessions_backup_*/
find ~/project -name '__pycache__' -type d -exec rm -rf {} +
pip cache purge
```

**Expected results:** System prompt tokens ~18K → ~13K, response time 4-8s → 2-4s.

### 4. Skill Audit (Bloat Reduction)

Agent-created skills accumulate historical detail (test logs, migration notes, debugging artifacts) alongside operational instructions. Skills >15KB inflate system prompt tokens every time they're loaded, slowing responses.

**Detection:**
```bash
find ~/.hermes/skills/ -name 'SKILL.md' -not -path '*/.archive/*' -exec wc -c {} \; | sort -rn | head -30
```
Focus on agent-created skills >15KB. Bundled skills (shipped with Hermes) and hub-installed skills are protected — skip them.

**Podding strategy for each heavy skill:**
1. **Read SKILL.md** — identify sections that are operational (setup, commands, workflow, stack reference) vs historical (debugging logs, specific-past-fix narratives, migration diaries, test results, version-specific workarounds no longer active, session-level checkpoints).
2. **Move historical content** to `references/historial-<skill>.md` via `skill_manage(action='write_file', name='<skill>', file_path='references/...')`.
3. **Rewrite SKILL.md** to be the compact operational guide only. Target: ~15KB max for complex skills, ~10KB for medium ones.
4. **Keep linked files intact** — scripts/ and existing references/ stay. Add a one-line pointer in SKILL.md to any new reference file.
5. **Verify** — `skill_view(name='<skill>')` loads cleanly.

**When to NOT pod:**
- Skills <10KB are fine as-is
- Bundled skills (`hermes-agent`, hub-installed) — protected
- Skills that are naturally dense (full API references, protocol specs) — split into references/ instead

**Parallel execution pattern (proven):**
Heavy skills can be podded in parallel via `delegate_task(tasks=[...])` — each subagent reads, restructures, writes SKILL.md, and creates `references/historial-*.md` independently. This completes 3+ skills in the time one sequential pod would take.

**Real case (2026-06-29):** `cej-scraper-auditoria` (40KB → ~15KB) and `rag-legal` (37KB → ~15KB) podded in parallel, saving ~47KB of context. Archived stale skills (thinking-toggle, think, deepseek-reasoning-content-error) also removed.

See `references/skill-audit-methodology.md` for the full walkthrough with exact commands.
See `references/systematic-optimization-audit.md` for the general 5-step workflow (ingest → filter → prioritize → parallel-implement → report with numbers).

### 5. Token Tracking — Session Consumption Monitoring

Hermes does not expose an API to query its own token consumption. Subagents (`delegate_task`) report `input`/`output` on completion, but main conversation tokens are not directly measurable.

See `references/hermes-token-tracking.md` for the full pattern: SQLite-based manual tracker, pricing, and accumulation across sessions.

Example from a medium refactoring session (2026-05-05):
- Subagents: 4.2M input + 99K output = 4.3M tokens
- Main conversation (est): 500K + 50K = 550K tokens
- Total: ~4.9M tokens, ~$4.46 USD (DeepSeek V4-Pro)

### 5. Session Corruption — Incomplete/Truncated Sessions After Power Loss

When a user's system loses power during a session (confirmed pattern with this user's team), the session file may be saved but with **incomplete content** — only tool calls persist while user/assistant messages, reasoning, and final responses are truncated or missing.

**Symptoms:**
- `session_search` shows the session exists but returns only tool-call metadata
- Reading the session JSON file shows messages with tool calls but empty/missing `content` fields
- The agent cannot reconstruct what was actually discussed

**Diagnosis:**
```bash
ls -lt ~/.hermes/sessions/ | head -10   # Check file timestamps
# Compare against: file is dated AFTER last known good session
```

**Recovery strategy (in order):**
1. **Check memory** — durable facts survive across sessions. Memory may contain the last task summary (e.g. "Pipeline F1-F5 completado, API en :8000")
2. **Check project status files** — look for `reports/STATUS_*.md` or similar in the project directory. The user's workflow generates status reports at end of sessions.
3. **Check git log** — `git log --oneline -5` shows last committed changes. If the push succeeded before power loss, the commit message reconstructs what was done.
4. **Check sessions directory** — there may be a NEWER session file (timestamps can be misleading; last_active metadata may corrupt on unclean shutdown). Run `ls -lart ~/.hermes/sessions/` to see actual file modification times.
5. **Ask the user** — "¿En qué estábamos?" with your findings from steps 1-4. The user remembers the context even if the system lost it.

**Do NOT** insist that the *session_search result* is authoritative when the user contradicts it. The user can see their terminal history and knows what they were doing. If they say "creo que hay una más reciente", there probably is — look at raw file timestamps, not session metadata.

**Prevention:** The user's workflow already includes generating `STATUS_*.md` reports at end of major sessions. This is the best defense against data loss from power cuts.

### 5. Session Resilience — Memory-First Workflow

When resuming work after a crash or when the agent was stuck and had to be killed, **optimize memory before doing anything else**. The agent loads memory at session start — if memory is bloated (>70%), it wastes context tokens on stale information and slows down every response. The user may have killed the agent BECAUSE it was slow, creating a vicious cycle.

**Pre-task checklist (before any complex work):**
1. **Check memory usage** — shown in system prompt header or via `memory(action='add'...)` which reports usage %
2. **If >70%**: consolidate entries, remove obsolete ones (bugs already fixed, completed tasks, duplicate info)
3. **If >85%**: aggressive cleanup. Remove all non-critical entries. The agent can re-discover facts from session_search.
4. **Then create snapshots** of any files that will be modified:
   ```bash
   git tag -a "v4.0-pre-CHANGE-YYYYMMDD" -m "Snapshot pre-change"
   git push origin TAG
   cp file.py backups/file_v4.0_pre_change.py
   sha256sum file.py > backups/file_v4.0.sha256
   ```
5. **Then begin the actual task**

This prevents: slow responses causing user frustration → user kills agent → agent loses context → next session starts with bloated memory → even slower responses.

**Real case (2026-04-29):** Agent spent 1h fixing api_rest.py corruption. Memory was 79% full. User explicitly said "optimiza primero la memoria, a veces sucede que te cuelgas y tengo que reiniciarte" — memory had likely contributed to prior session crashes. After optimization to 40%, the rest of the session ran smoothly.

Two companion tools for toggling DeepSeek thinking mode:

### `/think` — User-facing slash command
Activates thinking mode for deep reasoning tasks (complex debugging, architectural analysis, exhaustive code review). Adds ~2-5K tokens/turn. Not for simple/fast tasks.

### `thinking-toggle` — CLI script
```bash
thinking-toggle on      # Enable thinking mode (remove reasoning_effort: none)
thinking-toggle off     # Disable thinking mode (add reasoning_effort: none)
thinking-toggle status  # Show current state
```

Modifies `agent.reasoning_effort` in `~/.hermes/config.yaml`. Changes take effect on next Hermes session restart.

## Common Pitfalls

- **Old processes hold config in memory** — always kill and restart after config changes\n- **`hermes config set` is the ONLY safe way to modify config** — direct yaml editing via `patch` to `~/.hermes/config.yaml` is blocked by a safety guard (`Refusing to write to Hermes config file`). Always use `hermes config set <key> <value>`. This applies to auxiliary providers, model settings, and all runtime config.\n- **MCP server changes require process kill — not hot-reloaded** — Changing a wrapper script, env vars, or provider priority in an MCP server requires killing the old processes (`pkill -f "server-name"`) so the watchdog respawns them with the new config. Use `hermes mcp test <name>` to verify.\n- **`reasoning_effort: none` disables thinking for ALL providers**, not just DeepSeek\n- **DeepSeek reasoning_content error is NON-retryable** — agent loop aborts, must restart
- **VSCode terminal shell integration** can interfere with signal delivery
- **Long-running child processes** (API servers) can block terminal I/O
- **Multiple Hermes instances** compete for resources — kill stale ones
- **`hermes model` command** requires interactive terminal — can't run via pipe/subprocess
- **Config changes require restart** — not hot-reloaded
- **Session data persists** even after SIGKILL — use `hermes --resume SESSION_ID`
- **Cronjobs — common failure modes and fixes.** Cronjobs CAN fail silently if misconfigured. Known failure modes and how to fix them:

  | Symptom | Root cause | Fix |
  |---------|-----------|-----|
  | Job never fired | One-shot (`repeat: once`) with past timestamp; scheduler wasn't active at that time | Use recurring `"every 30m"` schedule, not `"once in 30m"` with a past timestamp |
  | Job fired but no visible result | `deliver: local` — saved to local DB only, never shown to user | Set `deliver: origin` |
  | Python script crashes with ImportError | Missing `workdir` — imports from `core/` etc. need `PYTHONPATH=.` | Set `workdir: /absolute/project/path` |
  | Job fires but the agent has no context | No `workdir` for relative path resolution | Always set `workdir` for project-bound tasks |

  **PITFALL:** A one-shot cronjob with a timestamp in the past (e.g., scheduled at 08:59 but created at 08:10) never fires — the scheduler checks if the time has already passed. Always use recurring schedules for ongoing monitoring tasks, and if you need one-shot, set the timestamp to a future time.
- **Auxiliary models default to "auto" — silent token waste** — Hermes v0.12 sets ALL `auxiliary.*.provider` fields to `auto` by default. This silently routes compression, session_search, title_generation, curator, vision, and other mechanical tasks to the primary provider (e.g., DeepSeek V4-Pro). This wastes ~30% of tokens on tasks that could run on free models. Always explicitly configure these providers after initial setup: `hermes config set auxiliary.compression.provider google_ai_studio`, etc. See `hermes-multi-provider-config` skill for full configuration procedure.
