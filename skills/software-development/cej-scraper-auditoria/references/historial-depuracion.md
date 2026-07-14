# Historial de depuración y migración Ubuntu (2026)

> Este archivo contiene el historial detallado de debugging, migración de Windows a Ubuntu,
> y pruebas realizadas. Se mantiene como referencia histórica; el SKILL.md principal
> contiene solo la información operativa esencial.

---

## 8. MIGRACION A UBUNTU NATIVO (2026)

El proyecto original se creó en Windows 10 y requiere ajustes para correr en Ubuntu.

### 8.1 ChromeDriver version pinning

Chrome 149 instalado, pero `undetected_chromedriver` descarga ChromeDriver 150 → `SessionNotCreatedException: This version of ChromeDriver only supports Chrome version 150`.

**Solución:** Forzar `version_main=149` en cada creación de Chrome:
```python
from undetected_chromedriver import Chrome, ChromeOptions
opts = ChromeOptions()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
driver = Chrome(options=opts, version_main=149)  # ← clave
```

### 8.2 distutils fallo

En Python 3.12, `distutils` fue eliminado. `undetected_chromedriver` lo importa:
```
ModuleNotFoundError: No module named 'distutils'
```
**Solución:** `pip install setuptools` (provee el submodulo `_distutils_hack`).

### 8.3 Entry points para Ubuntu

Los archivos `run_A.py`, `run_B.py`, `run_opt.py` apuntan a `~/chromium/chrome-linux64/chrome`. En Ubuntu el Chrome está en `/usr/bin/google-chrome`.

```python
# run_A_linux.py
os.environ['CHROME_BINARY_PATH'] = '/usr/bin/google-chrome'
os.environ['PJ_INPUT_FILE'] = 'input/slice_LA_DC_A.xlsx'
os.environ['PJ_SPIDER_ID'] = 'A'
```

Los entry points Windows (`run_A_win.py`, `run_A_win_remote.py`, `run_B_win_remote.py`) con rutas `C:\\Program Files\\...` y backslashes se descartan en Ubuntu — no borrar, crear variantes `run_A_linux.py`.

### 8.4 Navegación resultados → detalle (form submit)

El spider original usa JavaScript para buscar un link con `detalleform` en href y hacer click:
```python
driver.execute_script("""
    var links = document.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
        if (links[i].href && links[i].href.includes('detalleform')) {
            links[i].click(); return;
        }
    }
""")
```

**Esto NO funciona en la versión actual del CEJ.** No hay link directo a detalleform. En su lugar, hay un formulario con `action=detalleform.html`:

```python
# CORRECTO: submit del formulario
forms = driver.find_elements(By.TAG_NAME, 'form')
for f in forms:
    action = f.get_attribute('action') or ''
    if 'detalleform' in action:
        driver.execute_script("arguments[0].submit();", f)
        sleep(5)
        break
```

### 8.5 Captcha refresh — página completa vs btnReload

El botón `#btnReload` del CEJ **no refresca consistentemente** la imagen del captcha. A veces cambia el src pero el canvas captura la imagen anterior, resultando en el mismo código OCR repetido.

**Estrategia probada:** recargar la página completa del CEJ y re-llenar los campos:
```python
for intento in range(8):
    codigo = resolver_captcha(driver)
    if codigo is None: break  # sin captcha
    
    if len(codigo) < 3:
        # Reload completo de la pagina CEJ
        driver.get(CEJ_URL); sleep(6)
        driver.execute_script('document.querySelector("a[href=\'#tabs-2\']").click()'); sleep(3)
        llenar_campos(parts, parte)
        continue
    
    driver.execute_script(f'document.getElementById("codigoCaptcha").value="{codigo}";')
    sleep(1)
    driver.find_element(By.CSS_SELECTOR, '#consultarExpedientes').click()
    sleep(8)
    if 'detalleform' in driver.current_url: break
    if 'busquedacodform' in driver.current_url: break
```

### 8.6 ddddocr en Ubuntu — tasa de acierto y códigos cortos

En Ubuntu + Chrome 149, `ddddocr` a veces retorna códigos de 3 caracteres (ej. "1MB", "8X5") para un captcha de 4 caracteres. El CEJ rechaza estos códigos inválidos.

**Posibles causas:**
- La imagen del captcha del CEJ cambió (nuevo fondo/fuente) desde que se entrenó ddddocr
- El canvas resize (img.width vs naturalWidth) pierde resolución
- El captcha a veces no carga completamente antes de capturarlo

