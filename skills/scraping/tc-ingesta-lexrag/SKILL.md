---
name: tc-ingesta-lexrag
description: >-
  Ingesta de PDFs del TC SEDETC al sistema LexRAG (FAISS + BM25 + NetworkX).
  Pipeline completo: extraccion de texto con PyMuPDF, Groq Batch API para
  extraccion estructurada, conversion a formato indexer e indexacion.
category: scraping
triggers:
  - "tc sedetc pdf ingestion lexrag"
  - "ingesta pdfs tribunal constitucional lexrag"
  - "procesar pdfs tc a faiss bm25 grafo"
  - "groq batch api jurisprudencia tc"
related_skills:
  - tc-sedetc-scraper
  - peruvian-judicial-scraping
  - hermes-agent
---

# TC SEDETC — Ingesta a LexRAG

Pipeline para incorporar PDFs de jurisprudencia del Tribunal Constitucional
(descargados con `tc-sedetc-scraper`) al sistema de busqueda hibrida LexRAG
(FAISS + BM25 + NetworkX).

## Trigger

Usar este skill cuando:
- El usuario tenga PDFs de jurisprudencia del TC Peruano (SEDETC) y quiera indexarlos
- Se necesite procesar PDFs via Groq Batch API para extraccion estructurada
- Se quiera agregar documentos nuevos a un sistema LexRAG existente
- Se necesiten estimaciones de costo/tiempo para ingesta masiva de PDFs

## Arquitectura

```
PDFs/*/*.pdf                    (descargados por tc_scraper.py)
    ↓ PyMuPDF extrae texto
Texto plano (con limpieza)
    ↓ clasifica por tokens
Cortos (≤1000 tok) → Llama-3.1-8B    |   Largos (>1000 tok) → Llama-3.3-70B
    ↓ JSONL format                    |   ↓ JSONL format
Archivos JSONL para Groq Batch API
    ↓ Upload + Create Batch
Groq Batch API (procesamiento asincrono)
    ↓ Download results
JSON con hechos + problema + fallo + entidades
    ↓ Convertir a formato rag_listo_batch_*.json
Archivos en data_raw/ (mismo formato que pipeline original)
    ↓ pipeline/indexer.py
FAISS + BM25 + NetworkX actualizados
```

## Prerequisitos

- Proyecto LexRAG en D:\PyCode\ResumenTokensJurisprudencias (o /mnt/d/...)
- PDFs en D:\PyCode\TC_SEDETC_Scraper\pdfs\ (por ano)
- Metadata en D:\PyCode\TC_SEDETC_Scraper\data\metadata.csv
- GROQ_API_KEY valida en .env
- pymupdf instalado (pip install pymupdf)
- Python 3.10+

## Pipeline Paso a Paso

### 1: Preparar Batch

```bash
cd D:\PyCode\ResumenTokensJurisprudencias

# N docs mas recientes (escanea de 2026 hacia abajo)
python scripts/data_prep/preparar_batch_tc.py --max 5000 --workers 8

# Anos especificos (ej: 2018-2023)
python scripts/data_prep/preparar_batch_2018_2023.py

# Solo estimar costos sin extraer
python scripts/data_prep/preparar_batch_tc.py --max 5000 --dry-run
```

Esto genera archivos en `data_raw/batches_tc/`:
- `batch_tc_70B_pt*.jsonl` — largos (>1000 tok, Llama-3.3-70B)
- `batch_tc_8B_pt*.jsonl` — cortos (<=1000 tok, Llama-3.1-8B)

### 2: Subir a Groq Batch API

```bash
python scripts/data_prep/enviar_batch_tc.py
```

Upload automatico + creacion de batches + monitoreo + descarga + conversion.

Para subida manual:
```bash
python scripts/data_prep/subir_batch_v2.py
```

### 3: Indexar

```bash
set PYTHONPATH=%CD%
python pipeline/indexer.py
```

El indexer es **resumible**: carga indices existentes, detecta doc_ids ya procesados,
solo ingesta documentos nuevos. Usa `--force` para reindexar desde cero.

## Costos (Groq API, Jun 2026)

| Modelo | Precio input | Precio output | Costo/doc |
|--------|:-----------:|:------------:|:---------:|
| Llama-3.3-70B | $0.59/1M tok | $0.79/1M tok | ~$0.0019 |
| Llama-3.1-8B | $0.05/1M tok | $0.08/1M tok | ~$0.0001 |

- 90% docs son largos (70B), 10% cortos (8B)
- Promedio ponderado: ~$0.0017/doc
- 1,500 docs: ~$2.50
- 5,000 docs: ~$9.00
- 11,224 docs (corpus completo): ~$20.00

## Tiempos

| Fase | 1,500 docs | 5,000 docs |
|------|:----------:|:----------:|
| Extraccion PDFs | 4-5 min | 15-20 min |
| Groq Batch API | 30-45 min | 2-3 horas |
| Indexacion | 2-3 min | 8-10 min |

## Pitfalls

1. **custom_id duplicados**: Si dos PDFs tienen el mismo nombre de archivo en distintos directorios,
   el batch falla con `duplicate_custom_id`. Solucion: agregar sufijo unico con
   `line_data['custom_id'] = f'{cid}_v{seen[cid]}'` en el JSONL.

