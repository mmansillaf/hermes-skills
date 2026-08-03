# CEJ Scraper (cej.pj.gob.pe)

## Stack
- Python 3.11, Scrapy, Selenium (puro, no undetected_chromedriver)
- Chrome 149, ChromeDriver version_main=149
- Captcha: 2Captcha API (primario) + ddddocr (fallback local)
- WAF: Radware (perfdrive.com)

## Convenciones
- NO usar undetected_chromedriver — usar Selenium puro con CDP anti-detección
- Para paralelismo: Selenium puro (2 instancias simultáneas OK)
- Descarga serial con sleep 8-15s entre requests (Radware detecta ráfagas)
- Filtro post-descarga por contenido PDF (pymupdf), NO pre-filtrado por HTML

## Comandos clave
- `python run_ettda_linux.py` — entry point principal (ETTDA completo)
- `python run_A_parallel.py` — spider A (lote 0-5)
- `python run_B_parallel.py` — spider B (lote 5-10)
- `python cej_scraper_optimizado.py` — script standalone (ddddocr + 2Captcha)
- `python test_captcha.py` — probar resolución de captcha

## Reglas críticas
- Campo `parte` OBLIGATORIO en formulario de búsqueda
- documentD.html SOLO funciona con sesión CEJ viva (cookies + headers exactos)
- Si Radware bloquea: navegar con driver.get() primero, re-obtener cookies, reintentar
- page_load_strategy='none' + CDP bypass cuando la página ya tiene frame Radware
- max 1 Chrome en paralelo para navegación (2 para descarga paralela OK)

## Headers para descarga documentD.html
- referer: exactamente https://cej.pj.gob.pe/cej/forms/detalleform.html
- user-agent: Chrome 149 Linux
- Cookies extraídas DESPUÉS de llegar a detalleform.html

## Costos
- 2Captcha: $0.0002 por captcha (ImageToTextTask)
- ~10,000 captchas por $1.99
- API key en .env
