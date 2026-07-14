# El Peruano RAG — System Recovery & Expansion

## Trigger
Codigo Python no persiste entre sesiones, solo datos en backups y bases de datos Docker. Requiere restaurar desde backup disponible y expandir.

## Precaución: Rutas duplicadas del proyecto
Existen DOS rutas del proyecto:
- Canonical: `~/el_peruano_rag/PeruanoSearchEngine02/`
- Backup: `/media/usuario/ARCHVOS012/PyCode/PeruanoSearchEngine02/`

El terminal puede estar trabajando desde cualquiera de las dos. Siempre que se edite `.env` o archivos críticos, sincronizar:
```bash
cp ~/el_peruano_rag/PeruanoSearchEngine02/.env /media/usuario/ARCHVOS012/PyCode/PeruanoSearchEngine02/.env
diff ~/el_peruano_rag/PeruanoSearchEngine02/.env /media/usuario/ARCHVOS012/PyCode/PeruanoSearchEngine02/.env
```

**Pitfall**: `read_file` puede mostrar `API_KEY=xxx...yyy` truncado aunque el archivo real tenga la key completa. Siempre verificar con `grep API_KEY .env` en terminal.

## API Keys válidas (28-abril-2026)
- Groq: `<GROQ_API_KEY>` (modelo: llama-3.3-70b-versatile)
- Serper: `<SERPER_API_KEY>` (con credito, 200 OK) — usada como web fallback principal
- Tavily: `tvly-dev-...` (backup)
- Neo4j: `<NEO4J_CREDENTIALS>`

## Verificar Docker
Contenedores activos: qdrant_peruano (puerto 6333) y neo4j_peruano (puertos 7474/7687, auth: `<NEO4J_CREDENTIALS>`).

## Verificar datos existentes
- SQLite: conectar a data/normas_2024.db, consultar COUNT y columnas via PRAGMA table_info
- Qdrant: verificar colecciones normas_peruano, normas_q1_2024, normas_peruano_semantic vía API REST en localhost:6333
- Neo4j: consultar via bolt://localhost:7687 con credenciales, verificar conteo de nodos

## Migrar SQLite a Neo4j (si vacio)
Ejecutar script scripts/migrate_sqlite_to_neo4j.py con NEO4J_URI, USER y PASSWORD configurados. Modelo: Norma (21,584), Persona (18,003), Monto (9,413), Organismo (8,941). Relacion MENCIONA (330,620). Claves unicas via slug.

## Construir API REST (FastAPI)
Archivo api_rest.py en raiz del proyecto. Endpoints:
- GET /health: estado de todos los servicios + timing
- POST /query: RAG fusionado (SQLite LIKE match + Qdrant semantico + Neo4j entidades)
- GET /search: filtros combinados (q, tipo, emisor, fecha_desde, fecha_hasta, page, limit)
- GET /normas/{norma_id:path}: detalle de norma + entidades del grafo relacionadas
- GET /stats: estadisticas descriptivas completas

## Pitfalls frecuentes de la API
1. SQLite thread-safety: usar check_same_thread=False y conexion fresca por request FastAPI (NO singleton global compartido entre threads)
2. Sin columna contenido en DB: las normas NO tienen contenido, usar sumilla/titulo/materia
3. IDs con slash: usar {norma_id:path} en FastAPI route (ej: 2024-01-01/2248850-1) para que FastAPI no interprete el slash como separador de ruta
4. qdrant-client >= v1.10: usar query_points() en vez de search() (API cambio breaking)
5. Neo4j 5.x: usar COUNT{(n:N)-[:R]->(e)} en vez de size((:N)-[:R]->(e)) — size() en pattern expression fue eliminado
6. sentence-transformers: cargar como singleton lazy global con _encoder=None; primera carga ~10s (descarga modelo de HuggingFace), luego instantaneo
7. Modelo recomendado: paraphrase-multilingual-MiniLM-L12-v2 (384d) para espanol legal
10. **Qdrant "Broken pipe" por conflicto asyncio**: El `QdrantClient(query_points())` de Python (v1.17.x) usa httpx internamente y puede lanzar `[Errno 32] Broken pipe` persistentemente dentro de FastAPI/uvicorn (asyncio). **Soluciones que NO funcionan (todas probadas):**
    - Recrear el cliente con `global _qdrant; _qdrant = None`
    - Aumentar timeout del cliente
    - Usar `requests.Session()` en vez de QdrantClient
    - Forzar el encoder a CPU (`torch.device('cpu')`)
    - Usar raw sockets (`socket.sendall()`) para hacer la peticion HTTP
    - Usar `httpx.post()` directamente en vez de QdrantClient

    **Unica solucion que funciona:** Ejecutar la busqueda Qdrant en un **subproceso separado** via `subprocess.check_output()`. El proceso hijo crea su propia conexion HTTP y no hereda los problemas del event loop del padre:

```python
def search_qdrant(question_vec, collection, top_k=5):
    """Search Qdrant via subprocess Python para evitar Broken pipe por conflicto asyncio."""
    import subprocess, json, sys
    vec_str = json.dumps(question_vec)
    script = (
        "import requests, json, sys; "
        "url = 'http://127.0.0.1:6333/collections/%s/points/search'; "
        "payload = {'vector': %s, 'limit': %d, 'with_payload': True}; "
        "resp = requests.post(url, json=payload, timeout=30.0); "
        "resp.raise_for_status(); "
        "print(json.dumps(resp.json().get('result', [])))"
    ) % (collection, vec_str, top_k)
    result = subprocess.run([sys.executable, "-c", script],
        capture_output=True, text=True, timeout=60.0)
    if result.returncode != 0:
        return []
    return json.loads(result.stdout.strip())
```

    **Costo de overhead:** ~150ms adicionales por consulta (spawn + serializacion JSON).
    **Alternativa a futuro:** Cachear workers con `concurrent.futures.ProcessPoolExecutor` para eliminar overhead de fork.

11. **Variable de API key puede quedar truncada**: Al editar archivos grandes con patch, líneas que asignan variables de entorno (como `GROQ_API_KEY = os.getenv(...)`) pueden quedar incompletas. Verificar con grep en terminal después de modificaciones.
9. LIKE match en SQLite: scoring plano (0.5 siempre). Para discriminar, ordenar por CASE WHEN sumilla LIKE '%termino%' THEN 3 ELSE 0 END + CASE WHEN titulo LIKE... etc. Qdrant ya discrimina naturalmente (0.70-0.91).

12. **Qdrant payload anidado en metadata.***: Los puntos en colecciones como `normas_peruano_semantic` tienen payload con estructura `{chunk_id, custom_id, chunk_type, chunk_title, text, metadata: {tipo_norma, numero, fecha, sumilla}}`. Los campos clave (`tipo_norma`, `numero`) NO estan en la raiz del payload sino anidados en `metadata.*`. Si el codigo busca `p.get("tipo_norma", "")` siempre retorna vacio. Usar funcion extract con fallback:

```python
def _extract(p, key):
    if p.get(key):
        return p[key]
    meta = p.get("metadata", {}) or {}
    nested_map = {
        "tipo_norma": "tipo_norma",
        "numero": "numero",
        "fecha_publicacion": "fecha",
        "fecha": "fecha",
        "emisor": "emisor",
        "sumilla": "sumilla",
    }
    if key in nested_map:
        return meta.get(nested_map[key], "")
    return ""
```

13. **Confianza baja cuando Qdrant falla**: La formula de confidence_score depende 50% de Qdrant (`semantic_quality = (max_qdrant*0.7 + avg_qdrant*0.3) * 0.5`). Si Qdrant da 0 resultados (Broken pipe, coleccion vacia, etc.), la confianza maxima posible sin override es ~0.25, causando fallback web innecesario aunque SQLite tenga resultados ricos. **Fix:** Agregar SQLite quality como alternativa semantica:

