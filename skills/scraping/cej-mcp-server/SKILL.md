---
name: cej-mcp-server
description: "MCP server para controlar los spiders CEJ desde Hermes (WSL). HTTP transport. Tools: start, stop, status, logs, restart."
version: 1.0.0
author: mmansillaf
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cej, mcp, spider, judicial, peru]
    related_skills: [cej-peru-scraper, mcp-server-authoring, native-mcp]
---

# CEJ MCP Server

## Overview

MCP server que corre **nativamente en Windows** (HTTP transport) para controlar los spiders del CEJ (Poder Judicial del Perú) desde Hermes Agent en WSL.

Evita todos los problemas de stdio-through-WSL (buffering, encoding, orphan processes) usando HTTP transport.

## Arquitectura

```
 Windows (localhost:8765)                WSL (Hermes)
┌─────────────────────────┐     HTTP     ┌────────────────┐
│  cej_mcp_server.py      │◄───────────►│  config.yaml   │
│  (MCP SDK + Flask)      │   JSON-RPC  │  mcp_servers:  │
│                         │             │    cej:        │
│  Tools:                 │             │    url: ...    │
│   cej_start_spider      │             └────────────────┘
│   cej_stop_spider       │
│   cej_get_status        │
│   cej_get_logs          │
│   cej_restart_both      │
└─────────────────────────┘
```

## Estructura del proyecto

```
D:\PyCode\cej-mcp-server\
├── cej_mcp_server.py       # MCP server (HTTP transport, FastMCP)
├── requirements.txt        # mcp>=1.5.0
├── start_server.cmd        # Watchdog batch para inicio automatico
├── config.json             # Config: rutas, chrome paths, puerto
└── README.md
```

## Archivos de referencia

- `cej_mcp_server.py` — server completo con FastMCP + HTTP transport (usa `run_streamable_http_async()`)
- `start_server.cmd` — watchdog batch (UTF-8, unbuffered, auto-reinicio)
- `config.json` — config con rutas Windows (`http_host: "0.0.0.0"`)
- `references/run_streamable_http_fix.md` — fix del bug `mcp.run()` que muere silenciosamente con `Start-Process -WindowStyle Hidden`
- `scripts/run_mcp.ps1` — script PowerShell para iniciar el MCP server en background con verificación de logs

## Config del MCP server

```json
{
  "project_dir": "D:\\PyCode\\poder_judicial_results-PY-OK",
  "spider_dir": "DescargaPJ_optimizado\\poder_judicial_results",
  "venv_python": "D:\\PyCode\\poder_judicial_results-PY-OK\\venv\\Scripts\\python.exe",
  "chrome_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "api_key_env": "TWOCAPTCHA_API_KEY",
  \"http_host\": \"0.0.0.0\",\n  \"http_port\": 8765\n}\n```\n\nLa API key de 2captcha se lee de la variable de entorno del sistema Windows, NO está hardcodeada.\nEl host por defecto es `0.0.0.0` (todas las interfaces) para aceptar conexiones desde WSL.\n\n## Verificar que el server funciona\n\nEl server usa **FastMCP con StreamableHTTP transport** explicito (`run_streamable_http_async()`).\nCon `curl` normal (sin header SSE) responde error 406 JSON-RPC, lo cual CONFIRMA que funciona:\n\n```powershell\ncurl.exe http://127.0.0.1:8765/mcp\n# → {\"jsonrpc\":\"2.0\",...,\"Not Acceptable: Client must accept text/event-stream\"}\n```\n\nEse error 406 es NORMAL y esperado. Para verificar desde WSL, usar el header correcto\n+ la IP del gateway:\n\n```bash\nGW=$(ip route show default | awk '{print $3}')\ncurl -s -m 5 \"http://$GW:8765/mcp\" -H \"Accept: text/event-stream\"\n```

## Config en Hermes (~/.hermes/config.yaml)

```yaml
mcp_servers:
  cej:
    url: "http://localhost:8765/mcp"
    timeout: 120
    connect_timeout: 30
```

