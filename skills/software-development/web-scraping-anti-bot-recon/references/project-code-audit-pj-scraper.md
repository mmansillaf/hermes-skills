# Project Code Audit: poder_judicial_results (Scraper PJ Peru)

## Overview

A Scrapy/Selenium hybrid scraper for cej.pj.gob.pe (Consulta de Expedientes Judiciales del Perú).
Uses undetected-chromedriver with Chrome real profile + 2Captcha for text CAPTCHA solving.
Runs on Windows with Chrome remote debugging, two parallel instances (A and B).

**Optimized version published at:** https://github.com/mmansillaf/cej-scraper
**Script de prueba:** `cej_scraper_optimizado.py` (ddddocr + 2Captcha combo, descarga paralela, filtro keywords)

## Key Stats (as of Jun 2026)

- **Total expedientes**: 38,242 (LA + DC)
- **Completados**: 334 (0.9%)
- **PDFs descargados**: 826 (169 MB)
- **Captcha fails**: 554 (vs 334 OK — ~62% fail rate)

## Architecture

```
run_A.py → env vars → scrapy crawl poder_opt
                                          ↓
                         PoderSpiderOptimizado (spider)
                              ↓                    ↓
                    Selenium Chrome            Scrapy idle loop
                    (undetected)               (for auto-restart)
                              ↓
                    busquedaform.html
                    → tab "Por Código"
                    → llenar 7 campos + parte
                    → resolver captcha (2Captcha)
                    → submit → resultados
                    → click lupa → detalle
                    → extraer datos → CSV
                    → descargar PDFs (serial, 8-15s sleep)
```

## Project Structure

```
poder_judicial_results/
├── spiders/poder_opt.py      # Spider principal (938 lines)
├── items.py                  # Empty (no fields defined)
├── pipelines.py              # Empty pass-through
├── middlewares.py            # Default Scrapy boilerplate
├── settings.py               # AUTOTHROTTLE enabled, ROBOTSTXT_OBEY=False
├── runner.py                 # Auto-reboot loop (max 90 min/run)
├── run_A.py / run_B.py       # Entry points for two parallel instances
├── stats.py                  # Real status against disk PDFs
├── remote_poder.py           # Connect to Chrome via remote debugging
├── cej_scraper_optimizado.py # NUEVO: script optimizado con ddddocr + descarga paralela
├── cej_scraper_test.py       # NUEVO: script de prueba con ddddocr
├── input/                    # Excel files with expediente codes
│   ├── slice_A.xlsx          # Spider A input
│   ├── slice_B.xlsx          # Spider B input
│   ├── LA_DC.xlsx            # Master file
│   └── ExpedienteCodeDownload.xlsx
├── output/                   # CSVs with extracted data
├── details/                  # CSVs with detailed extraction
├── documents/                # Downloaded PDFs (per-expediente folders)
├── debug_captcha/            # Screenshots on captcha failure
└── checkpoint_opt_A/B.json   # Resume checkpoints
```

## Technology Stack

| Component | Technology |
|---|---|
| Framework | Scrapy 2.11+ |
| Browser | undetected-chromedriver 3.5 |
| Captcha | 2Captcha API v2 (createTask/getTaskResult) |
| Input | openpyxl (Excel) |
| Output | CSV (csv.DictWriter) |
| Chrome | Real Chrome + user-data-dir (persistent profile) |
| Platform | Windows (original) / WSL (Linux) |

## Issues Found (P1-CRITICAL)

### 1. Captcha fail rate ~62% (P1)
- 554 fails vs 334 OK = ~62% failure rate
- Each fail costs ~2-3 min + screenshot
- **SOLUCION PROBADA**: ddddocr + 2Captcha combo. En pruebas desde Ubuntu:
  - ddddocr resolvio `K5GK` y `KK90` exitosamente (0 costo)
  - Combo estimado: ~60-80% de acierto vs 35-50% actual
  - **Script en GitHub:** https://github.com/mmansillaf/cej-scraper

### 2. Throughput too slow (P1)
- ~5-8 exp/hour effective rate
- At this rate: 2,500+ hours for remaining 37,908 expedientes
- **SOLUCION PROBADA**: Descarga paralela de documentos:
  - documentD.html NO tiene rate limiting
  - 5 workers en paralelo: 36 documentos en ~3s (vs ~216s en serie)
  - **Ahorro: ~98% del tiempo de descarga**

### 3. items.py is empty (P3)
- `PoderJudicialResultsItem` has `pass` — no fields defined
- Uses OrderedDict inline instead of typed Scrapy Items

### 4. Scrapy used as mock (P3)
- Real work is done by Selenium, not Scrapy
- Scrapy only provides the idle loop for auto-restart

### 5. No retry on download (P2)
- `requests.get(url, timeout=30)` has no retry logic
- Network blips cause lost PDFs

### 6. Hardcoded paths (P2)
- `CHROME_BINARY_PATH`, `CHROME_DRIVER_PATH` hardcoded in run scripts

## New Findings from Ubuntu Test (Jun 2026)

### ddddocr funciona en Linux
- Resolvio captcha `K5GK` y `KK90` sin 2Captcha
- Tasa estimada: ~40-60% en primera pasada
- Cuando falla, 2Captcha como fallback
- Ahorro: ~50% del costo de captchas

### Descarga paralela confirmada
- documentD.html acepta requests sin cookies ni rate limiting
- 5 workers simultaneos funcionaron sin bloqueo
- 36 documentos en ~3 segundos

### Filtro por keywords implementado
- Solo descarga documentos con: SENTENCIA, RESOLUCION, AUTO FINAL, FUNDADA, INFUNDADA, IMPROCEDENTE, DEMANDA, etc.
- Aplica pre-descarga (no gasta ancho de banda en notificaciones)

### Multi-pestaña: NO recomendado
- En Windows funciono temporalmente con 2 Chrome
- Despues de ~100 expedientes, solo 1 seguia funcionando
- Radware correlaciona sesiones

### Scripts creados
| Script | Descripcion |
|---|---|
| `cej_scraper_test.py` | Prueba inicial con ddddocr |
| `cej_scraper_optimizado.py` | Version completa con combo captcha + descarga paralela + filtro |

## Key Learnings

1. **Radware deploy differs by environment**: Windows + Chrome real profile = text PNG captcha only. Linux headless = hCaptcha.
2. **ddddocr funciona** para el captcha de texto del CEJ - prueba exitosa en 2/2 intentos.
3. **documentD.html sin rate limiting** - la descarga paralela es segura y efectiva.
4. **VPN Mexico ayuda**: Proton VPN MX (WireGuard) paso Radware desde Linux.
5. **Chrome remote debugging es el mejor bypass**: Funciona en Linux y Windows.
6. **Parte field es OBLIGATORIO** - el scraping falla sin el nombre de la parte.
7. **Filtro pre-descarga reduce tiempo**: no descargar notificaciones/cédulas (HTML ~15KB), solo resoluciones (PDF).

## Optimizaciones Recomendadas (aplicables al proyecto Windows)

| Prioridad | Cambio | Impacto |
|---|---|---|
| P1 | Reemplazar 2Captcha con ddddocr + fallback | 2-3x throughput, 50% menos costo |
| P1 | Paralelizar descarga de documentos | 98% mas rapido en descarga |
| P2 | Reducir cooldown entre expedientes | 2x throughput |
| P3 | Parametrizar paths via .env | Portabilidad |
