---
name: building-rag-systems-with-multiple-stores
description: Build a production-grade RAG system integrating SQLite (structured data), Qdrant (vector search), and Neo4j (knowledge graph), with a FastAPI REST layer, Groq LLM for answer generation, and Streamlit dashboard.
category: software-development
---

# Building RAG Systems with Multiple Data Stores

## When to use
You need to build or reconstruct a multi-component RAG system with:
- SQLite for structured/relational data
- Qdrant for semantic/vector search
- Neo4j for entity relationships and graph traversal
- Groq LLM (via API) for natural language answer generation
- FastAPI REST layer
- Streamlit monitoring dashboard

## Steps

### 1. Discover & Restore Project Data

Check these locations in order:
1. Active filesystem (find . -name "*.db")
2. Backup archives (find . -name "*.tar.gz")
3. Trash/recycle bin
4. External drives (/media/...)
5. Docker volumes

For tar backups, always list contents before extracting:
```
tar tzf backup.tar.gz | grep -v "node4j_data/" | grep -v "qdrant_storage/"
```

### 2. Verify Existing Infrastructure

Check Docker containers:
```
docker ps
```

Get Neo4j auth credentials:
```
docker inspect neo4j_peruano --format '{{range .Config.Env}}{{println .}}{{end}}' | grep NEO4J_AUTH
```

### 3. Check SQLite Schema First

Always verify the actual table schema — column names in code may not match:
```
python3 -c "
import sqlite3
db = sqlite3.connect('data/normas_2024.db')
cols = [r[1] for r in db.execute('PRAGMA table_info(normas)').fetchall()]
print(cols)
"
```

**Pitfall**: Column `contenido` may not exist. Use `sumilla`, `titulo`, `materia` instead.

### 4. Load Neo4j from SQLite (Migration)

Docker volume data is unreliable. Build a migration script from SQLite:
1. Clean: MATCH (n) DETACH DELETE n
2. Constraint: CREATE CONSTRAINT FOR (n:Norma) REQUIRE n.id IS UNIQUE
3. Indexes on Norma(id), Norma(tipo_norma), Entidad(nombre)
4. Batch of 200 rows from SQLite
5. Nodes:
   - (:Norma {id, tipo_norma, numero, fecha, emisor, sumilla, materia})
   - (:Entidad:Organismo {nombre})
   - (:Entidad:Persona {nombre})
   - (:Entidad:Monto {nombre, valor})
6. Rels:
   - (:Norma)-[:EMITIDA_POR]->(:Entidad:Organismo)
   - (:Norma)-[:MENCIONA]->(:Entidad)

### 5. FastAPI — Thread Safety

```python
# SQLite: FRESH connection per request (NOT singleton!)
def get_sqlite():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Qdrant: thread-safe singleton
def get_qdrant():
    global _qdrant
    if _qdrant is None:
        from qdrant_client import QdrantClient
        _qdrant = QdrantClient(url=QDRANT_URL)
    return _qdrant

# Neo4j: thread-safe singleton
def get_neo4j():
    global _neo4j
    if _neo4j is None:
        from neo4j import GraphDatabase
        _neo4j = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    return _neo4j

# Embedding model: thread-safe singleton
def get_encoder():
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        _encoder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _encoder
```

**Pitfall**: Qdrant API changed. Use `query_points()` not `search()` in v1.10+.

### 6. SQLite Scoring with Relevance

Weighted scoring by field:
```python
score_parts = []
for t in terms:
    if len(t) < 3: continue
    score_parts.append(f"(CASE WHEN LOWER(emisor) LIKE '%%{t}%%' THEN 5 ELSE 0 END)")
    score_parts.append(f"(CASE WHEN LOWER(titulo) LIKE '%%{t}%%' THEN 4 ELSE 0 END)")
    score_parts.append(f"(CASE WHEN LOWER(sumilla) LIKE '%%{t}%%' THEN 3 ELSE 0 END)")
    score_parts.append(f"(CASE WHEN LOWER(materia) LIKE '%%{t}%%' THEN 2 ELSE 0 END)")
score_clause = " + ".join(score_parts)

qry = f"SELECT id, ..., ({score_clause}) as score FROM normas WHERE ... ORDER BY score DESC LIMIT {top_k}"

max_score = max(r.get('score',0) for r in results)
for r in results:
    r['relevance'] = round(r['score'] / max(max_score, 1), 4)
```

**Pitfall — Qdrant double-scoring in blend**: When both `relevance` (0.50 weight) and `_qdrant_score` (0.30 weight) carry the same `h.score` value, Qdrant gets 0.80 effective weight vs SQLite's 0.50. This drowns correct SQLite results with Qdrant semantic noise. Fix: set `relevance=0.0` for Qdrant results, keeping only `_qdrant_score` for the blend.

**FTS5 stop words for Spanish**: BM25 OR queries drown rare terms when common words dominate. Filter 130+ Spanish stop words (articles, prepositions, common verbs, domain-generic terms like 'norma', 'ley', 'articulo') from FTS5 query tokens. Boost rare terms (len≥5, non-stop) by searching them separately with quoted phrases and forcing results to top.

### 7. Query Pipeline — 3-Source Fusion

1. **SQLite**: FTS5 full-text with BM25 ranking + stop-word filtering + rare-term boosting. Fast (<2ms).
2. **Qdrant**: Semantic search via embeddings. Set `relevance=0.0` to avoid double-scoring in blend. (~100ms after warmup)
3. **Neo4j**: Entity relationship traversal

Deduplicate by ID, sort by relevance:
```python
seen = set()
unique = []
for r in all_results:
    rid = r.get("id", "")
    if rid and rid not in seen:
        seen.add(rid)
        unique.append(r)
unique.sort(key=lambda x: x.get('relevance', 0), reverse=True)
```

### 8. Embedding Model — Warm-up

First request loads model (~12s with download). Singleton pattern caches in memory. Warm up in startup:
```python
@app.on_event("startup")
async def warmup():
    get_encoder()
```

After warmup: ~130ms per query.

### 9. Groq LLM Integration

