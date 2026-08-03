# Retrieval Strategist — Resultados finales

**Archivo:** `agents/retrieval_strategist.py`
**Última actualización:** 2026-05-20

## Precisión final: 86% (18/21)

Usando el test de 21 queries con texto completo (incluyendo C02 que antes fallaba).

### Matriz de confusión

| Esperado → Obtenido | Simple | Media | Compleja | Estadística |
|---------------------|--------|-------|----------|-------------|
| Simple (5) | **5** | 0 | 0 | 0 |
| Media (5) | 3 | **2** | 0 | 0 |
| Compleja (7) | 0 | 0 | **7** | 0 |
| Estadística (4) | 0 | 0 | 0 | **4** |

### LLM calls: 2 de 21 (90% menos vs original)

Solo las queries ambiguas de 7-14 palabras sin keywords claros llaman al LLM.

### Reglas duras (orden de evaluación)

| # | Regla | Condición | Resultado |
|---|-------|-----------|-----------|
| 1 | Estadística | keywords: "mas sentencias", "mas citadas", "que juez", "que entidad" | k=12, g=S2 |
| 2 | Simple | < 7 palabras | k=4, sin grafo |
| 3 | Comparativa | "comparar"/"diferencia" + ≥7 palabras | k=10, g=S2 |
| 4 | " y " conector | 7-14 palabras con " y " | k=7, g=S1 |
| 5 | Compleja | ≥ 15 palabras | k=11, g=S2 |
| 6 | Ambiguo | 7-14 palabras, sin reglas anteriores | LLM decide simple/media |

### Historial de versiones

| Versión | Precisión | LLM calls | Notas |
|---------|-----------|-----------|-------|
| Solo LLM (original) | 35% | 20/20 | Clasificaba todo como media |
| Prompt mejorado | 38% | 20/20 | Prompt más detallado pero LLM 8B ignoraba reglas |
| Opción B v1 (reglas <8, >15) | 75% | 3/20 | Primer híbrido. C02 perdido por orden de reglas |
| Opción B v2 (+comparar, +"y") | 85% | 2/20 | Reorden: ≥15 antes que "y" |
| Opción B final (threshold <7) | 86% | 2/20 | Threshold ajustado |
