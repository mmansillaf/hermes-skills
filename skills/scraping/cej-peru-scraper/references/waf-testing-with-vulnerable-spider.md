# WAF Testing with a Deliberately Vulnerable Spider

## Why Create a Vulnerable Spider?

When debugging WAF/anti-bot systems (Radware, Cloudflare, DataDome), it's easy to
confuse "WAF blocking the spider" with "spider logic bug." A **control spider** that
omits all anti-detection measures serves as a negative control:

| Scenario | Vulnerable spider | Production spider | Diagnosis |
|----------|:-----------------:|:-----------------:|-----------|
| WAF is up | ❌ Blocked (Radware page) | ✅ Works | WAF active, anti-detection working |
| WAF down / IP whitelisted | ✅ Works (surprise) | ✅ Works | No blocking happening (remove controls?) |
| Logic bug in spider | ❌ Blocked (Radware) | ❌ Blocked (Radware) | Not a logic bug — WAF is blocking |
| Logic bug in spider | ✅ CEJ accessible | ❌ Fails differently | Spider code has a bug, not WAF |

## What to Remove

To build a vulnerable control, strip everything that makes `undetected_chromedriver`
work against Radware:

| Feature | Production | Vulnerable |
|---------|-----------|------------|
| Driver class | `undetected_chromedriver.Chrome` | `selenium.webdriver.Chrome` |
| CDP patches | `Page.addScriptToEvaluateOnNewDocument` (navigator.webdriver, plugins, languages) | None |
| `--disable-blink-features=AutomationControlled` | ✅ Set | ❌ Omitted |
| User-Agent | Matching Chrome version (e.g., Chrome/148.0.0.0) | Generic old UA (e.g., Chrome/91) |
| Sleep timing | `random.uniform(5, 9)` — unpredictable | `sleep(5)` — fixed, predictable |
| Form input | `send_keys()` — fires native onkeyup | `execute_script` — sets value, no events |
| HTTP sessions | Independent `requests.get()` per download | `requests.Session()` — shared, TLS correlatable |
| Download parallelism | Serial (1 doc at a time) | `ThreadPoolExecutor(max_workers=3)` — DDoS pattern |
| Rate limiting | AUTOTHROTTLE + cooldown (15-30s) | None (CONCURRENT_REQUESTS=16) |
| Radware detection | `_is_radware_blocked()` — closes spider early | None — spider runs blind |

## Observed Failure Modes (plain selenium.webdriver.Chrome)

When tested against CEJ (cej.pj.gob.pe) from a Peruvian residential IP, the
vulnerable spider fails in this order:

1. **Navigation**: Radware redirects to `validate.perfdrive.com` with title
   "Radware Captcha Page". This happens on the FIRST or SECOND navigation —
   sometimes the first request passes, then Radware blocks on interaction.

2. **Form elements**: `document.getElementById('cod_expediente')` returns `null`
   because the CEJ DOM was never loaded — the browser is on the Radware captcha page.
   Any `execute_script` attempting to set fields throws:
   ```
   javascript error: Cannot set properties of null (setting 'value')
   ```

3. **Captcha**: `#captcha_image` doesn't exist on the Radware page, so captcha
   solving is impossible.

4. **Selenium detection**: `navigator.webdriver` remains `true` (no CDP patch),
   `chrome.runtime` is detectable, and `--disable-blink-features=AutomationControlled`
   is absent — all signals Radware uses for fingerprinting.

## Practical Notes

- **Run the vulnerable spider first** to establish that the WAF is active against
  bare Selenium. If it succeeds, there's no point debugging anti-detection — the
  WAF is already bypassed.

- **Run the production spider next**. If it also fails with the same Radware redirect,
  the anti-detection measures are insufficient — not a spider logic bug.

- **HTTP requests (requests library) may still get 200 OK** even when Selenium is
  blocked. Radware differentiates between browser automation and plain HTTP —
  HTTP requests may pass while Selenium sessions are intercepted. This is normal.

- **IP matters**: From a Peruvian residential IP, the vulnerable spider was blocked
  ~50% of the time. From a datacenter/VPN IP, it was blocked 100% of the time.

## Project Template

A fully-functional vulnerable spider project exists at:
`D:\PyCode\cej-scraper-vulnerable\`

Includes:
- `spiders/poder_vuln.py` — Spider without any anti-detection
- `run_vuln.py` — Entry point with automated tests
- `input/expedientes_muestra.xlsx` — 100 sample expedientes
- `settings.py` — CONCURRENT_REQUESTS=16, no AUTOTHROTTLE
