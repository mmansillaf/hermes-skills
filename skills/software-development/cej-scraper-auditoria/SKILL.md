---
name: cej-scraper-auditoria
description: "Flujo completo de scraping, descarga masiva optimizada y auditoria de seguridad para cej.pj.gob.pe (Consulta de Expedientes Judiciales - Poder Judicial Peru). Incluye bypass de Radware, resolucion de captcha combinada (ddddocr + 2Captcha), extraccion de datos, descarga paralela con filtro inteligente por keywords, y auditoria de vulnerabilidades."
version: 4.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [cej, poder-judicial, scraping, radware, captcha, ddddocr, descarga-paralela, filtro-keywords, python, selenium]
---

# CEJ Scraper + Descarga Masiva Optimizada (v4)

## Stack del sitio

| Componente | Detalle |
|---|---|
| WAF | Radware (perfdrive.com) - `server: rdwr` |
| Captcha externo | hCaptcha (sitekey: `ae73173b-7003-44e0-bc87-654d0dab8b75`) |
| Captcha interno | Imagen `Captcha.jpg`, 4 chars alfanumericos |
| Frontend | jQuery 1.10.2 + Bootstrap + Angular |
| Backend | Java JBWEB, migrado JSF → Angular + REST |
| Server docs | Apache |
| Version | 2.5.0 |

---

## 1. OPTIMIZACIONES COMPROBADAS

| # | Optimizacion | Ganancia | Estado |
|---|---|---|---|
| 1 | **Selenium puro** (reemplaza undetected_chromedriver) | Elimina race condition en paralelo, -87% RAM (740MB→97MB) | ✅ Nuevo estandar |
| 2 | **ddddocr** OCR local para captcha (gratis) | Reduce costo 2Captcha ~50% | ✅ Probado OK |
| 3 | ~~Descarga paralela (5 workers)~~ | ~~98% mas rapido~~ | ❌ **DESACTIVADO** — ThreadPoolExecutor genera ráfagas que Radware detecta como DDoS. Solo descarga SERIAL con sleep 8-15s. |
| 4 | **Filtro por keywords** pre-descarga | Solo documentos valiosos | ✅ Implementado |
| 5 | **2Captcha como resolvedor principal** (ddddocr fallback) | 100% acierto en pruebas (vs ~35-50% ddddocr solo) | ✅ Recomendado |
| 6 | **Sesiones paralelas (multi-pestana/Chrome)** | 2x velocidad | ⚠️ Solo con Selenium puro |

## 2. VECTORES EXPLOTABLES (hacks)

| # | Vector | Valor | Seguro? | Detalle |
|---|---|---|---|---|
| 1 | **documentD.html** — requiere sesion viva + referer | ⚠️ MEDIO | ❌ NO desde Ubuntu | En Windows funcionaba con HTTP directo. **En Ubuntu Chrome 149 (2026) da "Acceso denegado"** incluso con cookies validas. El CEJ agrego proteccion anti-hotlinking. Solucion: hacer click en el link DENTRO de Chrome (navegar con driver.get()), NO requests.get() directo. |
| 2 | **ddddocr para captcha** | 🔥 ALTO | ✅ SI | OCR local gratuito. Resolvio captcha OK en prueba (codigos "K5GK", "54J0") |
| 3 | **Filtro keywords pre-descarga** | ✅ SI | Analizar texto del item. Solo bajar SENTENCIA, RESOLUCION, DEMANDA, etc |
| 4 | **Multiples pestanas Chrome** | ⚠️ EXPERIMENTAL | Comparten cookies Radware. En Windows dejo de funcionar eventualmente |
| 5 | **Cache/inferencia de nids** | ❌ NO CONFIRMADO | 18 nids de un exp: 18 prefijos distintos, 6 longitudes distintas (15-20 chars). Sin patron. Inviable |
| 6 | **resumenform.html como atajo** | ❌ NO | Muestra solo lista de resultados, no documentos |
| 7 | **API REST interna** | ❌ NO | Radware bloquea acceso directo |
| 8 | **CSRF / ViewState** | ❌ N/A | Sitio publico, migrado de JSF |

### 2.1 Error critico: Radware bloquea JS al conectar debugger a pagina ya cargada

Cuando conectas Selenium a un Chrome que **ya tiene** una pagina Radware cargada (via `--remote-debugging-port=9225`), Radware intercepta la pagina con un frame sandbox sin contexto de ejecucion. **TODO JavaScript falla** — no solo `execute_script()`, sino tambien `current_url`, `window_handles`, y `window.open()`.

