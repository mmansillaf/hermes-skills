# Reconocimiento: cej.pj.gob.pe (Consulta de Expedientes Judiciales - Perú)

## Protecciones identificadas (Jun 2026)

| Capa | Tipo | Detalle |
|---|---|---|
| **Bot Manager** | Radware (perfdrive.com) | Redirige a validate.perfdrive.com con hCaptcha antes de cargar la página real |
| **Captcha externo** | hCaptcha checkbox (Radware) | Sitekey: `ae73173b-7003-44e0-bc87-654d0dab8b75`. Solo visible desde IPs/browsers no confiables |
| **Captcha interno** | Texto PNG (4 chars alfanumericos) | Imagen `Captcha.jpg`. Visible desde Chrome real + perfil persistente |
| **Framework** | Angular (migrado de JSF) | Sin ViewState hidden fields. Compiled JS bundles. |
| **Backend** | Java JBWEB (JBoss/Tomcat) | Server header oculto por Radware |
| **Server descargas** | Apache | `Server: Apache` en respuestas de `documentoD.html` |
| **Version app** | 2.5.0 | |

## URLs conocidas

- `https://cej.pj.gob.pe/cej/forms/busquedaform.html` — búsqueda por nombre/apellido (ACEPTA GET)
- `https://cej.pj.gob.pe/cej/forms/busquedacodform.html` — búsqueda por código de expediente (SOLO POST, GET da 405)
- `https://cej.pj.gob.pe/cej/forms/detalleform.html` — detalle del expediente
- `https://cej.pj.gob.pe/cej/forms/documentoD.html?nid=<HASH>` — descarga de documentos (SIN AUTH, sin rate limiting)
- `https://cej.pj.gob.pe/cej/forms/resumenform.html` — resumen de busqueda (NO tiene documentos directos)
- `https://cej.pj.gob.pe/cej/forms/preguntasFrecuentes.html` — FAQ
- `https://cej.pj.gob.pe/cej/forms/videosTutoriales.html` — videos tutoriales
- `https://cej.pj.gob.pe/cej/Captcha.jpg` — imagen del captcha de texto

## Evidencia de Radware

Cuando se accede desde un headless browser sin protección, Radware responde con:
- URL: `https://validate.perfdrive.com/?ssa=...&ssb=...&ssc=https%3A%2F%2Fcej.pj.gob.pe%2Fcej%2Fforms%2Fbusquedaform.html&...`
- Título: "Radware Captcha Page"
- Mensaje: "your activity and behavior on this site made us think that you are a bot"
- Incident ID generado
- Widget hCaptcha con checkbox "Soy humano"

## Repositorios GitHub relacionados

| Repo | URL | Estado | Notas |
|---|---|---|---|
| **mmansillaf/cej-scraper** | https://github.com/mmansillaf/cej-scraper | ✅ ACTIVO | Scraper optimizado con ddddocr + 2Captcha, descarga paralela, filtro keywords |
| **aniversarioperu/scrapy_pj** | https://github.com/aniversarioperu/scrapy_pj | Obsoleto | Spider Scrapy para `jurisprudencia.pj.gob.pe` (subdominio diferente, Corte Suprema). Usa JSF postbacks. Pre-Radware. |
| **Datos-Incorruptibles/poder-judicial-scraper** | https://github.com/Datoss-Incorruptibles/poder-judicial-scraper | Obsoleto | Selenium + OCR (pytesseract) para captcha de texto antiguo. El captcha ya no es texto, es hCaptcha. |
| **sillydrycoder/judicial_records_scrapper** | https://github.com/sillydrycoder/judicial_records_scrapper | No relevante | Scraper para `www.poderjudicial.es` (ESP, no Perú) |

## Código de expediente (búsqueda por código)

Formato: `NNNNN-AAAA-I-DDDD-OO-EE-II`
Ejemplo: `00060-2021-0-1801-JR-DC-03`

| Campo | ID | Descripcion |
|---|---|---|
| Número | `cod_expediente` | 5 digitos |
| Año | `cod_anio` | 4 digitos |
| Incidente | `cod_incidente` | Generalmente 0 |
| Distrito/Prov | `cod_distprov` | 4 digitos (ej: 1801) |
| Órgano | `cod_organo` | JP (Juzgado Paz), JR (Juzgado) |
| Especialidad | `cod_especialidad` | CI (Civil), PE (Penal), LA (Laboral), FC (Familia), DC (Constitucional) |
| Instancia | `cod_instancia` | 01-09 |
| **Parte** | `parte` | **OBLIGATORIO** — Nombre del demandante/demandado |

