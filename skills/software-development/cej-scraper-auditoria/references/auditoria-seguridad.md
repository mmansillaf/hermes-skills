# Auditoria de Seguridad - cej.pj.gob.pe
## Hallazgos de la sesion del 08-Jun-2026

## Resumen

Auditoria black-box (sin credenciales) realizada desde ThinkPad P53 (Linux) con
Chrome real + VPN Proton MX (WireGuard). Radware fue bypassed exitosamente.

## Metodos de bypass probados

| Metodo | Resultado |
|---|---|
| rebrowser-playwright headless (IP directa) | Intermitente |
| rebrowser-playwright + VPN Proton NL (OpenVPN) | BLOQUEADO (IP NL reconocida como VPN) |
| rebrowser-playwright + VPN Proton MX (WireGuard) | ACCESO EXITOSO |
| Chrome real + perfil persistente + debugging (sin VPN) | ACCESO EXITOSO |
| Chrome real + WireGuard MX | ACCESO EXITOSO |
| browser_navigate de Hermes | BLOQUEADO (headless detectable) |
| curl/requests directos | BLOQUEADO por Radware |

## Cabeceras de seguridad

TODAS ausentes. Zero proteccion a nivel HTTP:
- Strict-Transport-Security (HSTS): AUSENTE
- Content-Security-Policy (CSP): AUSENTE
- X-Frame-Options: AUSENTE
- X-Content-Type-Options: AUSENTE
- X-XSS-Protection: AUSENTE
- Referrer-Policy: AUSENTE
- Permissions-Policy: AUSENTE

Esto expone a clickjacking, MIME-sniffing, XSS sin mitigacion CSP, y
posible downgrade MITM por falta de HSTS.

## Cookies

Cookies de Radware (__uzma, __uzmb, etc):
- Sin flag HttpOnly (accesibles desde JS -> XSS puede robarlas)
- Sin flag Secure (se envian tambien por HTTP)
- Sin SameSite configurado

Cookie PHPSESSID de perfdrive.com: Secure=True pero HttpOnly=False.

## CSRF

Meta tag `<meta name="_csrf" content="">` existe pero con valor VACIO.
Los formularios POST no tienen token CSRF funcional.

## JSF ViewState

No se encontro `javax.faces.ViewState`. El sitio migro de JSF a Angular.
Sin vector de deserializacion JSF.

## Backend inferido

- Server header: `rdwr` (Radware reverse proxy)
- Backend real: Java (JBWEB - posiblemente JBoss/Tomcat)
- Framework frontend: Angular (compilado, no JSF)
- APIs: No detectadas directamente. Los formularios POSTean a
  `busquedacodform.html` y `detalleform.html` (postbacks clasicos)

## Documentacion del WAF

- Radware deploya proteccion condicional segun IP/fingerprint:
  - IPs de datacenter/VPN conocidas: BLOQUEO DIRECTO (403)
  - IPs de datacenter menos conocidas (Proton MX): CAPTCHA hCaptcha
  - IPs limpias o Chrome real con perfil: PASO DIRECTO sin captcha
- El captcha hCaptcha de Radware usa sitekey `ae73173b-7003-44e0-bc87-654d0dab8b75`
- Una vez pasado Radware, el CEJ tiene su propio captcha de texto
- Las cookies __uzm* son el mecanismo de tracking de sesion de Radware

## Captcha interno del CEJ

- Imagen PNG de 4 caracteres alfanumericos (fuente distorsionada, fondo ruidoso)
- URL: `https://cej.pj.gob.pe/cej/Captcha.jpg` (con query param timestamp anti-cache)
- Se extrae via canvas: `canvas.toDataURL('image/jpeg', 0.85)`
- 2Captcha API v2 (ImageToTextTask): tasa de acierto ~35-50%
- Alternativas no probadas: Anti-Captcha, CapSolver, ddddocr (OCR local)

## Proteccion por capas del sitio

1. Radware WAF (primera linea - la unica realmente efectiva)
2. Captcha de texto interno (segunda linea - debil)
3. No hay mas capas detectadas

## Riesgos identificados

- Si Radware es bypassed, no hay capas de seguridad adicionales
- Clickjacking posible - el sitio puede embeberse en iframes maliciosos
- Las cookies sin HttpOnly permiten exfiltracion via XSS
- Sin HSTS, un MITM puede interceptar la conexion si el usuario usa HTTP
- Los codigos de expediente son predecibles (formato secuencial NNNNN-AAAA-...)

## URLs y endpoints documentados

```
GET  /cej/forms/busquedaform.html        - Pagina principal (acepta GET)
GET  /cej/forms/busquedacodform.html     - 405 (solo POST)
POST /cej/forms/busquedacodform.html     - Busqueda por codigo
GET  /cej/forms/detalleform.html         - Detalle del expediente
GET  /cej/forms/documentoD.html?nid=XXX  - Descarga de documentos
GET  /cej/forms/preguntasFrecuentes.html - FAQ
GET  /cej/Captcha.jpg                    - Imagen del captcha
```
