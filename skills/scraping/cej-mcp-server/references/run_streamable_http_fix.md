# Fix: mcp.run() silently dies with Start-Process -WindowStyle Hidden

## Symptom

When launching `cej_mcp_server.py` via `Start-Process -WindowStyle Hidden` (or any
background launch method without a TTY), FastMCP's `mcp.run()` starts, logs
"CEJ MCP Server starting on 0.0.0.0:8765", and then silently exits. No port
ever appears in `netstat`. Process is gone after 1 second.

## Root Cause

`FastMCP.run()` auto-detects the transport based on environment:
- If stdin is a TTY → stdio transport
- If not → tries SSE/HTTP but the detection can fail when there's no console window

With `-WindowStyle Hidden`, Windows creates the process without a console, so
stdin detection fails and the transport init throws an unhandled exception that
`Start-Process` swallows silently.

## Fix

Replace `mcp.run()` with explicit StreamableHTTP transport:

```python
import asyncio

try:
    asyncio.run(mcp.run_streamable_http_async())
except KeyboardInterrupt:
    logger.info("Server stopped by user")
except RuntimeError as e:
    if "already running" in str(e).lower() or "cannot be called from a running event loop" in str(e).lower():
        mcp.run_streamable_http_async()
    else:
        raise
```

## Verification

After the fix, the server log should show:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     StreamableHTTP session manager started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8765 (Press CTRL+C to quit)
```

And `netstat -ano | Select-String "8765"` should show:
```
TCP    0.0.0.0:8765           0.0.0.0:0              LISTENING       PID
```

Curl from Windows should respond (even without Accept header):
```
curl.exe http://127.0.0.1:8765/mcp
→ {"jsonrpc":"2.0","id":"server-error","error":{"code":-32600,"message":"Not Acceptable: Client must accept text/event-stream"}}
```

The 406 error is CORRECT — it proves the server is alive and responding to HTTP.