Generate natural language answers from results. Key findings from real-world integration:

**Model selection**: The models `llama3-70b-8192` and `mixtral-8x7b-32768` are decommissioned. Use `llama-3.3-70b-versatile` or `llama-3.1-8b-instant`. To discover available models:

```bash
curl -s --http1.1 -X GET "https://api.groq.com/openai/v1/models" \
  -H "Authorization: Bearer $GROQ_API_KEY" | python3 -c "
import sys,json
models = json.load(sys.stdin)['data']
for m in sorted(models, key=lambda x: x.get('created',0), reverse=True):
    print(m['id'])
"
```

**HTTP protocol**: Python's `urllib.request` uses HTTP/2 by default, and the Groq API rejects POST requests over HTTP/2 (error 43: "upstream connect error or disconnect/reset before headers"). Always use the `requests` library — it defaults to HTTP/1.1 and works reliably. For curl testing, always add `--http1.1` flag.

**If the LLM answer field comes back empty but no error is shown in logs**, the most likely culprit is HTTP/2 vs HTTP/1.1 protocol mismatch — not an API key issue. The `urllib.request` + `HTTP1Handler` workaround is unreliable (can still fail). Just use `requests`.

**Code structure** (use `requests`, never `urllib`):

**Streaming SSE (preferred for production)** — The `requests.post()` blocking call makes users wait 3-5s in silence. Use Groq's native `stream=True` + `AsyncGroq` + FastAPI `StreamingResponse` (SSE) to achieve **TTFT of 0.34s** — tokens appear instantly while the full response streams. Full pattern, benchmarks, and parallel-search integration in `references/rag-performance-optimization.md`.

**Code structure — non-streaming fallback** (use value from env var, never hardcode):
```python
def generate_answer(question, profile, results):
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return ""
    import requests
    system = SYSTEM_PROMPTS.get(profile, SYSTEM_PROMPTS["ciudadano"])
    context = "\n".join(
        f"- [{r['source']}] {r['tipo']} {r['numero']} ..."
        for r in results[:6]
    )
    prompt = f"Pregunta: {question}\nResultados: {context}\nResponde usando SOLO los resultados."
    resp = requests.post(GROQ_URL, json={
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1024
    }, headers={"Authorization": f"Bearer {key}"}, timeout=40)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
```

**Timeout**: Set 40s+ timeout. First cold-start Groq call can be slow.

**Performance optimization**: See `references/rag-performance-optimization.md` for streaming SSE patterns, parallel search (1.65x speedup with asyncio.gather), model benchmarks (5 models tested), 2-level routing (8B for BASIC, 70B for complex), and the definitive Rust evaluation (NOT worth it).

### 10. Web Fallback (Serper) with Confidence Threshold

When local multi-source results are insufficient, fall back to web search via Serper API. This handles queries about recent events or topics not yet indexed.

**Architecture**: After deduplication, compute a confidence score (0-1). If below threshold, call Serper and prepend web results to the LLM prompt.

#### Confidence Score Formula

```python
def confidence_score(results: list) -> float:
    if not results:
        return 0.0
    # Calidad semantica Qdrant (0-0.6) — el indicador mas fiable
    qdrant_scores = [r["relevance"] for r in results if r.get("source") == "qdrant"]
    max_qdrant = max(qdrant_scores) if qdrant_scores else 0.0
    avg_qdrant = sum(qdrant_scores) / len(qdrant_scores) if qdrant_scores else 0.0
    semantic_quality = (max_qdrant * 0.7 + avg_qdrant * 0.3) * 0.6
    # Cantidad (0-0.2)
    count_score = min(len(results) / 15.0, 1.0) * 0.2
    # SQLite boost (0-0.1)
    sqlite_boost = 0.1 if len([r for r in results if r.get("source") == "sqlite"]) > 2 else 0.0
    # Neo4j boost (0-0.1)
    neo4j_boost = min(len([r for r in results if r.get("source") == "neo4j"]) * 0.03, 0.1)
    return round(min(semantic_quality + count_score + sqlite_boost + neo4j_boost, 1.0), 4)
```

**Threshold tuning**: Start at 0.75. Adjust based on:
- Too many false negatives (local results are good but fallback triggers) → lower threshold
- Too many false positives (bad local results pass without fallback) → raise threshold or adjust weights

**Known issue**: Qdrant can find semantically similar results that are tangentially relevant, inflating confidence. This is acceptable — Groq will still correctly report "no information found" if results don't actually answer the question.

#### Serper Web Search

```python
SERPER_URL = "https://google.serper.dev/search"

def search_web_fallback(question: str, top_k: int = 5) -> list:
    if not SERPER_API_KEY:
        return []
    import requests
    sites = ["site:diariooficial.elperuano.pe", "site:gob.pe"]
    results = []
    for site in sites:
        resp = requests.post(SERPER_URL, json={"q": f"{site} {question}", "num": top_k},
            headers={"X-API-KEY": SERPER_API_KEY}, timeout=15)
        for r in resp.json().get("organic", []):
            results.append({
                "id": None, "tipo": "WEB", "numero": "",
                "sumilla": r.get("snippet", ""),
                "source": "serper_web", "relevance": 0.15,
                "url": r.get("link", ""), "titulo_web": r.get("title", ""),
            })
    # Deduplicar por URL
    seen = set()
    return [r for r in results if r.get("url") and r["url"] not in seen and not seen.add(r["url"])][:top_k]
```

**Key insight — Local priority with web enrichment**: When fallback activates, web results should be APPENDED (not prepended) to preserve local entity enrichment. Extract names and amounts from Serper snippets to give web results context. Set web relevance lower (0.30) than local so the LLM prioritizes local data.

```python
if confidence < CONFIDENCE_THRESHOLD:
    web_results = search_web_fallback(question, top_k)
    if web_results:
        # Enrich web results from snippet text
        for wr in web_results[:3]:
            snippet = wr.get("sumilla", "") + " " + wr.get("titulo_web", "")
            names = re.findall(r'[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{5,40}', snippet)
            if names:
                wr["_funcionarios_web"] = [n.strip() for n in names[:3] if len(n.strip()) > 10]
            wr["relevance"] = 0.30  # Lower than local
        # APPEND, not prepend — local priority
        unique_results = unique_results + web_results[:3]
```

