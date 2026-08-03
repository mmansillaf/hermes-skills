# El Peruano RAG — Pipeline de Procesamiento

Sistema real de RAG legal del usuario: `PeruanoSearchEngine02/`

## Estructura del Proyecto

```
PeruanoSearchEngine02/
├── DATA/                    # HTMLs crudos por fecha (DATA/YYYYMMDD/*.html)
├── data/
│   ├── clean_YYYY/          # Markdowns limpios (Fase 1)
│   ├── batches_YYYY_groq/   # JSONL para Groq Batch API (Fase 2)
│   ├── normas_2024.db       # SQLite principal (~150 MB)
│   ├── qdrant_storage/      # Embeddings vectoriales
│   └── neo4j_data/          # Grafo de relaciones
├── scripts/
│   └── data_prep/
│       ├── 01_clean_html.py       # HTML → Markdown
│       ├── 02_groq_batch_pipeline.py  # Extracción LLM (Groq Batch)
│       ├── 03_build_sqlite.py     # Construye SQLite
│       ├── 04_vectorize_qdrant.py # Embeddings Qdrant
│       ├── 05_build_neo4j_graph.py # Grafo Neo4j
│       └── 06_generate_catalogs.py
├── api_rest.py              # API FastAPI en :8000
├── dashboard.py             # Streamlit (en reparación)
└── requirements.txt
```

## Pipeline Moderno (Numerado)

| # | Script | Función | ¿Groq? |
|---|--------|---------|--------|
| 01 | `01_clean_html.py` | HTML → Markdown limpio | No |
| 02 | `02_groq_batch_pipeline.py` | Genera JSONL, sube, descarga Groq | **Sí** |
| 03 | `03_build_sqlite.py` | Crea BD SQLite desde resultados | No |
| 04 | `04_vectorize_qdrant.py` | Embeddings en Qdrant | No |
| 05 | `05_build_neo4j_graph.py` | Grafo de relaciones | Opcional |
| 06 | `06_generate_catalogs.py` | Catálogos de referencia | No |

## Procesamiento Multi-Año

El sistema procesa normas por año (2020-2025). Los datos fuente están en `data/` como directorios `YYYYMMDD/` con HTMLs.

### ⚠️ Scripts con año hardcodeado (PITFALL)

**TODOS los scripts del pipeline tienen el año 2024 hardcodeado.** No aceptan parámetro `--year`:

| Script | Path hardcodeado |
|--------|-----------------|
| `01_clean_html.py` | `OUTPUT_DIR = "data/clean_2024"` (línea 26) |
| `02_groq_batch_pipeline.py` | `INPUT_DIR = "data/clean_2024"`, `BATCH_DIR = "data/batches_2024_groq"` (líneas 77-79) |

**NO existe el flag `--year`** en ningún script. Para procesar otro año, se necesita un **wrapper independiente** que:
1. Filtre archivos fuente por año
2. Apunte a los directorios correctos (`clean_YYYY`, `batches_YYYY_groq`)
3. Use tracking file separado por año (`groq_batch_tracking_YYYY.json`)

**Wrappers creados (2026-05-01):**
- `scripts/process_2021_only.py` — Limpieza HTML→MD solo para 2021 (14,189 docs, 365 dirs, 0 fallos)
- `scripts/process_2021_groq.py` — Generación JSONL para 2021 (29 batches, 155 MB)
- `scripts/upload_2021_groq.py` — Subida a Groq Batch API (usa tracking separado: `groq_batch_tracking_2021.json`)

**Patrón para replicar con otros años:** copiar el wrapper, cambiar `2021` por el año deseado en INPUT_DIR, BATCH_DIR, OUTPUT_DIR, TRACKING_FILE.

### Monitoreo Automático con Cron

Después del upload, los batches Groq tardan 1-24h en procesarse. Usar cron job de Hermes para monitoreo:

```
cronjob create "Monitor Groq YYYY + descargar" \
  --schedule 30m --repeat forever --deliver origin
```

El cron debe:
1. Leer `groq_batch_tracking_YYYY.json`
2. Consultar estado de cada batch vía `client.batches.retrieve(batch_id)`
3. Si `status == "completed"` y no descargado: descargar con `client.files.content(output_file_id)`
4. Guardar en `data/json_extracted_YYYY/`
5. Actualizar tracking con `"downloaded": true`
6. Cuando todos los batches estén `completed` + descargados: reportar finalización y cancelar cron

**Código de monitoreo:** ver `scripts/process_2021_groq.py` y `scripts/upload_2021_groq.py` como templates.

### Pipeline Batch con Groq

Costo: ~$0.0015 por documento (llama-3.1-8b-instant). Máximo 500 docs por batch.
Tiempo de procesamiento Groq: 1-24h asíncrono.
Modelo: `llama-3.1-8b-instant` con `response_format: json_object` y `temperature: 0.0`.

```bash
# Generar JSONL (wrapper por año)
python scripts/process_2021_groq.py

# El upload se hace desde el mismo script con:
python scripts/process_2021_groq.py upload --max-batches 5
```

## Sesiones Multi-Instancia

El usuario frecuentemente tiene múltiples sesiones de Hermes abiertas:
- Sesión CLI en VSCode (pts/0, pts/3) — procesamiento batch
- Sesión WhatsApp (gateway) — consultas interactivas

Para diagnosticar qué está haciendo otra sesión:
1. `ps aux | grep hermes` — identificar PIDs y terminales
2. Leer `~/.hermes/sessions/session_*.json` — ver últimos mensajes
3. Buscar comandos bloqueados: `"BLOCKED: User denied"` en logs

### Bloqueo "User denied" en Terminal

Cuando el usuario comparte un comando entre sesiones y una sesión CLI tiene un comando bloqueado con "User denied", leer el session JSON para identificar qué comando fue y ejecutarlo desde la sesión actual si el usuario lo pide.

## Diferencias con rag-legal-local

| Aspecto | rag-legal-local | PeruanoSearchEngine02 |
|---------|-----------------|----------------------|
| Fuente | Word/PDF locales | HTMLs de El Peruano |
| Escala | ~15K docs | ~65K+ normas |
| Pipeline | Un solo script | 6 fases numeradas |
| LLM | DeepSeek/Groq | Groq Batch API |
| DB | Qdrant + SQLite | Qdrant + SQLite + Neo4j |
| API | Streamlit app | FastAPI REST |
