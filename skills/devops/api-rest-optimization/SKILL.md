---
name: api-rest-optimization
description: Fixes y optimizaciones aplicados a api_rest.py del RAG El Peruano. Documenta graph traversal, system prompt, floor confianza, timeout async, anti-hallucination, max_tokens, question validation, Q&A logging, y arquitectura del sistema.
---

# API REST Optimization — El Peruano RAG

## Fixes aplicados (02-may-2026)

### 1. Graph Traversal habilitado
**Archivo:** `src/core/query_classifier.py` + `api_rest.py:1540`

Habilitado `use_graph_traversal: True` en estrategias B (Semántica), D (Emisor+Acción), E (Acrónimo).
Antes solo funcionaba en F y G (~5% queries). Ahora ~70%.

**Bugs corregidos:**
- `seen_ids` no inicializado → `seen_ids = set()`
- `top_ids` no definido si `unique_results` vacío → `top_ids = []`
- Indentación rota en `neo = get_neo4j()`

### 2. System Prompt anti-derrotista
**Archivos:** `api_rest.py:1357-1363`, `src/orchestrators/orchestrator_rag_v3.py:816`

Reemplazado "Si no hay normas relevantes, dilo honestamente" por:
- Lista explícita de 10 frases PROHIBIDAS
- Fórmulas constructivas: "Según los datos disponibles..."
- max_tokens: 600→800, 1000→1200

### 3. Floor de confianza 0.75 → 0.60
**Archivo:** `api_rest.py:607`

```python
# Antes
if has_real_overlap and weighted < 0.75:
    weighted = 0.75
# Ahora
if has_real_overlap and weighted < 0.60:
    weighted = 0.60
```

Reduce falsos positivos en queries adversariales. Trade-off: baja algunas queries legítimas que dependían del floor anterior.

### 4. Filtro temporal año+mes
**Archivo:** `api_rest.py:814-830`

Detecta año (`\b20\d{2}\b`) y mes (español) en la query. Agrega `AND fecha_publicacion LIKE 'YYYY-MM%'` a consultas FTS5.

Ej: "normas de setiembre 2024" → filtra solo septiembre 2024 (no todo el año).

### 5. Boost de confianza post-LLM (3 factores)
**Archivo:** `api_rest.py:1873-1919`

```python
# Factor 1: Entidades (+0.08 c/u, max +0.30)
# Factor 2: Calidad de respuesta (+0.10 a +0.25)
# Factor 3: Penalización por negación (-0.15 a -0.40)
confidence = max(0.05, min(confidence + total_boost, 1.0))
```

### 6. Otros fixes
- **Índices SQLite**: `idx_normas_id`, `idx_normas_numero`, `idx_normas_fecha`, `idx_normas_tipo`
- **Neo4j cleanup**: 51% entidades genéricas eliminadas (verbos, 1-mención)
- **`import re`**: Agregado al inicio de `api_rest.py` para evitar `UnboundLocalError`

### 9. COUNT Temporal Filter + Abbreviations + Materia Ordering (Fix 2026-05-05)

**Problema compuesto (4 sub-bugs):**

**9a. COUNT sin filtro temporal.** La sección que construye `_where_parts` para el COUNT (línea ~286) detectaba trimestre y tipo_norma pero NO año/mes. El filtro temporal `fecha_publicacion LIKE 'YYYY-MM%'` solo se aplicaba a la query FTS5 (línea ~389), no al COUNT. Queries como "cuantas RM en marzo 2024" devolvían COUNT de toda la DB (328) en vez de solo marzo 2024 (243).

**9b. Filtro de materia colisiona con tipo+fecha.** El filtro de materia (`sumilla LIKE '%palabra%'`) se aplicaba ANTES de los filtros de tipo_norma y temporal porque estaba posicionado entre trimestre y tipo_norma en el flujo de `_where_parts`. Cuando una query tenía tipo+fecha, el filtro de materia ya se había agregado con palabras de la query (ej: "rm", "marzo", "publicacion") que no aparecen en las sumillas reales, llevando el COUNT a 1.

**9c. Abreviaturas no reconocidas.** Los regex de tipo_norma solo detectaban formas completas (`resoluciones?\s*ministeriales?`) pero no abreviaturas (`RM`, `DS`, `RS`, `RD`, `DL`, `DU`). Además, los patrones estaban en mayúsculas pero `_ql` está en minúsculas → nunca matcheaban.

**9d. LLM ignora COUNT en la respuesta.** El prompt no instruía al LLM a usar el bloque `[DATOS AGREGADOS]`. El LLM contaba normas de los resultados individuales (5-10) en vez del total real (243).