#### Qdrant Retry for "Broken Pipe"

Qdrant's REST client occasionally throws `[Errno 32] Broken pipe`. Two distinct causes:

1. **Asyncio event loop conflict** — QdrantClient inside uvicorn/FastAPI. Use REST API via `requests.post()` instead of `QdrantClient`.

2. **Stale uvicorn process** — The API process accumulates corrupted HTTP connections over hours/days. Symptoms: health check times out, curl hangs, `lsof` shows CLOSE_WAIT connections. The old process often has TWO PIDs (bash wrapper + python child) — `pkill` alone won't catch both, and `lsof` only shows the listener. Fix:
```bash
# Kill ALL related processes (wrapper + python child + listener)
ps aux | grep 'api_rest.py' | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
sleep 2
# Verify port is free: lsof -i :8000 should show nothing
# Restart with terminal(background=true), never use & in foreground commands
```
**Critical**: Use `terminal(background=true)` to restart the API. Never use `&` in foreground terminal commands — Hermes blocks this pattern. After restart, verify with `curl -s --max-time 5 http://localhost:8000/health` — should return in <2s. First query after restart takes 4-5s (cold Groq start).
**Diagnostic**: If Qdrant works via direct curl but fails through the API (even with `requests`), the uvicorn process is stale. A full restart takes <5 seconds and resolves it.

3-attempt retry for transient failures:
```python
for attempt in range(3):
    try:
        hits = qclient.query_points(collection_name="...", query=vec, ...).points
        break
    except Exception as qe:
        if "broken pipe" in str(qe).lower() and attempt < 2:
            time.sleep(1)
        else:
            raise
```

#### Prompt Formatting for Web Results

Update `build_llm_prompt` to handle both local and web result formats:

```python
for r in results[:6]:
    if r.get("source") == "serper_web":
        context_parts.append(
            f"- [WEB] {r.get('titulo_web','')} "
            f"| Fuente: {r.get('url','')} "
            f"| Contenido: {r.get('sumilla','')[:250]}"
        )
    else:
        context_parts.append(
            f"- [{r['source']}] {r['tipo']} {r['numero']} ({r.get('fecha','')}) "
            f"| Emisor: {r.get('emisor','')} "
            f"| Contenido: {r.get('sumilla','')[:200]}"
        )
```

#### Response Enrichment

Expose confidence and fallback status in API response for debugging:
```python
return {
    ...
    "confidence": confidence,
    "web_fallback_used": len(web_results) > 0,
    ...
}
```

### 11. Testing Pipeline with 5 Questions

Use this test script to validate the full pipeline:

```python
import requests, json

QUESTIONS = [
    {"q": "designacion de funcionarios en salud publica 2024", "profile": "ciudadano", "desc": "ALTA cobertura local"},
    {"q": "regimen disciplinario de la policia nacional del peru", "profile": "abogado", "desc": "MEDIA cobertura local"},
    {"q": "bonificacion por preparacion academica en educacion 2024", "profile": "docente", "desc": "BAJA cobertura local"},
    {"q": "nombramiento de nuevo ministro de economia 2025", "profile": "periodista", "desc": "BAJA cobertura local"},
    {"q": "impuesto a la renta de tercera categoria 2025 reajuste", "profile": "contador", "desc": "BAJA cobertura local"},
]

for item in QUESTIONS:
    resp = requests.post("http://localhost:8000/query", json={
        "question": item["q"], "profile": item["profile"], "top_k": 5
    }, timeout=60)
    data = resp.json()
    print(f"{item['desc']:30s} | conf={data['confidence']} | fallback={data['web_fallback_used']}")
    # Check answer quality
    if "no encontr" in data.get("answer","").lower():
        print(f"  WARNING: Groq found no relevant info despite {data['total_results']} results")
```

#### What to check in test results
- **Confidence > threshold + fallback=False**: Good — local sources sufficient
- **Confidence < threshold + fallback=True**: Good — fallback activated correctly
- **Confidence > threshold + fallback=False + Groq says "no info"**: False positive — confidence formula needs tuning (Qdrant weight too high)
- **Confidence < threshold + fallback=True + web results present but Groq ignores them**: Web results not reaching prompt — check prepend logic

Generate a markdown report from test results for documentation.

### 12. Complete Query Endpoint

The `/query` pipeline:
1. Parse question into search terms
2. SQLite text search with weighted scoring
3. Qdrant semantic search via embeddings (with retry)
4. Neo4j entity relationship traversal
5. Collect, deduplicate, sort by relevance
6. Compute confidence score, fallback to Serper if below threshold
7. Pass top results to Groq for answer generation
8. Return: `{question, profile, total_results, results, sources, confidence, web_fallback_used, answer, timing_ms}`

### 13. Web UI — Serving a Single-Page App Alongside the API

To serve a web UI at `GET /` without breaking API endpoints:
- **DO NOT use** `app.mount("/", StaticFiles(...))` — this intercepts ALL paths including `/health`, `/query`, `/stats`.
- **DO use** `@app.get("/", include_in_schema=False)` with `HTMLResponse(INDEX_HTML)`.
- Preload the HTML at module startup (read from file) for zero-latency serving.

Full pattern in `references/serving-web-ui-with-fastapi.md`, including: mount-at-subpath alternative, lazy FileResponse for large files, CORS setup, and startup-loading best practices.

### 11. Streamlit Dashboard

Call FastAPI endpoints, not databases directly:
```python
import urllib.request, json
def api_get(endpoint):
    req = urllib.request.Request(f"http://localhost:8000{endpoint}")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())
```

Sections: KPIs, charts (bar/pie/area), Neo4j stats, Qdrant collections, recent norms.

**Pitfall**: `use_container_width=True` -> `width='stretch'` in Streamlit 1.40+.

### 12. Endpoints

```
GET  /health       — All services status + counts
POST /query        — 3-source RAG + Groq answer
GET  /normas/{id:path}  — Full detail + Neo4j entities
GET  /search       — SQLite filtered search
GET  /stats        — System statistics
```

