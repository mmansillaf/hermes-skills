# Caso SDD: Intake CRM (Shiny + FastAPI + IA)

*Segundo caso real de SDD. Diferencia clave respecto a `caso-intake-legal.md`: stack 100% Python (sin React), dashboard con Shiny for Python, agente IA con Groq, formulario web + WhatsApp.*

## Contexto

Sistema de captura de prospectos (intake) para estudio legal. El prospecto llena un formulario web o escribe por WhatsApp → IA extrae datos y califica → lead se crea en CRM → abogado gestiona pipeline desde dashboard Shiny.

Stack: Python 3.12, FastAPI, Shiny for Python, SQLite/PostgreSQL, SQLAlchemy, JWT, Groq (Llama 3.1 8B), Twilio WhatsApp API.

Infraestructura modesta: on-premise o VPS $4-7/mes. Sin Node.js, sin Ruby, sin Kafka, sin soluciones no-oficiales de WhatsApp.

## Constitution

Ver archivo completo en `.specify/memory/constitution.md` del proyecto IntakeCRM_IA. Puntos clave:
- Python puro (FastAPI + Shiny) — sin React, sin Node, sin Ruby
- WhatsApp via API oficial (Twilio/360dialog) — jamas Baileys/Evolution API
- Reactividad selectiva de Shiny — sin rerun total como Streamlit
- JWT auth desde el inicio
- Codigo automatico CRM-YYYY-NNNN
- Timeline de actividades para cada lead

## Spec (resumen)

Feature: Intake CRM

User Stories (10):
- Prospecto envia formulario web → lead creado con codigo
- Prospecto escribe por WhatsApp → IA extrae datos → lead creado
- Abogado ve pipeline con filtros por estado/origen/busqueda
- Abogado cambia estado y agrega notas/llamadas
- Abogado recibe notificacion WhatsApp si score >= 70

EARS Criteria (18): ver spec.md completo. Ejemplos:
- WHEN prospecto llena formulario THEN sistema SHALL crear lead con codigo CRM-YYYY-NNNN
- WHEN prospecto envia WhatsApp THEN sistema SHALL procesar con IA y crear lead calificado
- IF lead duplicado THEN sistema SHALL mostrar advertencia
- THE sistema SHALL cifrar datos personales en reposo

## Data Model

3 tablas:
- `leads`: id, codigo (CRM-YYYY-NNNN), nombre, email, telefono, origen (web|whatsapp), estado, profesion, tipo_consulta, mensaje, score_ia, notas, datos_extra, created_at, updated_at
- `lead_logs`: id, lead_id (FK), accion, descripcion, usuario, created_at
- `users`: id, username, password_hash, nombre, email, telefono, created_at

## API (12 endpoints)

```
POST   /api/v1/auth/register       — Registrar abogado
POST   /api/v1/auth/login          — Login → JWT
POST   /api/v1/auth/refresh        — Refrescar token
GET    /api/v1/intake              — Servir formulario HTML
POST   /api/v1/intake              — Recibir formulario (publico)
POST   /api/v1/webhook/whatsapp    — Webhook Twilio (publico)
GET    /api/v1/leads               — Listar (filtros: estado, origen, busqueda)
GET    /api/v1/leads/stats         — Conteo por estado
GET    /api/v1/leads/{id}          — Detalle + timeline
POST   /api/v1/leads               — Crear lead (publico)
PUT    /api/v1/leads/{id}          — Actualizar (auth)
POST   /api/v1/leads/{id}/logs     — Agregar nota/llamada (auth)
```

## Arquitectura

```
[Formulario Web] + [WhatsApp → IA Agent] → [FastAPI :8000] → [SQLite/PG]
                                                   |
                                          [Shiny Dashboard :8501]
```

3 procesos separados: API (uvicorn), Dashboard (shiny run), IA Agent (integrado en API via Groq).

## Agente IA (Groq Llama 3.1 8B)

