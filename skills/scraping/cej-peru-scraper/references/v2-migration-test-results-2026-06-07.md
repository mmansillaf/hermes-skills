# 2captcha v2 API — Real-World Test Results (2026-06-07)

## Context

Captcha success rate on CEJ degraded from ~47% (v1, June 5) to **9%** (v1, June 7).
818 debug_captcha screenshots accumulated. The spider code (send_keys, JPEG display-size,
retries) was confirmed correct — the 2captcha solver service quality degraded,
likely due to Sunday afternoon peak in LATAM.

## Migration Applied

Migrated `_get_captcha_code()` from v1 (`in.php`/`res.php`) to v2 (`createTask`/`getTaskResult`)
in `poder_opt.py`. Changes:
- POST to `https://api.2captcha.com/createTask` (JSON body)
- Poll via `https://api.2captcha.com/getTaskResult` (JSON body)
- Added `"comment": "captcha CEJ Peru 4 caracteres alfanumericos"`
- Kept JPEG q0.85 + display-size canvas (img.width, not naturalWidth)

## Test Results

Tested with 3 real captcha images from `debug_captcha/` directory:

| Captcha image (from fail screenshot) | Base64 size | v2 solve time | Result |
|--------------------------------------|-------------|:---:|---|
| `fail_25332-2023-0-1801-JR-LA-15_*.png` | 131,076b (~100KB) | 15s | `LNJ0` |
| `fail_25338-2023-0-1801-JR-LA-18_*.png` | 133,300b (~102KB) | 5s | `2vi8` |
| `fail_25347-2023-0-1801-JR-LA-23_*.png` | 127,764b (~97KB) | 20s | `7K00` |

**Result: 3/3 (100%) solved in 5-20s average.** All responses are 4-char alphanumeric,
confirming `numeric=0` is the correct setting.

## Comparison: v1 vs v2

| Metric | v1 (`in.php`) | v2 (`createTask`) |
|--------|:---:|:---:|
| Solver type | Human-first | AI-first |
| Avg solve time | 15-30s | 5-20s |
| Cost per 1k | ~$2 | ~$1 |
| `comment` support | No | Yes (helps human fallback) |
| Test result (3 real CEJ captchas) | N/A (not tested same set) | 3/3 (100%) |
| Production rate (June 7) | 9% (13/147) | Pending real spider test |

## Next Steps

- Run a real spider test with 5-10 expedientes to measure production v2 rate
- If v2 stabilizes above 70%, switch both spiders permanently
- If v2 also degrades, the limiting factor is the CEJ captcha distortion itself,
  not the solving service — consider manual solving or reduced batch size
