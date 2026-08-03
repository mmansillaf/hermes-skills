# KGraphResolucionesV3

## Stack
- Python 3.11, Groq Batch API (Llama 3.1 8B), DeepSeek API
- FAISS + BM25 + NetworkX (GraphRAG híbrido)
- Pipeline: extractor (Groq Batch) → indexer (FAISS/BM25) → synthesizer (Llama 3.3 70B / DeepSeek) → critic

## Convenciones de código
- JSON estricto en toda extracción — validar schema antes de declarar éxito
- max_tokens=1024 OBLIGATORIO para Groq Batch API (512 produce ~11% truncados)
- type hints en todas las funciones nuevas
- Docstrings en español (usuarios finales son abogados peruanos)
- Separar resultados por materia (LABORAL, COMERCIAL, FAMILIA, CIVIL)

## Comandos clave
- `python indexer.py --force` — reindexar todo desde data_raw/
- `python batch_groq.py` — procesar lote Groq (prepara JSONL, sube, monitorea, descarga)
- `python graphrag_pro.py` — consulta interactiva (synthesizer + critic)
- `python evaluar_rag.py` — ejecutar evaluación con preguntas de prueba
- `python batch_runner.py N` — ejecutar pipeline de N docs

## Pipeline de indexación
1. PDFs fuente en data_raw/ (formato rag_listo_batch_*.json)
2. indexer.py → genera FAISS + BM25 + NetworkX en data/
3. graphrag_pro.py → consulta con router → strategist → synthesizer → critic

## Reglas de calidad
- Reportar tasa de éxito y costo en cada batch procesado
- Verificar 100% JSON válido antes de integrar un batch
- Si tasa de fallo >1%, investigar antes de continuar
- Documentos con 0 texto (PDFs escaneados) no son error del pipeline

## Proveedores
- Groq Batch: extracción masiva ($0.000084/doc con Llama 3.1 8B)
- DeepSeek: synthesizer y consultas (default)
- Groq síncrono: fallback para síntesis (Llama 3.3 70B)
- Gemini: fallback para tareas que requieren visión
