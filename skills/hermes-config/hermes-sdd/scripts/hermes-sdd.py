#!/usr/bin/env python3
"""hermes-sdd: Comandos SDD para Hermes Agent.

Uso:
  python hermes-sdd.py specify "descripcion de la feature"
  python hermes-sdd.py plan "tech stack (opcional)"
  python hermes-sdd.py tasks
  python hermes-sdd.py html-preview "feature-name"
  python hermes-sdd.py mcp-server "feature-name"
  python hermes-sdd.py status
  python hermes-sdd.py checklist

Requiere:
  - Ejecutarse desde la raíz del proyecto
  - Los artefactos se guardan en specs/, previews/, mcp/
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    """Encuentra la raíz del proyecto (donde está .specify/)."""
    cwd = Path.cwd()
    for p in [cwd] + list(cwd.parents):
        if (p / ".specify").exists():
            return p
    return cwd


def _read_file(path: str) -> str:
    """Lee un archivo de texto. Retorna '' si no existe."""
    p = Path(path)
    return p.read_text() if p.exists() else ""


def _ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ── Constitución ──────────────────────────────────────────────────────


def cmd_constitution(args: Any) -> None:
    """Genera constitution.md interactivamente."""
    root = _project_root()
    dest = root / ".specify" / "memory" / "constitution.md"
    _ensure_dir(str(dest.parent))

    print("=== SDD: Constitution ===")
    print("Responde las siguientes preguntas para establecer las reglas del proyecto.\n")

    lang = input("Lenguaje/framework principal (ej: Python 3.12+ / FastAPI): ") or "Python 3.12+ / FastAPI"
    database = input("Base de datos (ej: PostgreSQL / SQLite): ") or "PostgreSQL"
    auth = input("Auth (JWT / OAuth / sesiones): ") or "JWT con refresh tokens"
    testing = input("Framework de testing (pytest / jest): ") or "pytest"
    i18n = input("Idiomas (ej: es, en): ") or "es"
    hosting = input("Hosting (VPS / Railway / on-premise): ") or "VPS + Docker"
    multi_tenant = input("Multi-tenant? (si/no): ").lower() == "si"
    owasp_level = input("Nivel OWASP ASI (minimo/medio/completo): ") or "medio"

    content = f"""# Project Constitution

**Generada:** {datetime.now().strftime('%Y-%m-%d')}

## Stack
- Lenguaje: {lang}
- Base de datos: {database}
- Auth: {auth}
- Testing: {testing}

