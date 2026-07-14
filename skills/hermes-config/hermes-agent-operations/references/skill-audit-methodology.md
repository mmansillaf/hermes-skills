# Skill Audit & Bloat Reduction — Full Walkthrough

## When to Run

- Agent feels slow and memory is already <70% (likely skill bloat, not memory)
- After a heavy development session that generated/documented lots of tribal knowledge
- When a skill's SKILL.md has accumulated 3+ revision details, debugging logs, or migration notes
- Monthly or after every ~10 session-hours of active use

## Phase 1: Discovery

```bash
# List all skills sorted by file size (byte count)
find ~/.hermes/skills/ -name 'SKILL.md' -not -path '*/.archive/*' -exec wc -c {} \; | sort -rn

# Focus on agent-created skills >15KB
find ~/.hermes/skills/ -name 'SKILL.md' -not -path '*/.archive/*' -exec wc -c {} \; \
  | sort -rn | awk '$1 > 15000'

# Count total skills
find ~/.hermes/skills/ -name 'SKILL.md' | wc -l
```

**Thresholds:**
| Size | Priority | Action |
|------|----------|--------|
| <10KB | Low | Leave as-is |
| 10-15KB | Monitor | Review during next audit |
| 15-25KB | Medium | Consider podding if >30% is historical |
| >25KB | High | Pod as soon as practical |

## Phase 2: Triage — How to Review a Heavy Skill

1. **Load with skill_view(name='<skill>')**
2. **Ask: is this agent-created?** Bundled and hub-installed skills are protected.
3. **Scan for historical sections:**
   - "Real case (DATE)" narratives
   - "Update DATE" / "2026-MM-DD:" dated entries
   - Test results, error transcripts, code samples from debugging sessions
   - Migration diaries (Windows→Ubuntu, local→cloud, old_version→new_version)
   - Session-level checkpoints ("Fase 1 completado", "Pipeline F1-F5 hecho")
4. **Identify the operational core:** setup instructions, commands, workflow steps, stack reference, dependency list, anti-blocking rules — this is what should stay.
5. **Decide: pod or keep?**
   - If >40% of the skill is historical → pod
   - If historical content is still useful → keep but move to `references/historial-<topic>.md`
   - If historical content is obsolete → delete it entirely

## Phase 3: Podding Execution

### Step 1 — Create the reference file with historical content

```python
from hermes_tools import skill_manage

skill_manage(
    action='write_file',
    name='<skill-name>',
    file_path='references/historial-<topic>.md',
    file_content='# Historial de <skill>\n\n[Paste the historical sections here]'
)
```

### Step 2 — Rewrite SKILL.md (operational compact version)

Use `skill_manage(action='patch')` with old_string/new_string to replace bloated sections, or `skill_manage(action='edit')` for a full rewrite.

**Target structure for a compact SKILL.md:**
```yaml
---
name: <skill>
description: "One-line description"
version: X.Y.0
tags: [tag1, tag2]
---

# Skill Name

## Stack (table if applicable)

## Setup (exact commands)

## Core Workflow (numbered steps)

## Anti-Block Rules / Pitfalls

## Dependencies

## Support Files
- `references/...` — description
- `scripts/...` — description
```

### Step 3 — Verify

```python
result = skill_view(name='<skill>')

# Check 1: load cleanly
assert result['success'], f"skill_view failed: {result.get('error', '')}"

# Check 2: size ~15KB or less
sk_size = len(result.get('content', ''))
assert sk_size < 20000, f"SKILL.md still {sk_size} bytes — target is ~15KB"

# Check 3: ALL original linked files intact
# The linked_files dict shows references/, templates/, scripts/ still present
# Verify the new historial file also appears
print("linked_files:", result.get('linked_files', {}))
```

## Phase 4: Parallel Podding (Multiple Heavy Skills)

Use `delegate_task` to pod multiple skills simultaneously:

```python
delegate_task(tasks=[
    {
        'goal': 'Pod <skill-1> from ~40KB to ~15KB',
        'context': 'Full instructions from this reference...',
        'toolsets': ['file']
    },
    {
        'goal': 'Pod <skill-2> from ~35KB to ~15KB',
        'context': '...',
        'toolsets': ['file']
    },
])
```

Each subagent independently:
1. Reads the current SKILL.md
2. Identifies operational vs historical content
3. Creates references/historial-*.md with the historical sections
4. Rewrites SKILL.md compactly
5. Verifies the result

## Phase 5: Clean Up Archived Stale Skills

Skills in `.archive/` don't affect performance (they're never loaded), but housekeeping removes noise:

```bash
# Check what's in archive
find ~/.hermes/skills/.archive/ -name 'SKILL.md' -exec wc -c {} \; | sort -rn

# Remove truly obsolete ones (one-off fixes, transient issues)
rm -rf ~/.hermes/skills/.archive/<obsolete-skill>/
```

**Candidates for removal:**
- `thinking-toggle` / `think` — absorbed into hermes-agent-operations
- `deepseek-reasoning-content-error` — single-version fix, absorbed
- Session-specific errors that have been resolved upstream

## Results Tracking

After podding, log the delta:

| Session | Skill | Before | After | Δ | Downstream impact |
|---------|-------|--------|-------|---|-------------------|
| 2026-06-29 | cej-scraper-auditoria | 40KB | ~15KB | -25KB | Faster load + less prompt bloat |
| 2026-06-29 | rag-legal | 37KB | ~15KB | -22KB | Same |
| 2026-06-29 | 3 archived stale skills | ~5KB total | — | Removed | Housekeeping |
