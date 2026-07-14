"""
Clasificador para lotes adicionales de documentos legales.
Procesa PDFs (pdftotext) y DOC/DOCX (python-docx/olefile) en paralelo.
Solo procesa archivos NUEVOS (no duplicados de clasificaciones anteriores).
Optimizado para i7-9850H (12 hilos) con cuello de botella en disco HDD USB.
"""
import os, re, json, sys, time, subprocess
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

# === CONFIG (ajustar según hardware y rutas) ===
CLASIFICADOS_DIR = "/home/usuario/Escritorio/PyCode/ClasificacionJurisPDF/Clasificados"
OUT_DIR = "/home/usuario/Escritorio/PyCode/ClasificacionJurisPDF/data"
MAX_WORKERS_PDF = 8   # para HDD USB; usar 12 para NVMe
MAX_WORKERS_DOC = 12  # ThreadPoolExecutor, I/O bound

# === PATRONES DE CLASIFICACION ===
CATEGORY_ORDER = [
    ("sentencia", [r'\bSENTENCIA\b', r'\bFALLO\b', r'SE RESUELVE\b']),
    ("notificacion", [r'C[EÉ]DULA\s+DE\s+NOTIFICACI[OÓ]N', r'NOTIFIQU[EÉ]SE']),
    ("citacion", [r'\bCITO\b', r'CITACI[OÓ]N\b', r'C[IÍ]TESE']),
    ("oficio", [r'OFICIO\s+(N[°º]|No\.?-?)\s*\d+', r'OFICIO\s+(M[UÚ]LTIPLE|CIRCULAR)']),
    ("acta_audiencia", [r'ACTA\s+DE\s+(?:VISTA|REGISTRO\s+DE\s+AUDIENCIA|AUDIENCIA)',
                        r'AUDIENCIA\s+(?:ÚNICA|PUBLICA|PROGRAMADA)',
                        r'VISTA\s+DE\s+LA\s+CAUSA']),
    ("pericia", [r'INFORME\s+PERICIAL', r'DICTAMEN\s+PERICIAL', r'PERICIA\b']),
    ("conciliacion", [r'ACTA\s+DE\s+CONCILIACI[OÓ]N']),
    ("demanda", [r'INTERPONE\s+DEMANDA', r'ESCRITO\s+DE\s+DEMANDA']),
    ("resolucion_archivo", [r'ARCH[IÍ]VESE']),
    ("resolucion_remite", [r'REM[IÍ]TASE']),
    ("resolucion_admite", [r'ADMITIR\s+(?:A\s+)?TR[ÁA]MITE']),
    ("resolucion_generica", [
        r'RESOLUCI[OÓ]N\s+(N[UÚ]MERO|N[°º]|NRO\.?\s*|No\.?\s*)\s*\d+',
        r'RESOLUCI[OÓ]N\s+(NRO|NO\.?)\s+(UNO|DOS|TRES|CUATRO|CINCO|SEIS|SIETE|OCHO|NUEVE|DIEZ)',
        r'^RESOLUCI[OÓ]N\s+\d+\s*$',
        r'^RESOLUCI[OÓ]N\s*$',
    ]),
]

pat_materia = re.compile(r'MATERIA\s*:?\s*(.+?)$', re.IGNORECASE | re.MULTILINE)


def build_known_set():
    """Construye set de nombres de archivo ya clasificados."""
    known = set()
    for cat in os.listdir(CLASIFICADOS_DIR):
        cat_path = os.path.join(CLASIFICADOS_DIR, cat)
        if not os.path.isdir(cat_path):
            continue
        for f in os.listdir(cat_path):
            known.add(f.lower())
    return known


def collect_new_files(known, sources):
    """Colecta archivos PDF y DOC/DOCX que NO estan en known."""
    pdfs, docs = [], []
    for label, dirpath in sources:
        if not os.path.isdir(dirpath):
            continue
        for f in os.listdir(dirpath):
            fp = os.path.join(dirpath, f)
            if not os.path.isfile(fp):
                continue
            if f.lower() in known:
                continue
            fl = f.lower()
            if fl.endswith('.pdf'):
                pdfs.append(fp)
            elif fl.endswith(('.doc', '.docx')):
                docs.append(fp)
    return pdfs, docs


def classify_text(txt):
    """Clasifica el texto extraido en una categoria."""
    if len(txt) < 50:
        return "sin_texto"
    upper = txt.upper()
    for cat, patterns in CATEGORY_ORDER:
        for pat in patterns:
            if re.search(pat, upper):
                return cat
    # Extraer materia para no_clasificado si es posible
    m = pat_materia.search(txt)
    return "no_clasificado"


def classify_pdf(path):
    """Clasifica un PDF usando pdftotext."""
    try:
        res = subprocess.run(['pdftotext', '-f', '1', '-l', '1', path, '-'],
                           capture_output=True, text=True, timeout=10)
        txt = res.stdout
    except:
        return os.path.basename(path), "error"
    return os.path.basename(path), classify_text(txt)


