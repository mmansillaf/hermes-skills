#!/usr/bin/env python3
"""CLI interactivo para consultar El Peruano RAG via API.
Uso: python3 consultar.py
Variables de entorno: ELPERUANO_API (default: http://localhost:8000)
                      ELPERUANO_PROFILE (default: abogado)"""
import requests, sys, os

API = os.environ.get("ELPERUANO_API", "http://localhost:8000")
PROFILE = os.environ.get("ELPERUANO_PROFILE", "abogado")

try:
    r = requests.get(f"{API}/health", timeout=5)
    if r.status_code != 200:
        print(f"API no disponible en {API}")
        sys.exit(1)
    health = r.json()
except:
    print(f"No se pudo conectar a {API}")
    print("Ejecuta: python3 api_rest.py")
    sys.exit(1)

print(f"""
╔══════════════════════════════════════════════╗
║  EL PERUANO RAG v3.0 — Consulta Legal       ║
║  API: {API:<34s} ║
║  SQLite: {health['services']['sqlite']:<32s} ║
║  Perfil: {PROFILE:<34s} ║
║  Escribe 'salir' para terminar              ║
╚══════════════════════════════════════════════╝
""")

while True:
    try:
        q = input("\n📝 Consulta: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nHasta pronto!")
        break
    
    if not q: continue
    if q.lower() in ('salir', 'exit', 'quit', 'q'):
        print("Hasta pronto!")
        break
    
    print("Buscando...", end="\r")
    try:
        resp = requests.post(f"{API}/query", json={
            "question": q, "profile": PROFILE, "top_k": 10
        }, timeout=90)
        r = resp.json()
        
        conf = r.get("confidence", 0)
        ans = r.get("answer", "Sin respuesta")
        sources = r.get("sources", {})
        sql_n = sources.get("sqlite", {}).get("count", 0)
        web = r.get("web_fallback_used", False)
        
        if conf >= 0.70: c = "🟢"
        elif conf >= 0.40: c = "🟡"
        else: c = "🔴"
        
        print(f"{c} Confianza: {conf:.0%} | Fuentes: SQLite={sql_n} | Web={web}")
        print(f"{'─'*60}")
        print(ans)
        print(f"{'─'*60}")
        
    except Exception as e:
        print(f"Error: {e}")
