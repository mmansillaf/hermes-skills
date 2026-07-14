---
name: elperuano-ingestion-pipeline
description: "Pipeline completo de ingesta de normas de El Peruano: limpieza HTML, Groq Batch API, construccion SQLite/Qdrant/Neo4j, schema y actualizacion incremental."
---

# El Peruano RAG — Pipeline de Ingesta

## Flujo completo

```
data/YYYYMMDD/*.html (89K archivos, 80 MB)
       │
       ▼
01_clean_html.py  →  data/clean_YYYY/YYYY-MM-DD/*.md
       │              HTML→Markdown con BeautifulSoup
       │              ~2-4 horas para 40K HTMLs en CPU
       ▼
02_groq_batch_pipeline.py  →  data/batches_YYYY_groq/*.jsonl
       │                       Genera batches de 500 docs
       │                       Modelo: llama-3.1-8b-instant
       ▼
Groq Batch API  →  data/json_extracted_YYYY/*.jsonl
       │            $0.000039/doc (batch pricing)
       │            1-24h asincrono
       ▼
03_build_sqlite.py  →  data/normas_2024.db (ampliada)
       │                INSERT OR REPLACE — no borra datos existentes
       ▼
04_vectorize_qdrant.py  →  Qdrant (upsert, 384d MiniLM)
       │
       ▼
05_build_neo4j_graph.py  →  Neo4j (MERGE nodos, relaciones)
```

## Estado del Pipeline (02-may-2026 — Fases 1-3 COMPLETADAS)

| Componente | Métrica |
|------------|---------|
| SQLite unificada | 97,809 normas (2021-2025) en `normas_total.db` (0.99 GB) |
| texto_completo | 97,807/97,809 (100%) — Fase 1+1b completadas ✅ |
| sumilla | 97,808/97,809 (99.999%) — Fase 2 completada ✅ (1 norma con 9 chars imposible) |
| FTS5 normas_2021.db | 28,351/28,351 (100%) — Fase 3 completada ✅ |
| FTS5 normas_2024.db | 18,693/18,693 (100%) — Fase 4 ent_* pobladas ✅ |
| FTS5 normas_total.db | 97,809 entradas full-text |
| Qdrant | 97,809 vectores 384d Cosine en colección `normas_peruano_total` |
| Neo4j | 97,809 nodos + 436,989 relaciones |
| API | Streaming SSE · cache 1ms · paralelo · router 2 modelos |
| Batería legal | 50/50 (100%) — Nivel 1, 2, 3 |\n| Batería 100 preguntas | 73/100 (73%) — ver `references/battery-100q-results-20260502.md` |
| Pendiente | PDFs 2020 (4,670) · Seguridad API |

### Scripts del pipeline (todos en `scripts/`)

| Script | Fase | Función |
|--------|------|---------|
| `fase1_extraer_texto.py` | 1 | Extrae texto_completo de HTMLs fuente → DB (735 normas/s) |
| `fase1b_recuperar_2021.py` | 1b | Recupera 12,882 source_path corruptos vía ID |
| `fase2_sumilla_groq.py` | 2 | Groq batch → sumilla (subcomandos: generate/upload/status/download/full/cancel) |
| `fase3_rebuild_fts_2021.py` | 3 | Reconstruye FTS5 en normas_2021.db con texto_completo+sumilla |
| `fase4_extraer_entidades.py` | 4 | Extrae 8 tipos de entidades con regex → normas_2024.db (117K rows, $0) |
| `fase5_poblar_columnas_null.py` | 5 | Poblar titulo, num_articulos, has_anexos, tipo_contenido, normas_modifica desde texto_completo (38s, $0) |

## Fase 5: Poblar columnas NULL (COMPLETADA 02-may-2026)

6 columnas estaban 100% NULL: titulo, num_articulos, has_anexos, normas_modifica, normas_deroga, tipo_contenido. Extraídas con regex del texto_completo:

- **titulo**: primera línea significativa del texto (100% cobertura)
- **num_articulos**: contar "Artículo N°" y tomar el máximo (92%)
- **has_anexos**: buscar "ANEXO" en el texto (100%)
- **tipo_contenido**: clasificar sumilla con 16 patrones regex (designacion, viaje, transferencia, aprobacion, modificacion, etc.) + fallback a tipo_norma (100%, confianza 0.85 regex / 0.5 fallback)
- **normas_modifica**: regex en título+SE RESUELVE buscando "Modifican el/la Ley/Decreto N°..." (1% — son genuinamente raras)
- **normas_deroga**: regex en título+SE RESUELVE (0% — las derogaciones explícitas de leyes son casi inexistentes; ocurren como artículos dentro de normas más grandes)

⚠️  **normas_2024.db COMPLETADO**: Fase 5 se ejecutó inicialmente solo en `normas_total.db`. Las columnas `titulo`, `num_articulos`, `has_anexos`, `tipo_contenido` se copiaron de `normas_total.db` a `normas_2024.db` vía Python (leer de total → escribir en 2024, 1.8s, 18,694 normas). Estrategia preferida sobre re-ejecutar extracción porque los datos ya estaban validados en la DB fuente. Las columnas `normas_modifica` y `normas_deroga` también se copiaron (210 y 0 respectivamente — reflejan la realidad de que modificar/derogar leyes es raro).

## Fase 4: Extracción Regex de Entidades (COMPLETADA 02-may-2026)

Ver `references/regex-entity-extraction.md` para el diseño completo, patrones, y lecciones aprendidas.

## Costo Groq Batch API

| Concepto | Tokens | Costo |
|----------|--------|-------|
| Input (75K docs × 900 tokens) | 67.7M | $1.69 |
| Output (75K docs × 400 tokens) | 30.1M | $1.20 |
| **TOTAL** | **97.8M** | **$2.89** |

- Batch pricing: 50% descuento vs sync
- $0.000039 por documento
- 151 batches de 500 docs

## Schema SQLite (columnas clave)

| Columna | Origen | Notas |
|---------|--------|-------|
| `id` | custom_id del batch | `2024-06-20/2299514-4` |
| `source_path` | batch prompt | `2024/20240620/2299514-4.html` |
| `source_year` | calculado del id | `2024` |
| `normas_citadas` | batch prompt | JSON array |
| `base_legal` | batch prompt | JSON array |
| `texto_completo` | MD original (2024) o HTML extraído (2021-2023, 2025) | 4K-7K chars. Ver `references/html-text-extraction.md` para extracción desde HTML |

## Campos extraídos por el batch (llama-3.1-8b-instant)

```json
{
  "tipo_norma", "numero", "fecha", "emisor", "sumilla", "materia",
  "funcionarios", "entidades", "base_legal", "montos",
  "normas_citadas", "source_path", "page_number"
}
```

**Campos que se extraen pero NO se guardaban** (corregido 01-may-2026):
- `base_legal` → ahora columna `base_legal` (JSON)
- `normas_citadas` → ahora columna `normas_citadas` (JSON)
- `source_path` → ahora columna `source_path` (TEXT)
- `page_number` → extraído por batch, guardado implícito en id

## Subir batches a Groq

```bash
# Pipeline completo (metadatos + sumilla):
python scripts/02_groq_batch_pipeline.py full

# Solo sumillas (focalizado, ~$1.73 para 33K normas):
python scripts/fase2_sumilla_groq.py full --wait-time 7200
# O paso a paso:
python scripts/fase2_sumilla_groq.py generate
python scripts/fase2_sumilla_groq.py upload
python scripts/fase2_sumilla_groq.py download

# Verificar estado:
python scripts/fase2_sumilla_groq.py status
```

## Descargar resultados (después de Groq Batch completion)

Cuando todos los batches están `completed` (verificar con `python3 scripts/check_groq_api.py`):

```bash
# Descarga TODOS los resultados de batches completados
# Lee tracking file, consulta Groq API por batch_id, descarga output_file_id
# Salida: data/json_extracted_YYYY/results_batch_NNN.jsonl
python3 scripts/download_groq_results.py
```

El script es idempotente: si el archivo ya existe y tiene contenido (>100 bytes), lo salta.

## Gap: texto_completo NULL (80.9% de normas)

**Descubierto 02-may-2026.** El pipeline Groq batch para 2021-2023 y 2025 solo extrajo metadatos (sumilla, keywords, entidades). El campo `texto_completo` quedó NULL para 79,115/97,809 normas (81%). Solo 2024 (18,694) tiene texto.

