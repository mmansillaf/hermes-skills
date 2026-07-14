# Context Enrichment — Mejora de resultados al LLM (Mayo 2026)

## Sintoma

El documento correcto EXISTE en la BD pero el LLM nunca lo menciona en la respuesta.
Ej: Ley 32108 aparece en resultados de busqueda (posicion 5), pero el LLM solo cita las primeras 3 leyes.

## Causa raiz

- Solo se enviaban 10 resultados al contexto del LLM
- Los resultados de Neo4j graph traversal mostraban `tipo=None` (invisible al LLM)
- Las sumillas estaban truncadas a 300 chars (informacion perdida)
- El LLM no tenia scores de relevancia para priorizar
- El prompt decia "cita el numero exacto" pero no "menciona TODAS"

## Solucion (4 cambios simultaneos)

### 1. Resultados en contexto: 10 → 15

```python
for i, r in enumerate(results[:15]):  # era results[:10]
```

### 2. Scores visibles al LLM

```python
_score = r.get('relevance') or r.get('blend_score', 0)
_src = r.get('source', '?')
parts = [f"[{i+1}] {_tipo} {r.get('numero','')} (score={_score:.2f}, src={_src})"
         f" ({r.get('fecha','')}) - {r.get('emisor','')}"]
```

### 3. Sumillas mas largas: 300 → 500 chars

```python
parts.append(f"    Sumilla: {r['sumilla'][:500]}")  # era 300
```

### 4. Tipo fallback para Neo4j graph traversal

Los nodos Neo4j a veces no tienen propiedad `tipo_norma`. Fallback por regex:

```python
if not _tipo:
    import re
    _sum = d.get("sumilla", "") or ""
    _m = re.search(r'(LEY|DECRETO\s+(SUPREMO|LEGISLATIVO)|RESOLUCI[OÓ]N|ORDENANZA|ACUERDO)', 
                   _sum, re.IGNORECASE)
    _tipo = _m.group(0).upper() if _m else ""
```

### 5. Prompt inclusivo

```python
# Antes:
"- Si la respuesta esta en las normas, cita el tipo y numero exacto."

# Despues:
"- Menciona TODAS las leyes o normas relevantes de la seccion NORMAS ENCONTRADAS"
"  que apliquen a la pregunta, no solo la primera."
```

## Resultado

| Query | Antes | Despues |
|-------|-------|---------|
| "que ley modifica el crimen organizado?" | 3 leyes, sin Ley 32108 | **6 leyes**, incluye Ley 32108 |
| Longitud respuesta | ~600 chars | **1,270 chars** |

## Relacion con la cadena anti-alucinacion

Este pattern es la **Capa C** de la defensa en 4 capas. Las otras 3 capas son:
- **Capa D (LeyBooster)**: prioriza resultados tipo LEY en el retriever
- **Capa B (Prompt)**: grounding + enumeracion de leyes
- **Capa A (Cleaner+Validator)**: post-procesamiento regex + validacion heuristica

Ver `references/hallucination-auto-correction.md` para el patron completo.

## Pitfalls

1. **Pycache stale**: despues de modificar `graph_traversal.py`, limpiar `__pycache__/` o el proceso usara el .pyc viejo
2. **Numero de resultados**: 15 es seguro para Groq (128K tokens). Si se usa modelo con ventana mas pequena, reducir
3. **Scores 0.00**: si TODOS los resultados tienen score identico (FTS5 ranks muy cercanos), la normalizacion da 0. Verificar `_raw_ranks`
4. **LeyBooster + None tipo**: `r.get('tipo', '').upper()` crashea si `tipo=None`. Usar `(r.get('tipo') or '').upper()`
5. **Cleaner deja fragmentos**: al eliminar leyes organizativas, limpiar residuos: comas dobles, "se basan en , .", lineas vacias multiples
