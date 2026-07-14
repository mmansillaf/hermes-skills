# Plan: [Nombre de la Feature]

## Arquitectura General

```
[Cliente] ──> [Frontend/Shiny/HTML] ──> [Backend/FastAPI :8000] ──> [BD/SQLite/PG]
                               │
                               └──> [Servicios Externos / APIs / IA]
```

## Data Model

### Tabla: [nombre]
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID | PK |
| [campo] | [tipo] | [notas] |

## API Contracts

```
POST   /api/v1/[recurso]       # [descripción — pública o auth]
GET    /api/v1/[recurso]       # [descripción — filtros]
PUT    /api/v1/[recurso]/{id}  # [descripción]
DELETE /api/v1/[recurso]/{id}  # [descripción]
```

## Librerías y Justificación

| Librería | Propósito | Alternativa descartada |
|----------|-----------|------------------------|
| [lib] | [uso] | [alt — por qué no] |

## Constitucion Check

- [ ] Lenguaje y framework según constitution
- [ ] Sin dependencias externas obligatorias no autorizadas
- [ ] i18n desde el inicio
- [ ] Multi-tenant / seguridad
- [ ] Auth implementado
- [ ] OWASP ASI checklist aplicado

## Opciones de Hosting

| Opción | Costo/mes | Ideal si... |
|--------|-----------|-------------|
| VPS (DigitalOcean, Hetzner) | ~$4-12 | Control total, multi-proyecto |
| Railway / Fly.io | ~$5-20 | Deploy rápido, serverless |
| On-premise (Raspberry Pi / mini PC) | ~$0 (electricidad) | Datos sensibles, sin internet |

---

## Factores Críticos de Éxito (Lo que DEBE suceder)

*Listar condiciones verificables que garantizan el éxito del proyecto.*

- **[acción concreta]** — [por qué es crítico]
- **[tecnología/patrón específico]** — [por qué sin esto fracasa]

*Ejemplos:*
- Stack 100% Python — sin Node.js, Ruby, Kafka ni servicios exóticos
- WhatsApp via API oficial — Twilio o 360dialog, jamás soluciones no-oficiales
- Auth desde el inicio — JWT desde la primera línea de código
- Código único automático por lead — trazabilidad desde el día 1
- Previews HTML antes de implementar — aprobación visual del usuario

## Anti-patrones y Errores a Evitar (Lo que NO debe suceder)

- **NO [práctica peligrosa]** — [consecuencia concreta]
- **NO [tecnología inadecuada]** — [consecuencia concreta]
- **NO [omisión de seguridad]** — [consecuencia concreta]

*Ejemplos:*
- NO usar soluciones no-oficiales de WhatsApp (Evolution API, Baileys) — riesgo de baneo
- NO usar Streamlit para producción con DB — rerun total degrada rendimiento
- NO implementar microservicios sin necesidad real — para 2-5 usuarios es sobreingeniería
- NO almacenar credenciales en el código — usar .env desde el principio
- NO hacer deploy sin HTTPS — datos personales viajan en claro
- NO saltarse los HTML previews — el retrabajo arquitectónico cuesta 10x más que una preview
