---
name: bypass-paywall
description: Técnicas, herramientas y workflows para acceder a contenido detrás de paywalls (suscripción), login/registration walls (autenticación) y plataformas de documentos (Scribd, Everand, SlideShare). Cubre métodos manuales, spoofing de headers, servicios web, extensiones, temp mail, automatización con Playwright/Selenium, y casos específicos como Gestión.pe, El Comercio, GEC y Scribd.
category: scraping
---

# Bypass de Paywalls y Login/Registration Walls — Guía Completa

## 1. Identificar el Tipo de Barrera

Antes de aplicar cualquier técnica, determina qué tipo de barrera enfrentas. Esto define qué métodos funcionan.

### Paywalls (contenido pagado)

| Tipo | Descripción | Bypassabilidad |
|------|-------------|----------------|
| **Soft Paywall (Metered)** | N artículos gratis vía cookies. El contenido completo está en el HTML pero oculto por CSS/JS | ✅ Alta |
| **Hard Paywall** | Bloquea desde el servidor. No envía el contenido hasta validar suscripción | ❌ Baja |
| **Freemium** | Contenido gratuito + premium bloqueado | ⚠️ Parcial |
| **Dynamic Paywall** | Se adapta según perfil/ubicación/comportamiento | ⚠️ Variable |

**Clave paywall**: Si el contenido se ve en View Source o DevTools, es soft → bypassable. Si el servidor ni siquiera envía el texto, es hard → servicios de archivo.

### Login/Registration Walls (autenticación)

| Tipo | Descripción | Ejemplos | Bypassabilidad |
|------|-------------|----------|----------------|
| **Login Wall / Overlay** | Overlay visual que oscurece contenido ya cargado y exige login | Pinterest, Quora (antiguo) | ✅ Alta (técnicas DOM) |
| **Registration Wall** | Exige crear cuenta gratuita (con email) | Foros, whitepapers, WiFi público | ✅ Media-Alta (temp mail) |
| **Hard Authentication (server-side)** | El servidor no envía contenido hasta autenticar | Bancos, intranets, GEC SSO | ❌ Baja (requiere credenciales) |
| **MFA / 2FA** | Segundo factor tras login | Microsoft 365, Google, bancos | ⚠️ Variable |

**Diferencia clave**: En login walls server-side (como id.gec.pe), el servidor **no envía el contenido protegido** sin sesión válida. Las técnicas de paywall (Googlebot UA, eliminar overlay) no funcionan aquí. Se necesita: temp mail para registro gratuito, OAuth, o session cookie reuse.

---

## 2. Métodos Rápidos (Sin Instalar Nada)

### 2.1 Modo Lectura / Reader Mode
Funciona en soft paywalls y login overlays que son capas JS sobre contenido ya cargado.

```
Chrome:  Menú → Más herramientas → Modo lectura
Firefox: Icono de libro en barra de direcciones
Edge:    F9 (Lector inmersivo)
Safari:  Icono de rectángulo con líneas
```

**Truco**: Recarga y activa modo lectura inmediatamente antes de que el script de bloqueo se ejecute.

### 2.2 Modo Incógnito + Limpiar Cookies
Para metered paywalls y registration walls que cuentan vistas vía cookies:

```
1. Cierra ventanas de incógnito abiertas
2. Ctrl+Shift+N → nueva ventana de incógnito
3. Accede al contenido
```

Si se agota el límite: limpia caché y cookies del sitio específico, repite.

### 2.3 Desactivar JavaScript
Para soft paywalls y login overlays client-side que dependen de JS.

```
Chrome: Configuración → Privacidad → Configuración de sitios → JavaScript → Bloquear
```

O desde DevTools (F12) → Settings → Disable JavaScript.

⚠️ Puede romper imágenes y carga dinámica, pero el texto base suele quedar accesible.

### 2.4 DevTools — Eliminar Overlay del DOM
Para paywalls y login walls que son capas visuales sobre contenido ya cargado:

```
1. F12 o Ctrl+Shift+I
2. Ctrl+Shift+C → click en el área bloqueada
3. En Elements, busca el contenedor (clase "paywall", "signwall", "modal-backdrop", "login-overlay")
4. Delete element o modifica CSS: display: none;
```

Busca también:
- `filter: blur(5px)` en el texto → elimínalo
- `overflow: hidden` en el body → cambia a `overflow: visible`
- `pointer-events: none` en contenedores padre

