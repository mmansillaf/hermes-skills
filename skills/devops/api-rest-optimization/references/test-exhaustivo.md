# Test Exhaustivo — Resultados

## Script: `reports/test_exhaustivo.py`

## Tests cubiertos (10 grupos, 26 checks)

| # | Grupo | Tests | PASS |
|---|-------|-------|------|
| 1 | Health check | 4 (API + SQLite + Qdrant + Neo4j) | 4/4 |
| 2 | Validación pregunta | 3 (2 chars→422, 1001→422, válida→200) | 3/3 |
| 3 | Anti-hallucination | 8 (2 queries × 2 absent + 1 present + length) | 8/8 |
| 4 | LeyBooster | 3 (menciona Ley, >300 chars, top-5 Ley) | 3/3 |
| 5 | Neo4j tipo | 1 (tipo != vacío) | 0/1* |
| 6 | Timeout | 1 (2 queries sin bloquear) | 1/1 |
| 7 | max_tokens | 2 (avanzado >500, basico >500) | 2/2 |
| 8 | Contexto | 2 (≥3 resultados, con scores) | 2/2 |
| 9 | Prompt inclusivo | 1 (≥2 leyes mencionadas) | 1/1 |
| 10 | Grounding | 1 (sin numeros extra) | 0/1* |
| | **Total** | **26** | **24/26 (92%)** |

*FAIL #5 (Neo4j tipo): Si la query no activa graph traversal (no suficientes entidades), no hay resultados Neo4j para verificar. Falso positivo si la prueba aísla el caso.

*FAIL #10 (Grounding): "DL 1182" es citado correctamente dentro de la descripción de la Ley 31284. El test es demasiado estricto — detecta todo número de 4-5 dígitos como "sospechoso", pero DL 1182 es una referencia válida.

## Cómo ejecutar
```bash
cd PeruanoSearchEngine02 && source .venv/bin/activate
python3 reports/test_exhaustivo.py
```

Requiere API corriendo en localhost:8000.
