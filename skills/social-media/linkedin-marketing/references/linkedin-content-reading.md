# LinkedIn Content Reading — Approaches & Tooling

> **Propósito:** Guía para LEER posts, feed, y buscar contenido en LinkedIn programáticamente.
> Esto es COMPLEMENTARIO al flujo de PUBLICACIÓN (cubierto en el SKILL.md principal).
> Ambos están en esta skill porque comparten el ecosistema LinkedIn, pero usan herramientas distintas.

---

## Problema Central

LinkedIn NO ofrece API oficial para leer el feed de otros miembros o buscar posts públicos.
El scope `r_member_social` de la API v2 está **cerrado** por LinkedIn ("not accepting access requests").
Tampoco existe un endpoint oficial de feed personal.

Esto significa que toda lectura programática de LinkedIn requiere **browser scraping**,
lo que viola la Sección 8.2 de los ToS de LinkedIn y conlleva riesgo de bloqueo de cuenta.

---

## Estado del Ecosistema (Junio 2026)

### APIs Oficiales

| Fuente | Capacidad | Scope | Estado |
|--------|-----------|-------|--------|
| LinkedIn API v2 (`/rest/posts`) | Crear posts, leer posts PROPIOS | `w_member_social`, `r_organization_social` | Funciona |
| LinkedIn API v2 (`r_member_social`) | Leer posts DE OTROS miembros | `r_member_social` | **CERRADO** — no acepta requests |
| LinkedIn API v2 Feed | No existe | — | — |
| LinkedIn API v2 Search | No existe | — | — |

### APIs No Oficiales

| Fuente | Capacidad | Última Actualización | Riesgo |
|--------|-----------|---------------------|--------|
| Voyager API (linkedin-api PyPI v2.3.1) | Search profiles, get_profile, messages | Nov 2024 — **abandonado** | Alto |
| Voyager (toxtli fork con keywords) | Feed posts (+keywords) | 2019 — **obsoleto** | Alto |

### MCP Servers

| MCP Server | Lee Feed? | Busca Posts? | Backend | Riesgo | Estado |
|------------|-----------|-------------|---------|--------|--------|
| **stickerdaniel/linkedin-mcp-server** ★2,186 | **SÍ** | **SÍ** | Patchright (Playwright fork) | Medio | **ACTIVO** (Jun 2026) |
| souravdasbiswas/linkedin-mcp-server | NO | NO | OAuth 2.0 oficial | Bajo | Activo |
| pegausheavy/linkedin-mcp | NO | NO | OAuth 2.0 oficial | Bajo | Activo |
| linkedapi-mcp | SÍ (cloud) | SÍ (cloud) | Cloud browser | Bajo-Medio | Activo |

### Librerías Python

| Librería | Capacidad | Última Actualización | Stars |
|----------|-----------|---------------------|-------|
| joeyism/linkedin_scraper | Company posts, profiles, jobs | Abril 2026 | 4,204 ★ |
| tomquirk/linkedin-api (PyPI) | Search profiles, get_profile | Nov 2024 (repo borrado) | — |

---

## Approach Recomendado

### Opción 1 (RECOMENDADA): stickerdaniel/linkedin-mcp-server

**Qué hace:** MCP server Python que usa Patchright (Playwright fork) para navegar LinkedIn
y exponer tools como `get_feed`, `search_people`, `search_posts`, `get_profile_posts`.

**Ventajas:**
- Único MCP server que implementa lectura de feed (Jun 2026)
- Activo (actualizado hoy, 963 commits)
- Arquitectura MCP nativa para Hermes — tools disponibles automáticamente
- Anti-detección incorporada (Patchright)

**Desventajas:**
- Riesgo de ban de cuenta (usar cuenta secundaria)
- Depende de que LinkedIn no cambie su HTML
- Login requiere navegador con display gráfico (usar `--login` flag)

**Setup (vía uvx, recomendado — sin clonar):**
```bash
# Solo para login inicial (en máquina CON monitor):
uvx linkedin-scraper-mcp@latest --login --no-headless
# Se abre Chromium, loguearse manualmente, resolver captcha si aparece.
# La sesión queda en ~/.linkedin-mcp/profile/
```

