# Groq Batch API — Extracción de Documentos Legales

## Resumen

Pipeline para extraer datos estructurados (hechos, problema, fallo, entidades)
de documentos legales PDF usando Groq Batch API con Llama 3.1 8B Instant.
Los resultados se indexan en FAISS + BM25 + NetworkX para búsqueda RAG.

## Modelo Recomendado

**Llama 3.1 8B Instant** (`llama-3.1-8b-instant`)

| Métrica | Valor |
|---------|-------|
| Velocidad | 560 TPS |
| Costo input | $0.05/1M tokens |
| Costo output | $0.08/1M tokens |
| Contexto | 128K tokens |
| Batch API | 50% descuento |

## Comparativa de Modelos (100 docs c/u, Batch API)

| Modelo | JSON dir. | JSON final | Con leyes | Fallo concr. | Costo Batch/100 | Costo 562K Batch |
|--------|:---------:|:----------:|:---------:|:------------:|:---------------:|:----------------:|
| **Llama 3.1 8B Instant** | **89%** | **99%** | 87% | **99%** | **$0.009** | **~$55** |
| Llama 4 Scout 17B | 97% | 97% | 86% | 87% | $0.021 | ~$120 |
| Llama 3.3 70B | 93% | 93% | 85% | 94% | $0.105 | ~$600 |
| Qwen3 32B | **0%** | **0%** | N/A | N/A | $0.028 | N/A |

Qwen3 32B falló completamente (0% JSON válido) — su formato de respuesta en Groq Batch no es compatible.

## Optimizaciones Clave

### max_tokens=1024

El parámetro más crítico para tasa de éxito:

| max_tokens | JSON válido | Tokens promedio | Token máximo | Fallos |
|:----------:|:-----------:|:---------------:|:------------:|:------:|
| 512 | 89% | ~390 | ~550 | 11/100 |
| 640 | 99% | ~406 | ~580 | 1/100 |
| **1024** | **100%** | **406** | **658** | **0/100** |

El token máximo real observado es 658. Con 1024 hay espacio de sobra.
Costo no aumenta porque solo se pagan tokens reales (~406 promedio).

### Límite de contenido: 30K chars

El truncado a 7K chars perdía 24-82% del contenido del PDF.
Con 30K chars:
- 89% de documentos entran completos
- 11% se truncan pero conservan el inicio (hechos + primeros fundamentos)

Distribución real (muestra de 156 sentencias LABORAL):
- 7K: solo 55% completos
- 15K: 75% completos  
- 30K: 89% completos
- Máximo observado: 181,927 chars (~180 páginas)

### Texto del PDF: pdftotext -layout

Usar pdftotext con flag `-layout` para preservar estructura de párrafos.
El texto plano es suficiente para extracción LLM — no se necesita OCR.

## Formato JSONL para Batch API

Cada línea debe tener esta estructura:

```json
{
  "custom_id": "doc_0001",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": {
    "model": "llama-3.1-8b-instant",
    "messages": [
      {"role": "system", "content": "Eres un asistente legal experto..."},
      {"role": "user", "content": "Analiza esta resolucion..."}
    ],
    "temperature": 0.1,
    "max_tokens": 1024
  }
}
```

### Límites del archivo JSONL
- **50,000 líneas** máximo por archivo
- **200 MB** máximo por archivo
- Si cada request pesa ~7KB: 25K lineas ≈ 175MB (seguro)
- Múltiples batches pueden enviarse en paralelo

## Flujo de Trabajo

```
1. Preparar JSONL (extraer texto de PDFs, generar requests)
2. Subir a Files API (POST /v1/files)
3. Crear batch job (POST /v1/batches, completion_window: "24h")
4. Monitorear estado (GET /v1/batches/{id}) cada 30-60s
5. Cuando status = "completed", descargar resultados
6. Parsear JSONs de respuesta, reparar si es necesario
7. Indexar en FAISS + BM25 + Grafo
```

## Prompt de Extracción

### System Prompt
```
Eres un asistente legal experto en indexacion de jurisprudencia peruana.
Analiza la resolucion judicial proporcionada y extrae la informacion 
en formato JSON. Debes devolver UNICAMENTE un objeto JSON valido, 
sin texto adicional.
```

### User Prompt (template)
```
Analiza esta resolucion judicial y genera un JSON con la siguiente 
estructura exacta:
{schema_json}

REGLAS:
- Extrae los hechos del CASO (lo que paso), no los fundamentos legales
- El problema es la CUESTION JURIDICA CENTRAL a resolver
- El fallo es la DECISION FINAL del tribunal (parte resolutiva)
- Si una entidad no existe en el texto, usa arreglo vacio []
- Normaliza nombres: quita tratamientos (Dr., Sr., etc.)
- Responde SOLO con el JSON, sin explicaciones ni bloques de codigo

TEXTO DE LA RESOLUCION:
{texto}
```

### Schema de Salida
```json
{
  "resumen_hechos": "Sintesis objetiva de los hechos relevantes",
  "resumen_problema": "Problema juridico central a resolver",
  "resumen_fallo": "Decision final del tribunal",
  "entidades_clave": {
    "jueces_magistrados": ["Nombre del juez"],
    "demandantes_accionantes": ["Nombre de quien demanda"],
    "demandados_accionados": ["Nombre del demandado"],
    "leyes_y_articulos_citados": ["Ley X, Art. Y"],
    "conceptos_legales_clave": ["Concepto juridico"]
  }
}
```

## JSON Repair (3 estrategias)

Para respuestas truncadas por límite de tokens:

1. **Extraer de bloques ```**: buscar el bloque más grande entre ``` y ```
2. **Regex de JSON plano**: buscar `{[^{}]*}` ordenados por tamaño, validar que contengan `resumen_fallo`
3. **Recorte desde último }**: recortar desde el último `}` válido hacia atrás, hasta 20 intentos

## Costos Proyectados

| Documentos | Costo normal | **Costo Batch (-50%)** | Archivos JSONL |
|:----------:|:-----------:|:---------------------:|:--------------:|
| 2,000 | $0.37 | **$0.18** | 1 |
| 10,000 | $1.83 | **$0.91** | 1 |
| 50,000 | $9.13 | **$4.56** | 1 |
| 100,000 | $18.25 | **$9.13** | 1 |
| 243,288 (Sentencias) | $44.41 | **$22.20** | 1 |
| 562,000 (todo) | $102.58 | **$51.29** | 1 |

## Estimaciones de Tiempo (Batch API)

- **Ventana configurada:** 24h (mínimo)
- **Tiempo típico:** 2-15 minutos (depende de carga de Groq)
- **Peor caso:** hasta 24h
- **Throughput observado:** ~2,000 docs en ~12 minutos

## Chunking Semántico para Documentos Legales

Tres estrategias implementadas:

1. **Multi-chunk con overlap** (recomendado para indexación completa)
   - Divide por párrafos
   - Overlap de ~500 chars entre chunks consecutivos
   - El fallo siempre cae en el último chunk

2. **Priorizar fallo** (una pasada rápida)
   - Toma últimos párrafos (fallo) + inicio del documento
   - Pierde fundamentos medios
   - Útil cuando solo se necesita el fallo

3. **Sub-chunking** (para párrafos muy largos)
   - Divide párrafos que exceden el límite por saltos de línea