Error tipico:
```
selenium.common.exceptions.TimeoutException: Message: timeout
from no such execution context: frame does not have execution context
```

**Que funciona y que no bajo esta condicion (Selenium vanilla):**

| Operacion | Funciona? |
|---|---|
| `save_screenshot()` | ✅ SI |
| `quit()` | ✅ SI |
| `driver.execute_script()` | ❌ NO |
| `driver.current_url` | ❌ NO |
| `driver.window_handles` | ❌ NO |
| `window.open()` via JS | ❌ NO |
| DevTools Protocol HTTP POST (/json) | ❌ NO (json decode fail) |

#### CDP bypass: cuando Selenium falla pero CDP funciona

Aunque `execute_script()` falle, **los CDP commands de bajo nivel funcionan** usando `page_load_strategy='none'` + `execute_cdp_cmd()`.

**Configuracion necesaria al conectar:**
```python
options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9225")
options.page_load_strategy = 'none'  # clave: no esperar a que el frame cargue
driver = webdriver.Chrome(options=options)
time.sleep(5)  # dar tiempo a que CDP se estabilice
```

**Comandos CDP que funcionan bajo Radware:**
```python
# 1. Obtener HTML completo
result = driver.execute_cdp_cmd("Runtime.evaluate", {
    "expression": "document.documentElement.outerHTML",
    "returnByValue": True, "awaitPromise": True
})
html = result.get("result", {}).get("value", "")

# 2. Extraer nids/documentos via JS
result = driver.execute_cdp_cmd("Runtime.evaluate", {
    "expression": """
        JSON.stringify(
            Array.from(document.querySelectorAll('a')).filter(a => a.href && a.href.includes('nid=')).map(a => ({
                nid: a.href.split('nid=')[1].split('&')[0],
                text: a.textContent.trim().substring(0, 100)
            }))
        )
    """,
    "returnByValue": True, "awaitPromise": True
})
docs = json.loads(result.get("result", {}).get("value", "[]"))

# 3. Obtener cookies de la sesion
result = driver.execute_cdp_cmd("Network.getAllCookies", {})
cookies = {c['name']: c['value'] for c in result.get("cookies", [])}
```

**Flujo completo de descarga con Chrome del usuario en detalleform.html:**
1. Conectar con `page_load_strategy='none'`
2. `time.sleep(8)` para que CDP se estabilice
3. Extraer nids via `Runtime.evaluate`
4. Obtener cookies via `Network.getAllCookies`
5. Descargar cada documento con `requests.get(url, cookies=cookies, headers=headers)` usando:
   - User-Agent real del navegador
   - Referer: `https://cej.pj.gob.pe/cej/forms/detalleform.html`
   - Accept-Language: `es-PE,es;q=0.9`
6. Si `requests` devuelve Radware block (~15KB HTML con "Radware Captcha Page"):
   - Navegar con `driver.get(url)`, esperar 5s, re-obtener cookies, reintentar

### 2.2 Comportamiento real: los links Descargar SIRVEN PDFs (con sesion viva)

Cuando se usa **el Chrome del usuario con sesion CEJ viva**, los enlaces `documentoD.html?nid=...` **devuelven PDFs reales**, no HTML. Probado con 18/18 documentos.

**Cuando se obtiene HTML (~15KB):**
- Si contiene "Radware Captcha Page" → Radware bloqueo. Solucion: navegar con `driver.get(url)` primero, refrescar cookies, reintentar.
- Si es pagina CEJ normal → sesion expiro. El usuario debe recargar.

**Cuando NO se tiene sesion viva** (undetected_chromedriver con perfil nuevo):
- Requests a `documentoD.html` son bloqueados (~15KB HTML con captcha)
- Solucion: usar el Chrome del usuario (sesion establecida) o mantener perfil persistente

### 2.2.1 Clasificacion de documentos para descarga selectiva

**Indicadores de CEDULA DE NOTIFICACION (saltar):**
- Contexto contiene "Tipo de Notificacion: Pta. Cedula" o "Cedula"
- Item muestra destinatario + anexo(s)
- Aparece "NOTIFICACION" con numero de envio

**Indicadores de RESOLUCION/AUTO/SENTENCIA (descargar):**
- Tipo de acto: "SENTENCIA", "SENTENCIA DE VISTA", "AUTO", "AUTO FINAL"
- Sumilla con "CONFIRMARON", "DECLARA IMPROCEDENTE", "FUNDADA"
- Tiene folios (ej. "Folios: 9")

