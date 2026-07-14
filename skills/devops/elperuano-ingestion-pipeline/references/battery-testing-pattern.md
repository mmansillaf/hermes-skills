# Battery Testing Pattern — El Peruano RAG

## Critical Pitfall: Truncated Answers

**NEVER** save `answer_preview[:200]` in test reports. The user needs FULL answers.  
When a test shows 50/50 (100%) but all answers are cut mid-sentence, it's useless for review.

```python
# WRONG — truncates answers
"answer": answer[:250]

# RIGHT — save full answer
"answer": answer
```

## Critical Pitfall: Dual JSON Schema Across Lotes

Cuando se ejecuta un test en lotes (ej: 4 lotes de 25 preguntas), cada lote puede usar un schema JSON diferente. Especificamente, `bateria_100q_lote2.json` usa un formato distinto a los lotes 1, 3 y 4:

| Campo | Lotes 1,3,4 | Lote 2 |
|-------|-------------|--------|
| Pregunta | `q` | `question` |
| Confianza | `conf` | `confidence` |
| Tiempo | `ms` | `timing_ms` |
| Calidad | `quality` (OK/WARN/ERROR) | `status` (ok/warn/error) |
| Nivel | `nivel` | `level` |
| Web | `web` | (ausente) |
| Cache | `cached` | (ausente) |

**Al generar reportes consolidados, normalizar ambos formatos:**

```python
def get_quality(item):
    qual = item.get('quality')
    if qual in ('OK', 'WARN', 'ERROR'):
        return qual
    status = item.get('status', '')
    return 'OK' if status == 'ok' else 'WARN'

def get_text(item):
    return item.get('q') or item.get('question') or '?'

def get_conf(item):
    return item.get('conf') or item.get('confidence') or 0

def get_ms(item):
    return item.get('ms') or item.get('timing_ms') or 0
```

## Execution Pattern

1. **Secuential, not parallel** — 50 queries × 3s = 2.5 min. Parallel would hit Groq rate limits.
2. **3 output formats** — JSON (raw data), MD (summary table), TXT (full Q&A for review)
3. **System monitoring** — sample RAM/CPU every 10 queries
4. **Per-question metrics** — confidence, sources (sqlite/qdrant/neo4j), router level, timing

## Report Structure

```
reports/battery_XXq_TIPO_TIMESTAMP.json  ← machine-readable
reports/battery_XXq_TIPO_TIMESTAMP.md    ← summary tables
reports/battery_XXq_TIPO_TIMESTAMP.html  ← dark theme
reports/battery_XXq_qa_TIMESTAMP.txt     ← FULL Q&A for human review
```

## Recovery: Full-Answer Regeneration

If a test was run with truncated `answer_preview[:200]` and the user requests complete answers, re-query the API for all questions. Do NOT hand-edit — re-run against the live API:

```python
# Regenerate full answers from original JSON questions
for q in original_json["levels"][level]["questions"]:
    resp = requests.post(f"{API}/query", json={"question": q["question"], "top_k": 8}, timeout=60)
    full_answer = resp.json().get("answer", "")
    # Write to TXT with confidence, sources, router info
```

Save as `battery_XXq_qa_COMPLETO_TIMESTAMP.txt` to distinguish from truncated version.

## CLI Testing (`consultar.py`)

The user-facing CLI must be tested separately from the API. Pipe questions via stdin:

```bash
# Create test file with one question per line
echo -e "Ley 32108\nUIT 2025 monto" > /tmp/consultar_test.txt

# Pipe to CLI with timeout
cat /tmp/consultar_test.txt | timeout 180 python3 consultar.py
```

The CLI uses interactive input and prints formatted responses with:
- `⏳ Buscando...` (searching)
- `🟢/🔴 Confianza: XX% | Fuentes: SQLite=N | Web=True/False` (confidence)
- Full answer with `────────────────` separators
- `FUENTES:` section at the end

Verify the CLI shows correct confidence levels, source counts, and the `FUENTES` section appears.

## User Preference

- User wants FULL answers in TXT, not previews
- User reviews answers manually for legal accuracy
- Reports must be pushed to GitHub (force-add HTML/JSON if gitignored)
- User wants CLI tested alongside API — both must work
- If answers appear truncated, regenerate immediately with full re-queries
