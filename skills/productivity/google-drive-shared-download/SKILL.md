---
name: google-drive-shared-download
description: "Use when downloading a shared Google Drive folder link."
version: 1.0.0
author: hermes-curator
license: MIT
platforms: [linux, macos, windows]
---

# Google Drive Shared Folder — Inventario y Descarga sin OAuth

Cuando el usuario da un link de carpeta compartida de Google Drive ("cualquiera
con el link") y pide saber qué contiene, cuánto pesa, o descargarla **no hace
falta OAuth** — se resuelve con gdown + los endpoints web anónimos. El setup
OAuth del skill `google-workspace` solo se necesita para acceder a contenido
privado de la cuenta.

## Flujo

1. **Leer el link.** Si está en un `.env`, `read_file` lo bloquea (archivo de
   credenciales). Leerlo vía terminal cuando el usuario lo pidió explícitamente:
   `sed 's/\(.\{80\}\).*/\1.../' .env` (enmascara por si hay secretos) o `cat`.

2. **Verificar acceso anónimo** (1 request):
   `curl -sL "https://drive.google.com/drive/folders/<FID>" -A "<UA Chrome>" -o /dev/null -w "%{http_code}"`
   - `200` → público, se puede todo sin login.
   - `403`/login → requiere OAuth (google-workspace) o cookies.

3. **Inventariar estructura** — usar SIEMPRE `embeddedfolderview`, NUNCA el
   JSON `_DRIVE_ivd` de la página normal:
   - Completo: `https://drive.google.com/embeddedfolderview?id=<FID>` lista
     TODOS los hijos (archivos, docs nativos, subcarpetas) en un HTML plano.
     Los nombres de carpeta van en `<div class="flip-entry-title">NOMBRE</div>`
     dentro del `<a>` — no directamente en el texto del anchor.
   - PITFALL (verificado): `window['_DRIVE_ivd']` de la página de carpeta
     PAGINA a ~50 ítems por carpeta. En "Maletín Jurídico 2025" dio 1252
     archivos; el real con embeddedfolderview fue 2208. Nunca confiar en
     `_DRIVE_ivd` para conteos. (Su único uso: entry[13] = tamaño en bytes
     de archivos, útil para un vistazo rápido.)
   - Recorrer recursivamente con ~0.2s de sleep entre carpetas (cortesía).

4. **Medir tamaños sin descargar** — truco HTTP Range:
   `GET https://drive.google.com/uc?export=download&id=<FID>` con header
   `Range: bytes=0-0` → respuesta `206` con `Content-Range: bytes 0-0/TOTAL`.
   El TOTAL es el tamaño exacto en bytes. ~2-6s por request con conexión
   nueva; paralelizar con `ThreadPoolExecutor` (24 workers, una Session por
   worker con keep-alive) → ~100 archivos/15s.
   - Archivos >~100MB devuelven página HTML "Virus scan warning" en vez de
     206 → su tamaño exacto solo se sabrá al descargar (gdown lo resuelve).

5. **Descargar** con gdown (ya instalado en WSL del usuario, v6.x):
   `gdown --folder <URL_o_FID> -O <destino>`
   - Recursivo, maneja las confirmaciones anti-virus, tiene `resume`.
   - **PoC antes de la descarga completa**: bajar 1 archivo pequeño y verificar
     que el tamaño resultante coincide con el medido (sanidad + estimar
     velocidad → ETA = total / velocidad PoC).

6. **Entregar** (preferencias del usuario): inventario JSON + informe .txt
   plano (sin markdown), desglose por carpeta temática, top de archivos
   grandes, notas de alcance (cuántos archivos quedaron sin medir y por qué).
   Pedir aprobación antes de lanzar la descarga completa de GB.

## Script

- `scripts/inventory_gdrive.py` — inventario completo listo para correr:
  estructura (embeddedfolderview recursivo) + tamaños (Range paralelo) →
  JSON + informe .txt.

## Pitfalls

- `_DRIVE_ivd` pagina a 50 → subestima totales. embeddedfolderview es la fuente completa.
- Nombres de subcarpeta en embeddedfolderview: extraer del `flip-entry-title`, no del texto del anchor.
- Construir rutas con el nombre del HIJO, no del padre (bug de concatenación que duplica el nombre raíz en el árbol).
- Los endpoints web de Drive son sensibles a rate-limit con UA de navegador; mantener sleeps y reintentos.
- gdown `download_folder(id=..., skip_download=True)` lista los archivos sin bajar (útil como cross-check del conteo), pero no trae tamaños.
