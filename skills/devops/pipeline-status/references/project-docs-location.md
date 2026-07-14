# Project Documentation Location — GRegElPeruano_v5.1

## The problem
The GitHub repo `mmansillaf/GRegElPeruano_v5.1` is **private** — returns 404 on the public API.
Session transcripts and Hermes skills contain operational knowledge but NOT a single consolidated
overview of characteristics, artifacts, and infrastructure.

## The ZIP
A downloaded ZIP of the repo lives at:
```
~/Descargas/GRegElPeruano_v5.1-main.zip
```
It contains **90+ documents** (markdown, text, JSON) across `GRegElPeruano_v5.1-main/docs/` and `GRegElPeruano_v5.1-main/reports/`.

## Key documents (in priority order)

| Doc | Size | Content |
|-----|------|---------|
| `README.md` | 10.6 KB | Full overview: architecture diagram, endpoints, performance, folder structure, quick start |
| `docs/Informe_Validacion_Arquitectonica.md` | 22.3 KB | Exhaustive architectural validation: 7 sections covering CLI, ingestion, chunking, DBs, retrieval, LLM, verification |
| `docs/Master_Blueprint_Proyecto_Peruano.md` | 5.2 KB | Master plan: 4 phases, rules, APIs, infrastructure decisions |
| `docs/Infraestructura_e_Ingesta_Fase1_3.md` | 2.6 KB | Mermaid diagram of ingestion flow + per-phase infra detail |
| `docs/Motor_Respuestas_y_Logica_Fase4.md` | 3.3 KB | Response engine and query logic |
| `docs/AGENTS.md` | 23 KB | AI agent context (Claude/Hermes instructions for the project) |
| `docs/CLAUDE.md` | 2.4 KB | Claude-specific context |
| `PIPELINE.md` | 13 KB | Pipeline documentation |

## Consolidated documents (created 2026-05-04)

After discovering the ZIP, we generated two unified references:

| Doc | Path | Size | Content |
|-----|------|------|---------|
| Consolidated report | `docs/CARACTERISTICAS_ARTEFACTOS_INFRAESTRUCTURA.md` | 20.8 KB | 8 sections: overview, features, artifacts (code/DBs/data/docs), infrastructure, performance, directory tree, roadmap, cross-references |
| Architecture text summary | `~/arquitectura_infraestructura_peruano_rag.txt` | 5.4 KB | ASCII diagram, 11-stage pipeline, infra table, hardware, data by year, costs, endpoints |

Both pushed to the private repo (`git push`), committed as `1fb587e`. Also available locally.

## Other notable docs (90+ total, not 37 — previous estimate was from ZIP header alone)

The repo contains 90+ markdown/text documents across 4 directories:

| Directory | Count | Content |
|-----------|-------|---------|
| `docs/` | 40+ | Architecture, blueprints, guides, informes, evaluaciones |
| `docs/blueprint_v2/` | 8 | Future-state blueprints (BLUEPRINT_v3, ARQUITECTURA_COMPLETA) |
| `docs/informes/` | 15 | Audit reports, test evaluations, comparative analyses |
| `docs/informes_fase1/` | 4 | Phase 1 analysis and MVP architecture |
| `docs/evaluaciones/` | 5 | JSON evaluation data |
| `reports/` | 100+ | Test batteries, diagnostics, handoffs, comparisons |

## Architecture summary (from README.md)
```
FastAPI :8000
  ├── SQLite FTS5 (BM25) — 18,694 normas, sparse retrieval, 50% weight
  ├── Qdrant (384d Cosine) — dense semantic retrieval, 30% weight
  ├── Neo4j (58K nodes, 330K edges) — entity enrichment, 20% weight
  └── Groq LLM (llama-3.3-70b-versatile) — answer generation
      + Serper API — web fallback
```

- **Data**: SQLite 66 MB compressed, Qdrant ~600 MB, Neo4j ~500 MB
- **Performance**: 100% score on 50-question legal battery (SET3), 92.5% on 40-question multilevel set
- **Stack**: Python 3.10+, FastAPI, Streamlit dashboard, Docker Compose (Qdrant + Neo4j)

## How to use in a session

When the user asks about project characteristics, artifacts, or infrastructure:

1. **First**: read the consolidated doc directly from the cloned repo or local copy:
   - Repo: `/tmp/GRegElPeruano_v5.1/docs/CARACTERISTICAS_ARTEFACTOS_INFRAESTRUCTURA.md`
   - Local: `~/CARACTERISTICAS_ARTEFACTOS_INFRAESTRUCTURA.md`
   - Text summary: `~/arquitectura_infraestructura_peruano_rag.txt`
2. **If the consolidated doc doesn't cover the need**: extract specific files from the ZIP:
   `unzip -o ~/Descargas/GRegElPeruano_v5.1-main.zip "GRegElPeruano_v5.1-main/docs/<file>.md" -d /tmp/`
3. **If the user provides a GitHub token**: clone the full repo for live access:
   `git clone https://<TOKEN>@github.com/mmansillaf/GRegElPeruano_v5.1.git /tmp/GRegElPeruano_v5.1`
4. For a directory listing: `ls /tmp/GRegElPeruano_v5.1/docs/ /tmp/GRegElPeruano_v5.1/reports/`

## Pitfall

The repo is private (404 on GitHub API). Do NOT conclude "no documentation exists" just because the
API returned 404. Check `~/Descargas/` for ZIP downloads first, then ask the user for a token if
live access is needed (they provided a token in the past).
