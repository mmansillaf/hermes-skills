#!/usr/bin/env python3
"""Inventario completo de carpeta compartida de Google Drive SIN OAuth.

Uso:
    python3 inventory_gdrive.py <FOLDER_ID_o_URL> [--out DIR] [--threads 24]

Hace 2 pasos:
  1. Estructura: recorre https://drive.google.com/embeddedfolderview?id=<id>
     (lista TODOS los hijos, sin paginacion; nombres de carpeta en
     <div class="flip-entry-title">). NO usar _DRIVE_ivd: pagina a ~50 items.
  2. Tamanos: GET https://drive.google.com/uc?export=download&id=<id> con
     header "Range: bytes=0-0" -> 206 + Content-Range: bytes 0-0/TOTAL
     (tamano exacto sin descargar). Paralelo, 1 Session por worker.
     Archivos >~100MB devuelven HTML "Virus scan warning" (size=None);
     gdown los resuelve al descargar.

Salida: <out>/inventario_completo.json + <out>/informe_inventario.txt
"""
import argparse
import concurrent.futures as cf
import json
import re
import sys
import time

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def new_sess():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9"})
    return s


def embedded_items(sess, fid):
    """(nombre, (files[(id,nombre)], docs[(id,nombre)], folders[(id,nombre)]))"""
    r = sess.get(f"https://drive.google.com/embeddedfolderview?id={fid}", timeout=45)
    if r.status_code != 200:
        return None, None
    m = re.search(r"<title>(.*?)</title>", r.text, re.S)
    name = m.group(1).strip() if m else fid
    files = re.findall(
        r'<a href="https://drive\.google\.com/file/d/([-\w]{25,})"[^>]*>.*?flip-entry-title">([^<]*)',
        r.text, re.S)
    docs = re.findall(
        r'<a href="https://docs\.google\.com/\w+/d/([-\w]{25,})"[^>]*>.*?flip-entry-title">([^<]*)',
        r.text, re.S)
    folders = re.findall(
        r'<a href="https://drive\.google\.com/drive/folders/([-\w]{25,})"[^>]*>.*?flip-entry-title">([^<]*)',
        r.text, re.S)
    return name, (files, docs, folders)


def walk(sess, fid, path, depth=0, out=None, max_depth=30):
    if out is None:
        out = {"folders": [], "files": [], "native": []}
    if depth > max_depth:
        return out
    name, kids = embedded_items(sess, fid)
    if kids is None:
        print(f"  [warn] no_http {path} ({fid})", file=sys.stderr, flush=True)
        return out
    files, docs, folders = kids
    out["folders"].append({"id": fid, "path": path, "name": name})
    for fid2, fname in files:
        out["files"].append({"id": fid2, "path": path, "name": fname, "bytes": None})
    for fid2, fname in docs:
        out["native"].append({"id": fid2, "path": path, "name": fname})
    seen = set()
    for fid2, child_name in folders:
        if fid2 == fid or fid2 in seen:
            continue
        seen.add(fid2)
        walk(sess, fid2, f"{path}/{child_name}", depth + 1, out, max_depth)
    time.sleep(0.2)
    return out


class SizeWorker:
    def __init__(self):
        self.s = new_sess()

    def size(self, fid):
        try:
            with self.s.get(
                f"https://drive.google.com/uc?export=download&id={fid}",
                headers={"Range": "bytes=0-0"},
                timeout=25, allow_redirects=True, stream=True,
            ) as r:
                cr = r.headers.get("Content-Range")
                if cr and "/" in cr:
                    return fid, int(cr.split("/")[-1])
                cl = r.headers.get("Content-Length")
                if cl and r.status_code in (200, 206):
                    return fid, int(cl)
                return fid, None
        except requests.RequestException:
            return fid, None


def fmt_bytes(n):
    if n is None:
        return "???"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.2f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="ID o URL de la carpeta compartida")
    ap.add_argument("--out", default=".", help="directorio de salida")
    ap.add_argument("--threads", type=int, default=24)
    args = ap.parse_args()

    fid = args.folder.rstrip("/").split("/")[-1]
    t0 = time.time()
    s = new_sess()
    print("Paso 1: estructura (embeddedfolderview)...", file=sys.stderr)
    tree = walk(s, fid, "ROOT")
    n = len(tree["files"])
    print(f"  carpetas={len(tree['folders'])} archivos={n} "
          f"nativos={len(tree['native'])} ({time.time()-t0:.0f}s)", file=sys.stderr)

    print(f"Paso 2: tamanos Range paralelo ({args.threads} hilos)...", file=sys.stderr)
    workers = [SizeWorker() for _ in range(args.threads)]
    sizes = {}
    done = 0
    t1 = time.time()
    with cf.ThreadPoolExecutor(max_workers=args.threads) as ex:
        futs = [ex.submit(workers[i % args.threads].size, f["id"])
                for i, f in enumerate(tree["files"])]
        for fut in cf.as_completed(futs):
            id2, sz = fut.result()
            sizes[id2] = sz
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{n} ({time.time()-t1:.0f}s)", file=sys.stderr)
    total = 0
    missing = 0
    for f in tree["files"]:
        sz = sizes.get(f["id"])
        f["bytes"] = sz
        if sz:
            total += sz
        else:
            missing += 1

    # desglose por tematica nivel 1
    by_top = {}
    for f in tree["files"]:
        parts = f["path"].split("/")
        key = parts[1] if len(parts) > 1 else "(raiz)"
        b = by_top.setdefault(key, [0, 0])
        b[0] += 1
        b[1] += f["bytes"] or 0

    print("\n=== RESUMEN ===")
    print(f"Carpetas     : {len(tree['folders'])}")
    print(f"Archivos     : {n}  (sin tamano: {missing})")
    print(f"Docs nativos : {len(tree['native'])} (se exportan a pdf/docx)")
    print(f"TAMANO TOTAL : {fmt_bytes(total)} ({total:,} bytes)")
    print(f"Tiempo total : {time.time()-t0:.0f}s")

    json.dump({"root": fid, **tree, "total_bytes": total,
               "total_human": fmt_bytes(total)},
              open(f"{args.out}/inventario_completo.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nJSON: {args.out}/inventario_completo.json")

    print("\n=== TAMANO POR CARPETA NIVEL 1 (desc) ===")
    for top, (cnt, sz) in sorted(by_top.items(), key=lambda x: -x[1][1]):
        print(f"  {fmt_bytes(sz):>10}  {cnt:>4}  {top}")


if __name__ == "__main__":
    main()
