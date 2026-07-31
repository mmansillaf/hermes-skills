---
name: web-data-extraction
category: scraping
description: Extract data from websites that block direct access — WAF, Cloudflare, IP bans. Uses Wayback Machine as proxy to access compiled JS bundles, then reverse-engineers Angular/React/SPA code to recover embedded data, API endpoints, and configuration. Also covers direct HTTP extraction with curl_cffi impersonation.
---

# Web Data Extraction from Blocked Sites

## When to use
- Site blocks all connections (TLS handshake fail, ERR_CONNECTION_CLOSED, HTTP 403/503)
- Standard tools fail: curl, Python requests, browser_navigate, curl_cffi
- Site is an Angular/React SPA — most data is in compiled JS bundles
- You need the data, not just the rendered page

## Step-by-step

### 1. Diagnose the block level

Run in order to determine what's blocking:

```
curl -v --max-time 15 "https://site.com/path" 2>&1 | tail -10
curl -sk --max-time 15 "https://site.com/path" -o /dev/null -w "%{http_code}"
```

Signals:
- `SSL_ERROR_SYSCALL` / `SSL_connect` errors → WAF blocking at TLS level
- `HTTP 403` → WAF blocking at HTTP level  
- `HTTP 503` / CAPTCHA page → Cloudflare or similar
- `HTTP 200` with "blocked" in title → Bot detection page

### 2. Try direct extraction workarounds

Before going to Wayback Machine:

```python
# curl_cffi with browser impersonation
from curl_cffi import requests as cr
r = cr.get(url, impersonate='chrome120', timeout=30)
r.text

# If SSL fails, try with verify=False
import requests
r = requests.get(url, verify=False, timeout=20, 
    headers={'User-Agent': 'Mozilla/5.0 ...'})
```

### 3. Use Wayback Machine as proxy

Navigate to the capture:
```
https://web.archive.org/web/2025*/https://sitio.gob.pe/ruta
```
Or use the most recent capture directly:
```
https://web.archive.org/web/<timestamp>id_/https://sitio.gob.pe/ruta
```

### 4. Extract JS bundles from the captured page

Look at the HTML for script tags pointing to chunk files:

```python
import re
with open('page.html') as f:
    content = f.read()
scripts = re.findall(r'<script[^>]*src="([^"]+)"', content)
# Filter for JS chunks
chunks = [s for s in scripts if 'chunk-' in s or 'main-' in s]
```

### 5. Download and analyze JS chunks

Download each chunk via Wayback Machine's `jm_` endpoint:
```
https://web.archive.org/web/<timestamp>jm_/https://sitio.gob.pe/chunk-XXXXXX.js
```

### 6. Reverse-engineer compiled SPA code

**Look for inlined static data:**
- `globalStats`, `config`, `environment` objects
- Department/region lookup tables with IDs
- Default filter options and static labels
- API base URLs and endpoint paths

**Extract structured data from minified JS:**
```python
import re
# Find embedded arrays/objects
idx = content.find('pyramidData')  # or any known key name
start = content.index('[', idx)
# Walk braces to find matching close
depth = 0
for i, c in enumerate(content[start:]):
    if c == '[' or c == '{': depth += 1
    elif c == ']' or c == '}': depth -= 1
    if depth == 0:
        data_str = content[start:start+i+1]
        break
```

**Find API endpoints:**
- Search for `apiUrl`, `apiExternalUrl`, `baseUrl` in config chunks
- Look for HTTP interceptors (JWT auth, error handling) to understand auth requirements
- Identify service method names that correspond to API calls

**Pitfalls:**
- Wayback wrapper (`_____WB$wombat$_____`) prepends code — strip everything before the first `import{` line
- Minified code uses abbreviated variable names — search by string literals, not variable names
- Some chunks are identical (duplicated by build tool) — skip exact duplicates
- API endpoints may be relative (`/api/v1`) — resolve against the site's base URL
- Auth tokens (JWT) are needed if the interceptor adds `Authorization: Bearer` — check if the route is under PublicLayout or PrivateLayout

### 7. Determine if API data is accessible

From the route config, check if the path is under:
- `PublicLayout` = no auth required (API may work with just IP access)
- `PrivateLayout` = auth guard active (needs JWT token)

Even public routes may have CORS or WAF blocking the API calls from external IPs.

