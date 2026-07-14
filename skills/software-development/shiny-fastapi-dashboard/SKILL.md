---
name: shiny-fastapi-dashboard
description: Build interactive data dashboards with Shiny for Python frontend + FastAPI backend. Covers JWT auth, CRUD APIs, reactive data loading, row-click navigation, modal login, and production deployment.
triggers:
  - User wants to build a dashboard or data app in Python
  - User mentions Shiny for Python
  - User wants a CRM, intake system, or business management UI
  - User asks for a FastAPI + frontend combination
version: 1.0.0
---

# Shiny + FastAPI Dashboard

Build a production-ready interactive dashboard with **Shiny for Python** as the frontend and **FastAPI** as the backend API.

## Architecture

```
[Browser] ──HTTPS──> [Shiny :8501] ──HTTP──> [FastAPI :8000] ──> [SQLite/PostgreSQL]
```

- **Shiny** handles UI rendering, reactivity, session state
- **FastAPI** handles data persistence, auth, business logic, external API calls
- They run as separate processes on different ports
- Shiny calls FastAPI via `httpx` — the dashboard never touches the DB directly

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Shiny for Python (1.6+) | Reactividad selectiva, Python puro, multi-pestaña nativa |
| Backend API | FastAPI + SQLAlchemy | Validacion Pydantic, OpenAPI docs, ORM flexible |
| Auth | JWT (PyJWT + bcrypt) | Stateless, simple, funciona entre procesos |
| DB | SQLite (dev) / PostgreSQL (prod) | SQLAlchemy abstrae el cambio |
| API Client | httpx | Async-capable, timeouts configurables |
| Package mgr | uv | Rapido, lockfile moderno |

## Shiny 1.6+ API (Critical)

Shiny 1.6.x **changed its API**. These are the correct imports:

| Instead of (`< 1.6`) | Use (`1.6+`) |
|----------------------|-------------|
| `ui.nav(...)` | `ui.nav_panel(...)` |
| `ui.page_navbar(..., ui.nav(...))` | `ui.page_navbar(..., ui.nav_panel(...))` |
| — | `ui.navset_bar(...)` for navbar-only |
| — | `ui.navset_card_tab(...)` for tab cards |

## Pattern: Connecting Shiny to FastAPI

### API Client Wrappers

```python
import httpx

API_BASE = "http://localhost:8000"

def _api_get(path: str, token: str | None = None) -> dict | list:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = httpx.get(f"{API_BASE}{path}", headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def _api_post(path: str, data: dict, token: str | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = httpx.post(f"{API_BASE}{path}", json=data, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def _api_put(path: str, data: dict, token: str) -> dict:
    r = httpx.put(f"{API_BASE}{path}", json=data,
                  headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status()
    return r.json()
```

### JWT Token Management

Store the JWT token in a `reactive.Value`:

```python
token = reactive.Value[str | None](None)

def _show_login():
    m = ui.modal(
        ui.h3("Iniciar sesión"),
        ui.input_text("login_user", "Usuario"),
        ui.input_password("login_pass", "Contraseña"),
        ui.input_action_button("btn_login", "Ingresar"),
        title=None, easy_close=False, footer=None,
    )
    ui.modal_show(m)

@reactive.effect
@reactive.event(input.btn_login)
def _do_login():
    try:
        resp = _api_post("/api/v1/auth/login", {
            "username": input.login_user(),
            "password": input.login_pass(),
        })
        token.set(resp["access_token"])
        ui.modal_remove()
        _cargar_datos()
    except Exception:
        ui.notification_show("Credenciales inválidas", type="error")
```

### Row Click Navigation

For table rows that navigate to a detail view:

```html
onclick="Shiny.setInputValue('_click_lead', {id}, {{priority:'event'}})"
```

Then in Shiny server:

```python
selected_lead_id = reactive.Value[int | None](None)

@reactive.effect
@reactive.event(input._click_lead)
def _on_click():
    lid = input._click_lead()
    if lid:
        selected_lead_id.set(lid)
        ui.update_navs("navbar", selected="Detalle")
```

### Complex Layouts

When Shiny's `ui.div()` nesting becomes cumbersome, use `ui.HTML()` with inline styles:

```python
@output
@render.ui
def stats_row():
    return ui.HTML(f"""
    <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;">
        <div class="stat-card">
            <div class="num" style="color:#3b82f6;">{count}</div>
            <div class="label">Nuevos</div>
        </div>
        ...
    </div>
    """)
```

### Reactive Data Loading Pattern

```python
leads_cache = reactive.Value[list]([])

def _cargar_datos():
    t = token.get()
    if not t:
        return
    leads_cache.set(_api_get(f"/api/v1/leads?{params}", t))

@reactive.effect
@reactive.event(input.btn_filtrar)
def _on_filtrar():
    _cargar_datos()

@output
@render.ui
def tabla_leads():
    leads = leads_cache.get()
    if not leads:
        return ui.p("Sin resultados.")
    # render leads as HTML...
```

## Procedure

### Sprint 1: Backend API

1. Initialize project with `uv init --app` and `uv add fastapi uvicorn sqlalchemy pydantic pyjwt bcrypt httpx python-dotenv`
2. Create models: Lead, LeadLog, User (SQLAlchemy)
3. Create schemas (Pydantic): Create, Update, Response, Login
4. Create config.py with DATABASE_URL, JWT settings, env vars
5. Create database.py with engine, SessionLocal, init_db(), get_db() dependency
6. Create security.py with hash_password, verify_password, create_access_token, decode_token
7. Create auth routes: POST /register, POST /login, POST /refresh
8. Create CRUD routes (protected with `get_current_user` dependency)
9. Create public POST endpoint for lead creation (no auth)
10. Verify with `curl` or httpx before building the dashboard

### Sprint 2: Shiny Dashboard

1. Add shiny: `uv add shiny`
2. Create `dashboard/app.py` with:
   - Login modal (JWT)
   - Main table (leads list)
   - Detail view (lead info + timeline + actions)
   - Config view
3. Use reactive.Value for: token, selected_lead_id, leads_cache, stats_cache
4. Use ui.HTML for complex grids/tables
5. Handle row clicks via Shiny.setInputValue
6. Test: `uv run uvicorn app.main:app --port 8000` + `uv run shiny run dashboard/app.py --port 8501`

### Sprint 3: Web Form + WhatsApp + IA Agent

1. Static HTML form submitting to POST /api/v1/leads
2. Twilio webhook endpoint receiving WhatsApp messages
3. IA agent calling Groq API to extract structured data
4. Auto-reply to prospect and notification to user

## Pitfalls

- **Shiny 1.6 API**: `ui.nav()` does not exist. Use `ui.nav_panel()` inside `ui.page_navbar()`.
- **JWT secret key**: Must be >= 32 bytes for HMAC-SHA256. Dev default should be 32+ chars.
- **SQLAlchemy + Pyright**: Column types vs Python types trigger false positive warnings from Pyright. Safe to ignore.
- **Shiny reactive.Value type hinting**: Pyright complains about `dict | list` vs specific types. Safe to ignore.
- **Background processes**: Shiny and FastAPI must run as separate background processes. Use `notify_on_complete=True` for bounded processes.
- **CORS**: FastAPI needs CORS middleware if Shiny runs on a different port.
- **uv add with big dep lists**: uv can appear slow. Run in background with `notify_on_complete=True`.

## Verification

- `curl http://localhost:8000/health` returns `{"status":"ok"}`
- `curl http://localhost:8501` returns 200
- Login with test credentials works
- Creating a lead via POST returns 201 and visible in dashboard after refresh
- Changing lead state is reflected in detail view timeline
