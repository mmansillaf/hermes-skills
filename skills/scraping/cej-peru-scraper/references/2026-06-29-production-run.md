# Production Run — June 29-30, 2026

## Summary

Launched 2 spiders (A + B) in WSL auto-mode to process ~1,000 expedientes
using mini-slices (500 each). First full E2E test of the WSL pipeline from
Hermes with watchdog auto-recovery.

**Final result (session 1)**: Spider A completed its entire 500-item batch after 18 watchdog
attempts. Spider B processed 572 items (still running at end of session).
Total: 207 new expedientes, 467 new PDFs in 3h 24min.

After first batch completion, Spider A was given a second batch (500 exp,
03559 → 06794, file `slice_A_1000_wsltemp_2.xlsx`). Watchdog A needed only
2 attempts (1 chrome crash + 1 completion) for the second batch, processing
~1 item before completing normally.

**Final result (session 2, June 30 continuation)**: Watchdog A exhausted all
100 retries by 05:09 (Chrome became non-functional after repeated crashes).
Spider B kept running and reached 765. Total today: +615 expedientes,
+1,435 PDFs, 61.5% of the 1,000-target. Spider A consumed 100 watchdog
attempts across both batches. Spider B's Chrome was more stable.

## Timeline

### Day 1 — June 29

| Event | Time | Details |
|-------|------|---------|
| Test run (A only) | 15:18-15:20 | 1 exp (02709), 4 PDFs, captcha OK first try |
| Launch A (prod) | 15:22 | PID 5844, Chrome pj_perfil_A, mini-slice A (500) |
| Launch B (prod) | 15:24 | PID 6254, Chrome pj_perfil_B, mini-slice B (500) |
| Chrome crash A-1 | ~15:32 (10 min) | chrome_dead after 5 items |
| Watchdog A-2 | 15:33 | Manual relaunch |
| Chrome crash B-1 | ~15:37 (13 min) | chrome_dead after 6 items |
| Watchdog B-2 | 15:38 | Manual relaunch |
| Chrome crash A-2 | ~15:39 (6 min) | chrome_dead after 2 items |
| Watchdog A-3 | 15:39 | Auto-relaunch (watchdog.sh created) |
| Chrome crash A-3 | ~16:17 (38 min) | chrome_dead — longest A run yet |
| Watchdog A-4 | 16:17 | Auto-relaunch |
| Chrome crash B-2 | ~16:35 (57 min) | chrome_dead — longest B run yet |
| Watchdog B-3 | 16:35 | Auto-relaunch |
| Chrome crash A-4→17 | 16:36→18:30 | Rapid crashes (~2-15 min each) |
| **Spider A completed** | **18:45** | **500 items done after 18 watchdog attempts** |
| Relaunch A batch 2 | 20:13 | Second batch (500 exp, slice_A_1000_wsltemp_2) |
| Chrome crash A-1 (b2) | 20:18 (5 min) | chrome_dead, watchdog auto-relaunched |
| Watchdog A-2 (b2) | 20:19 | Normal completion after 2 attempts |

### Day 2 — June 30 (continuation)

| Event | Time | Details |
|-------|------|---------|
| Watchdog A exhausted retries | 05:09 | Attempt 100/100 failed (Remote end closed). Chrome completely non-functional. A checkpoint: 675 |
| Watchdog A-6 (fresh profiles, remote debug fix) | 20:40 | Switched to `CHROME_USER_DATA_DIR=~/chromium/chrome_profile_A_fresh`, removed `REMOTE_DEBUGGING_PORT` |
| Watchdog B-3 (fresh profiles) | 21:11 | Same fix for B |
| A checkpoint growing | 21:14-22:54 | 505 → 564 (+59) with fresh profile |
| B checkpoint growing | 21:14-22:54 | 579 → 649 (+70) |
| **Session end** | **22:54** | **A alive (intento ~40), B alive** |

### Day 3 — June 30 (early morning, post-session)

