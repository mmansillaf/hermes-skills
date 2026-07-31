---
name: tc-sedetc-scraper
category: scraping
description: Scraper for Peru's TC (Tribunal Constitucional) jurisprudence at jurisprudencia.sedetc.gob.pe. API REST sin auth, sin captchas. Descarga masiva vía API + PDFs en paralelo con checkpoint reanudable.
triggers:
  - "tribunal constitucional scraper"
  - "sedetc tc jurisprudencia"
  - "tc jurisprudencia descarga"
  - "jurisbackend.sedetc.gob.pe"
---

# TC SEDETC Scraper — Tribunal Constitucional del Perú

## Descripción General

Scraper para el portal de jurisprudencia sistematizada del TC Peruano en
`jurisprudencia.sedetc.gob.pe`. A diferencia del CEJ (Poder Judicial), este
sistema NO tiene captchas, WAF ni bloqueo — es una API REST pública.

## API

| Item | Valor |
|------|-------|
| URL | `https://jurisbackend.sedetc.gob.pe/api/visitor/sentencia/busqueda?page=N` |
| Header | `User-Agent: Mozilla/5.0 ...` REQUERIDO (sin UA retorna default) |
| Rate limit | 60 req/min |
| Items/page | 10 (fijo, parámetro `size` ignorado) |
| Páginas | 1-1000 (página 1001+ da HTTP 500) |
| Total | 10,000 items (cap) |
| Response | JSON Elasticsearch: `data[]._source.{url_archivo, numero_expediente, ...}` |
| Auth | Ninguna |

## PDFs

| Item | Valor |
|------|-------|
| URL | `https://tc.gob.pe/jurisprudencia/{año}/{expediente}.pdf` |
| Redirección | `tc.gob.pe` → `www.tc.gob.pe` (seguir redirects) |
| Rate limit | Sin límite detectable |
| Tamaño | 200 KB - 1.3 MB por PDF |
| Verificación | Cabecera `%PDF-` |

## Uso del Scraper

```bash
cd D:\PyCode\TC_SEDETC_Scrader
python tc_scraper.py --max 1000 --workers 24
python tc_scraper.py --max 10000 --workers 24 --resume  # reanudar
python tc_scraper.py --metadata-only  # solo obtener metadatos
python tc_scraper.py --download-only  # solo descargar (requiere metadata.csv)
```

## Catálogo Completo (Jun 2026)

| Año | PDFs | Rango |
|-----|------|-------|
| 2026 | ~426 | Ene-Mar 2026 |
| 2025 | ~4,945 | Ene-Dic 2025 |
| 2024 | ~4,394 | Ene-Dic 2024 |
| 2023 | ~234 | Nov-Dic 2023 |
| **Total** | **9,997 únicos** | **Nov 2023 → Mar 2026** |

No hay datos publicados antes de noviembre 2023 en este sistema.

## Tipos de Resolución

Los tipos se extraen del expediente: AA (Amparo), HC (Hábeas Corpus),
AC (Cumplimiento), HD (Hábeas Data), AI (Inconstitucionalidad),
CC (Conflicto Competencial), Q (Queja). Muchos tienen sub-variantes
como AA (Aclaración), AA (Admisión en el PJ), etc.

## Limitaciones conocidas

### No hay datos anteriores a Nov 2023

El sistema SEDETC se lanzó en noviembre 2023. Solo indexa desde esa fecha.
No hay jurisprudencia publicada antes de esa fecha en esta API.

### Fuente alternativa: Consulta de Causas

El TC tiene un sistema más antiguo en `tc.gob.pe/consultas-de-causas/` que
SÍ contiene casos históricos (al menos desde 2020). Sin embargo:

- Es **WordPress + jQuery DataTables** con server-side processing via AJAX
- No tiene API REST pública — requiere interactuar con formularios JS
- La búsqueda por año requiere POST/JS, no GET con parámetros
- Para scrapearlo se necesitaría **Selenium/undetected_chromedriver**

Además, los PDFs individuales de años anteriores SÍ existen en
`tc.gob.pe/jurisprudencia/{año}/{expediente}.pdf` (verificado: 2010, 2023),
pero no hay un índice — hay que descubrir los nombres de archivo mediante
el sistema Consulta de Causas.

Ver `references/consulta-de-causas-exploration.md` para más detalles.

## Post-Scraping: Ingesta en Pipeline RAG