**Setup (local):**
```bash
git clone https://github.com/stickerdaniel/linkedin-mcp-server.git
cd linkedin-mcp-server
uv sync
```

Config en `config.yaml`:
```yaml
mcp_servers:
  linkedin-reader:
    command: "uvx"
    args: ["linkedin-scraper-mcp@latest", "--tool-timeout", "300", "--timeout", "15000"]
    timeout: 300
    connect_timeout: 90
```

> **⚠️ Importante:** El servidor NO usa `LINKEDIN_EMAIL`/`LINKEDIN_PASSWORD` como env vars.
> La autenticación es mediante login manual en navegador Chromium que se guarda en
> `~/.linkedin-mcp/profile/`. Para login headless, ejecutar `uvx linkedin-scraper-mcp@latest --login`
> en una máquina con monitor y copiar el profile al servidor.

### Opción 2: Script Python con rebrowser-playwright (fallback)

Si el MCP server falla o se prefiere Python puro, usar `rebrowser-playwright`
(Playwright fork con parches anti-detección mejorados):

```python
from rebrowser_playwright.sync_api import sync_playwright
# ... navegar linkedin.com/search/results/all/?keywords=...
# ... extraer posts del DOM
```

**Ventajas:** Control total, no depende de MCP server externo.
**Desventajas:** Más código que mantener, anti-detección manual.

### Opción 3: Apify (pago)

Actores de Apify como "LinkedIn Posts Scraper" — funcionan, pero son de pago.
Útiles como respaldo si las opciones 1 y 2 fallan.

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Ban de cuenta | Media | Alto | Usar cuenta SECUNDARIA, no la principal |
| LinkedIn cambia HTML | Alta | Medio | Tests periódicos, mantener fork propio |
| 2FA bloquea login | Media | Alto | Documentar setup con cookie manual |
| Rate limiting | Alta | Bajo | ~100 req/hora, respetar delays |
| MCP server desactualizado | Baja | Medio | Fork propio + PRs upstream |

---

## Referencias

- stickerdaniel/linkedin-mcp-server: https://github.com/stickerdaniel/linkedin-mcp-server
- joeyism/linkedin_scraper: https://github.com/joeyism/linkedin_scraper
- rebrowser-playwright: `pip install rebrowser-playwright`
- LinkedIn API v2 docs: https://learn.microsoft.com/en-us/linkedin/marketing/

## Verificación Post-Setup

Después de configurar el MCP server en config.yaml y hacer login:

```bash
# 1. El servidor carga correctamente con Hermes
hermes mcp test linkedin-reader
# Expected: ✓ Connected, ✓ Tools discovered: 17

# 2. La sesión de LinkedIn sigue siendo válida
uvx linkedin-scraper-mcp@latest --status
# Expected: "✅ Session is valid (profile: ~/.linkedin-mcp/profile)"
```

## Tools Confirmadas (v4.13.3, stickerdaniel/linkedin-mcp-server)

Verificadas funcionando Jun 2026:

| Tool | Propósito | Estado |
|------|-----------|--------|
| get_feed | Leer feed personal | working |
| search_people | Buscar personas por keyword/company | working |
| get_person_profile | Perfil completo con secciones | working |
| get_my_profile | Perfil propio | working |
| get_company_posts | Posts de empresa | working |
| search_companies | Buscar empresas | working |
| get_company_employees | Empleados por compañía | working |
| get_company_profile | Perfil de empresa | working |
| search_jobs | Buscar trabajos | working |
| get_job_details | Detalles de oferta | working |
| get_inbox | Bandeja de mensajes | working |
| get_conversation | Leer conversación | status varies |
| search_conversations | Buscar en mensajes | working |
| send_message | Enviar DM | confirmation needed |
| connect_with_person | Solicitud conexión | issues tracked |
| get_sidebar_profiles | Perfiles sugeridos | working |
| close_session | Cerrar navegador | working |
