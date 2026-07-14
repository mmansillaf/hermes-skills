# Feature: [Nombre de la Feature]

## User Stories

- Como [rol], quiero [capacidad], para [beneficio].
- Como [rol], quiero [capacidad], para [beneficio].

## Acceptance Criteria (EARS)

<!-- Usar los 5 patrones EARS: Ubiquitous, Event-driven, State-driven, Unwanted, Optional -->

- WHEN [trigger] THEN [el sistema|the system] SHALL [respuesta].
- IF [condición adversa] THEN [el sistema|the system] SHALL [respuesta].
- WHILE [estado] THEN [el sistema|the system] SHALL [comportamiento].
- WHERE [feature opcional] THEN [el sistema|the system] SHALL [comportamiento].
- THE [sistema|system] SHALL [requisito permanente].

## Out of Scope (MVP)

- [Funcionalidad que NO se cubre en esta iteración]

## Non-Functional Requirements

- **Rendimiento:** [expectativas]
- **Seguridad:** [OWASP ASI relevante — ver security section abajo]
- **i18n:** [idiomas]
- **Disponibilidad:** [SLO esperado]

## Security Considerations (OWASP ASI 2026)

<!-- Elegir los riesgos relevantes según el tipo de proyecto.
     Mantener solo los que aplican, eliminar el resto. -->

### Alto Riesgo
- [ASI05: RCE] Código generado se ejecuta en sandbox Docker network:none
- [ASI06: Memory Poisoning] Memoria persistente aislada por tenant con expiración

### Medio Riesgo
- [ASI02: Tool Misuse] Tools con permisos mínimos y rate limiting
- [ASI03: Identity Abuse] JWT con scopes específicos por endpoint

### Monitoreo
- [ASI08: Cascading Failures] Circuit breaker: max N retries por tool call
- [ASI10: Rogue Agents] Log de objetivos del agente para detección de drift
