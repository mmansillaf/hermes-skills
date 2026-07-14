# 6 Fixes de Confianza — Metodología Completa (01-may-2026)

## Diagnóstico inicial

Síntoma: SET2 50q legal — 5 LOWCONF con respuestas correctas pero conf 0.22-0.28 (deberían ser 0.70-0.85). El FAIL I30 tenía conf=0.75 con respuesta vacía ("no se encontraron motivos").

## Metodología de tracing

NO aplicar fixes sin trazar UNA query de principio a fin. Se usó un script de diagnóstico que importaba `confidence_score()` directamente y ejecutaba paso a paso:

```python
# Trazar componentes manualmente
base_weighted = semantic_quality + count_score + sqlite_boost + neo4j_boost
fp_penalty = Capa2 + Capa4 + Capa5
weighted = max(base_weighted - fp_penalty * ql_factor, 0.10)
```

## Bug #1: Capa 4 muerta (ROOT CAUSE)

`confidence_score()` línea ~481 usa `db.execute(...)` pero `db` nunca se inicializa con `db = get_sqlite()`. El `except: pass` silencia el NameError. `db_exist_count` siempre es 0, `db_ratio = 0.0`, y Capa 4 penaliza TODAS las queries con +0.30 fantasma.

**Fix:** Agregar `db = get_sqlite()` antes del loop de meaningful_words.

## Bug #2: Floor 0.75 demasiado agresivo

El floor `if _has_real_overlap and weighted < 0.75: weighted = 0.75` protegía queries válidas (B01) pero también falsos positivos (I30). I30 tenía alta confianza aunque el LLM respondía "no se encontraron motivos".

**Fix:** `if _has_real_overlap and weighted < 0.75 and (ratio >= 0.65 or db_ratio >= 0.90): weighted = 0.75`

## Bug #3: Post-hoc negation bypass en conf=0.75

La condición era `confidence < 0.75` (estricto). Cuando el floor empujaba la confianza a exactamente 0.75, el chequeo de negación se saltaba completamente.

**Fix:** `confidence <= 0.75` + verificar starts-negation en primeros 80 chars de la respuesta.

## Bug #4: Post-hoc negation bypass por alto overlap

El bypass `if overlap_ratio >= 0.4: IGNORE` protegía queries donde el LLM decía "no se encontró X específico" pero los resultados SÍ eran relevantes. Pero este bypass también protegía I30 donde la respuesta era genuinamente vacía.

**Fix:** `if overlap_ratio >= 0.4 and not _starts_negation: IGNORE`

## Bug #5: Capa 4 thresholds demasiado agresivos

`db_ratio < 0.40` penalizaba +0.30, `db_ratio < 0.60` penalizaba +0.15. Con Capa 4 muerta, db_ratio=0.0 siempre activaba la penalización máxima.

**Fix:** `db_ratio < 0.30` para +0.30, `db_ratio < 0.50` para +0.15

## Bug #6: debug_conf vacío

La variable `debug_conf = {}` se creaba al inicio de `confidence_score()` pero nunca se poblaba. Imposible diagnosticar sin visibilidad.

**Fix:** Poblar debug_conf con 11 métricas: base_weighted, fp_penalty, weighted_pre_floor, ratio, db_ratio, semantic_quality, sqlite_quality, qdrant_contrib, has_real_overlap, has_exact_id, ql_factor

## Resultado

200 preguntas en 4 baterías (SET1-SET4): 99.5% score, 1 solo fail. Confianza promedio: 0.55.

## Rollback

Si los fixes causan regresión:
```bash
git checkout v3.0-pre-html-fts5-20260501_1923
# O restaurar backup:
cp backups/api_rest_v3.0_pre_html_fts5_20260501_1923.py api_rest.py
```
