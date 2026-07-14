# Battery Test Pattern — El Peruano RAG

## Purpose
Script template for running graded legal-question batteries against the RAG API, saving full responses, and generating MD+HTML dark-theme reports. Used for regression testing, adversarial evaluation, and system health monitoring.

## Template Script
Copy `templates/battery_template.py` (in this skill's templates/ directory) and customize the `QUERIES` list.

## Methodology

### 1. Define queries by level
```python
QUERIES = [
    ("B01", "¿Qué número de resolución...?", "basico"),
    ("I16", "¿Cuál es la relación jurídica...?", "intermedio"),
    ("A36", "Analice la cadena de coherencia...", "avanzado"),
]
```

### 2. Evaluation verdicts
- **PASS:** has_content=True AND conf >= 0.60
- **WARN:** has_content=True AND 0.30 <= conf < 0.60 (response exists but confidence borderline)
- **LOWCONF:** has_content=True AND conf < 0.30 (correct response, confidence underrated — BUG SIGNAL)
- **FAIL:** has_content=False (no meaningful response despite docs found)
- **NODOCS:** No documents found in any store

### 3. What to save
- `battery_50q_legal_{timestamp}.json` — Full responses (answer, confidence, sources, pipeline_steps)
- `battery_50q_summary_{timestamp}.json` — Graded results + per-level breakdown
- `battery_50q_informe_{timestamp}.md` — Human-readable report with tables
- `battery_50q_informe_{timestamp}.html` — Dark-theme HTML version

### 4. Key metrics to report
- OK rate (PASS + WARN) / total
- Content generation rate (has_content / total)
- Keywords matched (evidence of document retrieval)
- Per-level breakdown (B/I/A) with conf_avg and time_avg
- List of all non-PASS results with answer previews

### 5. Diagnostic signals
- **LOWCONF on correct answers** → confidence_score() inverted or over-penalizing long queries
- **Neo4j=0 across all queries** → graph traversal regression (check Neo4j connectivity, verify `MATCH` returns nodes)
- **Qdrant=0 on >30% of queries** → Qdrant stale connections or collection empty
- **FAIL with high confidence (conf=0.75, no content)** → confidence inverted, answer generation pipeline failing silently
- **High SQL but no content** → FTS5 finding docs but LLM not generating from them (prompt or context window issue)

## Example: 50q Legal Battery (01-may-2026)

```bash
# Start API
cd PeruanoSearchEngine02 && python3 api_rest.py &

# Run battery
python3 /tmp/battery_50q_legal.py

# Output
# Total: 50 | PASS: 37 | WARN: 7 | FAIL: 1 | LOWCONF: 5
# OK: 44/50 (88.0%)
# Content: 49/50
# Time: 181s (3.6s/query)
```

Full results, summary, MD, HTML, and API backup saved to `reports/` and `backups/`.
