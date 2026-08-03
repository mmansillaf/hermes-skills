#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════╗
║  Torrent CLI - Búsqueda interactiva por terminal ║
║  Dependencias: pip install torrfetch            ║
║  Uso:        python3 scripts/torrent_cli.py      ║
╚══════════════════════════════════════════════════╝
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import torrfetch
except ImportError:
    print("❌ torrfetch no instalado. Ejecuta: pip install torrfetch")
    sys.exit(1)

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

SCRIPT_DIR = Path(__file__).parent.absolute()
RESULTS_DIR = SCRIPT_DIR / ".." / "results"
RESULTS_DIR = RESULTS_DIR.resolve()
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Utilidades ──

def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def formatear_tamano(size_str: str) -> str:
    if not size_str or size_str == "Unknown":
        return "—"
    return size_str


def truncar(texto: str, max_len: int = 80) -> str:
    if len(texto) > max_len:
        return texto[:max_len-3] + "..."
    return texto


# ── Búsqueda ──

def buscar(query: str, min_seeders: int = 1, max_results: int = 20) -> list[dict]:
    try:
        results = torrfetch.search_torrents(query, mode="parallel")
    except Exception as e:
        print(f"\n  ⚠️ Error en búsqueda: {e}")
        return []

    clean = []
    for r in results:
        seeders = r.get("seeders", 0)
        if isinstance(seeders, str):
            try:
                seeders = int(seeders)
            except ValueError:
                seeders = 0
        if seeders < min_seeders:
            continue
        clean.append({
            "titulo": r.get("title", "Sin título"),
            "tamaño": formatear_tamano(r.get("size", "")),
            "seeders": seeders,
            "leechers": r.get("leechers", 0),
            "magnet": r.get("magnet", ""),
            "fuente": r.get("source", "?"),
            "subido": r.get("uploaded", ""),
            "categoria": r.get("category", ""),
        })
        if len(clean) >= max_results:
            break
    return clean


# ── Mostrar ──

def mostrar_resultados(results: list[dict], query: str):
    if not results:
        print(f"\n  😕 No se encontraron resultados para '{query}'")
        return
    print(f"\n  ── 🔍  Resultados para \"{query}\"  ──\n")
    for i, r in enumerate(results, 1):
        print(f"  {i:>2}. {truncar(r['titulo'], 75)}")
        print(f"      📦 {r['tamaño']}  👤 {r['seeders']}S/{r['leechers']}L  🏷️ {r['categoria'][:30]}")
        print(f"      🔗 {r['fuente']}  📅 {r['subido']}")
        print()
    print(f"  ✅ {len(results)} resultados encontrados")


# ── Acciones ──

def copiar_magnet(magnet: str):
    import pyperclip as _pc
    if HAS_CLIPBOARD:
        _pc.copy(magnet)
        print("  ✅ Magnet copiado al portapapeles")
    else:
        print("  📋 Magnet (cópialo manualmente):")
        print(f"  {magnet}")


def guardar_magnet(magnet: str, titulo: str, archivo: str = None):
    if archivo is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = str(RESULTS_DIR / f"magnets_{ts}.txt")
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(f"# {titulo}\n{magnet}\n\n")
    print(f"  ✅ Magnet guardado en: {archivo}")
    return archivo


def guardar_todos_magnets(results: list[dict]):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = str(RESULTS_DIR / f"magnets_todos_{ts}.txt")
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(f"# Torrents exportados: {ts}\n")
        f.write(f"# Total: {len(results)} resultados\n\n")
        for r in results:
            f.write(f"# {r['titulo']}\n")
            f.write(f"# Tamaño: {r['tamaño']} | Seeders: {r['seeders']}\n")
            f.write(f"{r['magnet']}\n\n")
    print(f"\n  ✅ {len(results)} magnets guardados en: {archivo}")
    return archivo


def guardar_json(resultado: dict):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = resultado["titulo"][:40].replace("/", "_").replace(" ", "_")
    archivo = str(RESULTS_DIR / f"torrent_{nombre}_{ts}.json")
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Info guardada en: {archivo}")