**Fixes aplicados:**

```python
# 9a: Año+mes en COUNT (insertado después del bloque tipo_norma)
_year_m = re.search(r'\b(20\d{2})\b', _ql)
if _year_m:
    _year = _year_m.group(1)
    _meses_map = {'enero':'01','febrero':'02','marzo':'03',...}
    _mes_num = None
    for _mn, _mc in _meses_map.items():
        if _mn in _ql:
            _mes_num = _mc; break
    if _mes_num:
        _where_parts.append(f"fecha_publicacion LIKE '{_year}-{_mes_num}%'")
    else:
        _where_parts.append(f"fecha_publicacion LIKE '{_year}%'")

# 9b: _has_strong_filter flag + materia al FINAL
_has_strong_filter = False  # se activa con trimestre, tipo_norma, o fecha
# ... después de TODOS los filtros ...
if not _has_strong_filter:  # solo materia si no hay filtros fuertes
    _q_words = [w for w in _ql.split() if len(w) >= 4 and w not in stopwords]
    # ... LIKE sumilla ...

# 9c: Abreviaturas lowercase antes de formas completas
(r'\brm\b', 'RESOLUCIÓN MINISTERIAL'),
(r'\bds\b', 'DECRETO SUPREMO'),
(r'\brs\b', 'RESOLUCIÓN SUPREMA'),
(r'\brd\b', 'RESOLUCIÓN DIRECTORAL'),
(r'\bdl\b', 'DECRETO LEGISLATIVO'),
(r'\bdu\b', 'DECRETO DE URGENCIA'),

# 9d: Instrucción en SYSTEM_PROMPT
"- Si el contexto incluye [DATOS AGREGADOS], usa ESA cifra como total numerico. "
"Los resultados individuales son solo una muestra parcial."
```

**Resultado:** "cuantas RM en marzo 2024" pasó de COUNT:328 (R.Fiscalía:40, D.Alcaldía:37, RM:25) → COUNT:243 (RESOLUCIÓN MINISTERIAL: 243). LLM ahora dice "el total de normas encontradas es de 243". SQL generado: `SELECT COUNT(*) FROM normas WHERE UPPER(tipo_norma) LIKE '%RESOLUCIÓN MINISTERIAL%' AND fecha_publicacion LIKE '2024-03%'`.

**⚠️ Orden de filtros en `_where_parts`:** El orden de los bloques dentro del `try` que construye `_where_parts` determina qué filtros se aplican antes que otros. La materia debe ser el ÚLTIMO bloque y solo si `_has_strong_filter` es False. Si se agregan nuevos filtros en el futuro, deben ir ANTES del bloque de materia.

## Pitfalls conocidos

