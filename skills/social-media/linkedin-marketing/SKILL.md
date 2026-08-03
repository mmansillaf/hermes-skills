---
name: linkedin-marketing
description: LinkedIn marketing automation for B2B professional services — profile optimization, content creation (human-sounding posts), lead generation, anti-detection, and outreach via MCP servers, CLI tools, and Hermes skills.
triggers:
  - User asks about LinkedIn strategy, content, lead gen, or prospecting
  - User wants to post, comment, or engage on LinkedIn via agent
  - User wants to read, search, or monitor LinkedIn posts, feed, or hashtags (see references/linkedin-content-reading.md)
  - User wants to find prospects, clients, or decision-makers on LinkedIn
  - User needs anti-detection guidance for LinkedIn automation
  - User is positioning B2B services (legal tech, RAG, AI consulting) on LinkedIn
version: 1.0
---

# LinkedIn Marketing Skill

## Tool Landscape Overview

LinkedIn has NO open general-purpose API. There are 4 approaches, ordered by safety:

| Approach | Risk | Capability | Setup Time |
|----------|------|-----------|------------|
| MCP server (API oficial) | BAJO | Posts, comments, reactions, events, profile | 15 min |
| MCP server (browser scraping) | MEDIO | Read feed, search posts, search people, profiles | 20 min |
| MCP server (cloud browser) | BAJO-MEDIO | + search profiles, messages, leads | 10 min |
| Python Voyager client (cookie) | ALTO | Full access (search, DM, scrape) | 5 min |
| Browser automation (Playwright) | ALTO | Full access, highest ban risk | 30 min |

> **⚠️ ALCANCE:** Esta skill cubre PUBLICACIÓN y MARKETING (crear posts, comentar, reaccionar). Para **LEER** posts, feed, o buscar contenido — que requiere browser scraping y herramientas distintas — ver `references/linkedin-content-reading.md`. Ambos casos se documentan aquí porque comparten el ecosistema LinkedIn, pero son enfoques diferentes (API OAuth vs browser scraping).

## MCP Servers for Hermes Integration

### linkedin-mcp-server (API oficial — RECOMENDADO para contenido)
- **Repo:** github.com/souravdasbiswas/linkedin-mcp-server
- **Qué hace:** Crea posts, comenta, reacciona, crea eventos, sube imágenes
- **Auth:** OAuth 2.0 + LinkedIn Developer App
- **Config en Hermes config.yaml:**
  ```yaml
  mcp_servers:
    linkedin:
      command: node
      args: ["/path/to/linkedin-mcp-server/dist/index.js"]
      env:
        LINKEDIN_CLIENT_ID: "<client_id>"
        LINKEDIN_CLIENT_SECRET: "<client_secret>"
  ```
- **Setup:** Ver `references/oauth-setup-guide.md` — instrucciones detalladas paso a paso para crear la app, obtener Client ID + Secret, y configurar OAuth. ⚠️ El navegador automatizado NO puede iniciar sesión en LinkedIn — dar las instrucciones al usuario para que las siga en su navegador y devuelva los códigos.

### stickerdaniel/linkedin-mcp-server (Browser scraping — para LEER feed/posts)
- **Repo:** github.com/stickerdaniel/linkedin-mcp-server
- **PyPI:** `linkedin-scraper-mcp` (vía `uvx`)
- **Qué hace:** Lee feed personal (`get_feed`), busca posts/people/profiles/jobs, envía mensajes
- **Auth:** Login manual en navegador (NO OAuth, NO email/password env vars). Usa `--login` flag que abre Chromium para login interactivo; la sesión se guarda en `~/.linkedin-mcp/profile/`
- **Backend:** Patchright (Playwright fork con anti-detección), Python 3.12-3.14
- **Stars/Status:** 2,186 ★, ~963 commits, activo (actualizado Jun 2026)
- **Riesgo:** Medio — usa browser scraping, viola ToS. Usar cuenta secundaria.
- **Config en Hermes config.yaml:**
  ```yaml
  mcp_servers:
    linkedin-reader:
      command: "uvx"
      args: ["linkedin-scraper-mcp@latest", "--tool-timeout", "300", "--timeout", "15000"]
      timeout: 300
      connect_timeout: 90
  ```
- **Primer login (en máquina CON monitor):**
  ```bash
  uvx linkedin-scraper-mcp@latest --login --no-headless
  ```
  Esto abre Chromium. Loguearse manualmente, resolver captcha si aparece.
  La sesión queda guardada en `~/.linkedin-mcp/profile/`.
  Copiar esa carpeta al servidor si el login se hace en otra máquina.