### 2.5 Google Cache
```
https://webcache.googleusercontent.com/search?q=cache:URL
```
Funciona tanto para paywalls como para login walls si el contenido fue público alguna vez.

### 2.6 Manipulación de Parámetros URL
Para registration walls mal configurados:

```
?logged_in=false → ?logged_in=true
?require_auth=1   → ?require_auth=0
?redirect=login   → eliminar el parámetro
```

También probar endpoints alternativos:
- `/api/v1/content` (protegido) vs `/api/v2/content` (no protegido)
- `/article?print=true` o `/article?format=amp` o `/article.json`

### 2.7 Alternative Frontends (Sin Login)
Servicios mirror que no requieren autenticación:

| Herramienta | Sitio Original | Estado |
|-------------|----------------|--------|
| **Nitter.net** | X/Twitter | Activo (múltiples instancias) |
| **Teddit.net** | Reddit | Activo |
| **Invidious** | YouTube | Activo |
| **Scribe.rip** | Medium | Activo |
| **Textise** | General | Activo |

---

## 3. Spoofing de Headers HTTP (Paywalls)

### 3.1 User-Agent Googlebot (Técnica #1 para Paywalls)
Los sitios entregan contenido completo a crawlers de Google para SEO.

```bash
curl -A 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' \
  'https://gestion.pe/economia/articulo-ejemplo-noticia/'
```

**Explicación**: El contenido está en el campo `articleBody` del JSON-LD (`schema.org/NewsArticle`). Gestión.pe usa Piano (Tinypass), paywall client-side. Googlebot recibe el HTML completo.

**Script de extracción**:
```python
import re, sys
html = sys.stdin.read()
match = re.search(r'"articleBody":"(.*?)"', html, re.DOTALL)
if match:
    body = match.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
    print(body)
```

### 3.2 User-Agent Twitterbot / Facebookbot
Algunos medios muestran contenido completo para compartir en redes:

```bash
curl -A 'Twitterbot/1.0' 'URL'
curl -A 'facebookexternalhit/1.1' 'URL'
```

### 3.3 Spoofing de Referer
```bash
curl -H 'Referer: https://t.co/' 'URL'
curl -H 'Referer: https://www.google.com/' 'URL'
```

### 3.4 DevTools (sin curl)
1. F12 → Network conditions (⋮ → More tools)
2. Desmarca "Select automatically"
3. Ingresa User-Agent de Googlebot, recarga

---

## 4. Servicios Web de Bypass

| Servicio | URL | Para | Estado 2026 |
|----------|-----|------|-------------|
| **Archive.is / Archive.ph** | `https://archive.is/newest/URL` | Hard paywalls, login walls | ✅ Funciona |
| **1ft.io** | `https://1ft.io/URL` | Soft paywalls | ⚠️ Intermitente |
| **Remove Paywall** | `https://remove-paywall.com/` | Paywalls generales | ✅ Funciona |
| **Smry.ai** | `https://smry.ai/URL` | IA resume paywalled | ✅ Funciona |
| **Wayback Machine** | `https://web.archive.org/web/URL` | Contenido histórico | ✅ Funciona |
| **Textise (Jina AI)** | `https://r.jina.ai/http://URL` | Extracción por IA | ✅ Funciona |
| **Outline** | `https://outline.com/URL` | Login/paywall strips | ✅ Funciona |
| **12ft.io** | Cerrado Jul 2025 | — | ❌ Muerto |

```bash
# Archive.is
curl -sL 'https://archive.is/newest/https://ejemplo.com/articulo/'

# Wayback Machine
curl -sL 'https://web.archive.org/web/2025/https://ejemplo.com/articulo/'
```

---

## 5. Extensiones de Navegador

### 5.1 Bypass Paywalls Clean (BPC)
La más potente para paywalls. Open source, 936+ sitios.

- **Chrome**: `gitlab.com/magnolia1234/bypass-paywalls-chrome-clean`
- **Firefox**: repo específico del mismo dev
- **Instalación**: ZIP → chrome://extensions → Modo desarrollador → Cargar descomprimida

Automatiza: limpieza de cookies, User-Agent Googlebot, bloqueo de scripts, spoofing referer.

### 5.2 Tampermonkey + Scripts Personalizados
Para login walls con variables client-side:

```javascript
// Forzar variables de autenticación en localStorage
(function(){
    localStorage.setItem('AccessGranted', 'true');
    localStorage.setItem('articlesLeft', '999');
    localStorage.setItem('logged_in', 'true');
})();
```