**Mitigación:**
1. Validar que el código tenga al menos 3 caracteres alfanuméricos
2. Reintentar con refresco de página completa (no solo btnReload)
3. Tener 2Captcha como fallback (la key `1e563a7dfcc437d276d896fdebf88497` — verificar créditos)
4. Máximo 8-10 intentos; después de 3 refrescos de página, pasar al siguiente expediente

### 8.7 documentD.html — descarga con requests.get

**UPDATE 28-Jun-2026: FUNCIONA con cookies del driver + headers completos.** El error "Acceso denegado" inicial se debia a que faltaban headers HTTP especificos y las cookies debian extraerse DESPUES de navegar a `detalleform.html` (no desde `busquedaform`).

**Requisitos exactos (probado con 6 PDFs descargados):**

1. Cookies extraidas DESPUES de llegar a `detalleform.html`:
   ```python
   cookies = {c['name']: c['value'] for c in driver.get_cookies()}
   ```

2. Headers HTTP IDENTICOS a Chrome (copia exacta abajo). Especialmente importantes:
   - `referer`: exactamente `https://cej.pj.gob.pe/cej/forms/detalleform.html`
   - Todos los `sec-ch-ua*` headers
   - `sec-fetch-dest: document`, `sec-fetch-mode: navigate`
   - `upgrade-insecure-requests: 1`

3. Deteccion de PDF:
   ```python
   is_pdf = b'%PDF' in content[:100] or content[:4] == b'%PDF'
   ```

Headers necesarios (copia exacta de Chrome 149 Linux):
```python
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es-PE,es;q=0.9,en;q=0.8',
    'referer': 'https://cej.pj.gob.pe/cej/forms/detalleform.html',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin', 'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
}
```

**Patron exacto que funciona (del spider Scrapy):**
```python
# 1. Driver navega a detalleform y extrae cookies DESDE ALLI
self.driver.get(self.base_url)
sleep(8)
# ... resolver captcha, navegar a resultados, submit form a detalleform ...
cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}

# 2. requests.get con esas cookies
resp = requests.get(url, cookies=cookies, headers=headers, timeout=30)

# 3. Detectar PDF (bytes, no texto)
is_pdf = b'%PDF' in content[:100] or content[:4] == b'%PDF'
```

Resultados reales: 6 PDFs descargados de 4 expedientes (hasta 619KB c/u) usando el spider Scrapy. Deteccion: `b'%PDF' in content[:100]`.

### 8.8 Scrapy project structure fix para repos local (no pip package)

El proyecto original en Windows tenia los archivos Scrapy dentro de `poder_judicial_results/`. En el repo de GitHub los archivos estan sueltos en la raiz. Scrapy busca `poder_judicial_results.settings`.

**Fixes en Ubuntu:**
1. **scrapy.cfg:** `default = poder_judicial_results.settings` → `default = settings`
2. **settings.py:** `SPIDER_MODULES = ["poder_judicial_results.spiders"]` → `SPIDER_MODULES = ["spiders"]`
3. **Entry points:** `sys.path.insert(0, parent_dir) + os.chdir(project_dir)` antes de `cmdline.execute()`

### 8.10 Excel header detection — patron ETTDA

Headers en fila 3 (no fila 1): Fila 1="JAV", Fila 2=vacia, Fila 3=headers reales. Detectar con loop hasta 10 filas buscando 'EXPEDIENTE' o >=3 columnas de texto sin formato de expediente (`'+'-' in v and v.count('-') >= 3`).

**Deduplicación:** ETTDA tiene ~78K filas pero ~42K expedientes únicos. El spider toma solo la primera ocurrencia de cada numero de expediente (primer segmento antes de `-`).

### 8.11 Entry points nuevos

```python
# run_ettda_linux.py
os.environ['CHROME_BINARY_PATH'] = '/usr/bin/google-chrome'
os.environ['PJ_INPUT_FILE'] = 'Expediente 015433-2026-ETTDA-LIM.xlsx'
os.environ['PJ_SPIDER_ID'] = 'ETTDA'

# run_A_parallel.py (remote debugging puerto 9222)
os.environ['REMOTE_DEBUGGING_PORT'] = '9222'
os.environ['PJ_SLICE_OFFSET'] = '0'; os.environ['PJ_SLICE_LIMIT'] = '5'

# run_B_parallel.py (remote debugging puerto 9223)
os.environ['REMOTE_DEBUGGING_PORT'] = '9223'
os.environ['PJ_SLICE_OFFSET'] = '5'; os.environ['PJ_SLICE_LIMIT'] = '5'
```

### 8.11 Paralelismo

| Driver | 2 instancias simultaneas | Resultado |
|---|---|---|
| `undetected_chromedriver` | ❌ | Race condition: ambos spiders parchean el mismo binary de ChromeDriver → `ConnectionRefusedError` y `chrome_dead` para uno de ellos |
| **Selenium puro** (recomendado) | ✅ | **Comprobado 28-Jun-2026**: ambos spiders `finished`. Sin race condition porque no parchea el binary. |

