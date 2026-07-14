# QA Evaluation Framework — 4-dimension quality assessment

**Fecha:** 2026-05-02
**Applied to:** 150 legal questions across 3 batteries

## 4 Dimensions (1-5 scale)

| Dimension | Description | 5 = | 1 = |
|-----------|-------------|-----|-----|
| **V** Veracidad | Are factual claims correct per cited sources? | Impeccable | Hallucination |
| **L** Lógica | Is reasoning coherent, no contradictions? | Perfect | Nonsensical |
| **I** Inferencia | Are deductions justified or unsupported leaps? | Pure facts | Wild speculation |
| **E** Extensión | Is the answer complete for the question? | Complete | Irrelevant/incomplete |

## Classification

```
✅ CORRECTA:  V ≥ 4
⚠️ PARCIAL:  V = 2-3 or extension problems
❌ INCORRECTA: V = 1
```

## 8 Error Patterns Identified

1. **Modo BÁSICO raw text** — Returns DB record without LLM review (FIXED)
2. **"No se encuentra"** — Document not in DB (coverage issue)
3. **Norma equivocada** — FTS5 match incorrect (FIXED with entity validation)
4. **Inferencia no justificada** — LLM assumes without source
5. **Respuesta incompleta** — Partial answer (FIXED with dynamic max_tokens)
6. **Bloqueo AVANZADO** — Disclaimer without analysis (FIXED with borrador mode)
7. **Confianza alta + respuesta incorrecta** — confidence ≠ quality
8. **Qdrant/Neo4j unused** — Silent failure of enrichment layers

## Benchmark Results (150 questions)

| Battery | Correct | Partial | Incorrect | False Positives |
|---------|---------|---------|-----------|-----------------|
| 100q Rímac+ATU (WITHOUT fixes) | 38% | 36% | 26% | 8 |
| 100q Rímac+ATU (WITH fixes) | 38% | 36% | 26% | **0** |
| 50q VIVIENDA (WITH fixes) | 36% | 14% | 40%* | **0** |

*40% "sin datos" because municipal ordinances from 2021 have partial coverage.

## Report Format

```markdown
# INFORME DE CALIDAD — Batería X
## RESUMEN EJECUTIVO (table: total, CORRECTAS, PARCIALES, INCORRECTAS, promedios)
## TABLA COMPLETA (ID, question, V, L, I, E, clasif, observations)
## PATRONES DE ERROR (numbered, with frequency, root cause, fix)
## TOP 5 MEJORES / TOP 5 PEORES
## RECOMENDACIONES
```

Save in 3 formats: MD + HTML (dark theme) + TXT.