**Pitfall**: Use `{id:path}` for IDs with slashes (e.g. `2024-01-01/2248850-1`).

### 14. SQL Aggregate COUNT for Temporal/Count Queries

When the RAG receives count-type queries ("cuantas normas en enero 2024"), returning flat result rows to the LLM gives poor answers. Instead, execute a SQL `COUNT(*)` with GROUP BY and inject the result into the prompt.

**Trigger**: Query Classifier detects type C (TEMPORAL) with `skip_count_queries=True` AND the question contains count words (`cuantas`, `cuantos`, `total`, `conteo`).

**Dynamic WHERE construction from classifier entities**:

```python
_count_data = None
if strategy.get('skip_count_queries') and any(w in q_lower for w in ['cuantas','cuantos','total']):
    ent = classification.get('entities', {})
    where_parts = []
    
    # 1. Tipo de norma — keyword matching with accent-safe patterns
    for kw, sql_expr in [
        ('resolucion ministerial', "tipo_norma LIKE '%esoluci%n%inisterial%'"),
        ('resoluciones ministeriales', "tipo_norma LIKE '%esoluci%n%inisterial%'"),
        ('decreto supremo',         "tipo_norma LIKE '%ecreto%upremo%'"),
        ('ley',                     "LOWER(tipo_norma) = 'ley'"),
        ('leyes',                   "LOWER(tipo_norma) = 'ley'"),
    ]:
        if kw in q_lower:
            where_parts.append(sql_expr)
            break
    
    # 2. Emisor from classifier entities
    if ent.get('emisor'):
        for em in ent['emisor']:
            where_parts.append(f"LOWER(emisor) LIKE '%{em.lower()}%'")
    
    # 3. Year
    if ent.get('year'):
        where_parts.append(f"fecha_publicacion LIKE '{ent[\"year\"][0]}-%'")
    
    # 4. Month — name to number mapping
    if ent.get('mes'):
        mes_map = {'enero':'01','febrero':'02','marzo':'03','abril':'04',
                   'mayo':'05','junio':'06','julio':'07','agosto':'08',
                   'septiembre':'09','setiembre':'09','octubre':'10',
                   'noviembre':'11','diciembre':'12'}
        mes_num = mes_map.get(ent['mes'][0], '')
        if mes_num:
            yr = ent.get('year', ['2024'])[0] if ent.get('year') else '2024'
            where_parts.append(f"fecha_publicacion LIKE '{yr}-{mes_num}%'")
    
    # 5. Trimestre
    trim_match = re.search(r'(primer|segundo|tercer|cuarto)\s*trimestre', q_lower)
    if trim_match:
        yr = ent.get('year', ['2024'])[0] if ent.get('year') else '2024'
        trim_map = {'primer': ('01','03'), 'segundo': ('04','06'),
                    'tercer': ('07','09'), 'cuarto': ('10','12')}
        tr = trim_map.get(trim_match.group(1), ('01','12'))
        where_parts.append(f"fecha_publicacion >= '{yr}-{tr[0]}-01' "
                          f"AND fecha_publicacion <= '{yr}-{tr[1]}-31'")
    
    # 6. Materia/tema — ONLY if no other filters exist (guard pattern)
    if not where_parts:
        q_words = [w for w in q_lower.split() if len(w) >= 4 
                   and w not in ('cuantas','cuantos','normas','sobre','2024')]
        if q_words:
            materia = " OR ".join([f"LOWER(sumilla) LIKE '%{w}%'" for w in q_words[:3]])
            where_parts.append(f"({materia})")
    
    where = " AND ".join(where_parts) if where_parts else "1=1"
    total = db.execute(f"SELECT COUNT(*) FROM normas WHERE {where}").fetchone()[0]
    groups = db.execute(f"SELECT tipo_norma, COUNT(*) as cnt FROM normas "
                        f"WHERE {where} GROUP BY tipo_norma ORDER BY cnt DESC LIMIT 10").fetchall()
```

**Pitfall — Accent handling**: The database may store "RESOLUCIÓN MINISTERIAL" (with accent) but the query uses "resolucion" (without). A `LOWER(tipo_norma) LIKE '%resolucion ministerial%'` finds 0 results. Use patterns that skip the accented characters: `LIKE '%esoluci%n%inisterial%'` matches both "RESOLUCIÓN" and "RESOLUCION".

