---
name: skill-maintenance
description: "Mantener y optimizar skills de Hermes: podar skills sobredimensionadas, extraer detalle histórico a references/, consolidar entradas duplicadas, y mantener SKILL.md enfocado en guía operativa."
version: 1.0.0
author: Hermes Agent
tags: [hermes, skills, optimization, maintenance, podding, cleanup]
---

# Skill Maintenance

Mantener las skills de Hermes en buen estado es clave para el rendimiento. Skills muy grandes (>15KB) consumen contexto innecesario cuando se cargan.

## Trigger

Usar cuando:
- Una skill supera los 15KB y contiene debugging histórico o logs de prueba
- El usuario reporta que Hermes es "lento" o "verboso" (causa frecuente: skills pesadas)
- Dos skills se superponen en contenido
- Una skill tiene secciones de migración/depuración que solo son relevantes como referencia histórica
- Se identifica contenido que pertenece a `references/` y no al SKILL.md principal

## Proceso de Poda

### 1. Identificar skills candidatas
```bash
find ~/.hermes/skills/ -name 'SKILL.md' -not -path '*/.archive/*' -exec wc -c {} \; | sort -rn | head -20
```
Skills >15KB son candidatas. Skills >30KB requieren poda urgente.

### 2. Analizar contenido
Usar `skill_view(name)` para leer el SKILL.md completo. Identificar:

| Qué mantener en SKILL.md | Qué mover a references/ |
|---|---|
| Trigger conditions | Logs de prueba |
| Stack / setup | Debugging histórico |
| Comandos clave | Migraciones Windows→Ubuntu |
| Flujo optimizado | Resultados de tests antiguos |
| Anti-bloqueo / reglas | Comparativas de modelos |
| Pitfalls esenciales | Estructura del corpus/documentos |
| Dependencias | Evaluaciones descartadas |

### 3. Extraer a references/
Crear `references/historial-<skill>.md` con el contenido histórico extraído. Incluir un frontmatter descriptivo.

### 4. Reescribir SKILL.md
- Mantener solo la guía operativa esencial
- Incluir una tabla de Support Files al final listando todos los `references/` y `scripts/`
- Añadir enlace al nuevo archivo de historial

### 5. Verificar
```bash
skill_view(name="<skill-name>")
# Confirmar que carga correctamente y linked_files están intactos
```

## Estrategia de delegación

Para skills grandes (>30KB), usar `delegate_task` para la extracción:
```python
delegate_task(
    goal="Podar la skill <nombre> de ~XXKB a ~15KB",
    context="Ruta exacta, qué secciones mover, formato references/<nombre>.md",
    toolsets=["file"]
)
```

Luego verificar manualmente el resultado con `skill_view()`.

## Estrategia de memoria

Paralelo a la poda de skills, consolidar memoria:
1. Revisar `memory` entries actuales
2. Fusionar entradas relacionadas (ej. varias sobre el mismo proyecto)
3. Mover procedimientos a skills, dejar solo hechos compactos en memoria
4. Objetivo: mantener memoria por debajo del 80% (1,760/2,200 chars)

## Poda de skills archivadas

Skills en `.archive/` no se cargan pero ocupan espacio:
```bash
# Listar archivadas
find ~/.hermes/skills/.archive/ -name 'SKILL.md' -exec wc -c {} \;

# Eliminar las obsoletas (thinking-toggle, think, deepseek-reasoning-errors, etc.)
rm -rf ~/.hermes/skills/.archive/<nombre>/
```

## Cuándo NO podar

- Skills bundled (shipped with Hermes) — no se pueden editar
- Skills instaladas via `hermes skills install` — protegidas
- Skills <10KB — no vale la pena
- Skills que se usan semanalmente y toda su información es relevante
