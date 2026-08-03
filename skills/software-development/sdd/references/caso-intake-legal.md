# Caso SDD: Intake de Clientes para Abogados

Ejemplo real de SDD ejecutado para un estudio legal con 2-3 abogados.

## Contexto

Sistema de captura de datos de clientes (intake) para abogados. El cliente llena un formulario web unico, adjunta hasta 3 documentos, y puede hacer seguimiento via web.

## Flujo de Diseno

```
1. Usuario pide "disena un SDD para intake de abogados"
2. AGENTE genera: constitution + spec + plan + tasks COMPLETOS
3. AGENTE muestra el plan completo primero
4. AGENTE hace preguntas de clarificacion
5. Usuario responde preguntas
6. AGENTE ajusta los artefactos con las respuestas
```

**REGLA IMPORTANTE:** El usuario quiere ver el plan PRIMERO, antes de responder preguntas. No preguntes detalles antes de mostrar el diseno completo.

## Constitution (ejemplo)

Lenguaje: Python 3.12+ / FastAPI / React + Tailwind
BD: PostgreSQL
Auth: JWT con refresh tokens
Infra: VPS + Docker
Multi-tenant por abogado
i18n ES/EN desde el dia 1

## Spec (resumen)

Feature: Intake de Clientes para Abogados

User Stories:
- Como cliente, quiero llenar un formulario simple con mis datos
- Como cliente, quiero adjuntar hasta 3 documentos
- Como cliente, quiero recibir un codigo de caso y hacer seguimiento
- Como abogado, quiero ver los intakes recibidos y registrar llamadas

EARS Criteria:
- WHEN un cliente envia el formulario THEN el sistema DEBE asignar codigo LEGAL-YYYY-NNNN
- WHEN el abogado registra una llamada THEN el sistema DEBE guardarla en el timeline
- WHEN un abogado ve sus casos THEN el sistema DEBE mostrar SOLO los suyos
- THE system DEBE cifrar datos personales en reposo

## Data Model

Tablas: lawyer, client, case (LEGAL-YYYY-NNNN), case_document, case_log

## API

POST /api/v1/intake — formulario publico
POST /api/v1/auth/login — login
GET /api/v1/lawyer/cases — casos del abogado
POST /api/v1/lawyer/cases/{id}/calls — registrar llamada
GET /api/v1/client/cases — caso del cliente

## MVP (5 sprints, 9-14 dias)

Sprint 1: Fundacion (Docker, modelos, auth)
Sprint 2: Formulario Intake (publico, upload)
Sprint 3: Dashboard Abogado (multi-tenant, llamadas)
Sprint 4: Dashboard Cliente (timeline)
Sprint 5: Despliegue (tests, Docker, hosting)

## Preguntas de Diseno (las que se hicieron)

1. Quien usa el intake? → Formulario que llena el cliente
2. Hay multiples abogados? → Si, 2-3 fijos
3. Cliente puede ver su caso? → Si, incluyendo registro de llamadas
4. Datos basicos? → Nombres, DNI, direccion, telefono, email
5. Documentos adjuntos? → Hasta 3 (PDF, JPG, PNG), max 10MB
6. Login? → Si, email + password
7. Codigo interno? → LEGAL-YYYY-NNNN
8. Integracion con KGraph? → Opcional, post-MVP
9. Idiomas? → Espanol e ingles
10. Hosting? → VPS recomendado por control
