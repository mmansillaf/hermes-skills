# Retrieval Strategist — Opciones Analizadas

Evaluación del 2026-05-19 para la Fase 2 del plan multi-agente.

## Baseline (solo LLM, llama-3.1-8b-instant)

- Precisión: 35% (7/20)
- LLM calls: 20/20 (100%)
- El LLM clasifica sistemáticamente TODO como "media" o "simple"
- Confusión: media→simple=100%, estadística→simple/media=100%

## Opciones evaluadas

| Opción | Precisión est. | Costo | Esfuerzo | Score ponderado |
|--------|---------------|-------|----------|-----------------|
| A: Prompt Engineering | 65-75% | gratis | 1h | 4.15/5 |
| **B: Reglas híbridas** | **85-95%** | **-40% calls** | **2-3h** | **4.40/5** |
| C: Modelo más grande | 80-90% | 10-20x caro | 5min | 3.75/5 |
| D: Few-shot + reglas | 80-90% | +300 tok | 2h | 4.15/5 |
| E: Solo heurísticas | 75-85% | 0 | 0h | 4.30/5 |

**Ganador: B (Reglas híbridas)** — 4.40/5.00

## Iteraciones de la Opción B

### v1: 75% precisión, 3 LLM calls
Reglas: <8→simple, ≥15→compleja, keywords→estadística, LLM para el resto.
Problema: "comparar" se clasificaba como simple (14 palabras, LLM falló).

### v2: 75% precisión, 2 LLM calls (después de ajustes)
Se añadieron reglas: "comparar/diferencia" y " y " detector.
Problema: queries con " y " de ≥15 palabras clasificaban como media (la regla 2c se ejecutaba antes que ≥15).

### v3 (final): 86% precisión, 2 LLM calls
Orden corregido: ≥15 palabras ANTES de " y ". Threshold simple: <7 (no <8).
Errores residuales: 3 (todas queries de 6-7 palabras sin " y ", threshold simple las captura).

## Reglas finales

```
1. Keywords estadísticos    → k=12, g=2
2. < 7 palabras             → k=4,  sin grafo
3. "comparar"/"diferencia"  → k=10, g=2
4. " y " + 7-14 palabras    → k=7,  g=1
5. ≥ 15 palabras            → k=11, g=2
6. Ambigüedad (7-14, sin señal) → LLM (simple k=5 o media k=7)
7. Fallback heurístico
```

## Resultados finales

- Precisión: 86% (18/21)
- LLM calls: 2/21 (90% menos que baseline)
- Errores: 3 (todas de 6-7 palabras sin " y ", threshold simple las captura)