## Reglas No Negociables
1. **i18n**: {i18n} desde el día 1. Todas las UI con soporte multi-idioma.
2. **Seguridad**: JWT/BCrypt para auth. HTTPS en producción.
3. **Código**: Type hints obligatorios. Ruff/black para linting.
4. **Testing**: Tests antes que código (TDD). pytest -v obligatorio.
5. **Hosting**: {hosting}
6. **Multi-tenant**: {"Sí — aislamiento por tenant en todas las queries." if multi_tenant else "No — aplicación single-tenant."}
7. **OWASP ASI**: Nivel {owasp_level} — aplicar checklist correspondiente.
8. **Tokens**: No hardcodear secrets. .env + secret manager.
9. **Commits**: Frecuentes con mensajes descriptivos (conventional commits).
10. **Previews**: Aprobación visual del usuario antes de implementar UI.
"""
    dest.write_text(content)
    print(f"\n✅ Constitution guardada en {dest}")


# ── Spec ─────────────────────────────────────────────────────────────


def cmd_specify(args: Any) -> None:
    """Genera spec.md con EARS."""
    description = args.description or "Feature sin nombre"
    root = _project_root()
    feature_dir = _sanitize_name(description)
    dest_dir = root / "specs" / feature_dir
    _ensure_dir(str(dest_dir))

    print("=== SDD: Specify ===")
    print(f"Feature: {description}\n")

    stories = []
    print("User Stories (deja vacío para terminar):")
    while True:
        s = input("  Story: ")
        if not s:
            break
        stories.append(s)

    ears_criteria = []
    print("\nAcceptance Criteria (EARS). Patrones:")
    print("  [U] Ubiquitous — THE system SHALL ...")
    print("  [E] Event-driven — WHEN ... THEN ...")
    print("  [S] State-driven — WHILE ... THEN ...")
    print("  [W] Unwanted — IF ... THEN ...")
    print("  [O] Optional — WHERE ... THEN ...")
    print("  (vacío para terminar)\n")
    while True:
        pattern = input("  Patrón (U/E/S/W/O): ").strip().upper()
        if not pattern:
            break
        criterion = input("  Criterio: ")
        prefix = {
            "U": "THE system SHALL",
            "E": "WHEN",
            "S": "WHILE",
            "W": "IF",
            "O": "WHERE",
        }.get(pattern, "")
        ears_criteria.append(f"- {prefix} {criterion}")

    out_of_scope = []
    print("\nOut of scope (MVP) — vacío para terminar:")
    while True:
        s = input("  Excluido: ")
        if not s:
            break
        out_of_scope.append(s)

    # OWASP ASI relevante
    print("\nRiesgos OWASP ASI relevantes (deja vacío para usar defaults):")
    print("  [1] Goal Hijack  [2] Tool Misuse  [3] Identity Abuse")
    print("  [4] Supply Chain [5] RCE           [6] Memory Poisoning")
    print("  [7] Inter-Agent  [8] Cascading     [9] Trust Exploit")
    print("  [10] Rogue Agents")
    asi_risks = input("  Riesgos (ej: 1,5,6): ") or "5,6"

    asi_map = {
        "1": ("ASI01: Goal Hijack", "Inputs externos como no confiables. HITL para cambios de objetivo."),
        "2": ("ASI02: Tool Misuse", "Permisos mínimos por herramienta. Rate limiting."),
        "3": ("ASI03: Identity Abuse", "JIT ephemeral tokens. Scopes por endpoint."),
        "4": ("ASI04: Supply Chain", "Allowlist MCP. Pinned deps."),
        "5": ("ASI05: RCE", "Sandbox Docker network:none. No eval()."),
        "6": ("ASI06: Memory Poisoning", "Memoria por tenant. Expirar datos no verificados."),
        "7": ("ASI07: Inter-Agent Comm", "mTLS entre agentes si multi-agente."),
        "8": ("ASI08: Cascading Failures", "Circuit breakers. Max retries."),
        "9": ("ASI09: Trust Exploitation", "Confidence scores. Step-up auth."),
        "10": ("ASI10: Rogue Agents", "Log de objetivos. Monitoreo de drift."),
    }
    selected_asi = []
    for r in asi_risks.split(","):
        r = r.strip()
        if r in asi_map:
            selected_asi.append(asi_map[r])

    # Generar spec
    now = datetime.now().strftime("%Y-%m-%d")
    stories_text = "\n".join(f"- {s}" for s in stories) if stories else "- Por definir"
    ears_text = "\n".join(ears_criteria) if ears_criteria else "- Por definir"
    oos_text = "\n".join(f"- {s}" for s in out_of_scope) if out_of_scope else "- N/A (MVP completo)"
    asi_text = "\n".join(f"### {r[0]}\n{r[1]}" for r in selected_asi)

    content = f"""# Feature: {description}

**Generada:** {now}
**Nivel SDD:** Spec-Anchored

## User Stories

{stories_text}

## Acceptance Criteria (EARS)

{ears_text}

## Out of Scope (MVP)

{oos_text}

## Non-Functional Requirements

- **Rendimiento:** < 200ms p95 para endpoints críticos
- **Seguridad:** OWASP ASI nivel medio (ver abajo)
- **i18n:** ES/EN desde el día 1

## Security Considerations (OWASP ASI 2026)

