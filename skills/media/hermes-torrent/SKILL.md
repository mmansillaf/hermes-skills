---
name: hermes-torrent
description: "Integracion de Hermes Agent con la red BitTorrent mediante MCP Server + qBittorrent + VPN/I2P. Permite busquedas automatizadas y descarga segura de archivos P2P."
version: 1.4.0
author: Hermes Agent
platforms: [linux, macos, wsl]
metadata:
  hermes:
    tags: [torrent, bittorrent, p2p, mcp, download, automation]
    related_skills: [mcp-server-authoring, native-mcp, mcporter]
---

# Hermes Torrent Skill

## Descripcion

Este skill dota a Hermes Agent de la capacidad de buscar y descargar archivos de la red BitTorrent de forma segura, anonima y automatizada mediante un MCP Server dedicado (el approach mas potente y el unico implementado actualmente).

Para una comparacion detallada de los **5 approaches alternativos** (Skill.md, scraper script, torrent-search-mcp, torrfetch, @register_tool) y el estado de implementacion real, ver `references/kimi-5-approaches-comparison.md`.

## Available Approaches (5 opciones de integracion)

| # | Approach | Complejidad | Seguridad | Estado | Cuando usarlo |
|---|----------|-------------|-----------|--------|---------------|
| 1 | **Hermes Skill** (SKILL.md con tools MCP) | Baja | Alta | ✅ Creado + integrado | Flujo completo con descarga via MCP |
| 2 | **Script Python + terminal/execute_code** (torrfetch) | **Minima** | Baja | ✅ Creado y probado | Busqueda rapida sin infraestructura Docker |
| 3 | **torrent-search-mcp** (philogicae/torrent-search-mcp) | Media | Media | ⚠️ No evaluado | Evaluar antes de custom MCP |
| 4 | **torrfetch directo** (`pip install torrfetch`) | **Minima** | Baja | ✅ Instalado y probado (v0.1.5) | Busqueda P2P en 1 linea de Python |
| 5 | **@register_tool nativa** (Registry de Hermes) | Alta | Media | 🟡 No prioritario | MCP SDK lo cubre mejor |

**⚠️ Decision arquitectonica**: El approach #2 (script torrfetch) es el camino mas rapido para busqueda funcional SIN docker. El #1 (MCP) es para produccion con descarga real. Elegir segun necesidad — no sobreingenieriar.

## Implementation Status (Julio 2026 — COMPLETADO)

| Componente | Estado | Ruta |
|-----------|--------|------|
| **MCP Server custom (6 tools)** | ✅ Completo (536 lines, SDK moderno) | `mcp/mcp_torrent_server.py` |
| Docker stack (Gluetun+qBittorrent+Prowlarr+ClamAV) | ✅ docker-compose.yml creado | `docker-compose.yml` |
| Config en Hermes config.yaml | ✅ `mcp_servers.torrent` configurado | `~/.hermes/config.yaml` |
| SKILL.md de integracion | ✅ Creado | `SKILL.md` en proyecto |
| torrfetch (busqueda P2P directa) | ✅ Instalado v0.1.5 + probado | `pip install torrfetch` |
| Script de busqueda torrfetch | ✅ Creado y probado | `scripts/torrent_search.py` |
| **CLI interactivo** (menu acciones) | ✅ Creado v1.0 | `scripts/torrent_cli.py` |
| Bug fix: MCP server SDK API | ✅ `app.run(transport='stdio')`→`stdio_server()` | Fix aplicado en ambos paths |
| Reporte final de integracion | ✅ Completo | `report/informe-final-hermes-torrent.md` |
| Reporte completo de arquitectura | ✅ Referencia | `report/informe-integracion-hermes-bittorrent.md` |

### Nota sobre las 5 opciones de Kimi
El documento original de Kimi proponia 5 approaches. Estado real:
1. **Skill de Hermes (SKILL.md)** → ✅ Creado
2. **Script Python + execute_code** → ✅ Creado (scripts/torrent_search.py con torrfetch)
3. **torrent-search-mcp existente** → ✅ CUBIERTO (MCP server custom es superior)
4. **torrfetch (pip install)** → ✅ Instalado y probado con datos reales
5. **@register_tool nativa** → 🟡 No prioritario (MCP SDK lo cubre mejor)