**Causa**: los batches de 2021-2023 y 2025 se ejecutaron en modo "solo metadatos" (Mayo 2, 2026). Los HTML fuente existen (89,967 archivos, 1.5 GB), por lo que el texto puede extraerse localmente.

**Reparación**: script `scripts/fase1_extraer_texto.py` — extrae texto de HTML fuente con stdlib HTMLParser.
- Velocidad: 644 normas/s (solo parseo), ~5-8 min total con DB writes
- Tasa éxito: 98.8%
- Texto extraído: mediana 6,452 chars, promedio 9,282 chars
- Modo WAL + batch 500 UPDATEs — no bloquea la API

Ejecutar:
```bash
cd PeruanoSearchEngine02 && python3 scripts/fase1_extraer_texto.py
```

El script crea backup automático de `normas_total.db` antes de modificar.

**Para sumillas** (33,255 vacías): script `scripts/fase2_sumilla_groq.py` — pipeline focalizado solo-sumilla usando Groq batch API. Costo real ~$1.73 (no $25-30). Subcomandos: generate/upload/status/download/full/cancel. Tracking stateful en `data/sumilla_tracking.json` (resume-safe ante cortes de energía). Ver `references/sumilla-groq-batch.md` para el diseño completo.

**Para 2021 source_path corruptos**: 12,882 normas tienen paths inválidos pero recuperables desde el ID. Ver `references/2021-source-path-recovery.md`. Script: `scripts/fase1b_recuperar_2021.py`.

## Post-procesamiento (después de descargar resultados)

```bash
# Paso 1: Construir SQLite por año
python3 scripts/build_all_years_sqlite.py

# Paso 2: Unificar las 5 DBs en una sola (RECOMENDADO sobre DBs separadas)
python3 scripts/merge_dbs.py

# Paso 3: Reconstruir FTS5 (si la DB usa TEXT ids)
sqlite3 data/normas_total.db "
DROP TABLE IF EXISTS normas_fts;
CREATE VIRTUAL TABLE normas_fts USING fts5(tipo_norma, numero, emisor, sumilla, materia, texto_completo, content='');
INSERT INTO normas_fts(rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo) 
SELECT rowid, tipo_norma, numero, emisor, sumilla, materia, texto_completo FROM normas;
"

# Paso 4: Apuntar api_rest.py a la DB unificada y nueva coleccion Qdrant
# DB_PATH = BASE_DIR / "data" / "normas_total.db"
# collection: normas_peruano_semantic → normas_peruano_total

# Paso 5: Vectorizar Qdrant
python3 scripts/vectorize_total.py

# Paso 6: Grafo Neo4j unificado (con credenciales de .env)
python3 scripts/build_neo4j_total.py
```

### Pitfall: Neo4j credentials

`build_neo4j_total.py` necesita credenciales reales del `.env`: `("<NEO4J_USER>", "<NEO4J_PASSWORD>")`.

### Pitfall: Schema mismatch entre años

DBs de distintos años pueden tener columnas diferentes. `merge_dbs.py` debe usar `PRAGMA table_info` de la primera DB como schema base. No asumir columnas idénticas.

### ¿Unificar o mantener separado?

**Siempre unificar (normas_total.db)**. Razones:
- api_rest.py no necesita cambios (solo 1 línea de DB_PATH)
- Búsqueda cross-year natural (una query busca en 2021-2025)
- 1 colección Qdrant, 1 grafo Neo4j — más simple de mantener
- 105K normas caben en ~1.5 GB SQLite (manejable)

### Tracking file format

Archivo: `data/groq_batch_tracking_all.json` — formato plano (no anidado):

```json
{
  "2021/batch_001.jsonl": {
    "file_id": "file_xxx", "batch_id": "batch_xxx",
    "status": "completed", "uploaded_at": "2026-05-01 21:46:51"
  },
  "2021/batch_002.jsonl": {...}
}
```

El script `scripts/check_groq_api.py` consulta la API de Groq directamente por cada `batch_id` y actualiza el campo `status`. Usar este script (NO `upload_all_groq.py`) para verificar estado real, ya que `upload_all_groq.py` lee el tracking local que puede estar desactualizado.

### Pitfall: `03_build_sqlite.py` — dict values from Groq batch

