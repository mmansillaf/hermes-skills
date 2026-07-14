# CEJ Scraper - Technical Reference

## Radware behavior (observed June 2026)

| Condition | Result |
|---|---|
| Chrome real + perfil persistente + remote debugging | ✅ Bypass completo |
| Chrome real + VPN MX (Proton free WireGuard) | ✅ Bypass completo |
| Chrome real + VPN NL (Proton free) | ❌ Bloqueado |
| rebrowser-playwright headless (sin VPN) | ⚠️ Intermitente |
| rebrowser-playwright headless + VPN MX | ✅ Funciona a veces |
| browser_navigate de Hermes | ❌ Bloqueado (headless detectable) |
| curl / requests directos | ❌ Bloqueado (Radware responde 302/403) |

**Anti-bloqueo:**
- Usar SIEMPRE Chrome real con perfil persistente reutilizado
- No cambiar de IP durante la sesion
- Sleeps de 5-15s entre acciones
- Rotar sesion cada ~15 min (timeout del sitio)
- No refrescar pagina sin necesidad

## Endpoint de descarga: documentD.html

```
GET https://cej.pj.gob.pe/cej/forms/documentoD.html?nid=<HASH>
```

**Caracteristicas:**
- NO requiere cookies de sesion
- SIN rate limiting (probado 5 requests consecutivos en ~1s sin bloqueo)
- Respuesta: PDF (resoluciones) o HTML (notificaciones/cédulas ~15KB)
- Clase de enlace en DOM: `aDescarg`
- Detectar PDF: `r.content[:4] == b'%PDF'`

**IDs (nid):**
- Longitud variable: 15-20 caracteres
- Alfanumerico: a-z, A-Z, 0-9 (~52 caracteres posibles)
- Sin patron detectable de secuencia
- Modificar un caracter → HTML de error (15KB), no 403

## Captcha de texto

- URL: `/cej/Captcha.jpg`
- Tipo: 4 caracteres alfanumericos, fondo con ruido
- Extraccion via canvas Selenium (resolucion natural, JPEG q0.85)
- ddddocr: funciona para ~40-60% de los casos (gratis)
- 2Captcha v2 (ImageToTextTask): funciona para ~35-50%
- Estrategia recomendada: ddddocr primero, 2Captcha fallback (~60-80% efectivo)

## Formulario de busqueda por codigo

```
POST https://cej.pj.gob.pe/cej/forms/busquedacodform.html
```

Campos:
- cod_expediente (5 digitos), cod_anio (4), cod_incidente, cod_distprov (4)
- cod_organo (JP/JR), cod_especialidad (CI/PE/LA/FC/DC), cod_instancia (01/02)
- **parte** — nombre del demandante/demandado (OBLIGATORIO)

Formato codigo: `NNNNN-AAAA-I-DDDD-OO-EE-II`

## Hallazgos de seguridad (Junio 2026)

| Hallazgo | Severidad |
|---|---|
| Sin HSTS, CSP, X-Frame-Options, X-Content-Type-Options | CRITICO |
| Cookies sin HttpOnly/Secure | ALTO |
| CSRF token `<meta name="_csrf" content="">` vacio | MEDIO |
| documentD.html funciona sin auth (solo hash nid) | MEDIO |
| Sin rate limiting en descargas | INFO |
| Migraron de JSF a Angular — no hay ViewState que explotar | INFO |

## Proyecto Windows (otro equipo)

- Chrome real + `--remote-debugging-port=9225`
- 2 spiders Scrapy + undetected-chromedriver paralelos (A y B)
- 38,242 expedientes (LA+DC), ~334 completados a Jun 2026
- Captcha: 2Captcha v2 ImageToTextTask
- Filtro documentos: solo keywords (SENTENCIA, RESOLUCION, AUTO FINAL, etc)
- Checkpoint JSON por spider
- Runner con auto-reinicio y rotation cada 90 min
