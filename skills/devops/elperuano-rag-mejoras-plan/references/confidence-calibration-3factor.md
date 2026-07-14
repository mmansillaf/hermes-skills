# Confidence Calibration — 3-Factor Model

## Context (02-may-2026)

After completing F1-F5 pipeline, ran 100-question battery. Found 21 WARN/FAIL with confidence <0.50 even when answers were CORRECT. Root cause: `confidence_score()` penalizes lexical overlap but doesn't recognize when the LLM successfully extracted the answer from `texto_completo`.

## The 3-Factor Post-LLM Boost

Applied AFTER the LLM generates the answer, before returning to user:

```
Final Confidence = Base Confidence + Entities + Quality - Negation
```

### Factor 1: Entity Match (+0.08 each, max +0.30)

Extract named entities from the question (person names, norm numbers, years). Check how many appear in the LLM's answer. If the answer contains them, the LLM successfully extracted data.

```python
q_entities = set()
# Person names: regex [A-ZÁÉÍÓÚÑ]{3,}[A-ZÁÉÍÓÚÑ\s]{3,40}?
# Norm numbers: RM/RS/DS/DL N° XXX-YYYY-XXXX
# Years: 20\d{2}
matches = sum(1 for e in q_entities if e in ans.upper())
ent_boost = min(matches * 0.08, 0.30)
```

### Factor 2: Answer Quality (+0.10 to +0.25)

Measures whether the answer is substantive:
- +0.10 if answer > 400 chars
- +0.05 if includes FUENTES section
- +0.05 if mentions monetary amounts (S/ XXX)
- +0.05 if mentions specific dates

### Factor 3: Negation Penalty (-0.15 to -0.40)

Penalizes answers that say "no se encontró":
- -0.15 per occurrence of "no se encontró" / "no se halló" in first 400 chars
- Extra -0.10 if the negation is about the MAIN entity the question asked about

## Simulation Results (10 queries, various levels)

| ID | Result | Conf Before | Conf After | Δ |
|----|--------|-------------|-----------|-----|
| B01 | CORRECT | 0.15 | 0.59 | +0.44 ✅ |
| B05 | WRONG | 0.25 | 0.41 | +0.16 (stays low) |
| I02 | CORRECT abstract | 0.15 | 0.40 | +0.25 |
| B13 | CORRECT | 0.41 | 0.75 | +0.34 ✅ |
| A02 | PARTIAL | 0.10 | 0.33 | +0.23 |
| B03 | PARTIAL | 0.34 | 0.51 | +0.17 ✅ |

Key: WRONG answers don't get boosted (B05 stays at 0.41). CORRECT answers cross the 0.50 threshold.

## Implementation Notes

- Apply in `query_endpoint()` after `generate_answer()` returns
- Must happen BEFORE the web fallback check (`if confidence < CONFIDENCE_THRESHOLD`)
- Otherwise correct answers still trigger unnecessary Serper calls
- Model: llama-3.1-8b-instant (same as batch pipeline)
- Cost: $0 (regex only, no API calls)

## Related Fixes (same session)

- System prompt: replaced "dilo honestamente" with "SIEMPRE intenta responder" + 10 forbidden phrases
- Confidence floor: 0.75 → 0.60 (reduced false positives from 6 to 1)
- Graph traversal: enabled for types B, D, E (was 0%, now ~32%)
- Temporal filter: year+month extraction from queries, AND fecha_publicacion LIKE
- Neo4j cleanup: 51% generic entities deleted (verbs like "Aprueban", "Autorizan")
