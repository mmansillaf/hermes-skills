---
name: hermes-sdd
description: "SDD workflow for Hermes Agent: constitution, spec (EARS), plan, tasks, implement with Hermes-native tooling (delegate_task, execute_code, patch). Generates HTML previews + MCP server scaffolding."
version: 2.0.0
author: Hermes Agent (synthesized from industry research Jun 2026)
license: MIT
platforms: [linux, macos, windows]
triggers:
  - User asks to create a spec or SDD
  - sdd:constitution
  - sdd:specify
  - sdd:plan
  - sdd:tasks
  - sdd:implement
metadata:
  hermes:
    tags: [sdd, agentic-engineering, planning, specification, ears, previews, mcp]
    related_skills: [sdd, writing-plans, test-driven-development, subagent-driven-development, plan]
---

# hermes-sdd — Spec-Driven Development con Hermes (2026 Edition)

## Overview

Ejecuta el flujo SDD completo con énfasis en **herramientas nativas de Hermes**:
`delegate_task` para paralelismo, `execute_code` para pipelines, `patch` para
cambios quirúrgicos, `write_file` para artefactos, y generación de MCP servers
cuando el proyecto lo amerite.

Basado en GitHub Spec Kit, OWASP ASI 2026, Karpathy Agentic Engineering,
y el ecosistema de herramientas SDD 2026.

## Diferencia clave respecto al skill `sdd` original

| Aspecto | sdd (original) | hermes-sdd (este skill) |
|---------|---------------|------------------------|
| Tooling | Genérico | Hermes-native (delegate_task, execute_code, MCP) |
| Madurez SDD | Spec-First | Spec-Anchored (sweet spot producción) |
| Seguridad | Prompt injection básico | OWASP ASI 2026 Top 10 |
| Testing | Mencionado | Record-Decisions-Not-HTTP + TDD |
| Previews | HTML opcional | HTML + MCP server scaffolding |
| Modelos | Mención genérica | Routing consciente (DeepSeek/Gemini/Kimi según tarea) |
| Token opt | Compresión genérica | Lazy tool loading, frozen memory, CACHE_BARRIER |
| Críticas | No cubre | Incluye debate SDD (Thoughtworks, Kindred, etc.) |

## Orden de entrega (crítico)

**REGLA: El plan se muestra completo PRIMERO.** Genera los 4 artefactos
(constitution + spec + plan + tasks) COMPLETOS antes de hacer preguntas de
clarificación. El usuario quiere ver el artefacto primero.

Flujo correcto:
  1. Preguntas de diseño (si el usuario no las ha respondido ya)
  2. Generar `constitution.md`
  3. Generar `spec.md` con EARS
  4. Generar `plan.md` con arquitectura, data model, factores de éxito, anti-patrones
  5. Generar `tasks.md` con sprints
  6. **Generar HTML previews** — páginas autocontenidas con CSS y datos de ejemplo
  7. **Generar scaffolding MCP** (si aplica) — `hermes-sdd-mcp/` server esqueleto
  8. MOSTRAR TODO al usuario (artefactos + previews)
  9. HACER preguntas de clarificación
  10. Ajustar según respuestas

## Maturity Model SDD (seleccionar según el caso)

| Nivel | Descripción | Cuándo |
|-------|-------------|--------|
| **Spec-First** | Specs seed la generación inicial, luego el código deriva | Prototipos, features exploratorias |
| **Spec-Anchored** ✅ | Specs + tests enforzan alineación continua | **Sweet spot para producción (recomendado)** |
| **Spec-as-Source** | Humanos editan SOLO la spec, código 100% generado | Equipos maduros con tooling confiable |

Por defecto apuntar a **Spec-Anchored**. Preguntar si el usuario quiere otro nivel.

## Estructura de artefactos

```
.specify/
  memory/
    constitution.md    - Reglas no negociables del proyecto
specs/
  NNN-nombre-feature/
    spec.md            - Especificación funcional (EARS)
    plan.md            - Plan técnico detallado
    tasks.md           - Desglose de tareas atómicas
previews/
  NNN-nombre-feature/  - HTML previews autocontenidos
mcp/
  hermes-sdd-mcp/      - MCP server scaffolding (opcional)
```

## Comandos SDD

### sdd:constitution
Crea la constitución del proyecto. Pregunta: lenguaje, framework, testing,
seguridad (OWASP ASI level), hosting, multi-tenant, i18n.
Guarda en `.specify/memory/constitution.md`

### sdd:specify "descripción"
Genera spec.md con User Stories, Acceptance Criteria EARS, Out of scope,
Non-functional requirements, y **sección de seguridad ASI relevante**.

### sdd:clarify
Revisa la spec y pregunta ambigüedades. Actualiza spec.md.

### sdd:plan "tech stack (opcional)"
Genera plan.md con Architecture, Data model, API contracts, Librerías,
Factores críticos de éxito, Anti-patrones, Hosting, y Constitution check.

### sdd:tasks
Desglosa plan.md en tareas atómicas con prioridad (P1/P2/P3), dependencias,
y verificación. Mínimo 5-15 min por tarea.

