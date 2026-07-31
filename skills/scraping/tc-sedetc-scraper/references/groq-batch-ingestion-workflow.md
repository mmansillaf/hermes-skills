# Groq Batch Ingestion Workflow — TC PDFs → LexRAG

## Visión General

Pipeline completo para procesar PDFs del TC SEDETC a través de Groq Batch API
e incorporarlos a un sistema LexRAG (FAISS + BM25 + NetworkX).

```mermaid
flowchart LR
    A[PDFs] --> B[PyMuPDF extract]
    B --> C[JSONL batch]
    C --> D[Groq Files API]
    D --> E[Groq Batch API]
    E --> F[Descargar resultados]
    F --> G[Convertir a formato indexer]
    G --> H[pipeline/indexer.py]
    H --> I[FAISS + BM25 + Grafo]
```

## Fase 1: Extracción de PDFs → JSONL

### Dependencias
- `pymupdf` (PyMuPDF) — extracción de texto
- `tqdm` — progress bars
- La función `estimate_tokens(words_count)` aproxima 1 palabra ≈ 1.33 tokens

### Limpieza de artefactos específicos de PDFs TC

```python
def clean_pdf_text(text: str) -> str:
    text = re.sub(r'[1I]\s*[1I]\s*[1I][1I\sI]+', '', text)  # barras formato
    text = re.sub(r'[■●►▪□○◇※★]+', '', text)                # caracteres especiales
    text = re.sub(r'[_\-=]{5,}', '', text)                    # líneas separadoras
    text = re.sub(r' {3,}', ' ', text)                        # espacios múltiples
    text = re.sub(r'\n{3,}', '\n\n', text)                    # saltos múltiples
    text = re.sub(r'\n\d{1,2}\n(?=[A-ZÁÉÍÓÚ])', '\n', text)  # números de página
    return text.strip()
```

### Prompt de extracción LLM — adaptado para TC

El prompt debe:
- Mencionar "Tribunal Constitucional del Perú" explícitamente
- Incluir tipos de proceso: AA (Amparo), HC (Hábeas Corpus), AC (Cumplimiento), HD (Hábeas Data), AI (Inconstitucionalidad), CC (Conflicto Competencial)
- Solicitar detección de voto singular / voto discrepante
- Usar terminología técnica peruana (no genérica)

### Clasificación por modelo

| Condición | Modelo | Costo |
|-----------|--------|-------|
| ≤ 1000 tokens estimados | `llama-3.1-8b-instant` | ~$0.00009/doc |
| > 1000 tokens estimados | `llama-3.3-70b-versatile` | ~$0.0011/doc |

Para PDFs TC, ~90% son "largos" (>1000 tokens) porque el contenido es denso.

## Fase 2: Groq Batch API

### 2.1 Subir archivos JSONL

```python
from groq import Groq
client = Groq(api_key=GROQ_API_KEY)

with open("batch_file.jsonl", "rb") as f:
    response = client.files.create(
        file=f,
        purpose="batch"
    )
file_id = response.id  # ej: "file_01kv7940wbe6ev58emk9jn4dyt"
```

**Nota:** El parámetro `purpose="batch"` es obligatorio. Archivos de hasta ~70MB
se suben en 15-20s.

### 2.2 Crear Batch Job

```python
batch = client.batches.create(
    input_file_id=file_id,
    endpoint="/v1/chat/completions",
    completion_window="24h"  # Groq usa 24h fijo
)
batch_id = batch.id  # ej: "batch_01kv794eqbeaq8k7dkze5dnr6g"
```

**Estados del batch:** `validating` → `in_progress` → `completed`/`failed`/`cancelled`

### 2.3 Monitorear progreso

```python
b = client.batches.retrieve(batch_id)
req = b.request_counts
print(f"{b.status} | {req.completed}/{req.total} completados, {req.failed} fallidos")
```

**Comportamiento típico observado:**
- **8B (pequeño):** Empieza a procesar casi inmediatamente. 255 docs en ~10 min
- **70B (grande):** Puede estar `in_progress` en 0/4500 por 30-60 min (en cola).
  Una vez que arranca, procesa ~300-400 docs cada 5 min
- **Las colas son independientes:** Un batch 8B puede completarse antes de que
  un 70B empiece a procesar

### 2.4 Descargar resultados

```python
content = client.files.content(b.output_file_id)
text_content = content.text()  # OJO: .text es un CALLABLE, no una property
lines = [l for l in text_content.strip().split('\n') if l.strip()]
results = [json.loads(l) for l in lines]
```

**Estructura de cada resultado:**
```json
{
  "custom_id": "tc_00004-2025-AI.pdf",
  "response": {
    "status_code": 200,
    "body": {
      "choices": [{
        "message": {
          "content": "{\"resumen_hechos\": \"...\", \"resumen_problema\": \"...\", ...}"
        }
      }]
    }
  }
}
```

