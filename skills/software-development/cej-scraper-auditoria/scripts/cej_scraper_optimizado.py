#!/usr/bin/env python3
"""
cej_scraper_optimizado.py - Scraper optimizado para CEJ
Caracteristicas:
  - ddddocr + 2Captcha combo para captcha
  - Filtro por keywords: solo documentos valiosos
  - Descarga paralela (5 workers)
  - Anti-bloqueo: sleeps conservadores, Chrome real

Uso:
  1. Tener Chrome abierto: google-chrome --remote-debugging-port=9225 ...
  2. source ~/cej-scraper/bin/activate
  3. python3 cej_scraper_optimizado.py

CONOCIDO: Los documentos descargados via documentoD.html?nid= son
NOTIFICACIONES (HTML), NO resoluciones PDF. Para PDFs reales hace
falta investigar el flujo alternativo.
"""

import os, sys, time, base64, csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── CONFIG ────────────────────────────────────────────────
DEBUG_PORT = 9225
API_KEY = "1e563a7dfcc437d276d896fdebf88497"
SLEEP_NAV = 5
SLEEP_FORM = 3
SLEEP_EXP = 20

KEYWORDS = [
    'SENTENCIA', 'SENTENCIA DE VISTA',
    'RESOLUCION', 'RESOLUCIÓN',
    'AUTO FINAL',
    'FUNDADA', 'INFUNDADA', 'IMPROCEDENTE', 'INADMISIBLE',
    'SE ADMITE', 'ARCHIVO DEFINITIVO',
    'CONCLUSIÓN', 'CONCLUSION', 'CONSENTIDA', 'DEMANDA',
]

EXPEDIENTES = [
    ("00060-2021-0-1801-JR-DC-03", "RODRIGUEZ CRUZ JUAN CARLOS"),
]

OUTPUT_DIR = "/home/usuario/cej_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/documents", exist_ok=True)

# ─── CHROME ────────────────────────────────────────────────
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
driver = webdriver.Chrome(options=options)
print(f"[*] Chrome OK. URL: {driver.current_url[:80]}")

# ─── CAPTCHA ────────────────────────────────────────────────
import ddddocr, requests
ocr = ddddocr.DdddOcr()

def resolver_captcha(imagen_bytes):
    resultado = ocr.classification(imagen_bytes)
    if resultado:
        resultado = resultado.strip().upper()
        if len(resultado) == 4 and resultado.isalnum():
            print(f"  [OCR] Captcha: {resultado}")
            return resultado, 'ocr'
    print(f"  [OCR] Fallo, usando 2Captcha...")
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

def extraer_captcha():
    b64 = driver.execute_script("""
        var img = document.getElementById('captcha_image');
        if (!img) return null;
        var c = document.createElement('canvas');
        c.width = img.naturalWidth; c.height = img.naturalHeight;
        c.getContext('2d').drawImage(img, 0, 0);
        return c.toDataURL('image/jpeg', 0.85).split(',')[1];
    """)
    return base64.b64decode(b64) if b64 else None

# ─── FILTRO ────────────────────────────────────────────────
def es_valioso(texto):
    texto_up = texto.upper()
    for kw in KEYWORDS:
        if kw in texto_up:
            return True
    return False

# ─── DESCARGA ──────────────────────────────────────────────
def descargar_doc(nid, exp, idx, valioso):
    if not valioso:
        return (idx, 'SKIP', 0)
    r = requests.get(
        f"https://cej.pj.gob.pe/cej/forms/documentoD.html?nid={nid}", timeout=30)
    ext = '.pdf' if r.content[:4] == b'%PDF' else '.html'
    tipo = 'PDF' if ext == '.pdf' else 'HTML'
    fname = f"{exp}_doc_{idx:02d}{ext}"
    fpath = f"{OUTPUT_DIR}/documents/{fname}"
    with open(fpath, 'wb') as f: f.write(r.content)
    return (idx, tipo, len(r.content))

def descargar_todos(docs_info, exp):
    if not docs_info:
        return
    with ThreadPoolExecutor(max_workers=5) as ex:
        futuros = []
        for i, doc in enumerate(docs_info, 1):
            valioso = es_valioso(doc.get('texto', ''))
            futuros.append(ex.submit(descargar_doc, doc['nid'], exp, i, valioso))
        for f in as_completed(futuros):
            idx, tipo, size = f.result()
            if tipo == 'SKIP':
                print(f"    [SKIP] Doc {idx}: no valioso")
            else:
                print(f"    [OK] Doc {idx}: {tipo} ({size} bytes)")