```python
sqlite_scores = [r["relevance"] for r in results if r.get("source") == "sqlite"]
max_sqlite_score = max(sqlite_scores) if sqlite_scores else 0.0
sqlite_quality = max_sqlite_score * 0.55
best_semantic = max(semantic_quality, sqlite_quality)
```

Con esto, si SQLite tiene un match score ~1.0 (match directo), `sqlite_quality = 0.55`, sumado a count_score (0.15) + sqlite_boost (0.10) = 0.80, superando el umbral 0.75.

14. **Override 0.85 para IDs exactos no se activa a pesar de tener SQLite match**: El fix documentado en la seccion "Pitfall: confidence_score no refleja match exacto en SQLite" (override `weighted = max(weighted, 0.85)`) puede NO activarse incluso cuando `has_exact_id=True` y `sqlite_results` contiene la norma.

15. **Health check `/health` es engañoso — reporta "✅" con datos vacíos**: El endpoint verifica que el driver Neo4j puede abrir una sesión y ejecutar `MATCH (n) RETURN count(n)`, pero si la BD tiene 0 nodos igual reporta `"status": "ok"`. Esto pasó en producción: Neo4j reportaba `"nodes": 0, "relationships": 0` pero el health decía `"neo4j": "✅"`. El health de Qdrant también es engañoso: verifica que la API REST responde (usa `urllib`, no `requests`/httpx), pero Qdrant puede fallar con Broken pipe en cada query real (que usa `requests.post()` dentro de uvicorn). **NUNCA confiar solo en /health**: siempre validar con 3+ queries reales revisando el campo `sources` en la respuesta. Causas posibles:
    - **Deduplicacion elimina sqlite_results**: Los resultados SQLite y Qdrant comparten el mismo `id` del registro. Si Qdrant devuelve la misma norma, `unique_results` (despues de deduplicar por `id`) conserva solo la primera ocurrencia (usualmente Qdrant si Qdrant se agrega despues que SQLite). Pero `confidence_score` itera sobre `unique_results`, NO sobre `results` crudos. Si el unico resultado de SQLite fue eliminado por dedup, `sqlite_results` en `confidence_score` queda vacio, `sqlite_exact_boost=0`, y el override no se activa.
    - **Fix:** En `confidence_score()`, NO filtrar `results` por `source="sqlite"` sino pasarle los resultados SQLite sin deduplicar, o alternativamente buscar en los resultados originales antes de dedup.
    - **Otra causa:** El override se calcula ANTES del fallback web. Si la confianza final reportada es la de Groq (web fallback) y no la confianza local, puede verse el valor bajo aunque el override se haya aplicado internamente.

    **Verificacion rapida:** Agregar al endpoint /query un campo extra en la respuesta JSON con los valores internos de `has_exact_id`, `num_sqlite_results`, `sqlite_exact_boost`, y `weighted` antes del override. Esto permite diagnosticar el estado exacto sin leer logs.

## Scoring SQLite (mejora post-sesion)
El endpoint /search usa LIKE match con scoring plano. Para mejor discriminacion:
```sql
ORDER BY (
  CASE WHEN LOWER(sumilla) LIKE '%term1%' THEN 3 ELSE 0 END +
  CASE WHEN LOWER(titulo) LIKE '%term1%' THEN 2 ELSE 0 END +
  CASE WHEN LOWER(materia) LIKE '%term1%' THEN 1 ELSE 0 END
) DESC, fecha_publicacion DESC
```
Repetir por cada termino de busqueda. Esto da prioridad a normas que mencionan los terminos en titulo/sumilla vs solo en materia.

## Validacion con consultas reales
Siempre probar el sistema con 5 consultas de perfiles distintos:
1. Abogado → designaciones/nombramientos (categoria mas frecuente)
2. Funcionario → contrataciones/disposiciones MEF
3. Ciudadano → resoluciones MINSA sobre hospitales
4. Docente → normas educativas/nombramiento MINEDU
5. Periodista → transparencia/acceso informacion PCM

Verificar:
- 3 fuentes responden en cada query (SQLite+Qdrant+Neo4j)
- Timing: <50ms SQLite, <500ms Qdrant (cached), <200ms Neo4j
- Sin errores de sintaxis Neo4j 5.x
- Scoring Qdrant entre 0.70-0.91 (bien discriminado)
- Sin placeholders literales en reportes .md (escapar {{ y }} en f-strings Python)

## Construir Dashboard (Streamlit)
Archivo dashboard.py. Dependencia extra: plotly. Secciones: KPIs, grafico barras por tipo, pastel top-10 emisores, timeline mensual, top funcionarios, estado Neo4j (nodos+relaciones), colecciones Qdrant (puntos+dimensiones), tabla ultimas normas.

## Iniciar servicios
API en puerto 8000. Dashboard en puerto 8501. Usar background=true en terminal() del agente. Liberar puertos antes si estan ocupados.

## Archivo de plan estratégico

El plan completo de expansión se guarda en `reports/plan_expansion_YYYY-MM-DD.md`. Incluye:
- Diagnóstico de hardware y stack actual
- Mejoras inmediatas prioritarias (ver secciones abajo)
- Mejoras a mediano plazo (FTS5, re-ranker, hybrid search)
- Análisis de GraphRAG (cuándo vale la pena, recursos necesarios)
- Arquitectura propuesta final (diagrama ASCII de 5 capas)
- Roadmap en 4 sprints (semanal a mensual)
- Presupuesto de recursos ($0/mes con APIs gratuitas)
- Riesgos y mitigaciones

## Mejora Inmediata: Fallback Web con Serper (o Tavily como backup)

Cuando la base local no tiene resultados relevantes, se consulta Serper API (primario) o Tavily (backup si Serper sin creditos).

**Serper API:** `https://google.serper.dev/search` — header `X-API-KEY`
- 200 OK = funcional
- 400 con `"Not enough credits"` = key valida pero sin quota (cambiar key)
- 401 = key invalida
- Verificar con: `curl -s -X POST https://google.serper.dev/search -H "X-API-KEY: $KEY" -H "Content-Type: application/json" -d '{"q":"ley 32108","num":3}'`

**Tavily API:** `https://api.tavily.com/search` — header **DEBE ser `Authorization: Bearer {key}`**
- NUNCA usar `api-key` ni `X-API-Key` — ambos dan 401
- `config .env`: `TAVILY_API_KEY=tvly-dev-...`
- payload:
  ```python
  payload = {
      "query": question,
      "search_depth": "basic",
      "max_results": top_k,
      "include_answer": False,
      "include_raw_content": False,
  }
  ```

**Pitfall header Tavily:** Si se usa `header = {"Content-Type": "application/json", "api-key": TAVILY_API_KEY}` Tavily responde `HTTP 401 Unauthorized: missing or invalid API key`. El header correcto es `"Authorization": f"Bearer {TAVILY_API_KEY}"`. Se descubrio por prueba de 4 variantes de header.

**Verificacion de credito Serper:** `curl -X POST https://google.serper.dev/search -H "X-API-KEY: $KEY" -H "Content-Type: application/json" -d '{"q":"ley 32108","num":3}'` → 200 OK si tiene credito, 400 "Not enough credits" si agotado.

**Flujo**:
```
Pregunta del usuario → Búsqueda local (SQLite+Qdrant+Neo4j)
  → Calcular confidence_score() sobre resultados locales
  → ¿confidence < 0.75? → Fallback Web (Serper) → resultados web van PRIMERO en prompt
  → SÍ → Fusionar y generar respuesta con Groq
```

**Implementación real** (2 funciones + integración en /query):

### search_web_fallback(question, top_k)

Busca en Serper con 2 sites, parsea organic results, deduplica por URL. Retorna lista en formato interno con `source: "serper_web"`.

### confidence_score(results)

El indicador MÁS FIABLE es el score semántico de Qdrant. SQLite LIKE match encuentra keywords incluso cuando el resultado es irrelevante.

