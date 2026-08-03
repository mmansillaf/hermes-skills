#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Plantilla: generador JSON -> buscador offline full-text (v2 TC Peru).
Uso: adaptar SRC (carpeta JSON), campos del JSON fuente, y el diccionario
DERECHOS/SECCIONES segun el dominio. Produce /tmp stage con datos.js,
indice.js (delta-encoded) y casos/*.html. Copiar luego con cp -r a destino.
"""
import json
import re
import html as html_mod
import unicodedata
from pathlib import Path
from collections import defaultdict

SRC = Path("RUTA_A_JSON")            # <<< adaptar: carpeta con subcarpetas de JSON
OUT = Path("RUTA_DESTINO")           # <<< adaptar
STAGE = Path("/tmp/buscador_stage")
(STAGE / "casos").mkdir(parents=True, exist_ok=True)

STOP = set('''de la el los las y o u a al del en un una unos unas con por para que es lo su sus se no ni mas sin sobre entre como ser esta este estas estos ese esa esos ante hasta desde cuando cual cuales quien quienes cuyo cuya cuyas cuyos ya muy asi mismo tambien donde pero si luego despues antes otra otras otro otros toda todas todo todos tanto tan al ser fue eran sido ha han habia hay'''.split())

def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower()

def tokenize(s, limite=None):
    t = norm(s)
    if limite:
        t = t[:limite]
    return [w for w in re.findall(r'[a-z0-9]{3,}', t) if w not in STOP]

def stem_es(tok):
    """Stemmer español simplificado (tok ya normalizado, sin tildes)."""
    if len(tok) <= 5:
        return tok
    for suf, rep in [('aciones','acion'),('imientos','imient'),('amiento','amient'),
                     ('idades','idad'),('ciones','cion'),('siones','sion'),('dades','dad'),
                     ('mente',''),('adores','ador'),('adora','ador'),('istas','ista'),
                     ('ismos','ism'),('ismo','ism')]:
        if tok.endswith(suf):
            return tok[:-len(suf)] + rep
    if tok.endswith('es') and len(tok) > 4 and not tok.endswith('dios') and not tok.endswith('mes'):
        return tok[:-2]
    if tok.endswith('s') and len(tok) > 5:
        return tok[:-1]
    return tok

# ------------------------------------------------------------ extraccion (adaptar al dominio)
PAT_DEM = [
    re.compile(r'interpuesto por (don|doña|d\.|dña\.?)\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü\.\'\-]+(?:\s+[A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü\.\'\-]+){1,6})', re.I),
    re.compile(r'demandante (don|doña|d\.|dña\.?)\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü\.\'\-]+(?:\s+[A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü\.\'\-]+){1,6})', re.I),
]

def extraer_demandante(texto, campo):
    if campo and len(campo.strip()) >= 25:
        return campo.strip()
    if texto:
        for rx in PAT_DEM:
            m = rx.search(texto)
            if m and len(m.group(2).strip()) >= 8:
                return f"{m.group(1).capitalize()} {m.group(2).strip()}"
    return (campo or "").strip()

DISTRITOS_SUCIOS = {'DEMANDANTE', 'DEMANDADO', 'JUEZ', 'MATERIA', 'PROCEDENCIA', 'EXPEDIENTE', 'CORTE', 'SALA'}

def extraer_distrito(texto, campo):
    """Recupera distrito real si el campo viene sucio/vacio (datos de scraper)."""
    c = (campo or '').strip().upper()
    if c and c not in DISTRITOS_SUCIOS and len(c) >= 3:
        return c
    if texto:
        m = re.search(r'CORTE SUPERIOR DE JUSTICIA DE\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ ]{2,30})', texto)
        if not m:
            m = re.search(r'DISTRITO JUDICIAL DE\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ ]{2,30})', texto)
        if not m:
            m = re.search(r'([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ ]{2,30}),\s*\d{1,2}\s+de\s+[a-záéíóúñü]+', texto)
        if m:
            d = m.group(1).strip().upper()
            d = re.split(r'\s+(?:SALA|JUZGADO|CORTE|SEGUNDA|PRIMERA|TERCERA|CUARTA|QUINTA)', d)[0].strip()
            if 3 <= len(d) <= 40:
                return d
    return c

def extraer_fallo(texto):
    t = norm(texto)
    def cerca(palabra):
        return bool(re.search(r'declar\w*\s+(?:la demanda\s+)?' + palabra, t)) or bool(re.search(r'\b' + palabra + r'\b', t))
    if cerca('improcedente'): return 'IMPROCEDENTE'
    if cerca('infundada'):    return 'INFUNDADA'
    if cerca('fundada'):      return 'FUNDADA'
    return ''

# <<< adaptar al dominio: categorias tematicas con patrones
DERECHOS = [
    ('Pensión',        re.compile(r'pensi[oó]n|jubilaci[oó]n|renta vitalicia|onp|sctr|afp', re.I)),
    ('Salud',          re.compile(r'salud|essalud|prestaci[oó]n m[ée]dica|discapacidad', re.I)),
]

def extraer_derechos(texto):
    t = norm(texto); out = []
    for nombre, rx in DERECHOS:
        if rx.search(t) and len(out) < 3:
            out.append(nombre)
    return out

def extraer_ponentes(texto):
    out = []
    for m in re.finditer(r'PONENTE\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ\-]+(?:\s+[A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ\-]+){0,3})', texto):
        out.append(m.group(1).strip())
    return list(dict.fromkeys(out))

def extraer_citas(texto):
    citas = set()
    for m in re.finditer(r'STC\s*(\d{4,5}-\d{4}(?:-[A-Z]{2,4})?(?:/TC)?)', texto, re.I):
        citas.add(m.group(1).upper())
    return sorted(citas)[:12]

def extraer_resumen(texto):
    t = " ".join(texto.split())
    i = t.upper().find('ASUNTO')
    if i >= 0:
        t = t[i+6:]
    frases = re.split(r'(?<=[.;:])\s+', t)
    out = []
    for f in frases:
        out.append(f.strip())
        if len(' '.join(out)) > 320:
            break
    return ' '.join(out)[:420]

# ------------------------------------------------------------ secciones del documento (adaptar)
SECCIONES_EXACTAS = {
    "asunto", "antecedentes", "fundamentos", "considerando", "resuelve",
    "parte resolutiva", "ha resuelto", "razón de relatoría", "petitorio",
}
SECCIONES_PREFIX = ("proceso de ", "exp. ", "voto ", "los magistrados", "el tribunal")

def esc(t):
    return html_mod.escape(t or "", quote=False)

def es_titulo_seccion(linea):
    s = linea.strip(); low = s.lower()
    return low in SECCIONES_EXACTAS or any(low.startswith(p) for p in SECCIONES_PREFIX)

def texto_a_html(texto):
    out = []; actual = []
    def flush():
        nonlocal actual
        if actual:
            out.append(f"<p>{esc(' '.join(actual))}</p>"); actual = []
    for linea in texto.split("\n"):
        l = linea.strip()
        if not l: flush(); continue
        if es_titulo_seccion(l):
            flush(); out.append(f'<h3 class="seccion">{esc(l)}</h3>')
        else:
            actual.append(l)
    flush()
    return "\n".join(out)

# ------------------------------------------------------------ delta encoding
def encode_postings(lst):
    out = []; prev = -1
    for x in lst:
        d = x - prev - 1
        prev = x
        out.append(chr(33 + d) if 0 <= d < 90 else f'~{d}~')
    return ''.join(out)

# ------------------------------------------------------------ proceso
casos = []
postings = defaultdict(list)
errores = []

# <<< adaptar el glob y los nombres de campo al JSON fuente
for json_path in sorted(SRC.glob("*/[0-9]*.json")):
    fecha = json_path.parent.name
    try:
        d = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        errores.append(f"{json_path}: {e}"); continue
    texto = d.get("texto") or ""
    num = d.get("numero") or json_path.stem
    tipo = d.get("tipo") or "Caso"
    dist = extraer_distrito(texto, d.get("distrito"))
    sent = (d.get("sentencia") or "").strip()
    edic = (d.get("edicion") or "").strip()
    dem = extraer_demandante(texto, d.get("demandante"))
    fallo = extraer_fallo(texto)
    derechos = extraer_derechos(texto)
    ponentes = extraer_ponentes(texto)
    citas = extraer_citas(texto)
    resumen = extraer_resumen(texto)
    stem = json_path.stem
    doc_idx = len(casos)
    casos.append([num, tipo, dist, dem, sent, fecha, edic, stem, fallo, derechos, ponentes, citas, resumen])

    (STAGE / "casos" / fecha).mkdir(parents=True, exist_ok=True)
    # <<< generar_caso(): HTML individual (TOC, breadcrumb, badges, resaltado ?q=, notas, print)

    toks_meta = tokenize(f"{num} {tipo} {dist} {dem} {sent} {fecha} {edic} {fallo} {' '.join(derechos)} {' '.join(ponentes)}")
    toks_texto = tokenize(texto, limite=12000)
    for t in set(toks_meta) | set(toks_texto):
        postings[t].append(doc_idx)
        if len(t) >= 6:
            postings['5:' + t[:5]].append(doc_idx)
        st = stem_es(t)
        if st != t:
            postings['s:' + st].append(doc_idx)
    for c in citas:
        for t in tokenize(c):
            postings[t].append(doc_idx)

(STAGE / "datos.js").write_text("window.CASOS=" + json.dumps(casos, ensure_ascii=False) + ";", encoding="utf-8")
(STAGE / "indice.js").write_text("window.INDICE=" + json.dumps({k: encode_postings(v) for k, v in postings.items()}, ensure_ascii=False) + ";", encoding="utf-8")
print(f"Casos: {len(casos)} | Terminos: {len(postings):,} | Postings: {sum(len(v) for v in postings.values()):,} | Errores: {len(errores)}")
