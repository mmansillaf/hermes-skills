---
name: peruvian-judicial-scraping
description: >-
  Class-level umbrella for scraping Peruvian judicial portals. Covers two
  distinct patterns: (A) CEJ/PJ — anti-bot/WAF evasion via browser
  fingerprint modification + text captcha + Selenium, and (B) SEDETC/TC —
  public Elasticsearch REST API + direct PDF download. Consolidates
  production debugging from both portals under one framework.
category: scraping
triggers:
  - "peruvian judicial scraping"
  - "scrape peru tribunal constitucional"
  - "sedetc tc scraper"
  - "jurisprudencia tc peru"
  - "tribunal constitucional pdf download"
  - "cej pj peru scraping"
  - "poder judicial peru descarga"
---

# Peruvian Judicial Scraping — Class-Level Patterns

## Overview

Peruvian judicial portals fall into two categories, each requiring a completely
different scraping approach:

| Portal | Domain | Pattern | Protection | Tooling |
|--------|--------|---------|------------|---------|
| **CEJ / Poder Judicial** | `cej.pj.gob.pe` | WAF + Captcha + Selenium | Anti-bot/WAF evasion via browser fingerprint patching (CDP), text captcha, sleep randomization | undetected_chromedriver, 2captcha, Scrapy |
| **SEDETC / TC** | `jurisprudencia.sedetc.gob.pe` | REST API + direct PDF | Rate limit only (60/min) | requests, ThreadPoolExecutor |

## Which Skill to Load

- For **CEJ/PJ** (WAF+anti-bot evasion, captchas, Selenium, Scrapy) → load `cej-peru-scraper`
- For **SEDETC/TC** (REST API, no WAF, direct PDFs) → load `tc-sedetc-scraper`
- For **TC Consulta de Causas** (older cases pre-2023, WordPress+DataTables, requires Selenium) → see `tc-sedetc-scraper::references/consulta-de-causas-exploration.md`
- For **Indecopi resoluciones** (JSF/RichFaces, no WAF, category-based browsing) → see Pattern C below
- For **blocked sites** (Cloudflare, IP bans, Wayback proxy) → load `web-data-extraction`

---

# Pattern C: Indecopi — Buscador de Resoluciones (servicio.indecopi.gob.pe)

## Portal Overview

| Attribute | Detail |
|-----------|--------|
| **URL** | `https://servicio.indecopi.gob.pe/buscadorResoluciones/` |
| **WAF** | ✅ **No WAF** — accessible via undetected-chromedriver without proxy |
| **Tech Stack** | JSF (RichFaces) + Seam framework, Java backend |
| **Session** | JSESSIONID cookies, semi-persistent |
| **Alternative source** | `https://www.gob.pe/10720-buscar-resoluciones-del-indecopi` (no WAF, direct HTTP) |
| **Blocked URL** | `https://enlinea.indecopi.gob.pe/serviciosenlinea/` — has Imperva/Incapsula WAF, DO NOT target this |

## Categories (6 main)

| Page | URL suffix | What it contains |
|------|-----------|-----------------|
| **Tribunal** | `tribunal.seam` | Resoluciones del Tribunal de Indecopi (máxima instancia) |
| **Propiedad Intelectual** | `propiedad-intelectual.seam` | Marcas, patentes, derechos de autor |
| **Protección al Consumidor** | `proteccion-consumidor.seam` | SPC — highest value for lawyers |
| **Defensa de la Competencia** | `competencia.seam` | Libre competencia + competencia desleal |
| **Sentencias PJ** | `poderjudicial.seam` | Sentencias del Poder Judicial (cross-reference) |
| **Laudos** | `pgw_laudos.seam` | Laudos arbitrales |

## SPC Subcategories (Protección al Consumidor)

The SPC page has 5 sub-areas:
1. Tribunal (SPC appeals level)
2. Comisiones de Lima
3. Comisiones de Provincias
4. Órganos Sumarísimos de Lima
5. Órganos Sumarísimos de Provincias

## Search Form Fields (JSF IDs)

```
FormListado1:txtTextoBusqueda     → Quick search (text)
FormListado1:b_RealizaBusqueda    → Search button
FormListado:txtNroResolucion      → Resolution number filter
FormListado:txtAnioResolucion     → Year filter
FormListado:lblNroExpediente      → Case number filter
FormListado:lblAnioExpediente     → Case year filter
```

## Known Issue: Error Modal