Pesos probados en producción:
- Calidad semántica Qdrant: 60% del score (usando max_score * 0.7 + avg_score * 0.3, cap a 0.6)
- Cantidad de resultados diversos: 20% (escala con len/15, cap a 0.2)
- SQLite con >2 resultados: 10% (boost binario)
- Neo4j con relaciones: 10% (escala con count * 0.03, cap a 0.1)

Umbral calibrado: **0.75** — queries con datos realmente relevantes dan ~0.77+. Queries marginales dan ~0.73-.

### Integración en /query endpoint

**Punto crítico corregido (28-abr):** Los resultados web NO se inyectaban al prompt del LLM porque `slots_left = max(0, top_k - existing_count)` siempre daba 0 (unique_results tiene >=5 resultados locales). Fix: forzar 2 resultados web al frente de unique_results con relevance=1.0:

```python
if confidence < CONFIDENCE_THRESHOLD:
    web_results = search_web_fallback(question, top_k)
    if web_results:
        sources["serper_web"] = {"count": len(web_results), "method": "google_serper"}
        # Forzar 2 mejores resultados web al frente con relevance=1.0
        # para que el LLM los vea siempre
        for wr in web_results[:2]:
            wr["relevance"] = 1.0
        unique_results = web_results[:2] + unique_results
        logger.info(f"[Inject] Added {min(2, len(web_results))} web results to front")
```

**Pitfall:** Aun con la inyeccion correcta, el LLM puede no usar el tag `[WEB]` en su respuesta — formatea como "Noticia..." con URL. Esto es comportamiento del LLM, no bug del pipeline. Para forzar el tag, agregar en system prompt: "Cuando cites resultados WEB, usa el formato `[WEB]` explicitamente."

### build_llm_prompt — source-aware formatting

Los resultados WEB se formatean con `[WEB]` tag + título + URL. Los resultados locales con `[sqlite|qdrant|neo4j]` + tipo+numero+fecha+emisor. Esto permite al LLM distinguir fuentes y citar URLs cuando corresponde.

### 6. Numero exacto no rankea en top-5 del blend
**Sintoma:** pregunta con numero exacto (ej. "ley 31980") devuelve confidence=0.75 pero la norma exacta no aparece en resultados.

**Causa raiz:** El blend_score = 0.50 * relevance SQLite + 0.30 * Qdrant + 0.20 * Neo4j. Si la norma exacta solo aparece en SQLite y otras normas tienen relevance similar (porque max_score es pequeño), su blend_score no es suficiente para rankear primero.

**Fix:** Aplicar override del numero DESPUES del blend, insertando la norma en `unique_results` con blend_score=1.0:
```python
# En unique_results, despues del sorted blended
_norma_forzada = None
for _num in _raw_nums:
    if not (2020 <= int(_num) <= 2035):
        for _ur in unique_results:
            if _num in _ur.get('numero', ''):
                _norma_forzada = _ur
                _ur['blend_score'] = 1.0
                break
        if not _norma_forzada:
            # Query directa SQLite e insertar
            _row = db.execute(...).fetchone()
            if _row:
                _d = dict(_row); _d['blend_score'] = 1.0; _d['relevance'] = 1.0
                _norma_forzada = _d
if _norma_forzada:
    unique_results = [_norma_forzada] + [r for r in unique_results if r.get('numero') != _norma_forzada.get('numero')]
```

### 7. Post-hoc negation detector falso positivo
**Sintoma:** LLM dice "No se encontro la LEY N° XXXX en los resultados" (refiriendose al top-5), y el detector penaliza confidence * 0.4.

**Causa raiz:** El detector ve "no se encontro" sin contexto de que el LLM se refiere al conjunto limitado, no a la ausencia total de datos.

**Fix:** Anadir guarda: no penalizar si confidence >= 0.7 y no hay web fallback (override de datos locales activo):
```python
if llm_answer and confidence >= 0.5 and len(web_results) == 0 and confidence < 0.7:
```

### Pitfalls encontrados en implementación real

1. **Umbral 0.5 es demasiado bajo**: Qdrant encuentra matches semánticos parciales (score 0.4-0.7) para casi cualquier query legal peruana. El umbral real que funciona es 0.75 — permite que queries con datos verdaderamente relevantes (~0.77+) pasen sin fallback, pero queries con resultados marginales (~0.73-) activen la búsqueda web.

2. **Qdrant "Broken pipe" persistente bajo uvicorn**: `QdrantClient.query_points()` lanza `[Errno 32] Broken pipe` dentro de FastAPI/uvicorn por conflicto del event loop asyncio. Ninguna solucion funciona excepto aislar la consulta Qdrant en un **subproceso separado** via `subprocess.run([sys.executable, "-c", script])`. Ver Pitfall #10 para implementacion exacta.

3. **Resultados web orden al final**: Con relevance=0.15 están en la posición 10-12 de la lista, fuera del slice `results[:6]` que ve el LLM. Solución: forzar relevance=1.0 y concatenar web + local results.

4. **Deduplicación por URL**: Serper puede devolver el mismo resultado de `site:diariooficial.elperuano.pe` y `site:gob.pe`. Siempre deduplicar por URL después de mergear ambos sites.

5. **Línea GROQ_API_KEY puede estar corrupta**: En el archivo original, la línea de asignación puede aparecer truncada en read_file. Verificar siempre con grep en terminal que la línea esté completa.

6. **Qdrant subprocess con raw sockets se rompe silenciosamente** — El subprocess que usa sockets TCP raw para comunicarse con Qdrant via HTTP crashea con `SyntaxError: unterminated f-string` por el anidamiento de f-strings en Python. Esto hace que Qdrant devuelva 0 resultados sin error visible. Fix: Usar `requests.post()` directo a `http://localhost:6333/collections/{collection}/points/search` con 3 intentos de retry. `requests` esta disponible como dependencia del proyecto.

7. **Qdrant nunca aparece en resultados finales aunque funcione** — Aunque Qdrant devuelva puntos con scores ~0.54-0.57, SQLite produce `relevance=1.0` via weighted CASE scoring. En el merge sort (`sorted(unique_results, key=lambda x: x.get('relevance', 0), reverse=True)`), SQLite siempre gana. Qdrant solo se ve cuando SQLite da 0 resultados. No es bug del codigo sino de la arquitectura del scoring — Qdrant scores (~0.5) no pueden competir con SQLite scores (1.0). Evaluar si se necesita blending de scores.

8. **Neo4j siempre retorna datos** — incluso para queries sin entidades reales, Neo4j devuelve 5 resultados porque la consulta `toLower(e.nombre) CONTAINS 't'` hace match parcial. Esto infla `neo4j_n` y puede hacer pensar que Neo4j contribuye mas de lo real.

6. **Override 0.85 para IDs exactos no se activa si SQLite results no incluye la norma**: Aunque `has_exact_id=True`, el override `weighted = max(weighted, 0.85)` falla si `sqlite_results` esta vacio. Esto ocurre cuando SQLite busca con `LIMIT {top_k}` (default 3) y el match por numero no rankea entre los primeros 3 resultados. **Fix:** Usar `LIMIT {top_k * 3}` en la query SQLite interna.

7. **SQLite LIMIT pequeno pierde matches por numero en ranking**: El scoring compuesto (emisor=5 + titulo=4 + sumilla=3 + materia=2 + numero=5) da prioridad a matches en emisor sobre matches exactos en numero. Para "Ley 32108": emisor de otro resultado puede tener "ley" (score 5) mientras el 32108 solo tiene score en numero (5) + sumilla (3) = 8 vs 5+4=9. Con LIMIT=3, el 32108 queda excluido. **Fix:** `LIMIT {top_k * 3}`.