- **Nota:** Es el ÚNICO MCP server que implementa lectura de feed a fecha de Jun 2026. La API oficial LinkedIn tiene scope `r_member_social` cerrado. Instalación local: `git clone <repo> && cd linkedin-mcp-server && uv sync` (no necesita Node.js).

### linkedapi-mcp (Cloud browser — para leads/outreach)
- **Repo:** github.com/Linked-API/linkedapi-mcp
- **Qué hace:** Busca perfiles, envía mensajes, analiza leads via cloud browser
- **Auth:** API key del servicio Linked-API
- **Riesgo:** Menor que Voyager directo porque el browser corre en su cloud, no en tu IP

## Content Creation Workflow

### Paso 1: Definir voz y audiencia
Antes de cualquier contenido, capturar en memory:
- Tu nicho y expertise específico
- Tu audiencia objetivo (roles, industrias, geografías)
- Tu tono (profesional, técnico, pedagógico, provocador)
- Palabras y frases que usas naturalmente vs AI tells a evitar

### Paso 2: Generar drafts con linkedin-post-writer
Usar hook formulas probadas (2026):
1. Anaphora — repetición de apertura para ritmo
2. R.I.P. Obituary — "RIP búsqueda manual de jurisprudencia"
3. Year-over-year pivot — "Hace 1 año usaba X. Hoy construí Y"
4. Curiosity gap — "El problema que ningún abogado ve en sus PDFs"
5. Before/after — "Así buscábamos antes. Así buscamos ahora."
6. Contrarian — "Tu ERP no necesita AI. Necesita RAG."
7. List with twist — "3 cosas que aprendí procesando 800K resoluciones"
8. Storytelling técnico — "Cómo pasé de PDFs a Knowledge Graph en 3 meses"

### Paso 3: Humanizar (CRÍTICO)
Usar linkedin-humanizer para eliminar:
- Em dashes (—) y conectores AI típicos
- "Leverage", "delve", "harness", "transformative", "game-changer"
- Listas de 3 puntos perfectamente paralelas
- Arcos narrativos predecibles (tensión → resolución siempre)
- Cero imperfecciones (insertar 1 flow-break genuino por post)
- Registro emocional mapeado (no fingir indignación sin trigger real)

### Paso 4: Auditar antes de publicar
Verificar:
- Non-Detection Index (NDI) > 5.0
- Variedad estructural (no repetir mismo formato)
- Epistemic verification (datos contrastables)
- Valor real para la audiencia (no autopromoción vacía)

## Anti-Detection Methodology (2 niveles)

### Level 1: Behavioral Rules
| # | Regla | Por qué |
|---|-------|---------|
| 1 | Max 2/5 comments mencionan tu herramienta | 3/5 fue flag en Day 1 |
| 2 | Variar estructura de comentarios | Repetición = #2 vector de detección |
| 3 | Al menos 1/5 comentarios fuera de tu nicho | 0/5 = 6.0/10, 1-2/5 = 8.5-9.0 |
| 4 | Max 1 frase promocional por sesión | "Lo uso todos los días" = flag instantáneo |
| 5 | Like-only en acuerdos | Extender hilos de acuerdo suena artificial |
| 6 | Verificar datos antes de afirmar | Incidente perfil-B |
| 7 | 1+ comentario en posts con 200+ reacciones | 7-12x reach multiplier |

### Level 2: Structural Naturalness
| Tell | Patrón | Fix |
|------|--------|-----|
| Simetría estructural | Todo post: Hook → Cuerpo (3 bloques) → Cierre | Rotar 6+ estructuras, max 2/semana misma |
| Paralelismo sintáctico | Listas con estructura gramatical idéntica | Romper: 1 elemento debe diferir |
| Informalidad ingenierizada | Marcadores informales en posiciones estratégicas | Debe emerger de la estructura |
| Cero imperfecciones | Sin pensamientos interrumpidos | Insertar 1 flow-break genuino por post |
| Casos de estudio cinematográficos | Setup-payoff perfecto con quotes limpios | Detalles sucios + vague memory |
| Arco emocional predecible | tensión → resolución siempre | 1 post/semana sin resolución |
| Registro emocional mapeado | Miércoles = indignación construida | Posts emocionales necesitan trigger real |

### Non-Detection Index (NDI)
```
NDI = (L1 × 2 + L2 × 1) / (L1 + L2 + L3) × 10

NDI > 5.0  = saludable
NDI < 3.0  = investigar
NDI < 4.0 dos semanas = pausa 48h y auditar
```

## Lead Generation Strategy for B2B Services

