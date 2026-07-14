# Confidence Calibration System — El Peruano RAG

## Architecture

The confidence system has 3 layers applied sequentially:

1. **Base confidence** (`confidence_score()` in api_rest.py:526) — lexical overlap + defense penalties
2. **Floor** (line 607) — minimum confidence when there's real overlap: `0.60` (was 0.75, lowered 2026-05-02)
3. **Post-LLM Boost** (line 1873) — 3-factor boost after LLM generates answer

## Floor (0.60)

```python
# api_rest.py:607
if has_real_overlap and weighted < 0.60 and (ratio >= 0.65 or db_ratio >= 0.90):
    weighted = 0.60
```

Trade-off:
- 0.75: eliminates fewer FPs, keeps legitimate queries higher
- 0.60: eliminates more FPs (5/6 in tests), but drops some legitimate queries
  that previously relied on the floor

Exact ID matches still get 0.85 via line 609-610.

## Post-LLM Boost (3 factors)

Applied after LLM generates answer, only if `confidence < 0.85`:

### Factor 1: Entities (+0.08/entity, max +0.30)
Extracts from question: proper names (UPPERCASE patterns), norm numbers (RM/RS/DS/DL N° XXX-YYYY-XX), years (20\d{2})
Counts how many appear in the answer. If none found, gives +0.10 minimum.

### Factor 2: Quality (+0.10 to +0.25)
- +0.10: answer > 400 chars
- +0.05: contains FUENTES: section
- +0.05: mentions S/ amounts
- +0.05: mentions specific dates

### Factor 3: Negation (-0.15 to -0.40)
Penalizes answers containing defeatist language:
- "no se encontró", "no se encuentra", "no se hall", "no hay información"
- Extra -0.10 if negation specifically targets an entity from the question

## Test Results (2026-05-02)

| Query | Base | After Boost | Δ | Notes |
|-------|------|-------------|---|-------|
| B01: Who was designated? (correct answer) | 0.15 | 0.59 | +0.44 | Entities (name + norm#) + quality boost |
| B05: Entity where designated? (wrong answer) | 0.25 | 0.26 | +0.01 | Negation penalty offsets entity match |
| I02: Office functions? (correct, abstract) | 0.15 | 0.40 | +0.25 | Quality boost only (no named entities) |
| B13: UISP 2022 amount? (partial) | 0.41 | 0.32 | -0.09 | Negation penalty for "no se encontró" |
| A03: Cofinancing structure? (correct) | 0.47 | 0.61 | +0.15 | Quality + entity match |

## When to recalibrate

- After any changes to the FTS5 tokenizer or scoring weights
- After changes to the LLM system prompt (affects negation patterns)
- When test batteries show >10% of correct answers below 0.50 confidence
