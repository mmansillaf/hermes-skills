# Web Security Audit: cej.pj.gob.pe (08 Jun 2026)

Real-world example of a web application security audit using Phase 8 methodology.

## Target

https://cej.pj.gob.pe/cej/forms/busquedaform.html — Consulta de Expedientes Judiciales (Peru Judicial Branch)

## Stack Tecnologico Detectado

| Componente | Tecnologia |
|---|---|
| Anti-bot | Radware Bot Manager (perfdrive.com) |
| Captcha | hCaptcha (checkbox + challenge) |
| Frontend | HTML + jQuery 1.10.2 + Bootstrap |
| Backend | Java (JBWEB — JBoss/Tomcat) |
| Framework JS | Angular (compiled /cej/js/main.*.js) |
| Tracking | Stormcaster JS (Radware analytics) |
| Server header | `server: rdwr` (Radware proxy) |

## Radware Bypass

**Metodo exitoso:** `rebrowser-playwright` (headless) + stealth patches via `add_init_script()`.

**Pasos:**
1. Navegar a `https://cej.pj.gob.pe/cej/forms/busquedaform.html` (NO directo a `busquedacodform.html`)
2. Radware NO bloquea esta ruta con fingerprint realista
3. Hacer click en tab "Por Codigo de Expediente" (`a[href="#tabs-2"]`)
4. Llenar formulario de 7 campos
5. Submit con captcha de texto (captcha_image) resuelto via 2Captcha

**Path bloqueado:** GET directo a `busquedacodform.html` → Radware redirige a `validate.perfdrive.com`

## Captcha Info

- **hCaptcha sitekey:** `ae73173b-7003-44e0-bc87-654d0dab8b75` (para Radware bypass)
- **Captcha interno CEJ:** Texto de 4 caracteres alfanumericos, imagen PNG con ruido de fondo
- **2Captcha API v2:** `ImageToTextTask`, `numeric: 0`, `minLength: 4`, `maxLength: 4`
- **Tasa de fallo observada:** ~65% (554 fails vs 334 exitos)

## Formulario de Busqueda por Codigo

POST a `busquedacodform.html` con 7 campos:

| Campo | Ejemplo | Descripcion |
|---|---|---|
| cod_expediente | 00001 | Numero de expediente |
| cod_anio | 2020 | Anio |
| cod_incidente | 0 | Incidente |
| cod_distprov | 0401 | Codigo distrito/provincia |
| cod_organo | JP | Organo (JP/JR) |
| cod_especialidad | CI | Especialidad (CI/PE/LA/FC) |
| cod_instancia | 01 | Instancia (01/02) |

GET a `busquedacodform.html` devuelve HTTP 405 (POST-only). El formulario existe en el HTML de `busquedaform.html` bajo tab `#tabs-2`.

## Vulnerabilidades Encontradas (Wapiti Scan)

| Tipo | Severidad | Hallazgo |
|---|---|---|
| Backup files | LOW | Falsos positivos (288). Backups como `/backup.tgz` devuelven 403 (Radware bloquea) |
| CSRF | MEDIUM | 1 formulario sin proteccion CSRF valida. Meta tag `_csrf` con contenido vacio |
| CSP | INFO | No configurada |
| X-Frame-Options | INFO | No configurada (posible clickjacking) |
| HSTS | INFO | No configurada |
| X-Content-Type-Options | INFO | No configurada |

## Recomendacion de Proxies

| Volumen | Recomendacion | Costo |
|---|---|---|
| Pruebas/UV | rebrowser-playwright sin proxy | $0 |
| Medio | DataImpulse ($1/GB) | ~$50/mes |
| Alto/Peru | Decodo o Byteful con IPs Peru | ~$150-300/mes |
| Produccion | Bright Data u Oxylabs (premium) | ~$500+/mes |
