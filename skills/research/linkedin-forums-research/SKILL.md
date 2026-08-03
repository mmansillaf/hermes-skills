---
name: linkedin-forums-research
description: >-
  Investigate LinkedIn (profiles, jobs, Pulse articles), Hacker News, Stack
  Overflow, and professional sources for any domain. Searches via Google
  dorking (Serper API), Jina AI Reader (Pulse article bypass), and public
  APIs. No scraping of LinkedIn directly.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin, research, legal, rag, devops, career, skills]
    related_skills: [web-deep-research, research-synthesis, plan]
---

# LinkedIn + Forums Research

> **Propósito:** Investigar LinkedIn (perfiles, vacantes, artículos Pulse),
> Hacker News, Stack Overflow y foros profesionales para CUALQUIER dominio
> — DevOps, Legal Tech, RAG, AI, Derecho, LATAM.
>
> **No hace scraping directo de LinkedIn** — usa Google dorking legal
> (`site:linkedin.com/in/`) vía Serper API, proxy de Google Translate para
> Jobs, y Jina AI Reader para artículos Pulse.

## Ubicación del proyecto

```
/mnt/d/PyCode/linkedin-forums-research/
├── main.py                  ← CLI principal
├── perfil_ejemplo.json       ← Plantilla de perfil profesional
├── src/
│   ├── linkedin_intel.py     ← LinkedIn vía Google dorking + Serper
│   ├── hn_scout.py           ← Hacker News (Algolia API)
│   ├── stack_scout.py        ← Stack Overflow (Stack Exchange API)
│   └── synthesizer.py        ← Fusión, gap analysis, reportes
├── reports/                  ← Reportes .md + .txt generados
├── cache/                    ← Cache de resultados JSON
├── tests/                    ← Tests unitarios
└── PLAN.md                   ← Plan de desarrollo original
```

## Queries por dominio (más allá de DevOps)

### Legal Tech / RAG / AI para abogados

```text
# Artículos RAG legal
site:linkedin.com/pulse RAG retrieval augmented generation legal
site:linkedin.com/pulse "retrieval augmented generation" law legal

# IA + Abogados (español)
site:linkedin.com/pulse "inteligencia artificial" abogados derecho 2025 2026
site:linkedin.com/pulse IA generativa derecho abogados Perú Latinoamerica

# Legal Tech Developer/DevOps
site:linkedin.com/pulse legal tech developer devops engineer AI
site:linkedin.com/pulse LLM fine-tuning legal documents NLP
site:linkedin.com/pulse n8n automation legal workflow

# Intake Automation
site:linkedin.com/pulse "intake automation" legal OR law firm OR abogados
site:linkedin.com/pulse WhatsApp chatbot legal abogados automation

# Jobs legal tech
site:linkedin.com/jobs "legal tech" engineer developer AI
site:linkedin.com/jobs "RAG" legal OR law OR attorney
site:linkedin.com/jobs "intake automation" legal OR law firm

# Perú / LATAM
site:linkedin.com/pulse legal tech Perú inteligencia artificial
site:linkedin.com/in legal tech Perú abogado digital
site:linkedin.com/jobs legal Perú tecnología derecho
```

### DevOps / Platform Engineering (original)

```text
site:linkedin.com/in/ DevOps AI ML engineer
site:linkedin.com/jobs/ "MLOps" Kubernetes
site:linkedin.com/in/ platform engineering SRE
site:linkedin.com/jobs/ "platform engineer" Kubernetes cloud
```

### Regla general de dorking

Siempre anteponer `site:linkedin.com/pulse` (artículos), `site:linkedin.com/in`
(perfiles), o `site:linkedin.com/jobs` (vacantes) + términos en inglés o español.
Usar `gl=pe` para resultados de Perú, `gl=es` para España, `gl=us` para global.

## Script reusable para investigación

El archivo `scripts/linkedin-legal-rag-research.py` es un script autónomo que
ejecuta 33 queries Serper en 7 grupos temáticos + HN + Stack Overflow sobre
legal tech, RAG, AI legal y abogados. Se puede adaptar cambiando el dict
`QUERIES` en la parte superior del script.

```bash
python3 scripts/linkedin-legal-rag-research.py
```

## Quick Start

```bash
cd /mnt/d/PyCode/linkedin-forums-research

# Investigación de mercado
python3 main.py --query "DevOps AI ML trends 2025" --focus market

# Skills demandados
python3 main.py --query "Kubernetes MLOps infrastructure" --focus skills

# Vacantes
python3 main.py --query "DevOps Engineer AI LATAM" --focus jobs

# Gap analysis (tu perfil vs mercado)
python3 main.py --profile perfil_ejemplo.json --focus gap

# Todo completo
python3 main.py --query "Platform Engineering MLOps 2025" --focus all --deep

# Tendencias del momento
python3 main.py --focus trends
```

