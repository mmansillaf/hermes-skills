# Memory Store Audit & Cleanup Methodology

## When to Run

- Memory usage >70% (shown in system prompt header)
- User reports slowness or the agent was killed due to unresponsiveness
- Before starting any complex multi-step task (prevent mid-session bloat crashes)
- After sessions that produced many `memory add` operations

## Audit Steps

### 1. Identify Bloated Entries

Scan each entry for **ephemeral data** — information that changes session to session:

| Ephemeral (REMOVE) | Permanent (KEEP) |
|---|---|
| Test scores (`50q→0.729`) | Architectural decisions (`floor confianza 0.75→0.60`) |
| DB sizes (`normas_total.db 1055MB`) | New indices added |
| Runtime state (`API en :8000 activa`) | Config changes applied |
| Timestamps of specific runs | Workflow conventions discovered |
| "Pipeline F1-F5 completado" (task progress) | "graph traversal habilitado (B,D,E)" (feature flag) |

**Rule of thumb:** If a fact will be stale within 2 sessions, it doesn't belong in memory. Use `session_search` to recover session-specific progress.

### 2. Deduplicate Between Stores

Check for information duplicated across `memory` and `user`:
- API keys often appear in both — keep the detailed version (with limits/status) in `memory`, bare list in `user`
- User preferences in `user` profile should not repeat verbatim in `memory`
- Stack components (SQLite, Neo4j, Qdrant) belong in `user` profile, not `memory`

### 3. Compact Verbose Entries

Trim without losing semantics:
- `"Word-Office integration: skill word-office-integration actualizado con multi-proveedor, GitHub Pages, troubleshooting Windows. Proyecto en github.com/mmansillaf/hermes-word-addin con Pages activo."` → `"Word-Office: skill word-office-integration (multi-proveedor, GitHub Pages, troubleshooting Windows). Proyecto: github.com/mmansillaf/hermes-word-addin, Pages activo."`
- `"Equipo del usuario sufre cortes de energia. Al reiniciar sesion, buscar siempre la ultima conversacion..."` → `"Equipo sufre cortes de energia. Al reiniciar, buscar ultima sesion con session_search."`

Target: each entry should be **one sentence** conveying one durable fact.

### 4. Execute Cleanup

Use `memory(action='replace', ...)` for trimming, `memory(action='remove', ...)` for obsolete entries. Run one operation at a time and verify the usage % drops.

## Target Thresholds

| Usage | State | Action |
|---|---|---|
| <60% | Healthy | No action needed |
| 60-75% | Acceptable | Audit if >10 entries exist |
| 75-85% | Warning | Run cleanup before next complex task |
| >85% | Critical | Aggressive cleanup before ANY task |

## Real Case (2026-05-04)

**Before:** 94% memory, 86% user profile, 7+3 entries
**Actions:**
1. Compacted Session 02-may entry: removed test scores, DB sizes, runtime state → saved ~200 chars
2. Deduplicated API keys: removed bare list from user profile (kept detailed version in memory)
3. Compacted 4 verbose entries
**After:** 65% memory, 83% user profile. Freed 618 chars (30% of capacity). All 7 memory entries preserved with full semantics.
