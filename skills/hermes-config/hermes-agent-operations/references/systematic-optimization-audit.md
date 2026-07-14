# Systematic Optimization Audit Workflow

## When to Use

When the user provides a large resource (doc, guide, blog post, research paper, configuration reference) and asks to "optimize" or "improve" — the goal is to extract actionable value without getting lost in the noise.

## The 5-Step Workflow

### Step 1: Ingest & Categorize

Read the full resource. Classify each section:

| Category | Label | Action |
|----------|-------|--------|
| **Already implemented** | ✅ | Note it, skip during execution |
| **Applicable & new** | 🆕 | Extract to action list |
| **Not applicable** | ❌ | Document why (different hardware, different model, different workflow) |
| **Generic / filler** | ⚪ | Ignore — no actionable content |
| **Wrong / outdated** | ⚠️ | Document discrepancy vs current reality |

**Target:** Reduce a 101KB document to ~20 actionable items.

### Step 2: Filter Against Real Config

Read the actual config files (config.yaml, .env, SOUL.md, skill files). For each candidate action:

- Does our config already cover this? → ✅ skip
- Is our setup different from what the resource assumes? → ❌ skip or adapt
- Is this specific to a model/provider we don't use? → ❌ skip
- Is it a good practice we should adopt? → 🆕 keep

**Real case (2026-06-29):** 101KB optimization doc → 15 candidate actions → 7 survived filtering. The rest were for models not in use, hardware we don't have, or already configured.

### Step 3: Prioritize by Impact/Effort

| Priority | Impact | Effort | Examples |
|----------|--------|--------|---------|
| 🔴 Alta | Alto | <15 min | SOUL.md rewrite, .hermes.md creation, config tweaks |
| 🟡 Media | Alto- Medio | 15-60 min | Skill creation, multi-file changes, delegation config |
| 🟢 Baja | Medio | 1-4 hrs | Custom skills, self-evolution, CI/CD |
| ⚪ Informativo | Bajo | N/A | Document for awareness, no immediate action |

Use this matrix. **High impact + low effort goes first.** Always.

**Real case:** SOUL.md (5 min, high impact) and .hermes.md (15 min, high impact) were day-1. Self-evolution with GEPA was flagged as low-ROI and deferred.

### Step 4: Implement in Parallel Where Possible

Batch independent tasks:

- SOUL.md + .hermes.md files → parallel (no dependencies)
- Skill podding (cej-scraper + rag-legal) → delegate_task parallel
- Config changes + memory cleanup → parallel (different systems)

Use `delegate_task(tasks=[...])` for skill modifications. Use the terminal for config changes. Use `memory` tool for memory cleanup.

**Track with todo tool** so nothing falls through:
```
todo(todos=[
  {"id": "task1", "content": "...", "status": "in_progress"},
  {"id": "task2", "content": "...", "status": "pending"},
])
```

### Step 5: Report With Concrete Numbers

After implementing, report:

| Action | Before | After | Reduction |
|--------|--------|-------|-----------|
| Memory usage | 85% (1,889 chars) | 30% (664 chars) | 55pp freed |
| cej-scraper skill | 39,683 bytes | 15,406 bytes | **61%** |
| rag-legal skill | 36,797 bytes | 6,330 bytes | **83%** |
| max_concurrent_children | 3 | 5 | +67% capacity |

**Do not** report qualitative descriptions alone. Numbers prove the optimization happened.

## When to Defer

Some optimizations are real but not worth executing now:

- **Requires purchase** (new API keys, paid tools, hardware) → note and move on
- **Low ROI relative to current workflow** (e.g., self-evolution at $2-10/run) → document and defer
- **Requires research to validate** (e.g., comparing 3 approaches) → defer to a spike
- **User explicitly says "ponlo en pendiente"** → honor it

## Guardrails

- Never modify config.yaml directly with `sed` — use `hermes config set` or ask user for approval
- Never suggest Self-Evolution (GEPA) for low-improvement apps — ROI is negative below ~$50/mo spend
- Never claim a tool is broken based on transient errors — capture the FIX, not the refusal
- Always verify with real file sizes and counts — subagent self-reports may be wrong

## References

- `hermes-agent-operations` → section 4 (Skill Audit - podding methodology)
- `hermes-multi-provider-config` → section 9 (DeepSeek context caching, model routing)
- `memory-audit.md` → memory compaction methodology