Requiere restart de Hermes para activarse.

## Tools MCP

### cej_start_spider(spider_id: "A" | "B")
Inicia el spider indicado. Puerto remote debugging: A=9222, B=9223.
Si Chrome no está abierto en el puerto correspondiente, falla con error claro.

### cej_stop_spider(spider_id: "A" | "B")
Mata el proceso Python del spider y Chrome asociado.

### cej_get_status()
Devuelve:
- Checkpoint A/B: count + último expediente
- Tasa éxito captcha por spider
- Carpetas documents count
- Procesos vivos (Chrome, Python)
- Tiempo estimado restante
- Timestamps de última actividad

### cej_get_logs(spider_id: "A" | "B", lines: 50 = 50)
Últimas N líneas del output del spider.

### cej_restart_both()
Mata ambos spiders, espera 5s, reinicia ambos.

## Setup de API Key (Windows)

La API key de 2captcha se lee de la variable de entorno `TWOCAPTCHA_API_KEY`.

**Opción A — Persistente (recomendado):**
```powershell
setx TWOCAPTCHA_API_KEY 1e563a7dfcc437d276d896fdebf88497
```
Luego cerrar y reabrir PowerShell. La variable persiste entre sesiones.

**Opción B — Solo para la sesión actual:**
```powershell
$env:TWOCAPTCHA_API_KEY="1e563a7dfcc437d276d896fdebf88497"
```

**Opción C — En el script de inicio:**
Editar `start_server.cmd` y agregar la línea:
```
set TWOCAPTCHA_API_KEY=1e563a7dfcc437d276d896fdebf88497
```

## Inicio en Windows

**Manual (para pruebas):**
```powershell
cd D:\PyCode\cej-mcp-server
python -u cej_mcp_server.py
```
Dejar la terminal abierta (el server corre en foreground).

**Con watchdog automático:**
```cmd
D:\PyCode\cej-mcp-server\start_server.cmd
```
El script reinicia el server automáticamente si se cae.

**Auto-inicio con Windows:**
`Win + R` → `shell:startup` → Crear acceso directo a:
```
C:\Windows\System32\cmd.exe /c D:\PyCode\cej-mcp-server\start_server.cmd
```

## Verificar que el server funciona

El server usa **FastMCP con StreamableHTTP transport**. NO responde a `curl` normal — la respuesta correcta a `curl -v http://127.0.0.1:8765/mcp` es que `curl` se quede esperando (el server no cierra la conexión hasta que recibe un mensaje JSON-RPC). Eso es NORMAL.

**Verificar desde Windows (PowerShell):**
```powershell
# Si netstat muestra el puerto escuchando, el server funciona
netstat -an | Select-String "8765"
# Deberías ver:  TCP    0.0.0.0:8765    LISTENING
```

**Verificar desde WSL que la red funciona:**
```bash
# Probar si el puerto está accesible (TCP connect, no HTTP)
timeout 3 bash -c 'echo > /dev/tcp/localhost/8765' 2>&1 && echo "OK" || echo "FALLA"
```

## Common Issues

### "ModuleNotFoundError: No module named 'mcp'"
El MCP SDK no está instalado en el Python de Windows. Solución:
```powershell
pip install mcp>=1.5.0 flask flask-cors
```

### MCP server no responde / Hermes no descubre las tools

**1. FastMCP no responde a HTTP plano — es normal.**
FastMCP usa StreamableHTTP: espera un mensaje JSON-RPC antes de responder. El `curl` se queda colgado o devuelve `exit 7`. No es un error. Usar `netstat` para verificar que el puerto escucha.

**2. WSL no puede conectar a localhost:8765**
Causas y soluciones:

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `curl: exit 7` | Firewall Windows bloquea | Desactivar Kaspersky/AVG/Windows Defender Firewall temporalmente |
| `Connection refused` | Server no está corriendo | Verificar terminal del server (Ctrl+C y reiniciar) |
| `No route to host` | WSL red aislada | Usar `127.0.0.1` en vez de `localhost` en `config.yaml` |