### sdd:html-preview
Genera HTML previews autocontenidos en `previews/NNN-feature/`.
CSS embebido, datos ficticios realistas, flujo completo visible.

### sdd:mcp-server
Scaffolding de un MCP server esqueleto en `mcp/hermes-sdd-mcp/`:
- Python FastMCP o TypeScript según el stack
- Herramientas para los endpoints principales
- README con configuración

### sdd:implement
Ejecuta tasks.md en orden usando `delegate_task` (una tarea por subagente)
con el skill `subagent-driven-development` y `test-driven-development`.
Cada tarea produce un commit.

### sdd:checklist
Genera checklist de calidad alineado con OWASP ASI 2026:
- [ ] ASI01: Goal Hijack — inputs externos como no confiables
- [ ] ASI02: Tool Misuse — permisos mínimos por herramienta
- [ ] ASI03: Identity Abuse — JIT ephemeral tokens
- [ ] ASI04: Supply Chain — MCP servers allowlist
- [ ] ASI05: RCE — sandboxing de código generado
- [ ] ASI06: Memory Poisoning — memoria por tenant, expirar no verificada
- [ ] ASI07: Inter-Agent Comm — mTLS si multi-agente
- [ ] ASI08: Cascading Failures — circuit breakers, cost-ceilings
- [ ] ASI09: Trust Exploitation — confidence scores, step-up auth
- [ ] ASI10: Rogue Agents — monitoreo de drift, kill switches

### sdd:status
Muestra progreso del feature actual (tasks completadas/pendientes).

## EARS — 5 Patrones para Acceptance Criteria

Usar SIEMPRE en spec.md:

### 1. Ubiquitous (siempre verdadero)
`THE [system] SHALL [comportamiento permanente].`
- "THE system SHALL log every authentication attempt."
- "EL sistema DEBE cifrar datos personales en reposo."

### 2. Event-driven (WHEN + trigger)
`WHEN [evento] THE [system] SHALL [respuesta].`
- "WHEN a user submits the login form THE system SHALL validate credentials."
- "WHEN el cliente envía el formulario THEN el sistema DEBE asignar código único."

### 3. State-driven (WHILE + estado)
`WHILE [estado] THE [system] SHALL [comportamiento].`
- "WHILE a sync is in progress THE system SHALL display a progress indicator."
- "WHILE no hay resultados THEN el sistema DEBE mostrar mensaje de no encontrado."

### 4. Unwanted behavior (IF + condición)
`IF [condición adversa] THEN THE [system] SHALL [respuesta].`
- "IF credential validation fails 3 times in 60s THEN the system SHALL lock the account."
- "IF PDF corrupto THEN el sistema DEBE saltarlo y reportarlo."

### 5. Optional features (WHERE + condición)
`WHERE [feature activa] THE [system] SHALL [comportamiento].`
- "WHERE multi-factor auth is enabled THE system SHALL require TOTP after password."
- "WHERE modo estricto THEN el sistema DEBE validar formato de expediente."

## Routing de Modelos (eficiencia agéntica)

Usar el modelo adecuado según la fase SDD. No todos los skills/documentos
lo especifican — aquí está el patrón probado:

| Fase SDD | Modelo recomendado | Por qué |
|----------|-------------------|---------|
| Constitution | Cualquiera (rápido) | Lista corta de reglas |
| Spec + EARS | DeepSeek Reasoner o Gemini | Precisión en lógica de requisitos |
| Plan | DeepSeek Reasoner | Arquitectura, trade-offs |
| Tasks | DeepSeek Flash o Gemini Flash | Desglose mecánico |
| HTML Preview | Modelo con output largo | Generar HTML completo |
| MCP Server | DeepSeek Reasoner | Schema definitions, tipos |
| Implement | DeepSeek Flash | Velocidad para código repetitivo |
| Code Review | Gemini (contexto masivo) | Revisión de diff grande |
| Security Review | Gemini o modelo especializado | OWASP ASI checklist |

Si el modelo actual no soporta alguna fase, adaptar — esto es un ideal,
no un requisito.

## Token Optimization Patterns (Hermes-native)

### 1. Lazy Tool Loading
Usar `execute_code` para operaciones por lotes en lugar de múltiples
tool calls independientes. Una sola llamada con pipeline Python procesa
N archivos reduciendo ~800 tokens/round-trip extra.

### 2. Frozen Memory Snapshot
La constitución (`constitution.md`) y reglas del proyecto deben cargarse
al inicio y no repetirse en cada turno. Hermes lo hace automáticamente
con MEMORY.md/USER.md — aprovecharlo.

### 3. Parallel Tool Calls with execute_code
```python
from hermes_tools import terminal, read_file, write_file

# Batch: leer múltiples archivos en paralelo
files = ["src/main.py", "src/models.py", "src/api.py"]
contents = {f: read_file(f)["content"] for f in files}
# Procesar y escribir resumen compacto
summary = {f: f"#{len(c.splitlines())} lines" for f, c in contents.items()}
write_file("docs/summary.md", str(summary))
```

