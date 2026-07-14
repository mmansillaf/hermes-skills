# PATRÓN: Surgical Refactoring — Extraer Helpers de Funciones Monolíticas

## Cuándo usar

Cuando una función tiene >300 líneas, múltiples responsabilidades, y debe seguir funcionando 100% igual después del cambio.

## Metodología (5 pasos, validada en api_rest.py)

### Paso 1: Identificar capas lógicas

Leer la función completa. Identificar bloques que hacen UNA cosa distinta. Nombrarlos como capas.

Ejemplo real (`confidence_score`, 354 líneas → 80 líneas):

```
Capa 0: _detect_exact_id()      — IDs exactos de normas (DS 009-2024)
Capa 0b: _calc_year_penalty()   — Penalización por año
Capa 1b: _detect_jailbreak()    — Patrones de jailbreak
Capas 2+4+5: _calc_semantic_defense() — Overlap + existencia + coexistencia  
Capa 6: _calc_temporal_anomaly() — Anomalía temporal
Helper: _query_len_factor()     — Reducción para queries largas
```

### Paso 2: Extraer UNA capa a la vez

NO reescribir toda la función de golpe. Extraer una capa, testear, commit. Luego la siguiente.

```python
# ANTES (354 líneas monolíticas):
def confidence_score(results, question, sqlite_source_count):
    if not results: return 0.0, {}
    # ... 350 líneas de lógica mezclada ...
    return round(weighted, 4), debug_conf

# DESPUÉS (80 líneas orquestador):
def confidence_score(results, question, sqlite_source_count):
    if not results: return 0.0, {}
    has_exact_id, boost, penalty = _detect_exact_id(results, question, ...)
    year_penalty = _calc_year_penalty(question, results)
    semantic_fp, defense_debug = _calc_semantic_defense(question, results)
    fp_penalty += semantic_fp
    fp_penalty += _calc_temporal_anomaly(question, results)
    # ... solo orquestación, 0 lógica de dominio ...
    return round(weighted, 4), debug_conf
```

### Paso 3: Las helpers son funciones puras (mismos inputs → mismos outputs)

Cada helper recibe `(question, results)` o equivalentes. NO dependen de estado global ni closures complejas. Esto permite testearlas aisladamente.

### Paso 4: Testear DESPUÉS de cada extracción

NO esperar a tener todas las helpers para testear. Después de extraer cada una:

```python
# Test rápido: misma query antes y después debe dar mismo confidence
resp = requests.post('http://localhost:8000/query', json={'question': 'Ley 32108'})
assert resp.json()['confidence'] == 0.85  # debe ser idéntico al original
```

### Paso 5: Commit atómico por helper

Cada extracción es un commit separado. Si una rompe algo, rollback de 1 commit.

```
34440a1 refactor: confidence_score en 6 helpers
20b3554 refactor: _dedup_and_blend + _make_result factory
```

## Anti-patrones a evitar

- **NO** reescribir la lógica. Solo reorganizar. Si un número cambia (ej: `0.25 → 0.30`), es un bug, no un refactor.
- **NO** crear helpers que dependen de 8 closures del scope padre. Si necesita más de 3 params del padre, está mal diseñada.
- **NO** hacer refactor + feature en el mismo commit. Refactor primero, feature después.

## Resultado en api_rest.py

| Función | Antes | Después | Cambio |
|---------|-------|---------|--------|
| `confidence_score()` | 354 líneas | 80 líneas | -274 (-77%) |
| `search_sqlite()` | 468 líneas | ~380 líneas | -88 (-19%) |
| Duplicación dict resultados | 5+ lugares | `_make_result()` | 1 factory |
| Dedup + blend | 38 líneas inline | `_dedup_and_blend()` | 1 helper |

## Verificación

10 queries de prueba (exact_id, broad, complex, basico, avanzado, SQLi) deben pasar con 0 regresiones. Si alguna falla, el último commit es el culpable — revertir.