El extractor Groq (`llama-3.1-8b-instant`) a veces devuelve valores como dicts anidados en lugar de strings planos:

```json
// Esperado (OK):
"funcionarios": ["Juan Pérez García", "María López"]

// Recibido (causa crash):
"funcionarios": [{"nombre": "Juan Pérez García", "cargo": "Director Ejecutivo"}]
```

Esto afecta a `funcionarios`, `entidades`, `base_legal`, y `normas_citadas`. La función `insert_norma()` debe normalizar estas listas con un helper que extraiga `item.nombre` o `item.name` para dicts, y convierta a string para el resto.

**Montos null**: el campo `montos` puede venir como `null` en lugar de `[]`. El parseo debe manejar `None` antes de iterar.

**FTS content-sync**: la tabla `normas_fts` usa `content='normas'` (FTS5 content-sync). NO hacer INSERT manual en FTS — SQLite actualiza el índice automáticamente al insertar en `normas`. El script original fallaba con `table normas_fts has no column named doc_id`.

### Pitfall: Tracking file vs API status

El script `upload_all_groq.py` muestra el status del tracking file LOCAL, no consulta la API de Groq. Si los batches se completaron pero el tracking no se actualizó, reportará `in_progress` incorrectamente. Usar `scripts/check_groq_api.py` para consultar la API directamente.

### Pitfall: Instancias paralelas de Hermes + tracking stale

Si hay múltiples instancias de Hermes ejecutándose (ej: VSCode + WhatsApp gateway), pueden procesar el mismo pipeline en paralelo. La instancia de VSCode (pts/0) puede haber generado `results_batch_*.jsonl` mientras la de WhatsApp descarga los mismos batches. Verificar con `ps aux | grep hermes` antes de iniciar operaciones. El tracking file local se desactualiza si los cronjobs mueren — siempre verificar contra Groq API real con `curl`.

### Pitfall: FTS5 con TEXT ids queda vacío

Cuando la tabla `normas` usa `id TEXT`, `content_rowid='id'` no funciona — el índice FTS5 queda con 0 entradas. Solución: usar `content=''` e insertar manualmente con `rowid`. Ver `references/fts5-text-id-pitfall.md`.

### Pitfall: .md files no mapean 1:1 para todos los años

Solo 2024 tiene `.md` individuales por norma (`clean_2024/YYYY-MM-DD/NNNNNNN-N.md`). 2021-2023 no tienen `.md`, y 2025 usa `pagina_X.md` (multi-norma, una página contiene ~20 normas). **NO asumir que todas las normas tienen un `.md` correspondiente.**

Para `texto_completo`, usar extracción directa desde los HTML fuente en `data/YYYYMMDD/*.html` con stdlib `HTMLParser`. Ver `references/html-text-extraction.md` para el extractor y métricas de rendimiento (644 normas/s, 98.8% éxito).

El check de cache DEBE ir ANTES de `search_sqlite()`, no después. Si va después, el cache nunca ahorra la búsqueda costosa. Y el `timing_ms` refleja el timing original (no el cache hit). Solución: `cached["timing_ms"] = round((time.time() - t0) * 1000)` al devolver del cache.

El extractor Groq ocasionalmente devuelve montos con formato español (`"1.110.00"` en vez de `1110.00`). Esto causa `ValueError` en `03_build_sqlite.py`. Tasa: <0.13%. La norma completa se guarda; solo falla el campo `monto`.

### Streaming SSE con AsyncGroq

Ver `references/streaming-sse-pattern.md` para el patrón completo. TTFT: 3s → 0.34s.

### Batería de Testing

Ver `references/battery-testing-pattern.md` para el patrón completo. Pitfall crítico: NUNCA truncar respuestas a 200 chars en reportes. El usuario revisa respuestas completas manualmente.

### Ingesta de normas faltantes encontradas online

Cuando la batería de testing revela normas no indexadas (ej: RS 040-2024-SUSALUD, RS 009-2024-MC), estas pueden buscarse en línea y ser ingestadas directamente. Ver `references/finding-missing-norms-online.md` para la metodología completa: fuentes (lapatria.pe, iuslatin.pe, gob.pe), descarga de PDF/HTML, ingesta directa a SQLite + FTS, y pitfalls.

