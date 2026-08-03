---
name: tc-searchrag
description: TC SearchRAG — buscador de jurisprudencia del Tribunal Constitucional peruano con Hybrid RAG (FAISS+BM25+RRF+Groq). 11,483 documentos indexados.
category: lex-rag
---

# TC SearchRAG — Hybrid RAG para Jurisprudencia del TC Peruano

## Descripción

Sistema de búsqueda y consulta en lenguaje natural sobre 11,483 sentencias del Tribunal Constitucional peruano (2005-2026). Usa Hybrid RAG (FAISS semántico + BM25 léxico + RRF fusion) con generación vía Groq llama-3.3-70b (refactorizado a Groq-only en Jun 2026, eliminado DeepSeek).

## Trigger

Usar este skill cuando el usuario pregunte por TC SearchRAG, búsqueda de jurisprudencia TC, consultas sobre el proyecto en D:\PyCode\TC_SearchRAG, o quiera saber cómo está implementado, refactorizado, o qué opciones de optimización tiene.

## Arquitectura

```
Router (Groq 8b, opcional) → Hybrid Retrieval (FAISS+BM25+RRF) → Filtros (materia/juez/año) → Generator (Groq llama-3.3-70b)
```

### Componentes clave

- **FAISS FlatL2**: 11,483 vectores, dim=512, modelo `distiluse-base-multilingual-cased-v2`
- **BM25 Okapi**: tokenización por palabras (sin stopwords)
- **Fusión RRF**: k=60, top_k=5-7 documentos
- **Filtros**: materia, juez, sala, año, tipo, departamento, cosa juzgada, fecha (YYYY-MM-DD), fecha-hasta
- **Generator**: Groq llama-3.3-70b (único proveedor, ~$0.0043/query)
- **Router**: Groq llama-3.1-8b (clasifica consulta como LEGAL/NO_LEGAL, ~$0.0001/query)
- **Sin chunking**: cada PDF completo = 1 embedding

### Modos de consulta

| Script | Descripción | Ejemplo |
|--------|-------------|---------|
| `search_tc.py` | Búsqueda con filtros, sin LLM | `python3 src/search_tc.py "" --materia Pensiones` |
| | | `python3 src/search_tc.py "" --fecha 2024-01-01 --fecha-hasta 2024-12-31` |
| | | `python3 src/search_tc.py "pension" --fecha 2025-01-01` |
| `ask_tc.py` | Consulta legal formal | `python3 src/ask_tc.py "requisitos pension"` |
| `narrar_tc.py` | Consulta conversacional | `python3 src/narrar_tc.py "por que me niegan mi pension?"` |
| `defiende_tc.py` | Consulta abogado experto, fuentes crono | `python3 src/defiende_tc.py "requisitos pension"` |
| `app.py` | API REST (FastAPI) | `GET /search?q=pension&materia=Pensiones` |

### Pipeline completo

```
Usuario → [Router Groq 8b opcional] → Embedding (distiluse) → FAISS search (top_k*3)
                                                              → BM25 search (top_k*3)
                                                              → RRF fusion (k=60)
                                                              → Filtros metadata
                                                              → Groq llama-3.3-70b
                                                              → Respuesta (formal o narrativa)
```

### Refactorización Jun 2026 — DRY + Groq-only + SearchArgs + cargar_textos

Cambios aplicados al código fuente en esta sesión:

