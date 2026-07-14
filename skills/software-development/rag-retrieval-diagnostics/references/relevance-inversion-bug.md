# Bug de Relevance Invertida — Detalle Técnico

## Síntoma

Un documento irrelevante (ej: "N° 158-2024-JUS" sobre extradición) aparece en posición 1 para TODAS las queries. El documento correcto aparece en FTS5 pero nunca en el top de la API.

## Causa

`api_rest.py` línea 822. La normalización de BM25 rank a relevance estaba invertida:

```python
# INCORRECTO:
relevance = round(1.0 - (abs(r.get("rank", 0)) - _min_rank) / _rank_range, 4)
```

FTS5 devuelve ranks NEGATIVOS (más negativo = mejor BM25). Ej: rank=-59 es excelente, rank=0 es pésimo.

`abs(-59) = 59`, `abs(0) = 0`. Con la fórmula `1.0 - (59-0)/59 = 0.0`, el mejor resultado obtiene relevance=0.0 y el peor relevance=1.0.

## Fix

```python
# CORRECTO:
relevance = round((abs(r.get("rank", 0)) - _min_rank) / _rank_range, 4)
```

Quitar el `1.0 -`. Mejor resultado → relevance=1.0, peor → 0.0.

## Impacto

| Set | Antes | Después |
|-----|-------|---------|
| Set 3 (40q) | 20/40 (50%) | 35/40 (88%) |
| Set 4 (40q) | N/A | 37/40 (92.5%) |

## Cómo detectarlo en otros sistemas

Si un documento irrelevante siempre aparece primero en TODAS las queries, imprimí los `relevance` scores de los top-5 resultados. Si todos son ~1.0 sin discriminación, el bug es este.
