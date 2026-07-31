# Node.js vs Python para Scraping del CEJ — Evaluación (Junio 2026)

## Contexto

Evaluación práctica de si Node.js (puppeteer-extra + stealth-plugin) ofrece
ventajas reales sobre Python (undetected-chromedriver + Scrapy) para el scraper
del CEJ (Poder Judicial Peruano), que está protegido por Radware/PerfDrive WAF.

## Resultado: No migrar. Python es la opción correcta aquí.

## Razón #1: WSL ↔ Windows es el problema real, no el lenguaje

El scraper del CEJ tiene que interactuar con **Chrome.exe en Windows** desde
**WSL**. Esto implica:

| Tarea | Python | Node.js |
|-------|--------|---------|
| Ejecutar Chrome.exe | `subprocess.Popen(['chrome.exe', ...], shell=True)` ✅ | `puppeteer.launch({executablePath: '/mnt/c/...'})` ❌ path no existe |
| Pasar `--user-data-dir` (ruta Windows) | `D:\\PyCode\\...` funciona directamente ✅ | `/mnt/d/...` no funciona para Chrome.exe, y convertir rutas WSL↔Windows añade complejidad |
| Detectar procesos Windows | `wmic process` via `subprocess.run(['cmd.exe','/c','wmic',...])` ✅ | No hay equivalente limpio desde Node.js en WSL — `child_process` no tiene wmic |
| Matar procesos | `taskkill` via PowerShell ✅ | `spawn('taskkill')` falla con ENOENT desde WSL |
| PowerShell quoting | `f'...'` con escapes funciona ✅ | Template strings con escapes anidados son propensos a errores |

**El problema de base**: puppeteer (Node.js) espera lanzar Chrome directamente.
Pero desde WSL, Chrome.exe no se comporta igual que desde Windows nativo. La
ruta `/mnt/c/...` no es accesible para `puppeteer.launch()` porque Node.js
verifica `fs.existsSync` contra el filesystem WSL, no contra el filesystem
Windows.

## Razón #2: puppeteer-extra-stealth no pudo probarse contra CEJ

El principal argumento a favor de Node.js era `puppeteer-extra-plugin-stealth`,
que tiene parches anti-detección más avanzados que `undetected-chromedriver`.

**Pero no se pudo probar**: el PoC falló en la conexión CDP porque Chrome
lanzado desde WSL no expuso `--remote-debugging-port` confiablemente.

La ventaja teórica de stealth **nunca llegó a probarse** contra el Radware del CEJ.

## Razón #3: La infraestructura existente es Python

El scraper actual (937 líneas en `poder_opt.py` + MCP server + pipelines) ya:

- Descarga resoluciones del CEJ con Radware bypass probado
- Maneja captcha loop con 2captcha (send_keys 100% vs execute_script 72%)
- Tiene checkpoint/resume, filtro DOC_KEYWORDS, CSV output
- Tiene un MCP server HTTP (FastMCP) funcionando con Hermes
- Maneja 2 spiders en paralelo (puertos 9222/9223)

Reescribir todo para Node.js por una ventaja teórica no justifica el riesgo.

## Cuándo Node.js SÍ tendría sentido

Node.js + puppeteer-extra-stealth sería mejor si:

1. **Chrome corriera nativo en Linux** (no Windows + WSL) — entonces puppeteer
   podría lanzarlo directamente sin fricción WSL↔Windows.
2. **Radware empezara a bloquear consistentemente** a undetected-chromedriver
   y los parches de stealth demostraran evadirlo.
3. El proyecto se moviera a un **VPS Linux** donde Node.js + Playwright nativo
   funcionan sin problemas de interoperabilidad.

Ninguna de estas condiciones se cumple hoy.

## Recomendación

Optimizar el scraper Python actual antes que migrar:
- Mejorar captcha rate (cambiar solver si 2captcha degrada)
- Reducir falsos positivos de Radware con mejores sleeps y cooldowns
- Agregar rotación de fingerprints vía CDP donde sea posible
- Si Radware aprieta, probar `curl_cffi` para TLS fingerprint spoofing desde
  Python (más rápido de implementar que una migración completa a Node.js)
