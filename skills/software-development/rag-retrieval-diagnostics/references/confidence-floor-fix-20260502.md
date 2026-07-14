# Confidence Floor Fix: 0.75 → 0.60

**Problema (02-may-2026):** 6 falsos positivos en batería 100 preguntas. Queries adversariales como "DS 501-2028-SA presupuesto", "presupuesto general de la republica 2027", "normas emitidas en 2010" obtenían confianza ≥0.75 sin activar web fallback.

**Causa raíz:** `api_rest.py` línea 607 (antes del fix):

```python
if has_real_overlap and weighted < 0.75 and (ratio >= 0.65 or db_ratio >= 0.90):
    weighted = 0.75  # ← FLOOR demasiado alto
```

Cuando hay CUALQUIER solapamiento léxico entre la query y los resultados (aunque sea tangencial — ej: "presupuesto" matchea en normas reales), la confianza salta automáticamente a 0.75. El sistema interpreta "hay términos en común" como "la respuesta es correcta", ignorando que el contexto es equivocado.

**Fix (02-may-2026):**

```python
if has_real_overlap and weighted < 0.60 and (ratio >= 0.65 or db_ratio >= 0.90):
    weighted = 0.60  # ← Floor bajado
```

**Resultados:**

| Query adversarial | Antes | Después |
|-------------------|-------|---------|
| DS 501-2028-SA presupuesto | 0.75 ❌ | 0.60 ✅ |
| decretos supremos del año 2019 | 0.75 ❌ | 0.60 ✅ |
| presupuesto general de la republica 2027 | 0.75 ❌ | 0.24 ✅ |
| normas emitidas en 2010 | 0.75 ❌ | 0.60 ✅ |
| arrendamiento naves espaciales | 0.75 ❌ | 0.24 ✅ |
| normas del año 2020 | 0.76 ❌ | 0.72 ⚠️ |

**Limitación:** "normas del año 2020" sigue en 0.72 porque la DB realmente tiene 854 normas con fecha 2020. No es un falso positivo — hay normas que legítimamente matchean. La solución complementaria es el filtro temporal en FTS5 (ver `references/temporal-filter-fts5.md`).

**Verificación:** Re-ejecutar las queries adversariales que antes eran FP. Confianza debe bajar a ≤0.60 o activar web fallback.

**Nota:** El floor de 0.75 original fue diseñado para evitar que queries funcionales legítimas con solapamiento parcial obtuvieran confianza demasiado baja. 0.60 es el nuevo balance: suficiente para queries reales con datos parciales, bajo para queries adversariales.
