#!/usr/bin/env python3
"""
cej_scraper_test.py - Script de prueba para scraping del CEJ
Modo conservador: sleeps largos, un request a la vez, Chrome real + perfil persistente.

Uso:
  1. Tener Chrome abierto con remote debugging:
     google-chrome --remote-debugging-port=9225 \\
       --user-data-dir=/home/usuario/.chrome_cej \\
       --no-first-run --no-default-browser-check \\
       "https://cej.pj.gob.pe/cej/forms/busquedaform.html"
  2. source ~/cej-scraper/bin/activate
  3. python3 cej_scraper_test.py
"""

import os, sys, time, json, base64, csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# CONFIGURACION — EDITAR SEGUN CORRESPONDA
# ============================================================
DEBUG_PORT = 9225
API_KEY_2CAPTCHA = "1e563a7dfcc437d276d896fdebf88497"
EXPEDIENTE = "00060-2021-0-1801-JR-DC-03"
PARTE = "RODRIGUEZ CRUZ JUAN CARLOS"
OUTPUT_DIR = "/home/usuario/cej_prueba_output"

DOC_KEYWORDS = ['SENTENCIA', 'RESOLUCION', 'RESOLUCIÓN', 'AUTO FINAL',
                'FUNDADA', 'INFUNDADA', 'IMPROCEDENTE', 'SE ADMITE']

SLEEP_NAV = 5
SLEEP_FORM = 3
SLEEP_CAPTCHA = 2
SLEEP_EXP = 20

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/documents", exist_ok=True)

# ============================================================
# CONEXION A CHROME
# ============================================================
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
driver = webdriver.Chrome(options=options)
print(f"[*] Conectado a Chrome. URL: {driver.current_url[:80]}")

# ============================================================
# RESOLUCION DE CAPTCHA (ddddocr + 2Captcha fallback)
# ============================================================
import ddddocr
import requests

ocr = ddddocr.DdddOcr()

def resolver_captcha(imagen_bytes):
    resultado = ocr.classification(imagen_bytes)
    if resultado:
        resultado = resultado.strip().upper()
        if len(resultado) == 4 and resultado.isalnum():
            print(f"  [OCR] Captcha resuelto localmente: {resultado}")
            return resultado, 'ocr'
    print(f"  [OCR] Fallo ({resultado}), usando 2Captcha...")
    b64 = base64.b64encode(imagen_bytes).decode()
    task = {
        "clientKey": API_KEY_2CAPTCHA,
        "task": {"type": "ImageToTextTask", "body": b64,
                 "numeric": 0, "minLength": 4, "maxLength": 4}
    }
    r = requests.post("https://api.2captcha.com/createTask", json=task, timeout=30).json()
    if r.get("errorId") == 0:
        tid = r["taskId"]
        for i in range(30):
            time.sleep(3)
            poll = requests.post("https://api.2captcha.com/getTaskResult",
                json={"clientKey": API_KEY_2CAPTCHA, "taskId": tid}, timeout=15).json()
            if poll.get("status") == "ready":
                codigo = poll["solution"]["text"]
                print(f"  [2Captcha] Captcha resuelto: {codigo}")
                return codigo, '2captcha'
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
    if b64: return base64.b64decode(b64)
    return None

# ============================================================
# EXTRACCION DE DATOS
# ============================================================
def extraer_datos_expediente():
    from selenium.webdriver.common.by import By
    texto = driver.find_element(By.TAG_NAME, "body").text
    datos = {}
    secciones = texto.split('PARTES PROCESALES')
    if secciones:
        reporte = secciones[0]
        for linea in reporte.split('\n'):
            linea = linea.strip()
            if ':' in linea and not linea.startswith('http'):
                key, val = linea.split(':', 1)
                datos[key.strip()] = val.strip()
    nids = driver.execute_script("""
        return Array.from(document.querySelectorAll('a.aDescarg, a[href*="documentoD"]')).map(a => {
            var nid = a.href.split('nid=')[-1];
            var ctx = a.closest('.row, .divResol, .item, div') || a.parentElement;
            var desc = ctx ? ctx.textContent.trim().substring(0, 200) : '';
            return {nid: nid, desc: desc};
        });
    """)
    datos['_nids'] = nids
    return datos