### 2.5 Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `expired_api_key` | Key de Groq vencida | Generar nueva en console.groq.com |
| `invalid_api_key` | Key mal formada | Verificar que la key empiece con `gsk_` |
| Rate limit (429) | Muchas requests simultáneas | Usar Batch API (es asíncrono) |
| HTTP 500 en file upload | Formato JSONL inválido | Validar cada línea con `json.loads()` |
| `duplicate_custom_id` en 8B | Dos requests en el mismo JSONL con igual `custom_id` | Verificar unicidad: `len(set(ids)) == len(ids)`. Si hay duplicados, añadir sufijo `_v2`, `_v3` |
| Key expirada mid-sesión | `expired_api_key` (~30-60 días de vida) | Rotar key en console.groq.com y actualizar `.env` |
| Output no visible en background | `print()` buferizado cuando stdout no es TTY | Usar `PYTHONUNBUFFERED=1` o `sys.stdout.flush()` |
| Error `'function' object has no attribute 'strip'` | `content.text` es un callable, no una property | Usar `content.text()` en lugar de `content.text` |

## Fase 3: Conversión a Formato Indexer

El indexer (`pipeline/indexer.py`) espera archivos `rag_listo_batch_*.json` con
esta estructura:

```python
doc = {
    "id_documento": "tc_00004-2025-AI.pdf",    # custom_id del batch
    "ruta_local": "/TC_SEDETC/pdfs/2026/00004-2025-AI.pdf",
    "contenido_a_vectorizar": {
        "hechos": "...",    # de resumen_hechos del LLM
        "problema": "...",  # de resumen_problema
        "fallo": "..."      # de resumen_fallo
    },
    "metadatos_graphrag": {
        "jueces_magistrados": [...],
        "demandantes_accionantes": [...],
        "demandados_accionados": [...],
        "leyes_y_articulos_citados": [...],
        "conceptos_legales_clave": [...]
    }
}
```

### Parseo del JSON devuelto por el LLM

El LLM a veces envuelve el JSON en bloques markdown ` ```json ... ``` `.
Estrategia de extracción:

```python
content_clean = content.strip()
if content_clean.startswith("```"):
    lines = content_clean.split('\n')
    json_lines = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            json_lines.append(line)
    content_clean = '\n'.join(json_lines)

# Fallback: extraer con regex
import re
json_match = re.search(r'\{.*\}', content_clean, re.DOTALL)
if json_match:
    parsed = json.loads(json_match.group(0))
```

### Batch size y naming

El indexer usa `glob.glob("data_raw/rag_listo_batch_*.json")`, así que
nombrando los archivos como `rag_listo_batch_tc_*.json` se integran
automáticamente. Recomendado:

- **Batch size:** 1000 docs por archivo (manejable, checkpoint cada 1000)
- **Naming:** `rag_listo_batch_tc_{timestamp}_pt{n}.json`
- **Output:** `data_raw/` (mismo directorio que los originales)

## Fase 4: Indexación

```bash
cd /ruta/del/proyecto/lexrag
PYTHONPATH=. python pipeline/indexer.py
```

### Comportamiento del indexer con datos existentes

- **Es resumible:** Carga índices existentes, detecta `doc_ids` ya procesados
- **Skip rápido:** Los documentos ya existentes se saltan en ~0s (dict lookup)
- **Embeddings nuevos:** Los nuevos documentos se embeddan en lotes de 64,
  a ~10-11 docs/s con SentenceTransformers en CPU
- **Grafo:** Documentos, jueces, leyes, demandantes y demandados se agregan
  como nuevos nodos con aristas

### Verificación post-indexación

```python
from core.index_manager import index_manager
index_manager.initialize(base_dir='.')
stats = index_manager.stats()
print(f"FAISS: {stats['faiss_vectors']} vect")
print(f"Grafo: {stats['graph_nodes']} nodos, {stats['graph_edges']} aristas")
```

## Costos Reales (5,000 PDFs — Jun 2026)

| Item | Docs | Costo |
|------|------|-------|
| 8B (cortos ≤1000 tok) | 255 | ~$0.03 |
| 70B (largos >1000 tok) | 4,745 | ~$8.87 |
| **Total 5,000 docs** | **5,000** | **~$8.90 USD** |
| **Total 11,224 docs** | **~11,224** | **~$20 USD** |

## Tiempos Reales (5,000 PDFs)

| Fase | Tiempo |
|------|--------|
| Extracción PDF → JSONL (8 workers) | ~17 min |
| Groq 8B batch | ~10 min |
| Groq 70B batch (en cola + proceso) | ~1h 47min |
| Conversión resultados | ~1s |
| Indexador (embeddings + FAISS + grafo) | ~9 min |
| **Total** | **~2h 46min** |

## Verificación con Consultas

Una vez indexados, hacer consultas con términos que deberían encontrar
documentos TC (ej: "amparo contra resoluciones judiciales").
Los documentos TC aparecen como `tc_XXXX-YYYY-AA.pdf` en el contexto.

## Archivos Clave del Pipeline

| Archivo | Propósito |
|---------|-----------|
| `scripts/data_prep/preparar_batch_tc.py` | Extrae PDFs, genera JSONLs |
| `scripts/data_prep/enviar_batch_tc.py` | Sube a Groq, espera, convierte |
| `pipeline/indexer.py` | Construye FAISS + BM25 + Grafo |
| `data_raw/batches_tc/` | JSONLs temporales y resultados crudos |
| `data_raw/rag_listo_batch_tc_*.json` | Datos listos para indexar |
