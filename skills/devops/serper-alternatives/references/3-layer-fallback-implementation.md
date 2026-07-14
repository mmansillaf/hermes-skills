# 3-Layer Web Fallback Implementation (01-may-2026)

## Arquitectura

```
Capa 1: FTS5 local sobre 89K HTMLs (fuentes_html.db, 1.15 GB)
  → Sin dependencia externa, sin limites, instantaneo
  → Si encuentra >= 3 resultados, no sale a internet
Capa 2: Serper API (Google Search) — 2,500 consultas/mes gratis
Capa 3: Tavily API (optimizado para RAG) — API key en .env
```

## Código en api_rest.py

### search_local_htmls() — Capa 1

```python
def search_local_htmls(question, top_k=5):
    db = sqlite3.connect("data/fuentes_html.db")
    tokens = [w for w in question.lower().split() if len(w) >= 3]
    if not tokens: return []
    query = " OR ".join(tokens)
    rows = db.execute("""
        SELECT path, snippet(html_fts, 2, '<b>', '</b>', '...', 40) 
        FROM html_fts WHERE html_fts MATCH ? LIMIT ?
    """, (query, top_k)).fetchall()
    if not rows:
        # fallback LIKE
        terms = " AND ".join(f'"%{t}%"' for t in tokens[:5])
        rows = db.execute(
            f"SELECT path, substr(texto, 1, 300) FROM html_raw WHERE texto LIKE {terms} LIMIT ?",
            (top_k,)
        ).fetchall()
    return [{"path": r[0], "snippet": r[1], "source": "fuente_local"} for r in rows]
```

### search_web_fallback() — Orchestrator

```python
def search_web_fallback(question, top_k=5):
    all_results = []
    
    # Capa 1: busqueda local
    local = search_local_htmls(question, top_k=top_k)
    all_results.extend(local)
    
    # Capa 2: Serper (solo si local < 3)
    serper_results = []
    if len(all_results) < 3 and SERPER_API_KEY:
        serper_results = search_serper(question, top_k=top_k)
        all_results.extend(serper_results)
    
    # Capa 3: Tavily (solo si Capa 1+2 < 3)
    if len(all_results) < 3 and TAVILY_API_KEY:
        tavily_results = search_tavily(question, top_k=top_k)
        all_results.extend(tavily_results)
    
    return all_results[:top_k]
```

### search_tavily() — Capa 3

```python
def search_tavily(question, top_k=5):
    resp = requests.post("https://api.tavily.com/search", json={
        "api_key": TAVILY_API_KEY,
        "query": question,
        "search_depth": "basic",
        "max_results": top_k
    }, timeout=15)
    results = resp.json().get("results", [])
    return [{
        "link": r["url"], "snippet": r["content"],
        "title": r.get("title", ""), "source": "tavily_web"
    } for r in results]
```

## build_html_index.py

Script que indexa 89,953 HTMLs en FTS5:

```python
db = sqlite3.connect("data/fuentes_html.db")
db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS html_fts USING fts5(path, fecha, texto)")
db.execute("CREATE TABLE IF NOT EXISTS html_raw (path TEXT PRIMARY KEY, fecha TEXT, texto TEXT)")

for html_file in Path("data").rglob("*.html"):
    rel = str(html_file.relative_to("data"))
    text = html_file.read_text(encoding="utf-8", errors="ignore")
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean)[:5000]
    date_str = extract_date_from_path(rel)
    db.execute("INSERT OR IGNORE INTO html_fts VALUES (?, ?, ?)", (rel, date_str, clean))
    db.execute("INSERT OR REPLACE INTO html_raw VALUES (?, ?, ?)", (rel, date_str, clean))

db.commit()
db.execute("INSERT INTO html_fts(html_fts) VALUES ('optimize')")
```

## Métricas

- Tiempo de indexación: 1:45 min para 89K HTMLs
- Tamaño de la DB: 1.15 GB
- Cobertura: ~80% de web fallbacks se resuelven con Capa 1
