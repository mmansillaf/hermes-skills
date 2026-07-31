---
name: bypass-login-wall
description: Técnicas, herramientas y workflows para acceder a contenido detrás de muros de login/registro (registration walls, login walls, autenticación requerida). Cubre temp mail automation, session cookie reuse, OAuth, CAPTCHA solving, y automatización con Playwright. Incluye casos específicos como GEC (Grupo El Comercio), LinkedIn, Medium, Quora.
category: scraping
---

# Login / Registration Wall Bypass — Guía Completa

## Diferencia Fundamental con Paywalls

| Paywall | Login/Registration Wall |
|---------|------------------------|
| El contenido **está en el HTML** (client-side), solo oculto por CSS/JS | El contenido **no está en la respuesta del servidor** hasta autenticar |
| Basta engañar al cliente (UA spoofing, eliminar overlay) | Requiere **credenciales válidas** o automatizar el registro |
| JSON-LD suele tener el texto completo accesible | Sin sesión, el servidor no envía el contenido |
| ✅ Alta tasa de éxito con técnicas simples | ⚠️ Variable — depende de la arquitectura de auth |

---

## 1. Tipología de Barreras de Autenticación

| Tipo | Descripción | Ejemplos | Bypassabilidad |
|------|-------------|----------|----------------|
| **Login Wall (overlay)** | Capa CSS/JS que oscurece contenido ya cargado en DOM | Pinterest, Quora (versiones antiguas) | ✅ Alta — eliminar overlay con DevTools |
| **Registration Wall** | Exige crear cuenta gratuita (email) para acceder | Foros, whitepapers, Medium | ✅ Media-Alta — temp mail + automation |
| **Hard Authentication** | Todo el contenido está detrás de auth server-side | Bancos, intranets, GEC SSO | ❌ Baja — requiere credenciales reales |
| **MFA / 2FA** | Segundo factor tras login | Google, Microsoft 365, bancos | ⚠️ Variable — phishing kits, session reuse |
| **SSO Federado** | Login via Google/Facebook/GitHub | id.gec.pe, muchos sitios modernos | ✅ Media — crear identidad OAuth dummy |

---

## 2. Técnicas Básicas (Sin Instalación)

### 2.1 Eliminar Overlay con DevTools
Para login walls que son solo capas visuales:

```
1. F12 → Ctrl+Shift+C → click en el overlay
2. Delete element o display: none
3. Si el body tiene overflow: hidden, cámbialo a visible
```

### 2.2 Modo Lectura / Reader Mode
Chrome: Menú → Más herramientas → Modo lectura
Edge: F9 (Lector inmersivo)

### 2.3 Desactivar JavaScript
Chrome: Configuración → Privacidad → Configuración de sitios → JavaScript → Bloquear
⚠️ Solo funciona si el contenido ya está en el DOM y JS solo muestra el overlay.

### 2.4 Modo Incógnito
Para sitios con contador de vistas limitadas antes de pedir login.

---

## 3. Técnicas de Nivel Medio (Cookies, Headers, Parámetros)

### 3.1 Modificación de Cookies de Sesión
Para sistemas mal diseñados que confían en cookies client-side:

```javascript
// En DevTools → Application → Cookies
// Buscar cookies como: logged_in, isAuthenticated, admin
// Cambiar valores a true / 1
```

### 3.2 Manipulación de Parámetros URL
```bash
# Probar variantes de URL
?logged_in=false  → ?logged_in=true
?require_auth=1   → ?require_auth=0
?redirect=login   → eliminar parámetro
```

### 3.3 Spoofing de User-Agent Googlebot
Similar a paywalls, algunos sitios permiten acceso a crawlers:
```bash
curl -A 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' 'URL'
```

### 3.4 Content Format Variants
```bash
?output=json       # JSON representation
?format=json       # Alternative
?print=true        # Print-friendly (no gated)
?amp               # AMP version
m.URL              # Mobile version (different access controls)
```

---

## 4. Temporary Email — El Fundamento del Registration Bypass

