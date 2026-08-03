---
name: rag-legal
description: RAG local sobre documentos legales (Word/PDF). Busca en Qdrant + SQLite y genera respuestas con fuentes citadas usando DeepSeek/Groq.
category: legal
---

# RAG Legal Local

Sistema de Retrieval-Augmented Generation sobre carpeta de documentos legales (Word + PDF).

## Trigger

Cuando el usuario:
- Pregunta sobre normativa, leyes, sentencias, doctrina legal
- Busca términos jurídicos en su colección de documentos
- Necesita respuestas con fuentes citadas
- Quiere indexar nuevos documentos legales
- Menciona "El Peruano", "PeruanoSearchEngine", "pipeline", "procesar años"
- Trabaja con el pipeline batch multi-año (2020-2025)
- Quiere **comparar documentos**, buscar **contradicciones**, o hacer **análisis**
- Pregunta sobre **citación de fuentes** o validación de respuestas

## Sistemas Cubiertos

1. **rag-legal-local** — RAG sobre Word/PDF (sistema original)
2. **PeruanoSearchEngine02** — RAG sobre normas de El Peruano (~65K normas, pipeline 6 fases con Groq Batch API)
3. **KRagLocal** — RAG ligero embedded. ChromaDB + e5-small + SQLite FTS5 + pipeline multi-agente. FastAPI + HTML plano.

### KRagLocal — Regla crítica
Los documentos reales están en **`Contratos/`**, NO en `test_docs/`. Verificar que `Contratos/` exista antes de ingestar.

### Dependencias LLM
```
LLM_PROVIDER=groq   -> Groq API (llama-3.3-70b-versatile) [default]
LLM_PROVIDER=openai -> OpenAI API (gpt-4o-mini)
LLM_PROVIDER=gemini -> Google Gemini (gemini-2.0-flash)
LLM_PROVIDER=ollama -> Ollama local (llama3.2:3b)
```

### Archivos de inicio
- `start.sh` — para Linux/macOS
- `start.bat` — para Windows
- Ambos soportan: `serve` (default), `ingest`, `list`, `query`.

## Pipeline de Query (KRagLocal — multi-agente)

1. `classify_intent()` — clasifica intención (qa/resumen/comparar/contradicciones/analizar/listar)
2. `retrieval_agent()` — hybrid search (ChromaDB vector + FTS5 keyword) + cross-encoder reranker
3. `compare_agent()` o `contradictions_agent()` — análisis vía LLM
4. `validation_agent()` — verificación de citas 2-stage (regex rápido + LLM solo si hay dudas)
5. Respuesta con fuentes y métricas

## Pipeline de Query (RAG Legal Local)

1. Clasificar pregunta → tipo (semántica, keywords, temporal)
2. Buscar en SQLite FTS5 → términos legales exactos
3. Buscar en Qdrant → similitud semántica con bge-m3 embeddings
4. Merge + deduplicar → combinar resultados, ordenar por relevance
5. Confidence score → si < 0.75, sugerir web fallback
6. Generar respuesta → DeepSeek API (primario) o Groq API (fallback)
7. Citar fuentes → `[Fuente: archivo.docx, sección]`

## Pipeline Groq Batch API

**Modelo recomendado:** `llama-3.1-8b-instant` (560 TPS, $0.05/$0.08 por 1M tokens)

**Flujo:** preparar JSONL → subir a Groq Files API → crear batch job → monitorear → descargar → convertir a formato indexer

**Límites:** max 50,000 líneas por archivo, max 200MB, ventana 24h-7d, 50% descuento.

**Scripts:** `batch_groq.py` y `extractor_qwen.py` en `/home/usuario/Escritorio/PyCode/KGraphResolucionesV3/`

## Referencias

Para detalle técnico ampliado (tests, cache, exportación, streaming, UI, evaluaciones, costos, estructura del corpus):
- `references/historial-rag-legal.md`
- `references/ligero-embedded-rag.md` — estructura, comandos y pitfalls de Peruano
- `references/kraglocal-multiagent-pipeline.md` — pipeline multi-agente
- `references/multi-provider-llm-architecture.md` — integración multi-provider
- `references/groq-batch-api-extraction.md` — Groq Batch API detallado
- `references/kgraph-multiagent-pipeline.md` — pipeline multi-agente KGraphResolucionesV3

Para estrategias de chunking: `building-rag-systems-with-multiple-stores` → `references/document-ingestion-chunking-strategies.md`

## Comandos

```bash
# Consultar
python query_pipeline.py "¿cuál es el plazo de apelación?"

# Modo interactivo
python query_pipeline.py --interactive

# Interfaz web
streamlit run app.py

# KRagLocal
python krag.py                    # Menú interactivo
python krag.py ingest ./Contratos  # Ingestar carpeta
python krag.py serve               # Iniciar servidor web
python krag.py list                # Listar documentos
python krag.py delete <doc_id>     # Eliminar documento
python krag.py query "pregunta"    # Consulta desde terminal
```

## Requisitos

- Proyecto `rag-legal-local/` clonado e indexado
- API keys en `.env`: DEEPSEEK_API_KEY, GROQ_API_KEY
- Índices generados con `ingestion_pipeline.py`

## Código

Repositorio: https://github.com/mmansillaf/rag-legal-local

- `config.py` — configuración central
- `utils/extractor.py` — extrae texto de .docx/.pdf
- `utils/chunker.py` — divide por artículos legales
- `utils/embedder.py` — embeddings bge-m3
- `utils/indexer.py` — Qdrant + SQLite FTS5
- `utils/retriever.py` — búsqueda combinada
- `utils/generator.py` — DeepSeek + Groq
- `app.py` — interfaz web Streamlit

## Pitfalls

- **Critic alucinaciones de leyes:** El Critic original no detectaba leyes citadas textualmente. Verificar citas contra `context_doc_ids` recuperados.
- **max_tokens=1024 es esencial** para Groq Batch API (512 tokens → ~11% JSONs truncados). No afecta al costo.
- **Indexación inicial lenta:** 1-2h para 15k docs. Usar `--incremental` después.
- **API keys:** Sin DEEPSEEK_API_KEY solo busca, no genera respuestas.
- **PDFs escaneados:** No soportados sin OCR. Solo texto copiable.
- **Pipeline multi-año:** Todos los scripts tienen `clean_2024` hardcodeado. Para otro año se necesita wrapper independiente.
- **Multi-provider LLM:** Al cambiar de proveedor, instalar dependencias: `pip install openai google-generativeai`
- **Contratos/ folder:** Usar `krag ingest ./Contratos`, NO `test_docs/`.
- **Background processes en Hermes:** Scripts bash largos mueren con error `tcsetattr`. Redirigir a archivo `> /tmp/batch.log 2>&1` o usar `execute_code`.
- **Costos Groq Batch:** ~$0.000084/doc real (vs ~$0.00015 estimado). Datos actualizados en `references/groq-batch-api-extraction.md`.

## Convenciones de Reporte

1. **Formato TXT** (`reports/<nombre>.txt`)
2. **Formato MD** (`reports/<nombre>.md`)
3. **JSON con resultados crudos** (`reports/<nombre>.json`)

No truncar respuestas. Cada pregunta y respuesta deben aparecer completas.