def extraer_docs_con_texto():
    return driver.execute_script("""
        const results = [];
        document.querySelectorAll('a[href*="documentoD"]').forEach(a => {
            const ctx = a.closest('.row, div[id], .item, [class*="divResol"]') || a.parentElement;
            results.push({
                nid: a.href.split('nid=')[-1],
                texto: ctx ? ctx.textContent.trim().substring(0, 300) : ''
            });
        });
        return results;
    """)

# ─── EXTRACCION DATOS ─────────────────────────────────────
def extraer_datos():
    from selenium.webdriver.common.by import By
    texto = driver.find_element(By.TAG_NAME, "body").text
    datos = {}
    secciones = texto.split('PARTES PROCESALES')
    if secciones:
        for linea in secciones[0].split('\n'):
            linea = linea.strip()
            if ':' in linea and not linea.startswith('http'):
                k, v = linea.split(':', 1)
                datos[k.strip()] = v.strip()
    return datos

def guardar_csv(datos, exp):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = f"{OUTPUT_DIR}/cej_{exp.replace('-','_')}_{ts}.csv"
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Campo', 'Valor'])
        for k, v in datos.items():
            w.writerow([k, str(v)[:200] if v else ''])
    return path

# ─── PROCESAR ──────────────────────────────────────────────
def procesar(exp, parte):
    partes = exp.split('-')
    if len(partes) != 7:
        print(f"[!] Formato invalido: {exp}")
        return

    print(f"\n{'='*60}")
    print(f"[{exp}] Parte: {parte}")

    driver.get("https://cej.pj.gob.pe/cej/forms/busquedaform.html")
    time.sleep(SLEEP_NAV)
    if 'perfdrive' in driver.current_url:
        print("[!] RADWARE - resuelve captcha manual")
        return

    driver.execute_script('document.querySelector("a[href=\'#tabs-2\']").click()')
    time.sleep(SLEEP_FORM)

    campos = [("cod_expediente",partes[0]),("cod_anio",partes[1]),
              ("cod_incidente",partes[2]),("cod_distprov",partes[3]),
              ("cod_organo",partes[4]),("cod_especialidad",partes[5]),
              ("cod_instancia",partes[6])]
    for fid, val in campos:
        driver.execute_script(f'document.getElementById("{fid}").value = "{val}";')
    driver.execute_script(f'document.getElementById("parte").value = "{parte}";')
    time.sleep(SLEEP_FORM)

    driver.find_element("id", "consultarExpedientes").click()
    time.sleep(SLEEP_NAV)

    for intento in range(5):
        captcha = extraer_captcha()
        if not captcha:
            break
        codigo, fuente = resolver_captcha(captcha)
        if not codigo:
            break
        driver.execute_script(f'document.getElementById("codigoCaptcha").value = "{codigo}";')
        time.sleep(1)
        driver.find_element("id", "consultarExpedientes").click()
        time.sleep(SLEEP_NAV)
        if 'detalleform' in driver.current_url:
            print(f"[+] Captcha OK intento {intento+1}")
            time.sleep(3)
            break
        if extraer_captcha() is None and 'busquedacodform' in driver.current_url:
            print("[+] Sin captcha - en resultados")
            time.sleep(3)
            break

    if 'busquedacodform' in driver.current_url:
        try:
            driver.execute_script('document.querySelector("form[action=\'detalleform.html\'] button, a[href*=\'detalle\']").click()')
            time.sleep(SLEEP_NAV)
        except:
            pass

    if 'detalleform' in driver.current_url:
        print("[*] Extrayendo datos...")
        datos = extraer_datos()
        csv_path = guardar_csv(datos, exp)
        print(f"    CSV: {csv_path}")

        print("[*] Extrayendo documentos...")
        docs = extraer_docs_con_texto()
        valiosos = [d for d in docs if es_valioso(d.get('texto',''))]
        print(f"    Docs: {len(docs)}, Valiosos: {len(valiosos)}/{len(docs)}")

        print("[*] Descargando...")
        descargar_todos(docs, exp.replace('-', '_'))
        print(f"[✓] {exp}")
    else:
        print(f"[!] No detalle. URL: {driver.current_url}")

# ─── MAIN ──────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"[*] Inicio: {datetime.now().strftime('%H:%M:%S')}")
    print(f"[*] Output: {OUTPUT_DIR}")
    print(f"[*] Exp: {len(EXPEDIENTES)}")
    for exp, parte in EXPEDIENTES:
        procesar(exp, parte)
        time.sleep(SLEEP_EXP)
    print(f"[*] Fin: {datetime.now().strftime('%H:%M:%S')}")
    print("[*] Done.")