1. **Conflictos de scope con `re`**: El archivo usa `import re as _re_X` en múltiples funciones. Si agregas código nuevo que use `re`, verifica que no haya un `import re` local que lo oculte.
2. **Floor 0.60**: Queries con ID exacto que antes obtenían 0.85 ahora pueden bajar si el detector de IDs no las captura.
3. **`_re_boost.IGNORECASE`**: Siempre usar el alias local, no `re.IGNORECASE` dentro del bloque del boost.
4. **Serper key name**: El source key es `serper_web`, no `web` ni `web_fallback`.
5. **Orden de filtros en COUNT**: El bloque de materia (`sumilla LIKE`) debe ser el ÚLTIMO en la construcción de `_where_parts` y solo ejecutarse si `_has_strong_filter` es False. Si se inserta antes de tipo_norma o temporal, colapsa el COUNT con palabras de la query que no existen en las sumillas reales. Ver Fix 9b.
6. **Abreviaturas lowercase**: Los patrones de tipo_norma deben estar en lowercase porque `_ql = question.lower()`. Patrones en uppercase como `\bRM\b` nunca matchean. Ver Fix 9c.
7. **`.pyc` cache**: Después de modificar `api_rest.py` en el servidor, limpiar `__pycache__` antes de reiniciar: `find /opt/elperuano -type d -name __pycache__ -exec rm -rf {} +`. Si no, el intérprete carga el bytecode viejo.
8. **`generate_answer()` síncrono bloquea event loop (Fix 10)**: Si `generate_answer()` es `def` síncrono (usa `requests.post`), toda consulta entrante se encola mientras espera a Groq. Convertir a `async def` con `asyncio.to_thread()` + `asyncio.wait_for()` para que corra en thread pool. Sin esto, una consulta lenta congela la API para todos los demás clientes. **Impacto real demostrado**: el script `bateria_100q_full.py` fallaba con 99 TIMEOUTs después de la query #1 — la API dejaba de responder incluso `/health`. Post-fix: 100/100 queries en 4.8 min, 0 timeouts.
9. **Hallucination legal en SYSTEM_PROMPT (Fix 11)**: El LLM tiende a asignar leyes genéricas (Ley 29158, Ley 27594) a temas específicos (crimen organizado). El prompt debe incluir ejemplos concretos de qué NO decir, no solo instrucciones abstractas. Frases como "NUNCA digas que Ley X trata sobre tema Y — son leyes generales" funcionan mejor que "no inventes normas".
10. **Ruta del log de consultas**: `Path("logs")` falla si el CWD no es el directorio del script. Usar `Path(__file__).parent / "logs"` o `BASE_DIR / "logs"` (si BASE_DIR ya existe en el módulo).
11. **`numeros_alucinados` out of scope en `validar()`**: La variable `numeros_alucinados` se define dentro de `_validar_heuristicamente()` pero se usa en `validar()` para construir `ValidationResult`. Debe retornarse en el dict de heuristica y extraerse con `.get()`. Si no, `NameError` silencioso (atrapado por `try/except` en el pipeline). Ver Fix 13.
12. **Validación desde cache no aplica**: Las respuestas cacheadas NO pasan por el validador. `validation_result` será `None` en cache hits. Si se modifica el validador, las respuestas cacheadas seguirán sin corregir.
13. **Validator pattern `numeros_fuentes`**: Buscar en `texto_completo` además de `titulo`/`sumilla`/`numero`/`id`. Muchas normas solo tienen su número en el texto completo.
14. **.venv CUDA bloat en VPS sin GPU**: `pip install sentence-transformers` instala torch con CUDA (~3.4G en `nvidia/`, `triton/`, partes de `torch/`). En VPS sin GPU (VMware SVGA, Contabo), instalar torch CPU-only: `pip install --index-url https://download.pytorch.org/whl/cpu torch` ANTES de instalar sentence-transformers. Diferencia: .venv de 5.5G → 1.5G. Ver también `references/venv-cpu-cleanup.md`.
15. **`pkill` en SSH sessions retorna 255 incluso si exitoso**: `pkill` retorna 1 si no hay proceso que matar, 0 si mató algo. Pero en sesiones SSH via `sshpass`, el código de salida puede ser 255 (error de terminal) aunque el kill haya funcionado. No usar el exit code como indicador de éxito. Verificar con `lsof -ti:8000` después.
16. **Reverse validation technique**: Convertir respuestas del sistema en preguntas para verificar consistencia lógica. Si el sistema dice "Ley 30077 regula crimen organizado", formular "¿qué ley regula el crimen organizado?" y verificar que la respuesta contenga Ley 30077. Script: `reports/test_reverse_validation.py`. Ver `references/reverse-validation.md`. Pitfall: respuestas cacheadas devuelven `validation_result: None` (el validador no corre en cache hits).

## Refactorización — Fases 1-4 (05-may-2026)

### api_rest.py: 2209 → 1443 líneas (-35%, -766 líneas)

### Módulos extraídos

| Módulo | Archivo | Líneas | Fase | Contenido |
|--------|---------|--------|------|-----------|
| Confidence scoring | `src/core/confidence.py` | 288 | F1 | `confidence_score` + 6 helpers, `db_getter` parametrizado |
| Web fallback | `src/web/fallback.py` | 163 | F2 | `search_web_fallback`, `search_tavily`, `search_local_htmls` |
| Metadata extractor | `src/core/metadata_extractor.py` | 103 | F2 | `extract_structured_metadata` (DNIs, CAP, fechas, etc.) |
| Scoring | `src/core/scoring.py` | 38 | F2 | `_dedup_and_blend` |
| Cache LRU | `src/core/cache.py` | 37 | F2 | `_get_cached`, `_set_cache` |
| Router | `src/core/router.py` | 151 | F4 | `route_response()` — 4 niveles (BÁSICO/INTERMEDIO/AVANZADO_ANALISIS/AVANZADO_CREACION) |
| Graph traversal | `src/core/graph_traversal.py` | 67 | F4 | `expand_graph()` — Neo4j 2-degree |
| Token tracker | `src/utils/token_tracker.py` | 183 | — | SQLite, endpoint `/token-stats`, precios Groq reales |

### Helpers compartidos (F3 — deduplicación)

