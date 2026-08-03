---
name: sdd
description: Spec-Driven Development workflow for Hermes Agent.
triggers:
  - User asks to create a spec
  - sdd:specify
  - sdd:plan
version: 1.0.0
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
  6. MOSTRAR TODO al usuario
  7. HACER preguntas de clarificacion
  8. Ajustar segun respuestas

## Estructura

Cada feature crea:
  specs/NNN-nombre-feature/
    spec.md       - Especificacion funcional
    plan.md        - Plan tecnico (arquitectura, data model, hosting)
    tasks.md       - Desglose de tareas con sprints

La constitucion del proyecto va en .specify/memory/constitution.md

## Archivos del Skill

- `references/caso-intake-legal.md` — caso real completo (preguntas, data model, API)
- `references/herramientas-sdd.md` — herramientas populares y notacion EARS
- `templates/spec-template.md` — template para spec.md
- `templates/plan-template.md` — template para plan.md
- `templates/tasks-template.md` — template para tasks.md

Usa los templates como base y el caso de referencia como inspiracion.

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

## Notas

- No requiere herramientas externas
- Los archivos se guardan en specs/ en la raiz del proyecto
- Basado en GitHub Spec Kit, Autospec y EARS notation
