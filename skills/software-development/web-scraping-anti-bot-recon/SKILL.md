---
name: web-scraping-anti-bot-recon
description: Systematic reconnaissance of a website's anti-bot defenses — identify protection layers (Radware, Cloudflare, hCaptcha, reCAPTCHA), map captcha types to solving services, research existing GitHub tools, and produce a plan before any exploitation.
---

# Web Scraping Anti-Bot Reconnaissance

Systematic approach to evaluating a website's anti-bot defenses before writing any code. The goal is a clear, actionable plan — not a working scraper.

## When to Use
- A target website blocks automated access (CAPTCHA, bot manager, WAF)
- You need to understand what you're up against before building
- User asks "can you scrape/download from X?" and you hit a wall
- User has a captcha-solving API key (2Captcha, CapSolver, NopeCHA) and needs integration guidance

## Step 1.1 — Test Alternative Entry Points

Bot managers often protect primary entry points but leave secondary routes open. Before assuming you must solve a captcha, try:

```python
# Instead of the protected URL, try:
# 1. The homepage first (often unprotected)
page.goto("https://target.com/")
# 2. A secondary form page (may bypass Radware entirely)
page.goto("https://target.com/cej/forms/busquedaform.html")
# 3. Direct GET to form handlers (may return 405 — expected with JSF)
page.goto("https://target.com/cej/forms/busquedacodform.html")
```

**Documented case**: cej.pj.gob.pe — Radware blocks `busquedacodform.html` direct but NOT `busquedaform.html`. From there you can navigate to the codigo tab without ever seeing a captcha.

## Step 1.2 — Test Stealth Browser Tools

If vanilla Playwright triggers bot detection, try these drop-in replacements (in order of effectiveness):

| Tool | Install | Bypass level | Notes |
|---|---|---|---|
| **rebrowser-playwright** | `pip install rebrowser-playwright` | Strong | Drop-in for playwright. Patches `Runtime.enable` CDP detection + 7 other vectors. Works headless. |
| **undetected-chromedriver** | `pip install undetected-chromedriver` | Moderate | Selenium-based. Patches webdriver flags. |
| **nodriver** | `pip install nodriver` | Strongest | Drives Chrome directly via WebSocket CDP. No Playwright layer. Best against Radware per 2026 benchmarks. |

rebrowser-playwright usage:
```python
from rebrowser_playwright.sync_api import sync_playwright
import time

pw = sync_playwright().start()
browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
context = browser.new_context(
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    viewport={"width": 1920, "height": 1080},
    locale="es-PE", timezone_id="America/Lima",
)
context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
""")
page = context.new_page()
page.goto("https://target.com", timeout=60000, wait_until="domcontentloaded")
# If Radware still triggers, try busquedaform.html as alternative entry
```

## Step 2 — Classify the Captcha Type

From the browser snapshot, identify:

| Type | Detection signal | Solving via service |
|---|---|---|
| **hCaptcha** | iframe `hcaptcha.com`, checkbox "Soy humano" | 2Captcha `hcaptcha()`, NopeCHA `/v1/token/hcaptcha` |
| **reCAPTCHA v2** | iframe `recaptcha` + `/anchor`, `g-recaptcha` class | 2Captcha `recaptcha()`, NopeCHA `/v1/token/recaptcha2` |
| **reCAPTCHA v3** | Score-based, invisible, `render=` in script src | 2Captcha `recaptcha_v3()` |
| **Cloudflare Turnstile** | `challenges.cloudflare.com` iframe, `cf-turnstile` class | 2Captcha `turnstile()`, NopeCHA experimental |
| **Text CAPTCHA** | `<img>` with distorted text | 2Captcha `normal()`, pytesseract OCR |
| **Image CAPTCHA (grid)** | "Select all traffic lights" | 2Captcha `recaptcha()` with grid method |

## Step 3 — Research GitHub for Existing Tools

