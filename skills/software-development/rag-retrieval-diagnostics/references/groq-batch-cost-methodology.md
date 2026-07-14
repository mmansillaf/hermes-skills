# Metodología para Calcular Costos de Groq Batch API desde Facturas Reales

**Fecha:** 2026-05-01 | **Referencia:** sesión de procesamiento 65K docs

## Procedimiento

1. **Obtener facturas como PDF** y extraer texto con PyMuPDF (`import fitz`)
2. **Extraer subtotales:** `re.findall(r'Subtotal[^$]*\$\s*([\d,]+\.?\d*)', text)`
3. **Extraer modelos usados:** `re.findall(r'(llama[\w.-]+)', text)` — detectar si se usaron modelos caros (maverick) o baratos (8b-instant)
4. **Separar Batch de Sync:** Las facturas mezclan ambos. El batch usa `llama-3.1-8b-instant`, la sync usa `llama-3.3-70b-versatile`. Identificar por modelo.
5. **Calcular costo real por documento:** `costo_batch / docs_procesados`

## Caso real (01-may-2026)

Facturas analizadas: 6 PDFs (Feb-Abr 2026), total facturado: $122.74

| Uso | Modelo | Costo estimado |
|-----|--------|---------------|
| Sync API (respuestas + tests) | llama-3.3-70b-versatile, llama-4-maverick | ~$122.02 |
| Batch API (ingesta 18K docs) | llama-3.1-8b-instant | ~$0.72 |

**Costo real por documento (batch):** $0.72 / 18,694 = $0.000039/doc = **$0.04 por 1,000 documentos**

**Proyección para 65K docs nuevos:** 65,000 × $0.000039 = **$2.54**

**Advertencias:**
- Factura duplicada detectada (Mar 06 aparece 2 veces con idéntico monto)
- Uso accidental de llama-4-maverick en Feb (modelo caro para pruebas)
- La sync API domina el gasto (~99% del total)