### Tests realizados
- MCP Server: Initialize OK, 6 tools listadas, search/get_status/verify graceful errors ✅
- torrfetch: `"ubuntu"` → 30 resultados, top con 25 seeders ✅
- torrfetch: `"linux"` → 30 resultados, top con 15 seeders ✅
- torrfetch: `"email list"` → 10 resultados (mayoria 0 seeders — listas de correos muertas) ⚠️
- torrfetch: `"email database"` → 0 resultados

## Arquitectura

```
Usuario (CLI/Telegram) → Hermes Agent → MCP Server (gateway) → qBittorrent → VPN/I2P → Red P2P
```

- **Hermes Agent**: Orquesta las operaciones, recibe instrucciones del usuario
- **MCP Server**: Gateway que expone tools de busqueda, descarga, monitoreo
- **qBittorrent**: Cliente BitTorrent headless con Web API
- **Gluetun**: Contenedor VPN con kill switch integrado (todo trafico P2P por VPN)
- **Prowlarr**: Gestor de indexadores para busqueda unificada
- **ClamAV**: Escaneo antivirus post-descarga

## Pre-requisitos

1. Docker y Docker Compose instalados
2. VPN activa (Mullvad, ProtonVPN, NordVPN, etc.) con clave WireGuard
3. Python 3.10+ con `pip install qbittorrent-api requests`
4. Hermes Agent v0.18.0+

## Instalacion

### 1. Estructura del proyecto

```bash
# El proyecto vive en D:\\PyCode\\hermes-skills\\torrent\\ (WSL: /mnt/d/PyCode/hermes-skills/torrent/)
ls -la /mnt/d/PyCode/hermes-skills/torrent/
# → bit*.txt  mcp/mcp_torrent_server.py  report/  scripts/  config/  downloads/  quarantine/
```

**⚠️ Ruta WSL**: Si Hermes corre desde WSL, la ruta del MCP Server en config.yaml debe ser:
```yaml
args: ["/mnt/d/PyCode/hermes-skills/torrent/mcp/mcp_torrent_server.py"]
```

### 2. Configurar credenciales

```bash
cp ~/hermes-torrent/.env.example ~/hermes-torrent/.env
# Editar .env con tus credenciales VPN y qBittorrent
nano ~/hermes-torrent/.env
```

### 3. Iniciar el stack Docker

```bash
cd ~/hermes-torrent
docker compose up -d
# Verificar que la IP de salida es la VPN:
docker compose exec qbittorrent curl -s ifconfig.me
```

### 4. Configurar Prowlarr

1. Abrir http://127.0.0.1:9696 en navegador
2. Anadir indexadores (YTS, 1337x, TorrentGalaxy, etc.)
3. Copiar API Key de Settings > General
4. Anadir en `.env`: `PROWLARR_API_KEY=tu_key`

### 5. Configurar qBittorrent

1. Abrir http://127.0.0.1:8080 (user: admin / pass: adminadmin)
2. Cambiar contrasena en Tools > Options > Web UI
3. Configurar en `.env` la nueva contrasena

### 6. Instalar dependencias Python

```bash
pip install qbittorrent-api requests
```

### 7. Configurar Hermes (ver seccion Configuracion)

### 8. Verificar conexion

```bash
hermes chat
/tools   # Deberias ver torrent-search_torrents, torrent-add_magnet, etc.
```

## Tools disponibles (vía MCP)

| Tool | Descripcion |
|------|-------------|
| `torrent-search_torrents` | Busca torrents por termino en Prowlarr. Filtra por seeders. |
| `torrent-add_magnet` | Anade magnet link a qBittorrent para descarga. |
| `torrent-get_status` | Estado de todas las descargas activas. |
| `torrent-get_torrent_info` | Info detallada de un torrent por hash. |
| `torrent-set_seed_limits` | Configura limites de ratio/tiempo de seeding. |
| `torrent-verify_download` | Verifica integridad SHA-256 de archivo descargado. |

## Flujo tipico de uso

```
Usuario > "Busca Ubuntu 22.04 ISO y descargalo"
  → Hermes llama torrent-search_torrents(query="ubuntu 22.04 iso", min_seeders=10)
  → Muestra resultados al usuario
  → Usuario confirma seleccion
  → Hermes llama torrent-add_magnet(magnet="magnet:?...")
  → Hermes monitorea con torrent-get_status
  → Al completar: torrent-verify_download(file_path="/downloads/...", expected_hash="...")
  → Hermes reporta resultado
```