**Regla practica:**
```python
EXCLUDE_KEYWORDS = ["CEDULA", "CÉDULA", "NOTIFICACION", "NOTIFICACIÓN", "Pta. Cedula"]
REAL_RESOLUTION_KEYWORDS = ["SENTENCIA", "AUTO FINAL", "AUTO:"]
def es_importante(contexto):
    ctx_upper = (contexto or "").upper()
    if any(kw in ctx_upper for kw in EXCLUDE_KEYWORDS):
        return False
    if any(kw in ctx_upper for kw in REAL_RESOLUTION_KEYWORDS):
        return True
    return False
```

**Nota:** NO todos los items del seguimiento tienen boton "Descargar". Algunas resoluciones aparecen en el texto pero no tienen enlace.

**Clasificacion POST-descarga por PDF es mas confiable.** Ver `references/clasificacion-documentos.md`.

---

## 3. FLUJO OPTIMIZADO

### 3.0 Regla critica: campo `parte` es OBLIGATORIO

El formulario de busqueda por codigo tiene **8 campos**, no 7. El campo `parte` (nombre del demandante/demandado) es **obligatorio**. Sin el nombre exacto de la parte, el captcha correcto no es suficiente.

**Como obtener el nombre de la parte:**
- Columna `PARTE PROCESAL` en el Excel de entrada
- Formato tipico: "APELLIDO1 APELLIDO2 NOMBRE1 NOMBRE2" o "RAZON SOCIAL"

### 3.1 Setup
```bash
google-chrome --remote-debugging-port=9225 \
  --user-data-dir=/home/usuario/.chrome_cej \
  --no-first-run --no-default-browser-check \
  "https://cej.pj.gob.pe/cej/forms/busquedaform.html"
```

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9225")
driver = webdriver.Chrome(options=options)
```

### 3.2 Resolucion de captcha (combo optimizado)
```python
import ddddocr, requests, base64, time
ocr = ddddocr.DdddOcr()
API_KEY = "1e563a7dfcc437d276d896fdebf88497"

def resolver_captcha(imagen_bytes):
    resultado = ocr.classification(imagen_bytes)
    if resultado:
        resultado = resultado.strip().upper()
        if len(resultado) == 4 and resultado.isalnum():
            return resultado, 'ocr'
    # fallback 2Captcha...
    ...

def extraer_captcha(driver):
    b64 = driver.execute_script("""
        var img = document.getElementById('captcha_image');
        if (!img) return null;
        var c = document.createElement('canvas');
        c.width = img.naturalWidth; c.height = img.naturalHeight;
        c.getContext('2d').drawImage(img, 0, 0);
        return c.toDataURL('image/jpeg', 0.85).split(',')[1];
    """)
    return base64.b64decode(b64) if b64 else None
```

### 3.3 Filtro de documentos por keyword
```python
KEYWORDS = [
    'SENTENCIA', 'SENTENCIA DE VISTA', 'RESOLUCION', 'RESOLUCIÓN',
    'AUTO FINAL', 'FUNDADA', 'INFUNDADA', 'IMPROCEDENTE', 'INADMISIBLE',
    'SE ADMITE', 'ARCHIVO DEFINITIVO', 'CONCLUSIÓN', 'CONCLUSION',
    'CONSENTIDA', 'DEMANDA',
]
```

### 3.4 Descarga paralela
```python
from concurrent.futures import ThreadPoolExecutor
def descargar_todos(docs_info, exp):
    with ThreadPoolExecutor(max_workers=5) as ex:
        futuros = [ex.submit(descargar_individual, d['nid'], exp, i)
                   for i, d in enumerate(docs_info, 1)]
        ...
