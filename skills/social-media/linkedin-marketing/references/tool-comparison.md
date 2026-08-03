# LinkedIn Tool Comparison

## MCP Servers

| Característica | linkedin-mcp-server | linkedapi-mcp |
|----------------|---------------------|---------------|
| **Repo** | github.com/souravdasbiswas/linkedin-mcp-server | github.com/Linked-API/linkedapi-mcp |
| **Tipo API** | Oficial LinkedIn REST v2 | Voyager via cloud browser |
| **Auth** | OAuth 2.0 + Developer App | API key + cloud session |
| **Crear posts** | SI | SI |
| **Comentar** | SI | SI |
| **Reaccionar** | SI | NO explícito |
| **Buscar perfiles** | NO | SI |
| **Enviar mensajes** | NO | SI |
| **Analizar leads** | NO | SI |
| **Crear eventos** | SI | NO |
| **Riesgo cuenta** | BAJO (API oficial) | BAJO-MEDIO (cloud) |
| **Costo** | Gratis | Servicio terceros |
| **Setup** | 15 min | 10 min |
| **Idioma** | TypeScript | TypeScript |
| **Hermes config** | config.yaml stdio | config.yaml stdio |

## CLI & Python Libraries

| Herramienta | Acceso | Riesgo | Output | Ideal para |
|-------------|--------|--------|--------|------------|
| open-linkedin-api | Voyager (cookie) | ALTO | Python objects | Scripting custom |
| linkedin-agent-cli | Voyager (cookie) | ALTO | JSON | Tool-use Hermes |
| LinkedInDumper | Voyager (cookie) | ALTO | CSV/JSON | Dump empleados |
| OpenOutreach | Browser + Voyager | ALTO | CRM+leads | Lead gen completo |
| LinkedinPy | Voyager (cookie) | ALTO | Python | Automatización simple |
| linkauto | Voyager (cookie) | ALTO | Async Python | Proyectos async |

## Skills Exportables (Claude Code / Codex → adaptables a Hermes)

### sergebulaev/linkedin-skills (10 skills, MIT)

| Skill | Función | Hermes? |
|-------|---------|---------|
| Post Writer | Drafts virales con 10 hook formulas | Fácil |
| Comment Drafter | Comenta desde URL del post | Fácil |
| Reply Handler | Replies respetando flattening | Media |
| Post Audit | Algoritmo 2026 check | Fácil |
| Humanizer | Elimina AI tells | Fácil |
| Hook Extractor | Reverse-engineer de posts virales | Fácil |
| Content Planner | Plan semanal | Fácil |
| Engagement Monitor | Trackea threads + engagers | Media |
| Profile Optimizer | Headline, about, experiencia | Fácil |
| Employee Advocacy | Programa de equipo | Baja |

### backpropagation6/claude-linkedin-automation (MIT)

| Componente | Valor |
|------------|-------|
| Anti-detection L1 | 7 behavioral rules validadas empíricamente |
| Anti-detection L2 | 7 structural tells + 6 post structures |
| NDI Formula | Non-Detection Index matemático |
| Epistemic Gate | 7-checkpoint verification |
| Wizard 5 fases | Identity → Strategy → Engagement → Task Plan → Deploy |
| Tasks | 10 tareas (post, engage, reply, DM, scout, audit, plan, diary, report, outreach) |
| Producción | 27+ días, 0 detecciones, 3.9% engagement rate |

## Servicios Comerciales

| Servicio | Función | Precio | Para qué |
|----------|---------|--------|----------|
| **Publora** | Publishing API cross-platform | Free: 15 posts/mes | Publicar directo desde agente |
| **Apify** | LinkedIn scraping (no-cookies) | Free: $5/mes crédito | Leer posts, comments, engagers |
| **Landbase** | AI lead gen para legal tech | Pago (enterprise) | Encontrar prospects ICP |
| **ConnectSafely** | LinkedIn automation engagement | $10/mes | Inbound engagement |
| **Overloop** | Multi-account outreach | ~$50-100/mes | Outreach multi-cuenta |
| **Expandi** | LinkedIn automation | ~$99/mes | Outreach tradicional |
| **Proxycurl** | Profile data API | Pay-per-use | Enriquecer perfiles |
| **Unipile** | Unified messaging API | Trial 7 días | Mensajería multi-platform |
