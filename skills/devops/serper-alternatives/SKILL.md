---
name: serper-alternatives
description: "Alternativas para reemplazar Serper API como web fallback en El Peruano RAG. Self-hosted, APIs gratuitas y estrategia hibrida."
---

# Alternativas a Serper API — Web Fallback para El Peruano RAG

## Qué hace Serper actualmente

```python
# api_rest.py linea 195-233
def search_web_fallback(question, top_k=5):
    queries = [
        f"site:elperuano.pe {question}",
        f"normas legales Peru {question}",
    ]
    # → Google Search via Serper API
    # → Resultados con snippet, link, title
    # → relevance=0.15, source="serper_web"
```

**Se activa cuando:** `confidence < 0.50` (2,500 consultas gratis/mes)

## Estrategias de Reemplazo

### A) Búsqueda local sobre los 89K HTMLs (RECOMENDADA)

Ya tienes los HTMLs fuente. En vez de buscar en Google, buscar DENTRO de tus propios archivos.

```
┌─────────────────────────────────────────────────────────────┐
│  En vez de: "Google, dime qué dice El Peruano sobre X"      │
│  Hacer:     "Mis 89K HTMLs, ¿en cuáles aparece X?"         │
└─────────────────────────────────────────────────────────────┘
```

**Implementación:**
- Índice FTS5 sobre los 89K HTMLs (misma tecnología que normas_2024.db)
- Base de datos `fuentes_html.db` con: path, fecha, texto_completo, numero_norma
- Búsqueda: `SELECT path, snippet(html_fts, 0, '<b>', '</b>', '...', 40) FROM html_fts WHERE html_fts MATCH ?`
- Resultados: link directo al HTML en R2, snippet con highlighting

**Ventajas:**
- Cero dependencia externa
- Cero costo
- Resultados 100% relevantes (solo normas peruanas)
- Respuesta instantánea (local)
- Links directos a la fuente original

**Desventajas:**
- Solo busca en lo que ya tienes (no encuentra normas nuevas no ingeridas)
- Requiere indexar 80 MB de HTMLs (~5 minutos, una vez)

### B) DuckDuckGo Instant Answer API (Gratis, sin key)

```
GET https://api.duckduckgo.com/?q=resolucion+ministerial+peru&format=json
```

**Ventajas:** Sin API key, sin rate limits documentados, resultados decentes
**Desventajas:** Solo devuelve topics relacionados, no resultados web completos. Sin snippet de texto.

### C) Brave Search API (Free tier generoso)

```
GET https://api.search.brave.com/res/v1/web/search?q=normas+peru
Header: X-Subscription-Token: <key>
```

**Free tier:** 2,000 queries/mes
**Ventajas:** Resultados web completos, snippet, independiente de Google
**Desventajas:** Sigue siendo dependencia externa, requiere registro

### D) SearXNG (Self-hosted, docker)

Motor de metabúsqueda que agrega Google, DuckDuckGo, Bing, Wikipedia, etc.
Un solo docker container, sin API key, sin rate limits.

```
docker run -p 8080:8080 searxng/searxng
GET http://localhost:8080/search?q=normas+peru&format=json
```

**Ventajas:** Self-hosted, sin límites, múltiples fuentes, JSON API
**Desventajas:** Un servicio más que mantener, ~500 MB RAM

### E) El Peruano — Búsqueda directa en el sitio oficial

El sitio `elperuano.pe` tiene un buscador interno. Se podría hacer scraping:
```
GET https://elperuano.pe/buscar/{terminos}
```

**Ventajas:** Resultados oficiales, actualizados al día
**Desventajas:** Frágil (cambios en el sitio rompen el scraper), sin API oficial, posible bloqueo

### F) Bing Web Search API (Azure, free tier)

```
GET https://api.bing.microsoft.com/v7.0/search?q=normas+peru
Header: Ocp-Apim-Subscription-Key: <key>
```

**Free tier:** 1,000 queries/mes (Azure free account)
**Ventajas:** Resultados de Bing, bien estructurados
**Desventajas:** Requiere Azure account, límite bajo

## Estado Actual (01-may-2026)

**El sistema ya NO depende de Serper como unica fuente de web fallback.** Se implemento una arquitectura de 3 capas en `search_web_fallback()`:

```
Capa 1: FTS5 sobre 89K HTMLs locales (fuentes_html.db, 1.15 GB)
        → Sin dependencia externa. Se activa primero siempre.
Capa 2: Serper API (Google Search)
        → Solo si Capa 1 encuentra < 3 resultados.
Capa 3: Tavily API (optimizado para RAG)
        → Respaldo final. API key en .env como TAVILY_API_KEY.
```

**Tavily esta integrado** como `search_tavily()` en `api_rest.py`. Usa `https://api.tavily.com/search` con payload `{api_key, query, search_depth: "basic", max_results}`. Devuelve resultados con `content` (mas rico que snippets de Serper).

**El indice FTS5 local** cubre ~80% de los web fallbacks. Solo queries sobre temas sin cobertura en los HTMLs ingeridos (ej: "IA en Peru 2025") caen a Capa 2 o 3.

