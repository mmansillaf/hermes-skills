---
name: hermes-performance-tuning
description: "Tune Hermes performance: memory limits, skill-index tokens."
version: "1.0"
author: Hermes Agent
metadata:
  hermes:
    tags: [hermes, performance, memory, tokens, sqlite, context]
    category: devops
    related_skills: [hermes-agent, hermes-maintenance-wsl]
---

# Hermes Performance Tuning

Class-level procedures for optimizing Hermes Agent performance: expanding memory limits, reducing skill-index token overhead, and verifying SQLite/state.db health. Complementary to `hermes-maintenance-wsl` (recovery/crashes) and `hermes-agent` (configuration reference).

## When to Use

- User asks "how can we optimize your performance?", "can you expand your memory?", "what's your current state?"
- User wants faster responses / lower per-turn token cost
- state.db is large and user asks whether to clean it up / VACUUM
- Skill count is growing and user asks about the index overhead

## 1. Memory Expansion (safe, instant, reversible)

Memory is injected into EVERY turn, so limits trade space vs per-turn tokens (small: ~1-2K tokens per 8K chars). Defaults: `memory_char_limit: 4000`, `user_char_limit: 3000`.

```bash
hermes config set memory.memory_char_limit 8000
hermes config set memory.user_char_limit 5000
hermes config set checkpoints.auto_prune true   # snapshots auto-clean after 7d, cap 500MB
```

Takes effect immediately (memory tool reports new limit). Reversible with `hermes config set` back to previous values. Verify with the memory tool's reported `current/limit chars`.

## 2. Skill-Index Token Cost (the real lever — read the source first)

**KEY FACT (verified in agent/skill_utils.py + agent/prompt_builder.py):**
- Skill descriptions are truncated to 57+3 chars BEFORE injection (`extract_skill_description`, `SKILL_PROMPT_DESC_LIMIT`). Trimming SKILL.md descriptions saves ~NOTHING.
- Category descriptions (`DESCRIPTION.md` frontmatter) are injected COMPLETE, UNTRUNCATED (`index_lines.append(f"  {category}: {cat_desc}")`). **This is the actual lever.**
- Total rendered index ≈ 123 skills × ~80 chars ≈ 2.5K tokens, and after the first turn it's prompt-cache priced (~1/10). NOT 18-20K tokens/turn.
- The `.skills_prompt_snapshot.json` (cache) already stores truncated descriptions; editing SKILL.md triggers regeneration via manifest mtime.

### Audit procedure
1. Parse all `SKILL.md` frontmatters for description length; identify >57-char ones (they're truncated anyway — skip).
2. Measure `DESCRIPTION.md` files (category descriptions) — these are the untruncated cost:
   ```bash
   find ~/.hermes/skills -name "DESCRIPTION.md" | while read f; do \
     d=$(grep -m1 "^description:" "$f" | sed 's/^description:\s*//'); \
     echo "$(echo -n "$d" | wc -c) | $f"; done | sort -rn
   ```
3. Rewrite long category descriptions to ≤90 chars, keeping the trigger keywords in the first 57 chars. Typical win: 3,100 → 1,600 chars (~365 tokens/session).
4. Estimate the full index: count SKILL.md files × ~80 chars ÷ 4 ≈ tokens.

### Skill consolidation (destructive — requires user approval)
Overlapping skill clusters (e.g. 3-4 MCP skills, multiple paywall-bypass skills, multiple Peruvian scraping skills) can be merged into umbrellas via `skill_manage(action='delete', absorbed_into=...)`. Check cron jobs for skill-name references first. Only do with explicit user OK — these are the user's skills.

## 3. SQLite / state.db Health Check (read-only, no VACUUM unless freelist > 0)

```bash
export LD_PRELOAD="/home/usuario/.hermes/lib/libsqlite3.so${LD_PRELOAD:+:$LD_PRELOAD}"
python3 -c "
import sqlite3
c = sqlite3.connect('file:/home/usuario/.hermes/state.db?mode=ro', uri=True)
print('SQLite:', sqlite3.sqlite_version)
print('journal_mode:', c.execute('PRAGMA journal_mode').fetchone()[0])
print('page_size:', c.execute('PRAGMA page_size').fetchone()[0])
print('page_count:', c.execute('PRAGMA page_count').fetchone()[0])
print('freelist_count:', c.execute('PRAGMA freelist_count').fetchone()[0])
"
```

- SQLite ≥ 3.51.3 + `journal_mode: wal` = healthy (LD_PRELOAD lib compiled earlier; Ubuntu 24.04's 3.45.1 has the WAL corruption bug).
- `freelist_count = 0` → VACUUM reclaims NOTHING. A 500-600MB state.db is real FTS5-indexed session history, not garbage. **Verify before claiming cleanup is possible.**
- WAL file small (<3MB) next to a big .db = normal in WAL mode.

## Pitfalls

- **Estimate from source, not assumption.** This session's first estimate (18-20K tokens/turn) was 8x wrong; reading `agent/skill_utils.py` showed truncation. Grep the code before quoting token costs.
- **Verify before claiming** — the user explicitly values this (freelist check showed VACUUM pointless; reported honestly instead of running it).
- **User-owned skills are protected** — `hermes-maintenance-wsl` is user-authored; recommend `hermes curator adopt <name>` if it needs updates, don't patch it.
- **Never hand-edit config.yaml** — use `hermes config set KEY VAL` (a stray indent breaks the live gateway).
- **Memory is text injected per turn, not RAM** — expanding limits helps but the hard ceiling is the model's context window; token hygiene (section 2) is the real speed lever.

## References

- `references/skill-index-audit.md` — full audit methodology + consolidation cluster examples
- `references/sqlite-health-check.md` — read-only DB check recipe and expected outputs
