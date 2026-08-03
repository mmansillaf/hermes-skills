# SDD: Referencia de Herramientas y Notación EARS

## Herramientas SDD Populares (GitHub, Junio 2026)

| Herramienta | Repo | Formato | Multi-Agent | Dashboard | Costo |
|-------------|------|---------|-------------|-----------|-------|
| Spec Kit | github/spec-kit | Markdown | Si (CLI + slash cmds) | No | Gratis |
| Autospec | ariel-frischer/autospec | YAML | Si (Go CLI) | No | Gratis |
| GSD | gsd-build/get-shit-done | Markdown | Si (meta-prompting) | Si (externo) | Gratis |
| Spec Workflow MCP | Pimzino/spec-workflow-mcp | JSON/MD | Si (MCP server) | Si (web) | Gratis |
| Kiro (AWS) | — | Markdown | No (IDE) | Si | Gratis |
| OpenSpec | Fission-AI/OpenSpec | MD+YAML | Si | No | Gratis |

## Los 3 Niveles de SDD (Martin Fowler)

1. **Spec-first**: Spec se escribe, genera codigo, se descarta. Util para tareas individuales.
2. **Spec-anchored**: Spec se mantiene y evoluciona con el codigo. Actualizar spec antes que codigo.
3. **Spec-as-source**: Solo se edita la spec. El codigo se regenera automaticamente.

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