## Cuando usar este skill

| Situación | Comando |
|-----------|---------|
| Investigar skills demandados en el mercado | `--focus skills --query "..."` |
| Ver qué vacantes existen para un perfil | `--focus jobs --query "..."` |
| Comparar tu perfil vs mercado | `--focus gap --profile tu_perfil.json` |
| Investigación completa multi-fuente | `--focus market --query "..."` |
| Todo a la vez + reportes | `--focus all --query "..." --deep` |
| Tendencias del momento | `--focus trends` |
| Guardar resultados para post-procesar | `--cache` |

## Métodos de bypass para contenido bloqueado

LinkedIn bloquea scraping directo y el acceso sin login a muchos contenidos.
Tres métodos comprobados para bypass (Jun 2026):

### 1. Serper API + Google Dorking ✅ (desde cualquier IP)

La Serper API es un servicio que da acceso al índice de Google Search vía API.
### Buscar perfiles (con filtro temporal)

```python
key = os.environ.get("SERPER_API_KEY")
# Filtro temporal: tbs=qdr:m6 = últimos 6 meses
resp = requests.post("https://google.serper.dev/search",
    json={"q": "site:linkedin.com/in/ RAG legal AI",
          "gl": "pe", "num": 5, "tbs": "qdr:m6"},
    headers={"X-API-KEY": key})

**Ventaja:** Funciona desde cualquier ubicación. Sin bloqueos CAPTCHA.
**Límite:** Free tier 2500 queries/mes.
**Solo indexado:** Solo contenido que Google indexó. Perfiles privados no aparecen.
**Filtro temporal:** Agregar `tbs=qdr:m6` al JSON de Serper para limitar a últimos 6 meses.
  - `qdr:m3` = 3 meses, `qdr:m6` = 6 meses, `qdr:y` = 1 año
  - Es clave para investigaciones enfocadas en contenido reciente (evita artículos de 2024)

### 2. Jina AI Reader ✅ (bypass completo de authwall de Pulse)

Jina AI (`r.jina.ai`) es un reader/proxy que devuelve el contenido de URLs
en markdown, bypasseando muros de autenticación de LinkedIn Pulse.

```bash
curl -sL "https://r.jina.ai/http://www.linkedin.com/pulse/[SLUG]" \
  -H "User-Agent: Mozilla/5.0" -H "X-Return-Format: markdown"
```

**Probado exitosamente con:**
- "RAG, Confidentiality, and the Future of AI in Legal Practice" (artículo completo)
- "Beyond Naive RAG: Achieving High-Precision Legal AI" (completo)
- "Adaptive RAG and Access to Justice" (completo)
- "NotebookLM para abogados" (completo)
- "IA agéntica: hacia un nuevo modelo operativo" (completo)

**Limitación:** ~20% de artículos tienen paywall fuerte que ni Jina sortea.

### 3. Google Translate Proxy ✅ (bypass parcial para Jobs)

`translate.google.com/translate?hl=es&sl=auto&tl=es&u=[URL_LINKEDIN]`

Carga LinkedIn a través de los servidores de Google, bypasseando el authwall.

| Contenido | Resultado |
|---|---|
| linkedin.com/jobs/search | ✅ Muestra listados completos (vs solo contadores sin proxy) |
| linkedin.com/pulse | ⚠️ Parcial — si la URL existe, funciona; si no, 404 |
| linkedin.com/company | ❌ Redirige a feed principal |

## Fuentes consultadas

| Fuente | Método | API Key | Límite |
|--------|--------|---------|--------|
| LinkedIn (perfiles) | Google dorking vía Serper | SERPER_API_KEY | 2500/mes free |
| LinkedIn (Jobs) | Google Translate proxy | No necesita | Generoso |
| LinkedIn (Pulse) | Jina AI Reader | No necesita | Generoso |
| Hacker News | Algolia Search API | No necesita | Muy generoso |
| Stack Overflow | Stack Exchange 2.3 | No necesita | 300/día sin key |
| Tendencias HN | Algolia top stories | No necesita | Ilimitado |

## Formato de salida

- **.md** — Reporte con tablas, formato legible
- **.txt** — Versión texto plano (portable)
- **.json** — Datos crudos para post-procesamiento (con `--output json`)

Los reportes siempre se guardan en formato dual (.md + .txt) bajo `reports/`.

## Gap Analysis

El módulo `synthesizer.py` compara tu perfil actual (definido en un YAML/JSON)
contra los skills detectados en el mercado. Usa una base de referencia de +60
skills del nicho DevOps+IA/ML con categorías y demanda asignada.

Resultados:
- **skills_ok** — lo que tienes y vale
- **skills_gap** — lo que te falta, priorizado por demanda
- **skills_extra** — lo que tienes pero no se detectó en mercado (diferenciadores o legacy)
- **ruta de aprendizaje** — certificaciones recomendadas

## Perfil de ejemplo

```json
{
  "nombre": "Tu Nombre",
  "titulo": "Infrastructure / DevOps Engineer",
  "skills": ["docker", "kubernetes", "terraform", "aws", "python"],
  "experiencia_anios": 5,
  "certificaciones": [],
  "objetivo": "Integrar IA/ML a mi stack de infraestructura",
  "region_interes": "LATAM"
}
```

## Dependencias

```bash
pip install requests lxml   # ya instalados
pip install pyyaml          # opcional, para perfiles YAML
pip install python-dotenv   # opcional, para cargar SERPER desde .env
```

## Arquitectura

```
query → main.py (CLI)
         ├── linkedin_intel.py → Serper API → Google index → perfiles/jobs/skills
         ├── hn_scout.py       → Algolia API → HN stories/comments/jobs
         ├── stack_scout.py    → StackExchange API → preguntas/tags/votos
         └── synthesizer.py    → Fusión + gap analysis + reportes .md/.txt
