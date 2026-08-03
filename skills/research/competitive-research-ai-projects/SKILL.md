---
name: competitive-research-ai-projects
title: "Competitive Research Methodology for AI/Tech Projects"
description: "Systematic multi-source research methodology for finding and analyzing competitors, papers, and commercial solutions in any AI/tech domain. Uses GitHub API, Serper/Google, arXiv, and structured comparison matrices."
category: research
tags: [competitive-research, market-research, github-api, serper, arxiv, benchmarking]
---

# Competitive Research Methodology for AI/Tech Projects

## When to Use

When you need to:
- Find open-source projects similar to yours
- Identify commercial/paid competitors
- Locate relevant academic papers
- Build a structured competitive landscape
- Validate architectural decisions against market

## Step 1: GitHub API — Multi-Query Search

**Autenticación opcional (USAR SIEMPRE QUE ESTÉ DISPONIBLE):** sin token limitas a 60 req/h.
Con token subes a 5000 req/h. El token de GitHub vive en `~/Escritorio/PyCode/env.md` con
formato `token_gh = ghp_...`:

```python
import urllib.request, json, os

def _gh_token() -> str:
    """Lee el token de GitHub desde ~/Escritorio/PyCode/env.md si existe."""
    try:
        with open(os.path.expanduser("~/Escritorio/PyCode/env.md")) as f:
            for line in f:
                if line.strip().startswith("token_gh"):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except FileNotFoundError:
        pass
    return ""

GH_TOKEN = _gh_token()

def _github_headers() -> dict:
    h = {"Accept": "application/vnd.github.v3+json", "User-Agent": "HermesAgent"}
    if GH_TOKEN:
        h["Authorization"] = f"Bearer {GH_TOKEN}"
    return h

queries = [
    "legal+rag+retrieval+augmented+generation",  # Domain-specific
    "legislation+ai+search+chatbot",              # Alternative phrasing
    "law+document+retrieval+llm",                 # Technical variant
    "graphrag+legal",                             # Sub-technique
    "spanish+legal+nlp",                          # Language-specific
]

all_results = []
for q in queries:
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=10"
    req = urllib.request.Request(url, headers=_github_headers())
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        for r in data.get("items", []):
            all_results.append({...})
```

**Pitfall:** El token del env.md puede caducar (ghp_ classic). Si GitHub devuelve 401, ignorarlo
y seguir sin auth (cae a 60 req/h). Si devuelve 403/rate-limit sin token, usar Serper para
buscar "github.com repo-name". NUNCA exponer el valor del token en logs o salidas.

## Step 2: Dedeuplicar y Ordenar

Siempre deduplicar por `full_name` o `html_url`:

```python
seen = set()
unique = []
for r in sorted(all_results, key=lambda x: x["stars"], reverse=True):
    if r["name"] not in seen:
        seen.add(r["name"])
        unique.append(r)
```

## Step 3: Fetch README de los Top-N

Para los ~6 más relevantes, obtener README completo:

```python
readme_url = f"https://api.github.com/repos/{repo}/readme"
req = urllib.request.Request(readme_url, headers={
    **_github_headers(),
    "Accept": "application/vnd.github.v3.raw",  # ← RAW para texto, no base64
})
```

Y estructura de archivos:
```python
tree_url = f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1"
```

## Step 4: Serper/Google — Papers, Blogs, Comerciales

Usar Serper (ya configurado en .env) para búsquedas complementarias:

```python
import urllib.request, json, os

SERPER_KEY = os.environ.get("SERPER_API_KEY", "")
commercial_queries = [
    "AI legal research platform RAG law firm pricing 2025",
    "legislation search engine AI commercial solution",
    "legal chatbot norms regulations SaaS platform",
    "graphrag legal production deployment enterprise case study",
]

for q in commercial_queries:
    data = json.dumps({"q": q, "num": 8}).encode()
    req = urllib.request.Request("https://google.serper.dev/search", data=data,
        headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        r = json.loads(resp.read().decode())
```

## Step 5: arXiv API — Papers Académicos

```python
import urllib.request, xml.etree.ElementTree as ET

# Buscar por ID
url = "https://export.arxiv.org/api/query?id_list=2505.00039&max_results=1"
# Buscar por query
url = "https://export.arxiv.org/api/query?search_query=all:legal+rag+benchmark&max_results=10"

req = urllib.request.Request(url, headers={"User-Agent": "HermesAgent"})
with urllib.request.urlopen(req, timeout=20) as resp:
    content = resp.read().decode()
    root = ET.fromstring(content)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns).text
        summary = entry.find('atom:summary', ns).text
```

**Pitfall:** arXiv HTML puede ser JavaScript-rendered. Preferir API XML (siempre funciona) o buscar el paper vía Serper para obtener resúmenes/blog posts.

## Step 6: Categorizar Resultados

Clasificar cada resultado en categorías para el análisis:

```python
categories = {
    "PROYECTOS OPEN SOURCE SIMILARES": [],
    "SOLUCIONES COMERCIALES": [],
    "PAPERS / BENCHMARKS": [],
    "ARTÍCULOS TÉCNICOS": [],
    "OTROS": []
}

for r in all_results:
    title_lower = (r["title"] + " " + r["snippet"]).lower()
    if any(w in title_lower for w in ["github", "open source", "repo"]):
        categories["PROYECTOS OPEN SOURCE SIMILARES"].append(r)
    elif any(w in title_lower for w in ["startup", "platform", "saas", "pricing", "enterprise"]):
        categories["SOLUCIONES COMERCIALES"].append(r)
    elif any(w in title_lower for w in ["benchmark", "dataset", "paper", "arxiv", "survey"]):
        categories["PAPERS / BENCHMARKS"].append(r)
    # ...
```

## Step 7: Compilar Matriz Comparativa

Crear una tabla markdown con características clave:

| Solución | Tipo | Precio | Multi-Store | Grafo | Temporal | Idioma | OS |
|---|---|---|---|---|---|---|---|
| Proyecto A | OS | $0 | ✅ | ✅ | ❌ | ES | ✅ |
| Comercial B | SaaS | $$ | ✅ | ❌ | ✅ | EN | ❌ |

**Columnas sugeridas:** Nombre, Tipo (OS/Comercial/Académico), Precio, Características técnicas relevantes (3-5), Idioma, Licencia, Diferenciador.

## Step 6b (Alternative): Parallel Multi-Source Research via delegate_task

When the research spans multiple independent domains (e.g., Cloudflare + HuggingFace + GitHub), parallelize with `delegate_task`:

```python
# Launch independent research agents in parallel
tasks = [
    {"context": "Investigate Cloudflare for RAG deployment...", 
     "goal": "Cloudflare RAG capabilities, pricing, templates",
     "toolsets": ["browser", "terminal"]},
    {"context": "Investigate HuggingFace Spaces for RAG...",
     "goal": "HF Spaces RAG capabilities, pricing, templates",
     "toolsets": ["browser", "terminal"]},
]
results = delegate_task(tasks=tasks)
```

Each agent returns a self-contained summary. Merge their outputs in the main thread and deduplicate cross-references. This turns a 15-minute sequential session into 8 minutes of parallel work.

**When to use delegate_task vs execute_code:**
- `execute_code`: API calls (GitHub, Serper, arXiv), data processing, dedup, README fetching. Fast, no context-switching.
- `delegate_task`: Web research requiring browser navigation, multi-page scraping, documentation reading. Slower per-task but parallelizable.

**Pitfall:** delegate_task agents may write files to disk. Read them with `read_file` after they complete rather than relying on in-summary data.

## Step 8: Guardar Reportes

Siempre guardar en `reports/` con timestamp:

```
reports/investigacion_mercado_{dominio}_{YYYY-MM-DD}.md
reports/evaluacion_arquitectura_{YYYY-MM-DD}.md
reports/investigacion_detallada_{topico}_{YYYY-MM-DD}.md
```

## Pitfalls

0. **GitHub token provisioning from a plaintext file.** When the user provides the PAT in a file (e.g. `env.md`, `.env`), the key is often non-standard (`token_gh =`). A valid PAT lifts the GitHub API ceiling from 60 req/h (anonymous) to 5000 req/h — always worth provisioning before a deep research session. Parse + validate + export WITHOUT echoing the token back:

```bash
# Extraction handles any likely prefix (token_gh / GITHUB_TOKEN / GH_TOKEN)
TOKEN=$(grep -iE '^(#?\s*)?(token_gh|GITHUB_TOKEN|GH_TOKEN)\s*=' "$FILE" \
        | head -1 | sed -E 's/^[^=]*=\s*//' | tr -d '\r\n')
# Validate: /user returns the login if live; rate_limit core.limit==5000 proves authenticated
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/user
export GITHUB_TOKEN="$TOKEN"
```

Then send `Authorization: Bearer $GITHUB_TOKEN` on GitHub API calls. Never print the raw token into your reply — show only presence/length (`len ${#TOKEN}`) and name the user by the `login` from the API response. Classic PAT (`ghp_...`) works with `Bearer`; fine-grained (`github_pat_...`) is repo-scoped and will 403 on repos outside its allowlist. This file path is the fallback when env vars are empty AND `gh auth status` reports an invalid keyring token.
1. **GitHub API rate limit (403)**: Sin token = 60 req/h (anónimo). Con token de `~/Escritorio/PyCode/env.md` = 5000 req/h. Usar `execute_code` con `urllib` y `_github_headers()`. Si aún así se excede, usar Serper para buscar repos. Nunca exponer el token en logs.
2. **arXiv HTML vacío**: La página HTML de arXiv requiere JavaScript. Usar la API XML (`export.arxiv.org/api/query`) que siempre funciona.
3. **Serper devuelve muchos resultados irrelevantes**: Usar queries muy específicas con comillas para términos exactos.
4. **curl | python3 bloqueado por seguridad**: No usar pipes a intérprete. Siempre usar `execute_code` con `urllib`.
5. **Deduplicación**: GitHub y Serper pueden devolver el mismo recurso. Siempre deduplicar por URL o nombre canónico.
6. **Reportes muy grandes**: Si el reporte supera 30KB, dividir en 2-3 archivos por tema.
7. **Browser snapshots truncados por bot detection**: Sitios como Cloudflare Docs o Imgur a menudo truncan el contenido del `<main>` en snapshots del browser (marcan 1180+ lines truncated). Workaround: usar `browser_console` con `document.querySelector('main')?.innerText?.substring(0, 5000)` y luego continuar con `substring(5000, 10000)`. Esto extrae el texto real del DOM aunque el snapshot esté truncado.
8. **Vision analyze falla con ciertos modelos/proveedores**: deepseek no soporta imágenes via API; otros proveedores pueden fallar con webp. Si la imagen es crucial y no se puede analizar, descargarla con curl y convertirla a PNG/JPG, o usar `browser_get_images` para encontrar la URL directa y `browser_vision` como alternativa.

