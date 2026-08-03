---
name: skill-consolidation
description: "Consolidar skills solapados en umbrellas con absorbed_into."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, consolidation, maintenance, skill_manage, umbrella]
    category: autonomous-ai-agents
    related_skills: [hermes-agent-skill-authoring, hermes-agent]
---

# Skill Consolidation — Fusionar Skills Solapados en Umbrellas

Procedimiento validado (Jul 2026, 4 fusiones ejecutadas: MCP 2→1, Paywall 3→1, Forense 3→1, Estadística 2→1). Reduce el tamaño del índice de skills y — más importante — la AMBIGÜEDAD de trigger: cuando hay 3 skills que cubren lo mismo, el agente carga los 3; con un umbrella carga 1 con todo.

## Cuándo Usar

- El usuario pide "consolidar skills", "limpiar skills solapados", "reducir el índice"
- Hay N skills con descripciones/temáticas casi idénticas (duplicados reales)
- El usuario pide optimizar el rendimiento del agente (token hygiene)

## Paso 0 — Análisis (ANTES de tocar nada)

1. **Escanear frontmatters** de todos los SKILL.md: name, description (largo), created_by:

```python
import os, re, glob
SKILLS = os.path.expanduser("~/.hermes/skills")
for path in glob.glob(f"{SKILLS}/**/SKILL.md", recursive=True):
    c = open(path, encoding="utf-8").read()
    fm = re.match(r"^---\n(.*?)\n---", c, re.S)
    if fm:
        name = re.search(r"^name:\s*(.+)$", fm.group(1), re.M)
        desc = re.search(r"^description:\s*(.+)$", fm.group(1), re.M)
        created = re.search(r"^created_by:\s*(.+)$", fm.group(1), re.M)
        # agrupar por similitud temática
```

2. **Identificar clusters** por solapamiento real (mismo dominio, misma audiencia):
   - 🔴 DUPLICADO REAL → fusionar (ej: dos skills "build MCP servers")
   - 🟠 RELACIONADO → evaluar (cliente vs CLI del mismo sistema)
   - 🟢 DISTINTO / cluster activo del usuario → NO tocar sin aprobación explícita

3. **Verificar qué se inyecta de verdad** (no asumir):
   - Descripciones de SKILL se truncan a 57+3 chars antes de inyectarse (`extract_skill_description` en `agent/skill_utils.py`) → recortarlas NO ahorra nada
   - Descripciones de CATEGORÍA (`DESCRIPTION.md`) se inyectan COMPLETAS sin truncar (`prompt_builder.py`) → ese es el lever rápido
   - Índice total ≈ N_skills × ~80 chars ≈ N×20 tokens

4. **Chequear cron jobs** que referencien nombres de skills antes de borrar:
   `grep -r "<skill-name>" ~/.hermes/cron/`

5. **Presentar plan al usuario** con veredicto por cluster (🔴🟠🟢) y pedir aprobación. Las fusiones son destructivas — nunca ejecutar sin OK explícito.

## Paso 1 — Backup (OBLIGATORIO, siempre)

```bash
cd ~/.hermes && tar czf skills-backup-$(date +%Y%m%d_%H%M%S).tar.gz skills/
```

## Paso 2 — Elegir el Umbrella

El skill MÁS COMPLETO del cluster (mayor tamaño, más secciones, ya cubre el tema). Leer TODOS los skills del cluster con `skill_view` para identificar qué es contenido ÚNICO de cada uno (lo que no está ya duplicado en el candidato a umbrella).

## Paso 3 — Copiar references/ y scripts/ ANTES de borrar (pitfall #1)

Los `skill_manage delete` eliminan el directorio completo del skill. Todo archivo en `references/`, `scripts/`, `templates/`, `assets/` debe copiarse al umbrella PRIMERO:

```bash
cd ~/.hermes/skills/<categoria>/
mkdir -p <umbrella>/references/ <umbrella>/scripts/
cp <absorbido>/references/*.md <umbrella>/references/ 2>/dev/null
cp <absorbido>/scripts/* <umbrella>/scripts/ 2>/dev/null
```

## Paso 4 — Patch del Umbrella con el contenido único

`skill_manage(action='patch')` en el umbrella, insertando secciones nuevas con el contenido ÚNICO de cada absorbido, etiquetado como `(absorbido de <skill>)`. NO duplicar lo que el umbrella ya tiene. Incluir:
- Datos/reglas/scripts que solo existían en el absorbido
- Secciones completas si el absorbido era profundo (ej: patrón WSL→Windows completo)
- Actualizar las listas de "Related Skills" y "Reference Files" del umbrella

## Paso 5 — Delete con absorbed_into (el target DEBE existir ya)

```bash
skill_manage(action='delete', name='<absorbido>', absorbed_into='<umbrella>')
```

El umbrella debe estar patcheado ANTES — `absorbed_into` exige que el target exista. El orden importa: patch primero, delete después.

## Paso 6 — Verificación (siempre con datos reales)

```python
import os, re, glob
SKILLS = os.path.expanduser("~/.hermes/skills")
skills = glob.glob(f"{SKILLS}/**/SKILL.md", recursive=True)
print(f"SKILLS: {len(skills)} (antes → después)")
# 1. Umbrellas existen con refs/scripts intactos
# 2. Absorbidos NO existen (grep por name en frontmatter)
# 3. Índice estimado: len(skills) × 80 chars
# 4. Ahorro: N_eliminados × 80 chars ≈ tokens/sesión
```

## Pitfalls (aprendidos en ejecución real)

1. **Copiar refs/scripts ANTES de delete** — el delete borra el directorio entero. El pitfall #1 de todo el proceso.
2. **No recortar descripciones de skills** — ya se truncan a 57+3 en el índice (`SKILL_PROMPT_DESC_LIMIT`). Perder tiempo y no ahorrar nada.
3. **El lever rápido real son las DESCRIPTION.md de categoría** — se inyectan completas. Recortarlas (3,103→1,640 chars en la ejecución real) sí ahorra tokens por sesión.
4. **Los cambios del índice toman efecto en la PRÓXIMA sesión** — el snapshot (`.skills_prompt_snapshot.json`) se regenera; nunca romper prompt caching a mitad de conversación.
5. **curator solo toca skills con `created_by: "agent"`** — la mayoría de skills del usuario tienen `created_by: (none)` y no son elegibles. No contar con curator para consolidar skills propios.
6. **No fusionar clusters activos del usuario** sin aprobación explícita (ej: scraping Perú) — cada skill puede cubrir un sistema distinto; consolidar ahí es alto riesgo, bajo beneficio.
7. **El ahorro de tokens por skill eliminado es pequeño (~80 chars ≈ 20 tokens/sesión)** — el beneficio real es la calidad: menos ambigüedad de trigger, una sola fuente de verdad, mantenimiento más simple. Ser honesto con el usuario sobre esto.
8. **Backup SIEMPRE** — 2.6MB por 123 skills, restaura todo con `tar xzf`.
9. **El índice de skills no es 18-20K tokens** (estimación errónea inicial) — es ~N×80 chars ≈ 2.5K tokens para 123 skills, y con prompt caching se paga cache-hit tras el primer turno. Verificar en el código antes de afirmar cifras.

## Verificación final del usuario

Reportar: tabla por cluster (qué se fusionó en qué), conteo antes→después, refs/scripts preservados, ruta del backup, ahorro real, y qué quedó pendiente. Estimar tokens consumidos en la tarea.