```

Todos los módulos se ejecutan en paralelo con ThreadPoolExecutor (max_workers=4).

## Lectura de comentarios y discusiones profundas

Los artículos de LinkedIn Pulse no exponen comentarios sin login. Sin embargo,
**Hacker News tiene discusiones activas sobre los mismos temas** y su API es
totalmente pública.

### Patrón: Descubrir discusiones en HN

```bash
# 1. Buscar threads sobre el tema
curl -s "https://hn.algolia.com/api/v1/search?query=legal%20RAG%20bench&hitsPerPage=3&tags=story"

# 2. Obtener el objectID del resultado
# 3. Leer el thread completo con comentarios
curl -s "https://hn.algolia.com/api/v1/items/{OBJECT_ID}"
```

**Ejemplo verificado (Jun 2026):**
- "Claude for Legal" → ID:48141234 (225pts, 30 comments)
- "Legal RAG Bench" → ID:47086383 (4pts, comentarios con insights de chunking)
- "Anthropic hallucination legal citation" → ID:43998805 (5pts)

Los comentarios de HN revelan:
- Opiniones sinceras de abogados sobre herramientas AI
- Advertencias sobre privilege abogado-cliente y datos confidenciales
- Discusiones técnicas sobre chunking, retrieval, y RAG legal
- Sentimiento del mercado sobre startups (Harvey, Claude Legal, etc.)

### Búsqueda de discusiones en otras plataformas

Para Reddit y Twitter, los snippets vía Serper revelan qué hilos existen.
Las URLs de Reddit se pueden guardar para que el usuario las lea desde su
navegador (Reddit bloquea IPs de datacenter con Cloudflare).

```python
# Buscar discusiones en Reddit y Twitter sobre un artículo
query = "site:reddit.com OR site:x.com \"Graph RAG\" legal"
```

### Búsqueda combinada completa

Para investigación profunda de un tema, ejecutar en paralelo:
1. **Serper** → descubre artículos LinkedIn + discusiones Reddit/Twitter
2. **Jina AI** → extrae full-text de artículos Pulse
3. **HN Algolia** → lee comentarios de threads relacionados
4. **Stack Exchange** → busca preguntas técnicas sobre el tema

## Plan C: Navegación directa a portales regionales (cuando TODO falla)

Cuando Serper no está configurada Y todos los buscadores (Google, DuckDuckGo,
Startpage) bloquean la IP del datacenter con CAPTCHA Y las redes sociales
(Reddit, LinkedIn, Facebook) bloquean con Cloudflare/authwall, hay un fallback
viable: **ir directamente a portales de nicho regionales y usar su buscador
interno**.

### Patrón comprobado (Jul 2026, investigación LegalTech Perú)

1. **Identificar portales de nicho**: Para derecho peruano: enfoquederecho.com
   (THĒMIS, +950 artículos), ius360.com (IUS ET VERITAS, PUCP).
2. **Usar URL de búsqueda directa**: Muchos portales WordPress aceptan `?s=query`.
   Ej: `https://enfoquederecho.com/?s=inteligencia+artificial+derecho+penal`.
