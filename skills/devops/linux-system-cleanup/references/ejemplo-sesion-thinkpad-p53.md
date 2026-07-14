# Ejemplo real: ThinkPad P53 (julio 2026)

## Estado inicial
- Disco: 233G total, 160G usados (73%), 62G libres
- RAM: 46 GB total, 4.1 GB usados

## Inventario — hallazgos principales

| Ruta | Tamaño | Categoría |
|---|---|---|
| `~/.cache/pip/` | 3.3 GB | Seguro |
| `~/.npm/` | 1.2 GB | Seguro |
| `~/.local/share/Trash/` | 5.8 GB | Seguro |
| `~/.cache/thumbnails/` | 25 MB | Seguro |
| `/var/log/journal` | 626 MB | Seguro (vacuum 7d) |
| `/var/cache/apt` | ~300 MB | Seguro |
| Kernel `6.17.0-29-generic` (inactivo) | ~400 MB | Seguro |
| `~/.cache/google-chrome/` | 4.4 GB | Requiere cerrar Chrome |
| `~/.cache/microsoft-edge/` | 1.6 GB | Requiere cerrar Edge |
| `Descargas/Microsoft_365*.pkg` | 3.1 GB | Decisión usuario (macOS, inservible) |
| `Descargas/*.deb` (instaladores) | ~570 MB | Decisión usuario |
| `~/.linkedin-mcp/` | 1.3 GB | **No tocar** (browser headless LinkedIn) |
| `~/.chrome_cej/` | 188 MB | **No tocar** (perfil Selenium CEJ) |

## Resultado post-limpieza segura
- Disco: 149G usados (68%), 73G libres
- 11.2 GB recuperados en lote seguro
- Kernel -29 eliminado por el usuario manualmente
