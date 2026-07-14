# Resultados de Prueba — 6 Junio 2026

## Hardware
- ThinkPad P53 | i7-9850H (6C/12T) | Quadro T1000 4GB | 46GB RAM
- HDD USB como almacenamiento de origen (cuello de botella)

## Qwen 2.5 7B Q4_K_M (modelo recomendado)

### Configuración
- n_gpu_layers: 20 (NO 24 — OOM)
- n_threads: 12
- contexto: 8192
- batch: 512
- mlock: sí
- max_tokens: 512 (en prompt de extracción)

### Resultados multi-formato (4 muestras)

| # | Archivo | Formato | Tiempo | Tok/s | JSON | Contenido |
|---|---------|---------|--------|-------|------|-----------|
| 1 | `01_res_costos_procesales.pdf` | PDF | 37.3s | 11.1 | ✅ | Costos procesales laboral |
| 2 | `02_res_incautacion.pdf` | PDF | 41.2s | 11.1 | ✅ | Garantía mobiliaria |
| 3 | `Modelo-de-contrato-1.docx` | DOCX | 22.8s | 11.0 | ✅ | Contrato (no judicial) |
| 4 | `res_1996_archivo.doc` | DOC | 25.7s | 9.2 | ✅ | Devolución archivo |

**Promedio: 32s por doc | 10.7 tok/s | 100% JSON válido**

### Warmup
- Consulta #1 (cold start): 18.2s, 3.5 tok/s
- Consultas #2-3 (warm): 4.9s, 12.7-12.8 tok/s

## Gemma 4 E2B Q4_K_M (NO recomendado para Quadro T1000)

### Configuración
- n_gpu_layers: 12 (solo 12/~30 caben en 4GB)
- contexto: 4096 (mitad que Qwen)
- reasoning: off (--reasoning off)

### Resultados
- Promedio: 48.1s por doc (51% más lento que Qwen 7B)
- Tok/s: 9.9
- JSON: 4/4 (100%)
- OOM con -ngl ≥ 20

## Archivos generados esta sesión

En /home/usuario/Escritorio/PyCode/KGraphResolucionesV3/:
- `extractor_qwen.py` — extractor que genera JSONs compatibles con indexer.py
- `data_raw/rag_listo_batch_qwen_*.json` — checkpoints de extracción
- `output/resultados_batch.csv` — resultados en CSV
- `reports/comparativa_final_qwen_vs_gemma4.md`
- `reports/arquitectura_pipeline.html`
- `backup_pre_cambios.tar.gz` — backup de pipeline/indexer.py, core/*, retrieval/*, utils/*

En /home/usuario/Escritorio/PyCode/QwenLegalExtractor/:
- `test_multiformat.py` — prueba multi-formato
- `test_gemma4.py` — prueba específica Gemma 4
- `chunking_demo.py` — 3 estrategias de chunking semántico
- `output/resultados_prueba_completa.json` — resultados Qwen 7B
- `output/resultados_gemma4.json` — resultados Gemma 4
- `modelos_gemma4/gemma-4-E2B-it-Q4_K_M.gguf` — modelo descargado (2.9 GB)
