#!/usr/bin/env python3
"""
consultar.py — Cliente simple para El Peruano RAG API
Uso:
  python3 consultar.py "pregunta" [perfil] [servidor]
  python3 consultar.py                        # modo interactivo

Ejemplos:
  python3 consultar.py "Ley 32108"
  python3 consultar.py "¿Cuántas RM en 2024?" fiscal
  python3 consultar.py "teletrabajo" ciudadano 192.168.18.217
"""

import urllib.request
import urllib.error
import json
import sys
import os

SERVIDOR = os.environ.get("PERUANO_HOST", "192.168.18.217")
PUERTO = os.environ.get("PERUANO_PORT", "8000")
TIMEOUT = 50

G = '\033[0;32m'
C = '\033[0;36m'
Y = '\033[1;33m'
R = '\033[0;31m'
N = '\033[0m'

def consultar(pregunta, perfil="abogado", top_k=5):
    url = f"http://{SERVIDOR}:{PUERTO}/query"
    datos = json.dumps({"question": pregunta, "profile": perfil, "top_k": top_k}).encode()
    req = urllib.request.Request(url, data=datos,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"{R}Error de conexión: {e.reason}{N}")
        return None
    except Exception as e:
        print(f"{R}Error: {e}{N}")
        return None

def mostrar_resultado(r):
    if not r:
        return
    answer = r.get("answer", "")
    conf = r.get("confidence", 0)
    tiempo = r.get("timing_ms", 0)
    n_results = len(r.get("results", []))
    router = r.get("sources", {}).get("router", {}).get("nivel", "?")
    count_data = r.get("sources", {}).get("sql_count")

    print(f"\n{G}{'='*60}{N}")
    if answer.startswith("[Error"):
        print(f"{R}{answer}{N}")
    else:
        print(answer)

    print(f"\n{C}{'─'*60}{N}")
    print(f"  Confianza: {Y}{conf:.0%}{N}  |  Tiempo: {tiempo}ms  |  "
          f"Fuentes: {n_results}  |  Router: {router}")

    if count_data:
        total = count_data.get("total", "?")
        print(f"  COUNT: {Y}{total}{N} normas  ", end="")
        bd = count_data.get("breakdown", [])
        if bd:
            parts = [f'{g["tipo_norma"]}: {g["cnt"]}' for g in bd[:3]]
            print(f"({', '.join(parts)})", end="")
        print()
    print(f"{C}{'─'*60}{N}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        return

    if len(sys.argv) > 1:
        pregunta = sys.argv[1]
        perfil = sys.argv[2] if len(sys.argv) > 2 else "abogado"
        if len(sys.argv) > 3:
            global SERVIDOR
            SERVIDOR = sys.argv[3]
        print(f"{C}🔍 {pregunta}  (perfil: {perfil}){N}")
        r = consultar(pregunta, perfil)
        mostrar_resultado(r)
        return

    print(f"{G}⚖️  El Peruano RAG — Cliente interactivo{N}")
    print(f"   Servidor: {SERVIDOR}:{PUERTO}")
    print(f"   'salir' para terminar, 'health' para estado\n")
    while True:
        try:
            q = input(f"{C}❓ {N}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Y}¡Hasta luego!{N}")
            break
        if not q:
            continue
        if q.lower() in ("salir", "exit", "quit", "q"):
            print(f"{Y}¡Hasta luego!{N}")
            break
        if q.lower() == "health":
            r = urllib.request.urlopen(f"http://{SERVIDOR}:{PUERTO}/health", timeout=5)
            h = json.loads(r.read())
            print(f"  Status: {G if h['status']=='ok' else R}{h['status']}{N}")
            for svc, state in h.get("services", {}).items():
                ok = "OK" in state
                print(f"  {svc}: {G if ok else R}{state}{N}")
            continue
        r = consultar(q, "abogado")
        mostrar_resultado(r)

if __name__ == "__main__":
    main()