def classify_doc(path):
    """Clasifica un DOC/DOCX usando python-docx (docx) u olefile (doc)."""
    try:
        from docx import Document
        doc = Document(path)
        txt = ' '.join(p.text for p in doc.paragraphs[:50])
    except:
        try:
            import olefile
            ole = olefile.OleFileIO(path)
            txt = ole.openstream('WordDocument').read().decode('utf-8', errors='ignore')[:3000]
            ole.close()
        except:
            return os.path.basename(path), "error"
    return os.path.basename(path), classify_text(txt)


def main():
    t0 = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando...")

    known = build_known_set()
    print(f"  Ya clasificados en {CLASIFICADOS_DIR}: {len(known)}")

    sources = [
        ("SALACOMPIE", "/media/usuario/Nuevo vol/Saleman/DescargaTotalSALACOMPIE-COPIADO"),
        ("SAL_Files", "/media/usuario/Nuevo vol/Descargas/SAL/Files"),
        ("PESQUERA", "/media/usuario/Nuevo vol/Saleman/DESCARGA-PESQUERA"),
        ("PJ_PENDIENTE", "/media/usuario/Nuevo vol/Saleman/DescargaPJpc-lnvhome3PENDIENTE-EXTRACT"),
    ]
    pdfs, docs = collect_new_files(known, sources)
    total_pdfs, total_docs = len(pdfs), len(docs)
    print(f"  PDFs nuevos: {total_pdfs}")
    print(f"  DOC/DOCX nuevos: {total_docs}")
    print(f"  Total: {total_pdfs + total_docs}")

    if total_pdfs + total_docs == 0:
        print("  No hay archivos nuevos. Saliendo.")
        return

    resultados = []
    counter = Counter()

    # --- PDFs ---
    if pdfs:
        t1 = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Procesando {total_pdfs} PDFs con {MAX_WORKERS_PDF} workers...")
        with ProcessPoolExecutor(max_workers=MAX_WORKERS_PDF) as pool:
            futuros = {pool.submit(classify_pdf, p): p for p in pdfs}
            done = 0
            for f in as_completed(futuros):
                bn, cat = f.result()
                counter[cat] += 1
                resultados.append((bn, cat))
                done += 1
                if done % 20000 == 0:
                    elapsed = time.time() - t1
                    rate = done / elapsed
                    rem = (total_pdfs - done) / rate
                    print(f"    [{time.strftime('%H:%M:%S')}] {done}/{total_pdfs}  |  {rate:.0f} docs/s  |  ETA: {rem/60:.1f} min")
        t = time.time() - t1
        print(f"  PDFs: {total_pdfs} en {t:.0f}s ({total_pdfs/t:.0f} docs/s)")

    # --- DOCS ---
    if docs:
        t2 = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] Procesando {total_docs} DOC/DOCX con {MAX_WORKERS_DOC} workers...")
        batch_size = 500
        batches = [docs[i:i+batch_size] for i in range(0, len(docs), batch_size)]

        def process_batch(batch):
            return [classify_doc(p) for p in batch]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS_DOC) as pool:
            futuros = {pool.submit(process_batch, b): b for b in batches}
            done = 0
            for f in as_completed(futuros):
                for bn, cat in f.result():
                    counter[cat] += 1
                    resultados.append((bn, cat))
                    done += 1
                if done % 10000 == 0:
                    elapsed = time.time() - t2
                    rate = done / elapsed
                    rem = (total_docs - done) / rate
                    print(f"    [{time.strftime('%H:%M:%S')}] {done}/{total_docs}  |  {rate:.0f} docs/s  |  ETA: {rem/60:.1f} min")
        t = time.time() - t2
        print(f"  DOCS: {total_docs} en {t:.0f}s ({total_docs/t:.0f} docs/s)")

    # --- Reporte ---
    t_total = time.time() - t0
    print(f"\n{'='*60}")
    print(f"RESULTADOS LOTE 2")
    print(f"{'='*60}")
    print(f"Procesados: {len(resultados)} en {t_total:.0f}s ({len(resultados)/t_total:.0f} docs/s)")
    print(f"\n{'Categoria':<35} {'Cantidad':>10} {'%':>7}")
    print('  ' + '-' * 52)
    for cat, count in counter.most_common():
        pct = count / len(resultados) * 100
        print(f'  {cat:<35} {count:>10} {pct:>6.1f}%')

    # Guardar CSV
    csv_path = os.path.join(OUT_DIR, "clasificacion_lote2.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("filename,categoria\n")
        for bn, cat in resultados:
            f.write(f"{bn},{cat}\n")

    report = {
        "hardware": "i7-9850H 6C/12T, 46GB RAM",
        "fuentes": [s[0] for s in sources],
        "total_procesados": len(resultados),
        "pdfs": total_pdfs,
        "docs": total_docs,
        "tiempo_segundos": round(t_total, 1),
        "docs_por_segundo": round(len(resultados)/t_total, 1),
        "distribucion": dict(counter.most_common()),
    }
    json_path = os.path.join(OUT_DIR, "resumen_lote2.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nCSV: {csv_path}")
    print(f"JSON: {json_path}")
    print(f"\n[FIN] {time.strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