The search engine may show a hidden error modal:
"Debido a problemas técnicos, la búsqueda de resoluciones a través de nuestro gestor de contenidos se ha visto afectada momentáneamente."
This appears when the backend search fails. Category browsing may still work.

## Scraper Approach

```python
os.environ['CHROME_BINARY_PATH'] = os.path.expanduser('~/chromium/chrome-linux64/chrome')
opts = uc.ChromeOptions()
opts.binary_location = os.environ['CHROME_BINARY_PATH']
driver = uc.Chrome(version_main=149, options=opts)
driver.get("https://servicio.indecopi.gob.pe/buscadorResoluciones/proteccion-consumidor.seam")
```

Key differences from CEJ scraper:
- **No CAPTCHA handling needed** (no WAF on buscadorResoluciones, but WAF on enlinea.indecopi.gob.pe — do NOT target that subdomain)
- **No 2captcha integration needed**
- **No remote Chrome debugging needed** — direct undetected-chromedriver works
- **JSF forms use AJAX** — clicks may not change URL; use time.sleep(2-3) and snapshot
- **Search engine has intermittent technical issues** — check for error modal before proceeding

## Scraper Architecture (Dual Path)

Given intermittent technical issues with the buscador, use dual-path:

```
PATH A: Buscador oficial (servicio.indecopi.gob.pe)
  - Chrome + undetected-chromedriver (version_main=149)
  - Navigate to proteccion-consumidor.seam or tribunal.seam
  - Check for error modal before proceeding
  - Select year/subcategoria -> click search -> wait AJAX
  - Extract result table (RichFaces rich-table)
  - Download PDF attachments from each row

PATH B: Gob.pe (no WAF, direct HTTP)
  - requests.get() with User-Agent
  - Listings at /institucion/indecopi/normas-legales/tipos/10-resolucion
  - Pagination: ?page=N (max 5 pages per type)
  - Extract PDF links from detail pages with regex
  - NOTE: gob.pe mainly has ADMINISTRATIVE resolutions (GEG, PRE),
    NOT SPC jurisprudence — use as fallback only
```

## Checkpoint Strategy

Save as JSON every 10 downloads. Track `resoluciones_descargadas` URL list to skip re-downloads. Keep last 1000 URLs to limit memory.

## Metadata Schema per Resolution

When extracting, aim for this structure:
```
numero, fecha, sala, subcategoria, instancia, tipo, expediente,
denunciante, denunciado, ruc, materia, sector, sumilla, fallo,
sancion_monto, sancion_moneda, medida_correctiva, url_pdf, url_original
```

## Priority When Buscador Recovers

1. SPC Proteccion al Consumidor (5K-10K docs) — most cited by litigators
2. Tribunal de Indecopi (2K-5K) — precedentes vinculantes
3. Competencia Desleal (1K-3K) — corporativo/marcas
4. Propiedad Intelectual (5K-10K) — marcas/patentes

## Integration into LexRAG

After scraping: index in FAISS+BM25 with 'fuente: indecopi' tag, enrich graph with empresas sancionadas and sectores economicos, extend Critic Agent to verify Indecopi citations. Do NOT mix with PJ corpus without source tag.

## Alternative Source: gob.pe (no WAF)

Resolution PDFs published at:
`https://www.gob.pe/institucion/indecopi/normas-legales/{id}-resolucion`

Accessible via direct HTTP:
```python
import requests, re
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
pdf_links = re.findall(r'href="([^"]*\.pdf)"', r.text, re.IGNORECASE)
```

**Caveat**: Only administrative resolutions on gob.pe (PRE, GEG), not SPC case law.

## Related Skills

- `cej-peru-scraper` — CEJ/PJ (Radware + captcha + Selenium)
- `scrapy-selenium-captcha-scraping` — Captcha-heavy portals
- `tc-sedetc-scraper` — TC (REST API, no WAF)
- `tc-ingesta-lexrag` — Post-scraping ingestion (PDFs -> FAISS+BM25+Graph)

---



# Pattern B: SEDETC / Tribunal Constitucional

## Stack Analysis

The TC's jurisprudencia portal at `jurisprudencia.sedetc.gob.pe` is built on:

| Component | Technology | Detail |
|-----------|-----------|--------|
| Frontend | **Nuxt.js** (Vue.js SSR + SPA) | Vuetify UI, server-side rendered shell |
| Backend API | **jurisbackend.sedetc.gob.pe** | AWS EC2, Apache, PHP |
| Database | **Elasticsearch** | Index `sentencias`, field `_source` |
| PDF hosting | **tc.gob.pe** | Direct HTTP, no rate limit, no auth |