## Configuracion de Hermes (~/.hermes/config.yaml)

```yaml
mcp_servers:
  torrent:
    command: python
    args: ["/mnt/d/PyCode/hermes-skills/torrent/mcp/mcp_torrent_server.py"]
    env:
      QBT_HOST: "127.0.0.1"
      QBT_PORT: "8080"
      QBT_USER: "admin"
      QBT_PASS: "${QBITTORRENT_PASS}"
      PROWLARR_API_KEY: "${PROWLARR_API_KEY}"
      PROWLARR_URL: "http://127.0.0.1:9696"
      TORRENT_SAVE_PATH: "/downloads/hermes"
```

**⚠️ Pitfall de ruta**: Si clonas el proyecto a otro lado, actualiza el `args:` en config.yaml. La ruta debe ser absoluta. Las credenciales se almacenan seguras con:

```bash
hermes secret set QBITTORRENT_PASS "tu_contrasena"
hermes secret set PROWLARR_API_KEY "tu_api_key"
```

## Configuracion de seguridad en qBittorrent

1. Anonymous Mode: ON (Tools > Options > Advanced > Anonymous mode)
2. Encryption: Required (Tools > Options > BitTorrent > Encryption mode)
3. Proxy: Configurar solo si NO usas Gluetun (Tools > Options > Connection)
4. Seeding limits: Ratio 1.0, tiempo 1440 min (24h)
5. Blocklist: Habilitar y auto-actualizar (Tools > Options > Advanced)
6. Desactivar UPnP/NAT-PMP (Tools > Options > Connection)
7. Puerto entrante: Aleatorio, no 6881

## Verificacion de seguridad

```bash
# 1. Verificar que la IP de salida es la VPN (NO tu IP real)
docker compose exec qbittorrent curl -s ifconfig.me

# 2. Verificar kill switch (detener VPN y verificar que el trafico se corta)
docker compose stop gluetun
docker compose exec qbittorrent curl -s --max-time 5 ifconfig.me  # debe fallar
docker compose start gluetun

# 3. Verificar que WebUI solo escucha en localhost
curl -s http://127.0.0.1:8080 > /dev/null && echo "OK: localhost accesible"
curl -s http://HOST_IP:8080 > /dev/null 2>&1 && echo "FALLA: debe rechazar conexion externa"
```

## Migracion a I2P (para maxima privacidad)

1. Anadir contenedor i2pd:
```yaml
  i2pd:
    image: purplei2p/i2pd:latest
    container_name: hermes_i2p
    volumes:
      - ./i2pd:/home/i2pd/data
```

2. Configurar qBittorrent para usar I2P (Tools > Options > Advanced > I2P)
3. Habilitar I2P en libtorrent (v2.1.0+ soporta i2p_pex)

## Solucion de problemas

| Problema | Causa | Solucion |
|----------|-------|----------|
| MCP server no conecta | Handshake incorrecto | Verificar que el server lee de stdin y escribe a stdout |
| Tools no aparecen en Hermes | Config mala en config.yaml | Revisar ruta y dependencias Python |
| IP real se filtra | network_mode no configurado | `network_mode: service:gluetun` OBLIGATORIO |
| Prowlarr sin resultados | API Key incorrecta | Verificar en Settings > General |
| Descarga no inicia | qBittorrent no autenticado | Verificar QBT_USER/QBT_PASS |
| MCP muere silenciosamente | Error en tool handler | Revisar stderr/logs de Hermes |

## Pitfalls descubiertos en produccion

### 1. qBittorrent genera password temporal aleatorio en primer arranque
La imagen `linuxserver/qbittorrent` NO usa `admin/adminadmin` por defecto.
En el primer arranque genera una password temporal aleatoria y la escribe en los logs.

**Sintoma:** MCP server falla con "Login failed" al conectar a qBittorrent.

