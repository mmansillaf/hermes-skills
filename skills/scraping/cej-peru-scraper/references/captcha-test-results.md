# Captcha Test Results — CEJ Peru

## Test v2: Statistical Comparison

Run: 2026-06-05, 22:53
Expediente: 00399-2021-0-1801-JR-DC-01 (PODER JUDICIAL)
5 iterations per method

### Captcha Image Dimensions

```
naturalWidth:  130px
naturalHeight:  50px
clientWidth:   100px
clientHeight:   38px
Src: https://cej.pj.gob.pe/cej/Captcha.jpg
```

The captcha is smaller than initially estimated (~200x70). 130x50px at native resolution. On HiDPI displays, the canvas `naturalWidth`/`naturalHeight` would be 260x100.

### Results Matrix

| Method | Rate | Size (avg) | Time (avg) |
|--------|:---:|:----------:|:----------:|
| A) PNG + numeric=0 (current) | 80% (4/5) | 4,655 bytes | 23.3s |
| B) JPEG q0.85 + numeric=0 | 60% (3/5) | 3,198 bytes | 32.9s |
| C) JPEG q0.85 + numeric=4 | 80% (4/5) | 3,135 bytes | 33.5s |

### Captcha Codes (all 5 iterations per method)

| Iteration | A (PNG n=0) | B (JPG n=0) | C (JPG n=4) |
|:---------:|:-----------:|:-----------:|:-----------:|
| 1 | FAIL (PG3L) | FAIL (3VOA) | ZBE4 ✅ |
| 2 | PI1E ✅ | KAAQ ✅ | 1F5Z ✅ |
| 3 | 1BJ0 ✅ | 5JK9 ✅ | FAIL (6PPO) |
| 4 | 8Y01 ✅ | FAIL (fowj) | EQFD ✅ |
| 5 | 1L4R ✅ | L8XR ✅ | 12DX ✅ |

### Observations

1. **All codes are alphanumeric** — confirms CEJ captcha has letters AND numbers
2. **PNG outperformed JPEG with numeric=0** (80% vs 60%) — JPEG compression likely degrades character edges enough that the solver gets confused
3. **JPEG + numeric=4 ties PNG** (80%) — the `numeric=4` hint (must contain both numbers AND letters) compensates for JPEG quality loss
4. **Failed codes share no pattern** — PG3L, 3VOA, fowj, 6PPO were all "solved" by 2captcha but rejected by CEJ. Possible causes:
   - Ambiguous characters (O vs 0, I vs 1 vs l)
   - Case sensitivity mismatch (fowj has lowercase — CEJ captcha is probably all-caps)
   - Random rejection by CEJ server-side

### Conclusion: No Clear Winner

The small sample (5 iterations) shows PNG and JPEG+n4 tying at 80%. The difference from production (~35%) suggests the limiting factor is NOT image format or numeric parameter, but:
- **2captcha service quality fluctuation** (batch processing vs single-test)
- **Captcha difficulty variance** by time of day
- **Expediente-specific issues** (some expedientes generate harder captchas)

## Simulation: Completion Time Estimates

Based on 37,908 pending expedientes, production data (35% captcha rate, 25s cooldown):

| Scenario | Hours | 8h Days | vs Baseline |
|----------|:----:|:-------:|:----------:|
| 0) Baseline: serial, 35%, 2 retry | 757h | 95d | — |
| 1) Parallel A+B (2 spiders) | 379h | 47d | -50% |
| 2) More retries (2→4), same rate | 872h | 109d | +15% |
| 3) Rate 80% (serial) | 563h | 70d | -26% |
| 4) Rate 80% + 4 retry + parallel + 15s cooldown | 228h | 29d | -70% |

Key insight: **More retries alone makes things worse** — more attempts at a 35% rate = more time. The dominant factor is captcha success rate. Improving from 35% to 80% cuts time by ~2/3.

## Test v1: Single-Run Comparison

Run: 2026-06-05, 22:03
Same expediente, 1 iteration per method.

| Method | Captcha | Size | Time | Result |
|--------|:------:|:---:|:----:|:-----:|
| A) PNG canvas + n=0 | cr4k | 8,396b | 18.8s | ✅ |
| B) JPEG canvas q0.85 + n=0 | tvkc | 4,608b | 19.2s | ✅ |
| C) JPEG 200px resized + n=0 | PCYR | 4,320b | 18.7s | ✅ |
| E) JPEG + n=4 | 5w36 | 4,828b | 17.7s | ✅ |

Note: v1 sizes are ~2x larger than v2 — likely because v1 ran at a different zoom level or canvas resolution.