{asi_text if asi_text else "- Nivel mínimo — riesgos gestionados en implementación."}
"""
    dest_file = dest_dir / "spec.md"
    dest_file.write_text(content)
    print(f"\n✅ Spec guardada en {dest_file}")


# ── Plan ──────────────────────────────────────────────────────────────


def cmd_plan(args: Any) -> None:
    """Genera plan.md."""

    # Buscar la spec más reciente
    root = _project_root()
    spec_dirs = sorted((root / "specs").iterdir()) if (root / "specs").exists() else []

    if not spec_dirs:
        print("❌ No hay specs. Ejecuta 'specify' primero.")
        return

    latest = spec_dirs[-1]
    spec_content = _read_file(str(latest / "spec.md"))

    print("=== SDD: Plan ===")
    print(f"Generando plan para: {latest.name}\n")

    tech_stack = args.tech_stack or input("Tech stack (o Enter para usar constitution): ") or "Ver constitution"

    arch = input("Arquitectura (ej: Frontend Web → API → BD): ") or "Web frontend → FastAPI :8000 → SQLite/PG"
    db_tables = []
    print("\nTablas de datos (vacío para terminar):")
    while True:
        table = input("  Nombre de tabla: ")
        if not table:
            break
        fields = input(f"  Campos ({table}): ")
        db_tables.append((table, fields))

    success_factors = []
    print("\nFactores críticos de éxito (vacío para terminar):")
    while True:
        s = input("  Factor: ")
        if not s:
            break
        success_factors.append(s)

    antipatterns = []
    print("\nAnti-patrones a evitar (vacío para terminar):")
    while True:
        s = input("  Anti-patrón: ")
        if not s:
            break
        antipatterns.append(s)

    now = datetime.now().strftime("%Y-%m-%d")

    tables_text = "\n".join(f"### Tabla: {t}\n| Campo | Tipo | Notas |\n|-------|------|-------|\n| id | UUID | PK |" for t, f in db_tables) if db_tables else "- Por definir en implementación"

    api_text = """```
POST   /api/v1/auth/login          # Login → JWT
GET    /api/v1/resource            # Listar (auth)
POST   /api/v1/resource            # Crear
PUT    /api/v1/resource/{id}       # Actualizar
```"""

    factors_text = "\n".join(f"- {s}" for s in success_factors) if success_factors else "- Ver constitution.md"
    antipatterns_text = "\n".join(f"- {s}" for s in antipatterns) if antipatterns else "- Ver constitution.md"

    content = f"""# Plan: {latest.name}

**Generado:** {now}

## Arquitectura General

```
{arch}
```

## Data Model

{tables_text}

## API Contracts

{api_text}

## Tech Stack

{tech_stack}

## Constitution Check

- [ ] Lenguaje y framework según constitution
- [ ] Sin dependencias externas obligatorias no autorizadas
- [ ] i18n desde el inicio
- [ ] Multi-tenant / seguridad
- [ ] OWASP ASI checklist aplicado

## Opciones de Hosting

| Opción | Costo/mes | Ideal si... |
|--------|-----------|-------------|
| VPS (Hetzner/DigitalOcean) | ~$4-12 | Control total |
| Railway / Fly.io | ~$5-20 | Deploy rápido |

---

## Factores Críticos de Éxito

{factors_text}

## Anti-patrones y Errores a Evitar

