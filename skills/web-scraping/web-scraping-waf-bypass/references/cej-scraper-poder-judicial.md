# CEJ Scraper — Poder Judicial del Perú

Técnicas específicas para scrapear el CEJ (Consulta de Expedientes Judiciales).

## Anti-bot stack del CEJ

- **Radware / PerfDrive** — WAF que bloquea paralelismo, correlaciona TLS, y redirige a `validate.perfdrive.com`
- **Captcha alfanumérico** — 4 caracteres, en página de búsqueda
- **Hotlink protection** en `documentoD.html?nid=...` — rechaza requests sin los headers de navegador completos
- **JSESSIONID** — requiere mantener sesión para consultar

## Navegación con undetected_chromedriver

```python
from undetected_chromedriver import Chrome, ChromeOptions

opts = ChromeOptions()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--disable-blink-features=AutomationControlled')
driver = Chrome(options=opts, version_main=149)  # PIN version_main a la version local de Chrome!
```

**Pitfall**: `undetected_chromedriver` descarga el ChromeDriver más reciente automáticamente. Si tu Chrome local (ej. 149) no coincide con el último ChromeDriver (ej. 150), la sesión falla con `SessionNotCreatedException: This version of ChromeDriver only supports Chrome version 150`. Usar `version_main=<tu_version>` para forzar el driver correcto.

## Captcha: ddddocr + 2captcha fallback

El CEJ usa captcha alfanumérico de 4 caracteres. Estrategia de dos niveles:

1. **Primer intento**: `ddddocr` (local, gratis, ~30-50% de acierto)
2. **Fallback**: 2captcha API v2 (`ImageToTextTask`, ~$0.01/captcha)

```python
import ddddocr, base64, requests

ocr = ddddocr.DdddOcr()

# Extraer del DOM
captcha_b64 = driver.execute_script("""
    var img = document.getElementById('captcha_image');
    if (!img) return null;
    var c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    c.getContext('2d').drawImage(img, 0, 0);
    return c.toDataURL('image/jpeg', 0.85).split(',')[1];
""")

img_bytes = base64.b64decode(captcha_b64)
codigo = ocr.classification(img_bytes)

if not codigo or len(codigo.strip()) < 3:
    # Fallback a 2captcha
    resp = requests.post('https://api.2captcha.com/createTask', json={
        'clientKey': API_KEY,
        'task': {
            'type': 'ImageToTextTask',
            'body': captcha_b64,
            'numeric': 0, 'minLength': 4, 'maxLength': 4
        }
    }).json()
```

## PDF download — headers requeridos

`documentoD.html?nid=...` rechaza requests simples con "Acceso denegado". Requiere headers **idénticos a Chrome** incluyendo:

```python
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es-PE,es;q=0.9,en;q=0.8',
    'referer': 'https://cej.pj.gob.pe/cej/forms/detalleform.html',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36',
}
resp = requests.get(url, cookies=driver_cookies, headers=headers, timeout=30)
is_pdf = b'%PDF' in resp.content[:100]
```

## Navegación resultados → detalle

Cuando el captcha es exitoso, el CEJ redirige a `busquedacodform.html` (resultados). Para ir a detalle, **submitear el formulario** con `action=detalleform.html` — no buscar links:

```python
for f in driver.find_elements(By.TAG_NAME, 'form'):
    if 'detalleform' in (f.get_attribute('action') or ''):
        driver.execute_script("arguments[0].submit();", f)
        break
```

## Expansión de links de descarga y filtro por Sumilla

El HTML del CEJ tiene múltiples bloques `#divResol` (1 por seguimiento). Cada bloque contiene:
- `roptionss > Sumilla:` + `fleft > TEXTO DE SUMILLA`
- `dBotonDesc > a[title="Descargar"]`

Las Sumillas se extraen buscando hacia atrás desde el href del link. Una regex robusta:

```python
import re
before = html[max(0, html.find(href) - 3000):html.find(href)]
m = re.search(r'roptionss\s*>\s*Sumilla\s*:?\s*</div>.*?fleft\s*>\s*([^<]+)', before, re.DOTALL)
```

## Filtro de documentos valiosos

Solo descargar PDFs cuya Sumilla contenga: `SENTENCIA`, `RESOLUCION`, `AUTO FINAL`, `FUNDADA`, `INFUNDADA`, `IMPROCEDENTE`, `INADMISIBLE`, `SE ADMITE`, `ARCHIVO DEFINITIVO`, `CONCLUSIÓN`, `CONSENTIDA`.

## Excel input — detección de header row

Los Excels del CEJ pueden tener headers en filas no convencionales (ej. fila 3 en el archivo ETTDA, con "JAV" en fila 1). Detectar automáticamente:

```python
header_row = 1
for r in range(1, min(10, sheet.max_row + 1)):
    vals = [str(c.value or '') for c in sheet[r]]
    if any('EXPEDIENTE' in v.upper() for v in vals):
        header_row = r; break
    text_cols = [v for v in vals if v and not v.replace('.','').replace('-','').replace('/','').replace(' ','').isdigit() and len(v) > 2]
    if len(text_cols) >= 3:
        has_exp_format = sum(1 for v in vals if '-' in v and v.count('-') >= 3)
        if has_exp_format == 0:
            header_row = r; break
```

## Multi-spider para acelerar

Ejecutar 2 spiders con perfiles Chrome separados (puertos 9222 y 9223), cada uno con su slice del Excel. Radware limita ~1 request cada 10-15s por IP, pero dos sesiones Chrome distintas (cada una con su JSESSIONID) duplican el throughput.

No usar paralelismo dentro de un mismo spider (ThreadPoolExecutor) — Radware detecta ráfagas como DDoS.
