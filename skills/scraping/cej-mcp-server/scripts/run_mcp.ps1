# Kill existing python processes running cej_mcp
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Start MCP server in background with log capture
$proc = Start-Process -FilePath "C:\Python314\python.exe" `
    -ArgumentList "-u", "D:\PyCode\cej-mcp-server\cej_mcp_server.py" `
    -PassThru `
    -RedirectStandardOutput "D:\PyCode\cej-mcp-server\server_out.log" `
    -RedirectStandardError "D:\PyCode\cej-mcp-server\server_err.log" `
    -WindowStyle Hidden

Write-Output "PID: $($proc.Id)"
Start-Sleep -Seconds 8

Write-Output "--- STDOUT LOG ---"
Get-Content "D:\PyCode\cej-mcp-server\server_out.log" -ErrorAction SilentlyContinue
Write-Output "--- STDERR LOG ---"
Get-Content "D:\PyCode\cej-mcp-server\server_err.log" -ErrorAction SilentlyContinue
Write-Output "--- NETSTAT ---"
netstat -ano | Select-String "8765"
Write-Output "--- PROCESS CHECK ---"
Get-Process -Id $proc.Id -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Responding
Write-Output "--- CURL ---"
curl.exe -s -m 3 http://127.0.0.1:8765/mcp 2>&1
Write-Output "curl exit: $LASTEXITCODE"
