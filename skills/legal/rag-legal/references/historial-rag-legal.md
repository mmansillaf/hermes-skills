---
name: historial-rag-legal
description: Historial de desarrollo, pruebas y detalle técnico del sistema RAG Legal Local, KRagLocal, y PeruanoSearchEngine.
---

# Historial de Desarrollo - RAG Legal

## KRagLocal — Detalle Técnico

### Pruebas FTS5 y auto-detección de tipo
La búsqueda por keywords (FTS5) requiere un `INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')` después de insertar chunks en SQLite. Sin esto, la tabla externa FTS5 queda vacía y `search_keyword()` siempre retorna 0 resultados. La función `add_chunks()` ahora lo hace automáticamente en la misma conexión SQLite. El método `delete_document()` también fue corregido para eliminar metadatos del documento incluso cuando no hay chunks (antes el `if chunk_ids:` guard impedía el DELETE FROM documents).

### Tests automatizados (138 tests)
El proyecto ahora tiene 3 suites de test:
- `tests/test_vector_store.py` (47 tests) — CRUD documentos, chunks, búsqueda híbrida, categorías, pinned, settings, preferencias, historial, stats, edge cases
- `tests/test_ingest.py` (62 tests) — detección de tipo, chunking por estrategia, hash, parsing, process_document end-to-end con los 7 tipos de documento
- `tests/test_pipeline.py` (29 tests) — clasificación de intención, retrieval agent mockeado, validación de citas 2-stage (regex + LLM), orchestrator completo
Los tests se ejecutan con `python -m pytest tests/ -q`. El fixture `tmp_path` aísla la base de datos para no contaminar datos reales. Se corrigieron 3 bugs reales descubiertos por los tests.

### Cache LRU en API
El endpoint `POST /query` tiene cache LRU con TTL de 5 minutos. Implementado como dict global `_QUERY_CACHE` con limpieza de entradas stale cada vez que se consulta.

### Exportación de respuestas
- `POST /query/export` — descarga respuesta como TXT con metadatos
- `GET /export/history/{id}` — exporta entrada del historial como TXT

### Filtros de metadata en documentos
- `GET /documents?categoria=X` — filtra por categoría
- `GET /documents?query=contrato` — busca por nombre (LIKE)
- `GET /documents?pinned=true` — solo favoritos
- Los filtros son combinables.

### Templates separados de api.py
Antes: 4 constantes HTML embebidas (~1100 líneas). Ahora: `api.py` carga desde `templates/` vía `_load_template()`. archivos: index.html, settings.html, viewer.html, compare.html. api.py pasó de 1832 a 719 líneas.

### Extracción de tablas desde PDF
`_extract_tables(pdf_path)` usa camelot-py con doble flavor: lattice y stream. Cada tabla se convierte en chunk tipo "tabla". Filtra falsos positivos (tablas 1x1, vacías).

### Auditoría granular
Tabla `audit_log` en SQLite con 13 campos. Eventos: query, query_export, ingest, ingest_batch, document_delete, settings_llm.

### PDFs escaneados/sin texto (0 chunks)
PDFs identificados sin texto seleccionable:
- `contrato_prestamos_firmados.pdf`
- `23.2 TERMINOS DE REFERENCIA ALQUILER DE BUSES.pdf`
- `15_09_25-COT-N°211-CONTRATACION-DEL-SERVICIO-DE-ALQUILER-DE-MINIBUS-PARA-JUEGOS-DEPORTIVOS.pdf`

## Auto-detección de Tipo de Documento y Chunking

| Tipo detectado | Estrategia de chunk | Patrón de detección |
|---|---|---|
| contrato | Por cláusula | CLAUSULA + número ordinal/árabe |
| resolucion | Por considerando + RESUELVE | CONSIDERANDO, SE RESUELVE |
| sentencia | Por VISTOS / CONSIDERANDO / FALLA | VISTOS, FALLA, PARTE RESOLUTIVA |
| libro | Por capítulo + subsecciones | CAPITULO I, II..., INDICE |
| informe | Por secciones numeradas | Numeración romana/arábiga al inicio |
| norma | Por artículo + título | ARTICULO 1, TITULO I |
| generico | 512 tokens con overlap 100t | (ninguno de los anteriores) |

## Categorías Jerárquicas
El campo `categoria` soporta paths jerárquicos: `"Contratos/Prestamos"`, `"Resoluciones/Municipales"`.

## Settings UI
Página `/settings-page` con selector de proveedor LLM, API keys, modelo, temperature, estilo, max_tokens, top_k, formato citas. Todo persiste en `.env` + SQLite.

## Streaming SSE
Endpoint `/query/stream` con Server-Sent Events: metadata, token, sources, warning, error, done.