```

---

## 4. ANTI-BLOQUEO (reglas estrictas)

1. **Chrome real siempre** con perfil persistente (`~/.chrome_cej`). Nunca headless.
2. **Misma IP** toda la sesion (VPN MX si es necesario, NL bloqueado).
3. **Un request a la vez en navegacion** — sleeps 5-15s entre acciones.
4. **Descarga paralela SI, navegacion paralela NO** — solo paralelizar el GET a documentoD.html.
5. **Multi-pestana: MAX 1** — solo una ventana Chrome sobrevive.
6. **Rotar sesion cada ~15 min** (timeout de sesion del sitio).
7. **SIEMPRE refrescar pagina si aparece "fin de espera"** (sesion expirada).
8. **NO conectar Selenium a Chrome con pagina Radware ya interceptada.** Usar `page_load_strategy='none'` + `execute_cdp_cmd('Runtime.evaluate', ...)` para extraer datos via CDP.
9. **No confiar en requests.get() para documentoD.html incluso con cookies validas** — Radware puede bloquear. Si recibes ~15KB HTML con "Radware Captcha Page", navegar con `driver.get(url)` primero y re-obtener cookies.
10. **page_load_strategy='none' es el modo correcto** para conectar a un Chrome que ya tiene una pagina Radware cargada.
11. **CDP bypass de Radware: funcionamiento comprobado** — `Runtime.evaluate`, `Network.getAllCookies`, `Page.captureSnapshot`, `DOM.getDocument` funcionan incluso cuando `execute_script()` falla.
12. **Compensacion undetected_chromedriver vs remote-debugging:**

    | Aspecto | undetected_chromedriver | remote-debugging (Chrome usuario) |
    |---|---|---|
    | Captcha ddddocr | ✅ Funciona | ❌ No aplica |
    | Descarga via requests | ❌ Radware bloquea | ✅ Funciona si sesion viva |
    | Descarga via driver.get() | ❌ Radware bloquea | ✅ Funciona con CDP |

    **Conclusion para automatizacion completa:**
    1. Usuario navega manualmente hasta `detalleform.html`
    2. Script se conecta via remote-debugging + CDP, extrae nids y cookies
    3. Descarga TODOS los documentos (ThreadPoolExecutor, 5 workers)
    4. Clasifica post-descarga por contenido del PDF (pymupdf)
    5. Mover descartados a subcarpeta "cedulas/"

13. **dddddocr funciona consistentemente** en CEJ captcha si se toman 2-3s de carga y se recarga la imagen 1 vez.
14. **Captcha "falso" en perfil Chrome nuevo.** Recargar la imagen 2-3 veces ANTES de resolver, forzando timestamp en la URL:
    ```python
    for _ in range(3):
        driver.find_element(By.CSS_SELECTOR, '#btnReload').click()
        time.sleep(3)
        driver.execute_script(
            "var img = document.getElementById('captcha_image');"
            "if(img) img.src = img.src.split('?')[0] + '?t=' + Date.now();"
        )
        time.sleep(2)
    ```
15. **Clasificacion POST-descarga es la unica estrategia confiable.** Ver `references/clasificacion-documentos.md`.

## 5. PAGINACION DEL SEGUIMIENTO (pendiente de implementar)

La pagina `detalleform.html` tiene **3 paginas** de seguimiento. Los enlaces son `<a>` dentro de `<li class="pointer-cursor">` activados via jQuery. El script actual solo captura la pagina 1.

**Pendiente:** Loop que clickee cada pagina, espere 3-4s, y extraiga los nids. Combinar todos y descargar en paralelo al final. Ver `references/paginacion-seguimiento.md`.

## 6. SUPPORT FILES

| File | Descripcion |
|---|---|
| `scripts/cej_scraper_optimizado.py` | Script completo listo para ejecutar (spider Scrapy) |
| `scripts/cej_scraper_test.py` | Script de prueba basico |
| `scripts/download_cej_important.py` | Script autonomo para descargar SOLO documentos con valor legal |
| `scripts/lanzar_chromes_linux.sh` | Lanza 2 Chromes independientes (puertos 9222/9223) para paralelismo en Ubuntu |
| `references/document-types.md` | Tipos de documentos y limitaciones |
| `references/paginacion-seguimiento.md` | Paginacion del seguimiento (3 paginas) |
| `references/cej-technical-reference.md` | Referencia tecnica del sitio |
| `references/auditoria-seguridad.md` | Detalle de hallazgos de seguridad |
| `references/descarga-sesion-viva.md` | Flujo CDP para descargar desde Chrome del usuario (Radware bypass comprobado) |
| `references/clasificacion-documentos.md` | Como distinguir resoluciones reales de cedulas de notificacion (post-descarga por PDF) |
| `references/integracion-kgraph.md` | Integracion con KGraphResolucionesV3 (formato rag_listo_batch_*.json) |
| `references/historial-depuracion.md` | Historial detallado de migracion Ubuntu y debugging (referencia) |
| `references/radware-cve-analysis.md` | Analisis de CVE-2024-56523/56524 (Radware WAF) — no aplican a nuestro caso |
| `references/radware-cve-research.md` | Investigacion de CVE-2024-56523/56524 — confirmados reales pero no aplican |

## 7. PENDIENTE: PAGINACION COMPLETA

1. Hacer click en pagina "2" (via `By.LINK_TEXT, "2"`)
2. Esperar 3-4s a que cargue
3. Extraer nids
4. Click en pagina "3", repetir
5. Combinar todos los nids y descargar en paralelo

Ver `references/paginacion-seguimiento.md` para implementacion detallada.

## Dependencias
```bash
pip install ddddocr opencv-python-headless Pillow onnxruntime \
            selenium requests 2captcha-python
```