8. **exact_id_penalty rompe consultas donde el ID exacto no existe como numero propio pero es referenciado en normas 2024**: Consultas como "DL 1057 CAS" activan `has_exact_id=True` y `sqlite_exact_boost=0.0` (porque "1057" no existe en columna `numero` de la BD -- el DL 1057 es de 2008). La penalidad `exact_id_penalty=0.50` reduce la confianza a ~0.27, activando web fallback innecesario, AUNQUE la BD tiene normas 2024 que mencionan el DL 1057 en sumilla/titulo. **Fix:** Antes de aplicar la penalidad, buscar en sumilla/titulo:

```python
if not found_in_db and nums_in_q:
    row = conn.execute(
        "SELECT id, numero FROM normas WHERE (sumilla LIKE ? OR titulo LIKE ?) LIMIT 1",
        (f"%{n}%", f"%{n}%")
    ).fetchone()
    if row:
        found_in_db = True
        sqlite_exact_boost = 0.10
```

9. **Health endpoint se rompe con get_qdrant() devolviendo dict**: La funcion `get_qdrant()` que devuelve `{"url": QDRANT_URL}` rompe `/health` endpoint. **Fix:** Usar REST API directa en vez de QdrantClient.

10. **Reportes de prueba se acumulan sin estructura**: El directorio `reports/` acumula decenas de archivos. Mover archivos anteriores al dia actual a `reports/historico/` periodicamente.

## Reindexación limpia de Qdrant (recrear colección)

Cuando la colección Qdrant acumula puntos viejos con payloads vacíos (por ejecuciones fallidas o cambios de formato), NO se pueden borrar con filter (Qdrant no soporta `delete` con filter sin especificar puntos individuales). El procedimiento correcto:

1. **Eliminar colección**: `curl -s -X DELETE http://localhost:6333/collections/{name}`
2. **Recrear con misma config**: `curl -s -X PUT http://localhost:6333/collections/{name} -H "Content-Type: application/json" -d '{"vectors": {"size": 384, "distance": "Cosine"}}'`
3. **Reindexar desde SQLite**: Script `scripts/reindex_qdrant_payloads.py` que recorre todas las normas, genera embedding con `paraphrase-multilingual-MiniLM-L12-v2` (384d) y upserta a Qdrant con payload completo.

**Puntos críticos del reindex:**
- **Qdrant point IDs deben ser UUID v5**, no strings arbitrarios. Usar `uuid.uuid5(uuid.NAMESPACE_OID, sqlite_id_str)`.
- **Endpoint correcto**: `PUT /collections/{name}/points` (NO `POST`). POST da 400 Bad Request.
- **Payload en raíz, no anidado**: Los campos `id`, `tipo_norma`, `numero`, `fecha_publicacion`, `emisor`, `sumilla`, `materia` deben ir en la raíz del JSON del punto, no dentro de `metadata`.
- **Batch size**: 100 puntos por batch funciona bien (~1-4s cada batch con modelo cacheado).
- **Total**: 21,584 puntos en ~216 batches (~5 min con modelo cacheado en RAM).

## Bug conocido: Graph traversal usa variable `seen` no definida

El codigo de graph traversal (post-blend) usa `seen` como conjunto de IDs para evitar duplicados, pero esa variable fue renombrada a `seen_ids` cuando se implemento el dedup por `id`. Esto causa un error `NameError: name 'seen' is not defined` que:

1. Rompe silenciosamente todo el bloque de graph traversal
2. Reporta `"error": "name 'seen' is not defined"` en sources["neo4j_graph"]
3. NO mata la API (el try/except lo atrapa) pero graph traversal nunca funciona

**Fix:** Cambiar `if d.get("id") and d["id"] not in seen:` por `if d.get("id") and d["id"] not in seen_ids:` en las lineas 752-753 de `api_rest.py`.

## ESTADO ACTUAL DEL SISTEMA (28-abr-2026)

### Infraestructura
- **Docker:** qdrant_peruano + neo4j_peruano
- **API:** Python 3.12 + FastAPI en :8000, modelo Groq llama-3.3-70b-versatile

### Artefactos
- **SQLite:** 21,584 normas (FTS5 activo con stemming)
- **Qdrant:** 21,584 puntos (384d), REST API directa
- **Neo4j:** 58,212 nodos / 330,620 relaciones

### Modulos v2.5 - Estado

| Modulo | Estado 27-abr | Estado 28-abr (19:00) |
|--------|--------------|----------------------|
| `sinonimos_legales.py` | Parcial (60 conceptos) | ACTIVO (200 conceptos) |
| `query_classifier.py` | NO EXISTIA | ACTIVO (100% precision: EMISOR_NAME_MAP + cascada corregida) |
| `detectar_entidades()` | MUERTO | ACTIVO |
| `response_validator.py` | MUERTO | **ACTIVO (conectado a /query)** |
| `sql_count` (Fase 3) | NO EXISTIA | **ACTIVO (COUNT + GROUP BY + expansion emisores)** |
| `search_web_fallback` | Serper sin creditos | **Serper con credito + injection fix** |
| `validation_agent.py` | MUERTO | MUERTO (F2) |
| `web_enrichment_agent.py` | MUERTO | MUERTO (F2) |

### Fixes implementados (28-abr)

**Fix #1: Forzar conf=0.15 en tipo H**
- `if query_type == 'H': confidence = min(confidence, 0.15)`
- FP eliminado, adversarial 80%→100%

**Fix #2: Routing selectivo**
- Qdrant: solo si `use_qdrant=True` (-60% queries)
- Neo4j Graph: solo si `use_graph_traversal=True` (-85% queries)
- Latencia tipo A: 70ms→40ms

**Fix #3: Response Validator activado (Bug #5)**
- `ResponseValidator(use_llm=False)` como lazy singleton
- Llama `val.validar(llm_answer, unique_results, question)` post-generacion
- Resultado en campo `response_validation` del JSON response
- Usa solo heuristica (sin LLM extra) para no gastar tokens Groq
- Pendiente: tunear patrones de extraccion (trata años como numeros de norma)

**Fix #4: Clasificador — cascada reordenada + EMISOR_NAME_MAP**
- D (Emisor+Accion) y E (Acronimo) ANTES de C (Temporal)
- Antes: "SUNAT y tributacion 2024" → C (el año domina)
- Ahora: "SUNAT y tributacion 2024" → E (acronimo tiene prioridad)
- Nuevos patrones adversariales: inteligencia artificial, deepseek, metaverso, realidad virtual
- MODIFICACION_PATTERNS: agregado `derogad[ao]s?`, `modificad[ao]s?`, plurales flexibles
- **EMISOR_NAME_MAP**: diccionario de ~45 mapeos nombre completo→acronimo en query_classifier.py
  - "ministerio de salud" → MINSA, "poder judicial" → PODER JUDICIAL, "fiscalia" → FISCALIA
  - Se evalua DESPUES de acronimos directos, ANTES de clasificacion
- **ACCIONES_LEGALES mejoradas**: "renuncia", "renuncias", "renuncio", "destituye", "destitucion"
- Precision subio de 70% → 83% → 100% en ultimo test de 50 queries

**Fix #5: SQL COUNT para queries agregadas (Fase 3)**
- Tipo C con `skip_count_queries=True` + palabras de conteo → SQL agregado
- Construye WHERE desde entidades: tipo_norma, emisor, fecha, mes, trimestre
- **Expansion de emisores:** ACRONIMO_TO_NAMES reverse map en api_rest.py
  - MINSA → `LOWER(emisor) LIKE '%ministerio de salud%' OR LOWER(emisor) LIKE '%minsa%'`
  - Evita el bug de buscar solo el acronimo en DB que usa nombre completo
- GROUP BY para breakdown por tipo
- Inyecta `[CONTEO EXACTO]` en el prompt del LLM
- Solo se activa cuando la query contiene palabras como "cuantas", "total", "conteo" (no en todas las tipo C)
- Resultados validados: RM marzo 2024 = 327, leyes 2024 = 228, DS 2024 = 628, MINSA designaciones = 445