{antipatterns_text}
"""
    dest_file = latest / "plan.md"
    dest_file.write_text(content)
    print(f"\n✅ Plan guardado en {dest_file}")


# ── Tasks ─────────────────────────────────────────────────────────────


def cmd_tasks(args: Any) -> None:
    """Genera tasks.md interactivamente."""
    root = _project_root()
    spec_dirs = sorted((root / "specs").iterdir()) if (root / "specs").exists() else []

    if not spec_dirs:
        print("❌ No hay specs. Ejecuta 'specify' primero.")
        return

    latest = spec_dirs[-1]

    print("=== SDD: Tasks ===")
    print(f"Desglosando tareas para: {latest.name}\n")

    tasks = []
    sprint_num = 1
    while True:
        print(f"\n--- Sprint {sprint_num} ---")
        while True:
            task_name = input("  Tarea (vacío = terminar sprint): ")
            if not task_name:
                break
            priority = input(f"    Prioridad (P1/P2/P3) [{task_name}]: ").strip() or "P1"
            deps = input(f"    Dependencias: ")
            steps = []
            print("    Pasos (vacío = terminar):")
            while True:
                step = input("      > ")
                if not step:
                    break
                steps.append(step)
            verification = input(f"    Verificación: ")
            tasks.append((priority, task_name, deps, steps, verification))

        more = input("¿Otro sprint? (s/n): ").lower()
        if more != "s":
            break
        sprint_num += 1

    now = datetime.now().strftime("%Y-%m-%d")

    # Dividir en sprints
    lines = [f"# Tasks: {latest.name}", f"", f"**Generado:** {now}", f"**Nivel SDD:** Spec-Anchored", f"**Testing:** TDD estricto — test primero, luego código", f""]
    sprint_num = 1
    task_num = 1
    for prio, name, deps, steps, verification in tasks:
        lines.append(f"## Sprint {sprint_num}")
        lines.append("")
        dep_text = f"**Dependencias:** {deps}" if deps else ""
        lines.append(f"### [{prio}] task_{task_num:03d}: {name}")
        if dep_text:
            lines.append(dep_text)
        for s in steps:
            lines.append(f"- {s}")
        lines.append(f"- **Verificación:** {verification}")
        lines.append("")

        if task_num % 4 == 0:
            sprint_num += 1
        task_num += 1

    content = "\n".join(lines)

    dest_file = latest / "tasks.md"
    dest_file.write_text(content)
    print(f"\n✅ Tasks guardadas en {dest_file}")


# ── HTML Preview ──────────────────────────────────────────────────────


def cmd_html_preview(args: Any) -> None:
    """Genera scaffolding de HTML preview."""
    feature = args.feature_name or "preview"
    root = _project_root()
    preview_dir = root / "previews" / _sanitize_name(feature)
    _ensure_dir(str(preview_dir))

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Preview: {feature}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #f5f5f5; color: #333; padding: 20px; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  header {{ background: #1a1a2e; color: white; padding: 20px 30px; border-radius: 8px; margin-bottom: 24px; }}
  header h1 {{ font-size: 1.5rem; }}
  header p {{ opacity: 0.8; margin-top: 4px; }}
  .card {{ background: white; border-radius: 8px; padding: 24px; margin-bottom: 16px;
           box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .stat-card {{ background: white; border-radius: 8px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .stat-card .value {{ font-size: 2rem; font-weight: bold; color: #1a1a2e; }}
  .stat-card .label {{ font-size: 0.85rem; color: #666; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 12px 8px; border-bottom: 1px solid #eee; }}
  th {{ color: #666; font-size: 0.8rem; text-transform: uppercase; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 500; }}
  .badge-active {{ background: #e8f5e9; color: #2e7d32; }}
  .badge-pending {{ background: #fff3e0; color: #e65100; }}
  .status-bar {{ height: 4px; background: #e0e0e0; border-radius: 2px; margin: 16px 0; }}
  .status-bar .fill {{ height: 100%; background: #1a1a2e; border-radius: 2px; width: 65%; }}
  .footer {{ text-align: center; color: #999; font-size: 0.85rem; margin-top: 40px; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🔍 Preview: {feature}</h1>
    <p>Datos ficticios para aprobación visual · {datetime.now().strftime('%d %b %Y')}</p>
  </header>

  <div class="stats">
    <div class="stat-card"><div class="value">12</div><div class="label">Total registros</div></div>
    <div class="stat-card"><div class="value">8</div><div class="label">Activos</div></div>
    <div class="stat-card"><div class="value">4</div><div class="label">Pendientes</div></div>
    <div class="stat-card"><div class="value">92%</div><div class="label">Tasa de éxito</div></div>
  </div>

  <div class="card">
    <h3 style="margin-bottom: 12px;">Registros Recientes</h3>
    <table>
      <thead><tr><th>ID</th><th>Nombre</th><th>Estado</th><th>Fecha</th></tr></thead>
      <tbody>
        <tr><td>#001</td><td>Juan Pérez</td><td><span class="badge badge-active">Activo</span></td><td>2026-07-10</td></tr>
        <tr><td>#002</td><td>María García</td><td><span class="badge badge-pending">Pendiente</span></td><td>2026-07-09</td></tr>
        <tr><td>#003</td><td>Carlos López</td><td><span class="badge badge-active">Activo</span></td><td>2026-07-08</td></tr>
        <tr><td>#004</td><td>Ana Martínez</td><td><span class="badge badge-active">Activo</span></td><td>2026-07-07</td></tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h3 style="margin-bottom: 12px;">Progreso del Pipeline</h3>
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
      <span>Completado</span><span>65%</span>
    </div>
    <div class="status-bar"><div class="fill"></div></div>
  </div>

  <div class="footer">
    <p>Preview generado para aprobación — no es código funcional</p>
  </div>
</div>
</body>
</html>"""

    dest_file = preview_dir / "index.html"
    dest_file.write_text(html)
    print(f"\n✅ HTML preview guardada en {dest_file}")
    print(f"   Ábrela en tu navegador: file://{dest_file.resolve()}")


# ── MCP Server ────────────────────────────────────────────────────────


