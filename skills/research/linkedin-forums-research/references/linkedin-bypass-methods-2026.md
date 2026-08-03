# LinkedIn Bypass Methods — Resultados de Pruebas (Jun 2026)

IP de prueba: 38.25.16.30 (datacenter, Browserbase sin proxies residenciales)

---

## Método 1: Serper API + Google Dorking ✅ FUNCIONA

**Estado:** Funciona desde cualquier IP (es API, no scraping).
**Costo:** Free tier: 2500 queries/mes. ~$0.01/100 queries después.
**Setup:** Variable de entorno `SERPER_API_KEY`.

**Recomendaciones:**
- Usar `site:linkedin.com/pulse` para artículos, `site:linkedin.com/in` para perfiles
- Agregar filtro temporal: `tbs=qdr:m6` en el JSON de Serper
- `gl=pe` para resultados de Perú, `gl=es` para España, `gl=us` para global
- Espaciar queries con `sleep(0.3)` para evitar rate limits

---

## Método 2: Jina AI Reader ✅ FUNCIONA (bypass completo de authwall)

**Estado:** Bypass completo del muro de login de LinkedIn Pulse.
**URL base:** `https://r.jina.ai/http://www.linkedin.com/pulse/[SLUG]`
**Headers:** `X-Return-Format: markdown`

**Pruebas exitosas (Jun 2026):**
| Artículo | Estado | Tamaño |
|---|---|---|
| RAG, Confidentiality, and the Future of AI in Legal Practice | ✅ Completo | 38 KB |
| Beyond Naive RAG: Achieving High-Precision Legal AI | ✅ Completo | 36 KB |
| Adaptive RAG and Access to Justice | ✅ Completo | 35 KB |
| NotebookLM para abogados | ✅ Completo | 25 KB |
| IA agéntica: hacia un nuevo modelo operativo | ✅ Completo | 34 KB |
| Graph RAG in Production | ✅ Completo | 40 KB |
| Why Claude Legal Works—Until It Doesn't | ✅ Completo | 38 KB |
| The Agentic Edge - Why Most Legal RAG Pilots Fail | ✅ Completo | 35 KB |
| Operational AI in Law Firms | ✅ Completo | 31 KB |
| Legal Engineering for Semi-Automated Legal Work | ✅ Completo | 110 KB |
| La promesa rota de la IA para abogados | ⚠️ Parcial | El paywall más fuerte |

**Tasa de éxito:** ~90% en artículos Pulse estándar.
**Fallas típicas:**
- Paywall fuerte (~10%): el contenido está completamente detrás de login
- Timeout (>20s) en artículos muy largos
- Rate limit de Jina AI si se hacen >10 requests/min

---

## Método 3: Google Translate Proxy ⚠️ PARCIAL

**Estado:** Funciona para Jobs, NO para Pulse ni Company pages.
**URL:** `translate.google.com/translate?hl=es&sl=auto&tl=es&u=[URL]`

**Pruebas:**
- **LinkedIn Jobs:** ✅ Muestra listados completos de empleos. Probado con
  "legal tech Peru" → 9 resultados (vs 2 sin proxy).
- **LinkedIn Pulse:** ❌ Redirige a "No se puede usar este formulario" cuando
  hay forms de login.
- **LinkedIn Company:** ❌ Redirige a feed principal o "Page not found".

---

## Método 4: Google / Bing / DuckDuckGo directo ❌ BLOQUEADO

**Estado:** Todos bloquean IPs de datacenter con CAPTCHA/Cloudflare.
**Solución:** Serper API para búsquedas (es una API, no scraping directo).

---

## Conclusión: Stack recomendado

```
Descubrimiento:  Serper API (Google dorking) ← desde cualquier IP
Lectura:         Jina AI Reader (r.jina.ai) ← bypass authwall
Empleos:         Google Translate proxy ← bypass login
Comentarios:     HN Algolia API (hn.algolia.com) ← sin auth
Profundidad:     Browser login (cuando se necesita acceso completo)
```