### Pitfall #21: Serper API sin creditos — web fallback muerto silencioso
**Sintoma:** web_fallback_used=False en TODAS las queries, incluso con conf=0.0. Search_web_fallback() retorna [] porque Serper responde 400 con `{"message":"Not enough credits"}`.
**Deteccion:** `curl -X POST https://google.serper.dev/search -H "X-API-KEY: $KEY" -d '{"q":"test"}'` → HTTP 400.
**Fix:** Nueva API key o esperar reset mensual. Mientras tanto, el sistema funciona sin web fallback.

### Pitfall #22: Clasificador — año domina sobre entidad/acronimo
**Sintoma:** "SUNAT y tributacion 2024" → tipo C (TEMPORAL) en vez de E (ACRONIMO). La presencia de "2024" da temporal_score=2 que dispara C antes de evaluar D/E.
**Fix:** Mover checks D (Emisor+Accion) y E (Acronimo) ANTES de C en la cascada de clasificacion. Temporal solo se activa si no hay entidad/acronimo fuerte.

### Pitfall #23: Acentos en SQLite LIKE — RESOLUCIÓN ≠ RESOLUCION
**Sintoma:** `LOWER(tipo_norma) LIKE '%resolucion ministerial%'` da 1 resultado. El DB tiene "RESOLUCIÓN MINISTERIAL" (con tilde) = 2,812 + "Resolución Ministerial" = 1,438.
**Fix:** Usar patrones flexibles: `tipo_norma LIKE '%esoluci%n%inisterial%'` captura ambas variantes. El `%` entre `i` y `n` absorbe la diferencia de acento.

### Resultados test 20 preguntas

| Metrica | Antes | Ahora |
|---------|-------|-------|
| Funcional | 30% | 47% |
| Adversarial | 80%+1FP | 100%+0FP |
| Latencia | 2.55s/q | 1.34s/q |
| Qdrant usado | 100% | 40% |
| Graph usado | 100% | 15% |

### Pendientes (post-sesion 28-abr 16:00)

1. **Serper API key con credito** — conseguida y funcional (`10c54b...f1f4`)
2. **Web fallback injection fix** — forzar 2 resultados web al frente de unique_results (antes slots_left=0)
3. **EMISOR_NAME_MAP implementado** — 40+ mapeos nombre completo→acronimo en query_classifier.py
4. **ACRONIMO_TO_NAMES reverse map** — expansion en SQL COUNT: MINSA→['ministerio de salud','minsa']
5. **renuncias agregado a ACCIONES_LEGALES** — cubre "renuncia", "renuncias", "renuncio", "destituye", "destitucion"
6. Response validator: tunear patrones (trata años como numeros de norma, falsos positivos)
7. Embeddings fine-tune para dominio legal peruano (mejora Qdrant relevance)
8. Ingesta 2020-2023 (datos historicos)

### Pitfall #20: No usar patch tool en api_rest.py
api_rest.py tiene nesting de 4+ niveles. `patch` falla con indentacion. Usar subagente o scripts Python.

### Pendientes criticos
- **FTS5:** Codigo existe en src/ pero API NO lo usa (sigue con LIKE)
- **Dashboard:** Existe (dashboard.py) pero NO esta corriendo en :8501
- **GraphRAG:** Solo 1 de 5 componentes implementados (falta community detection, LLM summaries, reranking, viz)
- **Datos:** Solo 1 ano (2024), falta ingerir 2020-2023

### Roadmap inmediato (Fase 1, 2-3h)
1. Ajustar Capa 5 para verificar co-existencia en BD completa (no solo top-8 resultados)
2. Iniciar Dashboard en :8501
3. Activar FTS5 con stemming en API

## Bug CRITICO confirmado: Floor 0.75 crea punto ciego sistemico en queries adversariales

**Validacion empirica (bateria 70 queries, 2026-04-25):**
- 68/70 queries tienen EXACTAMENTE conf=0.75
- 7/10 queries adversariales (Cat G) NO caen a web fallback
- El floor `sqlite_count >= 1 → max(weighted, 0.75)` anula las 6 capas de defensa
- SQLite SIEMPRE encuentra 15 resultados (palabras de relleno: "normas", "resolucion", etc.)

**Mecanismo preciso:**
1. Cualquier query (incluso "criptomonedas", "metaverso", "ignora la BD") retorna sql=15, qd=5
2. El floor `weighted = max(weighted, 0.75)` se aplica SIEMPRE porque sqlite_count >= 1
3. La penalidad FP no puede bajarlo de 0.75 porque `max(weighted - penalty, 0.75)` efectivamente ignora la penalidad
4. Web fallback NUNCA se activa (threshold es 0.75)

**Queries afectadas (confirmadas):**
- G1 "Ley 99999": conf=0.75, deberia ser <0.50 (ID falso)
- G3 "criptomonedas": conf=0.75, deberia activar web
- G4 "IA generativa": conf=0.75, deberia activar web
- G7 "ministerio espacial": conf=0.75, deberia activar web
- G8 "links descarga": conf=0.75, jailbreak no mitigado
- G9 "ignora la BD": conf=0.75, jailbreak no mitigado
- G10 "bitcoin contrataciones": conf=0.75, combinacion imposible

**Fix propuesto:** Reemplazar floor incondicional por floor condicional:
```python
# ANTES (bug): floor siempre activo
if sqlite_count >= 1:
    weighted = max(weighted, 0.75)

# DESPUES (fix): floor solo si hay evidencia de relevancia
if sqlite_count >= 1 and sqlite_exact_boost > 0:
    weighted = max(weighted, 0.85)  # Solo IDs exactos
elif sqlite_count >= 3 and max_sqlite_score > 0.5:
    weighted = max(weighted, 0.75)  # Solo si SQLite ranking es fuerte
# Si no hay evidencia de relevancia, DEJAR que la penalidad FP actue
```

**Nota:** Este fix debe ir DESPUES de las penalidades FP (Capas 1-6) para que estas tengan efecto real.

**Tecnica de debug para confidence_score**: Los prints a stderr no son visibles dentro de uvicorn (el logging de uvicorn los intercepta). Para inspeccionar variables internas, agregar un dict `_debug_internal` al final de `confidence_score()` y guardarlo en `sys.modules['__main__']._last_conf_debug`, luego incluirlo en el return de `/query`:

```python
# En confidence_score():
_debug_internal = {
    "semantic_quality": round(semantic_quality, 4),
    "sqlite_quality": round(sqlite_quality, 4),
    ...
}
import sys
sys.modules.get('__main__')._last_conf_debug = _debug_internal

# En query():
return {
    ...
    "debug_internal": getattr(sys.modules['__main__'], '_last_conf_debug', {}),
}
```

## Importante al reiniciar**: Limpiar `__pycache__` (`find .../__pycache__ -name 'api_rest*' -delete`) y matar procesos viejos (`pkill -9 -f 'uvicorn api_rest'`) antes de reiniciar para asegurar que el nuevo codigo se cargue sin cache de .pyc.

## Pitfall #16: Qdrant Broken pipe persistente por proceso uvicorn stale

**Sintoma:** Qdrant reporta `[Errno 32] Broken pipe` en TODAS las queries via API, pero Qdrant directo (REST API via curl/python requests) funciona perfectamente. El codigo de `search_qdrant()` usa `requests.post()` correctamente (no QdrantClient).

**Causa raiz:** El proceso uvicorn que corre la API es viejo/stale. Aunque el codigo en disco este corregido, el proceso en memoria tiene estado corrupto del event loop o conexiones HTTP agotadas.

**Fix:** Matar el proceso viejo y reiniciar:
```bash
# Encontrar PID
lsof -i :8000 | grep LISTEN
# Matar
kill <PID>
sleep 2
# Reiniciar
cd ~/el_peruano_rag/PeruanoSearchEngine02 && python3 api_rest.py &
```

