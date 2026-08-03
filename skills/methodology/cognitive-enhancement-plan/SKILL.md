---
name: cognitive-enhancement-plan
description: Structured cognitive optimization framework — 8 principles of human intelligence abstracted for agent architecture, with scientific basis (DOI-cited papers) and prioritization tiers for implementation
---

## Base Científica (Julio 2026)

Este skill documenta principios de inteligencia humana investigados en la carpeta `InteligenciaHumana/` (~180KB, 14 archivos, 20+ papers con DOIs, 22 videos de YouTube). Cada principio mapea a una mejora concreta del agente.

Ver `references/human-intelligence-abstractions.md` en el skill `learning-loop-implementation` para el detalle completo de cada abstracción.

---

## 8 Principios de Inteligencia Humana → Abstracciones para Agente IA

### TIER 1 — Prioridad Alta (bajo riesgo, $0, máximo impacto)

| # | Principio Humano | Base Científica | Abstracción IA | Esfuerzo | Impacto |
|---|-----------------|----------------|---------------|----------|---------|
| 1 | **Metacognición** — monitorear y ajustar el propio pensamiento | Corteza prefrontal dorsolateral; AI Chatbots mejoran funciones ejecutivas (2025, 47 citas) | Self-critique: 4 preguntas auto-verificación al final de TASK_COMPLETION_GUIDANCE | 10 min | Elimina fabricación de DOIs falsos y outputs inventados |
| 2 | **Externalización de memoria** — liberar WM con "segundos cerebros" | WM limitada ~4 chunks (Cowan); sistemas de notas externas mejoran rendimiento | Hybrid search: embeddings (all-MiniLM-L6-v2) + FTS5 con RRF fusion (K=60) | 2-3h | Encuentra sesiones por significado, no solo keywords |

### TIER 2 — Prioridad Media

| # | Principio Humano | Base Científica | Abstracción IA | Esfuerzo | Costo |
|---|-----------------|----------------|---------------|----------|-------|
| 3 | **Adaptación al desafío** — ajustar approach según complejidad | Carga cognitiva (Sweller); dificultad adaptativa en entrenamiento (2025 meta-análisis) | Task classifier: clasifica SIMPLE/MEDIUM/COMPLEX antes de ejecutar | 3-4h | $0 heurística; ~$0.82/año con Groq |
| 4 | **Técnica Feynman** — simplificar sin perder precisión | Vocabulario-CI correlación 60%; pero claridad prima sobre complejidad léxica | Simplificar output complejo con analogías antes de deliver | 15 min | $0 |

### TIER 3 — Baja Prioridad (exploratorio)

| # | Principio Humano | Base Científica | Abstracción IA |
|---|-----------------|----------------|---------------|
| 5 | **Active Open-Minded Thinking** — buscar contra-evidencia | Pensamiento activamente abierto (Stanovich 1997); alto CI cambia opinión más fácilmente (2024) | Al analizar, considerar contraargumentos explícitamente |
| 6 | **Spaced Repetition** — repasar en intervalos óptimos | Curva del olvido (Ebbinghaus); LTP en hipocampo; Chan (2024) DOI:10.1038/s41746-023-00987-5 | Revisión periódica de entradas de memory tool |
| 7 | **Práctica deliberada** — generar variantes, evaluar, fusionar | Práctica deliberada (Ericsson); CCT con dificultad adaptativa (2025, 67 estudios) | Autoresearch loop: git branch/test/merge semanal |
| 8 | **Eficiencia neuronal (NEH)** — menos recursos en tareas conocidas | NEH: cerebros brillantes consumen menos glucosa en PET | Token optimization: decir más con menos tools |

---

## Métricas de Simulación Validadas (WSL, CPU, Julio 2026)

| Abstracción | Métrica | Resultado | Comando/Librería |
|------------|---------|-----------|-----------------|
| Hybrid Search | Carga modelo embeddings (1ra vez) | 6.34s CPU | sentence-transformers all-MiniLM-L6-v2 |
| Hybrid Search | Velocidad encode | ~66ms/query | CPU con CUDA_VISIBLE_DEVICES="" |
| Hybrid Search | RAM | ~200MB | sentence-transformers |
| Hybrid Search | Cache 100 sesiones | ~0.1ms, ~1MB disco | ~/.hermes/hybrid_cache.json |
| Hybrid Search | RRF Fusion (K=60) | Verificado | ranks sintéticos + coseno |
| Task Classifier | Costo por clasificación (Groq) | $0.000022 | llama-3.3-70b-versatile |
| Task Classifier | Costo anual | ~$0.82 | 5 clasificaciones/día |
| Self-critique | Costo | $0 | En prefix cache del system prompt |

---

## Research → Implementation Workflow

Cuando el usuario pida pasar de investigación a implementación:

1. **READ ALL** — leer todos los archivos fuente antes de actuar (no confiar en resúmenes o cache)
2. **SIMULATE** — ejecutar pruebas técnicas reales en el entorno actual (no teorizar)
3. **EVALUATE** — aplicar framework TIER 1/2/3: impacto × riesgo × costo
4. **REPORT** — entregar informe con valoraciones numéricas claras
5. **RECOMMEND** — priorizar TIER 1 para implementación inmediata

---

## Referencias

- Investigación completa: `/mnt/d/PyCode/hermes-skills/InteligenciaHumana/`
- Abstracciones detalladas: skill `learning-loop-implementation` → references/human-intelligence-abstractions.md
- Implementación técnica: skill `learning-loop-implementation` → SKILL.md
- Informe con simulaciones: `iq_reporte_implementacion.md` en InteligenciaHumana/