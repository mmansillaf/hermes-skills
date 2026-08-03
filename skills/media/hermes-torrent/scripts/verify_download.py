#!/usr/bin/env python3
"""
verify_download.py — Verifica integridad SHA-256 de un archivo descargado.

Uso:
    python verify_download.py <ruta_archivo> [hash_esperado]

Ejemplos:
    python verify_download.py ./ubuntu-22.04.iso
    python verify_download.py ./ubuntu-22.04.iso a1b2c3d4...

Retorna exit code 0 si el hash coincide, 1 si no.
"""

import hashlib
import sys
import os


def sha256sum(file_path: str) -> str:
    """Calcula SHA-256 de un archivo en chunks de 64KB."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def main():
    if len(sys.argv) < 2:
        print("Uso: python verify_download.py <ruta_archivo> [hash_esperado]")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.isfile(file_path):
        print(f"ERROR: Archivo no encontrado: {file_path}")
        sys.exit(1)

    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"Verificando: {file_path}")
    print(f"Tamano: {size_mb:.2f} MB")
    print(f"Calculando SHA-256... ", end="", flush=True)

    computed = sha256sum(file_path)
    print(f"{computed}")

    if len(sys.argv) >= 3:
        expected = sys.argv[2].lower()
        if computed == expected:
            print(f"ESTADO: HASH COINCIDE — Archivo integro")
            sys.exit(0)
        else:
            print(f"ESTADO: HASH NO COINCIDE")
            print(f"  Esperado: {expected}")
            print(f"  Obtenido: {computed}")
            sys.exit(1)
    else:
        print("(no se proporciono hash para comparar)")
        sys.exit(0)


if __name__ == "__main__":
    main()