---
name: web-scraping-waf-bypass
description: "Bypass WAF/bot-detection (Radware, Cloudflare, DataDome) for web scraping using rebrowser-playwright, stealth patches, and captcha-solving services (2Captcha/NopeCHA). Includes Radware-specific techniques, fingerprint management, and rate-limiting strategies."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [radware, waf-bypass, captcha, rebrowser-playwright, scraping, anti-bot, web-scraping, 2captcha, hcaptcha]
    related_skills: [project-audit-and-reporting]
---

# Web Scraping — WAF/Anti-Bot Bypass

Systematic approach for scraping websites protected by WAF/bot-detection systems (Radware, Cloudflare, DataDome, etc.) using stealth browser automation + captcha-solving services.

## When to Use

- Target site shows a Radware/Cloudflare/DataDome captcha page
- Plain curl/requests/playwright headless gets blocked
- Site returns `server: rdwr` (Radware), challenge pages, or captcha walls
- User asks to scrape a government, legal, or high-security site

## Prerequisites

- `rebrowser-playwright` installed (drop-in replacement for playwright-python with stealth patches)
- `2captcha-python` or `requests` for captcha solving
- API key for 2Captcha (https://2captcha.com) or NopeCHA (https://nopecha.com)
- Chrome/Chromium installed locally (for `channel='chrome'` mode)

## Step 1 — Reconnaissance (before writing code)

First, identify what you're up against:

```bash
curl -sI https://target-site.com | grep -i 'server\|set-cookie\|x-frame\|csp\|hsts'
```

**WAF signatures:**

| Header/Cookie | WAF |
|---|---|
| `server: rdwr` | Radware |
| `__uzma`, `__uzmb`, `__uzmc` cookies | Radware |
| `validate.perfdrive.com` in redirect URL | Radware |
| `cf-ray`, `__cf_bm` cookie | Cloudflare |
| `server: cloudflare` | Cloudflare |
| `x-datadome` header | DataDome |

**Test direct access:**
```bash
curl -s -o /dev/null -w '%{http_code}' https://target-site.com/page.html
```

If blocked (403/302 to captcha page), proceed to Step 2.

## Step 2 — Fingerprint Preparation

Use `rebrowser-playwright` (not plain playwright). It patches `Runtime.enable` CDP detection, the #1 signal that anti-bot systems use.

### Basic stealth setup (Python):

```python
from rebrowser_playwright.sync_api import sync_playwright

pw = sync_playwright().start()
browser = pw.chromium.launch(headless=True, args=[
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
])

context = browser.new_context(
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport={"width": 1920, "height": 1080},
    locale="es-PE",  # match target country
    timezone_id="America/Lima",  # match target timezone
)

# Critical CDP patches
context.add_init_script("""
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['es-PE', 'es', 'en'] });
""")

page = context.new_page()
```

### Radware detection helper

After any navigation, check if Radware blocked the request:

```python
def _is_radware_blocked(driver_or_page):
    """Detect Radware block by URL, title, and DOM signals."""
    try:
        url = driver_or_page.current_url.lower()
        title = driver_or_page.title.lower()
    except:
        url = driver_or_page.url.lower()
        title = driver_or_page.title.lower()
    
    # Signal 1: perfdrive redirect
    if 'validate.perfdrive.com' in url or 'radware' in url:
        return True
    # Signal 2: known Radware title
    if 'radware' in title or 'we apologize' in title or 'captcha page' in title:
        return True
    # Signal 3: page loaded but search form missing (partial block)
    if 'cej.pj.gob.pe' in url:
        try:
            el = driver_or_page.find_element(By.ID, 'cod_expediente')
            if not el: return True
        except:
            return True
    return False
```

### Chrome Remote Debugging Pattern (Windows — best Radware bypass)

The most effective way to bypass Radware is **not to use a headless browser at all**. Instead, connect to a real Chrome instance running on Windows with a persistent user profile:

```batch
:: Windows: Launch Chrome with remote debugging
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9225
```

```python
# Python: Connect to the real Chrome
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9225")
driver = webdriver.Chrome(options=options)

# Navigate to CEJ — no Radware, no captcha
driver.get("https://cej.pj.gob.pe/cej/forms/busquedaform.html")
```

**Why this works**: Real Chrome with a persistent profile = legitimate browser fingerprint. Radware sees a genuine user session. The user's cookies, cache, and previous browsing history all contribute to a trust score that bypasses the bot manager.

**Architecture pattern for production** (used in poder_judicial_results project):
- Spider A: Chrome on port 9222 (first half of data)
- Spider B: Chrome on port 9223 (second half of data)
- `runner.py` auto-restarts each spider every 90 minutes (rotate profile before Radware fingerprint builds up)
- Checkpoint JSON ensures no duplicate work after restart
- `stats.py` monitors real disk state (PDFs in `documents/`) vs checkpoint

**Pitfall**: Only one IP (the user's real IP). For large-scale scraping, still need proxy rotation. But for reconnaissance and small-volume extraction, this eliminates the captcha problem entirely.

### For stubborn WAFs:
- Use `headless=False` with a real Chrome installation (`channel='chrome'`)
- Use residential proxies (Bright Data, Decodo, DataImpulse)
- Consider `nodriver` (drives Chrome directly via CDP, no Playwright shim)
- Consider SeleniumBase "Stealthy Playwright Mode"

## Step 3 — Route Selection (critical for Radware)

Radware does NOT block all routes equally. Test multiple entry points:

```python
# Try the main page FIRST (often less protected than deep links)
page.goto("https://target.com/main-page.html", timeout=30000, wait_until="domcontentloaded")

# Check if blocked
if "perfdrive" in page.url.lower() or "radware" in page.title().lower():
    # Blocked — proceed to captcha solving
    pass
else:
    # Access granted! Navigate internally
    pass
```

**Key finding from CEJ (Poder Judicial Peruano):**
- `busquedaform.html` → **accessible** without Radware blocking
- `busquedacodform.html` direct GET → **blocked** by Radware + HTTP 405
- Always check if there's an alternative entry point that triggers less WAF scrutiny

## Step 4 — Captcha Detection and Solving

### Detect hCaptcha:

```python
sitekey = None
for f in page.frames:
    if "hcaptcha" in f.url and "sitekey=" in f.url:
        import re
        m = re.search(r'sitekey=([a-f0-9-]+)', f.url)
        if m:
            sitekey = m.group(1)
            break

# DOM fallback
if not sitekey:
    sitekey = page.evaluate("""
        () => {
            const el = document.querySelector('[data-sitekey]');
            return el ? el.getAttribute('data-sitekey') : null;
        }
    """)
```

### Solve with 2Captcha (hCaptcha):

```python
from twocaptcha import TwoCaptcha
solver = TwoCaptcha("YOUR_API_KEY")
result = solver.hcaptcha(sitekey=sitekey, url=page.url)
token = result.get('code')
```

### Solve with 2Captcha (Image-to-text captcha):

```python
# v2 API (createTask/getTaskResult)
payload = {
    "clientKey": api_key,
    "task": {
        "type": "ImageToTextTask",
        "body": base64_image,
        "numeric": 0,
        "minLength": 4,
        "maxLength": 4
    }
}
resp = requests.post('https://api.2captcha.com/createTask', json=payload)
task_id = resp.json().get('taskId')
# Poll getTaskResult every 5s until 'ready'
```

### Inject token:

```python
page.evaluate("""
    (token) => {
        const ta = document.querySelector('textarea[name="h-captcha-response"]');
        if (ta) { ta.value = token; ta.style.display = 'block'; }
        if (typeof hcaptcha !== 'undefined') {
            try { hcaptcha.setResponse(token); } catch(e) {}
        }
    }
""", token)

# Click submit
page.query_selector('button[type="submit"], input[type="submit"]').click()
time.sleep(5)
```

## Step 5 — Rate Limiting and Cooldown

Radware correlates TCP/TLS connections. Key rules:

| Strategy | Why |
|---|---|
| **No shared requests.Session()** | Radware correlates connections; use fresh sessions |
| **Serial downloads** (not parallel) | Parallel bursts trigger DDoS detection |
| **Random sleep 8-15s between actions** | Fixed intervals are bot-like |
| **Cooldown 15-30s between items** | Gives Radware time to forget the session |
| **Rotate Chrome profile every 90 min** | Long-lived sessions get fingerprinted |
| **Auto-reinicio con checkpoint** | Spider crashes are common; resume from last success |

## Step 6 — Security Audit Methodology (for WAF-protected sites)

When the WAF blocks direct scanning, audit through the browser:

### What CAN be tested through the WAF:
- HTTP security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options, etc.)
- Cookie security flags (HttpOnly, Secure, SameSite)
- CSRF token presence/validity
- Technology fingerprint (via headers, JS patterns, error pages)
- Clickjacking vulnerability (missing X-Frame-Options)

### What CANNOT be tested (WAF blocks):
- SQL injection (WAF terminates malicious requests before reaching the app)
- XSS (same)
- Path traversal (same)
- Deserialization attacks
- Actual server fingerprinting (WAF masks the real server)

### How to test the un-testable:
1. **Get inside the WAF** using a real Chrome profile + residential proxy
2. Intercept traffic with mitmproxy or Burp Suite
3. If the site uses JSF, intercept `javax.faces.ViewState` and test for deserialization
4. Fuzz parameters through the browser's JS context (page.evaluate can bypass URL-level WAF rules)

## Step 7 — Proxy/VPN Strategy Decision Matrix

Not all proxies are equal against Radware. Choose based on volume and environment:

| Scenario | Solution | Cost | Effectiveness |
|---|---|---|---|
| **Audit/recon** (< 50 requests) | Proton VPN (free/paid) or Bright Data free datacenter tier | Free-$5 | Moderate — datacenter IPs may still trigger Radware |
| **Small volume** (50-500 requests) | Residential proxy rotativo (DataImpulse $1/GB, Decodo $3/GB) | $1-10 | High — residential IPs are trusted more |
| **Mass extraction** (> 500 requests) | Residential proxy + Chrome real profile + 2Captcha + rate limiting | $10-50+ | Highest — multi-layer bypass |
| **Windows + Chrome debug** (any volume) | `--remote-debugging-port=9225` + real user profile | Free | Highest — Radware doesn't trigger at all |

### Proton VPN Analysis

**When it works**: Proton VPN provides IPs from real ISPs (not datacenter ranges). For reconnaissance (< 50 requests), it often bypasses Radware because:
- The IP hasn't been flagged for automated access
- Proton's IPs come from ISP partnerships (residential-like reputation)

**When it does NOT work**:
- For sustained scraping (50+ requests from one IP → Radware flags the IP)
- When Radware specifically blocks known VPN provider ranges (some Proton IPs are in threat intel feeds)
- Proton's free tier only has 3 countries (NL, US, JP) — may not have Peruvian IPs for geo-targeting

**Bottom line**: Good for auditing, insufficient for mass extraction.

## References

- `references/cej-pj-gob-pe.md` — Specific workflow for scraping the Peruvian Judicial Branch CEJ site

## Pitfalls

1. **`rebrowser-playwright` error messages are noise** — The `[rebrowser-patches][frames._context] cannot get world` error is harmless. It's a side-effect of the CDP patch and doesn't affect functionality.
2. **Radware is intermittent** — Same IP, same fingerprint, same route can work one minute and be blocked the next. The block depends on session state, request velocity, and backend load.
3. **Radware deploy differences per environment** — The SAME URL shows different captchas from different environments. Documented case: cej.pj.gob.pe shows **hCaptcha** from Linux + rebrowser-playwright, but **text captcha** (imagen PNG, 4 caracteres) from Windows + Chrome real profile. Never assume the captcha type — ask the user what they see, or test from their environment first.
4. **403 with Transaction ID = hard block** — When Radware returns HTTP 403 with `Incident ID: xxxx-xxxx`, the request never reached the origin server. Retrying from the same IP/fingerprint is futile. Must change IP (VPN/proxy) or fingerprint (real Chrome profile via remote debugging).
5. **Wapiti/w3af/etc won't work on WAF-protected sites** — The scanner hits the WAF, not the real server. Use browser-based manual testing instead.
6. **Never use `wait_until="networkidle"`** on sites with polling — JSF/Angular sites have constant AJAX polling. Use `domcontentloaded` + fixed sleep instead.
7. **Cache the Chrome profile** — Once you pass Radware with a profile, reuse it. Radware's `__uzm*` cookies are session tokens.
8. **2Captcha ImageToTextTask may have low accuracy** — For the CEJ text captcha, the fail rate was ~65%. Consider ddddocr (local OCR) as a cheaper alternative.
9. **Stay focused on the primary task** — During investigation, it's easy to get sidetracked by interesting findings (e.g., analyzing a ZIP extract instead of completing the security audit). Always complete the current phase before starting a new one. If the user asks for two things, do them in order: finish Phase A fully, then start Phase B.

## References

- `references/cej-pj-gob-pe.md` — Site profile, routes, and access flow for CEJ (Poder Judicial Perú)
- `references/cej-scraper-poder-judicial.md` — Ubuntu port details, Chrome version pinning, PDF download headers, captcha fallback, Excel header detection
