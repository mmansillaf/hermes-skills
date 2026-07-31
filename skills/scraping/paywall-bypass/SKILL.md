---
name: paywall-bypass
description: Access and extract content from subscription/paywall-restricted news sites (Gestión, El Comercio, NYT, WSJ, etc.) via Googlebot UA spoofing, archive services, DOM manipulation, and structured data extraction.
category: scraping
triggers:
  - paywall bypass
  - subscription wall
  - acceso a contenido premium
  - bypass paywall
  - extraer artículo detrás de paywall
  - Googlebot user-agent
  - JSON-LD article extraction
  - bypass suscripción
  - paywall Gestión Perú
  - Grupo El Comercio paywall
---

# Paywall Bypass — Técnicas de Acceso a Contenido Restringido

## 📋 Clasificación de Paywalls

| Tipo | Descripción | Bypassable |
|------|-------------|-----------|
| **Soft Paywall (Metered)** | Permite N artículos gratis vía cookies (NYT, Washington Post) | ✅ Alta |
| **Hard Paywall** | Bloquea desde servidor (WSJ, Financial Times) | ❌ Baja |
| **Freemium** | Contenido gratis + premium bloqueado (Medium, diarios locales) | ⚠️ Parcial |
| **Registration Wall** | Exige cuenta gratuita (LinkedIn, portales) | ✅ Media-Alta |
| **Dynamic** | Se adapta por perfil/comportamiento | ⚠️ Variable |

## 🎯 Técnica Principal: Googlebot User-Agent Spoofing (Probada)

La más efectiva porque los medios **entregan el contenido completo a crawlers de Google para SEO**.

### Método curl (probado en Gestión.pe)

```bash
curl -sL -A 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' \
  'https://gestion.pe/economia/articulo-noticia/' | python3 -c "
import sys, re
html = sys.stdin.read()
match = re.search(r'\"articleBody\":\"(.*?)\"', html, re.DOTALL)
if match:
    body = match.group(1).replace('\\\\n', '\n').replace('\\\\\"', '\"')
    print(body)
"
```

### En DevTools (manual)
1. F12 → Network conditions → Desmarcar "Select automatically"
2. Pegar User-Agent de Googlebot
3. Recargar página

### En navegador vía extensión
- User-Agent Switcher (Chrome/Firefox)
- Configurar perfil Googlebot

## 📐 Extracción del contenido vía JSON-LD

Muchos sitios (Gestión, El Comercio, Grupo El Comercio) usan **Piano** como paywall y estructuran el artículo completo en JSON-LD `schema.org/NewsArticle`:

```json
{
  "@type": "NewsArticle",
  "headline": "...",
  "articleBody": "...",
  "datePublished": "...",
  "description": "...",
  "author": "..."
}
```

**Tags clave en HTML** que indican contenido premium:
- `<meta property="article:content_tier" content="locked"/>`
- `<meta name="cXenseParse:per-tiponota" content="premium"/>`
- `<meta property="mrf:tags" content="notaPaywall:premium"/>`
- `EXCLUSIVO PARA SUSCRIPTORES` / `PLUS G`

## 🛠️ Técnicas Alternativas

### Nivel Básico (Sin instalar nada)
| Técnica | Cómo | Mejor para |
|---------|------|-----------|
| **Modo Lectura** | Barra URL / F9 (Edge) | Soft paywalls |
| **Modo Incógnito** | Ctrl+Shift+N | Metered (cookies) |
| **Desactivar JS** | DevTools → Settings → Disable JS | Soft paywalls JS |
| **DevTools DOM** | F12 → Delete element del overlay | CSS paywalls |

### Servicios Web
| Servicio | URL | Estado |
|----------|-----|--------|
| **Archive.is / Archive.ph** | `archive.is/newest/[URL]` | ✅ Funciona |
| **Wayback Machine** | `web.archive.org/web/[URL]` | ✅ Artículos antiguos |
| **1ft.io** | `1ft.io/[URL]` | ⚠️ Reemplazo de 12ft.io (cerrado) |
| **Textise** | `textise.iitty` | ✅ Texto plano |
| **RemovePaywall.com** | Web app | ✅ Multi-método |
| **Smry.ai** | `smry.ai/[URL]` | ✅ Resumen IA |

### Extensiones de Navegador
- **Bypass Paywalls Clean (BPC)** — La más completa, open source, ~936 sitios. No está en Chrome Web Store; instalación manual desde GitLab/GitHub.
- **Universal Web Bypass Injector** — Parcha Fetch/XHR, 80+ patrones.
- **Quick Archive Redirect** — Redirige a archive.is automáticamente.

### Spoofing de Referrer
```bash
curl -H "Referer: https://www.google.com/" [URL]
curl -H "Referer: https://t.co/" [URL]  # Twitter/X
```

### Google Cache
```
https://webcache.googleusercontent.com/search?q=cache:[URL]
```

## 📁 Investigación Local

El usuario mantiene investigación exhaustiva en:
`D:\PyCode\skill-bypass-paywall\` (paywall1.txt, paywall2.txt, paywall3.txt)

## ⚠️ Pitfalls

- **12ft.io cerró en julio 2025** por presión legal. Usar 1ft.io o Archive.is como alternativa.
- **Hard paywalls** (WSJ, FT) no entregan el contenido ni a Googlebot — requieren archive services.
- **Sitios con DataDome** (protección anti-bot) pueden bloquear curl incluso con Googlebot UA. Usar browser real o Selenium.
- **Gestión.pe y Grupo El Comercio** usan Piano.io como plataforma de suscripción — el contenido está en JSON-LD en el HTML original.
- El Googlebot UA funciona porque el sitio entrega el `articleBody` para indexación SEO. Si cambian su implementación (servir solo lead + paywall también a bots), la técnica deja de funcionar.
- **No usar en producción a escala** — viola términos de servicio de los sitios.

## 🔬 Verificación

1. `curl` con Googlebot UA + grep por `articleBody`
2. `wget` con User-Agent personalizado
3. Browser → DevTools → Network → Recargar → Buscar petición HTML → Ver si está el contenido completo