### 5.3 SpectreView (Userscript)
Script para bypass de login walls, overlays y paywalls en Twitter, Instagram, Reddit, Quora, Medium. Elimina los elementos que bloquean el contenido.

### 5.4 EditThisCookie / Cookie-Editor
Para session cookie injection: exportar cookies de una sesión autenticada e importarlas en otro navegador/sesión.

### 5.5 uBlock Origin (modo avanzado)
Bloquear scripts específicos del paywall/login sin desactivar JS globalmente.

---

## 6. Temp Mail para Registration Walls

Cuando un sitio exige registro gratuito con email, los servicios de correo temporal permiten crear cuentas al instante.

### Servicios Activos (2026)

| Servicio | API | Ideal para |
|----------|-----|------------|
| **Mail.tm** | ✅ REST API | Automatización programática |
| **10 Minute Mail** | ❌ | Uso manual rápido |
| **Guerrilla Mail** | ✅ REST API | Alternativa con API |
| **Temp-Mail.org** | ✅ limitada | Uso manual |
| **Mailinator** | ✅ API | Popular pero bloqueado |
| **YOPmail** | ❌ | Persistente, simple |

### Automatización con Mail.tm API (Python)

```python
import requests, time

BASE = "https://api.mail.tm"
with requests.Session() as s:
    # Obtener dominio disponible
    r = s.get(f"{BASE}/domains", headers={"Accept": "application/ld+json"})
    domain = r.json()["hydra:member"][0]["domain"]

    # Crear cuenta temporal
    email = f"user{int(time.time())}@{domain}"
    password = "TempPass123!"
    s.post(f"{BASE}/accounts", json={"address": email, "password": password})

    # Obtener token
    r = s.post(f"{BASE}/token", json={"address": email, "password": password})
    token = r.json()["token"]
    s.headers.update({"Authorization": f"Bearer {token}"})

    # Esperar emails de verificación
    for _ in range(30):
        r = s.get(f"{BASE}/messages", headers={"Accept": "application/ld+json"})
        if r.json()["hydra:member"]:
            print("Email recibido:", r.json()["hydra:member"][0])
            break
        time.sleep(1)
```

### Truco Gmail Plus
`tunombre+sitioweb@gmail.com` → Gmail lo recibe como `tunombre@gmail.com`. Útil para registros únicos sin crear cuentas nuevas.

---

## 7. Session Cookie Reuse

Una vez autenticado en un sitio, exportar las cookies para reutilizarlas sin re-login.

### CLI con curl
```bash
# Login y guardar cookies
curl -X POST 'https://id.gec.pe/elcomercio/login' \
  -c cookies.txt \
  -d 'username=email@ejemplo.com&password=contraseña'

# Reutilizar cookies para acceder a contenido protegido
curl -b cookies.txt 'https://elcomercio.pe/economia/articulo/'
```

### Python con requests.Session
```python
import requests
from http.cookiejar import LWPCookieJar

session = requests.Session()
session.cookies = LWPCookieJar("cookies.txt")

# Cargar cookies guardadas
try:
    session.cookies.load(ignore_discard=True)
except FileNotFoundError:
    # Login flow
    pass

# Acceder a contenido autenticado
r = session.get("https://elcomercio.pe/contenido-protegido/")
```

### Playwright — Session Persistence
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Restaurar sesión guardada
    context = p.chromium.launch_persistent_context(
        user_data_dir="/ruta/al/perfil",
        headless=False
    )
    page = context.new_page()
    page.goto("https://elcomercio.pe/contenido-protegido/")

    # Para guardar sesión después de login:
    # context.storage_state(path="auth.json")
```

---

## 8. Automatización Completa (Login + Paywall)

### 8.1 Login automático con Selenium
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--user-data-dir=/perfil_chrome")  # Mantiene sesión
driver = webdriver.Chrome(options=options)

driver.get("https://id.gec.pe/elcomercio/login")
driver.find_element(By.NAME, "username").send_keys("email@ejemplo.com")
driver.find_element(By.NAME, "password").send_keys("contraseña")
driver.find_element(By.XPATH, "//button[text()='Continuar']").click()

# Ahora acceder al artículo
driver.get("https://elcomercio.pe/economia/articulo/")
print(driver.page_source)
```

