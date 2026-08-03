# Estado del Proyecto Multi-Agente — Junio 2026

## Completado

| Componente | Impacto real |
|---|---|
| 🎯 **Retrieval Strategist** | 85% clasificación, 90% menos LLM calls, top_k dinámico (3-12) |
| 🕸️ **Graph Analyst** | Estadísticas precisas del grafo (sin LLM), cadenas de precedente reales, paralelizado con ThreadPoolExecutor |
| 🔍 **Critic Agent** | 19/20 consultas score 100%, detecta alucinaciones en citas, 6 patrones de extracción, fuzzy matching deshabilitado |
| 🔄 **Feedback Loop** | Máx 2 iteraciones, solo hallucinaciones reales, strict mode en 2do intento |
| 📊 **Auditoría granular** | JSON por consulta con trazabilidad completa (hybrid + graph + critic + feedback) |
| 💬 **Repreguntas** | Historial limitado (3 intercambios MAX_HISTORY_EXCHANGES=3, 4000 tokens MAX_HISTORY_TOKENS), follow-ups por número |
| ✍️ **Refactorización** | extract_citations() dividido en 7 métodos por patrón, funciones largas documentadas |

## Pendiente con impacto alto

### 1. Feedback loop → modo strict (2-3 días)
Hoy el feedback loop existe pero rara vez se activa (0/20 en última batería). El modo strict=False es warn-only. Para activar corrección automática real, cambiar a strict=True por defecto.

### 2. Orchestrator formal (3-5 días)
run_console_query() es monolítica (135+ líneas). Refactorizar como clase Orchestrator que delega explícitamente a cada agente. Necesario para flujos condicionales complejos.

## Pendiente con impacto medio/bajo

| Pendiente | Esfuerzo | Impacto |
|---|---|---|
| Deep Research (multi-query expansion, Opción B) | 1-2 días | Alto - cobertura 3-5× más amplia |
| Strategist en api.py | 1 hora | Bajo (API usa top_k fijo 7) |
| Paralelizar FAISS+BM25 | 2-3 horas | Bajo (~1-2s de 37s totales) |
| Dashboard de métricas | 1-2 días | Valor operativo |
| Tests automatizados | 1-2 días | Previene regresiones |

## Última batería de pruebas
20 consultas nuevas (mayo 2026): 20/20 exitosas, 858.7s, Critic 100% en 19/20. Feedback loop: 0 activaciones.

Ver `references/bateria-final-completa.md` para resultados detallados.
