"""
Reclasificador de no_clasificados.
Toma solo los PDFs en Clasificados/no_clasificado/ y los reclasifica
con patrones actualizados, moviendo symlinks a carpetas correctas.

USO:
    python3 scripts/reclasificar.py

Requiere:
    - pymupdf (fitz)
    - Estructura de carpetas: OUT_BASE/no_clasificado/
    - CATEGORIES actualizado en el clasificador principal

El script replica los mismos patrones de CATEGORIES del clasificador.py
para asegurar consistencia en la reclasificación.
"""
import fitz
import os
import re
import csv
import json
import time
from collections import Counter

OUT_BASE = "/home/usuario/Escritorio/PyCode/ClasificacionJurisPDF/Clasificados"
REPORT_DIR = "/home/usuario/Escritorio/PyCode/ClasificacionJurisPDF/data"

# Copiar CATEGORIES del clasificador.py aquí
# Mantener sincronizado con las actualizaciones
CATEGORIES = {
    "sentencia": [
        r'\bSENTENCIA\b',
        r'\bFALLO\b',
        r'SE RESUELVE\b.*?(?:\n|$)',
    ],
    "notificacion": [
        r'C[EÉ]DULA\s+DE\s+NOTIFICACI[OÓ]N',
        r'NOTIFIQU[EÉ]SE',
        r'NOTIFICACI[OÓ]N\s+ELECTR[OÓ]NICA',
    ],
    "citacion": [
        r'\bCITO\b', r'CITACI[OÓ]N\b', r'C[IÍ]TESE',
    ],
    "oficio": [
        r'OFICIO\s+N[°º]\s*\d+',
        r'OFICIO\s+No\.?-?\s*\d+',
        r'OFICIO\s+M[UÚ]LTIPLE',
    ],
    "acta_audiencia": [
        r'ACTA\s+DE\s+(?:VISTA|REGISTRO\s+DE\s+AUDIENCIA|AUDIENCIA)',
        r'AUDIENCIA\s+(?:ÚNICA|PUBLICA|PROGRAMADA)',
        r'VISTA\s+DE\s+LA\s+CAUSA',
    ],
    "pericia": [
        r'INFORME\s+PERICIAL', r'DICTAMEN\s+PERICIAL', r'PERICIA\b',
    ],
    "conciliacion": [
        r'ACTA\s+DE\s+CONCILIACI[OÓ]N',
        r'AUDIENCIA\s+DE\s+CONCILIACI[OÓ]N',
    ],
    "demanda": [
        r'INTERPONE\s+DEMANDA', r'ESCRITO\s+DE\s+DEMANDA',
        r'ADMITIR\s+(?:A\s+)?TR[ÁA]MITE\s+LA\s+DEMANDA',
    ],
    "resolucion_archivo": [
        r'ARCH[IÍ]VESE', r'DASE\s+POR\s+CONCLUIDO',
    ],
    "resolucion_remite": [
        r'REM[IÍ]TASE', r'ELEVAR\s+LOS\s+AUTOS',
    ],
    "resolucion_admite": [
        r'ADMITIR\s+(?:A\s+)?TR[ÁA]MITE', r'ADM[IÍ]TASE',
    ],
    "resolucion_generica": [
        # Standard
        r'RESOLUCI[OÓ]N\s+N[UÚ]MERO\s+',
        r'RESOLUCI[OÓ]N\s+N[°º]\s*\d+',
        r'RESOLUCI[OÓ]N\s+NRO\.?\s*\d+',
        # No. + digito
        r'RESOLUCI[OÓ]N\s+No\.\s*\d+',
        # Nro/No + letras
        r'RESOLUCI[OÓ]N\s+(NRO|NO\.?)\s+(UNO|DOS|TRES|CUATRO|CINCO|SEIS|SIETE|OCHO|NUEVE|DIEZ|ONCE|DOCE|TRECE|CATORCE|QUINCE|VEINTE|TREINTA|PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SÉPTIMA|OCTAVA|NOVENA|DÉCIMA)',
        r'RESOLUCION\s+(NRO|NO\.?)\s+(UNO|DOS|TRES|CUATRO|CINCO|SEIS|SIETE|OCHO|NUEVE|DIEZ|ONCE|DOCE|TRECE|CATORCE|QUINCE|VEINTE|TREINTA|PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA|SEPTIMA|OCTAVA|NOVENA|DECIMA)',
        # Solo digito en linea propia
        r'^RESOLUCI[OÓ]N\s+\d+\s*$',
        # Numero en linea aparte
        r'^RESOLUCI[OÓ]N\s*$',
    ],
}

CATEGORY_NAMES = {
    "sentencia": "Sentencia",
    "notificacion": "Notificación",
    "citacion": "Citación",
    "oficio": "Oficio",
    "acta_audiencia": "Acta de Audiencia",
    "pericia": "Pericia",
    "conciliacion": "Conciliación",
    "demanda": "Demanda",
    "resolucion_admite": "Resolución - Admite Trámite",
    "resolucion_archivo": "Resolución - Archivo",
    "resolucion_remite": "Resolución - Remite/Eleva",
    "resolucion_generica": "Resolución",
    "sin_texto": "Sin Texto Extraíble",
    "error": "Error de Lectura",
}

def clasificar(texto):
    if len(texto) < 50:
        return "sin_texto"
    upper = texto.upper()
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, upper):
                return cat
    return "no_clasificado"

def reclasificar():
    no_clas_dir = os.path.join(OUT_BASE, "no_clasificado")
    if not os.path.isdir(no_clas_dir):
        print(f"ERROR: No existe {no_clas_dir}")
        return
    
    files = [f for f in os.listdir(no_clas_dir) if os.path.islink(os.path.join(no_clas_dir, f))]
    total = len(files)
    print(f"Reclasificando {total} archivos de no_clasificado/...")
    
    t_start = time.time()
    counter = Counter()
    
    for i, f in enumerate(files, 1):
        path = os.path.join(no_clas_dir, f)
        real = os.path.realpath(path)
        
        doc = None
        try:
            doc = fitz.open(real)
            txt = ""
            for j in range(min(doc.page_count, 5)):
                txt += doc[j].get_text()
        except:
            categoria = "error"
        else:
            categoria = clasificar(txt)
        finally:
            if doc:
                doc.close()
        
        counter[categoria] += 1
        
        # Mover symlink si cambio de categoria
        if categoria not in ("no_clasificado", "error"):
            dir_name = CATEGORY_NAMES.get(categoria, categoria)
            safe_dir = dir_name.replace("/", "_").replace(" ", "_")
            new_link = os.path.join(OUT_BASE, safe_dir, f)
            os.makedirs(os.path.dirname(new_link), exist_ok=True)
            if os.path.islink(new_link) or os.path.exists(new_link):
                os.remove(new_link)
            os.symlink(real, new_link)
            os.remove(path)  # eliminar symlink viejo
        
        if i % 2000 == 0:
            elapsed = time.time() - t_start
            rate = i / elapsed
            print(f"  {i}/{total}  |  {rate:.0f} docs/s")
    
    t_total = time.time() - t_start
    print(f"\nTiempo: {t_total:.1f}s ({total/t_total:.0f} docs/s)")
    for cat, count in counter.most_common():
        print(f"  {CATEGORY_NAMES.get(cat, cat):<35} {count:>6}")


if __name__ == "__main__":
    reclasificar()
