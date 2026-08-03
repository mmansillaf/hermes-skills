# Auditoría de Seguridad — cej.pj.gob.pe (Jun 2026)

## Metodología
Black-box audit a través de Radware WAF. Se usó rebrowser-playwright para acceder al sitio real y wapiti3 para escaneo desde afuera.

## Hallazgos de Seguridad

### H1 — Ausencia total de cabeceras de seguridad [CRITICO]

| Cabecera | Estado | Riesgo |
|---|---|---|
| `Strict-Transport-Security` (HSTS) | AUSENTE | Downgrade attack HTTP → MITM |
| `Content-Security-Policy` (CSP) | AUSENTE | XSS, data exfiltration, clickjacking |
| `X-Frame-Options` | AUSENTE | Clickjacking: el sitio puede embeberse en iframe |
| `X-Content-Type-Options` | AUSENTE | MIME sniffing |
| `X-XSS-Protection` | AUSENTE | Protección antigua contra XSS reflejado |
| `Referrer-Policy` | AUSENTE | Fuga de URL vía Referer header |
| `Permissions-Policy` | AUSENTE | APIs del navegador sin restricciones |

### H2 — Cookies sin HttpOnly/Secure [ALTO]

Cookies de Radware (`__uzma`, `__uzmb`, `__uzmc`, `__uzmd`, `__uzme`, `__uzmf`):
- Sin `HttpOnly` → accesibles desde JavaScript (XSS puede robarlas)
- Sin `Secure` → se envían también por HTTP
- Sin `SameSite` configurado

Cookie `PHPSESSID` de perfdrive.com: `Secure=True` pero `HttpOnly=False`.

### H3 — CSRF Token vacío [MEDIO]

```html
<meta name="_csrf" content="">
```

El token CSRF existe en el HTML pero está **vacío**. Los formularios hacen POST sin verificación CSRF efectiva.

### H4 — Servidor expone tecnología [BAJO]

`server: rdwr` → Radware. No se puede fingerprintear el backend real.

### H5 — Dependencia exclusiva de Radware [MEDIO]

No hay WAF secundario, rate limiting a nivel aplicación, ni validación de input visible desde frontend. Si Radware es bypassed, no hay más capas de seguridad.

## Tecnología Inferida

| Componente | Evidencia |
|---|---|
| WAF | Radware (perfdrive.com) — `server: rdwr`, cookies `__uzm*` |
| Captcha | hCaptcha — sitekey `ae73173b-7003-44e0-bc87-654d0dab8b75` |
| Frontend | Angular compilado (js/main.*.js bundles) + jQuery 1.10.2 + Bootstrap |
| Backend | Java (JBWEB — posiblemente JBoss/Tomcat) |
| Tracking | Stormcaster JS (`/18f5227b-.../stormcaster.js`), Google Analytics UA-47013024-7 |
| Framework anterior | JSF Mojarra (scrapy_pj mostraba `javax.faces.ViewState`, formularios `formBusqueda`) |

## Lo que NO se pudo probar (Radware bloquea)

1. **JSF ViewState Deserialization**: Si el backend usa `STATE_SAVING_METHOD=client` con clave débil, podría haber RCE via ysoserial. Requiere acceso sin Radware para interceptar el ViewState.
2. **IDOR**: Los códigos de expediente son predecibles (`NNNNN-AAAA-I-DDDD-OO-EE-II`). Probar si cambiando el número se accede a datos de otros expedientes.
3. **API REST interna**: Angular sugiere APIs no documentadas en `/cej/api/` o `/cej/rest/`. Radware bloquea el acceso directo.
4. **SQLi / XSS**: No se encontraron, pero el WAF bloquea los payloads del scanner antes de llegar al servidor real.

## Herramientas usadas

```bash
~/cej-scraper/bin/  # venv con:
  - rebrowser-playwright 1.52.0
  - 2captcha-python 2.0.7
  - wapiti3 3.3.0
  - undetected-chromedriver 3.5.5
  - selenium 4.36.0
  - playwright 1.60.0
```

## Reportes guardados

- `/home/usuario/INFORME_AUDITORIA_CEJ.md` — Auditoría general + scraping + proxies
- `/home/usuario/INFORME_SEGURIDAD_CEJ.md` — Auditoría de seguridad pura
- `/home/usuario/wapiti_cej/` — Reporte HTML de wapiti (resultados limitados por Radware)
