# Descarga desde sesion CEJ viva (con Chrome del usuario)

## Contexto

Cuando el usuario ya tiene el Chrome abierto en `detalleform.html` con los botones rojos visibles (18 documentos del expediente), Radware ya bloquea el frame de ejecucion. No se puede usar `execute_script()` ni `current_url`. Pero los CDP commands funcionan.

## Flujo exacto probado (funciona 18/18 documentos)

### Paso 1: Conectar al Chrome remoto

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9225")
options.page_load_strategy = 'none'  # CLAVE: no esperar a que el frame cargue
driver = webdriver.Chrome(options=options)
time.sleep(5)  # estabilizar conexion CDP
```

### Paso 2: Extraer nids via CDP

```python
result = driver.execute_cdp_cmd("Runtime.evaluate", {
    "expression": """
        JSON.stringify(
            Array.from(document.querySelectorAll('a')).filter(a => a.href && a.href.includes('nid=')).map(a => {
                const nid = a.href.split('nid=')[1].split('&')[0];
                let ctx = a;
                let desc = '';
                for (let i = 0; i < 15; i++) {
                    ctx = ctx.parentElement;
                    if (!ctx) break;
                    const txt = (ctx.textContent || '').trim();
                    if (txt.length > 80) {
                        desc = txt.substring(0, 500);
                        break;
                    }
                }
                return {nid, desc};
            })
        )
    """,
    "returnByValue": True,
    "awaitPromise": True
})
docs_json = result.get("result", {}).get("value", "[]")
docs = json.loads(docs_json)  # 18 documentos
```

### Paso 3: Obtener cookies via CDP

```python
result = driver.execute_cdp_cmd("Network.getAllCookies", {})
cookies = {c['name']: c['value'] for c in result.get("cookies", [])}
```

### Paso 4: Descargar cada documento

```python
import requests as req

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.7827.53 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-PE,es;q=0.9,en;q=0.8',
    'Referer': 'https://cej.pj.gob.pe/cej/forms/detalleform.html',
}

for doc in docs:
    nid = doc['nid']
    url = f"https://cej.pj.gob.pe/cej/forms/documentoD.html?nid={nid}"

    r = req.get(url, cookies=cookies, headers=headers, timeout=30)
    is_pdf = r.content[:4] == b'%PDF'

    # Si Radware bloquea, navegar con Selenium y refrescar cookies
    if not is_pdf and 'Radware Captcha Page' in r.text:
        driver.get(url)
        time.sleep(5)
        result = driver.execute_cdp_cmd("Network.getAllCookies", {})
        cookies = {c['name']: c['value'] for c in result.get("cookies", [])}
        r = req.get(url, cookies=cookies, headers=headers, timeout=30)
        is_pdf = r.content[:4] == b'%PDF'

    if is_pdf:
        with open(f"/ruta/{nid[:8]}.pdf", 'wb') as f:
            f.write(r.content)
```

## Notas importantes

1. **Los nids cambian cada vez** que se carga `detalleform.html`. No son estables entre sesiones.
2. **page_load_strategy='none'** es esencial — sin esto, Selenium espera infinitamente al frame Radware y timeout.
3. **Runtime.evaluate con awaitPromise=True** es necesario para que JS asincrono se complete.
4. Las cookies obtenidas via CDP son las mismas que `driver.get_cookies()`, pero CDP no se bloquea por el frame.
5. Si un documento individual esta bloqueado por Radware (~15KB HTML con titulo "Radware Captcha Page"), navegar con `driver.get(url)` + refrescar cookies suele resolverlo.
6. Este metodo **no requiere undetected_chromedriver** — funciona con Selenium vanilla conectado a un Chrome ya abierto por el usuario.

## Captcha en sesiones frescas

Cuando se usa `undetected_chromedriver` con un perfil nuevo (sin sesion CEJ previa), el captcha del CEJ falla consistentemente — siempre devuelve el mismo texto ("FH6w") porque la imagen real no se ha cargado. La solucion es:
- Usar el Chrome que el usuario ya tiene abierto (sesion establecida)
- O forzar recarga del captcha 2-3 veces antes de resolver
- O usar 2Captcha como fallback
