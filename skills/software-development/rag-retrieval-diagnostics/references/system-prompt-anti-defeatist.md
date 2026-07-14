# System Prompt Anti-Derrotista

## Problema

El RAG generaba respuestas con lenguaje derrotista cuando no encontraba la respuesta exacta. 13 de 100 queries en la batería del 02-may-2026 contenían frases como "no se encontró", "no hay información", "lamentablemente".

## Causa raíz

DOS prompts independientes con instrucciones de "honestidad" mal calibradas:

**Prompt 1** (api_rest.py:1360): `Si no hay normas relevantes, dilo honestamente.`
**Prompt 2** (orchestrator_rag_v3.py:820): `Si el contexto no contiene la respuesta, indícalo claramente`

El LLM interpretaba esto como permiso para rendirse, incluso con información parcial disponible.

## Fix (02-may-2026)

Reemplazar instrucciones de honestidad por instrucciones constructivas + lista explícita de frases PROHIBIDAS. Ver SKILL.md sección "ANTI-PATRÓN: System prompt derrotista" para el código completo.

## Resultado

- "renuncias Poder Judicial": pasó de "no se encontró" a "Según los datos disponibles... Sin embargo, se encontraron..." + 3 citas reales
- "sanciones Contraloría": pasó de vacío a respuesta detallada con Resolución Nº 709-2024-CG
- "minería asteroides" (trampa): pasó de rendirse a citar DS 003-2025-IN como relacionado

El patrón cambió de **derrota → silencio** a **"no hay específico PERO sí hay relacionado"**.
