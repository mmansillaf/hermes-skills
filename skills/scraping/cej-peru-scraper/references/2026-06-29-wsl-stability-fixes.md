# 2026-06-29/30 Production Run — WSL Auto-Mode Stability Fixes

## Summary

14-hour session processing 615 CEJ expedientes (+1,435 PDFs) from WSL using Chrome for Testing.
Key findings: Chrome stability fixes (`--single-process`), comprehensive watchdog kill, fresh profiles.

## What Worked

- **WSL auto-mode (no remote debugging)**: Both spiders ran entirely from WSL with Chrome for Testing.
- **Watchdog v2**: Correctly detected 5 crash patterns vs v1's 2. Ran up to 100 retries per spider.
- **Fresh profiles via CHROME_USER_DATA_DIR**: Extended viable watchdog runtime vs project-level profiles.
- **Mini-slices**: Batch limiting via 500-item slices worked perfectly with checkpoint-based resume.

## What Didn't Work (Fixed)

| Problem | Fix | Effect |
|---------|-----|--------|
| Remote debugging mode raises `TypeError: Binary Location Must be a String` | Use normal mode (no REMOTE_DEBUGGING_PORT) | WSL auto-mode works |
| Chrome child processes (zygote, GPU, crashpad) survive `pkill -f "pj_perfil_A"` as orphans | `kill -9` on ALL chrome/chromedriver processes | No orphans after crash |
| Zombie `<defunct>` processes accumulate and can't be killed | `--single-process` + `--no-zygote` prevents forking | No child processes = no zombies |
| Chrome degrades after ~30 watchdog cycles (Connection refused) | Comprehensive kill + `--single-process` + fresh profiles | 80+ stable cycles |
| Watchdog says "completó su batch normalmente" but processed 0 items | v2 pattern matching catches `Connection refused`, `Remote end closed` | Correct retry |

## Chrome Flags Deployed

```python
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--disable-gpu')
opts.add_argument('--disable-software-rasterizer')
opts.add_argument('--single-process')           # KEY: no child processes
opts.add_argument('--no-zygote')                # no fork sandbox
opts.add_argument('--no-crash-upload')           # no crash reporter
opts.add_argument('--disable-background-networking')
opts.add_argument('--disable-sync')
opts.add_argument('--disable-blink-features=AutomationControlled')
opts.add_argument('--window-size=1920,1080')
opts.add_argument('--start-maximized')
```

## Numbers

- Time: 15:22 → 05:22 (14h)
- Before: 825 checkpoint, 941 PDFs, 373 exp with data
- After: 1,440 checkpoint, 2,376 PDFs, 855 exp with data
- Net new: +615 exp, +1,435 PDFs, +482 exp with data
- Target 1,000: 61.5% complete
- Storage: 204 MB → 527 MB (+323 MB)
- Spider A: 404 → 675 (+271)
- Spider B: 421 → 765 (+344)

## Remaining for Resume

- Spider A batch 2: `slice_A_1000_wsltemp_2.xlsx` (~334 remaining)
- Spider B original batch: `slice_B_1000_wsltemp.xlsx` (~156 remaining)
- Total remaining to hit 1,000: ~385

## Clean Restart Procedure

```bash
# 1. Kill ALL Chrome processes
kill -9 $(ps aux | grep -E "(chrome|chromium)" | grep -v grep | awk '{print $2}') 2>/dev/null

# 2. Delete profiles + binary config
rm -rf ~/chromium/chrome_profile_A_fresh ~/chromium/chrome_profile_B_fresh
rm -rf ~/.config/google-chrome-for-testing/
rm -rf /path/to/.chrome_profile/pj_perfil_A /path/to/.chrome_profile/pj_perfil_B

# 3. Launch watchdogs
cd /mnt/d/PyCode/poder_judicial_results-PY-OK/DescargaPJ_optimizado/poder_judicial_results
mkdir -p logs
bash watchdog.sh A > logs/watchdog_A_resume.log 2>&1 &
bash watchdog.sh B > logs/watchdog_B_resume.log 2>&1 &
```
