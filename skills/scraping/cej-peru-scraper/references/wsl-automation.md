# WSL Automation: Running CEJ Spiders from Linux

## The Problem

Hermes Agent runs in WSL (Linux). The CEJ spiders need:
- Real Chrome (Windows only — WSL Chrome triggers Radware)
- Windows Python venv (D:\PyCode\poder_judicial_results-PY-OK\venv\Scripts\python.exe)
- PowerShell for execution

From WSL, `powershell.exe -Command` can launch processes, but:
1. Background processes get killed when WSL pipe closes (SIGPIPE → SIGKILL)
2. The remote debugging port binding is Windows-side
3. Hard to monitor progress from WSL

## Option A: PowerShell.exe from WSL (Simple but Unreliable)

```bash
cd /mnt/d/PyCode/poder_judicial_results-PY-OK

# Launch Spider A (foreground — blocks WSL)
powershell.exe -Command "
  cd D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results
  & 'D:\PyCode\poder_judicial_results-PY-OK\venv\Scripts\python.exe' run_A_win_remote.py
"
```

**Problem:** Background mode (`Start-Process`, `-WindowStyle Hidden`) detaches the process
but Hermes loses its lifecycle tracking. The process could crash silently.

## Option B: MCP Server on Windows (Recommended)

A Python MCP server running **natively on Windows** that exposes tools like:

- `cej_start_spider_a` — launches and tracks Spider A
- `cej_start_spider_b` — launches and tracks Spider B
- `cej_status` — returns checkpoint sizes, Chrome PID, runtime
- `cej_stop_spiders` — kills both spiders
- `cej_stats` — runs stats.py and returns analysis

### Architecture

```
Hermes (WSL) ←→ MCP Server (Windows, stdio via SSH or dedicated process)
                              │
                   ┌──────────┴──────────┐
                   │                     │
            Spider A (:9222)      Spider B (:9223)
```

### Implementation

```python
# mcp_cej_server.py — runs on Windows, exposes CEJ spider control via MCP
import json, sys, subprocess, socket, os, signal, time

# Configuration
CEJ_DIR = r"D:\PyCode\poder_judicial_results-PY-OK"
VENV_PYTHON = r"D:\PyCode\poder_judicial_results-PY-OK\venv\Scripts\python.exe"
SPIDER_DIR = r"D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results"
CHROME_BIN = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

processes = {}  # {name: Popen}

def _send(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def _read():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)

def start_spider(spider_id, port):
    env = os.environ.copy()
    env["TWOCAPTCHA_API_KEY"] = os.environ.get("TWOCAPTCHA_API_KEY", "")
    env["REMOTE_DEBUGGING_PORT"] = str(port)
    env["PJ_INPUT_FILE"] = f"input\\slice_LA_DC_{spider_id}.xlsx"
    env["PJ_SPIDER_ID"] = spider_id
    
    p = subprocess.Popen(
        [VENV_PYTHON, f"run_{spider_id}_win_remote.py"],
        cwd=SPIDER_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes[f"spider_{spider_id}"] = p
    return {"spider": spider_id, "pid": p.pid, "port": port}

# MCP handlers
TOOLS = {
    "cej_start_spider": {
        "description": "Start a CEJ spider (A or B)",
        "parameters": {
            "type": "object",
            "properties": {
                "spider_id": {
                    "type": "string",
                    "enum": ["A", "B"],
                    "description": "Spider ID: A (port 9222) or B (port 9223)"
                }
            },
            "required": ["spider_id"]
        },
        "handler": lambda msg: {
            "content": [{"type": "text", "text": json.dumps(
                start_spider(
                    msg["params"]["spider_id"],
                    9222 if msg["params"]["spider_id"] == "A" else 9223
                ),
                indent=2
            )}]
        }
    },
    "cej_status": {
        "description": "Get current status of all CEJ spiders",
        "parameters": {"type": "object", "properties": {}},
        "handler": lambda msg: status_handler()
    },
    "cej_stop_spiders": {
        "description": "Stop all running CEJ spiders",
        "parameters": {"type": "object", "properties": {}},
        "handler": lambda msg: stop_handler()
    },
}

def status_handler():
    status = {}
    for name, proc in processes.items():
        status[name] = {
            "pid": proc.pid,
            "alive": proc.poll() is None,
            "returncode": proc.returncode if proc.poll() is not None else None,
        }
    # Also check checkpoints
    for sid in ["A", "B"]:
        cp_path = os.path.join(SPIDER_DIR, f"checkpoint_opt_{sid}.json")
        if os.path.exists(cp_path):
            with open(cp_path) as f:
                data = json.load(f)
            status[f"checkpoint_{sid}"] = len(data) if isinstance(data, list) else len(data)
    return {"content": [{"type": "text", "text": json.dumps(status, indent=2)}]}

def stop_handler():
    killed = []
    for name, proc in list(processes.items()):
        if proc.poll() is None:
            proc.terminate()
            killed.append(name)
        processes.pop(name, None)
    return {"content": [{"type": "text", "text": json.dumps({"killed": killed})}]}

# Main MCP loop
initialized = False
while True:
    msg = _read()
    if msg is None:
        break
    
    method = msg.get("method", "")
    msg_id = msg.get("id")
    
    if method == "initialize":
        _send({
            "jsonrpc": "2.0", "id": msg_id,
            "result": {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "cej-controller", "version": "1.0.0"},
            }
        })
        continue
    
    if method == "notifications/initialized":
        initialized = True
        continue
    
    if not initialized:
        if msg_id is not None:
            _send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32000, "message": "Not initialized"}})
        continue
    
    if method == "tools/list":
        _send({
            "jsonrpc": "2.0", "id": msg_id,
            "result": {
                "tools": [{
                    "name": name,
                    "description": t["description"],
                    "inputSchema": t["parameters"],
                } for name, t in TOOLS.items()]
            }
        })
    
    elif method == "tools/call":
        tool_name = msg["params"]["name"]
        handler = TOOLS.get(tool_name, {}).get("handler")
        if handler:
            try:
                result = handler(msg)
                _send({"jsonrpc": "2.0", "id": msg_id, "result": result})
            except Exception as e:
                _send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}})
        else:
            _send({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"}})
    
    elif method == "shutdown":
        break
```