Search patterns (try all):
```
github "site.target.com" scraper|bot|downloader python
github "target-site-name" judicial OR expediente OR scraper OR spider
github 2captcha hcaptcha selenium python bypass
github service-name (e.g. radware) bypass captcha python
```

Examine each repo for:
- Whether it actually works on the current version of the site (check last commit date)
- What approach it uses (Selenium, Playwright, Scrapy, direct API)
- How it handles auth/cookies/captcha
- Whether it's for the same site or just similar tech

**Pitfall**: Many repos labeled for a site are outdated — the protection layer may have been added later.

## Step 4 — Map Technology Stack (Vulnerability Vectors)

Identify the underlying web framework. Hidden form fields and URL patterns reveal it:

- **JSF (Java Server Faces)**: `javax.faces.ViewState`, `j_idt*` element IDs, `formBusqueda` naming. Vector: ViewState deserialization if encryption is weak/disabled (CVE-known).
- **ASP.NET**: `__VIEWSTATE`, `__EVENTVALIDATION`. Vector: ViewState MAC bypass.
- **PrimeFaces**: Component library on top of JSF. `p:*` widgets.
- **Spring Boot/REST**: JSON endpoints, `/api/`, `/rest/`. Vector: unprotected API endpoints.
- **Angular (compiled)**: `/js/main.*.js`, runtime/polyfills bundles, no ViewState hidden fields. Single-page app pattern.

### JSF → Angular Migration Detection

Some sites migrate from JSF to Angular over time. Signs of migration:
- **Before (JSF)**: `javax.faces.ViewState` hidden fields, `j_idt*` element IDs, Ajax postbacks with `javax.faces.source` params, form actions pointing to `.xhtml` or `.faces`
- **After (Angular)**: Compiled JS bundles (`main.*.js`, `runtime.*.js`, `polyfills.*.js`), JSON API calls, no ViewState fields, meta CSRF tokens, cleaner URL patterns

**When a site has migrated**, old scraping tools that relied on JSF ViewState manipulation will break. The new API layer may expose REST endpoints that are easier to work with — but also potentially less protected by the WAF.

**Probe for direct API endpoints** (may bypass the bot manager entirely):
```bash
curl -s -I "https://target.com/cej/rest/search" 2>&1
curl -s -I "https://target.com/cej/api/expediente" 2>&1
curl -s "https://target.com/cej/forms/detalleform.html?codigo=..." 2>&1
```

Also probe with POST (JSF forms reject GET):
```bash
curl -s -o /dev/null -w "%{http_code}" -X POST "https://target.com/cej/forms/busquedacodform.html" -d "cod_expediente=00001&cod_anio=2020"
```

### Radware-Specific Detection Patterns

Radware (perfdrive.com) has distinct behavioral signatures:

| Signal | Pattern |
|---|---|
| **URL redirect** | `validate.perfdrive.com/?ssa=...&ssc=https%3A%2F%2Ftarget...` |
| **Cookies** | `__uzma`, `__uzmb`, `__uzmc`, `__uzmd`, `__uzme`, `__uzmf` — tracking cookies |
| **Server header** | `server: rdwr` |
| **JS tracker** | `stormcaster.js` at a UUID path, e.g. `/18f5227b-e27b-445a-a53f-f845fbe69b40/stormcaster.js` |
| **Blocked page** | "We apologize for the inconvenience... but your activity and behavior on this site made us think that you are a bot" |
| **Incident ID** | Blocked page includes a unique `Incident ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` which the site owner can look up in Radware logs |
| **hCaptcha** | iframe `newassets.hcaptcha.com/captcha/v1/...` with sitekey |
| **Intermittent blocking** | Radware does NOT block consistently — same fingerprint may pass 3 times then fail on the 4th. This is by design (behavioral analysis). Pattern: first access often passes, subsequent rapid accesses trigger block. |

**Key insight**: Radware deploy differs by environment. Windows + Chrome real profile + persistent user data directory often bypasses Radware entirely, showing only the application-level captcha (text PNG). Linux + headless playwright always triggers hCaptcha. This means the same site has TWO different captcha workflows depending on the client's trust level.

