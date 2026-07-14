# Forced Injection — Parche Táctico para Búsqueda

**Fecha:** 30-abr-2026 | **Estado:** Parcialmente implementado, superado por fix de relevance

## Concepto

Cuando FTS5 no rankea documentos específicos, inyectarlos directamente vía SQL LIKE usando reglas de entidad.

## Ejemplo

```python
# Si la query menciona "Intercrédito", forzar SBS 03429-2024 al top
if 'intercrédito' in query.lower():
    doc = db.execute("SELECT * FROM normas WHERE numero LIKE '%03429%'")
    results.insert(0, doc)
```

## Reglas implementadas (10)

1. "000147" en query → INDECOPI 000147
2. "Intercrédito" → SBS 03429
3. SBS + Chile + viaje → SBS 03416
4. Molina/MDLM + prórroga → DA 006-2024
...etc

## Simulación vs Realidad

- **Simulación directa contra SQLite:** 17/17 docs forzados a posición 1
- **API real:** No efectivo — docs se pierden en merge/dedup del pipeline

## Por qué no funcionó

El código de inyección se ejecuta en `search_sqlite()` pero los resultados pasan por múltiples transformaciones posteriores (relevance normalization, merge con Qdrant, dedup por numero, sort por blend_score) que pueden reordenar o descartar los docs inyectados.

## Lección

Las reglas de inyección son un **parche táctico** que no escala. La solución arquitectónica es:
1. Arreglar el ranking FTS5 (relevance invertida — YA CORREGIDO)
2. Reformular queries FTS5: `(term_raro) AND (comun1 OR comun2)`
3. El fix de 1 línea (relevance) eliminó la necesidad del forced injection
