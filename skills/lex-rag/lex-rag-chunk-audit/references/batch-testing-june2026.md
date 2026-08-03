# Batch Testing Results — June 2026

## Session: 5 June 2026

### Evolution of batch testing approach

Three iterations were needed to find the correct pattern:

| Iteration | Script | Approach | Result |
|---|---|---|---|
| 1 | `bateria_15_subprocess.py` | `subprocess.run()` per query | TIMEOUT — recarga modelo ×15, ~150s/query |
| 2 | `bateria_15_directa.py` | `run_console_query()` + `redirect_stdout` | DEADLOCK — async generator roto |
| 3 | `bateria_15_directa_v2.py` | `run_console_query()` sin suppress | ✅ 15/15 en 6.7 min |

### Batch v3 results (fresh topics, 10 queries)

| # | ID | Nivel | Tiempo | Chars | Fuentes |
|---|---|---|---|---|---|
| 1 | T01 | Simple | 38s | 6,143 | 0 |
| 2 | T02 | Simple | 32s | 7,903 | 7 |
| 3 | T03 | Medio | 22s | 3,614 | 3 |
| 4 | T04 | Medio | 21s | 2,479 | 2 |
| 5 | T05 | Medio | 32s | 7,499 | 4 |
| 6 | T06 | Medio | 32s | 8,443 | 5 |
| 7 | T07 | Complejo | 28s | 6,713 | 0 |
| 8 | T08 | Complejo | 31s | 2,664 | 0 |
| 9 | T09 | Complejo | 12s | 1,381 | 0 |
| 10 | T10 | Complejo | 30s | 7,446 | 4 |

**Total**: 10/10 OK, 278s (4.6 min), 54,285 chars, 25 sources cited.

T07-T09 had 0 sources — honest "información insuficiente" responses (estado de cosas inconstitucional is very rare in Peruvian jurisprudence).

### Citation fix validation

Before fix: 3 out of 4 citations in C02 response were missing `Jurisprudencia/X.html`.
After fix (📄 FUENTE: prefix + reinforced prompt): 25/25 citations across 10 queries had source paths.

### Dependency fixes applied

Missing from venv_linux: `openai`, `rank-bm25`, `transformers`, `torch`, `scikit-learn`.
Added `HF_TOKEN` to `.env` for 5× faster HuggingFace downloads.
Fixed `get_sentence_embedding_dimension()` → `get_embedding_dimension()` in `core/embedding.py`.
