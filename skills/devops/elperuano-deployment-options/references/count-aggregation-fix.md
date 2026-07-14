# COUNT Aggregation Fix — Inyectar datos agregados en el prompt del LLM

Sesión: 05-may-2026. Fix de 2 partes aplicado en `api_rest.py`.

## Problema

Queries de conteo como "¿Cuántas Resoluciones Ministeriales hay en 2024?" ejecutaban
correctamente `SELECT COUNT(*)` (resultado: 15), pero el LLM respondía "varias..."
sin mencionar el número exacto. El dato agregado existía en `sources["sql_count"]`
pero nunca llegaba al contexto del prompt.

## Causa raíz

`_build_context()` en `api_rest.py:773` solo procesaba `results` (normas individuales).
El campo `sources["sql_count"]` con el total agregado y breakdown nunca se inyectaba
en el contexto que recibe el LLM.

Adicionalmente, la query COUNT usaba `sumilla LIKE '%keyword%'` en vez de filtrar
por `tipo_norma`, produciendo totales imprecisos (ej: "RM en 2024" devolvía 216
porque matcheaba cualquier norma con "resolución" en la sumilla, no solo RM).

## Fix Parte 1: Inyectar COUNT en el contexto del LLM

Modificar `_build_context(results)` → `_build_context(results, sources=None)`:

```python
def _build_context(results, sources=None):
    context_parts = []
    
    # Inyectar datos de agregacion (COUNT) al inicio si existen
    if sources and "sql_count" in sources:
        sc = sources["sql_count"]
        count_header = f"[DATOS AGREGADOS]\nTotal normas encontradas: {sc.get('total', '?')}\n"
        if sc.get('breakdown'):
            count_header += "Desglose por tipo:\n"
            for g in sc['breakdown'][:7]:
                count_header += f"  - {g['tipo_norma']}: {g['cnt']}\n"
        count_header += "\n[RESULTADOS INDIVIDUALES]"
        context_parts.append(count_header)
    
    for i, r in enumerate(results[:10]):
        ...
```

Y actualizar ambas funciones que llaman a `_build_context`:

```python
# En generate_answer() — línea 861:
context = _build_context(results, sources)  # antes: _build_context(results)

# En generate_answer_stream() — línea 893:
context = _build_context(results, sources)  # antes: _build_context(results)
```

## Fix Parte 2: Filtrar COUNT por tipo_norma exacto

Agregar detección de patrones de tipo de norma en la pregunta (`search_sqlite`):

```python
# Detectar tipo de norma en la pregunta para filtrar COUNT con precision
_tipo_patterns = [
    (r'resoluciones?\s*ministeriales?', 'RESOLUCIÓN MINISTERIAL'),
    (r'decretos?\s*supremos?', 'DECRETO SUPREMO'),
    (r'resoluciones?\s*supremas?', 'RESOLUCIÓN SUPREMA'),
    (r'resoluciones?\s*directorales?', 'RESOLUCIÓN DIRECTORAL'),
    (r'resoluciones?\s*jefaturales?', 'RESOLUCIÓN JEFATURAL'),
    (r'ordenanzas?', 'ORDENANZA'),
    (r'leyes?\b', 'LEY'),
    (r'decretos?\s*legislativos?', 'DECRETO LEGISLATIVO'),
]
for _pat, _tipo in _tipo_patterns:
    if re.search(_pat, _ql):
        _where_parts.append(f"UPPER(tipo_norma) LIKE '%{_tipo}%'")
        break
```

## Resultados

| Query | ANTES | DESPUÉS |
|-------|-------|---------|
| ¿Cuántas RM en 2024? | "varias RM... N° 377, 244..." (COUNT=216 impreciso) | "**15** Resoluciones Ministeriales" (COUNT=15 exacto) |
| ¿Cuántos DS en 2024? | — | COUNT=37 (21 DS + 16 DS normalizados) |
| ¿Cuántas leyes en 2024? | — | COUNT=2 |

## Archivos modificados

- `api_rest.py`: `_build_context()` (línea 773), `generate_answer()` (861), `generate_answer_stream()` (893), `search_sqlite()` (296-319)
