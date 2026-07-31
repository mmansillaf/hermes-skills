# Launching Chrome with remote-debugging-port from WSL

## Problem

The CEJ spiders require Chrome with `--remote-debugging-port=9222` (or 9223 for spider B). 
From WSL, it's tempting to try to auto-launch these Chromes programmatically. **Don't waste 
time on this** — every method tried fails.

## Failed approaches (all verified multiple times)

| Method | Result |
|---|---|
| `powershell.exe Start-Process -ArgumentList '--remote-debugging-port=9222'` | Chrome opens WITHOUT the flag |
| `powershell.exe -Command "& 'chrome.exe' --remote-debugging-port=9222"` | Same — flag lost in WSL→PowerShell bridge |
| `cmd.exe /c start "title" "chrome.exe" --remote-debugging-port=9222` | Times out or parses wrong |
| `terminal(background=true)` wrapper around above | Chrome launches but dies silently |
| Write temp .ps1 → execute | Flag doesn't propagate |
| Via MCP server's subprocess calling PowerShell | Same result — no flag |

## Root cause

The `--remote-debugging-port` flag must be applied to the **very first Chrome process**
that starts. WSL's bridge to PowerShell/CMD doesn't pass flags correctly for Chrome's 
process model — Chrome spawns a zygote/GPU process that inherits different flags.

## What works: user opens Chrome from native Windows PowerShell

```powershell
# Spider A (puerto 9222)
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-window --remote-debugging-port=9222 "https://cej.pj.gob.pe/cej/forms/busquedaform.html"

# Spider B (puerto 9223)
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-window --remote-debugging-port=9223 "https://cej.pj.gob.pe/cej/forms/busquedaform.html"
```

Note: `--new-window` ensures a separate Chrome window (not a tab in an existing one).

## Detection from WSL

After Chrome is open, verify from WSL:

```bash
powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress" | python3 -c "
import json,sys
data=json.load(sys.stdin)
items=data if isinstance(data,list) else [data]
for p in items:
    cl = p.get('CommandLine','')
    if '--remote-debugging-port=922' in cl and '--type=' not in cl:
        print(f'OK PID {p[\"ProcessId\"]}')
"
```

Only the main chrome.exe process (without `--type=`) counts — renderer processes with 
`--type=renderer` also show the port flag but are NOT valid targets for CDP connection.

## User flow when they ask "y lo puedes hacer tu?"

When the user asks "y lo puedes hacer tu?" or "lo puedes hacer tu desde el principio?" 
after a failed launch attempt, **do NOT keep trying from WSL**. Instead:

1. Say "Desde WSL no funciona confiablemente" (brief — don't over-explain)
2. Give them the exact PowerShell command to copy-paste
3. When they confirm Chrome is open, proceed with `cej_start_spider` via MCP

This avoids the frustrating loop of repeated failed attempts.
