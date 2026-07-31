# HeyGen API — Investigación Completa (Jul 2026)

Fuentes consultadas:
- https://developers.heygen.com/ — Documentación oficial
- https://developers.heygen.com/reference — API Reference
- https://www.heygen.com/api-pricing — Precios API
- https://www.heygen.com/pricing — Precios web

---

## Planes Web (con créditos)

| Plan | Precio | Créditos | Video máx | Resolución | Velocidad |
|------|--------|----------|-----------|------------|-----------|
| **Free** | $0/mes | 3 videos/mes | 1 min | Standard | Standard |
| **Creator** | $29/mes | 600 créditos | 30 min | 1080p | Fast |
| **Pro** | $49/mes | 1,000 créditos | 30 min | 4K | Faster |

## API Pay-As-You-Go (desde $5)

El saldo API es **separado** del plan web. Se recarga con dinero real.

## Endpoints Detallados

### Base URL: `https://api.heygen.com/v3/`

| Categoría | Endpoints | Descripción |
|-----------|-----------|-------------|
| **Video Agent** | `POST /video-agents` | Crear sesión y generar video desde prompt (one-shot) |
| | `GET /video-agents` | Listar sesiones |
| | `GET /video-agents/{id}` | Obtener sesión |
| | `POST /video-agents/{id}/message` | Enviar mensaje o pedir revisión |
| | `POST /video-agents/{id}/stop` | Detener sesión |
| **Videos** | `POST /videos` | Crear video con avatar (control granular) |
| | `GET /videos` | Listar videos |
| | `GET /videos/{id}` | Obtener estado/URL del video |
| | `DEL /videos/{id}` | Eliminar video |
| **Avatars** | `GET /avatars` | Listar avatares |
| | `POST /avatars` | Crear avatar personalizado |
| | `POST /avatars/consent` | Consentimiento para avatar |
| **Avatar Realtime** | `POST /avatar-realtime` | Sesión de avatar en streaming |
| **Voices** | `POST /voices/generate-speech` | Texto a voz (Starfish) |
| | `GET /voices` | Listar voces |
| | `POST /voices/clone` | Clonar voz |
| **Templates** | `GET /templates` | Listar plantillas |
| | `POST /templates/{id}/generate` | Generar video desde plantilla |
| **Video Translate** | `POST /video-translations` | Crear traducción |
| | `POST /proofread` | Sesión de revisión de traducción |
| **Lipsync** | `POST /lipsyncs` | Re-sincronizar labios con audio |
| **HyperFrames** | `POST /hyperframes/renders` | Render avanzado |
| **Webhooks** | `POST /webhooks` | Configurar webhook endpoints |
| | `GET /webhooks/events` | Listar tipos de eventos |
| **User** | `GET /user` | Info del usuario |
| **Brand** | `GET /brand-kits` | Kits de marca |
| | `GET /brand-glossaries` | Glosarios de marca |
| **Assets** | `POST /assets` | Subir multimedia |

## Casos de Uso LegalTech Peruano

| Caso | Descripción | Costo estimado/mes |
|------|-------------|-------------------|
| **Bienvenida personalizada** | Cada cliente recibe video de su abogado explicando el caso | $2-4/video |
| **Explicaciones legales** | Videos educativos sobre procesos (divorcio, herencia, laboral) | $2-4/video |
| **Testimonios** | Avatares narrando casos de éxito | $4/video |
| **Newsletters en video** | Resúmenes semanales de novedades legales | $2/video, 4-8/mes |
| **Landing page video** | Video institucional de 60-90s | $4-6/video único |

### Multi-idioma

| Idioma | Costo adicional |
|--------|----------------|
| Español (Perú) | Incluido |
| Inglés | $2-4/video |
| Portugués | $2-4/video |

### Limitaciones para el contexto peruano

1. Avatares stock predominantemente caucásicos/asiáticos — pocos latinos
2. Digital Twin Creation solo en Enterprise (contactar ventas)
3. Photo Avatar (desde foto) sí disponible en planes de pago
4. Español latinoamericano soportado en 175+ idiomas

## Reviews Públicas

- **G2**: Reconocido #1 Fastest Growing Product of 2025
- Usuarios: 1M+ developers, 100K+ businesses
- Clientes: Google, HubSpot, Deloitte, Duolingo, Zoom, J.P. Morgan, Intel
- 153M+ videos generados
- SOC 2 Type II y GDPR compliant