**Pitfall — Materia filter interference**: Adding sumilla-based keyword filters as AND conditions with type/date filters severely restricts results. For example, `tipo LIKE '%RM%' AND sumilla LIKE '%marzo%'` finds only 2 results when there are 327 RMs in March (most RM sumillas don't contain "marzo"). Solution: **only add materia filters when no stronger filters (type, date, emisor) are present**.

**Pitfall — Double-LIKE wrapping**: When the keyword mapping uses pre-built SQL expressions like `"tipo_norma LIKE '%esoluci%n%inisterial%'"`, do NOT wrap them again in `f"LOWER(tipo_norma) LIKE '%{expr}%'"`. Use `where_parts.append(expr)` directly.

**Prompt injection** — Include COUNT data before result context so the LLM can give numeric answers. In the El Peruano RAG codebase, this is done by passing `sources` to `_build_context(results, sources=None)` which prepends a `[DATOS AGREGADOS]` block when `sql_count` exists:

```python
# api_rest.py — _build_context()
if sources and "sql_count" in sources:
    sc = sources["sql_count"]
    count_header = f"[DATOS AGREGADOS]\nTotal normas encontradas: {sc.get('total', '?')}\n"
    if sc.get('breakdown'):
        count_header += "Desglose por tipo:\n"
        for g in sc['breakdown'][:7]:
            count_header += f"  - {g['tipo_norma']}: {g['cnt']}\n"
    context_parts.append(count_header)

# Both generate_answer() and generate_answer_stream() pass sources:
context = _build_context(results, sources)
```

```python
count_info = ""
if sql_count and sql_count.get("total", 0) > 0:
    count_info = f"\n[CONTEO EXACTO DESDE BASE DE DATOS]\nTotal: {sql_count['total']}\n"
    for g in sql_count.get("breakdown", [])[:8]:
        count_info += f"  - {g['tipo_norma']}: {g['cnt']}\n"

prompt = f"""...
Resultados de búsqueda:
{count_info}{context}
..."""
```

**Result example**: "cuantas RM en marzo 2024" → total=327, breakdown by tipo_norma. The LLM can now answer "Se encontraron 327 resoluciones ministeriales en marzo 2024."

### 15. Response Validator Integration

Wire a `ResponseValidator` into the `/query` pipeline to detect hallucinations and unsupported claims.

**Instantiation** (lazy singleton):
```python
_validator = None
def get_validator():
    global _validator
    if _validator is None:
        from response_validator import ResponseValidator
        _validator = ResponseValidator(use_llm=False)  # heuristic only, no extra LLM call
    return _validator
```

**Integration point** — after LLM answer generation:
```python
llm_answer = generate_answer(question, profile, results, sources)

# Validate the answer against sources
validation_result = None
try:
    val = get_validator()
    if val and llm_answer:
        vresult = val.validar(llm_answer, results, question)
        validation_result = {
            "validated": vresult.validada,
            "confidence": vresult.confianza,
            "issues": vresult.problemas,
            "metrics": vresult.metricas
        }
except Exception as e:
    logger.warning(f"[Validator] error: {e}")

# Include in response
return {
    ...
    "response_validation": validation_result
}
```

**Pitfall — Validator false positives**: The validator treats years (2020, 2021) as norma numbers AND confuses law numbers ("Ley 32108") with monetary amounts ($32,108). Two fixes needed:
1. Exclude year-like numbers (2020-2035) from norma detection
2. Exclude numbers preceded by norm prefixes (Ley, DL, DS, RM, N°) from monto detection:
```python
norm_pattern = r'(?:Ley|DL|DS|RM|RS|RD|RE|N[°º])\s*' + re.escape(match)
if re.search(norm_pattern, texto, re.IGNORECASE):
    continue  # Not a monto, it's a norm number
```

### 16. Query Classifier — Cascade Order Matters

When implementing a query classifier cascade, the order of checks determines accuracy:

**Correct cascade** (validated on El Peruano RAG, 93% accuracy):
1. **H** — Adversarial (security first)
2. **A** — ID Exacto (deterministic patterns)
3. **G** — Modificaciones (specific action verbs)
4. **D** — Emisor+Accion (entity+verb, BEFORE temporal)
5. **E** — Acronimo (short queries, BEFORE temporal)
6. **C** — Temporal (catch-all for dates, only if no stronger signal)
7. **F** — Narrativa (long questions, structural patterns)
8. **B** — Semantica (fallback)

**Key insight**: D and E must be checked BEFORE C. If C is checked first, any query containing a year (2024) will be classified as TEMPORAL even if it has clear entity/acronym signals. Example: "SUNAT y tributacion 2024" → C without this fix, E with it.

**Pattern flexibility**: Use flexible regex patterns that handle plurals and word boundaries correctly:
- `modificaci[oó]n(?:es)?` matches both "modificación" and "modificaciones"
- `derogad[ao]s?` matches "derogada", "derogado", "derogadas"
- Drop trailing `\b` for words that may be substrings of plurals

### 17. Final Verification

```
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question":"test","profile":"abogado"}'
```

Expected timing:
- Health: <100ms
- Search: <5ms
- Query (no LLM): ~130ms
- Query (with Groq): ~1500-3000ms
- Stats: <50ms

### 18. Entity Enrichment with Role Inference

When Groq Batch API extracts structured fields (`funcionarios`, `entidades`, `montos`), they end up in `norma_entities` but a flat list of names doesn't tell the LLM WHO does WHAT. Infer roles from sumilla keywords:

**Pattern**: `designa/nombra` → designado, `autorizan viaje` → viajero, `disolución` → administrador, `prorroga/emergencia` → firmante del decreto.

**Key rule**: The first funcionario in the list is usually the signer/approver, not the subject. Subsequent funcionarios are the subjects (designees, travelers, administrators).

**Impact**: Resolves persona/monto questions that previously failed despite having the data. See `references/groq-batch-extraction-and-enrichment.md`.

### 20. Regex-Based Post-Hoc Structured Extraction

When the extraction pipeline misses key structured fields (DNIs, registration numbers, internal dates, URLs, specific article references), add a post-hoc regex extractor that runs on `texto_completo` before building the LLM context. Extracts 10 categories with pure Python regex — zero cost, sub-millisecond per document.

Inject extracted fields as tagged lines (`DNIs: 06203134, 46238948`) BEFORE the raw text in the LLM context. Combined with expanding `texto_completo[:2000]`→`[:4000]`, this resolves gaps where data exists in the text but the LLM can't find it in narrative prose.

Full implementation and integration pattern in `references/regex-structured-extraction-from-full-text.md`.

When a battery of legal questions produces "no se encontró" answers despite norms being in the database, categorize failures by the TYPE of data missing:

| Category | Keywords in question | Typical fix |
|----------|---------------------|-------------|
| PERSONA | quién, persona, firma, ministro, administrador | Entity enrichment + role inference |
| MONTO | cuánto, monto, valor, viático, tasación | Entity enrichment + monto extraction |
| FECHA/PLAZO | cuándo, fecha, día, plazo, vigencia | Full text search (FTS5) |
| UBICACION | dónde, distrito, ciudad, departamento | Full text search + entity enrichment |
| CANTIDAD | cuántos, número de, área, m2, distritos | Full text search |
| CAUSAL/ARTICULO | causal, delito, motivo, artículo | Full text search (FTS5) |

**Methodology**: Run battery, extract all failing answers, categorize by keyword matching, then apply the appropriate fix per category. This turns a vague "system doesn't work" into a specific action plan.

**Real case (El Peruano RAG, 55 questions across 3 batteries)**: 25 failures categorized → 9 PERSONA, 5 MONTO, 3 FECHA, 3 CAUSAL, 1 CANTIDAD, 1 UBICACION. Entity enrichment + text search resolved ~70% of failures.

---

## Related Components & Advanced Topics

This umbrella covers the full lifecycle. The sections below summarize specialized topics; full detail is in `references/`.

### Cloud-First RAG Architecture
Pattern for building RAG on low-RAM (8-16GB) machines without GPU. Local embeddings (bge-m3 CPU) + cloud LLM (DeepSeek/Groq) + Streamlit UI. Stack: MarkItDown → bge-m3 → Qdrant file mode → SQLite FTS5 → DeepSeek API. Cost: $0-3/month. See `references/cloud-first-architecture.md`.

### Query Classification & Selective Routing
Classifying queries into 8 types (A-H: ID exact, semantic, temporal, emitter+action, acronym, narrative, modifications, adversarial) enables selective store routing — skipping Qdrant/Neo4j for types that don't benefit from them. Reduces latency by 53% for Qdrant and 83% for Neo4j graph. Key patterns: cascade order matters (D/E before C), emisor name mapping, adversarial forced-conf=0.15. See `references/query-classifier-selective-routing.md`.

### Confidence Scoring Diagnostics & Tuning
When functional queries get confidence < 0.50 despite good retrieval, trace the penalty chain through 6 capas (layers). Common bugs: overlap scope too narrow (results[:N] misses Qdrant), Capa 5 over-penalizes when Qdrant confirms relevance, unconditional floor `max(weighted, 0.75)` blocks penalties. Fix via debug_internal field tracing. See `references/rag-confidence-tuning.md`.

### KAG Patterns Integration (Fases A/B/C)
Production integration of KAG-inspired patterns into the RAG pipeline: mutual indexing (Neo4j ↔ text chunks with `_citas` field), schema-constrained legal ontology (7 entity types, 10 semantic relations, role inference), and planning operator (multi-hop query decomposition into 2-3 atomic steps). All phases are independent, flag-gated (KAG_PLANNING, KAG_MUTUAL_INDEX, KAG_SCHEMA), and integrated via 5 surgical insertion points in api_rest.py. Full implementation details, test results, and pitfalls in `references/kag-patterns-integration.md`.

### Code Refactoring: Monolithic Functions → Composable Helpers

**User mandate:** Código simple y fácil de entender y mantener. Pruebas conformes avanzas (test after every change). Snapshots antes de cambios (git tag + backup + checksum).

**Karpathy principles (mandatory for all new code in this project):**
1. THINK BEFORE CODING — analyze the problem, state assumptions, ask when unclear
2. SIMPLICITY FIRST — one function = one responsibility; no classes unless truly needed
3. SURGICAL CHANGES — modify only what must change; pipeline stays intact
4. MINIMAL DEPENDENCIES — zero new pip packages unless absolutely justified
5. HUMAN-READABLE — Spanish variable names, docstrings explain intent, no magic numbers
6. TEST AS YOU GO — every change must pass existing battery before proceeding

**"Antes vs Después" documentation convention**: When making architectural changes (new pipeline stages, new data flows), always produce a TXT report showing the full pipeline trace for a concrete query BEFORE and AFTER the change. Include: every pipeline step, what the context/prompt looks like at each stage, and how the LLM answer differs. The user values this format to understand impact without reading code. Save as `reports/antes_vs_despues_<change>_YYYYMMDD.txt`.

**Module pattern for new features**: Create independent modules under `src/<feature>/` with `__init__.py` + one file per concern. Wire into api_rest.py via surgical patches (never refactor the whole pipeline at once). Each module must work standalone (importable, testable) before integration. Use environment variable flags `FEATURE_NAME=1` (default ON) for each module so they can be disabled individually without code changes.

When the RAG codebase accumulates monolithic functions (300+ lines), refactor SURGICALLY — not by rewriting. Extract independent blocks into named helpers while keeping logic byte-for-byte identical. Pattern: identify layers → extract each into `_helper()` above main function → replace block with single call → test after each → commit.

**Real result:** `confidence_score()` refactored from 354 lines to 80-line orchestrator + 6 helpers. 10/10 tests passed, 0 regressions. Also extracted `_make_result()` factory (replaced 5+ repeated dict constructions) and `_dedup_and_blend()` (replaced 40-line inline dedup block).

**What to extract vs keep inline:**
- EXTRACT: independent blocks with clear input/output, repeated patterns, dedup/scoring logic
- KEEP INLINE: tightly coupled scoring that references many intermediate locals

Full methodology in `references/surgical-refactoring-pattern.md`.

### SQL Injection Prevention (Parameterized Queries)

When building dynamic SQL with user-supplied tokens, use `?` placeholders — NEVER f-string interpolation. This codebase had 5 SQL injection vectors in `confidence_score()` and `search_sqlite()` where user query terms were interpolated into LIKE clauses.

**Pattern (WRONG → RIGHT):**
```python
# WRONG: f-string interpolation
db.execute(f"SELECT 1 FROM normas WHERE sumilla LIKE '%{word}%'")

# RIGHT: parameterized query
db.execute("SELECT 1 FROM normas WHERE sumilla LIKE ?", (f"%{word}%",))
```

**For multi-condition queries:** build placeholders dynamically, collect params in a list:
```python
words = list(meaningful_words)[:4]
conditions = " AND ".join(["(sumilla LIKE ? OR titulo LIKE ?)" for _ in words])
params = []
for w in words:
    params.extend([f"%{w}%", f"%{w}%"])
db.execute(f"SELECT 1 FROM normas WHERE {conditions} LIMIT 1", params)
```

**SECURITY RULE:** Even when tokens come from "safe" sources (regex matches on digits, entity detection), ALWAYS use placeholders. Defense in depth.
Replace LIKE-based search with FTS5 for BM25 ranking and accent-insensitive matching. FTS5 `MATCH` uses AND by default — build explicit OR queries for bag-of-words search. Normalize negative BM25 ranks to 0-1 relevance scale. Keep LIKE fallback for stop-word queries. `tokenize='unicode61 remove_diacritics 2'` handles Spanish accents. See `references/sqlite-fts5-rag-integration.md`.

### GraphRAG vs KG-Enhanced RAG — Know the Difference

**GraphRAG (Microsoft Research)**: Community detection (Leiden algorithm) + LLM summarization of graph communities. Best for thematic queries ("qué temas dominan las normas ambientales"). High pre-processing cost ($0.04/150 communities via Groq Batch). Requires Docker for Leiden clustering.

**KG-Enhanced RAG (our approach, KAG-inspired)**: Schema-constrained knowledge graph with formal entity types (7) and semantic relations (10). No community detection, no pre-processing. Best for factual legal queries ("quién designó a X", "qué RM modifica Y"). Zero additional cost.

**Decision (2026-05-06)**: The El Peruano system stays as KG-Enhanced RAG. GraphRAG's community detection is unnecessary for a legal norms system where queries are predominantly factual, not thematic. See `references/kag-patterns-implementation.md` for the full implementation of mutual indexing, schema-constrained extraction, and multi-hop planning.

For the original GraphRAG planning (if ever needed): NetworkX approach works for <200K nodes without Docker changes (~$0). Groq Batch API costs ~$0.04 for 150 community summaries. Phase strategy: Graph Traversal first (80% of value), community detection only with 3+ years of data. See `references/graphrag-planning.md`.

### Adversarial Testing & Multi-Layer Defense
Test that the RAG system FAILS WELL on out-of-coverage queries. Design trap queries (topics that don't exist, fake IDs, temporal gaps, impossible combinations, jailbreak attempts). 6-layer defense architecture (post-hoc negation, semantic overlap, filler-word detection, DB existence verification, impossible combinations, temporal anomaly). Zero-match keyword detector with morphological tolerance. 100-query integrated battery (functional + adversarial). See `references/adversarial-rag-diagnostics.md` and `references/defensa-adversarial-multicapa.md`.

### Granular Audit Logging for Python Web Services

When running a RAG system in production, you need a persistent audit trail of significant operations: queries, ingestions, deletions, configuration changes, errors. A single SQLite `audit_log` table with event types, categories, timestamps, success/failure flags, and filtered REST endpoints covers this without external dependencies.

See `references/granular-audit-logging.md` for the full schema, event taxonomy, Python implementation, and integration pattern.

### Anti-Hallucination for Legal RAG Systems

LLMs hallucinate organizational/reference laws that appear in boilerplate legal clauses. The fix chain uses 3 layers: prompt engineering (~50% effective), LeyBooster (retrieval-side prioritization of law-type results), and regex post-cleaner (100% effective — strips known false positives from final answer). Also covers: making the LLM enumerate ALL relevant laws, async timeout for blocking LLM calls, and reverse validation testing.

See `references/anti-hallucination-legal-rag.md`.

### Testing & Demonstration Methodology
Systematic approach to testing RAG capabilities. Includes: database analysis for realistic queries, demo vs production comparison, 40-query diversified test suite (8 categories), automated quality scoring, answer coherence analysis, artifact health tracking from sources (NOT /health endpoint), and dual-format (MD + HTML) report generation.
### Large-scale batteries (100+ questions)

**CRITICAL: Never truncate answers in test scripts.** The user will complain about incomplete reports. Always save `"answer": answer` (not `"answer": answer[:250]`). See the `answer[:250]` pitfall in `references/large-scale-battery-testing.md` — this caused a real user frustration episode.

Split into batches of 25, use `execute_code` blocks (not background terminal — Python buffers stdout without TTY). Capture per-question metrics: confidence, timing, reasoning_mode, web_fallback, cached, sources_used. Classify as OK (>40 chars, no negation), WARN, ERROR. Aggregate across batches into JSON then TXT via `scripts/consolidate_battery_reports.py` (handles dict/list format AND schema inconsistency — lote2 uses `question`/`confidence`/`timing_ms`/`status` while other lotes use `q`/`conf`/`ms`/`quality`). See `references/large-scale-battery-testing.md`.

See `references/testing-and-demonstrating-rag-systems.md`.

### El Peruano Project Recovery & System State
Session-specific recovery procedures for the El Peruano legal norms RAG project. Includes: dual-path .env management, Docker container verification, API key status, current system state (28-abr-2026), Qdrant Broken pipe fixes, Neo4j 5.x syntax patterns, confidence score override bugs, and roadmap. See `references/el-peruano-project.md`.

### Document Type Auto-Detection & Per-Type Chunking

Before chunking ANY document, run auto-detection to determine the document type (contrato, resolucion, sentencia, libro, informe, norma, generico). Each type gets a DIFFERENT chunking strategy optimized for its structure. Generic documents get a 512-token sliding window with overlap. See `references/document-ingestion-chunking-strategies.md` for full implementation with regex patterns, scoring system, and Rust optimization notes.

**Key insight**: The category the user assigns (e.g., "Contratos/Prestamos") is a HINT for document organization, NOT for chunking strategy. Auto-detection always wins when it has clear structural signals.

### RAG UX Patterns (Streaming, Settings, Sidebar, Console Menu)

When building a RAG system for END USERS (not developers), implement these UX patterns:

**Streaming SSE**: Use Server-Sent Events to stream LLM tokens word-by-word. Achieves TTFT (Time To First Token) under 1s even when full response takes 5-10s. Pattern: FastAPI `StreamingResponse` + `asyncio.sleep(0.01)` between tokens. Events: `metadata` (intent + chunk count), `token` (each word), `sources` (final references), `done`.

**Settings UI**: Non-technical users cannot edit `.env` files. Provide a `/settings` page with:
- Provider selector (Groq/OpenAI/Anthropic/Gemini/Ollama)
- API key inputs (password-masked, written to `.env` via API)
- Model dropdown (per-provider)
- Temperature slider (0.0-1.0)
- Response style (formal/concise/detailed)
- Citation format (inline/footnote/end)
- Test connection button

**Collapsible Sidebar**: Ctrl+B toggle, 200ms CSS transition, state in localStorage. On mobile (<1024px), hidden by default with floating toggle button.

**Console TUI Menu**: `python krag.py` without args shows numbered menu (1-7). Must preserve CLI compatibility when args are passed.

See `references/rag-settings-ui-pattern.md` for the complete settings API structure (.env writing, provider switching, key management, preferences persistence). See `references/document-ingestion-chunking-strategies.md` for streaming SSE endpoint pattern and console menu architecture.

### Evaluate Before Implementing (Workflow)

When the user asks for improvements or changes, ALWAYS evaluate first. The user explicitly says "no hagas cambios, dame tu evaluacion" / "evalualo, ponderalo" before implementation. Follow this workflow:

1. READ the existing codebase thoroughly
2. ANALYZE each proposed change for: effort, impact, dependencies, risks
3. PRIORITIZE into tiers (P1 immediate, P2 short-term, P3 medium, P4 optional)
4. PRESENT the analysis with clear trade-offs
5. WAIT for explicit approval before writing code
6. Only after approval, IMPLEMENT in order of priority

**Pitfall**: Skipping evaluation and going straight to code will cause the user to push back ("todavia no hagas cambios"). Save time by doing the analysis first.

### Legal Chunking at Scale (10k-20k Documents)
Strategy for building local RAG over large folders of Word+PDF legal documents on Windows. Covers: MarkItDown ingestion pipeline, legal-specific chunking by articles/clauses, bge-m3 embeddings, Qdrant file mode, source citation patterns, and Hermes Agent as query orchestrator (not batch indexer). Reference implementation at https://github.com/mmansillaf/rag-legal-local (~1,100 lines Python). See `references/legal-rag-large-scale-ingestion.md`.

### Multi-Agent RAG Pipeline (Intent Routing + Analysis + Validation)
When you need a RAG system that handles MULTIPLE query intents (summarization, cross-document comparison, contradiction detection, risk analysis) with validated source citations, use a multi-agent architecture. 5 agents: orchestrator/intent classifier → retrieval (hybrid + reranker) → analysis (compare/contradictions) → generation → citation validation. LLM-provider-agnostic (Groq, OpenAI, Gemini, Ollama). Designed for local-first document management (ChromaDB + SQLite FTS5, CRUD, categories). See `references/multi-agent-rag-pipeline.md`.

**Pitfall — Comparison queries fetch wrong documents**: When a user asks "compara el contrato A con el contrato B", the retrieval agent searches by embedding similarity of the ENTIRE query. This finds semantically similar text from UNRELATED documents instead of the specific documents named in the query. The LLM then answers with generic structure ("I can help you compare...") using irrelevant chunks as sources.

**Fix — Auto-detect document names from query for COMPARE/CONTRADICTIONS intents**:
Before retrieval runs, extract document names from the natural language query and use them as `doc_filter`. Implementation pattern:

1. **Query parsing**: Strip stop words (`compara`, `contradicciones`, `documento`, `entre`, `con`, `vs`, `y`). Split by connectors (`y`, `e`, `vs`, `versus`, `con`, `,`). Each resulting fragment is a candidate document name.

2. **Fuzzy name matching**: For each candidate, search the document store with LIKE patterns: exact name, name + each known extension (.txt/.pdf/.docx), and word-by-word (for "contrato de servicios" matching "contrato_servicios_profesionales.txt"). Deduplicate by doc_id.

3. **Filtered retrieval**: Pass found names as `doc_filter=[name1, name2]` to the retrieval agent. When `doc_filter` is active, multiply `top_k` by 3 (e.g. 20→60) so chunks from the specific documents don't get truncated out of the result window.

4. **Fallback**: If no candidates survive the filter after hybrid search (rare edge case), retry with document names as the search query string instead of the user's full comparison sentence.

5. **Caveats**: 
   - Users typing partial names ("contrato de servicios" instead of "contrato_servicios_profesionales.txt") will match more broadly — validate matches are reasonable
   - The `_extract_doc_names_from_query` method returns `None` if no documents match, preserving backward compatibility (normal retrieval runs)
   - First compare/contradictions query after this fix will still fail if the documents weren't ingested — the fix only helps when documents exist in the store

See `references/multi-agent-rag-pipeline.md` for the full pipeline pattern.

### RAG Performance Optimization (Streaming, Parallel, Models)
Full breakdown of RAG pipeline latency: 94% Groq, 5% Neo4j, 1% everything else. Covers: streaming SSE with Groq + FastAPI (TTFT 0.34s), parallel search with asyncio.gather (1.65x speedup), 5-model Groq benchmark for Spanish legal text, 2-level model routing strategy, LRU cache with TTL, and the definitive Rust evaluation (NOT worth it). See `references/rag-performance-optimization.md`.

### Groq Batch Extraction & RAG Enrichment
Diagnosing and fixing incorrect metadata (sumillas) in large-scale legal RAG systems. Covers: root cause of schema mismatch (municipal schema applied to national norms), Groq Batch API workflow with universal extraction schema, cost analysis ($0.83 for 19,892 docs with llama-3.1-8b), Qdrant point ID hashing, structured entity enrichment from norma_entities, and full-text FTS5 indexing from markdown sources. Combined effect: 40% → 87% answer quality on 40-question legal battery. See `references/groq-batch-extraction-and-enrichment.md`.

### Cloud-First RAG for Low-RAM Windows (8-16GB, CPU-only)
When RAM is limited with no GPU, local LLMs are not viable. Architecture: local embeddings + local vector search + cloud LLM APIs. bge-m3 fits in 2GB RAM. DeepSeek API ~$0.60/month. Full cost breakdown in `references/cloud-first-rag-low-ram-windows.md`.

### KAG Patterns — KG-Enhanced RAG (Mutual Indexing + Schema + Planning)
Three modular upgrades that transform the flat RAG pipeline into a KG-Enhanced RAG: (A) mutual indexing linking Neo4j entities back to exact text chunks with offset tracking, (B) schema-constrained extraction with 7 formal entity types and 10 semantic relations (DESIGNA, MODIFICA, DEROGA, etc.), (C) multi-hop query planner that decomposes complex legal queries into atomic steps. ~560 lines, zero new dependencies, fully reversible. See `references/kag-patterns-implementation.md`.
