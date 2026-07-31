# Captcha Improvement Test Methodology

## Principle: Never modify production without isolated validation

The user's explicit rule: *"no modifiques este proyecto hasta tenerlo probado"* (don't modify this project until it's tested).

When proposing captcha (or any CEJ scraper) improvements, **always create a standalone test script first**.

## The Test Script Pattern

Create a self-contained script that:

1. **Uses a separate Chrome port** (e.g., `:9225` — never clash with production `:9222`/`:9223`)
2. **Tests MULTIPLE approaches on the SAME expedient** — so results are comparable
3. **Captures diagnostic artifacts** (image samples, timing, structured JSON report)
4. **Does NOT import or modify any production module**

### Test script skeleton

```python
"""
test_captcha_improvement.py — Standalone test, no production imports.
"""
import os, sys, time, base64, json, requests
from datetime import datetime

# Config
API_KEY = os.environ['TWOCAPTCHA_API_KEY']
CHROME_PORT = '9225'              # Separate from production :9222/:9223
TEST_EXP = '00399-2021-0-1801-JR-DC-01'  # Known-working expedient

# Chrome setup
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By

opts = ChromeOptions()
opts.add_experimental_option('debuggerAddress', f'127.0.0.1:{CHROME_PORT}')
driver = Chrome(version_main=148, options=opts)

# Test multiple approaches
results = []
for method_name, capture_fn, numeric in [
    ('A_PNG_numeric0', capture_png, 0),
    ('B_JPEG_numeric0', capture_jpeg, 0),
    ('C_JPEG_resized', capture_jpeg_resized, 0),
    ('D_HTTP_comment', capture_http, 0),    # + comment for human workers
    ('E_JPEG_numeric4', capture_jpeg, 4),   # force nums+letters
    ('F_HTTP_numeric4', capture_http, 4),
]:
    result = run_test(driver, TEST_EXP, capture_fn, numeric)
    results.append(result)
    print(f"{method_name}: {'✅' if result['success'] else '❌'} "
          f"captcha={result.get('code','N/A')} size={result.get('size','?')}b")

# Generate JSON report + save captcha image samples
report = {'timestamp': datetime.now().isoformat(), 'results': results}
with open('test_report.json', 'w') as f:
    json.dump(report, f, indent=2)
```

## Test Structure — What to Vary

Test ONE variable at a time while keeping everything else constant:

### Variable 1: Image Source
| Method | Description | Why test it |
|--------|-------------|-------------|
| Canvas PNG | `toDataURL('image/png')` | Current baseline |
| Canvas JPEG | `toDataURL('image/jpeg', 0.85)` | Smaller file, noise smoothed |
| Canvas JPEG resized | `img.width` not `img.naturalWidth` + JPEG | Smaller resolution |
| HTTP direct | HTTP GET the captcha image URL | Original JPEG from server |

### Variable 2: solve Parameters
| Parameter | Value | Meaning |
|-----------|:-----:|---------|
| `numeric` | `0` | Any character |
| `numeric` | `1` | Only numbers |
| `numeric` | `4` | Must contain numbers AND letters |
| `comment` | text | Instructions for human workers |

### Variable 3: API Version
| API | Endpoint | Cost | Speed |
|-----|----------|:----:|:-----:|
| v1 | `in.php` / `res.php` | ~$2/1k | 15-30s |
| v2 | `createTask` / `getTaskResult` | ~$1/1k | 5-15s |

## Measuring Success

Each test captures:
- **Success/failure** — Did the captcha solve result in CEJ returning `#command`?
- **Timing breakdown** — How long did each phase take? (navegar, llenar, capturar, resolver, submit)
- **Image size** — Base64 or raw bytes (important: 2captcha limit is 100KB for Normal Captcha)
- **Image sample** — Save the actual image sent to 2captcha for visual inspection
- **Error message** — If fail, was it a 2captcha error or a form validation error?

```python
result = {
    'method': method_name,
    'exp': exp_code,
    'success': True/False,
    'code': 'ABCD' or None,       # captcha solved value
    'size_bytes': 12345,           # image size
    'error': 'error message' if fail else None,
    'timing': {
        'navegar': 4.2,            # s
        'llenar': 0.8,
        'capturar': 0.05,
        'resolver': 8.3,
        'submit': 1.2,
        'total': 14.55,
    }
}
```

## The Report

Generate a structured JSON report that can be compared across test runs:

```json
{
    "timestamp": "2026-06-05T19:30:00",
    "expediente": "00399-2021-0-1801-JR-DC-01",
    "captcha_info": {
        "naturalWidth": 400,
        "naturalHeight": 140,
        "clientWidth": 200,
        "clientHeight": 70
    },
    "results": [
        {
            "method": "A_PNG_numeric0",
            "success": false,
            "size_bytes": 58932,
            "timing": {"total": 18.5},
            "error": "Captcha rechazado"
        },
        {
            "method": "B_JPEG_numeric0",
            "success": true,
            "code": "A3B2",
            "size_bytes": 21456,
            "timing": {"total": 12.3}
        }
    ]
}
```

## Pitfalls

1. **Don't test only one expedient** — the first one in the test file may not exist in CEJ (verified: some expedientes fail 100% of the time). Use at least 5 unique ones.
2. **Don't skip sleep between tests** — CEJ/Radware will rate-limit rapid retries. Add 2-3s delay between runs.
3. **Don't reuse the same Chrome session for hours** — Radware's behavioral tracking may flag long-running automated sessions. The production runner rotates Chrome every 90 minutes.
4. **Don't test on the production port** — `:9222` and `:9223` are for the running spiders. Use `:9225` for tests.
5. **Don't draw conclusions from a single test run** — captcha success is probabilistic. Each method needs 5+ attempts for statistical significance.
6. **Isolate the capture from the solve** — If a method fails, was it because the image quality was bad or because 2captcha just returned the wrong answer? Save the image so you can visually inspect it or re-test it manually.
