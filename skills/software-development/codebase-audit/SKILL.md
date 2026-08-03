---
name: codebase-audit
description: "Audit a full codebase for bugs, security, and architecture."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Code-Review, Audit, Code-Quality, Security, Architecture]
    related_skills: [codebase-inspection]
prerequisites:
  commands: [pygount]
---

# Codebase Audit

Systematic full-codebase quality audit. Not a PR review — read every source file,
find bugs, security gaps, dead code, architectural issues, and produce a
structured report with a prioritized action plan.

**Trigger:** User asks to "review this code", "audit this project", "check this
codebase", "propose improvements for this code", or drops a project path without
a specific PR/diff context.

## Phase 1: Landscape (2-5 min)

1. **List all source files** with `search_files(pattern='*.py', target='files')`.
   Note directory structure and module boundaries (agents/, core/, retrieval/, etc.).
2. **Count** with `pygount --format=summary` (see `codebase-inspection` skill).
   Know the scale: 500 lines vs 5,000 vs 50,000 drives different approaches.
3. **Identify architecture**: Is it MVC? Multi-agent? Pipeline? Monolith + API?
   Note the pattern before diving in.

## Phase 2: Deep Read (15-30 min for ~30 files)

Read EVERY source file, not a sample. Order matters:

1. **Entry points first**: `main()`, `app` factory, API router, CLI. These reveal
   architecture, dependency wiring, and data flow.
2. **Core modules**: config, models, DB layer, shared utilities. These affect
   everything.
3. **Feature modules**: agents, services, pipelines, controllers — in dependency
   order.
4. **Infrastructure**: Dockerfile, docker-compose, CI config, health checks,
   deployment scripts.

For each file, note:
- Bugs and logic errors
- Security issues (hardcoded secrets, missing auth, CORS, rate limiting)
- Duplication with other files
- Dead code (imported but unused, defined but uncalled)
- Thread-safety and concurrency issues
- Error handling gaps (bare excepts, swallowed exceptions)

## Phase 3: Review Checklist

Apply systematically across the whole codebase:

### Correctness
- Does code do what it claims? Are docstrings accurate?
- Edge cases: empty inputs, nulls, large data, concurrent access?
- Error paths handled gracefully or just try/except/pass?

### Security
- No hardcoded secrets, keys, tokens
- Input validation on all user-facing entry points
- CORS not wide open (no `allow_origins=["*"]` + `allow_credentials=True`)
- Auth/authz on sensitive endpoints
- Rate limiting present on API
- No path traversal or injection vectors

### Code Quality
- Clear naming, single-responsibility functions
- No duplicated logic across modules (CLI vs API copy-paste)
- No dead code (check: is this import actually used? is this function called?)
- Operator precedence is explicit (parentheses, not mental parsing)

### Architecture
- Circular dependency risk? Modules importing each other?
- Global mutable state vs dependency injection?
- Singleton pattern correctness (double-checked locking without races)?
- CWD-dependent paths (`glob.glob("some_dir/*")`) — fragile across entrypoints

### Testing
- Zero tests for N thousand lines = critical finding
- If tests exist, check coverage of: caching, retrieval, scoring, error paths

### Performance
- Lazy loading for heavy models (no `SentenceTransformer()` at import time)
- Background thread spawning per query vs shared pool
- Cache invalidation: does cache survive restart? (trace the save/load path)

### Documentation
- Public API documented?
- Non-obvious logic has "why" comments?
- README up to date?

## Phase 4: Structured Output

Always present findings in this format:

```
## Code Review Summary

### Verdict: (Approve / Changes Recommended)
N hallazgos: X criticos, Y warnings, Z sugerencias

### Critical (🔴)
- **file:line** — What is broken. Concrete fix in one line (→).

### Warnings (🟠)
- **file:line** — Issue, not breaking but degrades quality.

### Suggestions (💡)
- **file:line** — Improvement opportunity.

### Looks Good (✅)
- What the codebase does well.

### Action Plan (N days)
| Day | Tasks | Impact |
```

## Pitfalls

### Cache bugs are invisible
A cache that "works" but silently becomes useless after restart (embeddings
stripped on save, not recalculated on load) won't log errors. Trace the full
save→load→get path.

### Architecture contradictions
A codebase can have clean module boundaries but contradictory internal logic.
Example: system prompt says "act as Supreme Court", user prompt says "DON'T
pose as a judge" — both in the same file, 7 lines apart.

### Glob patterns with relative paths
`glob.glob("some_dir/*.json")` depends on CWD. In multi-entrypoint projects
(CLI + API + Docker), CWD varies. Flag all relative-path globs.

### Do not trust imports
Just because `from X import Y` exists does not mean Y is used. Verify call
sites. A fully-implemented module (e.g. reranker) may be imported by no
pipeline at all.

### Rate what is absent
Missing rate limiting, missing tests, missing input validation — these ARE
findings even though they are not code. List them.

### Thread safety in Python
`threading.Lock` is not reentrant. If `_save()` spawns a thread that calls
`to_dict()` which acquires the same lock, and the caller also holds it →
deadlock. Check lock acquire/release pairing.

### Precedence bugs
`a and b or c` in Python binds as `(a and b) or c`. Without parentheses, a
query with 8+ words may silently fall into the wrong classification branch.
Flag ambiguous boolean expressions.