## Estrategia Hibrida Implementada (3 Capas) — 01-may-2026

```
┌─────────────────────────────────────────────────────────────┐
│                 WEB FALLBACK — 3 CAPAS                       │
│                                                              │
│  Capa 1: BÚSQUEDA LOCAL (siempre, instantánea)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ SQLite FTS5 sobre 89K HTMLs (fuentes_html.db, 1.15GB)│   │
│  │ snippet(html_fts, 2, ...) — columna texto            │   │
│  │ → relevancia 0.25, source="fuente_local"             │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼ (si < 3 resultados)                │
│  Capa 2: SERPER (Google Search API)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Serper API — 2,500 consultas/mes gratis               │   │
│  │ → relevancia 0.15, source="serper_web"               │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│                         ▼ (si Capa 1+2 < 3 resultados)        │
│  Capa 3: TAVILY (optimizado para RAG)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Tavily API — devuelve content (no solo snippet)      │   │
│  │ → relevancia 0.12, source="tavily_web"               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Futuro (post-deploy):** Reemplazar Capa 2 con SearXNG self-hosted (Docker) para eliminar límite de 2,500/mes.

## Costo y Esfuerzo

| Estrategia | Esfuerzo | Costo | Dependencia |
|-----------|----------|-------|-------------|
| A) Búsqueda local HTMLs | Medio (indexar 80MB) | $0 | Ninguna |
| B) DuckDuckGo API | Bajo (20 líneas) | $0 | DuckDuckGo |
| C) Brave Search | Bajo (20 líneas) | $0 (2K/mes) | Brave |
| D) SearXNG docker | Medio (1 docker) | $0 | Ninguna |
| E) Scraping El Peruano | Alto (frágil) | $0 | elperuano.pe |
| F) Bing Azure | Bajo | $0 (1K/mes) | Microsoft |

## Estado Actual (implementado 01-may-2026)

El sistema ya tiene 3 capas de web fallback en produccion:
- Capa 1: FTS5 local sobre 89K HTMLs (gratis, sin limites)
- Capa 2: Serper API (respaldo)
- Capa 3: Tavily API (respaldo final)

Ver `references/3-layer-fallback-implementation.md` para el codigo y arquitectura.

**Fase inmediata (hoy):** Opción A (búsqueda local en HTMLs)
- Ya tienes los 89K HTMLs
- Misma tecnología que SQLite FTS5
- Indexar = 5 minutos, 1 script
- Resultados instantáneos, sin límites

**Fase 2 (cuando despliegues):** Opción A + Opción D
- Búsqueda local como primaria
- SearXNG docker como secundaria (auto-hosteado)
- Eliminar dependencia de Serper completamente

**Código de ejemplo para búsqueda local:**
```python
def build_html_index():
    """Crea índice FTS5 sobre los 89K HTMLs fuente."""
    db = sqlite3.connect("data/fuentes_html.db")
    db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS html_fts USING fts5(path, texto)")
    for html_file in Path("data").rglob("*.html"):
        text = html_file.read_text()
        text = re.sub(r'<[^>]+>', ' ', text)  # strip tags
        db.execute("INSERT INTO html_fts VALUES (?, ?)", 
                   (str(html_file.relative_to("data")), text))
    db.commit()

def search_local_htmls(question, top_k=5):
    """Busca en los HTMLs fuente locales."""
    db = sqlite3.connect("data/fuentes_html.db")
    tokens = [w for w in question.lower().split() if len(w) >= 3]
    query = " OR ".join(tokens)
    rows = db.execute(
        "SELECT path, snippet(html_fts, 0, '<b>', '</b>', '...', 40) "
        "FROM html_fts WHERE html_fts MATCH ? LIMIT ?",
        (query, top_k)
    ).fetchall()
        return [{"path": r[0], "snippet": r[1], "source": "fuente_local"} for r in rows]

## Integraciones Implementadas y Pendientes (01-may-2026)

### IMPLEMENTADAS

| Capa | Servicio | API Key en .env | Funcion | Estado |
|------|----------|----------------|---------|--------|
| 1 | FTS5 local (89K HTMLs) | N/A | `search_local_htmls()` | ✅ Activo |
| 2 | Serper API | `SERPER_API_KEY` | `search_web_fallback()` Capa 2 | ✅ Activo |
| 3 | Tavily API | `TAVILY_API_KEY` | `search_tavily()` | ✅ Activo |

### PENDIENTES (API keys ya en .env)

| Servicio | API Key | Uso potencial | Prioridad |
|----------|---------|---------------|-----------|
| ScrapeGraphAI | `SCRAPEGRAPHAI_API_KEY` (sgai-..., 500 cr/mes) | Monitor de nuevas normas, Capa 4 web fallback | Baja |
| DeepSeek | (pendiente agregar) | LLM provider alternativo (mas barato) | Media |
| Kimi | (pendiente agregar) | LLM para queries analiticas largas | Baja |
```
