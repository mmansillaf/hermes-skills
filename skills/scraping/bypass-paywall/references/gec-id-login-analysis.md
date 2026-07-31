# GEC SSO (id.gec.pe) — Análisis Técnico (Junio 2026)

## Sitio

`https://id.gec.pe/elcomercio/login?redirect_uri=https%3A%2F%2Felcomercio.pe%2F&ref=button_header`

## Arquitectura

| Componente | Detalle |
|------------|---------|
| **Propósito** | SSO centralizado para Grupo El Comercio (Gestión, El Comercio, PerúQuiosco, Club El Comercio) |
| **Método** | POST a `id.gec.pe/elcomercio/login` con `username` + `password` |
| **Formulario** | Campos: `username` (email), `password` (password); action: GET redirect con redirect_uri |
| **OAuth** | Google (botón "Iniciar con Google") |
| **Protección** | reCAPTCHA (iframe detectado en la página) |
| **Estado del cliente** | Sin datos sensibles en localStorage ni sessionStorage |
| **Cookies** | Solo `_ga`, `_ga_WKWY3DEGYS` (Google Analytics) |
| **Scripts** | 6 scripts cargados — liviano, SPA mínimo |

## Tipo de Barrera

**Hard login wall server-side.** El servidor de GEC gestiona la autenticación centralizada. No es como los paywalls donde el contenido está oculto en el HTML — aquí sin sesión válida no hay contenido.

El reCAPTCHA impide automatización directa con Selenium/Playwright sin servicios de resolución.

## Técnicas Aplicables

| Técnica | Aplicable | Explicación |
|---------|-----------|-------------|
| Googlebot UA spoofing | ❌ | No es paywall, no hay JSON-LD con articleBody |
| DevTools (eliminar overlay) | ❌ | No hay overlay client-side, es autenticación server-side |
| Google Cache | ⚠️ Parcial | Solo si el contenido fue público antes del muro |
| **Google OAuth** | ✅ | El botón "Iniciar con Google" usa OAuth estándar — si tienes cuenta Google, es el camino más directo |
| **Temp mail + registro** | ✅ | Si GEC permite crear cuenta gratuita con solo email (sin SMS), se puede automatizar |
| **Session cookie reuse** | ✅ | Una vez logueado, exportar cookies para reutilizar desde curl/scripts |
| 2captcha + Playwright | ✅ | Si se necesita automatizar login, reCAPTCHA requiere 2captcha |

## Flujo Recomendado

1. **Probar Google OAuth** primero — es el método más simple si ya tienes cuenta Google
2. **Si no hay cuenta Google**: intentar registro manual con temp mail (mail.tm o 10minutemail)
3. **Si el registro es exitoso**: guardar cookies con Playwright `storage_state` para reuso
4. **Automatización completa** (si es necesario): mail.tm → Playwright → 2captcha → login → cookie persistence

## Nota sobre el reCAPTCHA

El reCAPTCHA de Google es detectable en el DOM como un iframe. Servicios como 2captcha (~$0.50/1000 solves) pueden resolverlo. La alternativa es usar el flujo OAuth de Google que no requiere captcha.

## Sitios que comparten este SSO

- gestion.pe
- elcomercio.pe
- depor.com
- trome.com
- peruquiosco.pe
- clubelcomercio.pe
