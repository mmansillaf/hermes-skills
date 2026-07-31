# Multi-Spider Production Launch (PowerShell)

## Prerequisites

- Chrome closed (fresh start)
- Both user-data-dirs exist (`.chrome_profile/pj_perfil_A`, `.chrome_profile/pj_perfil_B`)

## Full Launch Sequence

Run these from **PowerShell** (not WSL, not CMD), in this order:

### 1. Open Chrome instances

```powershell
# Chrome A — port 9222
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  --remote-debugging-port=9222 `
  --user-data-dir='D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results\.chrome_profile\pj_perfil_A' `
  'https://cej.pj.gob.pe/cej/forms/busquedaform.html'

# Chrome B — port 9223  
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  --remote-debugging-port=9223 `
  --user-data-dir='D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results\.chrome_profile\pj_perfil_B' `
  'https://cej.pj.gob.pe/cej/forms/busquedaform.html'
```

Wait ~6s after each for DevTools to bind. Verify both ports are listening:

```powershell
netstat -ano | findstr ':9222|:9223'
```

### 2. Launch spiders

```powershell
# Spider A
cd D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results
D:\PyCode\poder_judicial_results-PY-OK\venv\Scripts\python.exe run_A_win_remote.py

# Open NEW PowerShell window for Spider B
cd D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results
D:\PyCode\poder_judicial_results-PY-OK\venv\Scripts\python.exe run_B_win_remote.py
```

### 3. Monitor

From WSL (ongoing):

```bash
# Newest outputs
ls -lt /mnt/d/PyCode/poder_judicial_results-PY-OK/DescargaPJ_optimizado/poder_judicial_results/output/ | head -5

# Documents on disk
ls -lt /mnt/d/PyCode/poder_judicial_results-PY-OK/DescargaPJ_optimizado/poder_judicial_results/documents/ | head -10
echo "Total: $(ls -d /mnt/d/PyCode/.../documents/*/ | wc -l)"

# Python processes alive
powershell.exe -Command "Get-Process -Name python* | Select-Object Id, StartTime, CPU | Format-Table -AutoSize"
```

### 4. Stop

Kill all python spider processes:

```powershell
Get-Process -Name python* | Stop-Process -Force
```

Chrome windows can be left open for the next run.

## Clean Restart (when Chrome processes accumulate)

If you've launched spiders multiple times, Chrome processes pile up and only some spiders actually connect to their debug ports.

### Symptoms
- User reports "hay 7 ventanas de Chrome abiertas pero solo 1 esta descargando"
- `Get-Process -Name chrome | Measure-Object` shows 14+ Chrome processes
- Multiple Python processes running but only one spider producing new outputs
- One debug port has `TIME_WAIT` entries instead of `LISTENING`

### Procedure

```powershell
# 1. Kill ALL python spiders (zombie processes from previous launches)
Get-Process -Name python* | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Kill ALL Chrome processes
Get-Process -Name chrome | Stop-Process -Force -ErrorAction SilentlyContinue

# 3. Wait a few seconds
Start-Sleep -Seconds 3

# 4. Verify nothing is left
Get-Process -Name python*,chrome -ErrorAction SilentlyContinue  # should return nothing
netstat -ano | findstr ':9222|:9223'  # should return nothing

# 5. Use FRESH user-data-dirs (not reusing old ones that may have corrupted session state)
# Create fresh profiles
New-Item -ItemType Directory -Force -Path 'D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results\.chrome_profile\pj_A_fresh'
New-Item -ItemType Directory -Force -Path 'D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results\.chrome_profile\pj_B_fresh'

# 6. Open Chrome A and B with fresh profiles + --no-first-run
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' --remote-debugging-port=9222 --user-data-dir='D:\...\pj_A_fresh' --no-first-run --no-default-browser-check 'https://cej.pj.gob.pe/cej/forms/busquedaform.html'
& 'C:\Program Files\Google\Chrome\Application\chrome.exe' --remote-debugging-port=9223 --user-data-dir='D:\...\pj_B_fresh' --no-first-run --no-default-browser-check 'https://cej.pj.gob.pe/cej/forms/busquedaform.html'

# 7. Verify both ports
netstat -ano | findstr ':9222|:9223'
# Expected: TCP 127.0.0.1:9222 LISTENING and TCP 127.0.0.1:9223 LISTENING

# 8. Launch spiders (in separate windows)
cd D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado\poder_judicial_results
D:\PyCode\poder_judicial_results-PY-OK\venv\Scripts\python.exe run_A_win_remote.py
# Open new PowerShell window:
D:\PyCode\poder_judicial_results-PY-OK\venv\Scripts\python.exe run_B_win_remote.py
```

### Why "14+ Chrome processes" is normal (and when it's not)

Chrome spawns multiple helper processes (GPU, network, audio, renderer, utility) even for a single window. `Get-Process -Name chrome` returning 10-14 entries with 2 windows is **normal**. The diagnostic criterion is:
- **Count of DEBUG PORTS** (netstat on :9222 and :9223), not count of Chrome processes
- **Python processes with CPU > 0** that correspond to spider start times
- **New CSVs appearing** in output/ with current timestamps

### Verifying which Chrome has remote debugging active

```powershell
# Which port each Chrome process owns
netstat -ano | findstr ':9222'
netstat -ano | findstr ':9223'

# The PID in the last column of netstat output corresponds to Chrome's main PID
# Get that Chrome process details:
Get-Process -Id <PID> | Select-Object Id, StartTime
```

If a port shows `TIME_WAIT` instead of `LISTENING`, Chrome on that port was killed/closed. Relaunch is needed.

## Common errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| `UnboundLocalError: cannot access local variable 'cej_url'` | Chrome was already open on port, `cej_url` never defined | Patch: move `cej_url = '...'` outside the `if not chrome_ya_abierto` block |
| `TypeError: Binary Location Must be a String` (WSL only) | uc.Chrome can't find Windows Chrome binary | Don't run from WSL — use PowerShell directly |
| `session not created: cannot connect to chrome at 127.0.0.1:9223` | Chrome bound to Windows 127.0.0.1, WSL can't reach it | Already on 127.0.0.1 — run spider from Windows PowerShell, not WSL |
| `FileNotFoundError: input\\slice_LA_DC_B.xlsx` | Backslash path in env var on Linux | Use forward slashes in env var, or run from PowerShell (where `\\` works) |

## When to run

- Outside peak hours (Peru business hours + weekends = worse 2captcha quality)
- With at least $1 2captcha balance (check: `requests.get('https://api.2captcha.com/res.php?key=KEY&action=getbalance').text`)
- With Peru direct IP (no VPN datacenter IPs — they trigger Radware faster)