**Solucion:**
```bash
# 1. Obtener la password temporal de los logs
docker logs hermes_torrent 2>&1 | grep "temporary password"

# 2. Login con la password temporal
TOKEN=$(curl -s -c /tmp/qbt_cookies.txt http://127.0.0.1:8081/api/v2/auth/login \
  -d "username=admin&password=TEMPORAL_PASS")

# 3. Cambiar a una password permanente
curl -s -b /tmp/qbt_cookies.txt http://127.0.0.1:8081/api/v2/app/setPreferences \
  -d 'json={"web_ui_password":"adminadmin"}'

# 4. Verificar que funciona
curl -s http://127.0.0.1:8081/api/v2/auth/login \
  -d "username=admin&password=adminpassword"
```

### 2. Indexadores Cardigann fallan con 500 via API Prowlarr (fileKey null)
Al agregar indexadores como 1337x, YTS, The Pirate Bay via API REST de Prowlarr,
fallan con `500: Value cannot be null (Parameter 'fileKey')`. Esto ocurre porque
las definiciones Cardigann no estan cacheadas en el contenedor.

**Sintoma:** `POST /api/v1/indexer` devuelve 500 con `ArgumentNullException: fileKey`.

**Solucion:**
- **Alternativa A**: Usar indexadores no-Cardigann via API. Funcionan sin cache:
  - `Anidex` (anime) ✅ probado
  - `Knaben` (meta-search) — pendiente de probar
- **Alternativa B**: Agregar indexadores manualmente desde el navegador:
  Abrir `http://localhost:9696`, Indexers > Add Indexer > buscar y agregar.
  La UI web descarga las definiciones Cardigann correctamente.

### 3. Puerto 8080 ocupado por otros servicios
El puerto por defecto de qBittorrent (8080) suele estar ocupado por otros
servicios (Dify, Nginx, etc.).

**Solucion:** Usar un puerto alternativo (ej: 8081):
```yaml
# docker-compose.yml
qbittorrent:
  environment:
    - WEBUI_PORT=8081
  ports:
    - "127.0.0.1:8081:8081"
```
Y reflejar el cambio en `~/.hermes/config.yaml`:
```yaml
mcp_servers:
  torrent:
    env:
      QBT_PORT: "8081"
```

## CLI Interactivo (torrent_cli.py)

Para uso directo desde terminal SIN Docker ni MCP:

```bash
cd /mnt/d/PyCode/hermes-skills/torrent
python3 scripts/torrent_cli.py
```

### Loop interactivo

1. Ingresas término → torrfetch busca en paralelo (PB, 1337x, etc.)
2. Resultados numerados con tamaño, seeders/leechers, categoría
3. Al seleccionar un resultado:

   | Opción | Acción |
   |--------|--------|
   | [1] | Copiar magnet al portapapeles (requiere pyperclip) |
   | [2] | Guardar magnet en archivo .txt |
   | [3] | Guardar info completa a JSON |
   | [4] | **Descargar** — intenta: qBittorrent API → cliente Windows → .magnet file |
   | [V] | Volver |

4. Desde pantalla principal: `[S]` guarda TODOS los magnets, `[N]` nueva búsqueda

### Dependencias
- `torrfetch` (obligatorio) — `pip install torrfetch`
- `pyperclip` (opcional, para portapapeles)
- `qbittorrent-api` (opcional, para descarga directa a Docker)

### Nota sobre resultados "email list" / listas de correos
En pruebas reales, búsquedas de `"email list"` devuelven ~10 resultados
pero casi todos con **0 seeders** (torrents muertos). No es viable para
obtener listas de correos vía P2P.

## Support Files

### References
- `references/kimi-5-approaches-comparison.md` — 5 approaches evaluados vs implementados
- `references/research-architecture-report.md` — Investigacion completa: stack, VPN vs I2P, BEP-52, seguridad post-descarga, mejores practicas

### Scripts
- `scripts/verify_download.py` — Verificacion SHA-256 de archivos descargados. Uso: `python verify_download.py <file> [expected_hash]`
- `scripts/torrent_cli.py` — CLI interactivo para busqueda + descarga desde terminal. Uso: `python scripts/torrent_cli.py`

### Templates
- `templates/docker-compose.yml` — Stack completo Docker (Gluetun + qBittorrent + Prowlarr + ClamAV)

### Cross-reference
- `report/informe-integracion-hermes-bittorrent.md` — Reporte original de investigacion
- **mcp-server-authoring skill** — Como construir MCP servers desde cero
- **mcp-server-development skill** — Alternativa MCP server building