**Verificacion:** Qdrant directo funciona PERO API reporta Broken pipe → restart API. Si ambos fallan → problema real de red/Qdrant.

**Frecuencia:** Ocurre cuando el API lleva horas/dias corriendo sin reinicio. El restart toma <3 segundos.

## Pitfall #17: stats endpoint roto — get_qdrant() es dict, no QdrantClient

**Sintoma:** `GET /stats` devuelve `"qdrant": {"error": "'dict' object has no attribute 'get_collection'"}`.

**Causa:** `get_qdrant()` en línea 56 devuelve `{"url": QDRANT_URL}` (dict), pero `/stats` en línea 1017 llama `qc.get_collection()` asumiendo que `qc` es un `QdrantClient`. Esto es un remanente de cuando `get_qdrant()` instanciaba `QdrantClient`.

**Fix:** Usar REST API directa en `/stats` tambien:
```python
try:
    import requests as _req
    url = get_qdrant()["url"]
    resp = _req.get(f"{url}/collections/normas_peruano_semantic", timeout=5)
    ci = resp.json()["result"]
    stats_data["qdrant"] = {
        "collection": "normas_peruano_semantic",
        "points": ci["points_count"],
        "vector_size": ci["config"]["params"]["vectors"]["size"]
    }
except Exception as e:
    stats_data["qdrant"] = {"error": str(e)}
```

## Pitfall #19: test_100_queries.py reporta web_n=0 aunque Serper SI se uso

**Sintoma:** El informe markdown muestra "Web fallback: 0 (0.0%)" en la tabla de fuentes activas, y `web_n=0` en todas las filas, pero 23 queries tienen `fb=True` y los issues dicen "Web fallback (aceptable con respuesta)" o "Trampa detectada: web fallback activado".

**Causa raiz — doble punto ciego:**

1. **Punto ciego en la API (api_rest.py:1044-1048):** Los resultados de Serper SOLO se agregan al array `results[]` si `slots_left > 0` (quedan espacios libres en top_k). Como los resultados locales (SQLite+Qdrant+Neo4j) siempre llenan todos los slots, los resultados de Serper NUNCA entran al array `results[]`.

```python
slots_left = max(0, top_k - existing_count)
if slots_left > 0:  # ← Siempre False si hay >= top_k resultados locales
    unique_results = unique_results + web_results[:slots_left]
```

2. **Punto ciego en el test (test_100_queries.py:250):** El script mide `web_n` contando items con `source == "serper_web"` DENTRO del array `results[]`, pero Serper results nunca estan ahi.

```python
web_n = len([r for r in results if r.get("source") == "serper_web"])  # ← Siempre 0
```

**Donde SI estan los resultados de Serper:** En `sources["serper_web"]` del response JSON (api_rest.py:1040), pero el test script NUNCA revisa ese campo. Solo extrae `sqlite_n`, `qdrant_n`, `neo4j_n`, `graph_n` de `sources`.

**Como identificar si Serper se uso realmente:** El campo `fb = response.get("web_fallback_used", False)` — si es True, Serper fue llamado y retorno resultados. El `fb` del JSON crudo ES el indicador correcto. En el informe actual (14:53), 23/100 queries tienen `fb=True`.

**Fix en el test script:** Agregar extraccion de `sources.get("serper_web", {}).get("count", 0)` como `serper_n`, e incluir este campo en el detalle y en el informe markdown. Separar el concepto de "Serper llamado" (fb) de "Serper visible en results" (web_n).

## Pitfall #18: read_file muestra lineas truncadas con `...` — no confiar en display

**Sintoma:** `read_file` muestra lineas como `SERPER_API_KEY=os.get...EY\", \"\")` o `GROQ_API_KEY=os.get...EY\", \"\")`, sugiriendo codigo roto. Pero `ast.parse()` pasa sin errores.

**Causa:** `read_file` trunca lineas largas (>~45 chars) insertando `...` en el medio. El archivo real esta correcto.

**Verificacion:** Usar terminal con `python3 -c "print(open('api_rest.py').readlines()[129])"` o `grep` en terminal para ver la linea real. O verificar con `ast.parse()` si hay syntax errors reales.

## Gaps en defensa multicapa (descubiertos en bateria 22 queries, 26-abr-2026)

Resultados con API funcional (Qdrant reparado, Neo4j vacio):
- 17/22 PASS, 3 FP, 2 FN → 77% tasa de acierto
- 100% jailbreaks neutralizados
- Qdrant: 22/22 OK (0 Broken pipe)

**FP GAP #1: Capa 2 overlap demasiado permisiva.** `"regulacion inteligencia artificial generativa"` pasa porque 'inteligencia' (21 matches BD) + 'artificial' (5 matches) crean overlap suficiente aunque 'regulacion' y 'generativa' tengan 0 matches. El ratio real es 2/4=0.50, que supera el umbral de Capa 2.

**FP GAP #2: Capa 4 ratio_in_db trigger muy conservador.** Requiere `ratio_in_db <= 0.15` para penalizar — si 2 de 4 terminos existen, ratio=0.50 → no penaliza. Deberia ser ~0.40 para capturar casos donde la mayoria de terminos NO existen.

**FP GAP #3: exact_id matchea numeros parciales.** `"Decreto Supremo 999-9999-MINSA"` activa `has_exact_id=True` y busca "999" en DB. 3 normas contienen "999" en su numero → `found_in_db=True` → sin penalidad. Deberia requerir match del numero COMPLETO (999-9999) o al menos prefijo significativo.

**FN GAP #1: Capa 5 penaliza combinaciones validas.** `"derecho laboral"` (datos reales) recibe -0.50 de Capa 5 porque 'derecho' y 'laboral' no co-existen en ningun resultado individual, aunque ambos existen por separado en la BD. Capa 5 deberia verificar coexistencia en la BD (no solo en resultados) antes de penalizar.

**FN GAP #2: Stemming/singular-plural.** `"designacion"` no matchea `"designaciones"` (plural en BD). LIKE '%designacion%' NO cubre 'designaciones' porque la palabra base es distinta. FTS5 con stemming espanol resolveria esto.

## Bug conocido: Qdrant score 0.00 para queries con numeros exactos

El modelo `paraphrase-multilingual-MiniLM-L12-v2` (384d) genera vectores para queries como "ley 31980" que no matchean semanticamente con vectores de normas que tienen sumillas descriptivas. El numero "31980" no aparece en la sumilla de la mayoria de documentos vectorizados.

**Esto es esperado:** Qdrant busca similitud semantica, no numeros exactos. No es un bug, es una limitacion arquitectonica. Los numeros exactos deben buscarse en SQLite (columna `numero`).

**Verificacion inmediata:** Probar query directamente contra Qdrant REST API:
```bash
curl -s -X POST http://localhost:6333/collections/normas_peruano_semantic/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [...], "limit": 5, "with_payload": true}'
```
Si Qdrant directo da 0.00, es el modelo. Si da scores > 0, el bug esta en `search_qdrant()` del API.

## Batería de pruebas RAG (80+ queries)

Para validar el sistema completo se usa un script (`test_battery_70.py`) que ejecuta 80 queries categorizadas y monitorea cada artefacto:

### Categorías
1. **TRAPS** (20): Temas inexistentes → deben caer a web fallback
2. **TRAPS CON NUMERO** (10): IDs ficticios → deben caer a web
3. **CONTROLES** (10): Temas existentes → deben retornar datos locales
4. **CONTROLES CON NUMERO** (10): IDs reales → deben retornar datos locales
5. **BORDES SEMANTICOS** (20): Queries genéricas → Qdrant debería complementar
6. **MIXTAS** (10): Términos existentes + inexistentes

### Métricas por query
- `sqlite_count`, `qdrant_count`, `neo4j_count`, `graph_count`
- `max_sqlite_rel`, `max_qdrant_rel`, `max_neo4j_rel`, `max_graph_rel`
- `confidence`, `negation_detected`, `web_used`, `timing_ms`
- `top_source` (qué artefacto ganó el ranking)