| Helper | Función |
|--------|---------|
| `_enrich_entities(results)` | Inferencia de roles de funcionarios, montos con contexto, entidades |
| `_build_context(results)` | Construye contexto con sumilla + structured_metadata + texto_completo |
| `SYSTEM_PROMPT` | Template multilínea con placeholders `{profile}`, `{question}`, `{context}` |

### Bugs corregidos acumulados (6)

1. Type annotation `confidence_score`: `-> float` → `-> Tuple[float, dict]`
2. Hack `'_materia_params' in dir()` reemplazado por inicialización explícita
3. Variables sin inicializar en `_calc_semantic_defense`: `_has_zero_match`, `_has_real_overlap`
4. `get_qdrant()` y `_make_result()` eliminadas (dead code, 0 usos)
5. `generate_answer_stream()` hardcodeaba modelo `llama-3.3-70b-versatile` → ahora usa `_model_for_level()`
6. `generate_answer_stream()` usaba contexto empobrecido (sin roles, sin structured metadata) → ahora usa `_enrich_entities()` + `_build_context()` completos

### Métricas post-refactor (24/24 PASS acumulados)

| Métrica | F1-2 | F3 | F4 |
|---------|------|----|----|
| Pass rate | 12/12 | 8/8 | 4/4 |
| Confianza promedio | 0.70 | 0.74 | 0.72 |
| Tiempo promedio | 4,764ms | 4,239ms | 5,470ms |

### Metodología de refactorización (4 fases, zero-downtime)

Ver `references/phased-refactor-methodology.md` para el checklist completo, plantilla de fases, y señales de peligro.
1. Backup nivel 2 (copia local + SHA256) antes de cada fase
2. Extracción quirúrgica por subagente, una fase a la vez
3. Verificación de sintaxis (`ast.parse`) + health check API en cada paso
4. Test battery multinivel (BÁSICO/INTERMEDIO/AVANZADO) tras cada fase
5. Token tracking para medir impacto en costos
6. Rollback instantáneo vía `cp backups/... api_rest.py`

## Referencias

- `references/count-sql-debugging.md` — Diagnóstico rápido de COUNT incorrecto: extraer SQL, formas correctas/incorrectas, orden de filtros, abreviaturas.
- `references/phased-refactor-methodology.md` — Metodología de refactorización en 4 fases con zero-downtime.
- `references/token-tracker-pattern.md` — Patrón de integración del token tracker.
- `references/venv-cpu-cleanup.md` — Limpieza de .venv con CUDA bloat en VPS sin GPU. Diagnóstico, recreación con torch CPU-only, ahorro de 3-4GB.
- `references/reverse-validation.md` — Técnica de validación inversa: convertir respuestas en preguntas para verificar consistencia lógica del sistema.

### 14. max_tokens insuficiente para respuestas jurídicas (Fix 2026-05-06)

**Problema:** max_tokens=800 (BÁSICO) y 1200 (INTERMEDIO/AVANZADO) producían respuestas truncadas para análisis jurídicos extensos. ~600-900 palabras en español, insuficiente para citar múltiples fuentes y desarrollar argumentos.

**Fix:** `api_rest.py:1016`:
```python
# Antes
max_tok = 1200 if router_nivel in ("AVANZADO_CREACION", "AVANZADO_ANALISIS", "INTERMEDIO") else 800
# Después
max_tok = 3000 if router_nivel in ("AVANZADO_CREACION", "AVANZADO_ANALISIS", "INTERMEDIO") else 1500
```

### 15. Pregunta sin validación de longitud (Fix 2026-05-06)

**Problema:** `QueryRequest.question` era `str` sin restricciones. Una pregunta excesivamente larga podía saturar el context window sin advertencia.

**Fix:** `api_rest.py:1087`:
```python
# Antes
class QueryRequest(BaseModel):
    question: str
    profile: str = "abogado"
    top_k: int = 15

# Después
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    profile: str = "abogado"
    top_k: int = Field(15, ge=1, le=50)
```
Requiere: `from pydantic import BaseModel, Field`

### 16. Arquitectura del sistema documentada

Ver `reports/arquitectura_completa_sistema_20260506.txt` en el proyecto. Incluye:
- 10 capas del pipeline (cache → clasificación → búsqueda → override → KAG → confidence → web fallback → router → LLM → validación → post-boost)
- Todos los umbrales (CONFIDENCE_THRESHOLD=0.75, floor=0.60, boost max=0.30)
- Restricciones globales (timeouts, cache TTL, max results)
- Flujo de decisiones paso a paso

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Token stats (tracking de consumo)
curl http://localhost:8000/token-stats?granularity=total

# Test rápido
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"contrataciones del estado","profile":"abogado","top_k":3}'