Herramientas de diagnóstico:
```bash
# Desde WSL
timeout 3 bash -c 'echo > /dev/tcp/localhost/8765' 2>&1 && echo "OK" || echo "FALLA"
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/8765' 2>&1 && echo "OK" || echo "FALLA"
```

```powershell
# Desde PowerShell (otra terminal)
netstat -an | Select-String "8765"
Test-NetConnection -ComputerName 127.0.0.1 -Port 8765
```

**3. Firewall de terceros (Kaspersky, AVG, Norton)**
Aunque la interfaz esté cerrada, el firewall del antivirus puede seguir activo como servicio de Windows. Solución: desactivar temporalmente desde el panel de control del antivirus (no solo cerrar la ventana), o agregar una regla de excepción para Python/puerto 8765.

**4. Windows Defender Firewall**
Agregar regla de entrada:
```powershell
New-NetFirewallRule -DisplayName "CEJ MCP Server" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow
```

**5. FastMCP escucha en IPv6 o `mcp.run()` falla con Start-Process**
FastMCP con `"http_host": "0.0.0.0"` puede escuchar solo en IPv6 en Windows,
bloqueando conexiones IPv4 desde WSL. Pero el problema más común es que
**`mcp.run()` autodetecta transporte y falla silenciosamente cuando se lanza
via `Start-Process -WindowStyle Hidden`** (sin TTY).

**Fix definitivo** (2 cambios en `cej_mcp_server.py`):

1. Usar `asyncio.run(mcp.run_streamable_http_async())` en vez de `mcp.run()`
2. Mantener `"http_host": "0.0.0.0"` en config.json para aceptar conexiones externas

```python
# En cej_mcp_server.py, reemplazar mcp.run() con:
import asyncio
try:
    asyncio.run(mcp.run_streamable_http_async())
except KeyboardInterrupt:
    logger.info("Server stopped by user")
except RuntimeError as e:
    if "already running" in str(e).lower():
        mcp.run_streamable_http_async()
    else:
        raise
```

**Conectividad WSL→Windows**: WSL no puede usar `127.0.0.1` para llegar a Windows
(es su propio loopback). Desde WSL, conectar via IP del gateway:
```bash
GW=$(ip route show default | awk '{print $3}')
curl -s -m 5 "http://$GW:8765/mcp" -H "Accept: text/event-stream"
```

Si falla, agregar regla de firewall:
```powershell
New-NetFirewallRule -DisplayName "CEJ MCP" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow
```

### Hermes no descubre tools después de configurar mcp_servers

No hay comando `hermes restart`. Para recargar:
1. Salir de la sesión actual de Hermes (Ctrl+D o `/exit`)
2. Iniciar una nueva sesión: `hermes chat`
3. Al inicio, Hermes intenta conectar a los MCP servers configurados
4. Si el server no está accesible en ese momento, las tools simplemente no aparecen
5. Verificar estado con: `hermes mcp status` (si existe el subcomando)

## Pitfalls

- **HTTP no stdio**: No intentar conectar via `command:` + `powershell.exe`. Usar `url:` siempre.
- **API key**: La key está en el sistema Windows, no en el repo. Configurar `TWOCAPTCHA_API_KEY` como variable de entorno del sistema.
### Chrome debe estar abierto: Los spiders se conectan a Chrome via remote debugging. Si Chrome no está abierto en el puerto correcto, fallan.

⚠️ **Chrome NO se puede auto-lanzar desde WSL para remote debugging (definitivo)** — múltiples intentos fallaron:

| Método desde WSL | Resultado |
|---|---|
| `powershell.exe Start-Process ... --remote-debugging-port=9222` | ❌ Chrome se abre pero SIN el flag |
| `powershell.exe -Command "& 'chrome.exe' ... --remote-debugging-port=9222"` | ❌ No propaga el flag |
| `cmd.exe /c start "" "chrome.exe" --remote-debugging-port=9222` | ❌ Timeout o error |
| `terminal(background=true)` con `powershell.exe &` | ❌ No propaga el flag |
| Script .ps1 temporal con Start-Process | ❌ No propaga el flag |