## Step 4.5 — Run wapiti Vulnerability Scan

After initial recon, run a black-box vulnerability scan with wapiti3 (install: `pip install wapiti3`):

```bash
wapiti --url "https://target.com/" --scope domain --module "sql,xss,crlf,csrf,backup,htaccess,exec" -o /home/usuario/wapiti_report -f html
```

Review the report for:
- **Backup files** (.bak, .old, .swp, .tgz) — often false positives if the bot manager returns 403 for all paths
- **CSRF** — missing anti-forgery tokens on forms
- **Missing security headers** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Information disclosure** — full paths, server versions, framework versions
- **SQLi / XSS** — rarely found behind aggressive bot managers (they block the scanner payloads)

**Pitfall**: Radware/Cloudflare will block wapiti's crawler on most paths. Results are limited to what the scanner can reach.

### Interpreting wapiti Results Through a WAF

When scanning behind Radware/Cloudflare, most findings will be false positives or WAF responses, not actual application vulnerabilities:

| Finding | Likely real? | Why |
|---|---|---|
| Backup files (.bak, .old, .tgz) | ❌ Usually false | WAF returns 403 for all paths — wapiti interprets 403 as "file exists" |
| CSRF missing | ⚠️ Possibly real | Check if the meta CSRF token is actually populated (not empty) |
| Security headers absent | ✅ Real | WAF doesn't add security headers — the server behind it is exposed |
| SQLi / XSS / Command Exec | ❌ False negative | Scanner payloads never reached the real server (WAF blocked them) |
| Server header (e.g. `server: rdwr`) | ✅ Real | Radware reveals itself via server header |

**Always verify wapiti findings manually** with a browser that bypasses the WAF (Chrome real profile, proxy, etc.). The scanner report is a starting point, not authoritative.

## Step 4.6 — Security Headers Audit

After establishing baseline access (via stealth browser or proxy), run a comprehensive security headers check:

### Headers to Check

| Header | What it prevents | If missing |
|---|---|---|
| `Strict-Transport-Security` (HSTS) | Downgrade attacks (HTTP → MITM) | Site can be served over HTTP |
| `Content-Security-Policy` (CSP) | XSS, data exfiltration, clickjacking | Any XSS found = game over |
| `X-Frame-Options` | Clickjacking (site embedded in iframe) | Site can be wrapped in malicious frames |
| `X-Content-Type-Options: nosniff` | MIME-type sniffing | Malicious uploads may execute as scripts |
| `Referrer-Policy` | URL leakage via Referer header | Sensitive URLs may leak to 3rd parties |
| `Permissions-Policy` | Browser API access (camera, mic, etc.) | No restriction on browser features |

### How to Check (from browser context)
```python
# Via Playwright page evaluate
headers = page.evaluate("""
    async () => {
        const r = await fetch(window.location.href);
        const h = {};
        r.headers.forEach((v, k) => { h[k] = v; });
        return h;
    }
""")
# Then inspect: 'strict-transport-security', 'content-security-policy',
# 'x-frame-options', 'x-content-type-options', 'referrer-policy' keys
```

### Cookie Security Check

```python
cookies = context.cookies()
for c in cookies:
    flags = []
    if c['httpOnly']: flags.append('HttpOnly')
    if c['secure']: flags.append('Secure')
    if c.get('sameSite'): flags.append(f'SameSite={c["sameSite"]}')
    # Cookies without HttpOnly are accessible via JS → XSS can steal them
    # Cookies without Secure are sent over HTTP → MITM can intercept them
```

### Technique 4: VPN as Proxy (Alternative when residential proxies aren't available)

When you don't have access to residential rotating proxies, a VPN (Proton VPN, Mullvad, etc.) can serve as a substitute for low-volume bypass testing (~50-100 requests):