### 8. Find SPA API endpoints via live browser inspection

When a site is an SPA (Nuxt.js, Next.js, Angular) but the SSR snapshots don't contain real data, the data loads client-side via an API. Use the **browser tool** to discover the endpoint.

#### 8a. Identify the SPA framework

Check the DOM for framework-specific markers — the browser snapshot or console can reveal:

```
<div id="__nuxt">    → Nuxt.js (Vue)
<div id="__next">   → Next.js (React)
<div ng-version>    → Angular
<div id="app">       → Generic Vue/React (check further)
```

#### 8b. Find API calls via Performance API

After the page fully loads (SPA makes its XHR/fetch calls), query the resource timing:

```javascript
performance.getEntriesByType('resource').filter(e =>
  e.name.includes('/api/') ||
  e.initiatorType === 'xmlhttprequest'
).map(e => ({url: e.name, duration: Math.round(e.duration), type: e.initiatorType}))
```

**Look for:**
- `initiatorType: 'xmlhttprequest'` — API calls (not page resources)
- Short duration — internal API (fast, not a page load)
- Subdomain patterns like `api.*`, `backend.*`, `data.*`, `services.*`
- Path segments like `/api/`, `/v1/`, `/graphql`, `/search`, `/busqueda`

#### 8c. Spot subdomain API patterns

Many SPA backends live on a separate subdomain. Common patterns:

| Frontend | Likely API subdomain |
|---|---|
| `app.example.com` | `api.example.com` |
| `example.com` | `backend.example.com` or `api.example.com` |
| `app.sedetc.gob.pe` | `jurisbackend.sedetc.gob.pe` ✓ |
| `www.example.org` | `services.example.org` |

The subdomain often mirrors the frontend's domain with a `backend`/`api` prefix, or uses the same root with a different first label.

#### 8d. Verify API endpoint with curl

Once you have candidate URLs, verify them:

```bash
# Check if endpoint exists (406 = exists, wrong Accept)
curl -s -D- "https://backend.example.com/api/search?page=1"

# Try with proper Accept header
curl -s -H "Accept: application/json" "https://backend.example.com/api/search?page=1"
```

**406 Not Acceptable** from Apache is a strong positive signal — the endpoint exists but expects specific headers. The response body may contain the actual JSON despite the 406 status.

#### Critical: User-Agent header can change API response

Some SPA backends check the `User-Agent` header and return **different data** depending on its value. Without a browser-like UA, the server returns a default/fallback response that ignores search and pagination parameters:

```bash
# Without browser UA — same data regardless of search/pagination params
curl -s "https://backend.example.com/api/search?page=1&q=habeas" | wc -c
# -> 21825 (same for every page)

# With browser UA — pagination and search work correctly
curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  "https://backend.example.com/api/search?page=1&q=habeas" | wc -c
# -> 45817 (different per page, search applied)
```

**When to suspect this:** Your curl call returns HTTP 200 with JSON, but the same URL in the browser shows different data. The API silently ignores query parameters when called from non-browser User-Agents.

