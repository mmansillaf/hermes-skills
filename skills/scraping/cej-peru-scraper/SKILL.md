---
name: cej-peru-scraper
description: Complete patterns for scraping Peru's CEJ (Poder Judicial) — anti-bot / WAF evasion via browser fingerprint modification, captcha solving with retries, form event dispatching, auto-launch Chrome, and multi-spider production architecture. Distilled from a production debugging session where parallel downloads triggered permanent IP blocking.
triggers:
  - "cej scraper"
  - "poder judicial peru scraping"
  - "anti-bot captcha scraping"
  - "peruvian judicial scraping"
  - "remote debugging chrome scraper"
  - "dispatchEvent form fields selenium"
  - "auto-launch chrome selenium"
  - "2captcha retry pattern"
  - "solo 1 esta descargando"
  - "multiples chrome abiertos"
  - "clean restart spiders"
  - "captcha siempre falla"
  - "form validation selenium"
  - "msjError CEJ"
  - "saltoCajaTexto"
  - "cod_distprovError"
  - "onkeyup selenium"
  - "WSL spider"
  - "background spider"
  - "batch limit"
  - "mini-slice"
  - "1000 expedientes"
---

# CEJ Peru Scraper — Production Patterns

## Overview

Complete toolkit for scraping Peru's CEJ (Consulta de Expedientes Judiciales) at
`cej.pj.gob.pe`, protected by Radware/PerfDrive WAF + text captcha. Distilled from
a production debugging session where speed optimizations (parallel downloads,
connection pooling) triggered permanent IP blocking.

## Trigger

User needs to scrape CEJ or a similar Radware-protected judicial portal. User
reports "Radware bloquea", "validate.perfdrive.com", "captcha siempre falla", or
"el spider funcionaba pero al optimizarlo empezó a bloquear".

## Critical Anti-Patterns (DO NOT)

These optimizations triggered Radware permanent IP blocking:

| What | Why it triggers Radware |
|------|------------------------|
| `ThreadPoolExecutor(max_workers=3)` for doc downloads | Burst of 3 simultaneous HTTP requests = DDoS signature |
| `requests.Session()` keep-alive across parallel workers | Identical TLS fingerprint across all requests |
| `stagger=0.3s` between parallel submissions | Too fast — looks like automated burst |
| No cooldown between expedientes | Continuous predictable traffic |
| Fixed sleeps (2s, 3s, 5s) | Predictable timing fingerprint |
| `driver.refresh()` after page load | Bot-like behavior pattern |

## WSL Auto-Mode (No Remote Debugging)

**New pattern verified 2026-06-29**: The spider can run entirely from WSL using Chrome
for Testing + `CHROME_BINARY_PATH`, completely bypassing remote debugging. This is the
simplest path for running spiders from Hermes.

### When to use WSL auto-mode vs Windows remote debugging

| Factor | WSL Auto-Mode | Windows Remote Debugging |
|--------|:---:|:---:|
| Chrome launch | Automatic (undetected_chromedriver) | Manual or auto-launch |
| Display | WSLg required | Windows desktop |
| WAF risk | Higher (test first with curl) | Lower (real browser) |
| Setup effort | Minimal | Multiple steps |
| Batch limiting | Easy (mini-slices) | Same |
| Background from Hermes | ✅ `terminal(background=true)` | ❌ complex |
| Multi-spider parallelism | ✅ 2x `terminal(background=true)` | ❌ cumbersome |

### How to set up WSL auto-mode

Create a run script per spider (see `run_A_wsl.py` / `run_B_wsl.py` in the project):

```python
import os, sys

os.environ['TWOCAPTCHA_API_KEY'] = 'your_key_here'
os.environ['CHROME_BINARY_PATH'] = os.path.expanduser('~/chromium/chrome-linux64/chrome')
os.environ['PJ_INPUT_FILE'] = 'input/slice_LA_DC_A.xlsx'
os.environ['PJ_SPIDER_ID'] = 'A'  # isolates checkpoints/CSVs

project_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_dir)
sys.path.insert(0, parent_dir)
os.chdir(project_dir)

from scrapy import cmdline
cmdline.execute("scrapy crawl poder_opt".split())
```

**Key differences from Windows remote-debugging entry points:**
- Use `CHROME_BINARY_PATH` instead of `REMOTE_DEBUGGING_PORT`
- The spider auto-launches Chrome in non-debug mode (lines 166-199 of `poder_opt.py`)
- Chrome for Testing at `~/chromium/chrome-linux64/chrome` must be installed
- `DISPLAY=:0` (WSLg) must be available for visible Chrome
- Use forward slashes in paths (Unix convention), not backslashes

### Fresh profiles with CHROME_USER_DATA_DIR (key reliability fix)

Chrome for Testing in WSL accumulates corrupted session state after repeated
crashes. The project's auto-created profiles (`.chrome_profile/pj_perfil_A/`)
degrade over 5-10 watchdog retries, causing progressively faster crashes.

**Fix**: Set `CHROME_USER_DATA_DIR` to a path OUTSIDE the project directory.
This gives a clean profile on each fresh start:

```python
os.environ['CHROME_USER_DATA_DIR'] = os.path.expanduser(
    '~/chromium/chrome_profile_A_fresh'  # or B for Spider B
)
```

Without this env var, the spider falls back to:
```python
profile_dir = os.path.join(self.script_dir, '.chrome_profile',
    f'pj_perfil_{sid}' if sid else 'pj_perfil')
```

The project-level profiles work for 1-2 runs but degrade rapidly under
repeated `chrome_dead` crashes. Fresh profiles in `~/chromium/` survived
15+ watchdog attempts without issues in production testing.

**Cleanup between batches**: Always delete the fresh profile before a new
batch to avoid carrying over corrupted state:

```bash
rm -rf ~/chromium/chrome_profile_A_fresh
rm -rf ~/chromium/chrome_profile_B_fresh
```

### Remote debugging mode limitation (TypeError: Binary Location)

When `REMOTE_DEBUGGING_PORT` is set, the spider's `__init__` creates Chrome
options with `debuggerAddress` but does NOT pass `browser_executable_path`:

```python
# Lines 146-152 of poder_opt.py — remote debugging path
opts.add_experimental_option('debuggerAddress', f'127.0.0.1:{debug_port}')
chrome_kwargs = {'version_main': 148, 'options': opts}
# NOTE: browser_executable_path is NOT set here!
self.driver = Chrome(**chrome_kwargs)
```

This causes `undetected_chromedriver` to auto-detect the browser binary,
which fails in WSL (no system Chrome binary found), raising:
```
TypeError: Binary Location Must be a String
```

**Contrast with normal mode** (lines 192-199):
```python
chrome_kwargs = {'version_main': 148, 'options': opts}
if chrome_path:
    chrome_kwargs['browser_executable_path'] = chrome_path  # ✅ present
```

**Fix**: Either:
- Use normal mode (no `REMOTE_DEBUGGING_PORT` env var) — recommended for WSL
- Or patch `__init__` to pass `browser_executable_path` in the remote debugging
  code path too

### Verification checklist

Before launching a long batch, verify each component works:

```bash
# 1. Chrome for Testing exists
ls -la ~/chromium/chrome-linux64/chrome

# 2. WSLg display works
echo $DISPLAY  # should show :0

# 3. Python venv with scrapy exists
source ~/venv_poder/bin/activate
python -c "import scrapy; print(scrapy.__version__)"

# 4. Quick smoke test (2-3 minutes)
cd /path/to/poder_judicial_results
source ~/venv_poder/bin/activate
python run_A_wsl.py &
sleep 90 && tail -20 logs/spider_A_*.log | head -10
# Should show: "Captcha OK", "Documentos: N encontrados, M importantes"
```

### Background process management from Hermes

Launch the spider as a long-lived background process via the terminal tool:

```
terminal(background=true, notify_on_complete=true, timeout=180000)
    cd /path/to/project && source ~/venv_poder/bin/activate \
    && python run_A_wsl.py > logs/spider_A_TIMESTAMP.log 2>&1
```

Key settings:
- `background=true` — runs in background so the session doesn't block
- `notify_on_complete=true` — sends notification when spider finishes
- `timeout=180000` — generous timeout (50h) for long batches
- Output redirection to `logs/` for post-mortem inspection

To launch both spiders in parallel, make two separate calls:

```python
# First call: Spider A
proc_a = terminal(background=true, notify_on_complete=true, timeout=180000,
    command="cd /path && source ~/venv/bin/activate && python run_A_wsl.py > logs/A.log 2>&1")

# Wait ~10s for Chrome A to initialize, then call Spider B
proc_b = terminal(background=true, notify_on_complete=true, timeout=180000,
    command="cd /path && source ~/venv/bin/activate && python run_B_wsl.py > logs/B.log 2>&1")
```

Mid-run status via `process(action="poll")` or `process(action="log")`.

