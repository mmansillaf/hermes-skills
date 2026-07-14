# COUNT SQL Debugging Methodology

## Quick Diagnostic (30 segundos)

Cuando el COUNT en la respuesta parece incorrecto, extraer el SQL generado:

```bash
curl -s -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"cuantas RM en marzo 2024?","profile":"abogado","top_k":5}' \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
sc=d.get('sources',{}).get('sql_count',{})
print('TOTAL:', sc.get('total'))
print('BREAKDOWN:', sc.get('breakdown'))
print('SQL:', sc.get('query'))
"
```

Esto expone la query SQL real que generó el COUNT, permitiendo diagnosticar si:
- Falta filtro temporal (`fecha_publicacion LIKE 'YYYY-MM%'`)
- Falta filtro de tipo_norma (`UPPER(tipo_norma) LIKE '%...%'`)
- Sobra filtro de materia (`sumilla LIKE '%palabra_query%'`)

## Forma correcta del SQL

Para "cuantas RM en marzo 2024", el SQL correcto es:

```sql
SELECT COUNT(*) FROM normas 
WHERE UPPER(tipo_norma) LIKE '%RESOLUCIÓN MINISTERIAL%' 
AND fecha_publicacion LIKE '2024-03%'
```

## Formas incorrectas y sus causas

| SQL | COUNT | Causa |
|-----|-------|-------|
| `WHERE (sumilla LIKE '%marzo%' OR sumilla LIKE '%publicacion%') AND tipo_norma LIKE '%RESOLUCIÓN MINISTERIAL%'` | 1-10 | Filtro de materia colisiona (palabras de query no existen en sumillas) |
| `WHERE (sumilla LIKE '%rm%' OR ...) AND tipo_norma LIKE '%RESOLUCIÓN MINISTERIAL%' AND fecha_publicacion LIKE '2024-03%'` | 0-1 | Materia + temporal combinados → demasiado restrictivo |
| `WHERE UPPER(tipo_norma) LIKE '%RESOLUCIÓN MINISTERIAL%'` | 3000+ | Sin filtro temporal → cuenta todas las RM de todos los años |
| `WHERE fecha_publicacion LIKE '2024-03%'` | 500+ | Sin filtro de tipo → cuenta todas las normas de marzo (no solo RM) |
| `WHERE tipo_norma LIKE '%Resolución Ministerial%' AND fecha_publicacion LIKE '2024-03%'` | 243 | CORRECTO ✓ |

## Orden de filtros (crítico)

El orden de los bloques dentro del `try` que construye `_where_parts` en `search_sqlite()` determina qué filtros se aplican:

```
1. Trimestre (si se detecta)          → _has_strong_filter = True
2. Tipo de norma (regex + abreviaturas) → _has_strong_filter = True  
3. Año + mes (si se detecta)          → _has_strong_filter = True
4. Materia (sumilla LIKE)             → SOLO si _has_strong_filter es False
```

**Regla**: El bloque de materia DEBE ser el último. Si se inserta antes de tipo_norma o temporal, el filtro de materia se aplica incluso cuando hay filtros fuertes.

## Abreviaturas reconocidas

| Abreviatura | Tipo de norma |
|-------------|---------------|
| RM | RESOLUCIÓN MINISTERIAL |
| DS | DECRETO SUPREMO |
| RS | RESOLUCIÓN SUPREMA |
| RD | RESOLUCIÓN DIRECTORAL |
| DL | DECRETO LEGISLATIVO |
| DU | DECRETO DE URGENCIA |

Los patrones deben estar en **lowercase** porque `_ql = question.lower()`. Patrones en uppercase nunca matchean.

## LLM ignora el COUNT

Si el SQL es correcto pero el LLM sigue dando un número equivocado en su respuesta, verificar que el `SYSTEM_PROMPT` incluya:

```
- Si el contexto incluye [DATOS AGREGADOS], usa ESA cifra como total numerico. 
  Los resultados individuales son solo una muestra parcial.
```

Sin esta instrucción, el LLM cuenta manualmente de los ~5-10 resultados individuales mostrados.