**Con undetected_chromedriver:** No es suficiente usar perfiles separados (`CHROME_USER_DATA_DIR=tempfile.mkdtemp()`). El conflicto es a nivel del binary del ChromeDriver, no del perfil de Chrome. Tampoco funciona `UNDETECTED_CHROMEDRIVER_DIR` (undetected_chromedriver ignora esta variable).

**Con Selenium puro:** Cada spider usa el ChromeDriver del sistema (`which chromedriver` o el descargado por undetected_chromedriver) sin parchearlo. Concurrencia sin race condition. Usar `CHROME_USER_DATA_DIR` con directorios temporales (`tempfile.mkdtemp(prefix='cej_sel_A_')`) para perfiles separados.

### 8.12 Costos 2Captcha

| Concepto | Valor |
|---|---|
| Tipo | ImageToTextTask (el mas barato) |
| Precio | **$0.0002** por captcha (NO $0.01 — segun [tabla oficial](https://2captcha.com/loadbalance): $0.001 por cada 5 solicitudes) |
| Captchas por $1.99 | ~10,000 |
| Costo ETTDA completo (42K exps) | ~$8.50 |
| API key | `1e563a7dfcc437d276d896fdebf88497` ($1.99 al 28-Jun-2026, verificada con saldo via `getBalance` API) |

### 8.13 Resumen de cambios al spider para Ubuntu

| Elemento | Ruta en Ubuntu |
|---|---|
| Repositorio activo (GitHub) | `/media/usuario/ARCHVOS013/PyCode/cej-scraper/` |
| Virtualenv | `/media/usuario/ARCHVOS013/PyCode/cej-scraper/.venv/` |
| Chrome binario | `/usr/bin/google-chrome` (versión 149.0.7827.196) |
| ChromeDriver | Forzar `version_main=149` |
| Input Excel ETTDA | `Expediente 015433-2026-ETTDA-LIM.xlsx` (78,867 filas, 42,782 expedientes únicos, 8 especialidades) |
| Salida de prueba | `/media/usuario/ARCHVOS013/PyCode/cej-scraper/test_output/` |

### 8.14 Migracion a Selenium puro (reemplazo de undetected_chromedriver)

`undetected_chromedriver` fue reemplazado por **Selenium ChromeDriver estandar** con parches CDP anti-deteccion. Razones:

1. **Race condition con 2+ instancias** — undetected_chromedriver parchea UN solo binary en `~/.local/share/undetected_chromedriver/`. Cuando 2 spiders se inicializan casi simultáneamente, el binary se corrompe → `ConnectionRefusedError` y `chrome_dead`.
2. **Mayor consumo de memoria** — undetected_chromedriver ~740MB vs Selenium puro ~97MB.
3. **Dependencia extra** — undetected_chromedriver requiere `version_main` explicito y falla con `SessionNotCreatedException` si Chrome se actualiza.

**Cambio exacto en el spider:**
```python
# ANTES (undetected_chromedriver):
from undetected_chromedriver import Chrome, ChromeOptions
opts = ChromeOptions()
driver = Chrome(options=opts, version_main=149)

# DESPUES (Selenium puro):
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
opts = Options()
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=opts)
```

**Parche anti-deteccion CDP post-creacion (necesario):**
```python
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['es-PE','es','en']});
"""})
```

**Resultados:** `navigator.webdriver` retorna `None` (no detectable), CEJ sin Radware.

**Resultados de prueba con Selenium puro (28-Jun-2026):**

| Test | Spider A | Spider B |
|---|---|---|
| Single-instance (4 exps) | `finished` ✅, 6 PDFs | — |
| Paralelo (2 exps c/u) | `finished` ✅, 0 PDFs (solo seguimiento) | `finished` ✅, 1 PDF |
| Consumo memoria | ~97MB | ~97MB |
| ChromeDriver | Sistema (no parchea binary) | Sistema (no parchea binary) |

**IMPORTANTE:** Selenium puro NO parchea el ChromeDriver binary, permitiendo 2+ instancias simultáneas sin race conditions.

### 8.15 Playwright como alternativa standalone (NO compatible con Scrapy)

Playwright (v1.61.1, Chromium 148) es estable como script independiente pero **NO compatible con Scrapy** porque Scrapy corre sobre asyncio y Playwright Sync API requiere event loop propio.

**Error exacto:**
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

Playwright queda como alternativa para scripts standalone, NO para reemplazar undetected_chromedriver/Selenium dentro de Scrapy.

### 8.15 Resultados reales de prueba (28-Jun-2026)

**Prueba single-instance:** 4 expedientes del Excel ETTDA, spider Scrapy adaptado a Ubuntu, 2captcha como resolvedor:

| Expediente | Docs totales | PDFs descargados | Tamaño |
|---|---|---|---|
| 00020-2021-0-1801-JR-LA-07 (LA) | 12 | 4 | 427KB, 619KB, 177KB, 135KB |
| 00026-2021-0-1801-JR-LA-08 (LA) | 2 | 0 | (solo seguimiento, filtrados) |
| 00017-2021-0-1801-JR-FC-14 (FC) | 5 | 1 | 108KB |
| 00021-2021-0-1801-JR-FC-14 (FC) | 6 | 1 | 114KB |

Ritmo: ~1 expediente/minuto (navegacion + captcha 2captcha + descarga + sleeps anti-Radware).
Captcha: 100% acierto en 4/4 con 2captcha.
**Total confirmado: requests.get con headers completos + cookies del driver SÍ descarga PDFs.**

**Prueba paralela (2 spiders simultaneos):**
- Spider A (puerto 9222, remote debugging): `chrome_dead` — Chrome se cayó, procesó 3/5 expedientes.
- Spider B (puerto 9223, remote debugging): `finished` — 5/5 expedientes procesados, 1 PDF descargado.
- **Conclusión:** Modo remote debugging con Chromes pre-lanzados funciona pero es inestable. El spider individual (modo normal) es más confiable.

**Fallo típico del spider individual:** En 2 de 3 intentos de paralelismo, el primer spider lanzado falla con `chrome_dead` porque undetected_chromedriver parchea el ChromeDriver mientras el otro spider lo usa. El segundo spider siempre funciona.

### 8.16 Resumen de entry points creados

| Entry point | Modo | Slice | Proposito |
|---|---|---|---|
| `run_A.py` | Selenium puro (auto-launch) | slice_LA_DC_A.xlsx | Original adapted for Linux |
| `run_B.py` | Selenium puro (auto-launch) | slice_LA_DC_B.xlsx | Original adapted for Linux |
| `run_ettda_linux.py` | Selenium puro (auto-launch) | ETTDA completo | Produccion ETTDA |
| `run_A_parallel.py` | Selenium puro (auto-launch) | offset=0, limit=5 | Paralelo A |
| `run_B_parallel.py` | Selenium puro (auto-launch) | offset=5, limit=5 | Paralelo B |
| `run_test_linux.py` | Selenium puro (auto-launch) | prueba_3_exp.xlsx | Testing |

Los entry points Windows (`run_A_win.py`, `run_B_win_remote.py`, `run_autotest.py`) se conservan para referencia pero no se usan en Ubuntu.

**Modo normal (Selenium puro):** cada spider lanza su propio Chrome con perfil separado. No necesita remote debugging. Usar `CHROME_USER_DATA_DIR=tempfile.mkdtemp()` para perfiles temporales. **No necesita `version_main` ni undetected_chromedriver.**

**Modo remote debugging:** pre-lanzar Chrome con `--remote-debugging-port=9222`. Menos estable que modo normal. Usar solo cuando se requiera sesion manual persistente.

**Para paralelismo con Selenium puro:**
```bash
# Terminal 1
cd /media/usuario/ARCHVOS013/PyCode/cej-scraper && source .venv/bin/activate && python3 run_A_parallel.py
# Terminal 2 (8s despues)
cd /media/usuario/ARCHVOS013/PyCode/cej-scraper && source .venv/bin/activate && python3 run_B_parallel.py
```
Ambos spiders completan `finished` sin race conditions. Comprobado 28-Jun-2026.

### Estructura del repositorio activo

```
/media/usuario/ARCHVOS013/PyCode/cej-scraper/
├── spiders/poder_opt.py    # Spider Scrapy principal (937 lines, anti-Radware)
├── cej_scraper_optimizado.py  # Script standalone (ddddocr + 2Captcha)
├── test_captcha.py / v2.py    # Modulos de prueba de captcha
├── runner.py               # Orquestador con auto-reintento + rotacion 90min
├── run_A.py / run_B.py / run_opt.py  # Entry points por lote
├── input/                  # Excels con expedientes (slice_A.xlsx, etc.)
├── output/                 # CSVs resultado (~50 archivos)
├── details/                # Detalle de descargas
├── checkpoint_opt_*.json   # Checkpoints de progreso
├── settings.py             # Scrapy settings (AUTOTHROTTLE)
├── middlewares.py          # Middlewares anti-deteccion
└── requirements.txt        # scrapy, selenium, undetected-chromedriver, openpyxl, requests
```
