# Groq Batch API — Costos Reales (Facturas)

**Sistema:** El Peruano RAG | **Fecha:** 2026-05-01

## Facturas Analizadas

6 facturas de Groq (GROQ_Invoice/) entre Feb-Abr 2026:

| Factura | Fecha | Subtotal | Modelos usados |
|---------|-------|----------|----------------|
| GROQ-TAAS-202602-212117 | Feb 06 | $0.01 | llama-3.3-70b, llama-4-maverick |
| GROQ-TAAS-202602-229896 | Feb 25 | $8.83 | llama-3.3-70b, llama-4-maverick |
| GROQ-TAAS-202603-252453 | Mar 06 | $53.59 | llama-3.1-8b, llama-3.3-70b, llama-4-maverick |
| GROQ-TAAS-202603-252453 (dup) | Mar 06 | $53.59 | ⚠️ Duplicado |
| GROQ-TAAS-202603-254455 | Mar 09 | $36.75 | llama-3.1-8b, llama-3.3-70b |
| GROQ-TAAS-202604-269954 | Abr 06 | $23.56 | llama-3.1-8b, llama-3.3-70b |

## Desglose

- **Total facturado:** $122.74
- **Batch API (ingesta 18K docs):** ~$0.72
- **Sync API (respuestas, tests):** ~$122.02 (99% del gasto)

El costo real de ingesta es minusculo. El grueso del gasto es la API sync para respuestas a consultas.

## Proyeccion 75K docs pendientes

- Input: 67.7M tokens x $0.025/M = $1.69
- Output: 30.1M tokens x $0.04/M = $1.20
- **Costo Batch API: $2.89**

Costo por documento: $0.000039 (menos de 4 centavos por 1,000 normas).