### 8.2 Pipeline completo: Temp Mail → Registro → Login → Extracción
```python
# Pseudocódigo del pipeline completo
# 1. mail.tm crea un inbox temporal
# 2. Playwright navega al formulario de registro
# 3. Completa campos con el email temporal
# 4. mail.tm polling para capturar link de verificación
# 5. Playwright hace clic en el link
# 6. Guarda storage_state (cookies)
# 7. Usa el estado guardado para acceder a contenido
# 8. Extrae el artículo

# Desafíos comunes:
# - reCAPTCHA → 2captcha (servicio de pago, ~$0.50/1000 solves)
# - Rate limiting → proxies residenciales
# - Fingerprinting → Playwright stealth mode
```

---

## 9. Caso Específico: Gestión.pe / El Comercio / GEC

### Arquitectura del Grupo El Comercio

| Componente | Detalle |
|------------|---------|
| **SSO** | `id.gec.pe` — Identity Provider centralizado |
| **Método login** | POST a `id.gec.pe/elcomercio/login` con `username` + `password` |
| **OAuth** | Google ("Iniciar con Google") |
| **Protección** | reCAPTCHA en login |
| **Paywall** | Piano (Tinypass) — client-side, contenido en JSON-LD |

### Para paywall (artículos): Googlebot UA
```bash
curl -sL -A 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' \
  'https://gestion.pe/economia/ARTICULO/' | \
  python3 -c "
import re, sys
html = sys.stdin.read()
m = re.search(r'\"articleBody\":\"(.*?)\"', html, re.DOTALL)
if m:
    print(m.group(1).replace('\\\\n', '\\n').replace('\\\"', '\"'))
"
```

### Para login (id.gec.pe): OAuth Google o registro + session persistence
1. Usar "Iniciar con Google" si tienes cuenta Google
2. O registrarse con temp mail (si permiten registro gratuito)
3. Una vez autenticado: Playwright `storage_state` → cookies.txt → curl

**Referencia detallada**: `references/gec-login-architecture.md` — análisis técnico del formulario de login, reCAPTCHA, Google OAuth, y session persistence.

### Sitios del grupo que comparten esta arquitectura
- gestion.pe
- elcomercio.pe
- depor.com
- trome.com
- peruquiosco.pe
- clubelcomercio.pe

---

## 9b. Caso Específico: Scribd / Everand (Document Platform)

### Mecanismo de protección

Scribd NO sirve PDFs. Renderiza en `<canvas>` con fragmentación tipo puzzle (confirmado por changelog de HugoAleOlguin v2.9.0). Las herramientas viejas que hacían "canvas stitching" (rearmar tiles) están rotas desde que Scribd cambió el algoritmo.

### Método verificado (Jul 2026)

**fullstackusama/scribd-downloader** (Python + Selenium + CDP):
1. Convierte URL → embed: `scribd.com/embeds/{ID}/content`
2. Abre en Chrome headless, scrollea para lazy-load
3. Imprime a PDF vía CDP `Page.printToPDF`

### ⚠️ Pitfalls críticos

**Subdominio `es.scribd.com`**: el regex de `convert_scribd_link()` solo acepta `www.scribd.com`. Normalizar:
```python
url = re.sub(r'https://[\w.-]+\.scribd\.com/', 'https://www.scribd.com/', url)
```

**CDP stream roto en Chrome 149**: `transferMode: "ReturnAsStream"` produce `"Invalid stream handle"`. Usar `"ReturnAsBase64"`:
```python
pdf_opts = {"transferMode": "ReturnAsBase64", ...}
```

**Documentos gigantes (1000+ págs)**: algunos son hojas de cálculo enormes. Poner `MAX_PAGES=200`.

**Reutilizar sesión Chrome**: no abrir/cerrar browser por cada doc. Una sola sesión para todo el batch.

Detalle completo en `references/scribd-download.md`.

---

## 10. Árbol de Decisión Unificado

