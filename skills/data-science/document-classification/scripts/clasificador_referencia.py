#!/usr/bin/env python3
"""
Bulk classifier for Peruvian judicial PDFs.
Extracts text with pymupdf, classifies by regex rules, creates symlinks.

See SKILL.md for full workflow.
"""
import fitz
import os
import re
import csv
import sys
import glob
import time
import json
from collections import Counter

# ---------- CONFIG ----------
PDF_DIR = "/ruta/a/tus/pdfs"
OUT_BASE = "./Clasificados"
REPORT_DIR = "./data"

# ---------- CATEGORIES ----------
CATEGORIES = {
    "sentencia": [r'\bSENTENCIA\b', r'\bFALLO\b', r'VISTA LA CAUSA'],
    "notificacion": [r'C[EÉ]DULA\s+DE\s+NOTIFICACI[OÓ]N', r'NOTIFIQU[EÉ]SE'],
    "citacion": [r'\bCITO\b', r'CITACI[OÓ]N\b', r'C[IÍ]TESE'],
    "oficio": [r'OFICIO\s+N[°º]\s*\d+', r'OFICIO\s+M[UÚ]LTIPLE'],
    "pericia": [r'INFORME\s+PERICIAL', r'DICTAMEN\s+PERICIAL'],
    "conciliacion": [r'ACTA\s+DE\s+CONCILIACI[OÓ]N', r'AUDIENCIA\s+DE\s+CONCILIACI[OÓ]N'],
    "demanda": [r'INTERPONE\s+DEMANDA', r'ESCRITO\s+DE\s+DEMANDA'],
    "resolucion_archivo": [r'ARCH[IÍ]VESE', r'DASE\s+POR\s+CONCLUIDO'],
    "resolucion_remite": [r'REM[IÍ]TASE', r'ELEVAR\s+LOS\s+AUTOS'],
    "resolucion_admite": [r'ADMITIR\s+(?:A\s+)?TR[ÁA]MITE', r'ADM[IÍ]TASE'],
    "resolucion_generica": [
        r'RESOLUCI[OÓ]N\s+N[UÚ]MERO', r'RESOLUCION\s+NUMERO',
        r'RESOLUCI[OÓ]N\s+N[°º]', r'RESOLUCION\s+N[°º]',
    ],
}

CATEGORY_NAMES = {
    "sentencia": "Sentencia", "notificacion": "Notificacion",
    "citacion": "Citacion", "oficio": "Oficio",
    "pericia": "Pericia", "conciliacion": "Conciliacion",
    "demanda": "Demanda", "resolucion_admite": "Resolucion_Admite_Tramite",
    "resolucion_archivo": "Resolucion_Archivo",
    "resolucion_remite": "Resolucion_Remite",
    "resolucion_generica": "Resolucion",
    "sin_texto": "Sin_Texto", "error": "Error",
}

def extraer_texto(pdf_path, max_pages=5):
    doc = fitz.open(pdf_path)
    txt = ""
    for i in range(min(len(doc), max_pages)):
        txt += doc[i].get_text()
    doc.close()
    return txt, len(doc)

def clasificar(texto):
    if len(texto) < 50:
        return "sin_texto", 0.0
    upper = texto.upper()
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, upper):
                return cat, 1.0
    return "no_clasificado", 0.0

def crear_symlink(origen, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.islink(destino) or os.path.exists(destino):
        os.remove(destino)
    os.symlink(origen, destino)

def main():
    os.makedirs(OUT_BASE, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)

    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    total = len(pdfs)
    print(f"Procesando {total} PDFs...")

    # Create category dirs
    for cat in list(CATEGORY_NAMES.keys()) + ["no_clasificado"]:
        os.makedirs(os.path.join(OUT_BASE, CATEGORY_NAMES.get(cat, cat)), exist_ok=True)

    resultados = []
    counter = Counter()
    t0 = time.time()

    for i, pdf in enumerate(pdfs, 1):
        try:
            texto, n_pages = extraer_texto(pdf)
            categoria, conf = clasificar(texto)
            size_kb = os.path.getsize(pdf) / 1024
        except Exception as e:
            resultados.append({"filename": os.path.basename(pdf), "categoria": "error", "error": str(e)})
            counter["error"] += 1
            continue

        resultados.append({
            "filename": os.path.basename(pdf),
            "categoria": categoria,
            "nombre_categoria": CATEGORY_NAMES.get(categoria, categoria),
            "paginas": n_pages,
            "size_kb": round(size_kb, 1),
            "path": pdf,
        })
        counter[categoria] += 1

        dir_name = CATEGORY_NAMES.get(categoria, categoria)
        link_path = os.path.join(OUT_BASE, dir_name, os.path.basename(pdf))
        crear_symlink(pdf, link_path)

        if i % 10000 == 0:
            rate = i / (time.time() - t0)
            eta = (total - i) / rate / 60
            print(f"  {i}/{total}  |  {rate:.0f} docs/s  |  ETA: {eta:.1f} min")

    elapsed = time.time() - t0
    print(f"\nCompletado: {total} PDFs en {elapsed:.0f}s ({total/elapsed:.0f} docs/s)")
    print("\nDistribucion:")
    for cat, count in counter.most_common():
        print(f"  {CATEGORY_NAMES.get(cat, cat):<30} {count:>8} ({count/total*100:>5.1f}%)")

    # CSV
    csv_path = os.path.join(REPORT_DIR, "clasificacion.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["filename", "categoria", "nombre_categoria", "paginas", "size_kb", "ruta"])
        for r in resultados:
            w.writerow([r.get("filename"), r.get("categoria"), r.get("nombre_categoria"),
                        r.get("paginas", 0), r.get("size_kb", 0), r.get("path")])
    print(f"\nCSV: {csv_path}")

if __name__ == "__main__":
    main()
