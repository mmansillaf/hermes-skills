---
name: pipeline-status
description: Estado actual del pipeline RAG de normas El Peruano — metricas, snapshots, configuracion de BD y API.
---

# Pipeline Status — El Peruano RAG

## Base de Datos
- **DB unificada**: `normas_total.db` (97,812 normas, 2021-2025)
- **Path**: `/home/usuario/el_peruano_rag/PeruanoSearchEngine02/data/normas_total.db`
- **Tamaño**: 1,055 MB
- **FTS5**: 97,812 rows (3 normas ingestadas 06-may: RS 040/042 SUSALUD, RS 009-MC)
- **Índices**: idx_normas_id, idx_normas_numero, idx_normas_fecha, idx_normas_tipo

## Vector Store (Qdrant)
- **Colección**: `normas_peruano_total` — 97,809 puntos, dimensión 384, métrica Cosine

## Graph (Neo4j)
- **Nodos**: 97,809 Norma + 16,077 Entidad = 113,886 total
- **Relaciones**: 336,041 MENCIONA
- Graph traversal activo en tipos B, D, E (antes solo F, G)

## API — api_rest.py (1699 lineas, +256 desde 1443 post-refactor)

### Modulos extraidos (8)
```
src/core/
├── confidence.py          (288) — confidence_score + 7 helpers
├── scoring.py             (38)  — _dedup_and_blend
├── cache.py               (37)  — _get_cached, _set_cache
├── metadata_extractor.py  (103) — extract_structured_metadata
├── router.py              (151) — route_response (4 niveles, ahora async)
├── graph_traversal.py     (67)  — expand_graph (Neo4j 2-degree)
└── query_classifier.py    (667) — existente, sin cambios
src/web/
└── fallback.py            (163) — search_web_fallback + Tavily
src/utils/
└── token_tracker.py       (183) — tracker + GET /token-stats
src/validation/
└── response_validator.py  (367) — validacion post-LLM + auto-correccion
```

### Mejoras activas (ultima actualizacion: 06-may-2026)
- System prompt anti-derrotista (10 frases prohibidas)
- **Prompt grounding estricto (NUEVO)**: solo citar leyes en NORMAS ENCONTRADAS
- Floor confianza 0.60 (antes 0.75)
- Boost confianza post-LLM 3-factores
- Filtro temporal año+mes en FTS5
- Graph traversal tipos B, D, E, F, G
- Serper + Tavily web fallback
- Forced number override
- **Response validator con auto-correccion (NUEVO)**: detecta y elimina normas alucinadas
- Router 4 niveles: BASICO (8B), INTERMEDIO/AVANZADO_ANALISIS/AVANZADO_CREACION
- Streaming SSE con _model_for_level() corregido
- **generate_answer async (NUEVO)**: asyncio.to_thread + wait_for 50s, no bloquea event loop
- **max_tokens aumentado (NUEVO)**: 1500 BASICO / 3000 INTERMEDIO+ (antes 800/1200)
- **Query validation (NUEVO)**: min_length=3, max_length=1000 en QueryRequest
- **Q&A logging (NUEVO)**: historial_consultas.txt + .jsonl
- **KAG Patterns Fases A/B/C**: mutual indexing, schema extraction, planning operator
- **Interfaz web (NUEVO)**: static/index.html, dark mode, historial localStorage
- Serper + Tavily web fallback
- Forced number override
- Response validator (F2)
- Router 4 niveles: BÁSICO (8B), INTERMEDIO, AVANZADO_ANALISIS (disclaimer), AVANZADO_CREACION (borrador)
- Streaming SSE con _model_for_level() corregido

### Endpoints
- `GET /health` — estado SQLite + Qdrant + Neo4j
- `POST /query` — búsqueda principal
- `GET /normas/{id}` — detalle + entidades Neo4j
- `GET /search?q=` — búsqueda simple
- `GET /stats` — estadísticas
- `GET /token-stats?granularity=diario|mensual|total` — tokens + costos Groq

### Deprecados (Fase 5 / D1-D4)
- `scripts_legacy/orchestrator_rag_v3.py` + `v4.py` — deprecados, CLI migrado a API REST
- `scripts_legacy/ingestion_legacy/` — código Windows legacy
- `scripts_legacy/cli_archived/` — 2 CLIs redundantes

