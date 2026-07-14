---
name: sdd
description: Spec-Driven Development workflow for Hermes Agent.
triggers:
  - User asks to create a spec
  - sdd:specify
  - sdd:plan
version: 1.1.0
---

# SDD - Spec-Driven Development para Hermes Agent

Ejecuta el flujo completo SDD: Constitution, Specify, Clarify, Plan, Tasks, Implement.

## Orden de entrega (CRITICO)

**REGLA: El plan se muestra completo PRIMERO.** Cuando el usuario pide disenar
algo, genera los 4 artefactos (constitution + spec + plan + tasks) COMPLETOS
antes de hacer preguntas de clarificacion. El usuario quiere ver el artefacto
primero y luego respondera preguntas. NO preguntes detalles antes de mostrar
el plan completo.

Flujo correcto:
  1. Preguntas de diseno (si el usuario no las ha respondido ya)
  2. Generar constitution.md
  3. Generar spec.md con EARS
  4. Generar plan.md con arquitectura y data model
  5. Generar tasks.md con sprints
  6. **Generar HTML previews de la UI** (opcional pero recomendado) — crea paginas HTML autocontenidas con CSS y datos de ejemplo para mostrar el diseno visual al usuario antes de implementar. Cada preview es un archivo .html independiente que el usuario abre en su navegador. Incluye datos ficticios pero realistas para que se aprecie el flujo completo.
  7. MOSTRAR TODO al usuario (artefactos + previews)
  8. HACER preguntas de clarificacion
  9. Ajustar segun respuestas

**Cuando generar HTML previews:** cuando el proyecto tiene interfaz de usuario significativa (dashboards, formularios, paneles de administracion). No aplica para APIs puras, scripts o librerias.

## Estructura

Cada feature crea:
  specs/NNN-nombre-feature/
    spec.md       - Especificacion funcional
    plan.md        - Plan tecnico (arquitectura, data model, hosting)
    tasks.md       - Desglose de tareas con sprints

La constitucion del proyecto va en .specify/memory/constitution.md

## Archivos del Skill

### Referencias
- `references/caso-intake-legal.md` — caso real completo (preguntas, data model, API) con React+Tailwind
- `references/caso-intake-crm-shiny.md` — caso real de Intake CRM con Shiny+FastAPI+IA (stack 100% Python, sin Node.js). Incluye: constitution, spec, plan, data model, API, agente IA Groq, previews UI, lecciones aprendidas y notas sobre API de Shiny 1.6.3
- `references/herramientas-sdd.md` — herramientas populares, notacion EARS, y OWASP ASI 2026
- `references/owasp-asi-2026.md` — Top 10 de seguridad para agentes autonomos (checklist por riesgo)
- `references/frameworks-dashboard-comparativa.md` — comparativa de 7 frameworks Python para dashboards
- `references/whatsapp-integracion-bsp.md` — estrategia de integracion WhatsApp Business API para CRM

### Templates
- `templates/spec-template.md` — template para spec.md
- `templates/plan-template.md` — template para plan.md (incluye secciones de Factores de Exito y Anti-patrones)
- `templates/tasks-template.md` — template para tasks.md

Usa los templates como base y los casos de referencia como inspiracion.

### Nota sobre el plan-template
El template `plan-template.md` incluye dos secciones adicionales respecto a versiones anteriores:
- **Factores Criticos de Exito** — lista de condiciones verificables que garantizan exito
- **Anti-patrones y Errores a Evitar** — practicas y tecnologias que tipicamente causan fracaso
Estas secciones responden al formato "lo que DEBE suceder / lo que NO debe suceder". Usarlas siempre en proyectos donde el usuario pidio explicitamente factores de riesgo y exito.

## Comandos

### sdd:constitution
Crea la constitucion del proyecto. Pregunta al usuario sobre lenguaje, framework, convenciones de codigo, estandares de testing y restricciones de arquitectura. Guarda en .specify/memory/constitution.md

### sdd:specify "descripcion"
Genera spec.md con User Stories, Acceptance Criteria en notacion EARS, Out of scope y Non-functional requirements.

### sdd:clarify
Revisa la spec y pregunta sobre ambiguedades. Actualiza spec.md.

### sdd:plan "tech stack (opcional)"
Genera plan.md con Architecture, Data model, API contracts, Librerias y Constitucion check.

### sdd:tasks
Desglosa plan.md en tareas atomicas en tasks.md con prioridad, dependencias y verificacion.

### sdd:implement
Ejecuta las tareas de tasks.md en orden. Cada tarea produce un commit.

### sdd:checklist
Genera checklist de calidad: seguridad, tests, rendimiento, logging.

### sdd:status
Muestra progreso del feature actual.

## Reglas EARS

Usar estos 5 patrones para acceptance criteria. Ver referencia completa en `references/herramientas-sdd.md` y ejemplo real en `references/caso-intake-legal.md`.

1. Ubiquitous - "El sistema DEBE loguear todo intento de autenticacion"
2. Event-driven - "WHEN el procesamiento falla THEN el sistema DEBE registrar el error"
3. State-driven - "WHILE no hay resultados THEN el sistema DEBE mostrar mensaje"
4. Unwanted - "IF PDF corrupto THEN el sistema DEBE saltarlo y reportarlo"
5. Optional - "WHERE modo estricto THEN el sistema DEBE validar formato de expediente"

