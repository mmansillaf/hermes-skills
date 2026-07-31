# SEDETC TC Implementation — 2026-06-13

## Session Summary

Built and deployed a scraper for the Tribunal Constitucional's jurisprudencia
portal (`jurisprudencia.sedetc.gob.pe`), completing the full catalog of ~10,000
PDFs across two batch runs with zero permanent failures.

## Batch Run Results

### Batch 1: First 1,000 (fresh, no --resume)

| Metric | Value |
|--------|-------|
| PDFs | 1,000 |
| OK | 1,000 |
| FAIL | 0 |
| Time | 188s (3m 8s) |
| Size | 794.9 MB |
| API calls | ~100 pages |
| Years | 2026 (426), 2025 (573), 2024 (1) |

### Batch 2: Full catalog (resume from page 521 after bugfix)

| Metric | Value |
|--------|-------|
| PDFs | ~10,000 (9,997 unique + 3 duplicates) |
| OK | 8,999 |
| SKIP | 1,001 (existing from batch 1) |
| FAIL | 0 |
| Time | 1,646s (27.4 min) |
| Size | 4,364.6 MB (4.3 GB) |

### Final Distribution

| Year | PDFs | MB |
|------|------|----|
| 2026 | 426 | 346.9 |
| 2025 | 4,945 | 2,729.6 |
| 2024 | 4,394 | 1,224.4 |
| 2023 | 234 | 63.7 |
| **Total** | **9,999** | **4,364.6** |

### Type Distribution

| Type | Count | % |
|------|-------|---|
| AA (Acción de Amparo) | ~4,700 | 47% |
| HC (Hábeas Corpus) | ~3,560 | 36% |
| AC (Acción de Cumplimiento) | ~430 | 4% |
| HD (Hábeas Data) | ~190 | 2% |
| Q (Queja) | ~210 | 2% |
| PI/CC (Conflicto Competencial) | ~40 | <1% |
| AI (Acción de Inconstitucionalidad) | ~180 | 2% |
| Sub-variants (Aclaración, Nulidad, etc.) | ~690 | 7% |

## Bug Encountered: `sentencia_distrito: null`

### Error

```
AttributeError: 'NoneType' object has no attribute 'get'
```

On page 522, an item had `sentencia_distrito: null` (Pleno session case
`02203-2023-AA (Amicus Curiae)`). The code used:
```python
src.get("sentencia_distrito", {}).get("nombre", "")
```
When the key EXISTS with a null value, `.get(key, {})` returns `None`
(the default `{}` is only used if the key is MISSING, not when it's null).
Calling `.get("nombre", "")` on `None` raises `AttributeError`.

### Fix

```python
(src.get("sentencia_distrito") or {}).get("nombre", "")
```

This handles both missing keys (→ `{}`) and null values (→ `{}`).

### Resume After Crash

The checkpoint had `last_metadata_page: 520` with 5,200 cached items.
Running with `--resume` continued from page 521, deduplicated the first
5,200 items, and collected the remaining 4,800 items.

## API Discovery Walkthrough

### Step 1: Browser fails

`browser_navigate` to the SPA URL returned empty page or "Loading..." state.
Standard SSR page (via `web_extract`) showed the server-side shell but no data.

### Step 2: Find API endpoints

```javascript
// In browser_console, after page fully loaded:
performance.getEntriesByType('resource').map(e => e.name)
```

This revealed:
- `https://jurisbackend.sedetc.gob.pe/api/visitor/init`
- `https://jurisbackend.sedetc.gob.pe/api/visitor/sentencia/busqueda`
- `https://jurisbackend.sedetc.gob.pe/api/visitor/sentencia/tipo/74818`

### Step 3: Test API — fails without User-Agent

```bash
curl "https://jurisbackend.sedetc.gob.pe/api/visitor/sentencia/busqueda?page=1"
```
Returns HTTP 406 Not Acceptable (Apache). Adding `User-Agent: Mozilla/5.0`
makes it return proper JSON with HTTP 200.

### Step 4: Verify PDFs

```bash
curl -s "https://tc.gob.pe/jurisprudencia/2026/04442-2024-AA.pdf" | head -c5
# → %PDF-  ✅
```

### Step 5: Build scraper

See `tc_scraper.py` in `D:\\PyCode\\TC_SEDETC_Scraper\\`. Architecture:
- Phase 1: Serial API calls with 1.2s throttle, checkpoints every 10 pages
- Phase 2: 24 worker ThreadPoolExecutor for PDFs
- Resumable via checkpoint.json

## API Catalog Limits

- **Hard cap**: 10,000 items (1,000 pages × 10 items/page)
- **Page 1001+**: HTTP 500 (Laravel `UnexpectedValueException: log file cannot be opened in append mode`)
- **Earliest data**: November 2023 (page 1000)
- **Latest data**: March 2026 (page 1)
- **No 2022-or-carlier publication data** available via this API

## Connection Pool Warning

With 24 workers and default `requests.Session()` pool size of 10,
warnings appeared: `Connection pool is full, discarding connection`.
All PDFs still downloaded successfully (no failures), but the warnings
are noisy. Fix for future: increase `pool_maxsize=24` on the session adapter.

## Project Structure

```
D:\\PyCode\\TC_SEDETC_Scraper\\
├── tc_scraper.py          # Main: metadata + download + checkpoint + CLI
├── specs/
│   ├── CONSTITUTION.md    # Principles
│   ├── SPEC-001-scraper.md # Behavior spec with acceptance criteria
│   └── PLAN-001-scraper.md # Technical plan
├── data/
│   ├── metadata.csv       # 10,000 rows: expediente, tipo, fecha, url_pdf, etc
│   ├── checkpoint.json    # Resumable progress (phase: download_done)
│   └── errors.json
└── pdfs/
    ├── 2023/              # 234 PDFs
    ├── 2024/              # 4,394 PDFs
    ├── 2025/              # 4,945 PDFs
    └── 2026/              # 426 PDFs
```