# Test con filtro temporal
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"normas de enero 2024","profile":"abogado","top_k":3}'
```

### Test battery multinivel (12 queries: BÁSICO, INTERMEDIO, AVANZADO_ANALISIS, AVANZADO_CREACION)

Script en `scripts/test_battery.py`. Ejecutar con API corriendo en :8000. Genera reporte en `reports/test_battery_YYYYMMDD.txt`.

## Token Tracker

Patrón de integración documentado en `references/token-tracker-pattern.md`. Endpoint: `GET /token-stats`.

## Métricas post-fixes

| Métrica | Antes | Después |
|---------|-------|---------|
| Graph traversal | 0% | 32-68% |
| Frases prohibidas | 13 | 4-5 |
| Falsos positivos | 6/100 | 1/100 |
| Confianza promedio (50q) | — | 0.729 |
| Confianza promedio (25q) | — | 0.788 |
| Serper activo | 0%* | 20-72% |

*Serper siempre funcionó, bug en script de test

### 17. LeyBooster: priorizar resultados tipo LEY (Fix 2026-05-06)

**Problema:** Al preguntar "qué leyes hablan de crimen organizado", el FTS5 rankeaba más alto las Resoluciones Ministeriales (que mencionan "Crimen Organizado" en sus títulos) que las leyes reales (Ley 30077, Ley 32108). El LLM recibía RMs en las primeras posiciones y terminaba respondiendo con esas en vez de las leyes.

**Fix:** Detectar si la pregunta contiene "ley", "leyes", "legislativo" y priorizar resultados cuyo campo `tipo` sea LEY, LEYES, DECRETO LEGISLATIVO o DECRETO LEY:
```python
# api_rest.py después de search_sqlite()
_q_words = question.lower().split()
_asks_for_ley = any(w in _q_words for w in ['ley', 'leyes', 'legislativo', 'decreto ley'])
if _asks_for_ley:
    _ley_results = [r for r in unique_results if ((r.get('tipo') or '').upper()) in
                   ('LEY', 'LEYES', 'DECRETO LEGISLATIVO', 'DECRETO LEY')]
    for r in _ley_results:
        r['relevance'] = min(r.get('relevance', 0.3) + 0.3, 1.0)
    unique_results = _ley_results + _other_results
```

**⚠️ Pitfall:** `r.get('tipo')` puede ser literal `None` (no string). Usar `(r.get('tipo') or '')` para evitar `AttributeError: 'NoneType' object has no attribute 'upper'`.

### 18. Neo4j tipo_norma fallback desde sumilla (Fix 2026-05-06)

**Problema:** Los resultados provenientes de Neo4j graph traversal no tenían el campo `tipo_norma` poblado en los nodos. Aparecían como `None N° 32108` en el contexto del LLM, que no identificaba la norma como una LEY.

**Fix en `src/core/graph_traversal.py`:**
```python
_tipo = d.get("tipo") or ""  # None → ""
if not _tipo:
    # Extraer tipo de la sumilla mediante regex
    import re as _re_tipo
    _sum = d.get("sumilla", "") or ""
    _m = _re_tipo.search(
        r'(LEY|DECRETO\s+(SUPREMO|LEGISLATIVO)|RESOLUCI[OÓ]N|ORDENANZA|ACUERDO)',
        _sum, _re_tipo.IGNORECASE)
    _tipo = _m.group(0).upper() if _m else ""
```

El regex busca en la sumilla patrones como "Ley", "Decreto Supremo", etc. Funciona porque las sumillas siempre empiezan con el tipo de norma. Ej: "Modifica el Código Penal, **la Ley Contra el Crimen Organizado**..." → captura "Ley".

### 19. Contexto al LLM extendido y con scores (Fix 2026-05-06)

**Problema:** El LLM solo veía 10 resultados en el contexto, sin información de qué tan relevantes eran. Las sumillas se truncaban a 300 chars.

**Fix en `api_rest.py`, función `_build_context()`:**
```python
# Cambios:
# 1. results[:10] → results[:15]
# 2. r.get('tipo','') → r.get('tipo', r.get('tipo_norma', ''))  # soporta ambos keys
# 3. Añadir "(score={_score:.2f}, src={_src})" visible al LLM
# 4. Sumilla[:300] → Sumilla[:500]