## Ejemplo

  sdd:constitution
  sdd:specify "modulo de busqueda semantica para jurisprudencia"
  sdd:plan "Python, FAISS, FastAPI"
  sdd:tasks
  sdd:implement
  sdd:status

## Pitfalls Conocidos

### Shiny for Python: API cambia entre versiones
En Shiny 1.6+, `ui.nav()` fue reemplazado por `ui.nav_panel()`. Usar `ui.nav()` da `AttributeError`. La estructura correcta:
```python
ui.page_navbar(
    ui.nav_panel("Pipeline", ui.layout_sidebar(...)),
    ui.nav_panel("Detalle", ui.layout_sidebar(...)),
    title="App", id="navbar",
)
```
`ui.update_navs("navbar", selected="Detalle")` para navegacion programatica.
Usar `ui.HTML(html_string)` para contenido HTML plano con CSS inline.

### TestClient + SQLite in-memory
FastAPI TestClient con SQLite in-memory requiere crear las tablas a nivel de modulo (NO en fixture con `yield`), porque los fixtures se ejecutan en orden impredecible con respecto a `app.dependency_overrides`. Patron correcto:
```python
Base.metadata.create_all(bind=engine)  # modulo-level
# luego override y client
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)
@pytest.fixture(autouse=True)
def clean_db():
    for table in reversed(Base.metadata.sorted_tables):
        with engine.connect() as conn:
            conn.execute(text(f"DELETE FROM {table.name}"))
            conn.commit()
```
Si las tablas se crean en un fixture `autouse`, los endpoints que se ejecutan via `client` pueden recibir la sesion ANTES de que el fixture cree las tablas.

## SDD Maturity Model (Junio 2026)

Seleccionar el nivel según el proyecto:

| Nivel | Descripcion | Cuando usarlo |
|-------|-------------|---------------|
| **Spec-First** | Specs seed la generacion inicial, luego el codigo deriva | Prototipos, features exploratorias |
| **Spec-Anchored** | Specs + tests enforzan alineacion continua | **Sweet spot para produccion (recomendado)** |
| **Spec-as-Source** | Humanos editan SOLO la spec, codigo 100% generado | Equipos maduros con tooling confiable |

Por defecto apuntar a **Spec-Anchored**. Preguntar si el usuario quiere otro nivel.

## Routing de Modelos por Fase SDD

Usar el modelo adecuado segun la fase para optimizar costo y calidad:

| Fase SDD | Modelo recomendado | Por que |
|----------|-------------------|---------|
| Constitution | Cualquiera (rapido) | Lista corta de reglas |
| Spec + EARS | DeepSeek Reasoner o Gemini | Precision en logica de requisitos |
| Plan | DeepSeek Reasoner | Arquitectura, trade-offs |
| Tasks | DeepSeek Flash o Gemini Flash | Desglose mecanico |
| Implement | DeepSeek Flash | Velocidad para codigo repetitivo |
| Code Review | Gemini (contexto masivo) | Revision de diff grande |

Si el modelo actual no soporta alguna fase, adaptar.

## OWASP ASI 2026 — Seguridad para Agentes Autonomos

El skill `hermes-sdd` (v2) integra el checklist completo. Para SDD basico,
considerar al menos estos riesgos. Ver referencia completa en:
`references/herramientas-sdd.md` (actualizado) o `hermes-sdd` skill.

| Riesgo | Descripcion | Mitigacion minima |
|--------|-------------|-------------------|
| ASI01: Goal Hijack | Manipulacion del objetivo del agente | Inputs externos = no confiables |
| ASI05: RCE | Ejecucion de codigo generado sin validacion | Sandbox + no eval() |
| ASI06: Memory Poisoning | Envenenamiento de memoria entre sesiones | Datos por tenant, expirar no verificados |

## Criticas y Debates sobre SDD

Cuando presentes SDD al usuario, es profesional mencionar que el paradigma
tiene voces escepticas en la comunidad:

- **"Same Patterns, New Hype" (Brandon Kindred, 2026)**: SDD es waterfall/contract-design rebautizado. El valor esta en pensar mientras escribes la spec, no en el tooling.
- **Thoughtworks Technology Radar**: SDD en "Assess", no "Adopt". El codigo ejecutable sigue siendo la fuente de verdad. "Specs alone suffice" es un riesgo.
- **Reddit r/AI_Agents**: "Spec-driven agentic coding is quietly making us worse at supervising agents" — la especulacion excesiva atrofia la habilidad humana de revisar codigo generado.
- **Debate video (Our Tech Journey, 3h)**: El problema mas duro no es escribir codigo, sino descubrir si estas construyendo lo correcto. Las specs perfectas no reemplazan feedback loops cortos.

**Como responder:** SDD no reemplaza la iteracion. Spec-Anchored (no Spec-as-Source) permite que specs y codigo evolucionen juntos. Los tests son el enforcement, no la spec sola.

## Notas

- No requiere herramientas externas
- Los archivos se guardan en specs/ en la raiz del proyecto
- Basado en GitHub Spec Kit, Autospec y EARS notation
- Para un flujo SDD mas completo con Hermes-native tooling (delegate_task, execute_code, MCP servers, HTML previews con script, OWASP ASI completo, y Script CLI interactivo), usar el skill `hermes-sdd` (v2.0.0). Este skill `sdd` es la version clasica; `hermes-sdd` es la evolucion con las practicas 2026 incorporadas.