```bash
# Install OpenVPN configs from your Proton VPN account
# Download configs from account.protonvpn.com → Downloads → OpenVPN config files
# Connect to a free server (NL, US, JP for free tier)
sudo openvpn --config nl-free-XX.ovpn --auth-user-pass auth.txt
# Verify IP change
curl -s https://api.ipify.org
```

**Limitations:**
- Single static IP — will be blocked after enough requests (no rotation)
- VPN IP ranges are known to some bot managers (but Radware specifically blocks based on browser fingerprint, not just IP)
- For scraping 10K+ records, residential rotating proxies (DataImpulse $1/GB) are still required
- For audit/testing (~50 requests), VPN IP alone + rebrowser-playwright is often sufficient to bypass Radware

**Effectiveness against Radware**: Proton VPN (Netherlands) + rebrowser-playwright bypassed Radware on cej.pj.gob.pe in testing. The clean IP reduced captcha triggers compared to the same fingerprint without VPN.

When the user already has a working browser setup on another machine (e.g., Windows with Chrome real profile), you can bypass Radware entirely by connecting remotely:

### On the User's Machine (Windows)
```batch
:: Launch Chrome with remote debugging and a persistent profile
chrome.exe --remote-debugging-port=9225 --user-data-dir="C:\chrome_profiles\pj"
:: Navigate manually to the target site once (builds trusted profile)
```

### Connecting from Script
```python
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9225")
driver = webdriver.Chrome(options=options)
# Chrome is already past Radware — you see only the application-level captcha
```

**Important**: This pattern means the user on Windows sees a different captcha than you see from Linux. The persistent Chrome profile has established trust with Radware, so only the application's internal captcha (text PNG, 4 chars) appears. Any tooling you write must handle BOTH captcha types.

**Critical pitfall — no execution context on already-loaded Radware pages**: If you connect Selenium to a Chrome that **already** has a Radware-protected page loaded, all JavaScript execution fails with `timeout from no such execution context: frame does not have execution context`. This affects `execute_script()`, `current_url`, `window_handles`, and `window.open()`. `save_screenshot()` still works.

**Correct order of operations:**
1. Launch Chrome with `--remote-debugging-port=9225`
2. Connect Selenium via `debuggerAddress`
3. *Then* navigate to the protected page
4. If reconnecting to an existing Chrome where the user already navigated: ask the user to describe what they see on screen (take screenshot), refresh manually (F5), or start fresh from `busquedaform.html`

If you already see the page with download buttons and Selenium fails, the Radware sandbox frame is already in place. A screenshot and manual instruction to the user is the only viable path.

## Step 4.8 — Captcha Solving Service Integration

### Text CAPTCHA (Image PNG) via 2Captcha API v2

For sites that present a simple text/image captcha (not hCaptcha/reCAPTCHA):

```python
import base64, requests

# Capture captcha image from page
captcha_b64 = driver.execute_script("""
    var img = document.getElementById('captcha_image');
    var c = document.createElement('canvas');
    c.width = img.width;
    c.height = img.height;
    c.getContext('2d').drawImage(img, 0, 0, img.width, img.height);
    return c.toDataURL('image/jpeg', 0.85).split(',')[1];
""")

# Send to 2Captcha API v2 (createTask / getTaskResult)
payload = {
    "clientKey": API_KEY,
    "task": {
        "type": "ImageToTextTask",
        "body": captcha_b64,
        "numeric": 0,
        "minLength": 4,
        "maxLength": 4,
        "comment": "captcha 4 caracteres alfanumericos"
    }
}
resp = requests.post('https://api.2captcha.com/createTask', json=payload)
task_id = resp.json()['taskId']

# Poll for result
for _ in range(30):
    time.sleep(5)
    poll = requests.post('https://api.2captcha.com/getTaskResult',
        json={"clientKey": API_KEY, "taskId": task_id}).json()
    if poll['status'] == 'ready':
        captcha_code = poll['solution']['text']
        break
```

**Captcha fail rate matters**: Test with 20+ samples. If fail rate > 30%, try:
1. Alternative service (Anti-Captcha, CapSolver, ddddocr local OCR)
2. Different image quality (JPEG 0.85 vs 1.0, display-size vs natural-size)
3. Increase retries from 2 to 4+