for i, r in enumerate(results[:15]):
    _score = r.get('relevance') or r.get('blend_score', 0)
    _src = r.get('source', '?')
    _tipo = r.get('tipo', r.get('tipo_norma', ''))
    parts = [f"[{i+1}] {_tipo} {r.get('numero','')} (score={_score:.2f}, src={_src})"
             f" ({r.get('fecha','')}) - {r.get('emisor','')}"]
    if r.get('sumilla'):
        parts.append(f"    Sumilla: {r['sumilla'][:500]}")
```

### 20. Prompt "enumera todas las leyes" (Fix 2026-05-06)

**Problema:** El prompt decía "cita el tipo y número exacto" pero no obligaba a listar todas las leyes. El LLM seleccionaba 3-4 y omitía el resto (ej: Ley 32108 en posición 4 del contexto era ignorada).

**Fix en SYSTEM_PROMPT:**
```
- Menciona TODAS las leyes o normas relevantes de la seccion NORMAS ENCONTRADAS
  que apliquen a la pregunta, no solo la primera.
- Si la pregunta pregunta 'que leyes' o 'menciona las leyes',
  ENUMERA cada ley encontrada, sin omitir ninguna.
```

### 21. Anti-hallucination cleaner post-procesamiento (Fix 2026-05-06)

**Problema:** El prompt solo no era suficiente. Llama 3.3 no tiene la capacidad de distinguir "ley citada como base legal" de "ley sustantiva del tema". Ley 29158 (Orgánica del Poder Ejecutivo) aparecía en resoluciones de crimen organizado como base legal, y el LLM la citaba como si fuera una ley de crimen organizado.

**Fix:** Post-cleaner por regex que se ejecuta DESPUÉS de que el LLM genera la respuesta, ANTES de la validación:

```python
# api_rest.py — bloque ANTI-HALLUCINATION CLEANER
LEYES_ORGANIZATIVAS = [
    (r'(?:la\s+)?Ley\s+(?:N[°º]\s*)?29158(?:[^.,;]*)?', 'Ley 29158 (Orgánica)'),
    (r'(?:la\s+)?Ley\s+(?:N[°º]\s*)?27594[^.,;]*?', 'Ley 27594 (designación)'),
    (r'(?:la\s+)?Ley\s+(?:N[°º]\s*)?27444[^.,;]*?', 'Ley 27444 (Procedimiento Adm.)'),
    (r'(?:el\s+)?Decreto\s+Legislativo\s+(?:N[°º]\s*)?1266[^.,;]*?', 'DL 1266 (Org. MININTER)'),
    # Descripciones completas (el LLM a veces no usa el número)
    (r'Ley\s+de\s+Organizaci[oó]n\s+y\s+Funciones\s+del\s+Ministerio\s+del\s+Interior',
     'DL 1266 (desc)'),
]

_q_is_organizativa = any(w in question.lower() for w in [
    'organizacion del poder ejecutivo', 'organizacion del estado',
    'nombramiento', 'designacion de funcionarios', 'procedimiento administrativo'])
if not _q_is_organizativa and llm_answer:
    for pattern, _name in LEYES_ORGANIZATIVAS:
        llm_answer = re.sub(pattern, '', llm_answer, flags=re.IGNORECASE)
    # Limpieza de residuales
    llm_answer = re.sub(r'\bse\s+basan?\s+en\s*,?\s*\.?', '', llm_answer, flags=re.IGNORECASE)
    llm_answer = re.sub(r'\s{2,}', ' ', llm_answer)
    llm_answer = llm_answer.strip()