## API Discovery Method

SPAs (Nuxt, React, Angular) load data client-side via hidden API calls.
Standard curl/browser_navigate only reveals the SSR shell. To find the API:

```javascript
// In browser_console, after page fully loads:
performance.getEntriesByType('resource')
  .filter(e => e.name.includes('/api/') || e.name.includes('backend'))
  .map(e => e.name)
```

This reveals backend subdomains and API endpoints that don't appear in the
page source. For SEDETC TC, this found `jurisbackend.sedetc.gob.pe`.

## API Details

| Parameter | Value |
|-----------|-------|
| **Base URL** | `https://jurisbackend.sedetc.gob.pe/api/visitor/sentencia/busqueda?page=N` |
| **Required header** | `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...` |
| **Without UA** | Returns cached default response (ignores page/search params) |
| **Rate limit** | 60 req/min (header: `X-RateLimit-Limit: 60`) |
| **Response** | JSON: `{data: [{_source: {...}}], total: {value}, pagination: ...}` |
| **Items/page** | 10 (fixed, `size` param ignored) |
| **Pages** | 1000 (10000 items, capped at 10000 with relation: 'gte') |
| **Search param** | `?page=N&search=termino` (filters by keyword) |

### Additional API Endpoints

```
GET /api/visitor/init                                   → Front page data (videos, gacetas, distritos, salas)
GET /api/visitor/sentencia/tipo/{id}                    → Sentencia type metadata
GET /api/visitor/sentencia/busqueda?page=N&search=XXX   → Filtered search
```

## Data Structure

Each `_source` object contains:

```json
{
  "numero_expediente": "04442-2024-AA",
  "numero_sentencia": "312/2026",
  "fecha_publicacion": "2026-03-04",
  "url_archivo": "https://www.tc.gob.pe/jurisprudencia/2026/04442-2024-AA.pdf",
  "slug": "04442-2024-aa-312-2026",
  "nombre_demandante": "Marina Ríos Morales",
  "nombre_demandado": "Municipalidad Provincial de Cajamarca",
  "fundamentos": ["VOTO DEL MAGISTRADO...", "..."],
  "sentencia_sala": {"id": 2, "nombre": "Sala 2"},
  "sentencia_distrito": {"id": 6, "nombre": "Distrito Judicial de Cajamarca"},
  "id": 74818
}
```

### Types of Sentencia (expediente suffix)

| Suffix | Meaning |
|--------|---------|
| **AA** | Acción de Amparo (~45%) |
| **HC** | Hábeas Corpus (~45%) |
| **AC** | Acción de Cumplimiento (~8%) |
| **HD** | Hábeas Data (~2%) |
| **AI** | Acción de Inconstitucionalidad (~1%) |

## Chronological Distribution

API orders by publication date descending (newest first):

| Publication Year | Pages (approx) | PDFs (approx) |
|-----------------|----------------|---------------|
| 2026 | 1-100 | ~1,000 |
| 2025 | 100-600 | ~5,000 |
| 2024 | 600-900 | ~3,000 |
| 2023 | 900-1000 | ~1,000 |

Expediente years range from **2022 to 2025** regardless of publication year.

## PDF Details

- **URL pattern**: `https://tc.gob.pe/jurisprudencia/{year}/{expediente}.pdf`
- **All verified**: HTTP 200 ✅ (2023, 2024, 2025, 2026 tested)
- **Redirect handling**: `tc.gob.pe` redirects to `www.tc.gob.pe` — use `requests.get(allow_redirects=True)`
- **Average size**: 200-800 KB (some 1.3 MB)
- **Total for 10,000 PDFs**: ~8 GB
- **Rate limit**: None detectable on PDF server

## Scraper Architecture

```
[Phase 1: Metadata]        [Phase 2: PDF Download]
API (serial, throttled)     ThreadPoolExecutor (24 workers)
       │                              │
       ▼                              ▼
metadata.csv ──→ checkpoint.json ──→ pdfs/{year}/{exp}.pdf
```

### Phase 1 — Metadata Fetch (serial)

- 1.2s between API calls = 50 req/min (margin under 60 limit)
- Save checkpoint every 10 pages
- Detect end: page returns 0 new items or 3 consecutive failures
- Save to CSV: expediente, exp_year, tipo, fecha_pub, pdf_year, url_pdf, demandante, demandado, sala, distrito, id_api

### Phase 2 — PDF Download (parallel)