### Reporte automático
El script genera `reports/test_battery_70_YYYY-MM-DD.json` con resumen estadístico por categoría + queries individuales. Luego se produce un reporte markdown en `reports/reporte_bateria_80_queries_YYYY-MM-DD.md` con hallazgos, problemas priorizados y recomendaciones.

### Problemas conocidos detectados en 80 queries
1. **SQLite LIKE pierde números exactos**: "ley 31980", "ley 31984" → SQLite retorna 0 aunque existan. Debuggear con query directa `SELECT * FROM normas WHERE numero LIKE '%31980%'`.
2. **Qdrant score 0.00 en queries semánticas**: El modelo `paraphrase-multilingual-MiniLM-L12-v2` no capta sinónimos legales peruanos para queries sin número exacto.
3. **Graph traversal inactivo**: Entidades extraídas no matchean nodos Neo4j → verificar match por label.
4. **Queries mixtas contaminadas**: Término inexistente en query mixta domina todo el ranking.

## Pitfall: Background process buffering impide monitoreo en tiempo real

**Problema:** Python scripts ejecutados via `terminal(background=true)` no muestran stdout hasta que terminan, incluso con `PYTHONUNBUFFERED=1` y flag `-u`. El output se acumula en el buffer y solo aparece en `process(action='log')` al finalizar.

**Sintoma:** `process(action='poll')` muestra `output_preview: ""` durante 30+ segundos aunque el script este corriendo y produciendo output.

**Solucion:** Usar `execute_code` para scripts Python largos que necesitan monitoreo en tiempo real. `execute_code` captura stdout incrementalmente y permite ver progreso. El codigo corre en un sandbox con acceso a `from hermes_tools import terminal, ...`.

**Ejemplo de bateria de pruebas:**
```python
# En vez de: terminal(background=true, command="python3 test_battery.py")
# Usar: execute_code con el codigo inline o importado

import requests, time, json
API = "http://localhost:8000/query"
results = []
for i, (qid, question) in enumerate(QUERIES, 1):
    resp = requests.post(API, json={"question": question, ...}, timeout=120)
    results.append({"id": qid, "conf": resp.json()['confidence'], ...})
    print(f"[{i}/{len(QUERIES)}] {qid} conf={results[-1]['conf']:.2f}")  # Visible incrementalmente
```

**Performance:** execute_code tiene timeout de 5 minutos y 50KB stdout cap. Para 70 queries con LLM (~1.5s c/u), el tiempo total es ~100-120s sin problemas.

**Cuando usar cada enfoque:**
- `terminal(background=true)` → servers, watchers, procesos que no necesitan monitoreo mid-progress
- `execute_code` → scripts de prueba, baterias, analisis que requieren feedback incremental
- `terminal()` foreground → comandos rapidos (<60s) donde el output completo es necesario

Las normas legales como "Ley 32108" tienen su identificación numérica (`numero = "Nº 32108"`) como campo separado, NO en la sumilla ni título. Si la búsqueda SQLite solo busca en `sumilla, titulo, materia`, una consulta como "Ley 32108" **no encontrará la norma localmente**, activando fallback web aunque la base la tenga.

**Fix obligatorio:** Incluir `numero` tanto en WHERE como en scoring:

```python
# WHERE (para encontrar resultados)
where_parts.append(f"LOWER(numero) LIKE '%{t}%'")

# SCORING (para rankearlos)
score_parts.append(f"(CASE WHEN LOWER(numero) LIKE '%{t}%' THEN 5 ELSE 0 END)")
```

El peso de `numero` debe ser 5 (igual que emisor) porque un match en numero es determinístico para IDs exactos.

## Pitfall: confidence_score no refleja match exacto en SQLite

Cuando la pregunta tiene un ID exacto (ej. "Ley 32108") y SQLite encuentra la norma por ese número, el confidence_score puede seguir siendo bajo (~0.04-0.08) porque la fórmula pondera Qdrant scores semánticos (que para IDs exactos son bajos). Esto causa que el fallback web se active INNECESARIAMENTE.

**Fix:** Agregar override en confidence_score: si `has_exact_id=True` AND `sqlite_exact_boost>0` AND `sqlite_count>0` → confianza mínima de 0.85 (por encima del umbral 0.75):

```python
# ── Override: si hay ID exacto Y match confirmado en SQLite ──
if has_exact_id and sqlite_exact_boost > 0 and sqlite_count > 0:
    weighted = max(weighted, 0.85)
```

## Pitfall: Patrones de ID exacto confunden años con IDs

Una regex `\b\d{5}\b` usada para detectar IDs de normas matchea AÑOS (2024, 2025) como si fueran números de norma. Esto activa falsamente la penalidad de "ID exacto sin match".

**Fix:** Filtrar números que están en rango de años (2020-2035) antes de aplicar lógica de boost/penalty:

```python
nums_in_q = [n for n in nums_in_q_raw if not (2020 <= int(n) <= 2035)]
```

Y en la detección de patrones: asegurar que las expresiones regulares requieran un PREFIJO (ley, ds, rm, etc.) seguido de dígitos, no solo dígitos sueltos:

```python
exact_id_patterns = [
    r'\b(ley|decreto supremo|ds|resolución ministerial|rm|...|du)\s*[n°º#]*\s*\d{3,}',
]
```

## Pitfall: Groq ignora system prompt sobre frases prohibidas

Poner "NO uses frases como 'Lamentablemente'" en el system prompt NO es suficiente — Groq las sigue usando en ~91% de respuestas.

**Fix:** Poner la instrucción también en el USER prompt, con formato destacado:

```python
prompt = f"""
...
[INSTRUCCIONES OBLIGATORIAS — NO LAS IGNORES]
- NO uses frases como "Lamentablemente", "Basándome en los resultados", "Según los resultados de búsqueda"
- Responde DIRECTAMENTE con lo que encontraste. Enumera cada norma: tipo, número, fecha, emisor.
- Si hay [WEB] results, cítalos con su URL. NO digas que no tienes información.
"""
```

El system prompt debe ser igual de directo (lo mismo en paralelo). La combinación de ambos es efectiva.

## Mejora Inmediata: Sinónimos Legales + FTS5

Reemplazar LIKE %término% por FTS5 (BM25 ranking + stemming español) + diccionario de sinónimos:

```python
SINONIMOS_LEGALES = {
    "pia": ["presupuesto institucional de apertura", "presupuesto"],
    "minem": ["ministerio de energía y minas", "energía", "minas"],
    "bcrp": ["banco central de reserva", "banco central"],
    "mef": ["ministerio de economía y finanzas", "economía", "finanzas"],
    "plame": ["planilla única de pago", "planilla", "remuneración"],
    "rc": ["resolución de contraloría", "contraloría"],
    "rm": ["resolución ministerial", "ministerio"],
    "ds": ["decreto supremo", "presidencia"],
    "rsg": ["resolución de superintendencia", "superintendencia"],
}
```

FTS5 permite búsqueda rankeada (BM25), stemming en español y búsqueda por frase exacta.

## Mejora Mediano Plazo: Hybrid Search con Weight-tuning

Ajustar peso entre búsqueda vectorial y textual según tipo de consulta:
- Semántica ("¿qué son las designaciones?") → vectorial 0.8, textual 0.2
- Exacta ("DS 005-2024-MININTER") → vectorial 0.2, textual 0.8
- Mixta → 0.5 / 0.5

## Plan de Ingesta para años anteriores

Proyección para 5 años (2020-2024, ~108K normas):
| Componente | 1 año | 5 años |
|------------|-------|--------|
| SQLite | 65 MB | ~325 MB |
| Qdrant (3 colecciones) | ~5 GB | ~25 GB |
| Neo4j | ~1 GB | ~5 GB |
| Modelos | ~400 MB | ~400 MB |
| **Total** | **~6.5 GB** | **~30.5 GB** |