```

**⚠️ Pitfall de scope regex:** El import `import re` puede fallar por shadowing si hay otro alias `re` en el mismo bloque. Usar `import re as _re_clean` explícito dentro del bloque.

### 22. Test exhaustivo de 10 tests (Fix 2026-05-06)

Creado `reports/test_exhaustivo.py` que prueba:
1. Health check (4 tests: API + SQLite + Qdrant + Neo4j)
2. Validación de pregunta (3 tests: 2 chars→422, 1001 chars→422, válida→200)
3. Anti-hallucination (4 tests x2 queries: Ley 29158/27594 ausentes, Ley 30077 presente, respuesta >200 chars)
4. LeyBooster (3 tests: menciona "Ley", respuesta >300 chars, top-5 incluye tipo LEY)
5. Neo4j tipo no None
6. Timeout (2 queries seguidas sin bloquear)
7. max_tokens (2 tests: avanza >500 chars, básico >500 chars)
8. Contexto (2 tests: ≥3 resultados, resultados con scores)
9. Prompt inclusivo (menciona ≥2 leyes)
10. Grounding (números extra fuera de resultados)

Ejecutar:
```bash
cd PeruanoSearchEngine02 && source .venv/bin/activate
python3 reports/test_exhaustivo.py
```

### 23. VM sync pitfalls (acumulado 2026-05-06)

- **.pyc cache bloquea cambios**: `find /opt/elperuano -name '__pycache__' -type d -exec rm -rf {} +` ANTES de reiniciar. Si no, Python carga el bytecode compilado viejo.
- **graph_traversal.py no se sincroniza automáticamente con rsync de api_rest.py**: rsync require inclusión explícita o copia separada con scp. Verificar siempre que `graph_traversal.py` esté actualizado en la VM después de cambios.
- **nohup sobre SSH + tool kill**: El tool de terminal mata procesos hijos cuando la sesión SSH se cierra. Usar `nohup ... </dev/null > log 2>&1 &` para desvincular. Verificar con `ps aux | grep api_rest` después.
- **Cache LRU persiste entre reinicios**: `data/tokens.db` contiene el cache. Eliminarlo con `rm -f /opt/elperuano/data/tokens.db` si se necesita cache limpio.

### 7. COUNT Aggregation → LLM Context Injection (Fix 2026-05-05)

**Problema**: `_build_context()` solo recibía `results` (normas individuales). El COUNT ejecutado en `search_sqlite()` se guardaba en `sources["sql_count"]` pero nunca llegaba al prompt del LLM. Queries como "¿Cuántas RM en 2024?" devolvían ejemplos sueltos en vez del total numérico.

**Fix**: `_build_context(results)` → `_build_context(results, sources=None)`. Cuando `sources` contiene `sql_count`, inyecta bloque `[DATOS AGREGADOS]` con total + breakdown al inicio del contexto. Archivos: `api_rest.py` líneas 773, 861, 901.

**⚠️ Prompt instruction (agregado 2026-05-05):** El `SYSTEM_PROMPT` debe incluir explícitamente: "- Si el contexto incluye [DATOS AGREGADOS], usa ESA cifra como total numerico. Los resultados individuales son solo una muestra parcial." Sin esta línea, el LLM ignora el COUNT y cuenta manualmente de los resultados individuales. Ver Fix 9d.

### 10. Groq timeout / event-loop deadlock (Fix 2026-05-06)

**Problema:** `generate_answer()` era una función síncrona (`def`) que usaba `requests.post(timeout=45)`. Al ser llamada desde un endpoint async de FastAPI, bloqueaba el event loop completo de `uvicorn`. Una consulta que demoraba 45s en Groq congelaba la API para TODOS los demás clientes durante esos 45s.

**Síntoma:** El script `bateria_100q_full.py` mostraba `TIMEOUT | >90s` en todas las queries después de la #1. La API dejaba de responder a cualquier request (incluyendo `/health`) mientras esperaba a Groq.

**Fix:**
```python
# Antes (síncrono, bloquea event loop)
def generate_answer(question, profile, results, sources):
    resp = _rq.post(..., timeout=45)
    return resp.json()["choices"][0]["message"]["content"]

# Después (async, thread pool + timeout 50s)
async def generate_answer(question, profile, results, sources):
    def _do_groq():
        r = _rq.post(..., timeout=45)
        return r.json()["choices"][0]["message"]["content"]
    answer = await asyncio.wait_for(
        asyncio.to_thread(_do_groq),
        timeout=50
    )
    return answer