### 4.1 Mail.tm API (Mejor para Automatización)
```python
import requests, time

BASE = "https://api.mail.tm"
with requests.Session() as s:
    # Get domains
    r = s.get(f"{BASE}/domains")
    domain = r.json()["hydra:member"][0]["domain"]

    # Create account
    email = f"user{int(time.time())}@{domain}"
    password = "TempPass123!"
    s.post(f"{BASE}/accounts", json={"address": email, "password": password})

    # Get token
    r = s.post(f"{BASE}/token", json={"address": email, "password": password})
    token = r.json()["token"]
    s.headers.update({"Authorization": f"Bearer {token}"})

    # Poll for messages
    for _ in range(30):
        r = s.get(f"{BASE}/messages")
        if r.json()["hydra:member"]:
            print("Email received!")
            break
        time.sleep(1)
```

### 4.2 Servicios de Email Temporal

| Servicio | API | Dominios | Detectabilidad |
|----------|-----|----------|----------------|
| **Mail.tm** | ✅ REST API | 50+ | Baja (mejor opción) |
| **Guerrilla Mail** | ✅ API | 10+ | Media |
| **Temp-Mail.org** | ✅ Limitada | 30+ | Media-Alta |
| **Mailinator** | ✅ API | 5+ | Alta (muy bloqueado) |
| **10 Minute Mail** | ❌ | 3+ | Alta |
| **Custom domain** (catch-all) | N/A | Ilimitado | Muy Baja (mejor stealth) |

### 4.3 Custom Domain Catch-All (Método Stealth)
```
1. Compra dominio barato (ej: miresearch.xyz)
2. Configura catch-all forwarding a tu email real
3. Usa sitio@miresearch.xyz para cada registro
4. Casi indetectable como temp mail
```

### 4.4 Gmail Plus Trick
```
tunombre+sitio@gmail.com → llega a tunombre@gmail.com
# Útil para filtrar, pero muchos sitios ya lo bloquean
```

---

## 5. Automatización de Registro (Playwright + Temp Mail)

### 5.1 Arquitectura Completa
```
mail.tm API → Playwright stealth → 2captcha (si hay CAPTCHA) → Credential Store
     ↓                                    ↓
Email verification                 Residential proxy
```

### 5.2 Playwright Anti-Fingerprinting
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir="/tmp/playwright_profile",
        headless=False,
        viewport={"width": 1920, "height": 1080},
        locale="es-PE",
        timezone_id="America/Lima",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."
    )
    page = context.new_page()

    # Ir al registro
    page.goto("https://sitio.com/register")
    page.fill("input[name='email']", temp_email)
    page.fill("input[name='password']", "Pass123!")
    page.click("button[type='submit']")

    # Guardar sesión para reuso
    context.storage_state(path="auth.json")
```

### 5.3 Reutilizar Sesión Guardada
```python
with sync_playwright() as p:
    context = p.chromium.new_context(storage_state="auth.json")
    page = context.new_page()
    page.goto("https://sitio.com/contenido-protegido")
    # La sesión se restaura automáticamente
```

### 5.4 CAPTCHA Solving
```python
# 2captcha API
import requests

api_key = "TU_API_KEY"
site_key = "6Lc..."  # Se obtiene del HTML del sitio

r = requests.post("https://2captcha.com/in.php", data={
    "key": api_key,
    "method": "userrecaptcha",
    "googlekey": site_key,
    "pageurl": "https://sitio.com/login"
})
captcha_id = r.text.split("|")[1]

# Esperar resolución
import time
for _ in range(60):
    r = requests.get(f"https://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}")
    if r.text == "CAPCHA_NOT_READY":
        time.sleep(5)
    else:
        token = r.text.split("|")[1]
        break
```

---

## 6. Google OAuth como Vía de Entrada

Muchos sitios ofrecen "Iniciar con Google/Facebook/GitHub" — crear una identidad OAuth dummy permite acceder sin cuenta específica del sitio.

**Estrategia:**
1. Crear cuenta Google con temp email + Google Voice number
2. Usar esa cuenta para "Login with Google" en el target
3. El sitio recibe la identidad verificada de Google
4. No necesita cuenta específica del target

**OAuth token reuse:**
- Los tokens OAuth suelen tener validez de 1-24h
- Se pueden extraer de localStorage del navegador
- Reutilizar en diferentes sesiones

---

## 7. Session Cookie Reuse

### 7.1 Exportar Cookies desde el Navegador
- **EditThisCookie** (Chrome) → exportar cookies en formato JSON/Netscape
- **Cookie-Editor** (Chrome/Firefox) → editar/exportar visualmente

### 7.2 Reutilizar con cURL
```bash
# Guardar cookies después del login
curl -X POST 'https://sitio.com/login' \
  -d 'username=user&password=pass' \
  -c cookies.txt