### Running the MCP Server

On Windows, start it persistently:

```powershell
# Run it (keep terminal open for debugging)
cd D:\PyCode\poder_judicial_results-PY-OK
.\venv\Scripts\python.exe mcp_cej_server.py

# Or run as background job (no window)
Start-Process -NoNewWindow -FilePath "D:\PyCode\poder_judicial_results-PY-OK\venv\Scripts\python.exe" -ArgumentList "mcp_cej_server.py"
```

### Configuring in Hermes

In `~/.hermes/config.yaml`, add the MCP server pointing to the **Windows Python**:

```yaml
mcp_servers:
  cej-controller:
    command: "powershell.exe"
    args:
      - "-Command"
      - "& 'D:\\PyCode\\poder_judicial_results-PY-OK\\venv\\Scripts\\python.exe' D:\\PyCode\\poder_judicial_results-PY-OK\\mcp_cej_server.py"
    timeout: 300
```

**Caveat**: Hermes runs the MCP server via stdio from WSL. The subprocess launched
by `powershell.exe -Command python.exe ...` runs on Windows but its stdin/stdout
is piped through WSL. This should work for simple commands but may have issues with
very long-running MCP sessions.

### Alternative: WS/HTTP MCP Server

If stdio-through-WSL is unreliable, run the MCP server as HTTP on Windows:

```yaml
mcp_servers:
  cej-controller:
    url: "http://localhost:8765/mcp"
```

The server would use `aiohttp` to serve MCP over HTTP. More robust but needs
a dedicated port and auto-start mechanism.

## Option C: Scheduled Polling (Simpler)

If the user doesn't mind manually starting spiders, configure a Hermes cron job
that polls checkpoint status every hour:

```yaml
cron:
  cej-status:
    schedule: "0 * * * *"  # every hour
    prompt: "Check CEJ spider status by reading checkpoints and counting documents"
    deliver: "origin"
```

This gives a passive status readout without needing MCP.

## Decision Guide

| Approach | Complexity | Reliability | User effort |
|----------|:---:|:---:|:---:|
| A: powershell.exe directly | Low | Low (process death) | Manual restart |
| B: MCP server stdio | Medium | Medium (pipe issues) | Zero — I launch |
| B: MCP server HTTP | High | High | Zero — I launch |
| C: Cron polling | Low | N/A | Manual start, auto-monitor |