```
¿El contenido es académico/científico?
├── SÍ → Unpaywall, Sci-Hub, arXiv, Google Scholar
└── NO → ¿Tipo de plataforma?

         === DOCUMENT PLATFORM (Scribd, Everand, SlideShare, Issuu) ===
         ├── Documento público/visible →
         │    ├── Servicio web: scribdown.netlify.app (pega URL, descarga PDF)
         │    ├── Extensión Chrome: Scribd Downloader (3/día gratis)
         │    ├── Wayback Machine (algunas URLs cacheadas)
         │    └── Extensión Chrome: Scribd PDF Downloader (gratis)
         ├── Documento premium/pago →
         │    ├── Temp mail + free trial de Scribd (método legal)
         │    └── Python + Playwright si tienes cuenta (scribd-downloader)
         ├── Puedes iniciar sesión? →
         │    ├── scribd-downloader (Python/Playwright) + cuenta propia
         │    └── Sistema de créditos de Scribd (subir docs → descargar)
         └── Ver `references/scribd-download.md` para método verificados (Selenium+CDP batch), pitfalls de subdominio/stream, y catálogo completo de herramientas
         │
         === PAYWALL (contenido pagado) ===
         ├── Hard (no hay texto en HTML) → Archive.is / Wayback Machine
         ├── Soft (texto en HTML, oculto) →
         │    ├── Modo lectura, desactivar JS, DevTools
         │    ├── Googlebot UA spoofing ← RECOMENDADO
         │    └── Extensiones BPC / Tampermonkey
         └── Metered (contador de vistas) →
              ├── Incógnito + limpiar cookies
              └── Google Cache

         === LOGIN WALL (autenticación) ===
         ├── Server-side (no hay datos sin sesión) →
         │    ├── Si el registro es gratuito: Temp mail + auto-registro
         │    ├── Si hay OAuth: Login con Google/Facebook
         │    └── Session cookie reuse (si ya tienes acceso)
         ├── Client-side overlay (datos en DOM) →
         │    ├── DevTools: eliminar overlay del DOM
         │    ├── Desactivar JavaScript
         │    ├── Manipular cookies/logged_in
         │    └── Tampermonkey script personalizado
         └── Registration wall (email) →
              ├── Mail.tm API (automático)
              └── Temp-mail.org / 10minutemail (manual)

¿Ninguno funciona? → Probar en orden:
   1. Google Cache / Wayback Machine
   2. Alternative frontends (Nitter, Scribe, Teddit)
   3. Archive.is
   4. Textise / Jina AI
   5. Bypass Paywalls Clean (extensión)
   6. Temp mail + Playwright (si hay registro gratuito)
```

---

## 11. Consideraciones Legales y Éticas

- **Términos de servicio**: La mayoría de sitios prohíben la evasión de paywalls/login walls
- **CFAA (EE.UU.)**: Van Buren v. United States (2021) redujo el alcance; violar ToS no es necesariamente delito
- **GDPR (UE)**: Crear identidades falsas puede violar leyes de protección de datos
- **Uso legítimo**: Investigación académica, periodismo de investigación, accesibilidad
- **Stop si te lo piden**: Continuar tras un cease-and-desist cambia el panorama legal
- **Alternativas legales**: Bibliotecas con suscripciones (PressReader, ProQuest), tarjetas de biblioteca, períodos de prueba gratuitos
- **Sostenibilidad**: Si consumes regularmente un medio, considera apoyar con una suscripción

---

## 12. Referencias

- `D:\PyCode\skill-bypass-paywall\paywall1.txt` al `paywall5.txt` — Técnicas de paywall
- `D:\PyCode\skill-bypass-paywall\login1.txt` al `login8.txt` — Técnicas de login/registration walls
- `D:\PyCode\skill-bypass-paywall\articulo_gestion_ia_empresas.txt` — Artículo extraído exitosamente
- `references/gec-id-login-analysis.md` — Análisis técnico del SSO de Grupo El Comercio (id.gec.pe): arquitectura, reCAPTCHA, técnicas aplicables
- `references/scribd-download.md` — **Scribd/Everand sin cuenta (Jul 2026)**. Arquitectura Canvas + image tiles + fragmentación puzzle, embed URL `scribd.com/embeds/{ID}/content`, método Selenium+CDP `Page.printToPDF` con `ReturnAsBase64`. Pitfalls verificados: subdominio `es.scribd.com`, CDP stream roto en Chrome 149, documentos gigantes 1000+ págs, lazy loading. Catálogo de herramientas verificadas (GitHub/web/extensiones). Batch wrapper Python para 59 docs probado en WSL.
- `references/pdf-contact-extraction.md` — **Extraer correos de PDFs descargados → CSV**. Extractor inline con PyMuPDF + regex emails/teléfonos/nombres peruanos. Genera `contacts.csv` (name,email,phone) + `emails_only.csv`. Resultados de prueba: 31 PDFs → 1064 correos únicos. Pitfalls: PDFs escaneados sin OCR, límite 50 págs, falsos positivos de teléfono. Template: `/mnt/d/PyCode/SkillScribidDown/extract_contacts.py`.
- `D:\\PyCode\\skill-bypass-paywall\\` → carpeta completa con toda la investigación original
