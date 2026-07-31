# Post-Scraping: Evaluación de Ingesta en Pipeline RAG

## Contexto

Los PDFs descargados por `tc_scraper.py` (en `pdfs/<año>/`) pueden integrarse
en un pipeline RAG existente (LexRAG / GraphRAG / TC SearchRAG). Este documento
describe cómo evaluar la compatibilidad y qué cambios se necesitan.

## Metodología de Evaluación (6 pasos)

Usar este checklist cada vez que se evalúe un corpus nuevo para ingesta en un
pipeline RAG existente:

### Paso 1: Examinar formato de archivo fuente

¿En qué formato están los documentos originales?

| Pregunta | Qué revisar |
|----------|-------------|
| ¿Son HTML, PDF, DOCX, TXT? | `file` command o PyMuPDF |
| ¿Están en una estructura plana o por carpetas? | `ls`, `find`, distribución por año |
| ¿Hay naming consistente? | Patrón en nombres de archivo |
| ¿Cuántos archivos y peso total? | `wc -l`, `du -sh` |

### Paso 2: Evaluar calidad de extracción de texto

¿Se puede extraer texto limpio y útil?

| Prueba | Métrica | Umbral |
|--------|---------|--------|
| Texto real vs escaneado | chars < 100 por PDF | < 5% escaneados es aceptable |
| Contenido sustancial | chars por documento | Media > 2000 chars |
| Artefacts de extracción | Barras "111111...", basura OCR | Documentar qué limpieza se necesita |

**Herramientas:**
```python
import pymupdf, glob
for p in glob.glob("pdfs/2024/*.pdf"):
    doc = pymupdf.open(p)
    chars = sum(len(page.get_text()) for page in doc)
    pages = len(doc)
    print(f"{p}: {chars} chars, {pages} págs, {'SCAN' if chars < 100 else 'texto'}")
    doc.close()
```

### Paso 3: Verificar metadata disponible

¿Qué metadatos ya existen y qué necesita extraerse vía LLM?

| Metadata | HTML original | PDFs TC | Fuente |
|----------|---------------|---------|--------|
| ID documento | filename numérico | Expediente + tipo (ej. `00004-2025-AI`) | Nombre de archivo |
| Órgano | Regex sobre HTML | Tribunal Constitucional (fijo) | Hardcodeable |
| Fecha | Regex sobre HTML | En `data/metadata.csv` | CSV existente |
| Tipo | Regex sobre HTML | AA/HC/AC/HD/Q + subvariante | CSV existente |
| Demandante/Demandado | LLM en batch | En `data/metadata.csv` | CSV existente |
| Hechos/Problema/Fallo | LLM en batch | LLM en batch (igual) | Groq Batch API |
| Jueces/Leyes citadas | LLM en batch | LLM en batch (igual) | Groq Batch API |

**Conclusión:** si el metadata existe en CSV, el pipeline NO necesita el paso
de extracción por regex sobre HTML — se puede convertir directamente.

### Paso 4: Mapear diferencias contra el pipeline existente

Para cada módulo del pipeline, determinar:

| Módulo | ¿Cambia? | Qué cambiar |
|--------|----------|-------------|
| Extracción de texto | SÍ | HTML → PDF (BeautifulSoup → PyMuPDF) |
| Limpieza de texto | SÍ | PDF requiere limpiar artefacts (barras, números repetidos) |
| Prompt de extracción LLM | SÍ* | Ajustar para tipo de tribunal (TC vs. genérico) |
| Preparación de batches | SÍ | Nuevo script o modificar existente |
| Indexación (FAISS/BM25/Grafo) | NO | Mismo formato JSON de entrada |
| Metadata docs | NO** | Convertir CSV existente en vez de ejecutar extracción regex |

\* El prompt debe mencionar "Tribunal Constitucional", "magistrados del TC",
"voto singular", etc. en vez de términos genéricos.
\** Si el CSV tiene los campos necesarios, se convierte con un script simple.

### Paso 5: Proyectar costos

| Concepto | Fórmula | Ejemplo (11K PDFs) |
|----------|---------|---------------------|
| Docs largos (>1000 tokens) | ~80% × N × $0.0011 | ~$9.90 |
| Docs cortos (<1000 tokens) | ~20% × N × $0.00009 | ~$0.18 |
| **Total estimado** | | **~$10 USD** |

La estimación de tokens se hace con `estimate_tokens()` que aproxima
1 palabra ≈ 1.33 tokens. Los PDFs del TC tienen promedio 13K-31K chars
(~2K-5K palabras), así que casi todos califican como "largos".

### Paso 6: Identificar casos borde

Detectar antes de iniciar:

- **PDFs escaneados**: ~1-2% sin texto extraíble → omitir o aplicar OCR
- **Documentos muy cortos**: Razones de Relatoría (~100 palabras) → valen la pena?
- **Duplicados**: ~3 expedientes duplicados con distinto API ID → el indexer los detecta por doc_id
- **Años anteriores**: Rezagados 1996-2017, PDFs pueden ser de menor calidad

## Cambios típicos al adaptar un pipeline HTML → PDF

### 1. Extracción de texto para PDF

Reemplazar:
```python
from bs4 import BeautifulSoup
text = BeautifulSoup(html, 'html.parser').get_text()
```

Por:
```python
import pymupdf
doc = pymupdf.open(pdf_path)
text = "\n".join(page.get_text() for page in doc)
doc.close()
# Limpieza de artefacts de PDF
import re
text = re.sub(r'[■●►▪]+\s*', '', text)
text = re.sub(r'\d{10,}', '', text)  # números repetitivos
text = re.sub(r'(111+)', '', text)   # barras de formato
```

### 2. Conversión de metadata CSV a formato del pipeline

```python
import csv, json

# metadata.csv → metadata_docs.json
mapping = {}
with open("data/metadata.csv", newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        filename = f"{row['expediente']}.pdf"
        mapping[filename] = {
            "identificador": f"EXP. N° {row['expediente']}/TC",
            "organo": "Tribunal Constitucional",
            "fecha": row.get("fecha_publicacion", ""),
            "tipo": f"Sentencia TC - {row.get('tipo', '')}",
            "materia": "",
            "demandante": row.get("demandante", ""),
            "demandado": row.get("demandado", ""),
        }
```

### 3. Prompt de extracción LLM adaptado al TC

El prompt del batch debe referirse a "Sentencia del Tribunal Constitucional"
en vez de "providencia judicial genérica". Agregar instrucciones para detectar:

- **Voto singular / voto discrepante** (los magistrados del TC suelen emitirlos)
- **Precedentes vinculantes** (el TC usa "precedente vinculante" explícitamente)
- **Control difuso** vs. **control concentrado** (distinción típica del TC)
- **Tipos de proceso**: AA (Amparo), HC (Hábeas Corpus), AC (Cumplimiento), HD (Hábeas Data), AI (Inconstitucionalidad), CC (Conflicto Competencial)

## Factibilidad general

| Factor | Evaluación |
|--------|------------|
| % del pipeline reutilizable | ~90% |
| Dificultad de cambios | Baja (cambios localizados en 2-3 módulos) |
| Riesgo de calidad de texto | Bajo (98% de PDFs tienen texto real extraíble) |
| Costo | ~$10 USD en Groq Batch API |
| Tiempo de desarrollo | 2-3 horas |

## Referencias

- `tc_scraper.py` — Scraper original que descarga los PDFs
- `preparar_batch_graphrag.py` — Script de preparación de batches (modificar para PDFs)
- `pipeline/indexer.py` — Indexador que consume los resultados (sin cambios)