| Event | Time | Details |
|-------|------|---------|
| Watchdog A final | 05:09 | Exhausted 100 retries after ~8h of runs |
| B still alive | 05:09 | PID 42596, checkpoint 765 |
| **Final totals** | **05:09** | **A=675, B=765, Total=1,440, PDFs=2,376** |

## Watchdog performance details

Spider A needed 18 attempts to finish its first 500-item batch. Crash frequency
was highly variable — some runs lasted 38 min, others only 2-6 min.

| Attempt range | Spider | Runtime range | Items per attempt (approx) |
|----------|--------|:---:|:---:|
| 1-5 | A | 2-10 min | ~2-3 |
| 6-10 | A | 5-15 min | ~3-5 |
| 11-15 | A | 8-20 min | ~5-8 |
| 16-18 | A | 5-30 min | ~8-15 |
| 1-3 | B | 13-57 min | ~20-30 |

**Pattern**: Chrome crashes are unpredictable — no progressive improvement
after the initial boot. The watchdog is essential for unattended operation.
The crash frequency does NOT correlate with runtime (longer runs don't predict
more crashes later).

### Watchdog exhaustion (100 attempts)

After ~100 watchdog attempts for Spider A, Chrome for Testing became
completely non-functional — every attempt failed immediately during
`Chrome(**chrome_kwargs)` initialization with `Remote end closed connection
without response`. This is a Chrome binary state issue in WSL, not a spider
bug.

**Mitigation attempted**: Deleting Chrome profiles (`.chrome_profile/pj_perfil_A/`)
and switching to fresh profiles (`~/chromium/chrome_profile_A_fresh/`) helped
briefly but didn't prevent eventual exhaustion. The Chrome binary itself may
accumulate state in its user config directory (`~/.config/google-chrome-for-testing/`).

**Practical workaround**: Kill the watchdog and restart both A and B watchdogs
simultaneously after a clean state reset:
```bash
pkill -f "chrome\|chromium\|run_A_wsl\|run_B_wsl\|undetected" -9 2>/dev/null
rm -rf ~/chromium/chrome_profile_A_fresh ~/chromium/chrome_profile_B_fresh
# Then relaunch both watchdogs
```

### Fresh profiles fix (June 30, 20:40 onward)

Chrome crashed every 1-3 minutes after the first round of attempts.
The project's `.chrome_profile/pj_perfil_A/` directory was corrupted from
18+ watchdog restart cycles. Switching to `CHROME_USER_DATA_DIR` pointing to
`~/chromium/chrome_profile_A_fresh` (outside the project directory) improved
stability — Spider A processed 1 full expediente (captcha OK first try, 3 PDFs)
on the next attempt.

**Key finding**: Even with fresh profiles, Chrome crashes every 1-2 items
per attempt after ~40+ total watchdog attempts. The WSL Chrome renderer
instability is progressive and cumulative.

**Remote debugging mode failed**: Setting `REMOTE_DEBUGGING_PORT` without also
passing `browser_executable_path` to undetected_chromedriver causes:
```
TypeError: Binary Location Must be a String
```
Fix: remove `REMOTE_DEBUGGING_PORT` and set `CHROME_BINARY_PATH` +
`CHROME_USER_DATA_DIR` instead (normal auto-launch mode).

## Aggregate stats

### Before session (historical totals before today)

| Metric | Value |
|--------|:---:|
| Checkpoint A | 404 |
| Checkpoint B | 421 |
| **Total checkpoint** | **825** |
| Expedientes con PDF | 373 |
| PDFs descargados | 941 |
| Tamaño en disco | 204 MB |

### After Day 1 (15:22 → 18:46 = 3h 24min)

| Metric | Value | Delta |
|--------|:---:|:---:|
| Checkpoint A | 500 | **+96** |
| Checkpoint B | 532 | **+111** |
| **Total checkpoint** | **1,032** | **+207** |
| Expedientes con PDF | 535 | **+162** |
| **PDFs descargados** | **1,408** | **+467** |
| Tamaño en disco | 305 MB | **+101 MB** |

### After Day 2-3 (15:22 → next day 05:09 = 13h 47min)

