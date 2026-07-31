# Citation Verification Critic — Implementation Reference

## What This Solves

RAG system LLM responses can invent document IDs (hallucinations). This reference provides a
verification system that checks every citation against the actual corpus metadata and can
trigger automatic rewrite when fake citations are found.

Originally extracted from the LexRAG project (64K+ legal documents corpus).

## Core Components

### CriticAgent Design

The critic extracts citations using 6 regex patterns and verifies them against a metadata index:

```
Patterns:
  1. Jurisprudencia/XXXXX.html    → doc_id directo (gold standard)
  2. EXP. N.º XXXX                → identificador textual
  3. CAS. N° XXXX                 → identificador textual
  4. RTF N° XXXX                  → identificador textual
  5. XXXXX.html suelto            → doc_id
  6. Numeros 6-7 digitos          → doc_id candidato
```

**Critical rule:** Pattern 6 uses `\\d{6,7}` not `\\d{5,7}` because most corpora have no 5-digit
doc IDs. 5-digit numbers (law numbers: 27803, 28706) are ignored automatically.

### Verification Against Metadata

```python
critic.verify(response_text, context_doc_ids=top_docs)
# Returns Verdict with: passed, score, hallucinated, verified, unverifiable
```

- **verified**: doc_id exists in metadata AND was in the context
- **hallucinated**: doc_id does NOT exist in metadata
- **unverifiable**: only textual identifier (EXP/CAS/RTF) without doc_id — the LLM may have reformatted it

### Feedback Loop Pattern

```
Writer → Critic → hallucination? → small model rewrites → Critic → ok?
                                     ↕ max 2 iterations
```

Only rewrites for **real hallucinations** (doc_id doesn't exist). Unverifiable identifiers do
not trigger rewrite.

### Anti-Loop Safeguards

1. `MAX_FEEDBACK_ITER = 2` — hard limit
2. `_needs_rewrite()` — only real hallucinations, not unverifiable
3. Strict mode on 2nd iteration
4. Cheap model (llama-3.1-8b-instant) for rewrite

## Pitfalls

1. **Phone numbers or short IDs**: Pattern 6 captures 6-7 digit numbers. Verify no false
   positives in your specific domain.
2. **No fuzzy match on identifiers**: Identifiers in metadata (`"000315-2003-SALA PENAL"`)
   don't match what the LLM generates (`"CAS. N° 1910"`). Only verify by doc_id.
3. **Empty response**: Score = 100% (nothing to verify = nothing incorrect). Don't force
   warnings.
4. **Feedback loop with streaming**: The original response is already shown to the user
   before feedback. The correction appears afterward as a separate section.

## Edge Cases Verified in Production

| Case | Result |
|------|--------|
| Empty response | score=100%, "no citations to verify" |
| No citations in text | score=100%, no warning |
| Real citation (Jurisprudencia/1308950.html) | detected and verified ✅ |
| Fake citation (9999999.html) | hallucinated=True ✅ |
| 5-digit laws (27803, 28706) | ignored (Pattern 6 uses \\d{6,7}) ✅ |
| Loose 5-digit number (12345) | ignored ✅ |
| Real 6-7 digit doc ID (1308950) | captured and verified ✅ |

## Quick Verification Command

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from agents.critic import CriticAgent
c = CriticAgent()
v = c.verify('According to EXP. N° 1308950 (Jurisprudencia/1308950.html)', ['1308950.html'])
print(f'Score: {v.score:.0%}, Hallu: {v.hallucinated}')
"
```
