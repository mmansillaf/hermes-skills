# Anti-Hallucination Patterns for Legal RAG

When LLMs generate answers over legal norms, they hallucinate organizational/reference laws that appear in boilerplate legal basis clauses. The LLM cannot distinguish "cited as legal footing" from "substantively about the topic."

## The Problem

Query: *"que leyes mencionan el crimen organizado?"* → FTS5 returns Resoluciones Ministeriales whose sumillas say *"Designan Director de la Dirección Contra Delitos de Crimen Organizado"*. These RMs have boilerplate *considerando* citing Ley 29158 (LOPE) and Ley 27594 (designaciones). The LLM sees RM + "crimen organizado" and concludes: Ley 29158 is about crimen organizado.

## The Fix Chain (3 layers, weakest→strongest)

### Layer 1: Prompt Engineering (~50% effective)

```python
"- Una ley organizativa (LOPE, Ley de Procedimiento Administrativo) NO es relevante a menos que la pregunta sea sobre organizacion del Estado."
```

Llama models (even 70B) lack the reasoning to distinguish boilerplate from substance.

### Layer 2: LeyBooster (retrieval priority)

```python
_asks_for_ley = any(w in question.lower().split() for w in ['ley', 'leyes', 'legislativo'])
if _asks_for_ley:
    _ley_results = [r for r in unique_results if ((r.get('tipo') or '').upper()) in ('LEY', 'DECRETO LEGISLATIVO')]
    for r in _ley_results:
        r['relevance'] = min(r.get('relevance', 0.3) + 0.3, 1.0)
    unique_results = _ley_results + [r for r in unique_results if r not in _ley_results]
```

When question says "ley/leyes", law-type results go to top. Without this, RMs drown actual laws.

### Layer 3: Regex Post-Cleaner (100% effective)

Run AFTER LLM generation. Strip known organizational laws from answer text:

```python
LEYES_ORGANIZATIVAS = [
    (r'(?:la\s+)?Ley\s+(?:N[°º]\s*)?29158[^.,;]*',          'Ley 29158 (LOPE)'),
    (r'(?:la\s+)?Ley\s+(?:N[°º]\s*)?27594[^.,;]*',          'Ley 27594 (designaciones)'),
    (r'(?:la\s+)?Ley\s+(?:N[°º]\s*)?27444[^.,;]*',          'Ley 27444 (PAG)'),
    (r'(?:el\s+)?Decreto\s+Legislativo\s+(?:N[°º]\s*)?1266', 'DL 1266 (MININTER)'),
    # LLM uses descriptive names too
    (r'Ley\s+de\s+Organizaci[oó]n\s+y\s+Funciones\s+del\s+Ministerio\s+del\s+Interior', 'DL 1266 (desc)'),
]

_q_is_organizativa = any(w in question.lower() for w in ['organizacion del poder ejecutivo', 'nombramiento', 'organizacion del estado'])
if not _q_is_organizativa and llm_answer:
    for pattern, _name in LEYES_ORGANIZATIVAS:
        llm_answer = re.sub(pattern, '', llm_answer, flags=re.IGNORECASE)
    # Clean artifacts
    llm_answer = re.sub(r'\s*,\s*,+\s*', ', ', llm_answer)
    llm_answer = re.sub(r'\bse\s+basan?\s+en\s*,?\s*\.?', '', llm_answer, flags=re.IGNORECASE)
    llm_answer = re.sub(r'\s{2,}', ' ', llm_answer).strip()
```

**Pitfall**: The LLM may write "Ley de Organización y Funciones del Ministerio del Interior" instead of "DL 1266". Maintain BOTH number-based and description-based patterns. Update when new patterns appear.

## Making the LLM Enumerate ALL Laws

Even with good retrieval, the LLM mentions only 2-3. Add:

```python
"- Menciona TODAS las leyes o normas relevantes de la seccion NORMAS ENCONTRADAS"
"- Si la pregunta pregunta 'que leyes' o 'menciona las leyes', ENUMERA cada ley encontrada, sin omitir ninguna"
```

## Async Timeout for Blocking LLM Calls

blocking `requests.post()` in a FastAPI async endpoint freezes the event loop. One slow Groq call blocks ALL concurrent requests.

Fix — asyncio.to_thread + wait_for:

```python
async def generate_answer(question, profile, results, sources):
    def _do_groq():
        r = requests.post(..., timeout=45)
        return r.json()["choices"][0]["message"]["content"].strip()
    try:
        answer = await asyncio.wait_for(asyncio.to_thread(_do_groq), timeout=50)
        return answer
    except asyncio.TimeoutError:
        return "[La respuesta esta siendo generada, intenta de nuevo]"
```

**Cascade**: HTTP timeout (45s) → asyncio timeout (50s) → FastAPI endpoint. All intermediate functions must be `async def` with `await`.

## Context Quality: 15 Results + Scores + Longer Sumillas

| Change | Before | After | Effect |
|--------|--------|-------|--------|
| Result count | 10 | 15 | More coverage |
| Scores shown | none | `(score=0.80)` | LLM prioritizes |
| Sumilla length | 300 chars | 500 chars | More context |
| Type field | `None N° 32108` | `LEY N° 32108` | Identifies as law |

Neo4j graph results lack `tipo_norma`. Fix: regex-extract from sumilla:

```python
_tipo = d.get("tipo") or ""
if not _tipo:
    _m = re.search(r'(LEY|DECRETO|RESOLUCI[OÓ]N|ORDENANZA)', d.get("sumilla",""), re.IGNORECASE)
    _tipo = _m.group(0).upper() if _m else ""
```

## Reverse Validation Testing

1. Run battery → get answers
2. Extract key claims from each answer
3. Convert each claim into a new question (reverse direction)
4. Submit new question to the system
5. Check: new answer contains same key claims as original?

Question conversion (priority order):
1. Law + action → `"que hace {la Ley X}?"`
2. Person + role → `"que cargo ocupa {person}?"`
3. Term defined → `"que es {termino}?"`
4. Else → summarize first sentence

Expected: >80% OK. Below 80% → retrieval inconsistency.

## max_tokens for Legal Answers

| Level | Before | After | Words |
|-------|--------|-------|-------|
| BASICO | 800 | 1500 | ~1100 |
| INTER/AVAN | 1200 | 3000 | ~2250 |

3000 tokens covers 4-5 cited laws with full descriptions.

## Input Validation

```python
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(15, ge=1, le=50)
```