**IMPORTANTE:** El campo `parte` es obligatorio. Sin el nombre exacto de la parte, el sistema rechaza la busqueda aunque el captcha sea correcto.

## Bypass probado y funcional (Jun 2026)

### Setup

```bash
python3 -m venv ~/cej-scraper
source ~/cej-scraper/bin/activate
pip install rebrowser-playwright 2captcha-python selenium ddddocr opencv-python-headless
python -m rebrowser_playwright install chromium
```

### Flujo que funciona (sin Radware)

**Hallazgo clave**: Radware NO bloquea el acceso vía `busquedaform.html`. Solo bloquea GET directo a `busquedacodform.html`.

```
1. Chrome real + perfil persistente (o rebrowser-playwright con stealth)
2. Navegar a https://cej.pj.gob.pe/cej/forms/busquedaform.html
3. Click en tab "Por Código de Expediente" (a[href="#tabs-2"])
4. Llenar 7 campos + campo "parte"
5. Resolver captcha de texto (ddddocr + 2Captcha combo)
6. Click Consultar → resultados
7. Click lupa/boton → detalle del expediente
8. Extraer datos + descargar documentos
```

### Chrome Remote Debugging (recomendado, funciona en Linux y Windows)

```bash
google-chrome --remote-debugging-port=9225 \
  --user-data-dir=/home/usuario/.chrome_cej \
  --no-first-run --no-default-browser-check \
  "https://cej.pj.gob.pe/cej/forms/busquedaform.html"
```

```python
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9225")
driver = webdriver.Chrome(options=options)
```

El perfil persistente de Chrome evita Radware por completo.

### Si Radware se activa (2Captcha fallback)

```python
from twocaptcha import TwoCaptcha
solver = TwoCaptcha("API_KEY")
result = solver.hcaptcha(sitekey="ae73173b-7003-44e0-bc87-654d0dab8b75", url=page.url)
token = result.get('code')

page.evaluate("""(token) => {
    const ta = document.querySelector('textarea[name="h-captcha-response"]');
    if (ta) { ta.value = token; }
    if (typeof hcaptcha !== 'undefined') { hcaptcha.setResponse(token); }
}""", token)
```

### Captcha de texto: ddddocr + 2Captcha combo

Probado exitosamente: ddddocr resolvio el captcha `K5GK` y `KK90` sin necesidad de 2Captcha.

```python
import ddddocr, base64, requests, time
ocr_local = ddddocr.DdddOcr()

def resolver_captcha(imagen_bytes):
    resultado = ocr_local.classification(imagen_bytes)
    if resultado:
        resultado = resultado.strip().upper()
        if len(resultado) == 4 and resultado.isalnum():
            return resultado, 'ocr'
    # Fallback 2Captcha
    b64 = base64.b64encode(imagen_bytes).decode()
    task = {"clientKey": API_KEY, "task": {
        "type": "ImageToTextTask", "body": b64,
        "numeric": 0, "minLength": 4, "maxLength": 4}}
    r = requests.post("https://api.2captcha.com/createTask", json=task, timeout=30).json()
    if r.get("errorId") == 0:
        tid = r["taskId"]
        for _ in range(30):
            time.sleep(3)
            poll = requests.post("https://api.2captcha.com/getTaskResult",
                json={"clientKey": API_KEY, "taskId": tid}, timeout=15).json()
            if poll.get("status") == "ready":
                return poll["solution"]["text"], '2captcha'
    return None, None
```

### VPN como ayuda para bypass

Proton VPN (WireGuard, servidor México) permitió acceso directo sin Radware:

```bash
sudo apt install wireguard
# Config desde account.protonvpn.com → Descargas → WireGuard
sudo wg-quick up /home/usuario/proton-configs/mx.conf
curl -s https://api.ipify.org  # → IP mexicana
```

**Resultados VPN:**