### Ideal Customer Profile (ICP)
Definir con precisión:
- Roles exactos (títulos que usan)
- Rango de tamaño de empresa
- Verticales industriales
- Señales de compra (hiring, funding, expansion)
- Tech stack indicators
- Dolor específico que resuena

### Content-Led Approach (RECOMENDADO)
Para servicios profesionales (legal tech, RAG, AI consulting):
1. **NO hacer outreach masivo** — riesgo de ban, y tu ventaja es autoridad, no volumen
2. **Publicar 3-4 posts/semana** que demuestren expertise real, no promocionales
3. **Comment-to-DM táctico** — cuando alguien comenta en posts de tu nicho, iniciar DM
4. **Intent signal tracking** — quién ve tu perfil, engagea con tu contenido, comenta en posts de competidores
5. **Contenido que educa** — el lead caliente se autorevela al interactuar

### Pain Point Mapping
Ejemplo para legal tech RAG:
| Dolor del cliente | Tu solución |
|-------------------|-------------|
| "Harvey/Lexis+AI no entiende jurisprudencia local" | RAG sobre resoluciones reales del país |
| "8+ h/semana buscando documentos" | Búsqueda semántica + graph en segundos |
| "No encontramos precedentes relevantes" | Knowledge Graph conecta resoluciones relacionadas |
| "Documentos en PDFs sin estructura" | Pipeline clasificación + extracción automatizada |
| "No podemos mandar datos al cloud" | Stack 100% local (llama.cpp, Qwen, ChromaDB) |
| "Gastamos $500+/mes en APIs" | Batch API ~$51 para 500K docs, o local $0 |
| "El AI alucina citas legales" | RAG con verificación epistemológica |

## Tools Reference

### MCP Servers
- stickerdaniel/linkedin-mcp-server: github.com/stickerdaniel/linkedin-mcp-server — **LEER** feed/posts (browser scraping, Python/uvx)
- linkedin-mcp-server (API oficial): github.com/souravdasbiswas/linkedin-mcp-server — PUBLICAR (OAuth 2.0)
- linkedapi-mcp (cloud browser): github.com/Linked-API/linkedapi-mcp — leads/outreach

### CLI & Python
- open-linkedin-api: github.com/EseToni/open-linkedin-api (Voyager client, ALTO riesgo)
- linkedin-agent-cli: github.com/eracle/linkedin-cli (CLI with JSON output)
- LinkedInDumper: github.com/l4rm4nd/LinkedInDumper (company employee dump)
- OpenOutreach: github.com/eracle/OpenOutreach (full lead gen system)

### Skills Exportables (Claude Code / Codex → adaptables a Hermes)
- sergebulaev/linkedin-skills — 10 skills MIT (post-writer, humanizer, content planner, etc.)
- backpropagation6/claude-linkedin-automation — battle-tested anti-detection system (27+ days, 0 detections, 3.9% engagement rate)

### Servicios Comerciales
- Publora (publora.com) — API publishing cross-platform
- Apify (apify.com) — scraping LinkedIn sin cookies
- Landbase (landbase.com) — AI lead gen for legal tech
- ConnectSafely / Overloop / Expandi — outreach tools (pagos)

## Pitfalls
- NO hacer outreach masivo desde cuenta nueva — warm up gradualmente (~100 connection requests/semana)
- NO publicar más de 1 post/día — LinkedIn penaliza
- NO usar plantillas genéricas en DMs — personalización o nada
- NO confiar en tools que prometen "AI automation" sin anti-detection real
- El navegador automatizado NO puede iniciar sesión en LinkedIn Developer Portal — dar instrucciones paso a paso al usuario para que las siga en su navegador y devuelva los códigos. No insistir con browser_navigate tras detectar login wall.
- El MCP server oficial NO permite buscar personas ni enviar mensajes directos
- La API Voyager (no oficial) cambia frecuentemente — requiere mantenimiento
- Los skills de sergebulaev están diseñados para Claude Code — adaptar formato a SKILL.md de Hermes
- Guardar cookie `li_at` para open-linkedin-api requiere extracción manual desde el navegador

## Related Files
- `references/oauth-setup-guide.md` — paso a paso para crear la app developer, obtener Client ID + Secret, y configurar OAuth
- `references/legal-tech-pain-points.md` — pain point mapping para RAG legal
- `references/anti-detection-excerpt.md` — anti-detection playbook condensado
- `references/tool-comparison.md` — comparativa detallada de herramientas
- `references/linkedin-content-reading.md` — cómo LEER posts/feed (browser scraping con stickerdaniel/linkedin-mcp-server, alternativas, riesgos)