**Warning**: Each spider processes ALL items in its input file. For limited batches
use mini-slices (see "Batch Limiting" section).

### Long-Running Batches: Watchdog Pattern

Chrome for Testing in WSL crashes every 5-15 minutes (`CloseSpider('chrome_dead')`)
due to WSL renderer instability. For batches longer than ~30 minutes, wrap the
spider in the watchdog script (`scripts/watchdog.sh`):

```
# From Hermes: launch via terminal tool
terminal(background=true, notify_on_complete=true, timeout=360000,
    command="cd /path/to/project && source ~/venv/bin/activate \
    && bash scripts/watchdog.sh A > logs/watchdog_A.log 2>&1")
```

### Watchdog v2 (improved crash detection)

The initial watchdog (v1) only checked for `Spider closed (chrome_dead)` and
`Spider closed (radware_blocked)`. It missed other WebDriver connection failures:

| Failure mode | v1 detection | v2 detection |
|---|---|---|
| `CloseSpider('chrome_dead')` | ✅ | ✅ |
| `CloseSpider('radware_blocked')` | ✅ | ✅ |
| `Remote end closed connection without response` | ❌ (exits as "normal") | ✅ |
| `Connection refused` on WebDriver port | ❌ | ✅ |
| `Max retries exceeded` (urllib3) | ❌ | ✅ |
| `Connection aborted` Chrome startup failure | ❌ | ✅ |
| `chrome not reachable` / `invalid session` | ❌ | ✅ |

**v2 fix**: Use a single `grep -E` with all known failure patterns:

```bash
if grep -qE "(chrome_dead|radware_blocked|Connection refused|\
Remote end closed connection|Cannot connect|Max retries exceeded|\
Connection aborted|chrome not reachable|invalid session)" "$LOG"; then
    REASON=$(grep -oE "(chrome_dead|radware_blocked|Connection refused|\
    Remote end closed connection|Max retries exceeded|Connection aborted)" \
    "$LOG" | tail -1)
    echo "Fallo detectado: $REASON. Relanzando..."
    pkill -f "pj_perfil_${SID}" 2>/dev/null || true  # clean Chrome orphans
    sleep 5
    continue
fi
```

**Always clean Chrome orphans between retries** -- stale Chrome processes with the
same `--user-data-dir` keep the WebDriver port occupied:

```bash
pkill -f "pj_perfil_${SID}" 2>/dev/null || true
sleep 5  # Give OS time to release port
```

**⚠️ Critical blind spot in `pkill`**: The profile-name-based `pkill -f "pj_perfil_${SID}"`
does NOT kill all Chrome children. After a `chrome_dead` crash, these processes
typically survive:

| Process | Survives `pkill -f "pj_perfil_A"`? | Why |
|---------|:---:|-----|
| `chrome` (main) | ✅ Killed | Has `--user-data-dir=...pj_perfil_A` in args |
| `chrome_crashpad_handler` | ❌ **Survives** | Args have no profile path — only `--monitor-self` |
| `chrome --type=zygote` | ❌ **Survives** | Same — no profile path in visible args |
| `chrome --type=gpu-process` | ❌ **Survives** | Same |
| `[chrome] <defunct>` (zombie) | ❌ **Unkillable** | Zombies cannot be killed — parent reaps them on death |

After 10-20 watchdog cycles, these residual processes accumulate and prevent
new Chrome instances from binding to ports or locks. The **zombie process**
(`<defunct>`) is particularly insidious — it consumes a PID table entry and
can't be killed by any signal.

**Fix**: Use a comprehensive kill targeting ALL Chrome processes, not just
those matching a profile name. The watchdog should run this before each retry:

```bash
# Kill ALL Chrome for Testing processes (any profile, any args)
kill -9 $(ps aux | grep -E "(chrom|chrome)" | grep -v grep \
  | awk '{print $2}') 2>/dev/null || true
# Also kill undetected_chromedriver which may hold stale ports
kill -9 $(ps aux | grep -i chromedriver | grep -v grep \
  | awk '{print $2}') 2>/dev/null || true
# Clean lock files from the Chrome profile
rm -f "$HOME/chromium/chrome_profile_${SID}_fresh/SingletonLock" 2>/dev/null || true
rm -f "$HOME/chromium/chrome_profile_${SID}_fresh/SingletonSocket" 2>/dev/null || true
sleep 5  # OS needs time to release PIDs and ports
```

Note: `grep -E "(chrom|chrome)"` catches both `chrome` (Linux) and `chromium` processes, while avoiding the `grep` false-positive issue with the `grep -v grep` filter.

Full system cleanup (for when watchdog exhausts 100 retries):
```bash
# Nuclear option — kill everything Chrome-related
ps aux | grep -E "(chrome|chromium|undetected)" | grep -v grep \
  | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true

# Delete ALL Chrome profiles (project + fresh + binary's own global config)
rm -rf ~/chromium/chrome_profile_A_fresh ~/chromium/chrome_profile_B_fresh
rm -rf /path/to/.chrome_profile/pj_perfil_A /path/to/.chrome_profile/pj_perfil_B
rm -rf ~/.config/google-chrome-for-testing/  # ← THIS IS KEY — binary global state
```

**Pitfall -- false "normal completion"**: Without the v2 pattern matching, a
Chrome startup failure (e.g., `Remote end closed connection without response`
during `driver = Chrome(...)` initialization) causes the spider to exit with
exit code 1, no `chrome_dead` message in the log, and the watchdog exits
thinking the batch is finished. The mini-slice will have items remaining in the
checkpoint, but the watchdog has stopped. The v2 `grep -E` catches this case.

See `scripts/watchdog.sh` for the full v2 implementation.

### Chrome Crash Root Cause Analysis