def descargar_torrent(magnet: str, titulo: str):
    # Intento 1: qBittorrent API (Docker)
    try:
        import qbittorrentapi
        client = qbittorrentapi.Client(
            host="127.0.0.1", port=8081,
            username="admin", password="adminadmin"
        )
        client.auth_log_in()
        client.torrents_add(urls=magnet)
        print(f"  ✅ Torrent enviado a qBittorrent (Docker)")
        print(f"     Monitorea en: http://127.0.0.1:8081")
        return True
    except Exception:
        pass

    # Intento 2: Cliente del sistema (Windows/WSL)
    try:
        if sys.platform == "win32" or "microsoft" in os.uname().release.lower():
            subprocess.run(["cmd.exe", "/c", "start", "", magnet], capture_output=True, timeout=5)
            print(f"  ✅ Magnet abierto en el cliente torrent de Windows")
            return True
        elif sys.platform == "darwin":
            subprocess.run(["open", magnet], capture_output=True, timeout=5)
            print(f"  ✅ Magnet abierto en el cliente torrent de macOS")
            return True
        else:
            subprocess.run(["xdg-open", magnet], capture_output=True, timeout=5)
            print(f"  ✅ Magnet abierto en el cliente torrent")
            return True
    except Exception:
        pass

    # Intento 3: Archivo .magnet de respaldo
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = titulo[:50].replace("/", "_").replace(" ", "_")
    archivo = str(RESULTS_DIR / f"{nombre}_{ts}.magnet")
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(magnet)
    print(f"  ✅ Archivo .magnet creado: {archivo}")
    print(f"     Ábrelo con tu cliente torrent (qBittorrent, Transmission, etc.)")
    return True


# ── Menú de acciones ──

def menu_acciones(resultado: dict):
    while True:
        print(f"\n  ── Acciones para \"{truncar(resultado['titulo'], 55)}\" ──")
        print(f"     📦 {resultado['tamaño']}  👤 {resultado['seeders']}S/{resultado['leechers']}L\n")
        print("  [1] 📋 Copiar magnet al portapapeles")
        print("  [2] 💾 Guardar magnet en archivo")
        print("  [3] 📄 Guardar info completa (JSON)")
        print("  [4] ⬇️  DESCARGAR torrent")
        print("  [V] ← Volver a resultados\n")

        opcion = input("  > ").strip().lower()
        if opcion == "1":
            copiar_magnet(resultado["magnet"])
        elif opcion == "2":
            guardar_magnet(resultado["magnet"], resultado["titulo"])
        elif opcion == "3":
            guardar_json(resultado)
        elif opcion == "4":
            descargar_torrent(resultado["magnet"], resultado["titulo"])
        elif opcion in ("v", "volver"):
            break
        else:
            print("  ⚠️ Opción inválida")


# ── Menú principal ──

def menu_principal():
    limpiar_pantalla()
    print("╔══════════════════════════════════════════╗")
    print("║       🔍 Torrent CLI - Buscador P2P      ║")
    print("║   python3 scripts/torrent_cli.py         ║")
    print("╚══════════════════════════════════════════╝")

    results = []
    while True:
        if not results:
            query = input("\n  🔎 Término de búsqueda (o Q para salir): ").strip()
            if query.lower() in ("q", "quit", "salir", "exit"):
                print("\n  👋 Hasta luego!")
                break
            if not query:
                continue
            print(f"\n  🔍 Buscando \"{query}\"...")
            results = buscar(query)
            if not results:
                print(f"\n  😕 Sin resultados para \"{query}\"")
                continue
            mostrar_resultados(results, query)

        print(f"\n  Opciones:")
        print(f"  [1-{len(results)}]  Ver detalles / acciones del resultado")
        print(f"  [S]    💾 Guardar TODOS los magnets")
        print(f"  [N]    🔎 Nueva búsqueda")
        print(f"  [Q]    🚪 Salir\n")

        opcion = input("  > ").strip().lower()
        if opcion == "s":
            guardar_todos_magnets(results)
        elif opcion == "n":
            results = []
        elif opcion == "q":
            print("\n  👋 Hasta luego!")
            break
        elif opcion.isdigit():
            idx = int(opcion) - 1
            if 0 <= idx < len(results):
                menu_acciones(results[idx])
            else:
                print(f"  ⚠️ Número inválido (1-{len(results)})")
        else:
            print("  ⚠️ Opción inválida")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n  👋 Interrumpido. Hasta luego!")
        sys.exit(0)