```

**Cambios requeridos en cadena:**
1. `generate_answer()` → `async def` (api_rest.py)
2. `route_response()` en `src/core/router.py` → `async def` y `await generate_answer(...)` en los 4 call sites
3. Llamada a `route_response()` en el endpoint `/query` → `await route_response(...)`
4. `import asyncio` agregado al inicio

**Resultado:** El event loop ya no se bloquea. `/health` responde incluso mientras Groq procesa. Timeout elegante a los 50s con mensaje al usuario.

### 13. Respuesta con "leyes X para tema Y" alucina normas procesales (Fix 2026-05-06)

**Problema:** Preguntando "qué leyes hablan del crimen organizado", el LLM responde que "Ley 29158 (Ley Orgánica del Poder Ejecutivo)" y "Ley 27594 (nombramientos)" tratan sobre crimen organizado. El LLM confunde leyes que aparecen como BASE LEGAL en resoluciones relevantes con leyes SUSTANTIVAS del tema.

**Causa raíz:** El prompt tenía reglas abstractas ("no inventes normas") pero no ejemplos concretos. Además, los números como "29158" (sin guion) no eran detectados por el validador existente porque su regex solo capturaba `\d{1,5}-\d{4}`.

**Fix de dos capas (A+C):**

**Capa C — Prompt grounding estricto:**
```python
# Reemplazar instrucciones hardcodeadas por reglas genéricas
"- SOLO puedes citar leyes cuyo NUMERO aparezca en NORMAS ENCONTRADAS\n"
"- Si citas una ley por su numero (ej. Ley 30077), verifica que ese numero\n"
"  esté en los titulos o sumillas de NORMAS ENCONTRADAS.\n"
"- Una ley organizativa (Ley Organica del Poder Ejecutivo,\n"
"  Ley de Procedimiento Administrativo) NO es relevante a menos que\n"
"  la pregunta sea sobre organizacion del Estado.\n"
```

**Capa A — Validación post-LLM con auto-corrección:**
Mejoras en `src/validation/response_validator.py`:
1. Nuevo patrón regex para leyes sin guion: `(?:Ley|Decreto Legislativo|Decreto Supremo)\s+(?:N[°º]\s*)?(\d{4,6})`
2. Búsqueda en `texto_completo` de las fuentes, no solo titulo/sumilla
3. Auto-corrección: si el validador detecta normas alucinadas, las elimina inline de la respuesta con `re.sub('[NORMA NO ENCONTRADA EN FUENTES]', ...)`
4. Campo `normas_alucinadas` en `ValidationResult` para que el pipeline sepa qué corregir

**Resultado:** "qué leyes hablan del crimen organizado" → "Ley N° 30077, Ley Contra el Crimen Organizado". Sin alucinaciones.

**Extensión — descripciones sin número:** El LLM a veces escribe la descripción completa sin el número (ej: "Ley de Organización y Funciones del Ministerio del Interior" en vez de "DL 1266"). Agregar patrón descriptivo al cleaner:
```python
(r'Ley de Organizaci[oó]n y Funciones del Ministerio del Interior',
 'DL 1266 (desc)'),
```

**⚠️ Pitfall de scope:** La variable `numeros_alucinados` se define DENTRO de `_validar_heuristicamente()` pero se referencia en `validar()` para construir `ValidationResult`. Debe retornarse en el dict de heuristica (`{"numeros_alucinados": numeros_alucinados}`) y extraerse en `validar()` con `numeros_alucinados = heuristica.get("numeros_alucinados", [])`. Si no, `NameError` en producción (silencioso porque está en `try/except`).

**⚠️ Pitfall de validación desde cache:** Las respuestas cacheadas NO pasan por el validador. Si se modifica el validador, el cache debe invalidarse o las respuestas cacheadas mantendrán alucinaciones. El `validation_result` del endpoint será `None` en cache hits.

### 12. Q&A Logging (Fix 2026-05-06)

**Problema:** No había registro persistente de las consultas realizadas. No se podía auditar qué preguntas se habían hecho, qué respuestas se dieron, ni qué fuentes se usaron.

**Fix:** Función `_log_query()` que escribe en dos formatos:

```python
def _log_query(question, profile, answer, timing_ms, confidence, sources):
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # TXT resumido (una línea por consulta)
    log_file = log_dir / "historial_consultas.txt"
    line = f"[{ts}] perfil={profile} conf={confidence:.2f} t={timing_ms}ms "
            f"fuentes={'+'.join(fuentes)} "
            f"Q: {question[:120]} A: {answer[:200]}\n"

    # JSONL completo (pregunta + respuesta integra + metadatos)
    log_json = log_dir / "historial_consultas.jsonl"
    entry = {"ts": ts, "perfil": profile, "pregunta": question,
             "respuesta": answer, "confianza": confidence,
             "tiempo_ms": timing_ms, "fuentes": fuentes}
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

**Archivos generados:**
- `logs/historial_consultas.txt` — Una línea por consulta, útil para `tail -f`
- `logs/historial_consultas.jsonl` — JSON completo, útil para análisis programático

**⚠️ Pitfall de ruta:** `Path("logs")` es relativo al CWD del proceso. Si `nohup` arranca la API desde un directorio distinto, el log se pierde. Usar `BASE_DIR / "logs"` donde `BASE_DIR = Path(__file__).parent.resolve()`. La función se llama desde el endpoint `/query` envuelta en `try/except: pass` para que un fallo de log nunca afecte la respuesta.

**Problema**: `validation_agent.py:365` tenía expresión matemática multilínea dentro de `{}` del f-string. Python 3.11 NO permite newlines en expresiones f-string (PEP 701, requiere 3.12+). VM staging usa Python 3.11.15.

**Fix**: Extraer cálculos a variables antes del f-string. Ver `vm-staging-deploy-troubleshooting` para detalle completo y diagnóstico.