## Backups
- `backups/api_rest_v4.1_pre_refactor_fase1_20260505.py` (2209 líneas, snapshot inicial)
- `backups/src_backup_20260505/` (35 archivos Python)
- `backups/api_rest_v4.1_20260505.sha256` (checksum)
- Rollback: `cp backups/api_rest_v4.1_pre_refactor_fase1_20260505.py api_rest.py`

## Reportes (06-may-2026)
- `reports/arquitectura_completa_sistema_20260506.txt` — diagrama 10 capas del pipeline
- `reports/limites_caracteres_sistema_20260506.txt` — auditoria de truncamientos
- `reports/bateria_100q_completa_20260506_v2.txt` — 100 preguntas con respuestas completas
- `reports/reverse_v2_reporte.txt` — reverse validation 30/30 OK
- `reports/reverse_validation_reporte.txt` — reverse validation v1 42/50 OK
- `reports/test_20q_remoto_vm.txt` — test 20 preguntas contra VM

## Reportes (05-may-2026)
- `reports/refactor_analysis_20260505.md` + `.txt` (20.9 KB)
- `reports/simulacion_comparativa_v3_20260505.txt` (v3 vs api_rest)
- `reports/prueba_final_20260505.txt` (10/10 PASS)
- `reports/test_battery_20260505.txt` (12/12 PASS)
- `reports/test_fase3_20260505.txt` (8/8 PASS)
- `reports/estado_pre_refactor_20260505.txt`

## Refactorización (05-may-2026) — Fases 1-5 + D1

- **api_rest.py**: 2209 → 1443 líneas (-35%)
- **8 módulos extraídos**: confidence.py (288), scoring.py (38), cache.py (37), metadata_extractor.py (103), fallback.py (163), router.py (151), graph_traversal.py (67), token_tracker.py (183)
- **6 bugs corregidos**: type annotation confidence_score, hack dir(), variables sin init, modelo hardcodeado en streaming, contexto divergente, generate_answer/stream duplicados
- **Deprecados**: orchestrators v3/v4 → scripts_legacy/, ingestion legacy → scripts_legacy/, 2 CLIs redundantes archivados
- **Nuevos**: deploy/ scripts MVP, test_usuario.py, hermes_token_tracker.py, token tracker en /token-stats
- **Tests**: 46/46 PASS acumulados (10+12+8+8+4+4)
- **Tests finales**: 10/10 OK (1 PARCIAL en IA, esperable)
- **Costo Groq tests**: $0.23 USD acumulado
- **Deploy**: scripts MVP en deploy/ (deploy.sh, install.sh, start.sh, test.sh) para VPS auto-contenido sin Cloudflare ni GitHub Pages

## Pendientes
- ⬜ Reindexar Qdrant con IDs de norma reales
- ⬜ Mejorar entidades Neo4j con NER real (~$10 Groq)
- ⬜ Seguridad API (rate limiting, JWT, CORS)
- ⬜ Desplegar en Contabo VPS produccion ($5.50/mes)

## Realizado (06-may-2026)
- ✅ Push a GitHub: commit eb50dbc (10 files, +5555 lines)
- ✅ VM staging 192.168.18.217 desplegada y corriendo
- ✅ 3 normas faltantes ingestadas (RS 040/042 SUSALUD, RS 009-MC BNP)
- ✅ Disco VM liberado: 99% → 84% (clean .venv CUDA, snap packages)
- ✅ Permisos Docker arreglados en VM
- ✅ Interfaz web static/index.html desplegada en VM
- ✅ Reverse validation v2: 30/30 OK (100%)
- ✅ Bateria 100q re-ejecutada: 0 timeouts, 4.8 min

## Deployment
- Ver skill `elperuano-deployment-options` para plan completo
- Fase 0: VM Ubuntu local (staging) — ver `references/vm-staging-deploy.md`
- Fase 1-3: GitHub Pages + Actions + Contabo VPS

## Hermes Agent Config (05-may-2026)
- Cache semántico: threshold 0.96, TTL 1h, strategy semantic
- 8 API keys en .env (DeepSeek, Kimi, Google, Groq, OpenRouter, NVIDIA, Tavily, ScrapeGraphAI)
- Fallback chain: Kimi→Google→Groq (cross-provider)
- Auxiliares 9/9 en google_ai_studio/gemini-2.5-flash
- max_context_tokens: 48000