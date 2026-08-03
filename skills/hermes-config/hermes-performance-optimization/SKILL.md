---
name: hermes-performance-optimization
description: "Optimizar Hermes: memoria, token hygiene, DB, aliases."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows, wsl]
metadata:
  hermes:
    tags: [hermes, performance, memory, tokens, sqlite, model-aliases, optimization]
    category: autonomous-ai-agents
    related_skills: [skill-consolidation, hermes-recovery, hermes-agent]
---

# Hermes Performance Optimization

Playbook validado (Jul 2026) para optimizar Hermes Agent: ampliar memoria, reducir tokens por sesión, verificar salud de la DB, y configurar aliases de modelo. Complementa a `skill-consolidation` (fusión de skills solapados) y a `hermes-agent` (config general, bundled — no editable).

## Cuándo Usar

- "¿Cómo optimizas tu rendimiento?", "amplía tu memoria", "reduce tokens", "¿cuál es tu estado?"
- Antes de tocar config.yaml con fines de rendimiento
- Cuando el usuario pregunta por el indicador naranja del modelo en el terminal

## 1. Ampliar Memoria

- Límites: `memory.memory_char_limit` (default 4000) y `memory.user_char_limit` (default 3000)
- Comandos: `hermes config set memory.memory_char_limit 8000`, `hermes config set memory.user_char_limit 5000`
- La memoria se inyecta en CADA turno: subir límites cuesta ~1-3K tokens/turno extra (fracciones de centavo con DeepSeek)
- `checkpoints.auto_prune: true` (retiene 7 días, tope 500MB)
- OJO: la memoria NO es RAM — es texto inyectado por turno. El límite duro es la ventana de contexto (1M ya configurado). Token hygiene > tamaño de memoria. Explicar esto al usuario con honestidad.

## 2. Token Hygiene — el lever REAL

Mecánica verificada en código (`agent/skill_utils.py`, `agent/prompt_builder.py`):
- Descripciones de SKILL se truncan a 57+3 chars antes de inyectarse (`extract_skill_description`) → recortarlas NO ahorra nada
- Descripciones de CATEGORÍA (`DESCRIPTION.md`) se inyectan COMPLETAS sin truncar → ese es el lever rápido
- Índice total ≈ N_skills × ~80 chars ≈ N×20 tokens (123 skills ≈ 2.5K tokens, no 18-20K)
- Con prompt caching (TTL 1h) el índice se paga a cache-hit (~1/10) tras el primer turno

Procedimiento categorías: escanear `DESCRIPTION.md`, recortar a ≤90 chars (trigger en primeros 57). Ejecución real: 22 categorías 3,103→1,640 chars (-365 tokens/sesión).

Reducir el NÚMERO de skills: usar `skill-consolidation` (workflow completo con backup + absorbed_into).

## 3. Salud de la DB (state.db)

- state.db = historial de TODAS las sesiones (puede ser 400-600MB) — es datos reales indexados FTS5, no basura
- VERIFICAR ANTES DE VACUUM: `PRAGMA freelist_count` == 0 → VACUUM no recupera nada (no asumir que la DB está inflada)
```bash
python3 -c "import sqlite3; c=sqlite3.connect('file:~/.hermes/state.db?mode=ro', uri=True); print('freelist:', c.execute('PRAGMA freelist_count').fetchone()[0])"
```
- journal_mode=wal + SQLite 3.51.3 (lib compilada + LD_PRELOAD en WSL/Ubuntu 24.04) = sano; el bug de corrupción WAL afecta SQLite <3.50.7 — ver `hermes-recovery`
- WAL sano = archivo .db-wal pequeño (KB-MB); si crece a GB, checkpoint

## 4. Aliases de Modelo (cambio por sesión)

- Definir: `hermes config set model.aliases.heavy deepseek/deepseek-v4-pro` (formato corto `provider/model`; forma larga con `model:` + `provider:` + opcional `base_url`)
- Uso: `/model heavy` — **session-scoped**: SOLO afecta la ventana actual
- `/model heavy --global` → persiste como default para futuras sesiones
- Alias built-in ya existen: `deepseek`, `sonnet`, `gpt5`, `qwen`, etc. (catalog-resolved); los del usuario tienen prioridad
- **Multi-ventana**: cada ventana/pestaña CLI es una sesión/proceso independiente; el cambio en una NO afecta a las demás. Estrategia: ventana A rutina (flash), ventana B razonamiento (pro)
- Costo: pro típicamente 2-4x flash; uso selectivo. `display.show_cost: true` para monitorear

## 5. Status Bar vs Footer (qué muestra el modelo)

- **STATUS BAR** (línea sobre el prompt, `cli.py:7432`): `● deepseek-v4-flash · N tools · provider: deepseek` — el modelo en accent color (`ui_accent`, #FFBF00 ≈ naranja/ámbar). Cambia con `/model` al instante. Usa `_reverse_alias_for_display()` → muestra el ALIAS si existe (ej: "heavy" en vez del nombre largo). El ● verde = API conectada.
- **FOOTER** (`gateway/runtime_footer.py`): línea de metadata al FINAL de cada respuesta del agente (`model · context_pct · cwd`). APAGADO por defecto. Toggle: `/footer on|off`. NO confundirlo con la status bar — el usuario suele llamar "footer" al modelo naranja del prompt, que es la status bar.

## Pitfalls

- NO afirmar cifras de tokens sin verificar en el código: estimación errónea de "18-20K tokens/turno" corregida a ~2.5K (el índice ya trunca descripciones). Verificar antes de reportar.
- Contar NOMBRES ÚNICOS de skills, no archivos SKILL.md: pueden existir duplicados con el mismo frontmatter `name` en 2 rutas (encontrados: `computer-use`, `dogfood`) que inflan el conteo crudo del glob. Detectar con set de names; reportar como hallazgo, no fusionar sin aprobación.
- Los cambios de config/índice toman efecto en la PRÓXIMA sesión — nunca romper prompt caching a mitad de conversación
- Reportar con honestidad qué se tocó y qué no (transparencia de alcance), incluir estimación de tokens consumidos al final
- Verificación con datos reales: `hermes config set` devuelve ✓, `freelist` medido, conteo de skills real

## Related

- `skill-consolidation` — fusión de skills solapados en umbrellas (workflow completo)
- `hermes-recovery` — SQLite WAL, backups, restauración post-crash
- `hermes-agent` (bundled) — config general, providers, toolsets
