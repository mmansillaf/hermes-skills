# Lex RAG: Arquitectura Actual vs Multi-Agente

## Hoy (pipeline secuencial)
```
Usuario → Router → Retrieval → Synthesizer → Respuesta
           (1 call)  (0 calls)   (1-2 calls)
```
- 2-3 LLM calls/query
- Sin verificación de citas
- top_k fijo (7)
- Sin feedback loop

## Multi-Agente (implementado parcialmente)
```
Usuario → Orchestrator → Router + Strategist + Retrieval → Writer → Critic → Respuesta
           (0-1 call)  (1+1+0 calls)  (algorítmico)   (1 call)  (1 call, 0 LLM)
```

### Agentes implementados (Fase 1 y 2)
| Agente | Estado | LLM calls | Herramientas |
|--------|--------|-----------|--------------|
| Router | ✅ Existente | 1 | Prompt |
| Retrieval Strategist | ✅ Nuevo (F2) | 1 (llama-3.1-8b) | Prompt + heurística fallback |
| Graph Analyst | ⬜ Pendiente (F3) | 0-1 | NetworkX API |
| Legal Writer | ✅ Existente | 1 | Prompt + contexto |
| Critic | ✅ Nuevo (F1) | 0 (solo regex + metadata lookup) | Regex + metadata FAISS |
| Orchestrator | ⬜ Pendiente (F5) | 0-1 | Delegate |

## Costo
| Métrica | Actual | Multi-Agente |
|---------|--------|-------------|
| LLM calls/query | 2-3 | 3-5 (con strategist + critic) |
| Latencia | ~12-18s | ~15-28s |
| Costo/query (DeepSeek) | ~$0.002-0.015 | ~$0.003-0.02 |
| Falsos positivos (alucinaciones) | Sin detección | Detectados por Critic |

## Plan de fases completo
| Fase | Agente | Esfuerzo | Riesgo | Valor |
|------|--------|----------|--------|-------|
| 1 | ✅ Critic Agent | 2 días | Bajo | Alto |
| 2 | ✅ Retrieval Strategist | 3 días | Medio | Alto |
| 3 | ⬜ Graph Analyst | 3 días | Medio | Alto |
| 4 | ⬜ Feedback loop (critic → rewrite) | 5 días | Alto | Máximo |
| 5 | ⬜ Orchestrator formal | 5 días | Alto | Máximo |
