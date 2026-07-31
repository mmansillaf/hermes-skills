# Grupo El Comercio (GEC) — Login SSO Architecture

## Overview

Grupo El Comercio uses a **centralized SSO** at `id.gec.pe` that authenticates
users across all their properties:

- `gestion.pe`
- `elcomercio.pe`
- `depor.com`
- `trome.com`
- `peruquiosco.pe`
- `clubelcomercio.pe`

## Login Form Analysis (June 2026)

### Endpoint

```
POST https://id.gec.pe/elcomercio/login?redirect_uri=https%3A%2F%2Felcomercio.pe%2F&ref=button_header
```

### Form Fields

| Field | Name | Type | Notes |
|-------|------|------|-------|
| Email | `username` | `email` | Standard email input |
| Password | `password` | `password` | Hidden, no visible length limit |
| Submit | `Continuar` | `button` | Triggers POST |

### Authentication Methods

1. **Email + Password** (POST form)
   - Protected by **reCAPTCHA** (iframe detected on page)
   - Likely CSRF token in session (not visible in DOM — server-side validation)

2. **Google OAuth** (`Iniciar con Google`)
   - Standard OAuth 2.0 flow with Google
   - No visible CAPTCHA on the Google redirect path
   - This is the path of least resistance if the user has or can create a Google account

### No Client-Side Bypass Possible

Unlike the paywall (which is client-side Piano/Tinypass), the login is
**server-side hard authentication**:

- No overlay to delete (the page IS the login screen, content is on another domain)
- No `articleBody` in HTML (not a NewsArticle page)
- No exposed auth tokens in localStorage/sessionStorage (empty on login page)
- Only cookies are Google Analytics (`_ga`, `_ga_WKWY3DEGYS`)

### Chrome Fingerprint on Login Page

| Property | Value |
|----------|-------|
| `navigator.webdriver` | `undefined` (legitimate browser) |
| `navigator.plugins.length` | 5+ (real Chrome) |
| `localStorage` | Empty |
| `sessionStorage` | Only `tsr-scroll-restoration` |
| Cookies | Only `_ga`, `_ga_WKWY3DEGYS` |

## Bypass Approaches (None are trivial)

### 1. Google OAuth (Most Practical)
If the user has a Google account (or can create one with a temp email + phone),
clicking "Iniciar con Google" bypasses the GEC registration entirely.

**Steps**:
1. Create a Google account (requires phone verification)
2. Click "Iniciar con Google" on id.gec.pe
3. Google authenticates → redirects to GEC → session established
4. Export session cookies for reuse

### 2. Temp Email Registration
If GEC allows free registration with just email (no payment):

**Theoretical pipeline**:
```python
# 1. mail.tm creates inbox
# 2. Playwright navigates to id.gec.pe
# 3. Fill registration form
# 4. Wait for verification email via mail.tm API
# 5. Click verification link
# 6. Save storage_state (cookies)
# 7. Reuse for authenticated requests
```

**Challenges**:
- reCAPTCHA (needs 2captcha service ~$0.50/1000 solves)
- Rate limiting on registrations
- GEC may block known temp mail domains

### 3. Session Cookie Reuse (Once Authenticated)
After successful login via any method, the session can be persisted:

**Playwright**:
```javascript
// Save after login
await context.storageState({ path: 'gec-auth.json' });

// Reload in future sessions
const context = await browser.newContext({ storageState: 'gec-auth.json' });
```

**curl**:
```bash
# Login
curl -X POST 'https://id.gec.pe/elcomercio/login' \
  -c cookies.txt \
  -d 'username=EMAIL&password=PASS'

# Reuse
curl -b cookies.txt 'https://elcomercio.pe/economia/articulo/'
```

## Paywall vs Login: Two Separate Systems

GEC uses **two independent layers**:

| Layer | Technology | Location | Bypass Method |
|-------|-----------|----------|---------------|
| **Login/SSO** | id.gec.pe (server-side) | Authentication | Google OAuth or registration |
| **Paywall** | Piano/Tinypass (client-side) | Article pages | Googlebot UA spoofing |

You can be **logged in without subscribing** (free account) — the paywall still
blocks premium articles. You can be **not logged in** and still extract article
content via Googlebot UA (the paywall is client-side, content is in JSON-LD).

## References

- `bypass-paywall` SKILL.md — section 9 (GEC case study)
- `D:\PyCode\skill-bypass-paywall\login1.txt` through `login8.txt` — Login wall research
- `D:\PyCode\skill-bypass-paywall\paywall1.txt` through `paywall5.txt` — Paywall research
