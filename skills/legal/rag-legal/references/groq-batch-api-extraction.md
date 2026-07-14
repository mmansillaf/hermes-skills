# Groq Batch API — Extracción Masiva de Documentos Legales

## Resumen

Pipeline para procesar documentos legales (PDF/DOC) usando Groq Batch API con Llama 3.1 8B Instant. Logra **99.9% de éxito** a **~135 docs/min** por **~$0.000084/doc** (50% descuento Batch).

## Flujo Completo

```
Preparar JSONL (25K docs ~175MB max)
  → Subir a Groq Files API (POST /v1/files, purpose=batch)
  → Crear batch job (POST /v1/batches, endpoint, completion_window=24h)
  → Monitorear (GET /v1/batches/{id}) hasta status=completed
  → Descargar resultados (GET /v1/files/{output_file_id}/content)
  → Convertir a formato indexer {id_documento, contenido_a_vectorizar, metadatos_graphrag}
  → Indexar en FAISS + BM25 + Grafo (pipeline/indexer.py --force)
```

## Scripts

- `batch_groq.py` — todo el pipeline (prepara, sube, monitorea, descarga, convierte)
- `extractor_qwen.py` — versión síncrona (--groq flag para usar Groq en vez de local)
- `monitor_batches.py` — verifica estado de batches en progreso, descarga e indexa cuando completan
- Todos en `/home/usuario/Escritorio/PyCode/KGraphResolucionesV3/`

## Modelo Recomendado

**Llama 3.1 8B Instant** (`llama-3.1-8b-instant`)
- 560 TPS, $0.05/$0.08 por 1M tokens
- 128K contexto, 131K max completion tokens
- **Production** (estable, no se depreca)

**max_tokens=1024** (obligatorio para 100% JSON válido)

## Límites Técnicos

| Recurso | Límite |
|---------|--------|
| Tamaño máximo archivo JSONL | **200 MB** |
| Líneas recomendadas | **~25,000** por archivo (con 30K chars/doc ≈ 175MB) |
| Ventana procesamiento | **24h** (mínimo aceptado por Batch API) |
| Descuento Batch | **50%** sobre precio normal |
| Tiempo efectivo típico | 1-4 hr (independiente de la ventana de 24h) |

## Tokenización Real

| Modelo | max_tokens | JSON válido | Tokens promedio | Token máximo |
|:------:|:----------:|:-----------:|:---------------:|:------------:|
| 8B | **512** | 89% | ~390 | ~550 |
| 8B | 640 | 99% | ~406 | ~580 |
| **8B** | **1024** | **100%** | **~406** | **~658** |

**Conclusión:** Con 512 tokens, 11% de JSONs se truncaban. Con 1024, **0%**. El costo es el mismo porque solo pagas los tokens reales (~406 promedio). El límite solo asegura que el modelo tenga espacio para completar.

## Costos Reales Medidos (Junio 2026)

### Batches Ejecutados

| Batch | Docs | Éxito | Costo Batch | Tiempo Groq | Ritmo |
|:-----:|:----:|:-----:|:-----------:|:-----------:|:-----:|
| Prueba | 100 | 100% | $0.009 | ~35s | 171 docs/min |
| Validación | 1,000 | 99.9% | $0.08 | ~5 min | 200 docs/min |
| **Producción 1** | **2,000** | **99.8%** | **$0.18** | **~12 min** | **166 docs/min** |
| **Producción 2** | **18,000** | **99.9%** | **$1.50** | **~133 min** | **135 docs/min** |
| **Acumulado** | **~21,000** | **99.9%** | **$1.76** | **~3 hr** | — |
| En progreso | 25,000 LAB | — | — | — | — |
| En progreso | 7,935 LAB+COM | — | — | — | — |

### Costo Unitario Real

$1.76 / 20,973 docs = **$0.000084/doc** en Batch API

### Proyecciones

| Documentos | Costo Batch | Tiempo efectivo |
|:----------:|:-----------:|:---------------:|
| 2,000 | $0.18 | ~12 min |
| 18,000 | $1.50 | ~2.2 hr |
| 55,800 (LAB restante) | $4.65 | ~7 hr |
| 77,876 (COMERCIAL) | $6.49 | ~10 hr |
| 136,586 (LAB+COM+FAM) | $11.38 | ~17 hr |
| 243,288 (Sentencias) | $20.27 | ~30 hr |
| 562,000 (Todo) | $46.83 | ~67 hr |

## Monitoreo Automático

Usar `cronjob` para monitorear batches largos:

```bash
hermes cron create \
  --schedule "30m" \
  --prompt "Ejecuta monitor_batches.py y verifica estado de los batches Groq.
Si ambos estan 'completed', descarga e indexa automaticamente." \
  --workdir /home/usuario/Escritorio/PyCode/KGraphResolucionesV3
```

O manualmente cada 2-3 min con `execute_code` (no usar `terminal()` con sleep largo porque el timeout max es 600s):

```python
from hermes_tools import terminal
r = terminal("curl -s ...", timeout=15)
```

## Problemas Conocidos

### Background processes (tcsetattr bash)
Cuando Hermes ejecuta `terminal(background=true)`, si el comando usa bash, `tcsetattr` falla con "no se puede establecer el grupo de proceso de terminal" y el proceso muere (exit 143/255). **Soluciones:**
1. Redirigir a archivo: `> /tmp/log 2>&1` en vez de pipe de Hermes
2. Usar `execute_code` con lotes pequeños (~5 docs) secuencialmente
3. Usar `batch_runner.py` que lanza subprocess desde Python (evita bash)
4. Para monitoreo: polling corto con `execute_code`

### Reparador JSON para Groq Batch
El reparador usa 3 estrategias en orden:
1. Extraer JSON de bloques ``` más grandes
2. Regex para encontrar el JSON más grande dentro del texto
3. Recorte iterativo desde la última `}` válida

### Clasificación por Materia
Los expedientes judiciales peruanos usan códigos en el nombre:
- `-LA-` → LABORAL
- `-CO-` → COMERCIAL  
- `-FT-` → FAMILIA (NO `-FA-`)
- `-CI-` → CIVIL
- `-CA-` → CONTENCIOSO ADMINISTRATIVO

## Comparativa Modelos Groq para Extracción

Resultados de 100 docs c/u con max_tokens=1024 (prueba del 7 Jun 2026):

| Modelo | JSON directo | JSON final | Fallo concreto | Costo Batch 562K |
|--------|:-----------:|:---------:|:--------------:|:----------------:|
| **Llama 3.1 8B** ✅ | 89% | **99%** (con 1024 tok) | **99%** | **$51** |
| Llama 4 Scout 17B | 97% | 97% | 87% | $117 |
| Llama 3.3 70B | 93% | 93% | 94% | $592 |
| Qwen3 32B | 0% | 0% | — | $158 |

**Qwen3 32B no funciona en Groq Batch** — su formato de respuesta es incompatible (0% JSON válido).

**Scout 17B** tiene más JSONs directos (97%) pero peor calidad de fallo (87% dice "No se proporciona" vs 99% del 8B).

**70B** es superior en calidad pero 11x más caro. Recomendado solo para respuestas RAG, no para extracción batch.