Dos llamadas a Groq por mensaje:
1. **Extraccion**: prompt estructurado que pide JSON con nombre, profesion, tipo_consulta, urgencia, presupuesto, resumen
2. **Score**: prompt que evalua calidad del lead (0-100) basado en especificidad, urgencia, presupuesto

Sin Groq configurado: el lead se crea igual pero con score None y nombre generico.

## Previews UI (antes de implementar)

Se generaron 6 HTML autocontenidos para aprobacion del usuario:
1. Login
2. Pipeline de leads (tabla + filtros + stats)
3. Detalle de lead (info + timeline + acciones)
4. Formulario web publico
5. Confirmacion de envio
6. Configuracion de notificaciones

Cada preview tiene datos ficticios (8 leads) y CSS embebido. El usuario los abrio en navegador y aprobo antes de implementar.

## Implementacion

### Sprint 1: Backend API (2 dias)
- `uv init --app --name intake-crm --python 3.12`
- Dependencias: fastapi, uvicorn, sqlalchemy, pydantic, pyjwt, bcrypt, httpx, python-dotenv, twilio, pytest, ruff
- Modelos: Lead, LeadLog, User (SQLAlchemy)
- Esquemas: LeadCreate, LeadUpdate, LeadResponse, LeadLogCreate, LeadLogResponse, LoginRequest, TokenResponse, StatsResponse (Pydantic v2)
- Auth: JWT con access (24h) y refresh (7d), bcrypt, middleware HTTPBearer
- CRUD leads con generacion automatica de codigo CRM-YYYY-NNNN
- Logging automatico de toda accion en timeline
- 8 leads de prueba insertados

### Sprint 2: Dashboard Shiny (2 dias)
- Shiny 1.6.3 (API: `ui.nav_panel()` dentro de `ui.page_navbar()`)
- Login modal con JWT
- Pipeline con tabla grid, 6 tarjetas de stats, filtros (estado, origen, busqueda)
- Detalle de lead con info + mensaje original + timeline + acciones (cambiar estado, agregar nota)
- Pestaña de configuracion con preview de notificaciones

### Sprint 3: Formulario + WhatsApp + IA (1 dia)
- Formulario web HTML embebido en FastAPI (GET /api/v1/intake)
- Validacion client-side con JS, confirmacion con codigo
- Webhook Twilio (POST /api/v1/webhook/whatsapp, form-data)
- Agente IA en `app/services/ia_agent.py` con extraccion + scoring via Groq
- Notificacion WhatsApp al abogado si score >= 70

### Shiny API Notes (Shiny 1.6.3)
- `ui.nav()` → `ui.nav_panel(title, content)`
- `ui.page_navbar(*panels, title=, id=)` en lugar de `ui.nav()` anidado
- `ui.update_navs("navbar", selected="Detalle")` para navegacion programatica
- `ui.HTML(html_string)` para HTML plano con CSS inline
- Las referencias a modulos de Shiny (`ui.nav`, `ui.page_navbar`) no son detectadas por Pyright — ignorar warnings de tipo
- Los `reactive.Value` tipados dan falsos positivos con Pyright — ignorar

## Lecciones Aprendidas

1. **Previews HTML primero** — el usuario aprobo el diseno visual antes de codificar. Evito retrabajo.
2. **WhatsApp via Twilio sandbox** — permite probar el flujo completo sin WABA aprobada ni numero real.
3. **Sin Groq, el sistema funciona** — el agente IA es un componente adicional, no critico. El intake web y el dashboard operan sin IA.
4. **Shiny reactive.Value vs API calls** — la reactividad de Shiny combinada con llamadas HTTP a la API requiere manejar estados intermedios (loading, error) explicitamente.
5. **Codigo auto-generado** — la generacion de CRM-YYYY-NNNN parece trivial pero es critica para trazabilidad. Implementarla desde el sprint 1 evita migraciones dolorosas.