def cmd_mcp_server(args: Any) -> None:
    """Scaffolding de MCP server."""
    feature = args.feature_name or "hermes-sdd-mcp"
    root = _project_root()
    mcp_dir = root / "mcp" / _sanitize_name(feature)
    _ensure_dir(str(mcp_dir))

    # server.py
    server_py = f'''"""
MCP Server: {feature}

Generado por hermes-sdd skill. Implementa herramientas para exponer
capacidades a otros agentes Hermes.
"""

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types


server = Server("{_sanitize_name(feature)}")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Lista las herramientas disponibles."""
    return [
        types.Tool(
            name="search",
            description="Buscar en el recurso principal",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "query": {{
                        "type": "string",
                        "description": "Término de búsqueda",
                    }},
                    "limit": {{
                        "type": "integer",
                        "description": "Máximo de resultados",
                        "default": 10,
                    }},
                }},
                "required": ["query"],
            }},
        ),
        types.Tool(
            name="get_detail",
            description="Obtener detalle de un registro por ID",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "id": {{
                        "type": "string",
                        "description": "ID del registro",
                    }},
                }},
                "required": ["id"],
            }},
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Ejecuta una herramienta."""
    if name == "search":
        query = (arguments or {{}}).get("query", "")
        limit = (arguments or {{}}).get("limit", 10)
        # TODO: implementar búsqueda real
        return [types.TextContent(type="text", text=f"Búsqueda: {{query}} (limit {{limit}})\\nResultados simulados.")]

    elif name == "get_detail":
        record_id = (arguments or {{}}).get("id", "")
        # TODO: implementar consulta real
        return [types.TextContent(type="text", text=f"Detalle del registro {{record_id}}:\\n(simulado)")]

    raise ValueError(f"Herramienta desconocida: {{name}}")


async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="{_sanitize_name(feature)}",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={{}},
                ),
            ),
        )
'''

    # README
    readme = f"""# MCP Server: {feature}

Servidor MCP generado por **hermes-sdd** skill.

## Instalación

```bash
cd mcp/{_sanitize_name(feature)}
pip install -r requirements.txt
```

## Uso

```bash
python server.py
```

## Configuración en Hermes

Agregar al `config.yaml` de Hermes:

```yaml
mcp_servers:
  {_sanitize_name(feature)}:
    command: python
    args:
      - mcp/{_sanitize_name(feature)}/server.py
    trust: tools
```

## Herramientas

- `search` — Buscar en el recurso principal
- `get_detail` — Obtener detalle de un registro por ID

## Desarrollo

Editar `server.py` para implementar la lógica real de cada herramienta.
"""

    # requirements
    requirements = "mcp>=1.0.0\nhttpx>=0.27.0\n"

    (mcp_dir / "server.py").write_text(server_py)
    (mcp_dir / "README.md").write_text(readme)
    (mcp_dir / "requirements.txt").write_text(requirements)

    print(f"\n✅ MCP server scaffolding en {mcp_dir}")
    print(f"   - server.py: herramientas esqueleto")
    print(f"   - README.md: instrucciones")
    print(f"   - requirements.txt: dependencias")


# ── Status ────────────────────────────────────────────────────────────


def cmd_status(args: Any) -> None:
    """Muestra el progreso del feature actual."""
    root = _project_root()
    spec_dirs = sorted((root / "specs").iterdir()) if (root / "specs").exists() else []

    if not spec_dirs:
        print("❌ No hay features en progreso.")
        return

    latest = spec_dirs[-1]
    spec = _read_file(str(latest / "spec.md"))
    plan = _read_file(str(latest / "plan.md"))
    tasks = _read_file(str(latest / "tasks.md"))

    total_tasks = len(re.findall(r"### \[P\d\] task_\d{3}", tasks))
    completed_tasks = len(re.findall(r"- \[x\]", tasks))

    print(f"\n{'='*50}")
    print(f"  SDD Status: {latest.name}")
    print(f"{'='*50}")
    print(f"  Spec:       {'✅' if spec else '❌'} {len(spec.split(chr(10)))} líneas")
    print(f"  Plan:       {'✅' if plan else '❌'} {len(plan.split(chr(10)))} líneas")
    print(f"  Tasks:      {'✅' if tasks else '❌'} {total_tasks} tareas ({completed_tasks} completadas)")
    print(f"  Progreso:   {completed_tasks}/{total_tasks}")
    print(f"{'='*50}\n")


# ── Checklist ─────────────────────────────────────────────────────────