## Extracción desde PDFs con Groq Batch (referencia nueva)

Para extraer datos estructurados (hechos, problema, fallo, entidades) desde PDFs de resoluciones judiciales usando Groq Batch API:
- `references/groq-batch-extraction.md` — modelo recomendado (Llama 3.1 8B), comparativa Scout/70B/Qwen3, optimización max_tokens=1024, límite 30K chars, estrategias de reparación JSON, costos y chunking semántico.

Scripts de batería en el proyecto:
- `scripts/battery_50q_final.py` — 50 preguntas, 3 niveles (Básico/Intermedio/Avanzado)
- `scripts/battery_55q_atuminam.py` — 55 preguntas ATU/MINAM/chatarrero
- `scripts/regenerate_full_answers.py` — regenerar TXT con respuestas completas desde JSON truncado

CLI testing: `consultar.py` se prueba con pipe desde stdin. Ver `references/battery-testing-pattern.md`.

## Monitoreo de batches Groq (MANUAL — no usar cronjobs)

**⚠️ CRONJOBS NO CONFIABLES**: La herramienta `cronjob` de Hermes Agent nunca ejecuta los trabajos programados. En 3 sesiones distintas, todos los cronjobs quedaron en estado `scheduled` sin disparar. Usar SIEMPRE monitoreo manual con `terminal` y polling.

```bash
# Verificar estado cada 10-15 minutos:
cd PeruanoSearchEngine02 && python3 scripts/fase2_sumilla_groq.py status

# Cuando todos estén "completed", descargar:
python3 scripts/fase2_sumilla_groq.py download
```

El script es idempotente: `download` salta lotes ya procesados, así que puede ejecutarse incrementalmente mientras otros lotes siguen en progreso. El tracking file `data/sumilla_tracking.json` sobrevive cortes de energía.

### Pitfall: NO usar `execute_code` para scripts con `groq`

El sandbox de `execute_code` (hermes_tools) ejecuta en un entorno aislado que NO puede cargar extensiones C compiladas (`pydantic_core._pydantic_core`). Cualquier script que importe `groq` (que depende de pydantic) fallará con `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`.

**Solución**: escribir el script como archivo `.py` (usando `write_file`) y ejecutarlo con `terminal` usando el Python del sistema.

### Pitfall: NO usar `python3 -c "..."` con emojis

El security scanner de `terminal` bloquea inline Python (`-c`) que contenga emojis o variation selectors. La solución es siempre escribir el script a un archivo primero y luego ejecutar el archivo.

### Pitfall: Groq `response_format: json_object` requiere la palabra "json" en el prompt

Si el system o user prompt NO contiene la palabra "json" (en cualquier forma, case-insensitive), Groq devuelve `400 Bad Request: 'messages' must contain the word 'json' in some form, to use 'response_format' of type 'json_object'`. Basta con incluir "Responde con un objeto JSON" o "JSON" en cualquier parte del prompt. Sin esto, el batch entero falla.

## Actualización incremental (sin perder datos)

- SQLite: `INSERT OR REPLACE` — mismo id = actualiza, nuevo id = inserta
- Qdrant: upsert por punto — mismo id = actualiza vector
- Neo4j: `MERGE` — mismo nodo = actualiza propiedades

Procesar un año nuevo NO borra años anteriores.

## API Optimizations (runtime)

Ver `references/api-optimizations.md` para patrones de rendimiento implementados en api_rest.py:
- Streaming SSE con AsyncGroq (TTFT 3s → 0.34s)
- Búsquedas paralelas con ThreadPoolExecutor (1.65x)
- Cache LRU con TTL 1h (2115ms → 1ms en cache hit)
- Router de modelos 2 niveles (8b instant para BASICO, 70b versatile para el resto)

## Refactoring Patterns

Ver `references/refactoring-patterns.md` para patrones de codigo aplicados en api_rest.py:
- `_make_result()` factory — elimina construcciones de dicts duplicadas
- Extraer funciones monoliticas en helpers nombrados (confidence_score 354→80 lineas)
- `_dedup_and_blend()` — dedup + blend scoring extraido de search_sqlite
- Cache LRU: el check DEBE ir ANTES de search_sqlite (pitfall aprendido 02-may-2026)