**Fix:** Always include a full browser User-Agent string when testing SPA APIs discovered via browser inspection:

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
```

#### 8e. Test API pagination

SPA APIs typically support pagination:

```bash
curl -s "https://backend.example.com/api/search?page=1&size=10"
```

Look for `total`, `pagination`, `num_pages` in the response to estimate total data size. If the API is Elasticsearch-backed, expect `_source` envelopes with the actual data.

**Real-world example (TC Peru jurisprudencia):**
- Frontend: `jurisprudencia.sedetc.gob.pe` (Nuxt.js)
- API: `jurisbackend.sedetc.gob.pe/api/visitor/sentencia/busqueda?page=1&size=10`
- Response: ES-backed JSON, 10,000 total, 1000 pages, no auth
- Each item includes `url_archivo` (direct PDF), metadata, and fundamentos text
- See `references/tc-jurisprudencia-api-discovery.md`

## Reference files
- `references/inei-censos2025-extraction.md` — Extracting Censos 2025 territorial data
- `references/legal-articles-corpus-expansion.md` — Expanding a legal RAG corpus from Wayback archive of legal blog: extract 600+ articles, clean blog artifacts, parse to JSON, merge with existing corpus, rebuild FAISS
- `references/tc-jurisprudencia-api-discovery.md` — SPA API discovery for TC Peru's jurisprudence portal
- `references/tc-consulta-causas-wordpress.md` — WordPress/DataTables GET-based scraping for older TC cases
- `references/googletranslate-authwall-bypass.md` — Bypass login/authwalls via Google Translate proxy (confirmed: LinkedIn Jobs)

## Related skills
- `scrapy-selenium-scraping` — for JS-heavy sites where you CAN run a browser
- `scrapy-selenium-captcha-scraping` — when CAPTCHAs are involved
- `spec-driven-development` — SDD workflow for scraper projects (spec → plan → implement, checkpoint pattern)

## 10. Authwall bypass via Google Translate proxy

Some sites serve content to crawler IPs (Googlebot) but block anonymous
visitors with a login wall. Google Translate loads pages from Google's
own servers, so the request arrives from a crawler IP that the target
site trusts.

### When to try it

| Signal | Eligible? |
|---|---|
| Site shows login wall for anonymous visitors | ✅ Often works |
| Site blocks your IP (CAPTCHA/Cloudflare) | ⚠️ Maybe — translate.goog IP may differ |
| Site requires JS execution (SPA) | ⚠️ Only initial HTML, no JS |
| Site requires session/cookies | ❌ No session is carried |

### URL pattern

```
https://translate.google.com/translate?hl=es&sl=auto&tl=es&u=<URL_ENCODED_TARGET>
```

The page loads via `<domain>.translate.goog`. Browse within the proxied
session to stay behind the authwall.

### Confirmed working: LinkedIn Jobs (Jun 2026)

| Feature | Direct | Via Translate |
|---|---|---|
| Jobs search | Count only + login wall | Full listings (9 vs 2 results) |
| Pulse articles | Login wall | Loads if URL exists |
| Company pages | Blocked | Redirects to feed |

### Limitations

- SPA content that fetches data client-side won't render
- Google may throttle aggressive usage  
- Some Cloudflare configs specifically block translate.goog
- Page structure is modified by translation wrapper

See `references/googletranslate-authwall-bypass.md` for details.

## 11. WordPress + DataTables scraping (GET-based)

Some legacy government sites use **WordPress + jQuery DataTables** with server-side processing. Unlike SPAs that load data via XHR JSON, these systems often support **direct GET requests** with pagination parameters — the server renders HTML tables that can be scraped without executing JavaScript.

### When to suspect a WordPress DataTables system

- Page loads show a DataTable with pagination but the HTML contains only table headers, not data rows
- URL parameters like `?pagina=N`, `?page=N`, `?start=N` appear in pagination links
- jQuery + DataTables JS files are loaded (`jquery.dataTables.min.js`)
- WordPress framework markers (`wp-content`, `wp-json`, `admin-ajax`)
- Form submission uses GET (visible params in URL) not POST

### Discovery approach

1. **Search for form IDs**: Look for `id="form_causas"`, `id="btn_consultar"` in the HTML
2. **Check form actions**: Forms without `action` attribute submit to the current URL
3. **Inspect JavaScript handlers**: Search for `btn_consultar`, `form_causas`, `load_table`, `cargar_tabla` in theme JS files
4. **Try GET directly**: Construct `?bus=tc&action=search&a_exp=2022&pagina=1` based on form field names
5. **Look for `total:` in response**: DataTables server-side often injects `total: N` in the HTML

### Common WordPress DataTables URL patterns

```
?bus=tc&action=search&a_exp={YEAR}&pagina={PAGE}
?action=search&anio={YEAR}&page={PAGE}
?consulta=expedientes&year={YEAR}&pag={PAGE}
```

### Parsing pitfalls

- **Expediente numbers are in `<th scope="row">`**, not `<td>`. Always match both: `<(?:td|th)[^>]*>`
- **`id_exp` links are in the last cell**, not the first. Extract `id_exp=N` from the `<a>` link in the row.
- **PDF URLs may contain spaces**: `00001-2022-AA Sentencia.pdf`. Normalize with `re.sub(r'\s+', ' ', filename)`.
- **Some rows have no detail link** (moot court, archived cases). Skip those.
- **Total counts per page** can be extracted via regex: `total:\s*(\d+)`

See `references/tc-consulta-causas-wordpress.md` for a complete real-world example (TC Peru, ~1,160 expedientes, 2018-2022).
