# Diagnóstico Completo: confidence_score() — 4 Bugs

**Fecha:** 01-may-2026 | **Archivo:** `api_rest.py:235-566, 1532` | **Diagnóstico:** traza quirúrgica componente por componente

## Problema

Las queries largas (>150 chars) y las queries con respuestas correctas reciben confianza baja (0.22-0.28), mientras que queries con respuestas tipo "no se encontró" reciben confianza alta (0.75). Tras aplicar el fix de reducción por query_len (30-abr), el problema persistió porque hay 3 bugs adicionales no detectados entonces.

## Metodología de Diagnóstico

Ver `scripts/trace_confidence.py` — script que importa `confidence_score()` directamente, obtiene resultados reales del API, y traza CADA componente: base_weighted, fp_penalty, capas, floor, post-hoc negation. Ejecutar con:

```bash
python3 scripts/trace_confidence.py
```

## Síntomas (batería 50q legal 01-may-2026)

- I30 FAIL: respuesta "no se encontraron motivos" (933 chars), conf=0.75
- B15 LOWCONF: respuesta correcta "UIT S/ 5,150" (977 chars), conf=0.275
- A38 LOWCONF: análisis constitucional completo (1418 chars), conf=0.575
- A50 LOWCONF: análisis integral de 4 lógicas de gestión (3092 chars), conf=0.575

## Hallazgo Clave: Base idéntica para TODAS las queries = 0.800

`sqlite_quality(0.55) + count_score(0.15) + sqlite_boost(0.10) = 0.800`. Qdrant y Neo4j aportan CERO porque los resultados no tienen `source="qdrant"` (el campo source se pierde en el merge/dedup). El ÚNICO diferenciador entre queries es el fp_penalty de las capas 2/4/5 y el floor.

## Bug #1: Floor `_has_real_overlap → 0.75` demasiado permisivo

**Línea 561-562:**
```python
if _has_real_overlap and weighted < 0.75:
    weighted = 0.75
```

**Condición:** `ratio >= 0.5 and (not _has_zero_match or db_ratio >= 0.80)`. Con solo 50% de overlap y sin zero-match words se activa. I30 tiene overlap=0.50 y solo "tamaños" como zero-match → floor se activa → conf=0.75.

**Fix:** Subir umbrales:
```python
if _has_real_overlap and weighted < 0.75:
    _has_real_overlap = ratio >= 0.65 and (not _has_zero_match or db_ratio >= 0.90)
    if _has_real_overlap:
        weighted = 0.75
```

## Bug #2: Post-hoc negation bypass cuando conf=0.75 exacto

**Línea 1532:**
```python
if llm_answer and confidence >= 0.5 and len(web_results) == 0 and confidence < 0.75:
```

El operador `< 0.75` (estricto) excluye conf=0.75 exacto. Cuando el floor de Bug #1 fuerza conf=0.75, el chequeo de negación post-hoc se salta completamente. I30 dice "no se encontraron motivos" pero no se penaliza.

**Fix:** Cambiar a `<=`:
```python
if llm_answer and confidence >= 0.5 and len(web_results) == 0 and confidence <= 0.75:
```

## Bug #3: Capa 4 sobre-penaliza db_ratio aceptable

**Línea 501-504:**
```python
if db_ratio < 0.40:
    fp_penalty += 0.30
elif db_ratio < 0.60 and _has_zero_match:
    fp_penalty += 0.15
```

B15 tiene db_ratio=0.75 (75% de meaningful words existen en BD) pero la respuesta es correcta. La penalización de +0.15 de Capa 2 (ratio=0.25) más la ausencia de floor la dejan en 0.275. El umbral 0.40 es demasiado alto para el mercado peruano donde muchas palabras técnicas no están en sumillas.

**Fix:** Bajar umbrales:
```python
if db_ratio < 0.25:
    fp_penalty += 0.30
elif db_ratio < 0.45 and _has_zero_match:
    fp_penalty += 0.15
```

## Bug #4: `debug_conf` nunca se puebla

**Línea 249:** `debug_conf = {}` — se crea vacío y nunca recibe asignaciones. La API devuelve `"debug_internal": {}` en todas las queries, imposibilitando el diagnóstico sin monkey-patching.

**Fix:** Poblar debug_conf en cada paso:
```python
debug_conf["base_weighted"] = round(weighted, 4)
debug_conf["fp_penalty"] = round(fp_penalty, 4)
debug_conf["ratio"] = round(ratio, 4) if 'ratio' in dir() else 0
debug_conf["db_ratio"] = round(db_ratio, 4)
debug_conf["_has_real_overlap"] = _has_real_overlap
debug_conf["floor_applied"] = _has_real_overlap and weighted_after < 0.75
```

## Fix Completo (aplicar en orden)

```python
# 1. Capa 4 umbrales (línea 501-504)
if db_ratio < 0.25:
    fp_penalty += 0.30
elif db_ratio < 0.45 and _has_zero_match:
    fp_penalty += 0.15

# 2. Floor condicional (línea 561-562)
if _has_real_overlap and weighted < 0.75:
    # Recalcular con umbrales mas estrictos
    _strong_overlap = ratio >= 0.65 and (not _has_zero_match or db_ratio >= 0.90)
    if _strong_overlap:
        weighted = 0.75

# 3. Post-hoc negation (línea 1532)
if llm_answer and confidence >= 0.5 and len(web_results) == 0 and confidence <= 0.75:

# 4. Poblar debug_conf (varias líneas) — ver script trace_confidence.py para ubicaciones exactas
```

## Impacto Estimado

- I30: 0.75 → 0.52 (floor NO activa con umbrales nuevos)
- B15: 0.275 → 0.65 (Capa 4 reducida + floor podría activar)
- A38: 0.575 → 0.76 (ya estaba cerca, floor activaría con nuevo umbral)
- Score batería 50q: 88% → ~96% (48/50)

## Historial de Intentos Previos

- **30-abr:** Fix de reducción por query_len (x0.3/x0.5/x0.7). Mejoró confianza avg de 0.219→0.628 pero NO resolvió los falsos positivos/negativos.
- **01-may:** Diagnóstico completo revela que el fix anterior era insuficiente porque no atacaba el floor ni el post-hoc bypass.