# Reutilizar para acceder a contenido protegido
curl -b cookies.txt 'https://sitio.com/contenido-protegido'
```

### 7.3 Reutilizar con Python
```python
from http.cookiejar import LWPCookieJar
import requests

session = requests.Session()
session.cookies = LWPCookieJar("cookies.txt")
try:
    session.cookies.load(ignore_discard=True)
except:
    # Login flow
    pass

response = session.get("https://sitio.com/protected")
```

### 7.4 Cookie Lifetime
- Session cookies → horas a días
- Persistent cookies → semanas a meses
- "Remember me" → 30+ días
- OAuth refresh tokens → 30-90 días
- **Tip:** Configurar cron jobs para refrescar cookies periódicamente

---

## 8. Alternative Frontends (Sin Login)

| Herramienta | Sitio Original | Estado |
|-------------|---------------|--------|
| **Nitter.net** | X/Twitter | ✅ Activo (múltiples instancias) |
| **Teddit.net** | Reddit | ✅ Activo |
| **Invidious** | YouTube | ✅ Activo |
| **Scribe.rip** | Medium | ✅ Activo |
| **Proxitok** | TikTok | ✅ Activo |
| **Bibliogram** | Instagram | ⚠️ Parcialmente roto |

---

## 9. API Reverse Engineering

Muchos sitios SPA cargan datos vía APIs internas que no están bien protegidas.

### 9.1 Técnica
1. Abrir DevTools → Network tab
2. Iniciar sesión
3. Identificar endpoints que devuelven el contenido real
4. Replicar esas llamadas directamente (bypasseando el frontend)

### 9.2 Qué buscar
- **GraphQL endpoints** (`/graphql`) — probar introspection
- **REST APIs** devolviendo JSON con datos del artículo
- **SSR payloads** (Next.js `__NEXT_DATA__`, Nuxt `__NUXT__`)
- **JSON-LD** en HTML (a veces accesible sin login)
- **RSS/Atom feeds** — a veces sirven contenido completo sin auth

### 9.3 GraphQL Introspection
```bash
curl -s -X POST 'https://target.com/graphql' \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ __schema { types { name } } }"}'
```

---

## 10. Caso Específico: id.gec.pe (Grupo El Comercio SSO)

### Análisis Técnico

| Aspecto | Detalle |
|---------|---------|
| **URL** | `https://id.gec.pe/elcomercio/login?redirect_uri=...` |
| **Propósito** | SSO centralizado: Gestión, El Comercio, PerúQuiosco, Club El Comercio |
| **Método** | POST con `username` + `password` |
| **OAuth** | Google (botón "Iniciar con Google") |
| **Protección** | **reCAPTCHA** (iframe detectado) |
| **Tipo** | **Hard authentication server-side** — no hay overlay que eliminar |
| **Estado cliente** | Sin datos sensibles en localStorage/sessionStorage |

### Técnicas Aplicables

1. **Google OAuth** — camino más directo si tienes cuenta Google
2. **Registro vía temp mail** — Si permite crear cuenta gratuita:
   ```
   mail.tm → Playwright + 2captcha (para reCAPTCHA) → guardar session
   ```
3. **Session cookie reuse** — Una vez logueado, exportar cookies para reuso
4. **No aplica**: Googlebot UA spoofing, DevTools overlay removal, parámetros URL

### Comando curl para login (con credenciales válidas)
```bash
curl -X POST 'https://id.gec.pe/elcomercio/login?redirect_uri=https://elcomercio.pe/' \
  -d 'username=email@ejemplo.com&password=contraseña' \
  -c cookies.txt \
  -L
```

---

## 11. Matriz Sitio × Técnica Recomendada

