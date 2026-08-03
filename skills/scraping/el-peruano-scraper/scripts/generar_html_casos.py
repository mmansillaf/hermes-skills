#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera HTML legibles a partir de JSON de casos TC (El Peruano, cuadernillos PC).

Uso:
    python3 generar_html_casos.py                     # carpeta BASE por defecto
    python3 generar_html_casos.py /ruta/a/carpeta     # otra carpeta con *.json

Salida: <carpeta>/html/<nombre_archivo>.html

Leccion clave (ver SKILL.md Paso 4):
- Detectar titulos de seccion a nivel de LINEA, ANTES de unir parrafos.
- NO usar heuristica "linea en MAYUSCULAS corta" (falsos positivos:
  nombres de magistrados, firmas "SS.", codigos de imprenta W-...).
  Usar lista exacta de titulos + prefijos conocidos.
"""
import json
import sys
from pathlib import Path
import html as html_mod

BASE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/mnt/d/PyCode/ProcesosConstitucionales/data/casos_2016_2021/2021-07-30"
)
OUT = BASE / "html"
OUT.mkdir(exist_ok=True)

# Titulos de seccion reales en sentencias TC (comparacion exacta, case-insensitive)
SECCIONES_EXACTAS = {
    "asunto", "antecedentes", "fundamentos", "análisis", "analisis",
    "considerando", "resuelve", "parte resolutiva", "ha resuelto",
    "razón de relatoría", "razon de relatoria", "petitorio",
    "delimitación del petitorio", "análisis de la controversia",
    "por tales consideraciones", "publíquese y notifíquese", "publiquese y notifiquese",
    "costos procesales", "sentencia del tribunal constitucional",
}
SECCIONES_PREFIX = ("proceso de ", "exp. ", "voto ", "los magistrados", "el tribunal")


def esc(t):
    return html_mod.escape(t or "", quote=False)


def es_titulo_seccion(linea):
    """True si la linea es un titulo de seccion real (no nombres ni firmas)."""
    low = linea.strip().lower()
    if low in SECCIONES_EXACTAS:
        return True
    return any(low.startswith(p) for p in SECCIONES_PREFIX)


def texto_a_html(texto):
    """Convierte el texto crudo (con \n) en parrafos y secciones HTML.
    Detecta titulos de seccion a nivel de linea ANTES de unir parrafos."""
    out = []
    actual = []

    def flush():
        nonlocal actual
        if actual:
            out.append(f"<p>{esc(' '.join(actual))}</p>")
            actual = []

    for linea in texto.split("\n"):
        l = linea.strip()
        if not l:
            flush()
            continue
        if es_titulo_seccion(l):
            flush()
            out.append(f'<h3 class="seccion">{esc(l)}</h3>')
        else:
            actual.append(l)
    flush()
    return "\n".join(out)


CSS = """
:root { --accent:#7c3aed; --accent2:#4f46e5; --bg:#f6f5fa; --card:#ffffff; --text:#1f2430; --muted:#6b7280; }
* { box-sizing:border-box; }
body { font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; background:var(--bg);
       color:var(--text); margin:0; padding:32px 16px; font-size:13px; line-height:1.65; }
.wrap { max-width:860px; margin:0 auto; }
.cabecera { background:linear-gradient(135deg,var(--accent),var(--accent2)); color:#fff;
            border-radius:14px; padding:28px 32px; margin-bottom:20px; box-shadow:0 6px 20px rgba(79,70,229,.25); }
.cabecera h1 { margin:0 0 6px; font-size:22px; letter-spacing:.3px; }
.cabecera .tipo { display:inline-block; background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35);
                  padding:2px 12px; border-radius:999px; font-size:12px; font-weight:600; margin-bottom:10px; }
.meta { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin-bottom:20px; }
.meta .card { background:var(--card); border:1px solid #e5e7eb; border-radius:10px; padding:12px 14px; }
.meta .card .k { font-size:11px; text-transform:uppercase; letter-spacing:.6px; color:var(--muted); margin-bottom:2px; }
.meta .card .v { font-size:14px; font-weight:600; }
.documento { background:var(--card); border:1px solid #e5e7eb; border-radius:14px; padding:28px 34px;
             box-shadow:0 2px 10px rgba(0,0,0,.04); }
.documento h3.seccion { margin:26px 0 8px; font-size:14px; text-transform:uppercase; letter-spacing:.8px;
                        color:var(--accent); border-bottom:2px solid #ede9fe; padding-bottom:5px; }
.documento h3.seccion:first-child { margin-top:0; }
.documento p { margin:0 0 12px; text-align:justify; }
@media (max-width:600px){ body{padding:16px 8px;} .cabecera{padding:20px;} .documento{padding:20px;} }
"""


def generar(data):
    """Genera el HTML para un caso."""
    titulo = f"{data.get('tipo', 'Caso')} {data.get('numero', '')}".strip()
    texto = data.get("texto") or ""

    metas = [
        ("Expediente", data.get("numero")),
        ("Sentencia", data.get("sentencia")),
        ("Tipo", data.get("tipo")),
        ("Distrito", data.get("distrito")),
        ("Publicación", data.get("fecha_publicacion")),
        ("Edición", data.get("edicion")),
        ("Corte", data.get("corte")),
        ("Demandante", data.get("demandante")),
        ("Fecha resolución", data.get("fecha_resolucion")),
    ]
    metas = [(k, v) for k, v in metas if v]
    cards = "".join(
        f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{esc(str(v))}</div></div>'
        for k, v in metas
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="cabecera">
    <span class="tipo">{esc(data.get('tipo', 'Caso'))}</span>
    <h1>{esc(titulo)}</h1>
  </div>
  <div class="meta">{cards}</div>
  <div class="documento">
{texto_a_html(texto)}
  </div>
</div>
</body>
</html>"""


def main():
    archivos = sorted(BASE.glob("*.json"))
    if not archivos:
        print(f"No hay *.json en {BASE}")
        return 1
    for ruta in archivos:
        data = json.loads(ruta.read_text(encoding="utf-8"))
        out = OUT / (ruta.stem + ".html")
        out.write_text(generar(data), encoding="utf-8")
        print(f"OK  {out.name}")
    print(f"Listo. Salida: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