### ddddocr + 2Captcha Combo (Text CAPTCHAs)

Combine local OCR with cloud fallback to cut costs ~50%. Probado en cej.pj.gob.pe:

```python
import ddddocr, base64, requests, time
ocr_local = ddddocr.DdddOcr()

def resolver_captcha(imagen_bytes, api_key, min_len=4, max_len=4):
    resultado = ocr_local.classification(imagen_bytes)
    if resultado:
        resultado = resultado.strip().upper()
        if min_len <= len(resultado) <= max_len and resultado.isalnum():
            return resultado, 'ocr'
    b64 = base64.b64encode(imagen_bytes).decode()
    task = {"clientKey": api_key, "task": {
        "type": "ImageToTextTask", "body": b64,
        "numeric": 0, "minLength": min_len, "maxLength": max_len}}
    r = requests.post("https://api.2captcha.com/createTask", json=task, timeout=30).json()
    if r.get("errorId") == 0:
        tid = r["taskId"]
        for _ in range(30):
            time.sleep(3)
            poll = requests.post("https://api.2captcha.com/getTaskResult",
                json={"clientKey": api_key, "taskId": tid}, timeout=15).json()
            if poll.get("status") == "ready":
                return poll["solution"]["text"], '2captcha'
    return None, None
```

**Real-world: cej.pj.gob.pe text captcha:** ddddocr ~40-60% solo, combo ~60-80%, costo ~50% menos.
**Cuando falla:** refrescar imagen del captcha, esperar 5-10s entre reintentos.

### hCaptcha via 2Captcha

```python
from twocaptcha import TwoCaptcha
solver = TwoCaptcha(API_KEY)
result = solver.hcaptcha(sitekey=SITEKEY, url=page.url)
token = result.get('code')

# Inject token into page
page.evaluate("""(token) => {
    const ta = document.querySelector('textarea[name="h-captcha-response"]');
    if (ta) { ta.value = token; }
    if (typeof hcaptcha !== 'undefined') { hcaptcha.setResponse(token); }
}""", token)
```

## Step 5 — Produce the Plan

Present to the user in this structure:

