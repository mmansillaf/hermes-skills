# TC Peru Jurisprudencia — SPA API Discovery

## Site
- **Frontend**: `https://jurisprudencia.sedetc.gob.pe/sistematizacion-jurisprudencial/busqueda`
- **Framework**: Nuxt.js (Vue.js + Vuetify) — SSR + SPA hybrid
- **Domain**: SEDETC = Sistema de Estadística y Documentación del Tribunal Constitucional del Perú

## API Discovery Path

1. Browser showed empty page (SPA waiting for JS). `web_extract` returned partial SSR shell.
2. Checked `document.getElementById('__nuxt')` → confirmed Nuxt.js.
3. Installed XHR/fetch interceptors in browser console, navigated to trigger API calls.
4. Interceptors missed the initial load (SPA uses axios, not native fetch).
5. **Breakthrough**: Used `performance.getEntriesByType('resource')` to find all network requests after the page loaded.

## API Details

### Main search endpoint
```
GET https://jurisbackend.sedetc.gob.pe/api/visitor/sentencia/busqueda?page=1&size=10
```

### Init endpoint (districts, rooms, keywords, types)
```
GET https://jurisbackend.sedetc.gob.pe/api/visitor/init
```
Returns: `distritos_judiales`, `salas`, `sentidos`, `tipos`, `palabras`, `sentencias` — usable as filter definitions.

### Individual sentencia type
```
GET https://jurisbackend.sedetc.gob.pe/api/visitor/sentencia/tipo/{id}
```

### Required headers
- `User-Agent: Mozilla/5.0 ...` — **mandatory**. Without it, the API returns ~21KB of default data ignoring all params.
- `Accept` is not required (returns `application/json` even with `text/html` Accept).

### Rate limiting
- `X-RateLimit-Limit: 60` requests per minute
- `X-RateLimit-Remaining: N` decrements per call

### Infrastructure
- **Host**: AWS EC2 (`54.146.225.190`)
- **Server**: Apache (PHP backend)
- **Database**: Elasticsearch (index `sentencias`, seen in `_index` field)

## Response Format (Elasticsearch-backed)

```json
{
  "error": false,
  "message": "Consulta correctamente",
  "data": [
    {
      "_index": "sentencias",
      "_type": "_doc",
      "_id": "74818",
      "_source": {
        "id": 74818,
        "numero_expediente": "04442-2024-AA",
        "numero_sentencia": "312/2026",
        "url_archivo": "https://www.tc.gob.pe/jurisprudencia/2026/04442-2024-AA.pdf",
        "slug": "04442-2024-aa-312-2026",
        "fecha_publicacion": "2026-03-04",
        "sentencia_sala": {"id": 2, "nombre": "Sala 2", "slug": "sala-2"},
        "sentencia_distrito": {"id": 6, "nombre": "Distrito Judicial de Cajamarca"},
        "nombre_demandante": "Marina Ríos Morales",
        "nombre_demandado": "Municipalidad Provincial de Cajamarca",
        "fundamentos": ["... array of legal text paragraphs ..."]
      },
      "sort": [1772582400000]
    }
  ],
  "total": {"value": 10000, "relation": "gte"},
  "searching_for_letter": false,
  "pagination": {
    "current_page": 1,
    "total_item": 10000,
    "num_items": 10,
    "num_pages": 1000,
    "show_pagination": 5
  }
}
```

## Data Distribution

| Pub Year | Pages (est.) | PDFs (est.) | Exp Years |
|---|---|---|---|
| 2026 | 1-100 | ~1,000 | 2023-2025 |
| 2025 | 100-600 | ~5,000 | 2023-2025 |
| 2024 | 600-900 | ~3,000 | 2022-2024 |
| 2023 | 900-1000 | ~1,000 | 2022-2023 |

**Total**: 10,000+ (relation: `gte` = greater than or equal; cap may be higher)

## Types (from expediente code suffix)

| Code | Type |
|---|---|
| AA | Acción de Amparo (~45%) |
| HC | Hábeas Corpus (~45%) |
| AC | Acción de Cumplimiento (~8%) |
| HD | Hábeas Data (~2%) |

## PDF Details

- **URL pattern**: `https://tc.gob.pe/jurisprudencia/{year}/{expediente}.pdf`
- **Verification**: HTTP 200 on all tested years (2023, 2024, 2025, 2026)
- **Size**: 200-800 KB typical (samples: 241KB, 255KB, 285KB, 291KB, 816KB)
- **Server**: `tc.gob.pe` — no rate limit headers observed
- **Redirects**: `tc.gob.pe` redirects to `www.tc.gob.pe` — handle with `curl -L` or `allow_redirects=True`
- **All items have `url_archivo`** — no missing PDFs in any sampled page

## Scraping Strategy

### Phase 1: Metadata (API)
- Iterate pages 1-1000 at 10-20 req/min (stay under 60/min limit)
- Save each page's `_source` as JSON lines or CSV
- Key fields: `numero_expediente`, `numero_sentencia`, `fecha_publicacion`, `url_archivo`, `nombre_demandante`, `nombre_demandado`, `fundamentos`, `sentencia_sala`, `sentencia_distrito`

### Phase 2: PDFs (direct HTTP)
- No rate limit on `tc.gob.pe` — can use ThreadPoolExecutor (10-20 workers)
- Follow redirects (`tc.gob.pe` -> `www.tc.gob.pe`)
- Save to `documents/{year}/{expediente}.pdf`
- Expected: ~10,000 PDFs, 2-8 GB total

### No GitHub scrapers exist
- First public scraper for this system.