## Sidebar Ocultable
Botón ☰ toggle con animación CSS, Ctrl+B, persistencia en localStorage.

## Menú Consola Interactivo (TUI)
```
python krag.py                     # Menu interactivo 1-7
python krag.py ingest ./Contratos  # CLI directa
```

## Evaluación Multi-Agente
El sistema actual es un pipeline orquestado secuencial de 5 funciones, NO multi-agente real:
1. `classify_intent()` — clasifica intención
2. `retrieval_agent()` — busca chunks (ChromaDB + FTS5 + reranker)
3. `compare_agent()` / `contradictions_agent()` — análisis
4. `generate_response()` — genera respuesta final
5. `validation_agent()` — valida citas

## Antipiratería (Pendiente F5)
Estrategia de 4 capas: License file + RSA fingerprint, PyInstaller + Pylock, Cloudflare Worker, Trial mode. No implementado aún.

## Evaluación del RAG (20,973 docs, 10 preguntas, 7 Jun 2026)
Hallazgo: El RAG funciona pero recupera resoluciones de trámite, no sentencias de fondo. El corpus actual solo tiene LABORAL. Tiempo promedio: 0.5s por consulta.

## JSON Repair

### Para Local (Qwen 7B)
Qwen 7B produce ~13% de JSONs truncados. Reparador multi-nivel:
1. Detectar `Unterminated string` → eliminar línea del error, cerrar con `}`
2. Coma final → quitarla
3. Búsqueda iterativa de última `}` válida (hasta 5 intentos)
4. Verificar balance de `{}` antes de parsear

### Para Groq Batch
3 estrategias: bloques ```, regex JSON, recorte iterativo. Logra 100% de JSONs válidos con `max_tokens=1024`.

## Comparativa de modelos Groq (Junio 2026)
- **Llama 3.1 8B Instant** es el mejor balance: $51 para todo el corpus
- **Llama 4 Scout 17B** tiene más JSONs directos (97%) pero peor calidad de fallo
- **Llama 3.3 70B** es superior en calidad pero 11x más caro
- **Qwen3 32B** no funciona en Groq Batch
- **max_tokens=1024** es esencial para 100% de JSONs válidos

## Groq Batch API para Extracción Masiva

### Flujo completo
1. Preparar JSONL
2. Subir a Groq Files API
3. Crear batch job
4. Monitorear hasta completed
5. Descargar resultados
6. Convertir a formato indexer

### Límites
- Max 50,000 líneas por archivo JSONL
- Max 200MB por archivo
- ventana de procesamiento: 24h a 7d
- 50% descuento vs precio normal

### Costos reales medidos
| Batch | Docs | Costo | Tiempo |
|---|---|---|---|
| Prueba inicial | 100 | $0.009 | ~35s |
| Validación | 1,000 | $0.08 | ~5 min |
| Producción 1 | 2,000 | $0.18 | ~12 min |
| Producción 2 | 18,000 | $1.50 | ~133 min |
| Acumulado | ~21,000 | $1.76 | ~3 hr |

## Documentos Clasificados — Estructura del Corpus

### Fuentes de documentos (HDD USB)
| Fuente | Archivos |
|---|---|
| ResolucionesSAL/PDFs | 558,329 |
| Saleman/DescargaTotal | 374,570 |
| Descargas/SAL/Files | 73,968 |
| Saleman/FundadaSoles | 48,344 |
| Otras fuentes | 52,672 |
| **Total bruto** | **1,107,883** |
| **Duplicados** | **-301,283** |
| **Total únicos** | **806,600** |

### Documentos con valor jurídico
- Sentencia: 243,288
- Resolución: 192,116 (~40% con valor)
- Demanda: 16,117
- Total: ~451,521 con valor comprobado
- Estimado total: ~562,000 PDFs

### Documentos SIN valor jurídico
Notificaciones (55K), Oficios (22K), Actas (9K), Conciliaciones (8K), Pericias (8K), Citaciones (4K), Resoluciones de trámite (18K), No clasificados (100K+).

## Pipeline de Query (KRagLocal)
1. `classify_intent()` — clasifica intención
2. `retrieval_agent()` — hybrid search + reranker
3. Para COMPARE/CONTRADICTIONS: `_extract_doc_names_from_query()` antes del retrieval
4. `compare_agent()` o `contradictions_agent()`
5. `validation_agent()` — 2-stage (regex + LLM)

## Pruebas de UI (Mayo 2026)
La interfaz web fue probada end-to-end con 22 documentos reales (19 PDF + 4 TXT = 354 chunks) vía browser. Resultados: sidebar lista documentos, dropdown de filtro, queries QA/resumen/comparación/contradicciones con citas clickables, visualizador de chunks por documento.