## Domain-Specific Query Templates

### Legal/Legislation
```
"{pais} legislation AI search RAG"
"diario oficial {pais} inteligencia artificial"
"official gazette AI search retrieval"
"legal knowledge graph platform enterprise"
```

### Healthcare
```
"medical RAG clinical decision support"
"healthcare retrieval augmented generation FHIR"
```

### Finance
```
"financial document RAG SEC filings"
"regulatory compliance AI platform banking"
```

## Verification

- [ ] At least 20+ results of GitHub
- [ ] At least 30+ results of Serper
- [ ] At least 5 papers of arXiv
- [ ] At least 3 commercial solutions identified
- [ ] Matrix comparative with 8+ columns
- [ ] Report saved in reports/
- [ ] All functional links

## RAG-Specific Research (Domain Extension)

When researching RAG projects specifically, extend the search queries:

**GitHub queries add:**
```
"graphrag+legal"
"knowledge+graph+legal+nlp"  
"multi+store+rag"
"rag+confidence+scoring"
```

**Serper queries add:**
```
"graphrag legal norms hierarchical temporal"
"legal RAG benchmark evaluation methodology"
"retrieval augmented generation legal domain survey"
```

**Domain-specific analysis (add after Step 5):**
- Check if any competitor has web fallback (Serper/Google)
- Check if any has adversarial defense layers
- Check if any uses query classification for selective routing
- Check for multi-store integration (vector + graph + relational)

**Key papers to check:** SAT-GraphRAG (arXiv 2505.00039), Domain-Partitioned Hybrid RAG (arXiv 2602.23371), Legal RAG Bench (arXiv 2603.01710).

**Key commercial solutions:** Harvey AI, CoCounsel (Thomson Reuters), vLex Vincent, BOE AI, LexLatam.ai.

**Key open-source projects:** justicio (BOE Spain), Azure GraphRAG Legal, EU-GraphRAG.

Full RAG-specific methodology including data-first analysis and architecture design grounded in findings is in the consolidated `building-rag-systems-with-multiple-stores` skill.

## Deployment-Platform Research (Domain Extension)

When the research goal includes evaluating WHERE and HOW to deploy the solution:

**Cloudflare-specific sources:**
- Pricing: `developers.cloudflare.com/workers/platform/pricing/`
- Containers pricing: `developers.cloudflare.com/containers/platform/pricing/`
- RAG tutorial: `developers.cloudflare.com/workers-ai/guides/tutorials/build-a-retrieval-augmented-generation-ai/`
- AI Search (new): `developers.cloudflare.com/ai-search/`
- Blog AI tag: `blog.cloudflare.com/tag/ai/`
- Key numbers: Workers $5/mes base, Containers desde $5/mes + uso, Vectorize $0.01/1M vectors, D1 SQLite $0.75/GB, R2 storage $0.015/GB sin egress

**HuggingFace Spaces-specific sources:**
- Overview: `huggingface.co/docs/hub/spaces-overview`
- GPU pricing: `huggingface.co/docs/hub/spaces-gpus`
- Pricing page: `huggingface.co/pricing`
- GitHub Actions CI/CD: `huggingface.co/docs/hub/spaces-github-actions`
- Key numbers: Free CPU (2vCPU/16GB/50GB), PRO $9/mes, GPU desde $0.40/h (T4)

**GitHub Pages for docs/landing:**
- Free static hosting via `github.io` domains
- Combine with Cloudflare Workers as backend proxy
- Good for documentation sites and project landing pages

**Combination patterns to evaluate:**
- Frontend HF Spaces (Gradio) + Backend Cloudflare Workers (API)
- All-in Cloudflare (Workers + D1 + R2 + Vectorize) + GitHub Pages (docs)
- HF Spaces GPU (heavy PDF processing) + Cloudflare Workers (lightweight query API)
- GitHub Actions as CI/CD glue between all platforms

**Cost analysis template:** Include columns for Workers/AI/Vectorize/D1/R2/Containers/GPU-hours side by side with free tier eligibility. Always present a "minimum viable cost" row.

See `references/rag-deployment-combinations.md` for detailed findings from the May 2026 research session.
