# Plan: [Nombre de la Feature]

## Arquitectura General

```
[Cliente] ──> [Frontend] ──> [Backend] ──> [Base de Datos]
                              │
                              └──> [Servicios Externos]
```

## Data Model

### Tabla: [nombre]
| Campo | Tipo | Notas |
|-------|------|-------|
| id | UUID | PK |
| [campo] | [tipo] | [notas] |

## API Contracts

```
POST   /api/v1/[recurso]      # [descripcion]
GET    /api/v1/[recurso]      # [descripcion]
```

## Librerias y Justificacion

| Libreria | Proposito | Alternativa |
|----------|-----------|-------------|
| [lib] | [uso] | [alt] |

## Constitucion Check

- [ ] Lenguaje y framework segun constitucion
- [ ] Sin dependencias externas obligatorias no autorizadas
- [ ] i18n desde el inicio
- [ ] Multi-tenant / seguridad

## Opciones de Hosting

| Opcion | Costo/mes | Ideal si... |
|--------|-----------|-------------|
| [opcion] | ~$X | [caso de uso] |

---

## Factores Criticos de Exito (Lo que DEBE suceder)

*Listar las condiciones que garantizan el exito del proyecto. Cada item debe ser verificable. Preferir acciones concretas sobre principios abstractos.*

- **[accion concreta]** — [por que es critico]
- **[accion concreta]** — [por que es critico]
- **[tecnologia/patron especifico]** — [por que sin esto fracasa]

*Ejemplos:*
- *Stack 100% Python — sin Node.js, Ruby, Kafka ni servicios exoticos*
- *WhatsApp via API oficial — Twilio o 360dialog, jamas soluciones no-oficiales (Evolution API/Baileys)*
- *Auth desde el inicio — JWT desde la primera linea de codigo del dashboard*
- *Formulario web primero — debe estar funcional antes que canales secundarios (WhatsApp, email)*
- *Codigo unico automatico por lead — para trazabilidad desde el dia 1*

## Anti-patrones y Errores a Evitar (Lo que NO debe suceder)

*Listar practicas, tecnologias o decisiones que tipicamente causan fracaso en este tipo de proyecto. Cada item debe responder a un riesgo real, no teorico.*

- **NO [practica peligrosa]** — [consecuencia concreta]
- **NO [tecnologia inadecuada]** — [consecuencia concreta]
- **NO [decision arquitectonica erronea]** — [consecuencia concreta]
- **NO [omision de seguridad]** — [consecuencia concreta]

*Ejemplos:*
- *NO usar soluciones no-oficiales de WhatsApp (Evolution API, Baileys, whatsapp-web.js) — riesgo de baneo del numero comercial*
- *NO usar Streamlit para produccion con DB — el rerun total degrada rendimiento al consultar DB en cada interaccion*
- *NO implementar microservicios sin necesidad real — para 2-5 usuarios es sobreingenieria pura*
- *NO almacenar credenciales en el codigo — usar .env desde el principio*
- *NO hacer deploy sin HTTPS — datos personales viajan en claro*
- *NO ignorar la validacion de datos de entrada — errores de validacion = leads perdidos*