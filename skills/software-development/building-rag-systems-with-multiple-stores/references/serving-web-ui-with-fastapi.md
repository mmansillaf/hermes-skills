# Serving a Web UI Alongside a FastAPI API

## The Problem

You have a FastAPI REST API with endpoints like `/health`, `/query`, `/search`. You want to serve a single-page web UI (HTML+CSS+JS) at the root path `/` so users can interact with the API visually.

## The Wrong Way: `app.mount("/", StaticFiles(...))`

```python
# DON'T do this:
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

**Why it breaks:** When you mount at `/`, Starlette intercepts ALL requests matching that prefix — including `/health`, `/query`, `/stats`, etc. The StaticFiles app tries to look for files named "health", "query", "stats" in the static directory and returns 404. API endpoints defined AFTER the mount become unreachable.

## The Right Way: `@app.get("/")` with `HTMLResponse`

Mount the static directory at a non-conflicting path (e.g., `/static`), and serve the root via a simple route:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

# 1. Mount static assets at a subpath (NOT at "/")
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    # Optional: serve CSS/JS/favicon from /static
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 2. Load HTML at startup
INDEX_HTML = None
if STATIC_DIR.exists():
    INDEX_HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    print(f"UI cargada ({len(INDEX_HTML)} chars)")

# 3. Serve root via a simple route
@app.get("/", include_in_schema=False)
async def serve_ui():
    if INDEX_HTML:
        return HTMLResponse(INDEX_HTML)
    return {"status": "ui_not_available"}
```

## The Clean Approach: Just Preload the HTML

If the UI is a single HTML file with inline CSS/JS (no external assets), skip the mount entirely:

```python
# At module level (not inside the route handler)
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = None
if STATIC_DIR.exists():
    INDEX_HTML = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

# Inline import — no top-level dependency on starlette.responses
@app.get("/", include_in_schema=False)
async def serve_ui():
    if INDEX_HTML:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(INDEX_HTML)
    return {"status": "ui_not_available"}
```

**Benefits:**
- No mount conflicts — API endpoints work normally
- No filesystem access at request time (text loaded at startup)
- `include_in_schema=False` keeps it out of OpenAPI docs
- Lazy import of `HTMLResponse` avoids dependency at module level

## Alternative: Mount at a Subpath

If your UI has multiple pages/assets, mount at `/app` instead:

```python
app.mount("/app", StaticFiles(directory="ui", html=True), name="ui")

@app.get("/", include_in_schema=False)
async def redirect_to_ui():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app")
```

## Pitfalls

### Health check must be defined BEFORE the root route
Starlette matches routes in order. Define `/health` before `/` to ensure it gets priority. Or use `include_in_schema=False` and rely on FastAPI's route ordering.

### Reloading the HTML
If you edit `index.html`, you need to restart the API process. For development, use `StaticFiles` mount at a subpath instead of preloading.

### CORS for embedded apps
If the UI is served from a different domain than the API, the API needs CORS middleware:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

### File size limits
For files > 100KB, read on first request (not at startup) to avoid memory waste:
```python
@app.get("/", include_in_schema=False)
async def serve_ui():
    from fastapi.responses import FileResponse
    path = STATIC_DIR / "index.html"
    if path.exists():
        return FileResponse(str(path), media_type="text/html")
    return {"status": "ui_not_available"}
```