# ============================================================
# DESCARGA DE DOCUMENTOS
# ============================================================
def descargar_documento(nid, exp, idx):
    try:
        r = requests.get(
            f"https://cej.pj.gob.pe/cej/forms/documentoD.html?nid={nid}", timeout=30)
        ext = '.pdf' if r.content[:4] == b'%PDF' else '.html'
        tipo = 'PDF' if ext == '.pdf' else 'HTML'
        fname = f"{exp}_doc_{idx:02d}{ext}"
        fpath = f"{OUTPUT_DIR}/documents/{fname}"
        with open(fpath, 'wb') as f: f.write(r.content)
        return (idx, tipo, len(r.content), None)
    except Exception as e:
        return (idx, 'ERR', 0, str(e))

# ============================================================
# PROCESAR EXPEDIENTE
# ============================================================
def procesar_expediente(exp, parte):
    exp_parts = exp.split('-')
    if len(exp_parts) != 7:
        print(f"[!] Error: formato expediente invalido: {exp}")
        return None

    print(f"\n{'='*60}")
    print(f"[*] PROCESANDO: {exp} | Parte: {parte}")
    print(f"{'='*60}")

    driver.get("https://cej.pj.gob.pe/cej/forms/busquedaform.html"); time.sleep(SLEEP_NAV)
    if 'perfdrive' in driver.current_url:
        print("[!] RADWARE BLOQUEO!"); return None

    driver.execute_script('document.querySelector("a[href=\'#tabs-2\']").click()'); time.sleep(SLEEP_FORM)

    campos = [("cod_expediente", exp_parts[0]), ("cod_anio", exp_parts[1]),
              ("cod_incidente", exp_parts[2]), ("cod_distprov", exp_parts[3]),
              ("cod_organo", exp_parts[4]), ("cod_especialidad", exp_parts[5]),
              ("cod_instancia", exp_parts[6])]
    for fid, val in campos:
        driver.execute_script(f'document.getElementById("{fid}").value = "{val}";')
    driver.execute_script(f'document.getElementById("parte").value = "{parte}";')
    time.sleep(SLEEP_FORM)

    driver.find_element("id", "consultarExpedientes").click(); time.sleep(SLEEP_NAV)

    captcha_bytes = extraer_captcha()
    intentos = 0
    while captcha_bytes and intentos < 5:
        intentos += 1; print(f"[5] Captcha intento {intentos}/5...")
        codigo, fuente = resolver_captcha(captcha_bytes)
        if not codigo: break
        driver.execute_script(f'document.getElementById("codigoCaptcha").value = "{codigo}";')
        time.sleep(1)
        driver.find_element("id", "consultarExpedientes").click(); time.sleep(SLEEP_NAV)
        if 'detalleform' in driver.current_url: print("[+] Captcha OK!"); break
        captcha_bytes = extraer_captcha()
        if captcha_bytes: print("[!] Captcha rechazado, reintentando..."); time.sleep(3)

    if 'detalleform' in driver.current_url:
        datos = extraer_datos_expediente()
        nids = datos.pop('_nids', [])
        print(f"[*] Documentos encontrados: {len(nids)}")
        if nids:
            print("[8] Descargando en paralelo...")
            with ThreadPoolExecutor(max_workers=5) as ex:
                futuros = [ex.submit(descargar_documento, item['nid'], exp.replace('-', '_'), i)
                          for i, item in enumerate(nids, 1)]
                for f in as_completed(futuros):
                    idx, tipo, size, err = f.result()
                    print(f"    [{'OK' if not err else 'FAIL'}] Doc {idx}: {tipo} ({size}b)" if not err else f"    [FAIL] Doc {idx}: {err}")
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = f"{OUTPUT_DIR}/cej_{exp}_{ts}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['Campo', 'Valor'])
            for k, v in datos.items(): w.writerow([k, str(v)[:200] if v else ''])
        print(f"[✓] CSV: {csv_path}")
        return datos
    else:
        print(f"[!] No se llego a detalle. URL: {driver.current_url}")
        return None

# ============================================================
if __name__ == '__main__':
    ts_inicio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[*] Inicio: {ts_inicio}")
    datos = procesar_expediente(EXPEDIENTE, PARTE)
    print(f"[*] Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
