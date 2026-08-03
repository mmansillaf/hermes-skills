# Skill-Index Token Audit — Methodology (verified 2026-07)

## Ground truth (from source, hermes-agent v0.19.1)

| Component | Truncation | Cost |
|---|---|---|
| SKILL.md `description` | truncated to 57+3 chars (`extract_skill_description`, `SKILL_PROMPT_DESC_LIMIT` in `agent/skill_utils.py`) | fixed ~60 chars/entry |
| `DESCRIPTION.md` (category) | **NONE — injected complete** (`prompt_builder.py`: `index_lines.append(f"  {category}: {cat_desc}")`) | full length, the real lever |
| Rendered index total | — | ~123 skills × ~80 chars ≈ 9.8K chars ≈ 2.5K tokens |

Prompt caching (`prompt_caching.cache_ttl`) prices the index at cache-hit rate (~1/10) after the first turn. Do NOT quote "X tokens per turn" — say "per session start / cache refresh".

## Audit steps

1. Count skills and measure SKILL.md descriptions:
```python
import os, re, glob
SKILLS = os.path.expanduser("~/.hermes/skills")
for p in glob.glob(f"{SKILLS}/**/SKILL.md", recursive=True):
    fm = re.search(r"^---\n(.*?)\n---", open(p, encoding="utf-8").read(), re.S).group(1)
    d = re.search(r"^description:\s*(.+)$", fm, re.M)
    print(len(d.group(1)) if d else 0, os.path.relpath(p, SKILLS))
```
Anything >57 chars is truncated at injection — trimming it saves nothing.

2. Measure category descriptions (THE lever):
```bash
find ~/.hermes/skills -name "DESCRIPTION.md" | while read f; do \
  d=$(grep -m1 "^description:" "$f" | sed 's/^description:\s*//'); \
  echo "$(echo -n "$d" | wc -c) | $f"; done | sort -rn
```
Rewrite each >90-char description to ≤90 chars, keeping trigger keywords in the first 57. Observed win: 22 files, 3,103 → 1,640 chars (~365 tokens/session).

3. Snapshot cache: `~/.hermes/.skills_prompt_snapshot.json` (`.skills[]` entries, `category_descriptions`, `manifest` with mtime+size per file). It already stores truncated descriptions; it regenerates when SKILL.md/DESCRIPTION.md mtimes change.

## Consolidation candidates found (2026-07, 123 skills)

All had `created_by: (none)` → curator will NOT touch them (curator only manages `created_by: agent`). Cron jobs referenced none of them.

| Cluster | Skills | Sizes |
|---|---|---|
| MCP | mcp-server-authoring, mcp-server-development, native-mcp, mcporter | 3-15KB |
| Peru scraping (CEJ/TC) | cej-peru-scraper, peruvian-judicial-scraping, cej-mcp-server, tc-sedetc-scraper, tc-ingesta-lexrag, tc-searchrag | 7-68KB |
| Paywall/login | bypass-paywall, bypass-login-wall | 5-20KB |
| Protocol forensics | crypto-protocol-analysis, anonymization-protocol-analysis, network-protocol-analysis, p2p-messaging-forensics, whatsapp-desanonimizacion-stack | 8-11KB |
| Statistics | scientific-statistical-engine, statistical-formula-engine, statistics-vs-ml-decision, method-selector, time-series-forecasting | 4-19KB |

Merge via `skill_manage(action='delete', absorbed_into=<umbrella>)` — but ONLY with explicit user approval; these are user-owned skills.