| Metric | Value | Delta this session |
|--------|:---:|:---:|
| Checkpoint A | 509 → 675 | **+271** |
| Checkpoint B | 532 → 765 | **+344** |
| **Total checkpoint** | **1,440** | **+615** |
| Expedientes con PDF | 535 → 855 | **+482** |
| **PDFs descargados** | **1,408 → 2,376** | **+968** |
| Tamaño en disco | 305 MB → 527 MB | **+222 MB** |

### Rates

| Metric | Day 1 (3.5h) | Combined (14h) |
|--------|:---:|:---:|
| Combined rate | ~61 exp/h | ~45 exp/h |
| PDF yield per 1,000 | ~2,256 | ~1,575 |
| PDFs per exp with data | 2.9 | 2.9 |
| Captcha first-try success | ~100% | ~100% |

**Note**: The rate drops when averaging over 14h because Chrome crash frequency
increases with cumulative watchdog attempts. The first 3h after a fresh start
are always the most productive.

## Files created/used

```
poder_judicial_results/
  run_A_wsl.py                    — WSL entry point (A), CHROME_BINARY_PATH mode
  run_B_wsl.py                    — WSL entry point (B), CHROME_BINARY_PATH mode
  launch_both_wsl.sh              — parallel launcher (deprecated by watchdogs)
  check_status.sh                 — lightweight progress monitor (disk + ps)
  watchdog.sh                     — auto-relaunch watchdog v2 (100 retries)
  logs/
    spider_A_watchdog_*.log       — 100+ per-attempt logs for A
    spider_B_watchdog_*.log       — ~15 per-attempt logs for B
    watchdog_A_6.log              — Final watchdog run (fresh profile, v2, exhausted 100 retries)
    watchdog_B_3.log              — B's v2 watchdog (still running at session end)
  input/
    slice_A_1000_wsltemp.xlsx     — mini-slice Spider A batch 1 (500 exp)
    slice_B_1000_wsltemp.xlsx     — mini-slice Spider B (500 exp)
    slice_A_1000_wsltemp_2.xlsx   — mini-slice Spider A batch 2 (500 exp)
```

## Key learnings

1. **Watchdog is non-negotiable for WSL batches** — Without it, manual
   intervention every 5-15 minutes is required. With it, 500 items completed
   unattended despite 18 Chrome crashes.

2. **Watchdog exhaustion is real** — After ~100 retries, Chrome for Testing in
   WSL becomes completely non-functional. The watchdog gives up. A clean
   restart (kill all Chrome/Python, delete profiles, relaunch) resets the state.

3. **Fresh profiles help but don't solve Chrome instability** — Switching from
   `.chrome_profile/pj_perfil_A/` to `~/chromium/chrome_profile_A_fresh/` gave
   temporary improvement but the underlying Chrome-for-WSL renderer instability
   remained.

4. **Checkpoint growth is monotonic** — Even with watchdog exhaustion, the
   checkpoint correctly saved every processed expediente. No work was lost.
   The next run (with fresh watchdog) resumes from the checkpoint.

5. **Exit code 1 = normal completion** — The watchdog checked for `chrome_dead`
   and `radware_blocked` in the log. When neither was found but exit code was
   non-zero, it assumed normal completion and stopped. For Spider A at attempt
   18, exit code 1 meant the batch was done (no more items in mini-slice).

6. **Captcha solves are reliable on Monday afternoon** — All captchas in this
   session solved on first attempt. Previous sessions (Sunday) had high failure
   rates. Time of day / day of week affects 2captcha solver quality.

7. **check_status.sh is simpler than stats.py** — The monitor script reads
   checkpoint files, counts PDFs on disk, checks `ps aux` for live processes,
   and reports du -sh for disk usage. All in ~25 lines of bash vs 155 lines of
   Python in stats.py.

8. **Chaining batches works smoothly** — After completing the first 500-item
   batch, a new mini-slice with the next 500 items was created and the
   watchdog was relaunched pointing at it. The checkpoint automatically skips
   already-processed items, so no special cleanup was needed.