- **Groq-only**: se eliminó DeepSeek como proveedor. `ask_tc.py` y `narrar_tc.py` usan solo Groq (router: llama-3.1-8b, síntesis: llama-3.3-70b). Ya no hay failover DeepSeek→Groq.
- **Sin duplicación de motor**: `ask_tc.py`, `narrar_tc.py`, `defiende_tc.py` y `app.py` importan `IndexManager`, `hybrid_search`, `SearchArgs` y `cargar_textos` de `search_tc.py`. El motor de búsqueda vive en UN solo archivo. Esto redujo ~200 líneas de código duplicado.
- **SearchArgs dataclass**: reemplazó el patrón `class Args: pass` + asignación manual de atributos. Es un `@dataclass` con todos los filtros tipados. Tiene `tiene_filtros()` para short-circuit y `desde_parser()` para construir desde argparse. El cache key ahora itera `fields(SearchArgs)` en vez de una lista hardcodeada — agregar un filtro nuevo actualiza el caché automáticamente.
- **cargar_textos()**: función compartida en `search_tc.py` que elimina la lógica duplicada de `_cargar_textos()` en ask_tc.py y `buscar()` en narrar_tc.py. Usa el singleton IndexManager y build de doc_map si es necesario.
- **Short-circuit en aplicar_filtros()**: si `SearchArgs.tiene_filtros()` es False, retorna `doc_ids[:]` sin iterar los 11,483 documentos. Ahorra ~0.5s en búsquedas sin filtros.
- **Carga incremental en IndexManager**: separó la carga en dos capas. Base (FAISS + metadata, 0.6s, 95 MB) y completa (BM25 + documents + embedder, ~22s, ~1.8 GB). `app.py` arranca en modo base (solo_filtros=True) y BM25/embedder se cargan bajo demanda en la primera búsqueda híbrida. Esto redujo el tiempo de arranque del servidor de 25s a 0.6s.
- **Prompts formales**: el prompt de `ask_tc.py` ahora exige estructura: (a) respuesta directa, (b) fundamentos jurídicos con citas EXP. N.°, (c) conclusión + preguntas de seguimiento. El prompt de `narrar_tc.py` mantiene tono explicativo pero profesional, sin exceso de coloquialismo.
- **Código comentado**: cada sección del motor y scripts tiene docstrings, comentarios de sección y explicaciones de por qué.
- **Carga unificada de documentos**: `documents.pkl` y `doc_map` ahora se cargan dentro del `IndexManager` singleton en `search_tc.py`, no dispersos en cada script LLM.

### Local deployment (PC usuario final, 16GB RAM)

El sistema puede ejecutarse completamente local sin APIs externas usando Ollama:

| Componente | Alternativa local | RAM | Tokens/s |
|-----------|-------------------|:---:|:--------:|
| LLM | Qwen3 8B (Q4_K_M) via Ollama | ~6 GB | 15-25 |
| LLM (mejor) | Qwen3 14B (Q4_K_M) via Ollama | ~10 GB | 5-10 |
| LLM (rápido) | Llama 3.1 8B (Q4_K_M) via Ollama | ~6 GB | 15-25 |
| Embeddings | all-MiniLM-L6-v2 (local) | ~1 GB | — |
| FAISS+BM25+metadata | Existentes (local) | ~3 GB | — |
| Total con Qwen3 8B | — | ~10 GB | ✅ Cabe en 16GB |

### Estructura del proyecto (post-refactor)

```
D:\PyCode\TC_SearchRAG\
├── sdd/              → Specs SDD (CONSTITUTION + 4 specs + PLAN)
├── src/
│   ├── index_tc.py   → Indexador multi-fuente con metadata híbrida
│   ├── search_tc.py  → Motor central: IndexManager + hybrid_search + filtros
│   ├── ask_tc.py     → Consulta legal formal (importa de search_tc)
│   ├── narrar_tc.py  → Consulta conversacional (importa de search_tc)
│   ├── defiende_tc.py  → Consulta con abogado experto (SPEC-006, importa de search_tc y ask_tc)
│   ├── app.py        → API REST FastAPI (importa de search_tc y ask_tc)
│   └── auditar.py    → Generador de reportes
├── data/             → Índices FAISS+BM25+metadata (sin git)
├── files/            → 1,511 PDFs TC 2005 (originales)
└── .env              → GROQ_API_KEY (única key necesaria)
```

**Regla:** para modificar la lógica de búsqueda, editar solo `search_tc.py`. Los otros scripts son wrappers delgados.

### Fuentes de datos