**Observed pattern**: Chrome for Testing in WSL crashes with increasing frequency
across watchdog cycles. First ~10 attempts: ~3-15 min runtime. Attempts 60-100:
instant failures (`Connection refused` — Chrome can't even start).

**3,000+ crash breakdown (one session):**

| Crash type | Count | What it means |
|-----------|:-----:|---------------|
| `Connection refused` | **1,949** | Chrome CAN'T START — WebDriver port not opened |
| `Remote end closed connection` | 397 | Chrome STARTED but died immediately (mid-init) |
| `chrome_dead` | 393 | Chrome crashed DURING operation (middle of captcha/download) |
| `Max retries exceeded` | 138 | WebDriver timed out waiting for Chrome response |
| `Connection aborted` | 117 | Chrome closed the TCP connection mid-request |
| `invalid session` | 30 | WebDriver session was invalidated by Chrome death |

**Why "Connection refused" is the dominant failure mode:**

Each Chrome launch spawns a process tree:
```
chrome (main)
  ├── chrome_crashpad_handler  (crash reporting)
  ├── chrome --type=zygote     (process sandbox)
  ├── chrome --type=gpu-process (GPU rendering)
  └── chrome --type=renderer   (page rendering)
```

When the watchdog's `pkill -f "pj_perfil_A"` fires, it only kills the main
`chrome` process. The zygote, GPU, and crashpad children **survive** because
their command-line args don't include the profile path. They become orphans
that the init process adopts but never reaps.

Additionally, Chrome creates zombies (`[chrome] <defunct>`) when child processes
die before the parent calls `wait()`. Zombies can't be killed — they persist
until the parent dies, and since the main Chrome process was already killed,
they live as orphans forever.

After 10-20 watchdog cycles, the system accumulates:
- 3-5 orphan `chrome_crashpad_handler` processes
- 3-5 orphan `chrome --type=zygote` processes  
- 3-5 orphan `chrome --type=gpu-process` processes
- 1-2 zombie `<defunct>` processes
- Lock files in `~/.config/google-chrome-for-testing/`

Eventually, a new Chrome instance can't:
1. Allocate a new PID (zombies consume entries in the PID table)
2. Bind to the chromedriver port (orphan processes hold it)
3. Initialize its GPU backend (WSLg/Weston accumulates stale resources)
4. Write to its user config directory (lock files from previous crashes)

**Why fresh profiles help temporarily but `--single-process` is the real fix**: Deleting `CHROME_USER_DATA_DIR` removes lock files that block new Chrome instances. But it doesn't fix the zombie/orphan accumulation. After ~40 watchdog attempts, even fresh profiles fail because the underlying OS resources are exhausted.

**The definitive fix** (deployed 2026-06-29): Add `--single-process` and `--no-zygote` to Chrome options. These flags prevent Chrome from forking child processes entirely — no GPU, Zygote, or Crashpad processes are created. When the watchdog kills the main Chrome process, there are NO orphans or zombies left behind. Combined with the comprehensive `kill -9` in the watchdog (see section above), this extends viable watchdog runtime from ~20 successful attempts to 80+.

**Which flags to add to `opts.add_argument()`:**
```python
opts.add_argument('--single-process')            # NO child processes = NO zombies
opts.add_argument('--no-zygote')                 # No fork-before-sandbox
opts.add_argument('--disable-software-rasterizer') # Reduce GPU memory
opts.add_argument('--no-crash-upload')            # No crash reporting background process
opts.add_argument('--disable-background-networking') # Less connections
opts.add_argument('--disable-sync')              # Less background processes
```

These were verified alongside the comprehensive watchdog kill in a 14-hour production session processing 615 CEJ expedientes without the degradation curve seen in earlier sessions.

**The `~/.config/google-chrome-for-testing/` corruption**: Even with completely
fresh `CHROME_USER_DATA_DIR`, Chrome for Testing stores some global state
(user config, crash reports, extension cache) in `~/.config/google-chrome-for-testing/`.
After 30+ crashes, this directory gets corrupted lock files. Deleting it is
essential for a clean restart:

```bash
rm -rf ~/.config/google-chrome-for-testing/
```

**Why "Connection refused" spikes after hour 4**: The timeline shows that
the first ~20 watchdog attempts mostly produce `chrome_dead` (Chrome starts,
crashes mid-operation). After hour 4, the ratio shifts to `Connection refused`
(Chrome can't even start). This is the zombie/orphan accumulation crossing a
threshold where system resources prevent Chrome initialization.

**Why Spider B outlasts Spider A**: When running A + B simultaneously, B
consistently runs 2-3x longer per attempt (57 min max vs 38 min max) and
survives more total watchdog cycles. Possible cause: A's Chrome profile
gets more corruption because it was the first to launch and crash, contaminating
shared Chrome state first. In production, expect A to exhaust its watchdogs
first. When A dies, B continues unaffected.

From production data (June 2026, 2 spiders, Peruvian residential IP):

| Metric | Value |
|--------|-------|
| Per-expediente time (1 spider) | ~3-4 min (captcha + extract + download + cooldown) |
| Combined rate (2 spiders) | ~30-61 exp/hour (varies by captcha solver quality) |
| Captcha success rate (v2 API) | ~26% historical, up to 100% on good days |
| Expected PDFs per 1,000 exp | ~260-782 (wide range based on captcha quality) |
| PDFs per expediente with data | ~2.5-2.9 |
| **Time for 1,000 exp (2 spiders)** | **~16-28 hours** |
| Total PDF storage | ~204MB for 373 exp / 941 PDFs |
| Chrome crash frequency (WSL) | Every 2-57 min, unpredictable |
| Watchdog attempts needed (500 batch, fresh start) | ~18 (observed, WSL Chrome for Testing) |
| **Watchdog exhaustion** | After ~100 total attempts, Chrome in WSL becomes completely non-functional — requires clean restart (see Pitfalls #23) |

## Batch Limiting (Mini-Slices)

### Problem

The spider has no built-in "max items" parameter — it processes ALL items in its
input Excel file. For large slices (19,000+ items), this means running for weeks.

### Solution: Create a mini-slice with only N expedientes

```python
import openpyxl, json, os
from openpyxl import Workbook

proj = '/path/to/poder_judicial_results'
sid = 'A'
n = 500  # batch size

# Load full slice
path = os.path.join(proj, 'input', f'slice_LA_DC_{sid}.xlsx')
wb = openpyxl.load_workbook(path)
ws = wb.worksheets[0]
headers = [c.value for c in ws[1]]
rows = []
for row in ws.iter_rows(values_only=True, min_row=2):
    d = dict(zip(headers, row))
    if d.get('N° EXPEDIENTE'):
        rows.append(d)
wb.close()

# Load checkpoint to filter already-processed
ckp_path = os.path.join(proj, f'checkpoint_opt_{sid}.json')
ckp_exps = set()
if os.path.exists(ckp_path):
    with open(ckp_path, encoding='utf-8') as f:
        items = json.load(f)
    ckp_exps = set(i.split('|')[0] for i in items)

# Take first N pending
pending = [r for r in rows
           if str(r.get('N° EXPEDIENTE','') or '').strip() not in ckp_exps]
batch = pending[:n]

# Write mini-slice
out_path = os.path.join(proj, 'input', f'slice_{sid}_batch_temp.xlsx')
wb_out = Workbook()
ws_out = wb_out.active
ws_out.append(headers)
for r in batch:
    ws_out.append([r.get(h, '') for h in headers])
wb_out.save(out_path)

print(f'Created mini-slice: {len(batch)} items')
```

Then point `PJ_INPUT_FILE` at the mini-slice instead of the original.

**Important**: The checkpoint (`checkpoint_opt_A.json`) continues to accumulate
normally — items processed from previous runs are still skipped. When you switch
back to the full slice later, already-processed items will be correctly excluded.

### Progress monitoring

Create a lightweight status checker (`scripts/check_status.sh`) that audits
checkpoint + disk state + process liveness:

```bash
#!/bin/bash
PROJ="/path/to/poder_judicial_results"
CKP_A=$(cat "$PROJ/checkpoint_opt_A.json" | python3 -c \
    "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
CKP_B=$(cat "$PROJ/checkpoint_opt_B.json" | python3 -c \
    "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
PDF_COUNT=$(find "$PROJ/documents" -name "*.pdf" 2>/dev/null | wc -l)
EXP_COUNT=$(ls -d "$PROJ/documents"/*/ 2>/dev/null | wc -l)
DOCS_SIZE=$(du -sh "$PROJ/documents" 2>/dev/null | cut -f1)
PID_A=$(ps aux | grep "run_A_wsl.py" | grep -v grep | awk '{print $2}')
PID_B=$(ps aux | grep "run_B_wsl.py" | grep -v grep | awk '{print $2}')
STATUS_A="VIVO (PID $PID_A)"; [ -z "$PID_A" ] && STATUS_A="DETENIDO"
STATUS_B="VIVO (PID $PID_B)"; [ -z "$PID_B" ] && STATUS_B="DETENIDO"

echo "Spider A: $STATUS_A  | Checkpoint: $CKP_A"
echo "Spider B: $STATUS_B  | Checkpoint: $CKP_B"
echo "Expedientes con PDF: $EXP_COUNT | PDFs: $PDF_COUNT | Tamaño: $DOCS_SIZE"
```

This is more reliable than `stats.py` because it reports actual disk state
rather than checkpoint metadata (which mixes captcha fails with successful downloads).

### Pitfalls

1. **Don't forget to remove the mini-slice lock** — If the spider is processing
   a mini-slice when it crashes, the checkpoint saved entries from the mini-slice
   are valid. The full slice will skip them correctly on resume.
2. **Mini-slice + original checkpoint = safe combination** — The checkpoint is
   global (shared across runs). It tracks what's been processed regardless of
   which slice was used. No conflicts.
3. **Memory warning** — 2 Chrome instances + 2 Python spiders can use 2-4GB RAM.
   Check `free -h` before launching both simultaneously. On a 15GB WSL machine,
   both spiders run comfortably with ~14GB free.
4. **Always test 1-2 items first** — Run the spider for 90 seconds and verify
   logs show "Captcha OK" and "Documentos encontrados" before committing to a
   full batch. Use a tiny mini-slice (e.g., 5 items) for the smoke test.
5. **Monitor logs during the first hour** — If captcha fails start accumulating
   fast (check `debug_captcha/` directory), the solver quality may have degraded.
   Kill the batch before burning through 2Captcha credits on wrong solves.

## Architecture: Remote Debugging

### Why remote debugging instead of undetected_chromedriver

Chrome for Testing (WSL/Linux) can get flagged by Radware depending on IP, time
of day, and Chrome build. The browser fingerprint is often the problem, not the IP.

**Important qualification (June 2026)**: Testing from a Peruvian residential IP
with Chrome for Testing v149 + undetected_chromedriver successfully reached the
CEJ search page without any Radware block. The "permanently flagged" assertion
is **conditional, not absolute**. See the "Chrome Version Compatibility" section
for details on when WSL Chrome may work without remote debugging.

When WSL auto-mode fails (Radware blocks), fall back to remote debugging:

**Solution**: Connect to the user's REAL Chrome via CDP remote debugging.
The real Chrome has:
- Legitimate browser fingerprint (no "HeadlessChrome" UA)
- Existing session cookies from manual visits
- Real profile that passes behavioral checks

### Auto-launch only works from native Windows, not via WSL→PowerShell

The spider's auto-launch (`subprocess.Popen` in `__init__`) works correctly when running directly from a Windows terminal (PowerShell/CMD). But when invoked INDIRECTLY from WSL via the MCP server's `_run_spider()` which runs `powershell.exe` → `python -m scrapy crawl poder_opt`, `subprocess.Popen` from inside the MCP server's PowerShell call path does NOT propagate `--remote-debugging-port` reliably.

**Practical consequence**: When running spiders via MCP from WSL, Chrome must be pre-opened manually by the user. The MCP's `cej_start_spider` tool checks `_find_remote_debug_ports()` first and fails immediately if Chrome isn't on the expected port.

**Failed attempts to auto-launch from WSL** (all verified):

| Method | Result |
|---|---|
| `powershell.exe Start-Process` | Chrome opens but WITHOUT `--remote-debugging-port` flag |
| `powershell.exe -Command "& 'chrome.exe' ..."` | Same — flag lost |
| `cmd.exe /c start "" "chrome.exe" ...` | Timeout or parsing error |
| `terminal(background=true)` wrapper | Flag propagates but Chrome dies silently |
| Write temp .ps1 script and execute | Same as Start-Process — no flag |

**Manual launch is the only reliable path. User must open from native Windows PowerShell (not Win+R, not CMD). Give them the exact command to copy-paste.** See `references/wsl-to-windows-chrome-launch.md` for the full guide on what to do when the user asks "y lo puedes hacer tu?" — the answer is not to keep trying from WSL, but to give the user the working command.

**Verification**: From WSL, run:
```bash
powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress" | grep "remote-debugging-port=9222"
```

The spider auto-launches Chrome if not already running on the debug port:

```python
import socket, subprocess, time

debug_port = os.environ.get('REMOTE_DEBUGGING_PORT', '9222')
chrome_bin = os.environ.get('CHROME_BINARY_PATH',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')
cej_url = 'https://cej.pj.gob.pe/cej/forms/busquedaform.html'

# Check if Chrome already running on port
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
chrome_running = sock.connect_ex(('127.0.0.1', int(debug_port))) == 0
sock.close()

if not chrome_running:
    subprocess.Popen(
        [chrome_bin, f'--remote-debugging-port={debug_port}', cej_url],
        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    # Wait up to 20s for Chrome to start
    for _ in range(20):
        time.sleep(1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        if sock.connect_ex(('127.0.0.1', int(debug_port))) == 0:
            sock.close()
            break
        sock.close()
    time.sleep(2)  # Let page load

# Connect via undetected_chromedriver
opts = ChromeOptions()
opts.add_experimental_option('debuggerAddress', f'127.0.0.1:{debug_port}')
driver = Chrome(version_main=148, options=opts)
```

### Multi-spider production

Two Chrome instances on different ports, each with its own Excel slice:

```
Chrome :9222 → Spider A → slice_LA_DC_A.xlsx (19,121 exp)
Chrome :9223 → Spider B → slice_LA_DC_B.xlsx (19,121 exp)
```

Entry point pattern:
```python
os.environ['REMOTE_DEBUGGING_PORT'] = '9222'  # or '9223'
os.environ['PJ_INPUT_FILE'] = 'input\\slice_LA_DC_A.xlsx'
os.environ['PJ_SPIDER_ID'] = 'A'  # isolates checkpoints/CSVs
```

## Form Event Dispatching (Critical Fix)

### Problem

CEJ's JavaScript validation relies on native browser events that `execute_script`
does NOT fire:

- `onkeyup="saltoCajaTexto(event,this,N,'nextField')"` — only fires on real keystrokes
- `oninput` handlers — only fire on native keyboard input
- **`execute_script` + `dispatchEvent` gives ~72% max success rate**

### Root Cause

The `execute_script` approach sets `el.value` and fires synthetic events:

```python
execute_script("""el.value = x; el.dispatchEvent(new Event('input', {bubbles:true}));""")
```

This works for some fields but the CEJ's captcha input specifically needs the
native `onkeyup` that `send_keys()` triggers. `dispatchEvent` with Event('keyup')
does NOT activate `saltoCajaTexto()` correctly because synthetic keyup events
lack the real `KeyboardEvent.key` and `KeyboardEvent.code` properties that the
native handler inspects.

### THE Fix: send_keys() achieves 100%

The definitive fix is `send_keys()` on the captcha field:

```python
# REPLACES execute_script for the CAPTCHA field (other fields can stay as execute_script)
import random, time

captcha = solve_captcha()
field = driver.find_element(By.CSS_SELECTOR, '#codigoCaptcha')
field.clear()
time.sleep(random.uniform(0.3, 0.8))
field.send_keys(captcha.upper())  # CEJ captcha is case-insensitive uppercase
time.sleep(random.uniform(0.3, 0.7))
# Then click consultar...
```

**Impact**: Captcha success rate went from 72% (execute_script + input/change) to
**100%** (send_keys). Verified across hundreds of expeditions with both spiders.

**IMPORTANT**: `send_keys()` works for the captcha field because:
- It fires native `onkeyup` → `saltoCajaTexto()` validates correctly
- CEJ's captcha input has no autocomplete/formatting JS that interferes
- The captcha field is a simple text input, not a masked/district selector

### When to use execute_script vs send_keys

| Field | Method | Why |
|-------|--------|-----|
| Captcha (`#codigoCaptcha`) | `send_keys()` | Needs native onkeyup for validation |
| District court (`#cod_distprov`) | `execute_script` + `input` + `change` | Select2/JS dropdown |
| Specialty (`#especialidad`) | `execute_script` + `input` + `change` | Select2/JS dropdown |
| Expediente number | `send_keys()` | Same — needs native events |

### Diagnostic technique

If captcha rejects despite correct solve:

1. **Check if `send_keys()` was used** for the captcha field. If not, that's likely the cause.
2. Capture pre-submit HTML and verify `value` attribute is actually set (not cleared by a blur handler).
3. Check for `msjError` divs in post-fail HTML — they tell you which field failed.
4. Try the failing expediente manually in a browser to confirm it exists in CEJ.

### History

This went through multiple iterations before arriving at the definitive fix:

| Iteration | Method | Success Rate | Notes |
|-----------|--------|:---:|-------|
| 1 | execute_script only (value set) | ~33% | No events fired |
| 2 | execute_script + input + change | ~72% | Best before send_keys |
| 3 | execute_script + input + change + keyup | ~10% | saltoCajaTexto breaks |
| 4 | execute_script + input + change + keyup + blur | 0% | Fields cleared to "" |
| **5** | **send_keys()** | **100%** | **Definitive — native onkeyup fires** |

### Pitfalls — events that BREAK validation

- `input` + `change` + `keyup`: `saltoCajaTexto()` corrupts validation (10% rate)
- `input` + `change` + `keyup` + `blur`: Fields cleared to `value=""` (0% rate)
- The CEJ form has `onkeyup="saltoCajaTexto(event,this,N,'nextField')"` on each field —
this auto-advances focus AND validates. Firing a synthetic `keyup` with no real
keystroke data confuses `saltoCajaTexto`. Similarly, the `blur` handler runs a
validation pass that can RESET field values. **Stick to `send_keys()` for the captcha field.**

## Captcha Retry with Forced Refresh

### Problem

2captcha returns wrong codes ~30% of the time on CEJ's distorted text captcha.
The `#btnReload` click alone sometimes doesn't refresh the image (browser cache).

### Fix (production pattern)

Retry up to 5 times (current deployed value), forcing image cache-bust on each retry:

```python
MAX_CAPTCHA_RETRIES = 4  # 1 initial + 4 retries = 5 total attempts

for intento in range(1, MAX_CAPTCHA_RETRIES + 2):  # 1 initial + 4 retries = 5 total
    if intento > 1:
        # Force reload with cache bust
        driver.find_element(By.CSS_SELECTOR, '#btnReload').click()
        time.sleep(2)
        driver.execute_script(
            "var img = document.getElementById('captcha_image');"
            "if(img) img.src = img.src.replace(/[?&]t=\\\d+/, '') "
            "+ '?t=' + Date.now();"
        )
        time.sleep(random.uniform(1, 2))

    captcha = solve_captcha()  # your 2captcha logic
    driver.find_element(By.CSS_SELECTOR, '#codigoCaptcha').clear()
    driver.find_element(By.CSS_SELECTOR, '#codigoCaptcha').send_keys(captcha)
    driver.find_element(By.CSS_SELECTOR, '#consultarExpedientes').click()

    # Wait for results
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#command'))
        )
        break  # Success
    except:
        if intento <= MAX_CAPTCHA_RETRIES:
            continue  # Retry
        else:
            # Definitive failure — save to checkpoint and move on
            save_as_captcha_fail()
            # Also force a full CEJ page refresh to reset captcha session state.
            # Captcha failures can contaminate the session; a fresh page gives
            # a clean solver context for the next expediente.
            driver.get('https://cej.pj.gob.pe/cej/forms/busquedaform.html')
            time.sleep(random.uniform(3, 5))
            if detect_radware():
                time.sleep(60)  # backoff if Radware caught the reload
                driver.get('https://cej.pj.gob.pe/cej/forms/busquedaform.html')
                time.sleep(random.uniform(3, 5))
            return
```

## Captcha Solving: 2captcha Configuration & Image Quality

### Problem

The spider has a high captcha failure rate (~65%: 8 successes vs 15 failures in the last run, 554 total fails vs 334 successful download sessions). Causes span API parameters, image encoding, and solver selection.

### When send_keys also fails (20-25% success) — triage

`send_keys` was the definitive fix that brought success from ~72% to 100%. But in
production, the rate can drop back to 20-25% even with correct `send_keys` usage.
This is NOT a `send_keys` regression — it means the **captcha solving service**
(2captcha) is returning wrong codes at a high rate.

**Rapid triage steps when rate drops below 50%:**

1. **Count the fails**: `ls debug_captcha/ | wc -l` — if 500+ in a few hours,
   the solver is the problem, not the form submission.

2. **Check if Radware is active**: Look for `validate.perfdrive.com` or
   `CloseSpider('radware_blocked')` in logs. If no Radware signal, the CEJ
   form itself is rejecting the captcha codes — the solver returned wrong text.

3. **Verify a captcha manually**: Open the debug_captcha screenshot, read the
   captcha text with your own eyes. Compare to what 2captcha returned (not
   directly logged, so check the CSV status). If you can read it and 2captcha
   got it wrong, the solver quality dropped.

4. **Check 2captcha balance**: Low balance (< $1) causes degraded service tier:
   ```python
   import requests
   print(requests.get('https://2captcha.com/res.php?key=YOUR_KEY&action=getbalance').text)
   ```

5. **Known causes of sudden 2captcha degradation:**
   - **Time of day**: Weekends (like Sunday) and Latin America business hours
     see higher solver demand, lower accuracy
   - **Captcha format change**: CEJ may have rotated their captcha font/noise
     set. The distortion algorithm changes periodically
   - **Account throttling**: Excessive failed solves in a short window can
     trigger account-level quality downgrade
   - **IP-based solver assignment**: 2captcha routes to different solver pools
     based on requester IP

6. **Mitigations to try (in order of likelihood to help):**
   - Switch captcha capture from PNG → JPEG (smooths background noise):
     `c.toDataURL('image/jpeg', 0.85)` instead of `'image/png'`
   - Switch API v1 (`in.php`) → v2 (`createTask`): v2 uses AI-first models
     that may handle this captcha better
   - Reduce canvas size: use `img.width` (CSS) instead of `img.naturalWidth`
     (may be 2x on HiDPI). Smaller image = less noise for the solver
   - Add `phrase: 1` to v1 API or `Case: false` to v2 to tell the solver
     case doesn't matter (CEJ captcha is case-insensitive uppercase)

7. **If none of the above works**: The captcha solver may have permanently
   degraded for this captcha type. Consider switching solver (CapMonster,
   Anti-Captcha, manual solving) or reducing batch size and running outside
   peak hours.

**Key insight**: A drop from 100% to 20-25% with no code changes means the
solver service quality changed, NOT the spider logic. Don't revert `send_keys`
or fiddle with form events — those are proven correct. Focus on image encoding,
API version, and solver choice.

For a concrete example of this exact scenario, see
`references/2026-06-07-captcha-degradation.md`.

### Root Causes (by impact)

**1. Image quality: `toDataURL('image/png')` preserves noise**

The captcha capture uses canvas `toDataURL('image/png')` (no compression). For a captcha image that is **130x50px natural** (100x38px CSS — verified via `driver.execute_script` on the live CEJ page), this generates a ~20-30KB PNG file. On HiDPI displays the natural dimensions may be 260x100 (2x), yielding ~50-80KB PNG. More importantly, PNG preserves ALL background noise (lines, gradients, artifacts) that the CEJ captcha uses for distortion.

**Fix**: Use `toDataURL('image/jpeg', 0.85)` instead. JPEG compression:
- Reduces file size to ~15-30KB (well under 2captcha's 100KB limit)
- Smooths background noise through lossy compression
- Keeps the captcha text readable since characters are high-contrast vs background

```javascript
// Before: PNG preserves all noise artifacts
return c.toDataURL('image/png').split(',')[1];

// After: JPEG smooths background noise
return c.toDataURL('image/jpeg', 0.85).split(',')[1];
```

**2. Canvas resolution: `naturalWidth` vs CSS `width`**

`naturalWidth`/`naturalHeight` returns the image's intrinsic resolution, which can be 2x on HiDPI displays (e.g., 400x140 instead of 200x70). A larger canvas means more pixels = more noise to process. Using CSS `width`/`height` (or `clientWidth`/`clientHeight`) captures at display size.

```javascript
// Before: captures at native resolution (may be 2x on HiDPI)
c.width = img.naturalWidth;
c.height = img.naturalHeight;

// After: captures at display size (smaller, less noise)
c.width = img.width;
c.height = img.height;
```

**3. `numeric` parameter depends on captcha type — verify first**

The CEJ captcha is **4-character alphanumeric** (letters + numbers, **confirmed by user**).

| numeric value | Meaning | CEJ? |
|:---:|---|---|
| `0` (default) | Any character | ✅ Correct for mixed letters+numbers |
| `1` | Only numbers | ❌ Wrong — CEJ has letters |
| `2` | Only letters | ❌ Wrong — CEJ has numbers |
| `3` | Only numbers OR only letters | ❌ No — CEJ has both |
| `4` | MUST contain both numbers AND letters | 🔶 Over-restrictive — rejects pure-numeric or pure-alpha captchas |

Always verify the actual captcha content before setting `numeric`. If in doubt, use `0`.

**4. API version: v1 vs v2**

v1 (`in.php` / `res.php`) uses human solvers primarily — slower (15-30s), more expensive (~$2/1k). v2 (`createTask` / `getTaskResult`) uses AI-first — faster (5-15s), cheaper (~$1/1k), with explicit `minLength`/`maxLength` support. Migration to v2 is recommended for cost and speed regardless of `numeric` setting. See `references/2captcha-v2-migration.md` for the full migration guide.

**5. No `comment` for human fallback**

When the AI model fails, 2captcha escalates to human workers. Without a `comment`, workers see a raw captcha image with zero context. Testing showed comment doesn't always help since many responses are AI-only now.

**Fix**: Add a descriptive comment — low cost, might help human fallback cases:

```python
# v2
"comment": "captcha CEJ Peru 4 caracteres alfanumericos"
```

**6. Low retry count**

`MAX_CAPTCHA_RETRIES = 2` means only 3 total attempts (1 initial + 2 retries). Each retry fetches a fresh captcha image via `#btnReload` + cache-busting. Increasing to `MAX_CAPTCHA_RETRIES = 4` (5 total attempts) gives more chances for a good captcha solve.

### Currently Deployed Fix (v2 API + JPEG/display-size + comment)

The production spider (poder_opt.py) uses the **v2 API** (createTask/getTaskResult)
with JPEG encoding at display resolution. Deployed 2026-06-07 after v1 success
rate degraded to 9% (Sunday afternoon). Verified with 3/3 real captcha images
solved in 5-20s each. See `references/2captcha-v2-migration.md` for the full
migration guide.

```python
# In _get_captcha_code() (poder_opt.py):

# 1. JPEG encoding at display resolution (img.width, not naturalWidth)
captcha_b64 = self.driver.execute_script("""
    var img = document.getElementById('captcha_image');
    if (!img || !img.complete || img.naturalWidth === 0) return null;
    var c = document.createElement('canvas');
    c.width = img.width;           /* CSS dimensions, not naturalWidth */
    c.height = img.height;
    c.getContext('2d').drawImage(img, 0, 0, img.width, img.height);
    return c.toDataURL('image/jpeg', 0.85).split(',')[1];  /* JPEG not PNG */
""")

# 2. v2 API (api.2captcha.com/createTask) — AI-first, cheaper, faster
payload = {
    "clientKey": self.captcha_api_key,
    "task": {
        "type": "ImageToTextTask",
        "body": captcha_b64,
        "numeric": 0,            # 0=any char (CEJ is alphanumeric)
        "minLength": 4,
        "maxLength": 4,
        "comment": "captcha CEJ Peru 4 caracteres alfanumericos"
    }
}
resp = requests.post('https://api.2captcha.com/createTask', json=payload, timeout=30)
task_id = resp.json()['taskId']

# 3. Poll for result (v2)
poll_payload = {"clientKey": self.captcha_api_key, "taskId": task_id}
for attempt in range(30):
    sleep(5)
    poll = requests.post(
        'https://api.2captcha.com/getTaskResult',
        json=poll_payload, timeout=30
    ).json()
    if poll.get('status') == 'ready':
        return poll['solution']['text']

# 4. More retries
MAX_CAPTCHA_RETRIES = 4  # was 2
```

### Expected Impact (from test v2)

| Fix | Test Result |
|-----|-------------|
| JPEG encoding (smooths noise + smaller files) | **Negligible alone** — 60% vs 80% baseline (JPEG lost quality) |
| JPEG + numeric=4 (force both nums+letras) | **Matches baseline** — 80% (JPEG+n4) = 80% (PNG+n0) |
| Display-resolution canvas (not naturalWidth) | Reduces base64 size ~30% (4,655b avg → 3,135b) |
| Comment for workers | Not tested in isolation |
| More retries (2→4) | **WORSENS total time** if rate stays low (simulation: 872h vs 757h) |
| **Composite (PNG + n=0 + parallel A+B)** | **Best actionable** — parallel cuts time in half (379h vs 757h) |

**Key insight from testing**: The captcha image is 130x50px (not 200x70), much smaller than assumed. The dominant factor is **2captcha service quality**, not image format or numeric parameter. Neither format (PNG/JPEG) nor numeric hint (0/4) significantly changed outcomes in statistical testing (80% vs 60-80% over 5 iterations each). Parallel processing (A+B simultaneously) has the biggest predictable impact at ~50% time reduction.

### Pitfalls

1. **Don't assume numeric-only output from caption** — The CEJ captcha is alphanumeric (letters + numbers). `numeric: 1` will cause the solver to return only digits when the actual answer contains letters, guaranteeing 100% failure on those captchas. Verify before setting a non-zero numeric constraint.
2. **JPEG quality too low** (< 0.7) can degrade captcha text readability. 0.85 is a safe starting point.
3. **CSS dimensions vs natural** — `img.width` returns CSS pixel width (e.g., 100). `img.naturalWidth` returns intrinsic resolution (e.g., 130 at 1x, 260 at 2x on HiDPI). The CSS dimensions give a smaller, cleaner image for OCR. Verified CEJ captcha: natural=130x50, CSS=100x38.
4. **API key exposed in code** — Always use env vars (`TWOCAPTCHA_API_KEY`). The production entry points (`run_A_win_remote.py`, `run_B_win_remote.py`) hardcode the key — that's an acceptable practice for a single-user project but should NOT be committed to a public repo.
5. **No 2captcha balance check** — Before starting a batch, check balance to avoid mid-batch exhaustion: `requests.get('https://api.2captcha.com/res.php?key=YOUR_KEY&action=getbalance').text`
6. **Retries without fresh image = waste** — Always reload the captcha image on each retry (already done via `#btnReload` + `Date.now()` cache bust). Solving the same image again will produce the same wrong result.

## Checkpoint Management (Critical Gap)

### Problem: Checkpoint never depopulates

The checkpoint file (`checkpoint_opt_A.json` / `checkpoint_opt_B.json`) stores ALL remaining expedientes as a flat JSON list. When the spider runs, it loads the full list and processes the first few, but NEVER writes back a reduced list — so **every run restarts from the full list**, reprocessing already-downloaded expedientes and wasting captcha solves.

**Symptoms**:
- Checkpoint always shows N items (same as at start), never shrinks
- Same expediente gets processed multiple times across runs
- Already-downloaded PDFs accumulate alongside redundant CEJ queries
- E.g. in production: `167 of 243` checkpoint-A expedientes already had PDFs, but kept being re-queried because the checkpoint never reduced

**Diagnostic** — to detect this bug on any running spider:
```bash
# Compare checkpoint size vs actual documents
CHECKPOINT_SIZE=$(python3 -c "import json; print(len(json.load(open('checkpoint_opt_A.json'))))")
DOC_COUNT=$(find documents -maxdepth 2 -name '*.pdf' | wc -l)
echo "Checkpoint: $CHECKPOINT_SIZE pending, $DOC_COUNT PDFs on disk"
# If CHECKPOINT_SIZE hasn't changed across runs but DOC_COUNT grows,
# the checkpoint is NOT being depopulated
```

### Fix: Checkpoint-as-queue pattern

```python
import json

CHECKPOINT_PATH = 'checkpoint_opt_A.json'

def load_checkpoint():
    with open(CHECKPOINT_PATH) as f:
        return json.load(f)  # Returns full list

def pop_and_process():
    """Pop one item, process it, save the remainder back to disk."""
    queue = load_checkpoint()
    if not queue:
        return None
    
    current = queue.pop(0)  # Take first item
    success = process_item(current)
    
    # WRITE BACK the reduced queue — this is the line that's missing!
    with open(CHECKPOINT_PATH, 'w') as f:
        json.dump(queue, f, indent=2)
    
    return current, success
```

**Index-based approach** (simpler for parallel spiders where the shared worklist shouldn't be mutated by both):

```python
# Use a separate index file so both spiders can read the same worklist
CHECKPOINT_PATH = 'checkpoint_opt_A.json'
INDEX_PATH = 'checkpoint_index_A.json'  # Just an integer offset

def get_next_batch(batch_size=1):
    with open(INDEX_PATH) as f:
        idx = json.load(f)['next_index']
    with open(CHECKPOINT_PATH) as f:
        queue = json.load(f)
    
    batch = queue[idx:idx + batch_size]
    
    # Save new index
    with open(INDEX_PATH, 'w') as f:
        json.dump({'next_index': idx + batch_size}, f)
    
    return batch
```

### Pitfalls

1. **Don't re-process failed items unless designed for retry** — maintain a `checkpoint_failed.json` for captcha-fail items you want to retry in a separate pass.
2. **Don't write to disk after every single item if I/O is slow** — batch writes every N items (e.g., every 5) and accept at most N items of duplicate work on crash.
3. **Don't confuse checkpoint-index with the total list** — the checkpoint file always shows the full original list, not what's remaining. The size never changes in index-based mode. Track `documents/` folder growth instead.
4. **Verify checkpoint reduction after each session** — run this quick check to catch the bug early: `python3 -c "import json; cp=json.load(open('checkpoint_opt_A.json')); print(f'{len(cp)} pending')"`
5. **If PDFs exist but checkpoint is full = checkpoint bug, not a fresh start** — this combination means the spider keeps re-querying CEJ for already-downloaded expedientes. Fix checkpoint logic before running again.

## Rate Limiting Strategy

### Cooldown between expedientes

```python
def spider_idle(self):
    if not self.input_codes:
        return
    sleep(random.uniform(15, 30))  # Human-like pause
    # Schedule next expediente...
```

### Random sleeps throughout

```python
# NEVER use fixed sleeps:
sleep(5)          # ❌ predictable

# ALWAYS use random ranges:
sleep(random.uniform(5, 9))   # ✅ 5-9 seconds, unpredictable
sleep(random.uniform(8, 15))  # ✅ between documents
sleep(random.randint(5, 10))  # ✅ integer range
```

### AUTOTHROTTLE

```python
# settings.py
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
```

## Radware Block Detection

CEJ-specific signals (in priority order):

```python
def _is_radware_blocked(self):
    url = self.driver.current_url.lower()
    title = self.driver.title.lower()

    # 1. Radware redirect URL
    if 'validate.perfdrive.com' in url or 'radware' in url:
        return True

    # 2. Block page title
    if 'radware' in title or 'we apologize' in title:
        return True

    # 3. Delayed redirect (Radware can take 3-5s)
    sleep(random.uniform(3, 5))
    if 'validate.perfdrive.com' in self.driver.current_url.lower():
        return True

    # 4. CEJ loaded but search element missing
    #    USE ID NOT TITLE (accents cause false positives!)
    if 'cej.pj.gob.pe' in self.driver.current_url.lower():
        try:
            self.driver.find_element(By.ID, 'cod_expediente')
        except:
            return True

    return False
```

**Pitfall**: `[title="Por codigo de expediente"]` fails because the real title
has accent: `código`. Use `By.ID('cod_expediente')` instead.

## Chrome Version Compatibility

### version_main should match installed Chrome

The spider hardcodes `version_main=148` in `Chrome(**chrome_kwargs)`, for example
in the auto-launch code above. As of June 2026, the installed Chrome for Testing
is **v149**. The `undetected_chromedriver` patcher auto-downloads a matching
driver binary even with a slight mismatch, but this may produce warnings.

**Recommendation**: Verify the installed version and set `version_main` accordingly:

```bash
~/chromium/chrome-linux64/chrome --version
# → "Google Chrome for Testing 149.0.7827.54" → major version 149
```

```python
Chrome(version_main=149, browser_executable_path=CHROME_BIN, ...)
```

### WSL Chrome works (conditional — test first)

On 2026-06-10, `undetected_chromedriver` + Chrome for Testing v149 from a
Peruvian IP reached the CEJ search page without Radware blocking. This means the
"WSL Chrome is permanently blocked" rule is not absolute.

**Quick test before falling back to remote debugging**:
```bash
curl -sI --max-time 15 'https://cej.pj.gob.pe/cej/forms/busquedaform.html' \
  | grep -i '200\|radware\|perfdrive\|validate'
```
- `200 OK` without Radware headers → try WSL Chrome directly
- Radware headers (`__uzma` cookies, `validate.perfdrive.com` redirect) → use
  Windows real Chrome via remote debugging

**Factors that affect WSL Chrome accessibility (observed, not confirmed):**
- **IP origin**: Peruvian residential IPs fare better than datacenter/VPN IPs
- **Time of day**: Radware thresholds may vary by load
- **Chrome version**: Newer builds may have improved stealth properties
- **Session history**: Fresh profile with clean cookies works differently than one with prior flags

## Production Rate

With 2 spiders on Windows (real Chrome + remote debug, Peru IP, no VPN):

| Metric | Session 1 (v1 API) | Session 2 (v2 API deployed) |
|--------|:---:|:---:|
| Captcha success | 49% (583/1,182) | **12%** (37/299 out of 809 total) |
| Avg rate per spider | — | A: 15%, B: 9% |
| PDF folders on disk | 920 | 366 |
| Total processed | 1,182 exp | 809 exp |
| Spiders status | Running | **Idle** — stopped ~84min |

**State as of 2026-06-07**: Both spiders deployed with v2 API (createTask/getTaskResult),
JPEG q0.85 at display-size, 5x retries. Despite these mitigations, captcha success
dropped to 12% (A: 15%, B: 9%). The bottleneck remains the **2captcha solver quality**
for this specific captcha type, NOT spider logic. The form submission (send_keys,
retry logic) is proven correct.

**Indicators that the solver is the bottleneck, not spider logic:**
- No Radware signals observed in logs
- send_keys() method is unchanged from the 100% pattern
- v2 API migration didn't materially improve solve rate
- Rate is consistent across both independent spiders (A vs B)
- Most failures are 'captcha_fail' not network/Chrome errors

**Estimated remaining**: ~37,191 expedientes. At 12% rate that's ~310k captcha
solves (avg 5 per exp = 1/0.12). Consider solver alternatives or off-peak runs.

## Status Audit & Reporting

### Problem: Checkpoint ≠ Reality

The checkpoint file (`checkpoint_opt_A.json`) tracks what the spider HAS PROCESSED (including captcha fails), NOT what has PDFs on disk. This creates a gap:

- Expedientes with PDFs but NO checkpoint entry → "orphan" PDFs (28 in production)
- Expedientes IN checkpoint but NO PDF → captcha fails or "sin documentos" (76 in Spider A)
- `stats.py` reads checkpoint as truth → **reports wrong pending counts**

**Correct approach**: Always audit against disk state (`documents/` folder), not the checkpoint.

### Audit Script: Compare Slice vs Documents/

```python
import json, os, openpyxl

def audit_spider(sid, slice_path, doc_dir):
    """Returns pending count by cross-referencing slice Excel against disk."""
    # 1. Load slice
    wb = openpyxl.load_workbook(slice_path)
    ws = wb.worksheets[0]
    headers = [c.value for c in ws[1]]
    rows = []
    for row in ws.iter_rows(values_only=True, min_row=2):
        rows.append(dict(zip(headers, row)))
    wb.close()

    # 2. What's actually on disk
    downloaded = set(d for d in os.listdir(doc_dir) 
                     if os.path.isdir(os.path.join(doc_dir, d)))

    # 3. Cross-reference
    con_pdf = sum(1 for r in rows if str(r['N° EXPEDIENTE'] or '').strip() in downloaded)
    total = len(rows)
    pend = total - con_pdf

    return {
        'total': total,
        'con_pdf': con_pdf,
        'pendiente': pend,
        'pct': con_pdf / total * 100,
        'por_especialidad': ...  # group by r['ESPECIALIDAD']
    }
```

**Key insight**: This is independent of checkpoint management. Even with a perfect checkpoint-as-queue, you still need this audit to answer "what's really left?"

### Generate a pendientes.csv

For operational use (e.g., loading into another tool or retrying captcha-fails):

```python
def export_pendientes(rows, doc_dir, output_path='pendientes.csv'):
    import csv
    downloaded = set(d for d in os.listdir(doc_dir) 
                     if os.path.isdir(os.path.join(doc_dir, d)))
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['EXPEDIENTE', 'PARTE', 'ESPECIALIDAD'])
        for r in rows:
            exp = str(r['N° EXPEDIENTE'] or '').strip()
            if exp not in downloaded:
                w.writerow([exp, str(r.get('PARTE PROCESAL','') or '').strip(), r.get('ESPECIALIDAD','')])
```

### Orphan detection

To find PDFs not tracked by any checkpoint:

```python
def find_orphans(doc_dir, *checkpoint_paths):
    downloaded = set(d for d in os.listdir(doc_dir) 
                     if os.path.isdir(os.path.join(doc_dir, d)))
    ckp_exps = set()
    for cp in checkpoint_paths:
        try:
            with open(cp) as f:
                ckp_exps.update(i.split('|')[0] for i in json.load(f))
        except:
            pass
    orphans = downloaded - ckp_exps
    return orphans  # Re-import or manually rerun these if needed
```

## Pitfalls Summary

1. **Parallel downloads = Radware DDoS detection**. Always serial.
2. **requests.Session() = TLS correlation**. Use independent requests.get().
3. **execute_script without input/change events = silent form rejection**. CEJ needs `input` + `change` events. Do NOT add `keyup` or `blur` — both break validation (verified in production: 10% and 0% success respectively).
4. **Testing with one expediente = misleading results**. The first expediente in a test file may not exist in CEJ (verified: 00060-2021-0-1801-JR-DC-03 fails 100% of the time while other expedientes succeed at 72%). Use at least 5 unique expedientes for diagnostics.
5. **Fixed sleeps = timing fingerprint**. Always random.uniform().
6. **Title selector with accents = false positive**. Use By.ID instead.
7. **WSL Chrome for Testing = can be flagged by Radware (test first)**. A curl
   connectivity check (`curl -sI ... | grep`) before choosing between WSL
   Chrome and Windows real Chrome saves unnecessary setup. On Peruvian
   residential IPs, WSL Chrome often works without remote debugging.
8. **Captcha retry without cache-bust = same image re-solved**. Force reload with `Date.now()`.
9. **No checkpoint = lost progress on crash**. Always save after each expediente.
10. **VPN datacenter IPs = still blocked**. Peru direct IP works fine.
11. **Hardcoded API keys in code = leaked to git**. Use env vars (TWOCAPTCHA_API_KEY), but ensure ALL entry points set it before importing scrapy.
12. **Solver degradation is NOT a spider bug** — If `send_keys()` was working at 100% and suddenly drops to 20-25% with no code changes, don't revert form events. The 2captcha solver service quality changed. Check balance, time of day (Sundays are worse), try JPEG/display-size capture, increase retries, and force page refresh between fails. Reverting proven fixes wastes time.
13. **Checkpoint never depopulated = silent reprocess bug**. The checkpoint file is loaded each run but NEVER written back with reduced content. Every run re-queries CEJ for already-downloaded expedientes, wasting captcha solves and inflating API costs. If the checkpoint size stays the same across runs but PDFs keep accumulating, this is the bug. Fix: add `json.dump(queue, f)` after each pop (see "Checkpoint Management" section).
14. **Captcha session contamination between fails** — After repeated captcha failures,
    the CEJ page session state degrades (the captcha loading mechanism gets confused).
    Always force a full page reload (`driver.get(cej_url)`) after a definitive fail,
    not just `#btnReload`. Without this, the next expediente starts with a
    contaminated session and fails at the same rate. Production fix: refresh + wait
    3-5s, then detect Radware, then 60s backoff if blocked.
15. **`cej_url` `UnboundLocalError` when Chrome is already running** — The auto-launch block (`if not chrome_ya_abierto`) defines `cej_url` locally. If Chrome is already open (the common case), the variable is never assigned, and `driver.get(cej_url)` on line ~161 throws `UnboundLocalError`. **Fix**: define `cej_url` unconditionally *after* the `if` block, not inside it:
   ```python
   # Always define cej_url — needed regardless of Chrome launch path
   cej_url = 'https://cej.pj.gob.pe/cej/forms/busquedaform.html'
   ```
   This applies both when running from native Windows PowerShell (where auto-launch does work) and from WSL (where Chrome is pre-opened by the user).

16. **Chrome process accumulation across restarts** — Each re-launch of Chrome with `--remote-debugging-port` and `--user-data-dir` spawns a new process tree while old ones linger. Over 3-4 restart cycles this can grow to 40-50 Chrome processes and 10+ orphan Python processes. Some spiders stop connecting because their debug port is owned by an orphan process. Fix: full kill of ALL Chrome and Python before re-launching (see `references/multi-spider-launch-powershell.md` "Clean Restart" section).

17. **Fresh profiles for reliability** — Reusing the same `pj_perfil_A`/`pj_perfil_B` profiles across restarts can accumulate corrupted session state. Use fresh profile dirs (`pj_A_fresh`, `pj_B_fresh`) with `--no-first-run --no-default-browser-check` flags when doing a clean restart.

18. **Scrapy project module not found (No module named 'poder_judicial_results')** —
    `scrapy.cfg` lives at the repo root (`D:\PyCode\poder_judicial_results-PY-OK\`),
    but the spider module is nested inside `DescargaPJ_optimizado\poder_judicial_results\`.
    Running `scrapy crawl` from the spider directory fails. Fix: `cd` to the repo root
    (where scrapy.cfg is) and add `DescargaPJ_optimizado` to `PYTHONPATH`:
    ```powershell
    cd D:\PyCode\poder_judicial_results-PY-OK
    $env:PYTHONPATH="D:\PyCode\poder_judicial_results-PY-OK\DescargaPJ_optimizado;$env:PYTHONPATH"
    scrapy crawl poder_opt
    ```

20. **`chrome_dead` recovery: watchdog required for long batches** — Chrome
    for Testing in WSL crashes every 5-15 minutes (CloseSpider('chrome_dead')).
    While the checkpoint correctly saves progress so no work is lost, manual
    relaunch does NOT scale for 25-30 hour batches. Use the watchdog script
    (`scripts/watchdog.sh`) which auto-relaunches on crash up to 100 times:
    ```bash
    bash watchdog.sh A   # Spider A, relanza hasta 100 veces
    bash watchdog.sh B   # Spider B, relanza hasta 100 veces
    ```
    The watchdog v2 detects `chrome_dead`, `radware_blocked`, `Remote end closed
    connection`, `Connection refused`, `Max retries exceeded`, and normal
    completion. On any detected error it kills orphan Chrome processes before
    relaunching. On `radware_blocked` it waits 60s before retry. On normal
    completion (batch finished) it exits cleanly. Run as a background Hermes process:
    ```
    terminal(background=true, notify_on_complete=true, timeout=360000,
        command="cd /path && bash watchdog.sh A > logs/watchdog_A.log 2>&1")
    ```
    See `scripts/watchdog.sh` for the full script (v2 since June 2026).

21. **`completó su batch normalmente` false positive** — The v1 watchdog exited
    on ANY non-chrome_dead/non-radware exit code, assuming it was "normal
    completion". This is wrong: Chrome startup can fail with exit code 1 and
    NO `Spider closed (chrome_dead)` message in the log, leaving 400+ items
    unprocessed. Symptom: the watchdog says "completó su batch normalmente" but
    the checkpoint grew by only 1-2 items. The v2 watchdog adds broader crash
    pattern detection (`Connection refused`, `Remote end closed`, etc.) and
    also checks `item_scraped_count` — if 0 items were scraped and exit ≠ 0,
    it retries.

22. **WSL auto-mode specifics** (verified 2026-06-29):
    - Both spiders running from WSL Chrome auto-mode consumed ~1.2GB RAM total (includes 2 Chrome instances + 2 Python processes)
    - Captcha solved on first attempt consistently in test runs
    - Chrome profile dirs created automatically: `.chrome_profile/pj_perfil_A` / `pj_perfil_B`
    - Logs directory (`logs/`) should be created before launching
    - Mini-slice batch files should use a distinctive name (e.g., `_wsltemp`) to distinguish from production slices
    - The spider auto-launches Chrome with `--no-sandbox --disable-dev-shm-usage --disable-gpu` flags in WSL mode
    - **Chrome for Testing in WSL crashes frequently (~5-15 min)** — this is not a bug in the spider, it's WSL instability with the Chrome renderer. Always use the watchdog script for batches longer than ~30 minutes. The spider's checkpoint ensures no work is lost on crash, but the watchdog ensures the batch keeps running unattended.

23. **Watchdog exhaustion after ~100 retries — detailed mechanism** — Chrome for Testing in WSL degrades cumulatively across watchdog restart cycles. After ~100 total attempts, every fresh Chrome launch fails immediately with `Remote end closed connection without response` during `Chrome(**chrome_kwargs)`. Even deleting `CHROME_USER_DATA_DIR` profiles doesn't help — the binary's own user config (`~/.config/google-chrome-for-testing/`) is corrupted. The fundamental cause is **orphan Chrome child processes** (zygote, GPU, crashpad handlers) that survive watchdog `pkill` and accumulate across cycles, eventually preventing new Chrome from starting. **Fix — comprehensive kill of ALL Chrome state** + **preventive fix: `--single-process` flag** (stops orphans from being created in the first place):
    ```bash
    kill -9 $(ps aux | grep -E "(chrome|chromium|run_A_wsl|run_B_wsl|undetected)" | grep -v grep | awk '{print $2}') 2>/dev/null
    rm -rf ~/chromium/chrome_profile_A_fresh ~/chromium/chrome_profile_B_fresh
    rm -rf /path/to/.chrome_profile/pj_perfil_A /path/to/.chrome_profile/pj_perfil_B
    rm -rf ~/.config/google-chrome-for-testing/  # Chrome binary's OWN global config!
    ```
    After this reset, expect another 20-30 stable runs before degradation returns. Spider B's Chrome consistently outlasts Spider A's (fewer watchdog cycles).

## Code Quality Notes

### `\d+` SyntaxWarning in JavaScript string

Line 380 of `poder_opt.py` triggers a Python SyntaxWarning:
```
SyntaxWarning: invalid escape sequence '\d'
```
The line has:
```python
"if(img) img.src = img.src.replace(/[?&]t=\\d+/, '') + '?t=' + Date.now();"
```
Python interprets `\\d` as `\d`, which is not a recognized Python escape, so it
triggers the warning. The string is then passed verbatim to the browser JS engine
where `\d+` correctly matches digits — so the code WORKS at runtime, but the
warning is noise that obscures real issues.

**Fix**: Use a raw string for the JS code:
```python
self.driver.execute_script(
    r"var img = document.getElementById('captcha_image');"
    r"if(img) img.src = img.src.replace(/[?&]t=\d+/, '') + '?t=' + Date.now();"
)
```
This tells Python to treat `\d` as literal characters, passing the correct
JavaScript regex to the browser.

## Reference Files

- `references/captcha-test-results.md` — Full test results from two rounds of captcha-method comparison (PNG vs JPEG, numeric=0 vs numeric=4, simulation completion-time estimates). Includes actual captcha codes returned and failure patterns.
- `references/diagnosing-form-failures.md` — Step-by-step methodology for diagnosing why CEJ rejects captcha-solved forms. Covers screenshot+HTML capture, msjError analysis, onkeyup/saltoCajaTexto debugging, and distinguishing systemic vs expediente-specific failures.
- `references/checkpoint-audit.md` — Diagnostic script and methodology for detecting the 'checkpoint never depopulated' bug where the spider re-queries CEJ for already-downloaded expedientes.
- `references/2026-06-07-captcha-degradation.md` — Session analysis of captcha success dropping from 100% to 20-25% with no code changes. Documents the triage path and recommended mitigations for when the solver (not spider logic) degrades.
- `references/wsl-to-windows-chrome-launch.md` — Guide for launching Chrome with `--remote-debugging-port` from WSL: what fails, what works, and the user-flow when asked "y lo puedes hacer tu?".
- `references/multi-spider-launch-powershell.md` — Full production launch sequence for both spiders (A + B) from PowerShell: open Chrome instances, run spiders, monitor progress, stop, and common errors.
- `references/nodejs-vs-python-evaluation.md` — Evaluation of Node.js (puppeteer-extra-stealth) vs Python (undetected-chromedriver) for CEJ scraping. Conclusion: stay with Python due to WSL↔Windows path/process management issues.
- `references/2026-06-10-session-audit.md` — Session audit from 2026-06-10: E2E test results, current download state (373 exp with PDFs, 0.98%), and findings (Chrome v149 works, CEJ accessible from WSL, \\d+ SyntaxWarning).
- `references/2026-06-29-production-run.md` — Production run of June 29-30: WSL auto-mode E2E test, `chrome_dead` crash timing and recovery, files created for batch limiting, watchdog exhaustion at 100 retries, fresh profiles fix, Spider B stability advantage. Final results: 2,376 PDFs across 1,440 expedientes.
- `references/waf-testing-with-vulnerable-spider.md` — Using a deliberately vulnerable spider (plain selenium.webdriver.Chrome) as a negative control to validate Radware blocking behaviour. Covers stripping all anti-detection measures, observed failure modes (validate.perfdrive.com redirect, null DOM elements), and how to distinguish WAF blocks from spider logic bugs using A/B comparison. Corresponding project: `D:\PyCode\cej-scraper-vulnerable\`.

## Scripts

- `scripts/watchdog.sh` — Watchdog v2 for long-running WSL batches. Auto-relaunches spider on Chrome/WebDriver crashes (up to 100 attempts). Usage: `bash watchdog.sh A` / `bash watchdog.sh B`. See reference file for exhaustion recovery.
- `scripts/check_status.sh` — Lightweight progress monitor (~25 lines bash). Reads checkpoints, counts PDFs on disk, checks process liveness via `ps aux`. Simpler than `stats.py` (155 lines Python).

## External References

- [`mcp-server-authoring::references/wsl-to-windows-mcp-pattern.md`](mcp-server-authoring::references/wsl-to-windows-mcp-pattern.md) — MCP server with HTTP transport to start/stop/monitor these CEJ spiders from Hermes in WSL. Covers server code, Windows startup script, Hermes config wiring, and pitfalls for cross-platform process management.