- ThreadPoolExecutor with `max_workers=24` (match CPU cores)
- PDF server (`tc.gob.pe`) has NO rate limit — parallel is safe
- Check existing files to skip re-downloads
- Reintentar 3x con backoff exponencial
- Verify HTTP 200, reject 404s

### Critical: Connection Pool Size

`requests.Session()` has a default pool of 10 connections. With 24 workers,
you'll get `Connection pool is full, discarding connection` warnings.
**Fix**: Either create a new session per request (no pool sharing) or
increase pool size:

```python
_pdf_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=24,
    pool_maxsize=24
)
_pdf_session.mount('https://', adapter)
```

## Checkpoint Strategy

```json
{
  "last_metadata_page": 42,
  "items": [...],
  "phase": "metadata_done",
  "downloaded_ids": [74818, 74819, ...],
  "downloaded_results": [...],
  "results": {"ok": 1000, "fail": 0, "skipped": 0}
}
```

- Resume: skip already-processed `id_api` values
- Phase `download_done`: skip download entirely on re-run
- Do NOT abort on individual PDF failures — log and continue

## CLI Interface

```bash
python tc_scraper.py --max 1000 --workers 24          # Fresh run
python tc_scraper.py --max 1000 --workers 24 --resume  # Resume
python tc_scraper.py --metadata-only --max 5000        # Metadata only
python tc_scraper.py --download-only                   # Download from existing CSV
```

## Pitfalls

1. **API requires User-Agent header** — Without it, returns stale cached response regardless of page/search params. Always set `User-Agent: Mozilla/5.0 ...`.
2. **Search param key is `search` not `q`** — `?page=1&search=habeas`, NOT `?q=habeas`. Misspelling = ignored parameter.
3. **`size` param is ignored** — Always returns 10 items per page regardless of `?size=100`.
4. **Total count says 'gte'** — `relation: 'gte'` means total is AT LEAST 10000, could be more.
5. **Connection pool full** — With 24 workers and default pool size 10, increase `pool_maxsize` matching workers:
   ```python
   adapter = requests.adapters.HTTPAdapter(pool_connections=24, pool_maxsize=24)
   session.mount('https://', adapter)
   ```
6. **Year boundaries are fuzzy** — Expect ~1-2 items from adjacent year at transition pages.
7. **PDF domain varies** — Some URLs use `tc.gob.pe` (without www) and redirect. Always follow redirects.
8. **`sentencia_distrito: null` in API responses** — Some items (e.g. Pleno session cases) have `sentencia_distrito: null`. Always use safe access: `(src.get("sentencia_distrito") or {}).get("nombre", "")` not `src.get("sentencia_distrito", {}).get(...)` — the second form returns `None` not `{}` when the key exists with null value.
9. **Page 1001+ returns HTTP 500** — The Laravel backend hits a log-permission error. The catalog is hard-capped at 10,000 items (1,000 pages). Earliest data is November 2023. No 2022-or-carlier publication data is available via this API.
10. **Duplicate expedientes in API** — ~3 items appear twice with different API IDs. The checkpoint deduplication by `id_api` handles this, but `metadata.csv` will have duplicate rows. The download skips the second copy (file already exists).
11. **Extra text in expediente numbers** — Some API `numero_expediente` fields include parenthetical annotations: `05145-2022-AA (Desistimiento)`, `02203-2023-AA (Amicus Curiae)`, `00345-2023-AA (Aclaración)`. The `url_archivo` PDF path uses the clean expediente code without annotations. Always use the `url_archivo` from the API, not a constructed URL.

## Post-Scraping: Ingestion into LexRAG

After downloading PDFs with `tc-sedetc-scraper`, the next step is to index them
into a searchable RAG system. The skill `tc-ingesta-lexrag` covers this pipeline:

1. Extract text from PDFs with PyMuPDF
2. Send to Groq Batch API for structured extraction (hechos, problema, fallo, entidades)
3. Convert results to FAISS + BM25 + NetworkX indices

See `tc-ingesta-lexrag` for full pipeline details, costs, and performance data.

## Related Skills

- `tc-ingesta-lexrag` — Post-scraping ingestion: PDFs → FAISS+BM25+Graph (LexRAG)
- `cej-peru-scraper` — Counterpart for CEJ/PJ (Radware + captcha + Selenium)
- `web-data-extraction` — For sites behind Cloudflare/WAF where Wayback proxy is needed
- `spec-driven-development` — Methodology used for this project (Constitution → Spec → Plan → Implement → Verify)
