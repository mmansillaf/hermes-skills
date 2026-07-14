# Tasks: [Nombre de la Feature]

**Prioridades:** [P1] Core MVP, [P2] Post-MVP, [P3] Futuro
**Nivel SDD:** Spec-Anchored (specs + tests enforzan alineación)
**Testing:** TDD estricto — test primero, luego código

---

## Sprint 1: [Nombre del Sprint — 2-3 días]

### [P1] task_001: [Nombre de la tarea — ~15 min]
- [Paso concreto 1 con path exacto]
- **Verificación:** [comando o criterio concreto]
- **Dependencias:** ninguna

### [P1] task_002: [Nombre]
- **Dependencias:** task_001
- [Paso concreto]
- **Verificación:** [comando pytest -v específico]

### [P1] task_003: [Nombre]
- **Dependencias:** task_002
- [Paso concreto]
- **Verificación:** [curl/httpx test]

---

## Sprint 2: [Nombre del Sprint — 2-3 días]

### [P1] task_004: [Nombre]
- **Dependencias:** task_003
- [Paso concreto]
- **Verificación:** [criterio]

### [P1] task_005: [Nombre]
- **Dependencias:** task_004
- [Paso concreto]
- **Verificación:** [criterio]

---

## Sprint 3: [Nombre — 1-2 días]

### [P1] task_006: [Nombre]
- **Dependencias:** task_005
- [Pasos]
- **Verificación:** [criterio]

---

## Post-MVP (no tocar aún)

### [P2] task_N: [Nombre]
- [Descripción breve]
- **Cuándo:** después de validación del MVP

### [P3] task_N+1: [Nombre]
- [Descripción breve]

---

## Notas de Implementación

- Cada task se implementa con `delegate_task` → subagente aislado
- Cada task produce un commit con mensaje claro
- Review de spec compliance después de cada task
- Si una task falla >3 intentos: marcar como BLOCKED y escalar