| VPN | Protocolo | Resultado |
|---|---|---|
| Proton VPN Netherlands (NL-FREE) | OpenVPN | Radware bloqueó ❌ |
| Proton VPN Mexico (MX-FREE#6) | WireGuard | Radware pasó ✅ |

## Descarga de documentos

### Endpoint
```
GET https://cej.pj.gob.pe/cej/forms/documentoD.html?nid=<HASH>
```

**Caracteristicas clave:**
- NO requiere cookies de sesion
- SIN rate limiting — acepta requests en paralelo
- Clase CSS de enlaces: `aDescarg`
- 2 tipos de respuesta:
  - **PDF** (Content-Type: application/pdf) — resoluciones reales
  - **HTML** (~15KB, Content-Type: text/html) — notificaciones/cédulas

### Descarga paralela (probado, seguro)
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def descargar(nid, exp, idx):
    r = requests.get(f"https://cej.pj.gob.pe/cej/forms/documentoD.html?nid={nid}", timeout=30)
    ext = '.pdf' if r.content[:4] == b'%PDF' else '.html'
    fname = f"{exp}_doc_{idx}{ext}"
    with open(fname, 'wb') as f: f.write(r.content)
    return idx, ext, len(r.content)

with ThreadPoolExecutor(max_workers=5) as ex:
    fut = [ex.submit(descargar, nid, exp, i) for i, nid in enumerate(nids)]
```

**Resultado:** 36 documentos en ~3s (vs ~216s en serie).

### Filtro por keywords (solo documentos valiosos)
```python
KEYWORDS = ['SENTENCIA', 'RESOLUCION', 'AUTO FINAL', 'FUNDADA',
            'INFUNDADA', 'IMPROCEDENTE', 'DEMANDA', 'SE ADMITE',
            'CONCLUSION', 'CONSENTIDA']

def es_valioso(texto):
    return any(kw in texto.upper() for kw in KEYWORDS)
```

## Analisis de nids

18 nids del expediente `00060-2021-0-1801-JR-DC-03`:
- Longitudes: 15 a 20 chars (todas distintas)
- Prefijos (3 chars): 18 diferentes
- Caracteres: a-Z (no numeros)
- **CONCLUSION:** Sin patron detectable. No se pueden inferir nids de otros expedientes.

## Observaciones tecnicas

| Aspecto | Hallazgo |
|---|---|
| **Frontend** | Angular compilado (NO JSF). Sin ViewState. |
| **busquedacodform.html GET** | HTTP 405 Method Not Allowed |
| **Server header** | `server: rdwr` (Radware) |
| **Server descargas** | `server: Apache` |
| **CSRF token** | VACIO `<meta name="_csrf" content="">` |
| **Stormcaster JS** | Tracking Radware: UUID path |
| **Session timeout** | ~15 min, muestra "fin de espera" |
| **No rate limiting** en documentD.html | Descarga paralela funciona sin bloqueo |
| **Datos personales** | Nombres completos expuestos |

## Seguridad: hallazgos

| # | Hallazgo | Severidad |
|---|---|---|
| 1 | CERO headers de seguridad (HSTS, CSP, X-Frame, etc.) | CRITICO |
| 2 | Clickjacking posible (sin X-Frame-Options) | ALTO |
| 3 | Cookies sin HttpOnly/Secure | ALTO |
| 4 | CSRF token vacio | MEDIO |
| 5 | Sin JSF ViewState (migrado a Angular) | INFO |
| 6 | documentD.html sin auth (solo hash nid) | MEDIO |
| 7 | Sin rate limiting en descargas | INFO |

## Multi-pestana: limitacion conocida

Probado en Windows con 2 ventanas Chrome (puertos 9225 y 9226):
- Inicialmente funciono: 2 spiders en paralelo
- Despues de ~100 expedientes, solo 1 ventana seguia funcionando
- Radware correlaciona las sesiones aunque sean puertos diferentes
- **RECOMENDACION:** MAX 1 instancia de Chrome por vez

## Proxies residenciales recomendados

| Proveedor | Precio/GB | Notas |
|---|---|---|
| DataImpulse | $1.00 | PAYG, trafico no expira, 90M IPs |
| Decodo | $2.75-3.75 | 195+ paises, cupon DECODO5 |
| Evomi | $0.49 | Mas barato, add-ons extra |
| Bright Data | $4.00 | Premium, cupon PROXYWAY60 |

## Herramientas instaladas

```bash
~/cej-scraper/bin/  # venv con:
  rebrowser-playwright, 2captcha-python, selenium, wapiti3,
  undetected-chromedriver, ddddocr, opencv-python-headless
```