Los PDFs descargados por este scraper pueden procesarse en un pipeline RAG
(LexRAG, GraphRAG, TC SearchRAG) para búsqueda semántica + generación de
respuestas. Ver `references/post-scraping-ingestion-evaluation.md` para la
metodología completa de evaluación y adaptación.
Ver `references/groq-batch-ingestion-workflow.md` para el pipeline
completo de ejecución: extracción PDF → JSONLs → Groq Batch API →
conversión → indexador (FAISS + BM25 + Grafo).

### Resumen rápido de compatibilidad

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Extracción de texto | ✅ PyMuPDF | ~98% PDFs tienen texto real extraíble |
| Metadata para RAG | ✅ Disponible en CSV | expediente, tipo, demandante, demandado, sala |
| Costo de procesar 11K docs | ~$10 USD | Groq Batch API (vs $31 de los originales 64K HTMLs) |
| Cambios necesarios vs pipeline HTML | 4 cambios localizados | Extracción (PDF→texto), limpieza, prompt TC, CSV→JSON |
| Índices (FAISS/BM25/Grafo) | ✅ Sin cambios | Mismo formato JSON de entrada |

### Secuencia recomendada (ejecución real verificada Jun 2026)

Ver `references/groq-batch-ingestion-workflow.md` para detalles
completos de cada paso. Resumen rápido:  

```bash
# 1. Descargar PDFs (ya hecho)
python tc_scraper.py --max 10000 --workers 24

# 2. Preparar batches para Groq
python scripts/data_prep/preparar_batch_tc.py --max 5000

# 3. Subir a Groq Batch y esperar resultados
python scripts/data_prep/enviar_batch_tc.py

# 4. Indexar (lee automáticamente rag_listo_batch_tc_*.json)
cd /mnt/d/PyCode/ResumenTokensJurisprudencias
PYTHONPATH=. python pipeline/indexer.py
```

## Pitfalls

1. **User-Agent obligatorio** — Sin `User-Agent: Mozilla/5.0` la API retorna
   datos default ignorando parámetros como `search` y `page`.
2. **sentencia_distrito puede ser null** — Algunos items (como Pleno)
   no tienen distrito judicial asignado. Usar `(src.get("sentencia_distrito") or {}).get("nombre", "")`.
   NO usar `src.get("sentencia_distrito", {}).get(...)` porque cuando la clave
   existe con valor null, `get(key, {})` retorna `None`, no `{}`.
3. **Expedientes con texto extra** — Algunos expedientes incluyen texto
   como `02203-2023-AA (Amicus Curiae)`. El PDF usa solo el número.
   Usar siempre `url_archivo` del API, no construir URL manualmente.
4. **Connection pool insuficiente** — Con `ThreadPoolExecutor(24)` y
   `requests.Session()`, el pool default (10 connections) se satura:
   ```
   Connection pool is full, discarding connection: www.tc.gob.pe
   ```
   **Fix**: crear el adapter con pool size igual a workers:
   ```python
   adapter = requests.adapters.HTTPAdapter(pool_connections=24, pool_maxsize=24)
   session.mount('https://', adapter)
   ```
5. **Checkpoint phase "download_done" bloquea reanudación** — Si el checkpoint
   tiene `phase: download_done` y se ejecuta `--resume` para añadir más items,
   la fase de descarga se salta completamente. **Fix**: borrar checkpoint y
   empezar fresh (los PDFs existentes se skipean por "ya existe").
6. **Duplicados en API** — ~3 expedientes aparecen duplicados (mismo
   número, distinto API ID). El scraper los sobrescribe.
7. **Página 1001+** — HTTP 500 error de Laravel (log permissions).\n   El catálogo termina en página 1000.\n8. **Duplicados de custom_id en JSONL batch** — Si al generar JSONLs para Groq\n   un mismo nombre de archivo PDF aparece dos veces (mismo expediente en dos\n   directorios-año distintos), el batch falla con `duplicate_custom_id`.\n   **Fix**: verificar unicidad antes de escribir: añadir sufijo `_v2` a duplicados.\n9. **Filtrado por año específico** — `preparar_batch_tc.py` escanea años en orden\n   descendente (2026 → 2025 → ...). Para procesar solo años antiguos (2018-2023),\n   no usar `--max` porque incluirá años recientes primero. Crear script separado\n   filtrando `YEARS = ['2018','2019',...]` explícitamente.