3. **Extraer URLs con console cuando JS no navega**: Si los clicks no funcionan,
   usar `browser_console` con `document.querySelector('h3 a[href]')?.href`.
4. **Extraer texto completo con console**: `Array.from(document.querySelectorAll('main p, main h2, main li')).map(el => el.innerText).join('\\n')`.
5. **Navegar al artículo por URL directa**: Usar la URL extraída.

### Portal → patrón de búsqueda

| Portal | URL búsqueda | Bloqueos |
|--------|-------------|----------|
| enfoquederecho.com | `/?s=terminos` | Ninguno |
| ius360.com | `/?s=terminos` | Ninguno |
| lpderecho.pe | N/A | Cloudflare CAPTCHA |
| legis.pe | Sin probar | — |
| pasionporelderecho.pe | Sin probar | — |

Este patrón es generalizable a cualquier dominio: encontrar 2-3 portales de
referencia del nicho/región, probar su buscador interno, extraer con console.

### Limitaciones

- Solo cubre contenido indexado por ese portal específico (no es búsqueda web
  general).
- Depende de que el portal tenga contenido relevante y buscador funcional.
- JS puede bloquear navegación; en ese caso extraer URLs con console y navegar
  directo.
- No reemplaza Serper + Reddit + LinkedIn; es un complemento de último recurso.

## Common Pitfalls

1. **SERPER_API_KEY no configurada**: El módulo `linkedin_intel.py` busca la key
   en `.env`, variables de entorno, y `~/.env`. Si no la encuentra, reporta error
   y funciona parcialmente con solo HN + Stack Overflow.
   **Fallback sin Serper**: usar Plan C (navegación directa a portales regionales)
   descrito arriba.
2. **LinkedIn no se scrapea directamente**: Solo se usa Google dorking legal
   (`site:linkedin.com/in/`). Los resultados dependen de lo que Google indexa.
3. **Datacenter IPs bloqueados por buscadores**: Google, Bing y DuckDuckGo
   bloquean búsquedas desde IPs de datacenter con CAPTCHA/Cloudflare (verificado
   con IP 38.25.16.30 en Jun 2026). SOLUCIÓN: usar Serper API para búsquedas
   (funciona desde cualquier IP por ser API) y Jina AI Reader para leer
   artículos Pulse (bypassea el authwall). El proxy de Google Translate funciona
   para LinkedIn Jobs pero no para Pulse ni Company pages.
4. **Jina AI reader tiene límite de velocidad**: ~10 requests/segundo aprox.
   Para leer lotes grandes de artículos, espaciar con `sleep(1)` entre requests.
5. **Stack Exchange rate limit**: Sin API key, límite de 300 requests/día.
   En modo `--deep` con queries múltiples, puede excederse.
5. **WSL rutas**: El proyecto vive en `/mnt/d/PyCode/` (Windows D:). Los
   reportes se guardan ahí. Si ejecutas desde WSL home, cambiar `--outdir`.
6. **Formato dual**: Siempre se generan .md y .txt. Si solo quieres uno,
   usa `--output md` o `--output text` en CLI.

## Verification Checklist

- [ ] `python3 main.py --focus trends` devuelve las 15 tops stories de HN
- [ ] `python3 main.py --query "DevOps" --focus skills` muestra skills detectados
- [ ] `python3 main.py --profile perfil_ejemplo.json --focus gap` genera gap analysis
- [ ] Los reportes se guardan en dual format (.md + .txt) en reports/
- [ ] Serper API funcional (si hay key configurada)
- [ ] Stack Overflow responde sin key (300 req/día)

## Referencias

- `references/skills-reference.md` — Catálogo de 60+ skills del nicho DevOps+IA/ML usado por el gap analysis
- `references/linkedin-bypass-methods-2026.md` — Resultados detallados de pruebas de bypass (Jina AI, Google Translate, Serper) para acceso a LinkedIn sin cuenta
- `references/linkedin-google-dorking.md` — Documentación externa del skill `web-deep-research` sobre Google dorking + Serper
- `references/peru-legaltech-ecosystem-2026.md` — Ecosistema LegalTech peruano: startups, necesidades, herramientas de referencia, portales jurídicos (investigación Jul 2026)
- `scripts/linkedin-legal-rag-research.py` — Script reusable para investigación de LinkedIn en dominio legal/RAG con 33 queries Serper
- `/mnt/d/PyCode/LinkedinResearch/linkedin_pulse_deep_research.py` — Script especializado en Pulse articles con filtro temporal (--months N) y extracción Jina AI