### 4. Context Pruning con /compress
Antes de alcanzar el límite de contexto, usar `/compress` en Hermes.
El pipeline de 5 fases (pruning → boundaries → LLM summary → assembly →
integrity) protege ambos extremos de la conversación.

### 5. Prompt Caching
Colocar reglas estáticas (constitución, guía de estilo, ejemplos de EARS)
al inicio del prompt para que permanezcan en KV cache. Lo dinámico
(la spec actual) después.

## Testing (Record Decisions, Not HTTP)

Para tests de agentes, NO mockear llamadas HTTP enteras (eso congela
el loop del agente). Usar el patrón **Record Decisions, Not HTTP**:

```python
# En lugar de mockear la API del LLM...
# Grabar SOLO las decisiones (qué tool, qué args, cuándo)
decisions = [
    {"tool": "search_files", "args": {"pattern": "*.py"}},
    {"tool": "read_file", "args": {"path": "src/main.py"}},
]

# Durante replay: USAR las decisiones grabadas, PERO ejecutar
# las herramientas reales (no mock)
for decision in decisions:
    tool = get_tool(decision["tool"])
    result = tool(**decision["args"])
    assert result["exit_code"] == 0
```

Esto valida tanto el razonamiento del agente como la implementación
real de las herramientas, sin llamadas costosas al LLM en cada test.

## OWASP ASI 2026 — Checklist de Seguridad Integrado

Cada spec DEBE incluir una sección de seguridad con los riesgos ASI
relevantes para el proyecto:

```
## Security Considerations (OWASP ASI 2026)

### Alto Riesgo
- [ASI05] Código generado se ejecuta en sandbox Docker network:none
- [ASI06] Memoria persistente aislada por tenant con expiración

### Medio Riesgo
- [ASI02] Tools con permisos mínimos y rate limiting
- [ASI03] JWT con scopes específicos por endpoint

### Monitoreo
- [ASI08] Circuit breaker: max 3 retries por tool call
- [ASI10] Log de objetivos del agente para detección de drift
```

## Debates y Críticas (contexto para informar al usuario)

Cuando presentes SDD, el usuario puede encontrar estas críticas en la
comunidad. Es profesional mencionarlas:

### "Same Patterns, New Hype" — Brandon Kindred
SDD es waterfall/contract-design rebautizado. El valor está en el
pensamiento detrás de la spec, no en el tooling.

### Thoughtworks Technology Radar
SDD está en "Assess", no "Adopt". El código ejecutable sigue siendo
la fuente de verdad. "Specs alone suffice" es un riesgo.

### "SDD nos está haciendo peores supervisando"
(Reddit r/AI_Agents) — La especulación excesiva atrofia la habilidad
humana de revisar código generado.

### "Waterfall con mejor tooling"
(Debate video 3h — Our Tech Journey) — El problema más duro no es
escribir código, sino descubrir si estás construyendo lo correcto.
Specs perfectas no reemplazan feedback loops cortos.

**Cómo responder:** SDD no reemplaza la iteración. Spec-Anchored
(no Spec-as-Source) permite que specs y código evolucionen juntos.
Los tests son el enforcement, no la spec sola.

## Implementación con delegate_task

Usar `subagent-driven-development` skill para implementar:

```python
from hermes_tools import delegate_task, read_file

tasks = read_file("specs/NNN-feature/tasks.md")["content"]

# Una tarea por subagente, en paralelo hasta 5
for task_block in parse_tasks(tasks):
    delegate_task(
        goal=f"Implement {task_block['name']}",
        context=f"""
        Project: {project_path}
        Constitution: {constitution_content}
        Spec: {spec_content}
        Plan: {plan_content}
        Task: {task_block['details']}

        Use test-driven-development skill: test first, then code.
        Use writing-plans skill for bite-sized sub-tasks.
        Commit after each sub-task.
        """,
        toolsets=["terminal", "file"]
    )
```

## Pitfalls Conocidos

### Shiny for Python: API cambia entre versiones
En Shiny 1.6+, `ui.nav()` → `ui.nav_panel()`. Usar `ui.nav()` da
`AttributeError`.

### TestClient + SQLite in-memory
Crear tablas a nivel de módulo (NO en fixture con `yield`), porque
los fixtures se ejecutan en orden impredecible con `app.dependency_overrides`.

### delegate_task sin contexto suficiente
Cada subagente empieza SIN memoria de la conversación. Pasar
TODO el contexto relevante (path de archivos, constitution, spec,
tarea específica) en el campo `context`.

### HTML previews con paths absolutos
Los HTML previews deben ser autocontenidos (CSS inline, sin
dependencias externas) para que el usuario pueda abrirlos
directamente desde el filesystem.

### MCP server scaffolding pesado
No generar MCP server si el proyecto no lo necesita. Solo cuando
el proyecto expondrá herramientas a otros agentes (RAG, APIs,
procesamiento de documentos). Para proyectos simples, omitir.

## Notas

- Los skills relacionados se cargan automáticamente desde Hermes
- No requiere herramientas externas — todo es Hermes-native
- Priorizar Spec-Anchored sobre Spec-as-Source
- Incluir siempre la sección de críticas SDD para transparencia
- Usar execute_code para batch processing, delegate_task para paralelismo