1. **Protection layers identified** (Radware → hCaptcha → JSF)
2. **Existing tools found** (name, approach, whether usable, what's outdated)
3. **Bypass approach**:
   - Radware/Cloudflare: rebrowser-playwright + residential proxies + stealth (try alternative entry points first)
   - Captcha: 2Captcha/NopeCHA API (token injection pattern)
   - Auth/cookies: session persistence
4. **Risk assessment** (rate limits, IP bans, legal)
5. **Proxy/VPN recommendation** for production volume (see reference file for provider comparison)
6. **Recommended next steps** (ordered, testable)

## Residential Proxy Providers for Production Scraping

When the user needs to scale past what stealth browser alone can handle, recommend:

| Provider | Price/GB | Tier | Best for |
|---|---|---|---|
| Decodo (ex Smartproxy) | $2.75-3.75 | Mid | Best value, 195+ countries, city/ASN targeting. Code: DECODO5 |
| DataImpulse | $1.00 | Budget | High volume, non-expiring traffic. Premium tier available |
| Evomi | $0.49 | Budget | Cheapest base rate. Add-ons for ISP/ASN/uptime. Code available |
| Bright Data | $4.00 | Premium | Largest pool, most features. Code: PROXYWAY60 |
| Oxylabs | $4.50-6.00 | Premium | Best infrastructure stability. Code: OXYLABS50 |
| Byteful | $2.75-3.25 | Mid | Fastest response time (0.41s). Code: PROXYWAY10 |

**Key**: For sites behind Radware, residential IPs from the target's country reduce captcha triggers significantly. Static datacenter IPs will almost always be blocked.

### VPN as Substitute for Low-Volume Testing

When residential proxies aren't available, a VPN with clean IP can bypass Radware for low-volume audit work (~50-100 requests):

```bash
# 1. Get config from your Proton VPN account (account.protonvpn.com → Downloads)
# 2. WireGuard is preferred (faster, simpler than OpenVPN)
sudo apt install wireguard

# 3. Save the config (e.g., /home/user/proton-configs/mx.conf)
sudo wg-quick up /home/user/proton-configs/mx.conf

# 4. Verify
curl -s https://api.ipify.org

# 5. When done
sudo wg-quick down /home/user/proton-configs/mx.conf
```

**Results on cej.pj.gob.pe:**
- Proton VPN Netherlands (OpenVPN, datacenter IP) → Radware blocked ❌
- Proton VPN Mexico (WireGuard, Datacamp IP) → Radware passed ✅
- The VPN alone was sufficient for bypass without residential proxy

**Limitations:** Single static IP, no rotation. Gets blocked after enough requests. Not suitable for production scraping at scale.

## API Token Injection Pattern (2Captcha + hCaptcha)

Once you have the sitekey and a solved token from 2Captcha:

```python
# Extract sitekey from page
sitekey = page.evaluate('''() => {
    const el = document.querySelector('[data-sitekey]');
    return el ? el.getAttribute('data-sitekey') : null;
}''')

# Solve via 2Captcha
solved = solver.hcaptcha(sitekey=sitekey, url=page.url)

# Inject token
page.evaluate('''(token) => {
    document.querySelector('textarea[name="h-captcha-response"]').value = token;
    if (typeof hcaptcha !== 'undefined') hcaptcha.execute();
}''', solved['code'])
```

## Pitfalls
- **Radware blocks before hCaptcha loads**: Solving the captcha is not enough — you must first bypass Radware's fingerprinting with realistic browser profiles and proxies.
- **Repos are often outdated**: The site likely added protections after the scraper was published. Always verify against the live site.
- **Rate limiting**: Some sites limit to 5 downloads per session or have aggressive IP-based throttling.
- **JSF ViewStates expire**: Each form submission needs a fresh ViewState; you cannot reuse them.
- **Always present the plan first** before writing any code. Users familiar with the target may have constraints or API keys that change the approach.
- **Do NOT mix recon with code audit in one pass.** Phase order: (1) anti-bot recon and bypassing the WAF, (2) security audit of the LIVE site (headers, endpoints, vulns), (3) code review of any existing project files. If you switch from live site auditing to reading project code mid-way, you will miss critical security checks on the live site. The user will correct you — finish each phase completely before moving to the next.
- **Wapiti results behind a WAF are mostly false positives.** Backup files, missing .htaccess, etc. — Radware returns 403 for everything. Only security headers and CSRF detection are reliable through a WAF.
- **Chrome remote debugging bypass may give a false sense of security.** The captcha you see from a trusted Chrome profile (text PNG) is NOT the same captcha a headless browser sees (hCaptcha). Any automation you write must handle BOTH scenarios.
- **Dual-captcha environments exist:** A site can have TWO captchas — one at the WAF layer (Radware hCaptcha) and one at the application layer (text PNG). Users with persistent Chrome profiles on Windows bypass the WAF layer and only see the app captcha. From a clean browser, you'll face BOTH. Design your automation accordingly.
- **Forms may have hidden required fields uncovered only through testing.** The CEJ search form has 7 visible fields but also requires a `parte` (name) field that is NOT obvious from the HTML alone. Always submit test data with empty optional-looking fields; if it fails, check JS-driven validation or hidden input requirements.
- **Multi-instance Chrome parallelism has diminishing returns against Radware.** Two Chrome instances (different ports) worked initially but Radware correlated them after ~100 requests. Plan for 1 instance as the stable configuration and treat multi-instance as experimental.
- **Document download endpoints may have zero rate limiting.** Always check: if `documentoD.html` style endpoints don't require auth cookies and return quickly, they can be parallelized aggressively (5-10 workers). Test incrementally — 1 → 5 → 10 workers — and watch for HTTP 429 or latency increases.