1. **TC 2005**: 1,501 PDFs escaneados (OCR imperfecto) en `files/`
2. **TC SEDETC**: 9,982 PDFs digitales (2024-2026) de `D:\PyCode\TC_SEDETC_Scraper\pdfs\`
3. **Total**: 11,483 documentos indexados (~25M palabras)

### API breaking changes (refactor Jun 2026)

**`hybrid_search()` ahora retorna 2 valores, no 3.**
Antes: `results, context_texts, doc_ids = hybrid_search(query)`
Ahora: `results, audit = hybrid_search(query)` — el audit contiene metadatos de la búsqueda (tiempo, candidatos, filtrados). Los textos completos se obtienen del singleton `IndexManager().documents[index]` vía `doc_map[archivo]`.

Si un script externo o legado usa el formato antiguo (3 valores), fallará con `ValueError: not enough values to unpack (expected 3, got 2)`. La corrección es:
```python
results, audit = hybrid_search(query)
context_texts = _cargar_textos(results)  # función helper que lee de IndexManager
```

**`app.py` — `uvicorn.run` corregido.**
Antes: `uvicorn.run("src.app:app", host="0.0.0.0", port=8000)` → falla con `ModuleNotFoundError: No module named 'src'` cuando se ejecuta desde cualquier directorio que no sea la raíz del proyecto.
Ahora: `uvicorn.run(app, host="0.0.0.0", port=8000)` — pasa el objeto `app` directamente, no un string con ruta de importación. Esto evita problemas de `sys.path`.
Para arrancar el servidor: `python3 src/app.py` (funciona desde cualquier directorio).

**`.env` ahora solo requiere `GROQ_API_KEY`.**
Se eliminó la dependencia de `DEEPSEEK_API_KEY`. El archivo `.env` mínimo es:
```
GROQ_API_KEY=***
HF_TOKEN=***  # opcional, acelera descargas de HuggingFace
```

### Costos (Groq-only, Jun 2026)

| Componente | Costo/consulta | Notas |
|-----------|:--------------:|-------|
| Búsqueda (search_tc.py) | **$0** | Todo local, sin API |
| Router (Groq llama-3.1-8b) | ~$0.0001 | Clasifica la consulta |
| Síntesis (Groq llama-3.3-70b) | ~$0.0043 | Genera respuesta estructurada |
| **Total consulta con IA** | **~$0.0044** | Router + síntesis |
| Indexación | **$0** | CPU local, sin APIs |
| Uso mensual 100 q/día | **~$13.20** | Solo Groq |

### Rendimiento medido (Jun 2026 — carga incremental + lazy)

Carga en dos niveles:

| Nivel | Componentes | Tiempo | RAM | Cuándo se carga |
|------|------------|:------:|:---:|----------------|
| **Base** | FAISS + metadata | **0.5-0.6s** | **95 MB** | Startup de app.py o primera búsqueda filtro |
| **Completa** | BM25 + documents + embedder | **~22s adicional** | **+1.8 GB** | Primera búsqueda híbrida |

Desglose de la carga completa (medido en proceso aislado con 3 GB RAM total):

| Componente | Tiempo | RAM adicional | Archivo |
|-----------|:------:|:------------:|:-------:|
| FAISS | 0.3s | 62 MB | 23 MB .bin |
| Metadata | 0.3s | +30 MB | 7.9 MB .jsonl |
| BM25 pickle | 7.2s | +1,700 MB | 265 MB .pkl |
| Documents | 1.6s | +291 MB | 162 MB .pkl |
| Embedder | 15.0s | +799 MB | distiluse-multilingual |
| **Total full** | **24.5s** | **2,882 MB** | |

Benchmark de búsqueda (post-carga):

| Tipo | Tiempo | Candidatos |
|-----|:------:|:----------:|
| Solo filtros (`"" --fecha ...`) | **0.3 ms** | 11,481 |
| Query corta ("pension ONP") | **564 ms** | 100 |
| Query media ("habeas corpus") | **57 ms** | 100 |
| Query larga ("enfermedad profesional ...") | **77 ms** | 100 |
| Caché (2da vez misma consulta) | **0 ms** | — |

Nota: el benchmark completo vive en `src/benchmark.py` en el repo.

### Mantenimiento: agregar documentos

| Comando | Cuándo usarlo |
|---------|---------------|
| `python3 src/index_tc.py --append` | Agregar PDFs nuevos (usa checksums MD5, no duplica) |
| `python3 src/index_tc.py --force` | Re-indexar todo (cambio de modelo, reglas, o índices corruptos) |
| `python3 src/index_tc.py --dry-run` | Verificar qué pasaría sin modificar nada |

**Para agregar una nueva fuente:** editar FUENTES en `index_tc.py`:
```python
FUENTES = [
    {"path": "files", "nombre": "TC 2005"},
    {"path": "D:\\nueva\\ruta", "nombre": "Nueva fuente"},
]
```
Los checksums MD5 evitan duplicados incluso si el mismo PDF está en carpetas distintas.

### Prompt engineering para legal RAG

**ask_tc.py** — consulta formal. El system prompt exige:
- (a) Respuesta directa: concisa, responde sí/no/qué.
- (b) Fundamentos jurídicos: cada documento citado con EXP. N.° y nombre de archivo.
- (c) Conclusión: síntesis de hallazgos y limitaciones.
- Preguntas de seguimiento: 2-3 sugeridas al final.
- Modelo: llama-3.3-70b, temperature 0.1, max_tokens 2000.

**narrar_tc.py** — consulta explicativa. El system prompt pide:
- Respuesta directa inicial.
- Explicación con casos concretos (EXP. N.°).
- Condiciones y dependencias si aplica.
- Consejo práctico final.
- Tono profesional pero accesible, no coloquial.
- Modelo: llama-3.3-70b, temperature 0.2, max_tokens 1500.

**defiende_tc.py** (SPEC-006, Jun 2026) — consulta con abogado experto. Tono entre formal y pedagógico: seguro, humano, autoridad. El prompt pide:
- Respuesta fluida sin títulos de sección, como abogado conversando.
- Fuentes ordenadas cronológicamente (más antigua → más reciente) para mostrar evolución jurisprudencial.
- Citas exactas (EXP. N.°) cada vez que se menciona un caso.
- Si hay contradicción, el fallo más reciente prevalece.
- Cierre con aplicabilidad práctica ("En tu caso concreto...").
- Modelo: llama-3.3-70b, temperature 0.3, max_tokens 2000.
- Los resultados se re-ordenan por `fecha` ASC antes de armar el contexto. Docs sin fecha van al final.

**Router (ask_tc.py)** — clasifica LEGAL/NO_LEGAL:
- Modelo: llama-3.1-8b-instant, temperature 0.0, max_tokens 10.
- Fallback seguro: si el router falla, asume LEGAL.

### Lecciones aprendidas

- **No chunking necesario**: con documentos <5,000 palabras, el embedding del documento completo es mejor que chunking.
- **Sin grafo**: documentos del TC son independientes entre sí. GraphRAG no aporta valor para este corpus de ~11K docs.
- **Sin critic agent**: con documentos completos en contexto, el LLM no alucina citas. Añadir critic solo añade latencia y costo.
- **Batch embeddings**: sentence-transformers.encode() en lotes de 50 es ~50x más rápido que uno por uno.
- **Un solo proveedor LLM simplifica**: eliminar DeepSeek redujo código duplicado (failover), evitó confusiones de API keys, y quitó dependencias. El usuario prefirió tener un único proveedor en vez de failover automático.
- **Importar vs duplicar**: compartir IndexManager desde search_tc.py vía import redujo ~200 líneas de código duplicado. Los cambios en la búsqueda se reflejan automáticamente en todos los scripts.
- **Siempre verificar contra los PDFs reales, no solo el código de extracción**: el código de `extraer_fecha()` en `index_tc.py` usa una regex que solo captura un formato de fecha (el de Pleno: "a los X días del mes de Y de ZZZZ"). El formato real y más común en Autos/Resoluciones/Interlocutorias es otro ("Lima, X de mes de YYYY"). La lección: cuando investigues cómo se extrae metadata, no confíes solo en la regex del código — extráela de documentos reales y compara.
- **Metadatos: no todos los campos filtrables están realmente poblados**: `--departamento` solo tiene 2 de 11,483 documentos. `--fecha` subió de 8,953 a 10,918 tras backfill con regex mejorada (Jun 2026). `--juez` solo en 2,170. `--materia` y `--tipo` son los filtros más fiables (100% poblados).
- **Backfill de metadata sin re-indexar**: cuando un campo de metadata se extrae mejorablemente (como `fecha`), se puede parchear `metadata.jsonl` directamente escaneando `documents.pkl` (los textos ya extraídos). No requiere re-correr FAISS/BM25 ni re-leer PDFs. El script de backfill es un one-off que se borra tras usar. En Jun 2026 la cobertura de fecha subió de 78% (8,953 docs) → 95.7% (10,992 docs) tras dos pasadas de backfill: primera con el patrón "Lima, 5 de marzo de 2019" (+1,965 docs), segunda con el patrón "Lima, al 1 de julio de 2025" (+74 docs). Quedan 491 docs (4.3%) sin fecha (OCR fallido).

### Pitfalls (concretos, verificados en sesión)

- **Groq API 403 desde WSL**: Python's default User-Agent (urllib `Python-urllib/3.x`) is blocked by Cloudflare's WAF on api.groq.com → HTTP 403 error code 1010, even for valid keys. Workaround: use the `groq` Python library which sets proper headers, or set `User-Agent: Mozilla/5.0...` explicitly when using raw urllib/requests. The `groq` library handles this correctly.
- **Modelos Groq se descontinúan**: `mixtral-8x7b-32768` fue descontinuado (Jun 2026). Actualmente disponibles: `llama-3.1-8b-instant`, `llama-3.3-70b-versatile`, `qwen/qwen3-32b`, `meta-llama/llama-4-scout-17b-16e-instruct`. Verificar con `GET https://api.groq.com/openai/v1/models`.
- **Groq 70b varía MUCHO en tiempo de respuesta**: desde 2.4s hasta 74s dependiendo del contexto y la cola de Groq. No es un problema de código.
- **uvicorn.run("src.app:app") falla**: `ModuleNotFoundError: No module named 'src'`...
- **Primera consulta lenta (~15-40s)**: sentence-transformers descarga/calienta el modelo la primera vez. Usar el servidor web (`app.py`) mantiene el modelo cargado en memoria entre consultas.
- **`python` vs `python3`**: en WSL Ubuntu el binario es `python3`, no `python`. Usar `python3` siempre.
- **Filtros parciales en docs pre-2024**: PDFs de 2005 escaneados con OCR de baja calidad. Metadata (juez, sala, fecha) incompleta. Los filtros por materia son más fiables porque se basan en el texto completo.
- **`extraer_fecha()` historial**: originalmente solo buscaba `"a los X días del mes de Y de ZZZZ"` (formato de sentencias de Pleno). No capturaba el formato estándar `"Lima, 5 de marzo de 2019"`. Esto dejaba ~2,530 documentos sin fecha. En Jun 2026 se agregó un segundo patrón: `r"Lima,\s*(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})"`. Después de backfill, cobertura subió de 78% → 95.7%. Aún quedan ~491 docs (4.3%) con formatos atípicos. También se agregó soporte para "Lima, al 1 de julio de 2025" (a+el=al) con patrón: `r"Lima,?\s*(?:a\s+)?(?:los\s+)?(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})"`.
- **Emojis rompen en Windows cmd.exe/PowerShell**: los scripts usan emojis que el terminal Windows (cp1252) no soporta. Error: `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4da'`. Soluciones: `$env:PYTHONIOENCODING="utf-8"` (PowerShell) o `python.exe -X utf8 src/search_tc.py "pension"`.
- **BM25 almacenado como dict**: `bm25_index.pkl` contiene `{'bm25': BM25Okapi, 'meta': list[dict]}`, no un objeto BM25 suelto. Acceder como `bd['bm25'].get_scores(tokens)` y `bd['meta'][idx]['archivo']`.
- **GROQ_API_KEY puede expirar**: retorna error 401 `expired_api_key` o `invalid_api_key`. La búsqueda (`search_tc.py`) sigue funcionando sin API. Renovar en https://console.groq.com/keys.
- **No editar ask_tc.py o narrar_tc.py para cambios de búsqueda**: el motor compartido vive en `search_tc.py`. Cambios de retrieval van ahí.
- **Servidor app.py no se inicia desde src/**: `cd /mnt/d/PyCode/TC_SearchRAG && python3 src/app.py` falla porque uvicorn.run("src.app:app") hace el import desde src/. Solución: corregir el app.py a `uvicorn.run(app, ...)` (sin string path), o arrancar como módulo `python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000` desde la raíz del proyecto.

### Optimizaciones recomendadas (priorizadas por impacto/esfuerzo)

Basado en benchmarks reales de Jun 2026:

| Prioridad | Optimización | Ahorro | Esfuerzo |
|:---------:|-------------|:------:|:--------:|
| **P0** | Servidor persistente `app.py` | ~11s por consulta | ✅ Ya existe |
| **P1** | Caché exacto (hash MD5 query+filtros) | ~13-32s por consulta repetida | ~30 líneas |
| **P2** | Skip BM25 si query vacía (solo filtros) | ~9s por consulta de filtros | ~10 líneas |
| **P3** | Wrapper CLI (alias/bat) | UX, no tiempo | ~5 min |
| **P4** | BM25 serialization (gzip/SQLite) | ~6-8s en carga | Medio |
| **P5** | Modelo embeddings más rápido | ~2-3s primer arranque | Re-indexar |

Detalles: ver `references/optimization-plan.md`.

## Reference files

- `references/project-packaging.md` — Clean ZIP for Windows (zipfile not PowerShell), .gitignore for AI projects, README template, GitHub push bypass (token truncation fix via .env).
- `references/demo-session.md` — End-to-end demo with real timings, commands, and outputs for all 4 query modes plus REST API.
- `references/local-llm-legal-comparison.md` — Model comparison for local deployment on 16GB RAM PCs.
- `references/windows-setup.md` — Windows venv creation, encoding fix (emoji crash), and verified PowerShell commands.
- `references/optimization-plan.md` — Benchmark-driven optimization plan (P0-P5): server mode, caching, BM25 skip, CLI wrapper, BM25 serialization, faster embeddings.
- `references/benchmarks.md` — Raw benchmark data: indexing times, search latency, battery results, cost analysis.
- `references/groq-models-verified.md` — Verified Groq model list (Jun 2026), API quirks, decommissioned models, and cost reference.
- `references/metadata-population.md` — Real population stats for every metadata field (11,483 docs verified). Which filters actually work vs which look good but are empty. Date format discrepancies found in source PDFs.