| Sitio | Mejor Método | Fallback |
|-------|-------------|----------|
| **GEC (Gestión, El Comercio)** `id.gec.pe` | Google OAuth | Temp mail + Playwright + 2captcha |
| **LinkedIn** | Google cache + public profile settings | Temp email + Playwright reg |
| **Medium** | Scribe.rip + JSON-LD extraction | Google cache |
| **Quora** | Google cache + `?share=1` param | Temp email reg |
| **X/Twitter** | Nitter.net + Google cache | archive.ph |
| **Substack** | Google cache + archive.ph | Temp subscription |
| **Glassdoor** | Temp email + Playwright reg | Google cache |

---

## 12. Herramientas y Servicios

### CAPTCHA Solving
| Servicio | Tipo | Costo |
|----------|------|-------|
| **2captcha.com** | Pool humano | ~$0.50/1000 solves |
| **Anti-Captcha** | Pool humano | ~$0.50/1000 solves |
| **CapSolver** | ML + pool | ~$0.40/1000 solves |

### Browser Automation
| Herramienta | Lenguaje | Propósito |
|-------------|----------|-----------|
| **Playwright** | Python/JS | Mejor headless browser moderno |
| **undetected-chromedriver** | Python | Selenium anti-detección |
| **Puppeteer + stealth** | JS | Anti-detección Chrome |

### Shared Credentials
| Servicio | Estado |
|----------|--------|
| **BugMeNot.com** | ✅ Activo (detrás de Cloudflare, declinando) |
| **Login2.me** | ❌ Muerto |
| **Fakeaccount.net** | ❌ Muerto |

---

## 13. Árbol de Decisión

```
¿El contenido está en el HTML visible con DevTools?
├── SÍ → Login wall overlay → Eliminar DOM, desactivar JS, modo lectura
└── NO → ¿Es gratis registrarse?
         ├── SÍ → ¿Tiene CAPTCHA?
         │      ├── SÍ → Temp mail + Playwright + 2captcha
         │      └── NO → Temp mail + Playwright (simple)
         └── NO → ¿Ofrece Google OAuth?
                  ├── SÍ → Crear cuenta Google dummy
                  └── NO → ¿Tienes credenciales?
                           ├── SÍ → Session cookie reuse / curl
                           └── NO → BugMeNot o buscar cache alternativo
```

---

## 14. Consideraciones Legales y Éticas

- **ToS violations** son civiles, no criminales — pero pueden llevar a baneo de IP
- **CFAA (US):** *Van Buren v. United States* (2021) — eludir ToS no es delito federal
  - **Pero:** continuar después de C&D sí viola CFAA
- **GDPR (UE):** Crear identidades falsas puede violar protección de datos
  - Investigación de interés público tiene exenciones
- **Mejores prácticas:**
  - Revisar robots.txt primero
  - Rate limiting — ser buen ciudadano
  - No acceder a datos personales/privados
  - Detenerse si el site operator lo solicita
  - Documentar propósitos de investigación

---

## 15. Referencias

- `D:\PyCode\skill-bypass-paywall\login1.txt` — Técnicas básicas a avanzadas (cookies, JWT, SQLi)
- `D:\PyCode\skill-bypass-paywall\login2.txt` — Gestión legítima de credenciales y SSO
- `D:\PyCode\skill-bypass-paywall\login3.txt` — Manipulación de sesiones, tokens, OWASP
- `D:\PyCode\skill-bypass-paywall\login4.txt` — Tipología de barreras, técnicas por nivel
- `D:\PyCode\skill-bypass-paywall\login5.txt` — (duplicado de login1)
- `D:\PyCode\skill-bypass-paywall\login6.txt` — (duplicado de login2)
- `D:\PyCode\skill-bypass-paywall\login7.txt` — (duplicado de login3)
- `D:\PyCode\skill-bypass-paywall\login8.txt` — (duplicado de login4)
- `D:\PyCode\skill-bypass-paywall\paywall1.txt` a `paywall5.txt` — Investigación de paywalls (relacionado)
- `D:\PyCode\skill-bypass-paywall\articulo_gestion_ia_empresas.txt` — Artículo extraído exitosamente