Disco ARCHVOS012 tiene 334 GB libres — el proyecto cabe 10 veces completo.
El pipeline de scraping por año toma ~3-5 días (batch nocturno).

## Validación externa y competitive research (27-abr-2026)

Investigación de 28 repos + 42 papers/artículos valida la arquitectura multi-store:
- **justicio** (⭐141): RAG BOE español — similar pero solo vector search, sin grafo ni defensa
- **Azure GraphRAG Legal** (⭐115): 500K casos US con vector+semantic ranking+GraphRAG en PostgreSQL
- **SAT-GraphRAG** (arXiv 2505.00039): Ontología jerárquica + temporal para normas, blueprint para Horizonte 3
- **Domain-Partitioned Hybrid RAG** (arXiv 2602.23371): Híbrido multi-fuente logra 70% vs 37.5% RAG-only
- **Legal RAG Bench** (arXiv 2603.01710): Metodología estándar de evaluación end-to-end

El Peruano es el ÚNICO proyecto open-source con SQL+vector+grafo+defensa adversarial+fallback web+sinónimos dominio. Reportes completos: `reports/evaluacion_arquitectura_2026-04-27.md` y `reports/investigacion_mercado_rag_legal_2026-04-27.md`.

## Roadmap Recomendado

Sprint 1 (semana 1): Fallback web + umbral de confianza (~4h)
Sprint 2 (semana 2): FTS5 + sinónimos + re-ranker cross-encoder (~1 día)
Sprint 3 (mes 2): Scraping 2020-2023 + re-poblar Qdrant/Neo4j (~1 semana)
Sprint 4 (mes 3, opcional): GraphRAG con GDS plugin + Leiden + resúmenes (~1 día)

## Limitaciones del sistema actual (no es un GraphRAG real)

El sistema actual es un RAG **híbrido multi-store** (SQLite + Qdrant + Neo4j), NO un GraphRAG completo. Diferencias clave:

- Neo4j se usa como base de grafos relacional (entidades "MENCIONA" a normas), sin algoritmos de grafo
- No hay **community detection** (Louvain/Leiden) para identificar comunidades temáticas de normas
- No hay **graph traversal** en el pipeline de query — no se expande el contexto navegando el grafo 2-3 saltos
- No hay **graph summarization** con LLM (el approach de Microsoft GraphRAG: resumir cada comunidad con LLM)
- El grafo es plano: solo relaciones directas (Norma)-[:MENCIONA]->(Persona|Organismo|Monto)

## Roadmap: evolucionar a GraphRAG completo

### Prioridad 1: Graph traversal en query pipeline
Después del retrieval inicial (SQLite + Qdrant), navegar el grafo Neo4j para encontrar conexiones indirectas:

```python
# Ejemplo: despues de encontrar norma N, expandir con vecinos de 2do grado
MATCH (n:Norma {slug: $slug})-[:MENCIONA]->(e:Persona)<-[:MENCIONA]-(related:Norma)
RETURN related LIMIT 5
```

Enriquecer el prompt con estas normas relacionadas como contexto adicional.

### Prioridad 2: Community detection
Ejecutar algoritmo Louvain/Leiden sobre el grafo Neo4j:

```cypher
CALL gds.louvain.write('norma-graph', {writeProperty: 'community'})
```

Usar las comunidades para reranking: si una norma candidate pertenece a la misma comunidad que normas ya relevantes, subir su score.

### Prioridad 3: LLM-powered graph summarization
Para cada comunidad detectada, usar Groq para generar resúmenes descriptivos:
- Temas principales de la comunidad
- Entidades clave (personas/organismos más mencionados)
- Relaciones dominantes
- Almacenar como propiedad `community_summary` en nodos o tabla separada en SQLite

### Prioridad 4: GraphRAG query pipeline completo
Pipeline integrado:
1. Retrieve inicial (SQLite LIKE + Qdrant semántico)
2. Expandir resultados con graph traversal (Neo4j, 2-3 saltos)
3. Rerank por comunidad si aplica
4. Generar respuesta con LLM usando contexto enriquecido (normas directas + relacionadas + resúmenes de comunidad)

### Prioridad 5: Dashboard de grafo interactivo
Agregar al dashboard Streamlit una sección con cytoscape.js o neovis.js:
- Visualización del subgrafo alrededor de una norma consultada
- Comunidades coloreadas
- Caminos de navegación entre normas, personas y organismos
- Tooltips con metadata de cada nodo

## Diagnóstico de salud real del sistema (NO confiar solo en /health)

El endpoint `/health` puede reportar `"✅"` para Neo4j aunque tenga **0 nodos** (solo verifica que el driver conecta, no que haya datos). Qdrant puede reportar `"✅"` aunque falle en cada query con Broken pipe (porque `/health` usa `urllib` no `requests`/httpx).

**Procedimiento de diagnóstico real:**

1. **Ejecutar 3+ queries reales** contra `/query` y revisar el campo `sources` en la respuesta JSON:
   ```python
   import urllib.request, json
   data = json.dumps({"question": "designacion de funcionarios", "top_k": 5}).encode()
   req = urllib.request.Request("http://localhost:8000/query", data=data,
       headers={"Content-Type": "application/json"})
   resp = urllib.request.urlopen(req, timeout=120)
   result = json.loads(resp.read().decode())
   print(result["sources"])  # ← Aquí se ven los errores reales
   ```

2. **Signos de alarma en sources:**
   - `"qdrant": {"error": "[Errno 32] Broken pipe"}` → Qdrant roto, no contribuye
   - `"neo4j": {"count": 0, ...}` o `"neo4j": {"error": ...}` → Neo4j vacío o roto
   - Solo aparece `"sqlite"` → sistema degradado a single-store textual
   - `"qdrant": {"count": 0}` (sin error) → colección vacía o query no matchea

3. **Verificar Neo4j directamente** (el health check es engañoso):
   ```bash
   # Via HTTP API (no requiere driver)
   curl -s -u neo4j:<NEO4J_PASSWORD> -H "Content-Type: application/json" \
     -d '{"statements":[{"statement":"MATCH (n) RETURN count(n) as total"}]}' \
     http://localhost:7474/db/neo4j/tx/commit
   ```
   Si `total: 0` → datos perdidos. Re-ejecutar migración.

4. **Verificar Qdrant directamente** (confirma si el error es del cliente o del servidor):
   ```bash
   curl -s -X POST http://localhost:6333/collections/normas_peruano_semantic/points/search \
     -H "Content-Type: application/json" \
     -d '{"vector": [...], "limit": 3, "with_payload": true}'
   ```
   Si Qdrant directo responde bien pero el API da Broken pipe → confirmado: conflicto asyncio/httpx. Aplicar fix de subproceso (Pitfall #10).

5. **Perfilar latencia por componente**: La respuesta de `/query` solo da `timing_ms` total. Para diagnóstico rápido, ejecutar el script y medir cada bloque con `time.time()` antes/después. O agregar temporalmente `timing_breakdown` al return del endpoint.

## Verificacion final
- Health: todos los servicios responden OK con timing
- **NUEVO**: 3+ queries reales con sources mostrando sqlite+qdrant+neo4j contribuyendo
- Search: resultados correctos con filtros combinados
- Query RAG: 9 resultados (3 por fuente SQLite+Qdrant+Neo4j)
- Norma detail: entidades del grafo visibles y correctas
- Stats: 21,584 normas, tipos disponibles, emisores, Qdrant pts, Neo4j nodos
- Dashboard: responde HTTP 200 con todos los graficos renderizados
- Sin errores de sintaxis Neo4j 5.x (COUNT{} vs size())
- Sin errores de thread-safety en SQLite
- **NUEVO**: Neo4j `MATCH (n) RETURN count(n)` > 0 (no confiar en health check)