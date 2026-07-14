# Técnicas y Pitfalls — Pipeline El Peruano

## Groq API

### response_format json_object
El flag `response_format={"type": "json_object"}` de Groq requiere que la palabra "json" o "JSON"
aparezca EXPLÍCITAMENTE en `messages` (system o user). Sin esto, error 400:
`'messages' must contain the word 'json' in some form, to use 'response_format' of type 'json_object'`.

Fix: incluir siempre en el system prompt: "Responde ÚNICAMENTE con un objeto JSON..."

### Batch API cost
Llama 3.1 8B instant en batch: ~$0.025/M input tokens, ~$0.04/M output tokens (50% descuento vs sync).
Costo real Fase 2: 33,254 normas × ~2,000 tokens avg = ~66.5M input → ~$1.66 + ~$0.07 output = ~$1.73 total.

### RE_FUNCIONARIO pattern
Mejor patrón para detectar funcionarios en normas peruanas:
```
r'(?:Designan?|Nombrar|Encargar|Cesan|Aceptan\s+renuncia)\s+a\s+(?:la\s+señora\s+|el\s+señor\s+)?([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]{6,80})'
```
Filtrar falsos positivos: mínimo 2 palabras, excluir "LOS", "LAS", "INTEGRANTES", "MIEMBROS".

### max_tokens exceeded
Con `max_tokens=150` y textos de 10K+ chars, Groq puede fallar con:
`max completion tokens reached before generating a valid document`

Fix: reducir input a 6,000 chars o subir max_tokens a 200. La sumilla debe ser 80-200 chars (~50 tokens).

## SQLite FTS5

### Sintaxis MATCH
FTS5 es una **tabla virtual**, no una columna. NO funciona:
```sql
SELECT id FROM normas WHERE normas_fts MATCH 'término'  -- ❌ Error: no such column
```

Sintaxis correcta (JOIN con rowid):
```sql
SELECT n.id, n.sumilla FROM normas n
JOIN normas_fts ON n.rowid = normas_fts.rowid
WHERE normas_fts MATCH 'término1 AND término2'
```

### Columnas ambiguas
Si ambas tablas tienen `sumilla`, especificar: `n.sumilla`.

### MATCH con números
Números en FTS5 MATCH requieren comillas dobles para evitar interpretación como columnas:
```sql
WHERE normas_fts MATCH '"158-2025" AND PROINVERSIÓN'
```

## Cross-DB Copy

Cuando dos DBs tienen IDs idénticos y mismos schemas, la estrategia más rápida:
1. Leer datos de DB fuente (Python `SELECT`)
2. Escribir en DB destino (`UPDATE ... SET col=? WHERE id=?`)
3. 18,694 registros en 1.8s

Alternativa: `ATTACH DATABASE` → single UPDATE cross-DB en <1s pero más frágil.

No usar `fase5_poblar_columnas_null.py` sobre DBs donde los datos ya fueron extraídos y validados en otra DB con IDs idénticos.

## Cronjobs Hermes Agent

**NO CONFIABLES.** En 3 sesiones distintas, cronjobs creados con `cronjob(action='create')` quedaron en estado `scheduled` sin ejecutarse nunca. `last_run_at` siempre null. Los jobs antiguos aparecen como `completed` pero con `last_run_at` de días anteriores y `enabled: false`.

Alternativa: usar `terminal(background=true)` + `process(action='wait')` para tareas asíncronas monitoreables.

## Viajes — Extracción Regex

Los nombres de personas NO aparecen en el título de autorizaciones de viaje. Patrón: "Autorizan viaje de [cargo genérico] a [país]". El nombre real está en SE RESUELVE.

Estrategia en 2 pasos:
1. Detectar viaje en primeros 500 chars del texto (título)
2. Buscar nombre de persona en `texto[resuelve_idx:resuelve_idx+3000]`

Destino: usar regex greedy `{4,40}` (sin `?`) para capturar nombre completo del país.
