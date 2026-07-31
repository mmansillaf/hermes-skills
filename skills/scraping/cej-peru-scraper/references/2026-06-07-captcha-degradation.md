# 2026-06-07: Captcha degradation from 100% to 20-25%

## Symptoms

- After 2 days of perfect 100% captcha success with `send_keys()`, rate dropped to 20-25%
- Both spiders (A and B) affected equally
- No code changes between the 100% and 20-25% periods
- No Radware signal detected (`_is_radware_blocked()` returned False)
- 650+ debug_captcha screenshots in ~2.5 hours
- Pattern: captcha accepted by form (no msjError visible), but no results page

## Root Cause

**The 2captcha solver degraded its accuracy for the CEJ captcha type.** Not a spider logic issue. `send_keys()` was and remains the correct approach.

Likely factors:
1. **Sunday afternoon** — higher solver demand, lower accuracy pool
2. **Captcha font/noise rotation** — CEJ may have rotated their distortion set
3. **Same API v1** — no change in solver configuration

## Mitigations Applied (same session)

1. **PNG -> JPEG q0.85**: smoother background noise for the solver
2. **naturalWidth -> img.width**: smaller canvas (display size, not HiDPI 2x)
3. **MAX_CAPTCHA_RETRIES 2->4**: more chances per expediente (5 total attempts)
4. **Page refresh on definitive fail**: force full CEJ page reload between expedientes to reset captcha session state

## Git commit

`2a6ff76` — "Fix captcha: JPEG display-size + MAX_RETRIES 4 + refresh on fail"

## Recommended Next Steps (if mitigations don't restore to 50%+)

1. **API v1 -> v2**: Migrate from `2captcha.com/in.php` to `api.2captcha.com/createTask`
   — v2 uses AI-first models that may handle this captcha better
2. **Check 2captcha balance**: Low balance (<$1) degrades solver tier
3. **Alternate solver**: Try Anti-Captcha or CapMonster as fallback
4. **Run outside peak hours**: Sunday afternoon appears to be worst time
