# SDD: Referencia de Herramientas y Notación EARS

## Herramientas SDD Populares (GitHub, Junio 2026)

| Herramienta | Tipo | Multi-Agent | Ideal para |
|-------------|------|-------------|------------|
| **GitHub Spec Kit** | Open-source CLI | Si (model-agnostico) | **Referencia estandar** |
| **AWS Kiro** | IDE agéntico | No (IDE) | AWS-native / serverless |
| **Claude Code (cc-sdd)** | Slash cmds nativos | Si | Trabajo CLI, `/sdd:specify` |
| **Cursor (Plan Mode)** | IDE + MCP | Si | Equipos que priorizan UX |
| **OpenSpec** | Markdown+YAML | Si | Indie devs, tooling minimo |
| **Tessl** | Compliance platform | Si | Fintech, healthtech |
| **Google Antigravity** | Agent-first | Si | Autonomia con restriccion |
| Autospec | YAML + Go CLI | Si | Alternativa ligera |
| GSD | Meta-prompting | Si | Workflow flexible |
| Spec Workflow MCP | MCP server | Si | Integracion MCP |

## Los 3 Niveles de SDD (consenso industria, Julio 2026)

1. **Spec-first**: Spec se escribe, genera codigo, se descarta. Prototipos.
2. **Spec-anchored (recomendado) 🎯**: Spec + tests enforzan alineacion. Sweet spot produccion.
3. **Spec-as-source**: Solo se edita la spec. Codigo 100% regenerado. Aspiracional.

## OWASP ASI 2026 — Referencia Rapida para SDD

Top 10 completo: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

Riesgos mas relevantes para SDD tipico:
| Riesgo | Descripcion | Mitigacion |
|--------|-------------|------------|
| ASI01: Goal Hijack | Manipulacion del objetivo agente | Inputs externos = no confiables |
| ASI05: RCE | Codigo generado sin validacion | Sandbox + no eval() |
| ASI06: Memory Poisoning | Memoria envenenada entre sesiones | Datos por tenant, expirar |
| ASI08: Cascading Failures | Fallos que propagan | Circuit breakers |
| ASI10: Rogue Agents | Agentes fuera de control | Monitoreo de drift |

## Notación EARS — 5 Patrones

Usar SIEMPRE para acceptance criteria en spec.md:

### 1. Ubiquitous (siempre verdadero)
`THE system SHALL [comportamiento permanente].`
- "THE system SHALL log every authentication attempt."
- "EL sistema DEBE cifrar datos personales en reposo."

### 2. Event-driven (WHEN + trigger)
`WHEN [evento] THE system SHALL [respuesta].`
- "WHEN a user submits the login form THE system SHALL validate credentials."
- "WHEN el cliente envia el formulario THEN el sistema DEBE asignar un codigo unico."

### 3. State-driven (WHILE + estado)
`WHILE [estado] THE [sistema] SHALL [comportamiento].`
- "WHILE a sync is in progress THE system SHALL display a progress indicator."
- "WHILE no hay resultados THEN el sistema DEBE mostrar mensaje de no encontrado."

### 4. Unwanted behavior (IF + condicion)
`IF [condicion adversa] THEN THE system SHALL [respuesta].`
- "IF credential validation fails 3 times in 60s THEN the system SHALL lock the account."
- "IF PDF corrupto THEN el sistema DEBE saltarlo y reportarlo."

### 5. Optional features (WHERE + condicion)
`WHERE [feature activa] THE system SHALL [comportamiento].`
- "WHERE multi-factor auth is enabled THE system SHALL require TOTP after password."
- "WHERE modo estricto THEN el sistema DEBE validar formato de expediente."

## Recursos Adicionales

- GitHub Spec Kit docs: https://github.com/github/spec-kit
- Autospec docs: https://ariel-frischer.github.io/autospec/
- Martin Fowler SDD analysis: https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- The BCMS SDD Guide (2026): https://thebcms.com/blog/spec-driven-development
- Addy Osmani — How to write a good spec for AI agents: https://addyosmani.com/blog/good-spec