9. **Mini-slice overlap is benign** — If the second mini-slice contains items
   already in the checkpoint, the spider finishes immediately (\"completó su
   batch normalmente\" with 0-1 items). No duplicate processing, no errors.
   Just update the input file with a fresh set of unprocessed expedientes.

15. **Spider B's Chrome is consistently more stable** — Across both days,
    Spider B crashed less frequently and ran longer per attempt (up to 57 min)
    than Spider A (max 38 min). Probable cause: B's Chrome profile is less
    contaminated (fewer watchdog restart cycles). When running A + B
    simultaneously, A's crashes don't affect B's stability.

## Detailed Crash Analysis (from watchdog A_6, 100 attempts)

### Crash type distribution

| Crash type | Count | Percentage |
|-----------|:-----:|:----------:|
| `Connection refused` | 1,949 | **63.4%** |
| `Remote end closed connection` | 397 | 12.9% |
| `chrome_dead` | 393 | 12.8% |
| `Max retries exceeded` | 138 | 4.5% |
| `Connection aborted` | 117 | 3.8% |
| `invalid session` | 30 | 1.0% |
| Other/unidentified | 48 | 1.6% |
| **Total** | **~3,072** | **100%** |

### System resources at end of session (after watchdog exhaustion)

| Resource | Value | Status |
|----------|:-----:|:------:|
| Memory | 14 GB free (of 15) | ✅ Healthy |
| Swap | 822 MB used (of 4 GB) | ✅ Healthy |
| `/dev/shm` | 0% used (of 7.9 GB) | ✅ Not the cause |
| Active PIDs | 42 (of 4,194,304 max) | ✅ Not exhausted |
| Residual Chrome processes | 7 (1 zombie `<defunct>`) | ⚠️ Leaking |

### Zombie/orphan analysis

The 7 residual processes after final kill:
```
chrome (main)            ← not cleaned by pkill if spider already dead
chrome_crashpad_handler  ← NOT killed by `pkill -f "pj_perfil_A"` — no profile path in args
chrome_crashpad_handler  ← same
chrome --type=zygote     ← same
chrome --type=zygote     ← same
chrome --type=gpu-process ← same
[chrome] <defunct>       ← ZOMBIE — unkillable, parent already dead
```

### Timeline of degradation (watchdog A_6)

| Attempt range | Runtime | Items/attempt | Failure mode |
|:---:|:---:|:---:|---|
| 1-6 | 0-5 min | 0 | Startup failure (corrupted old profile) |
| 7-20 | 3-15 min | 2-14 | `chrome_dead` mid-operation (best performance) |
| 21-40 | 5-30 min | 3-11 | Peak sustained productivity |
| 41-60 | 2-10 min | 1-4 | Rapid degradation begins |
| 61-80 | 0-5 min | 0-1 | Mostly `Connection refused` |
| 81-100 | 0-3 min | 0 | Complete failure — Chrome can't start |

### Key insight: the `~/.config/google-chrome-for-testing/` corruption

Deleting project-level profiles (`.chrome_profile/pj_perfil_A/`) and switching to
fresh profiles (`~/chromium/chrome_profile_A_fresh/`) only helped for ~10-20
attempts. The actual root cause of final exhaustion was Chrome's **own global
config directory** at `~/.config/google-chrome-for-testing/`. This directory
stores:
- Crash report metadata (from the crashpad handlers)
- Extension cache (`extensions_crx_cache/`)
- Component updates (`component_crx_cache/`)
- Safe Browsing data
- Certificate revocation data

After repeated crashes, lock files or corrupted data in this directory prevents
Chrome from initializing. The spider's `--user-data-dir` profile is separate.

**Fix for clean restart after exhaustion**:
```bash
kill -9 $(ps aux | grep chrome | grep -v grep | awk '{print $2}') 2>/dev/null
rm -rf ~/.config/google-chrome-for-testing/
rm -rf ~/chromium/chrome_profile_A_fresh ~/chromium/chrome_profile_B_fresh
```