**Causa raíz**: Al invocar `powershell.exe` desde WSL, el proceso PowerShell lanza Chrome como child, pero el flag `--remote-debugging-port` se pierde en la herencia del proceso — Chrome arranca como una nueva ventana/pestaña del perfil por defecto sin el flag de depuración. El flag SOLO funciona cuando se ejecuta directamente desde un shell nativo de Windows (PowerShell/CMD nativo, no desde WSL).

**Workaround definitivo**: El usuario debe abrir Chrome manualmente desde **PowerShell nativo de Windows** (no Win+R, no CMD):

```powershell
# Spider A (puerto 9222)
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 "https://cej.pj.gob.pe/cej/forms/busquedaform.html"

# Spider B (puerto 9223) — en OTRA ventana PowerShell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223 "https://cej.pj.gob.pe/cej/forms/busquedaform.html"
```

**No usar Win+R**: La tecla Windows + R no acepta argumentos de línea de comandos como `--remote-debugging-port`. Siempre PowerShell.

**No usar CMD**: `cmd.exe /c start "title" "chrome.exe" --remote-debugging-port=X` tiene problemas con el parsing de argumentos. Usar PowerShell siempre.

**No pegar ambos comandos en la misma ventana PowerShell**: El segundo sobreescribe la sesión del primero. Abrir una ventana separada para cada spider.

**Alternativa futura**: El spider SÍ puede auto-lanzar Chrome internamente (via `subprocess.Popen`) cuando corre directamente en Windows (desde PowerShell) — el código en `poder_opt.py` ya incluye esta lógica para arranque autónomo. Si el spider se ejecuta directamente en Windows (no via MCP desde WSL), el auto-lanzamiento funciona.
- **Encoding**: Aunque HTTP maneja UTF-8, el server internamente debe usar `chcp 65001` para no tener problemas con caracteres especiales desde PowerShell.
- **Puerto no disponible**: Si el puerto 8765 ya está en uso, cambiar en config.json.
- **Nueva sesión de Hermes**: Después de cambiar `config.yaml`, hay que cerrar la sesión actual y abrir una nueva. No existe `hermes restart`.
- **FastMCP no es un servidor HTTP**: No esperar respuestas de `curl` o navegador a un GET plano. Con StreamableHTTP, `curl` SIN header `Accept: text/event-stream` recibe `406 Not Acceptable` (JSON-RPC error), lo cual ES una respuesta válida y confirma que el server funciona. Con el header correcto, la conexión queda abierta esperando mensajes JSON-RPC. Usar `netstat` + `curl` como verificación complementaria.
- **Firewall de terceros**: Kaspersky/AVG mantienen el servicio de firewall incluso con la interfaz cerrada. Hay que desactivar el servicio o crear una regla de excepción.
- **`mcp.run()` muere silenciosamente con Start-Process -WindowStyle Hidden**: FastMCP autodetecta transporte en `run()`. Cuando se lanza via `Start-Process -WindowStyle Hidden` (sin TTY), falla silenciosamente — el proceso aparece brevemente y muere sin dejar el puerto escuchando. **Fix**: usar `asyncio.run(mcp.run_streamable_http_async())` explícitamente en vez de `mcp.run()`. Esto fuerza HTTP sin depender de auto-detección de TTY. Ver `references/run_streamable_http_fix.md`.
- **WSL no puede alcanzar `127.0.0.1` de Windows**: El `127.0.0.1` de WSL es su propio loopback, NO el de Windows. Aunque el server escuche en `0.0.0.0:8765` en Windows, WSL no llega via `localhost` ni `127.0.0.1`. Soluciones: (a) Conectar via IP del gateway WSL (`172.21.192.1` típicamente — usar `ip route show default`), (b) Agregar regla de firewall Windows para el puerto 8765, (c) Usar `http_host: "0.0.0.0"` en config.json para bindear a todas las interfaces. El orden correcto: `0.0.0.0` + firewall + conectar via IP gateway.