def cmd_checklist(args: Any) -> None:
    """Genera checklist de calidad con OWASP ASI."""
    print("=== SDD: Quality Checklist ===")
    print("Nivel: Spec-Anchored\n")
    print("## SDD Quality Gates")
    print("- [ ] Constitution existe y se respeta")
    print("- [ ] Spec usa EARS para acceptance criteria")
    print("- [ ] Out of Scope definido")
    print("- [ ] Plan tiene factores de éxito y anti-patrones")
    print("- [ ] Tasks atomicas (15-30 min cada una)")
    print("- [ ] HTML preview aprobada por el usuario")
    print()
    print("## OWASP ASI 2026 Security Checklist")
    print()
    print("*Seleccionar según el tipo de proyecto:*")
    print()
    print("### Alto Riesgo (aplica siempre)")
    print("- [ ] [ASI05] Código generado se ejecuta en sandbox (Docker network:none o Wasm)")
    print("- [ ] [ASI06] Memoria persistente aislada por tenant con expiración")
    print()
    print("### Medio Riesgo (aplica si hay tools/APIs)")
    print("- [ ] [ASI01] Inputs externos tratados como no confiables")
    print("- [ ] [ASI02] Tools con scopes mínimos y rate limiting")
    print("- [ ] [ASI03] JIT ephemeral tokens en lugar de API keys fijas")
    print("- [ ] [ASI04] Dependencias pinned por hash, allowlist MCP")
    print()
    print("### Multi-Agente (aplica solo si hay >1 agente)")
    print("- [ ] [ASI07] Inter-agent comm con mTLS o firma criptográfica")
    print("- [ ] [ASI08] Circuit breakers y fan-out caps")
    print()
    print("### Monitoreo Continuo")
    print("- [ ] [ASI09] Confidence scores visibles al usuario")
    print("- [ ] [ASI10] Log de objetivos del agente para detección de drift")
    print()
    print("## Testing")
    print("- [ ] TDD: tests escritos ANTES del código")
    print("- [ ] Cada test se vio fallar antes de implementar")
    print("- [ ] Tests de integración cubren paths críticos")
    print("- [ ] Record-Decisions-Not-HTTP para tests de agentes (no mock HTTP)")
    print()
    print("## Performance")
    print("- [ ] Lazy tool loading configurado (si aplica)")
    print("- [ ] Prompt caching estructurado (estático arriba, dinámico abajo)")
    print("- [ ] Cost-ceiling definido para llamadas API")


# ── Help ──────────────────────────────────────────────────────────────


# ── Main ──────────────────────────────────────────────────────────────


def _sanitize_name(name: str) -> str:
    """Convierte un nombre a slug de directorio."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name)
    return name.strip("-")[:64]


def main() -> None:
    parser = argparse.ArgumentParser(description="hermes-sdd: Comandos SDD para Hermes Agent")
    sub = parser.add_subparsers(dest="command", required=True)

    # specify
    p_specify = sub.add_parser("specify", help="Genera spec.md con EARS")
    p_specify.add_argument("description", nargs="?", default="", help="Descripción de la feature")

    # plan
    p_plan = sub.add_parser("plan", help="Genera plan.md")
    p_plan.add_argument("tech_stack", nargs="?", default="", help="Tech stack (opcional)")

    # tasks
    sub.add_parser("tasks", help="Genera tasks.md interactivamente")

    # html-preview
    p_preview = sub.add_parser("html-preview", help="Genera HTML preview")
    p_preview.add_argument("feature_name", nargs="?", default="preview", help="Nombre de la feature")

    # mcp-server
    p_mcp = sub.add_parser("mcp-server", help="Scaffolding de MCP server")
    p_mcp.add_argument("feature_name", nargs="?", default="hermes-sdd-mcp", help="Nombre del MCP server")

    # status
    sub.add_parser("status", help="Muestra progreso del feature actual")

    # checklist
    sub.add_parser("checklist", help="Genera checklist de calidad")

    # constitution
    sub.add_parser("constitution", help="Genera constitution.md interactivamente")

    args = parser.parse_args()

    handlers = {
        "constitution": cmd_constitution,
        "specify": cmd_specify,
        "plan": cmd_plan,
        "tasks": cmd_tasks,
        "html-preview": cmd_html_preview,
        "mcp-server": cmd_mcp_server,
        "status": cmd_status,
        "checklist": cmd_checklist,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