2. **GROQ_API_KEY expira**: El error `expired_api_key` (401) requiere renovar la key
   en https://console.groq.com/keys. Verificar con:
   ```python
   from groq import Groq; Groq(api_key='...').models.list()
   ```

3. **Output bufferizado en background**: Usar `PYTHONUNBUFFERED=1` para ver logs
   en tiempo real cuando se ejecuta en background.

4. **Primera carga lenta (~20s)**: SentenceTransformer descarga el modelo la primera vez.
   Usar el servidor web (uvicorn) para mantenerlo en memoria entre consultas.

5. **El indexer salta documentos ya procesados**: Si un batch se ejecuta dos veces,
   los documentos ya existentes se saltan (por doc_id). Esto significa que batches
   subsecuentes solo agregan documentos NUEVOS.

6. **Los PDFs escaneados (~1%) no tienen texto**: PyMuPDF extraera cadenas vacias.
   Se pueden omitir o procesar con OCR (tesseract).

7. **Los archivos de resultados de Groq se descargan via `files.content(batch.output_file_id)`:
   El metodo `.text` es **callable** (`.text()`) en la version actual de la libreria groq.

## Verificacion Post-Ingesta

### 1: Verificar indices

```python
from core.index_manager import index_manager
index_manager.initialize(base_dir='.')
stats = index_manager.stats()
print(f"FAISS: {stats['faiss_vectors']} vec | Grafo: {stats['graph_nodes']} nodos")
```

### 2: Verificar recuperacion de documentos TC

```python
from retrieval.hybrid_search import get_hybrid_context
_, context, _ = get_hybrid_context("amparo TC", top_k=5)
tc_count = context.count("tc_")  # >0 si hay docs TC
### 3: Generar metadata TC para citas legibles

Despues de indexar, los documentos TC se muestran con filename raw (`tc_00364-2022-AA.pdf`) en las citas. Para que muestren identificadores legibles (`EXP. N.° 00364-2022-AA/TC`):

```bash
cd D:\\PyCode\\ResumenTokensJurisprudencias
python -c "
import csv, json, glob, os, re
tc_meta = {}
with open('D:\\PyCode\\TC_SEDETC_Scraper\\data\\metadata.csv', newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        fname = f\"{row['expediente']}.pdf\"
        tc_meta[f'tc_{fname}'] = {'identificador': f\"EXP. N.° {row['expediente']}/TC\", 'organo': 'Tribunal Constitucional', 'tipo': f'Sentencia TC ({row.get(\"tipo\",\"\")})', 'fecha': row.get('fecha_publicacion',''), 'materia': ''}
for pdf in glob.glob('D:\\PyCode\\TC_SEDETC_Scraper\\pdfs\\*\\*.pdf'):
    key = f'tc_{os.path.basename(pdf)}'
    if key not in tc_meta:
        exp = os.path.basename(pdf).replace('.pdf','')
        exp_clean = re.sub(r'\s*\(.*?\)', '', exp)
        m = re.search(r'\((.*?)\)', exp)
        extra = f' ({m.group(1)})' if m else ''
        tc_meta[key] = {'identificador': f\"EXP. N.° {exp_clean}/TC{extra}\", 'organo': 'Tribunal Constitucional', 'tipo': 'Sentencia TC', 'fecha': '', 'materia': ''}
with open('data/indices/tc_docs_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(tc_meta, f, ensure_ascii=False, indent=1)
print(f'TC metadata generada: {len(tc_meta)} docs')
"
```

El archivo `retrieval/hybrid_search.py` ya carga automaticamente `data/indices/tc_docs_metadata.json` como fallback en `_doc_header()`. No requiere cambios adicionales. Los documentos TC apareceran como `EXP. N.° 00364-2022-AA/TC | Tribunal Constitucional`.

### 4: Consultar

Usar el script `consulta.py` (no `graphrag_console.py` que es legacy):

```bash
cd D:\\PyCode\\ResumenTokensJurisprudencias
python consulta.py "despido arbitrario segun el TC"
```

El system prompt en `consulta.py` ya incluye la instruccion de citar fuentes con el identificador del documento (EXP. N.°). Para que las citas aparezcan, el prompt **debe** incluir una regla explicita como:

```python
"REGLAS:\\n"
"2. Para cada afirmacion importante, CITA la fuente usando el identificador "
"del documento (ej: **EXP. N.° 00364-2022-AA/TC**).\\n"
```

Sin esa instruccion, el LLM cita usando nombres de partes en vez de identificadores de documento.

### 5: Verificar recuperacion de documentos TC

- `scripts/data_prep/preparar_batch_tc.py` — Batch preparation principal
- `scripts/data_prep/preparar_batch_2018_2023.py` — Batch para anos especificos
- `scripts/data_prep/enviar_batch_tc.py` — Upload + monitor + convert
- `scripts/data_prep/subir_batch_v2.py` — Upload simplificado
- `pipeline/indexer.py` — Indexer (sin cambios respecto al original)
- Ver `references/performance-data.md` para datos de rendimiento reales
