# Estrategia de Documentos de Prueba para RAG Legal

**Propósito:** Crear documentos ficticios con contradicciones intencionales para validar el pipeline multi-agente (comparación, detección de contradicciones, análisis de riesgos).

---

## Principios de Diseño

1. **Cada documento debe tener al menos un "gemelo"** — otro documento sobre el mismo tema pero con variaciones intencionales.
2. **Las contradicciones deben ser graduales**: algunas obvias (plazo: 12 vs 6 meses), otras sutiles (tasa de interés: 2% vs 1% mensual).
3. **Incluir "pistas falsas"**: datos que parecen relevantes pero no lo son, para probar la precisión del retrieval.
4. **Cubrir múltiples tipos documentales**: contratos, resoluciones, informes, dictámenes.

---

## Clases de Contradicciones

| Clase | Ejemplo | Dificultad |
|-------|---------|------------|
| **Plazo** | 12 meses vs 6 meses | Fácil |
| **Monto** | S/12,000 vs S/8,500 | Fácil |
| **Tasa** | 2% vs 1% mensual | Media |
| **Confidencialidad** | 2 años vs 3 años post-terminación | Media |
| **Propiedad intelectual** | Exclusiva del cliente vs conjunta | Media |
| **Responsabilidad** | Seguro S/500k vs sin seguro | Media |
| **Resolución** | 15 días para subsanar vs resolución inmediata | Difícil |
| **Jurisdicción** | Tribunales de Lima vs arbitraje | Difícil |
| **Definiciones** | Mismo término definido de forma distinta | Difícil |

---

## Estructura de Cada Documento

Usar formato de texto plano con estructura legal reconocible:

```txt
TITULO DEL DOCUMENTO
====================

CLAUSULA PRIMERA: [TITULO]
Texto de la clausula...

CLAUSULA SEGUNDA: [TITULO]
Texto de la clausula...
```

Para resoluciones:

```txt
RESOLUCION DE ALCALDIA N° XXX-2026
===================================

CONSIDERANDO:

Primero: Que, ...
Segundo: Que, ...

SE RESUELVE:

Articulo 1°.- ...
```

---

## Ejemplo: Par de Contratos con Contradicciones

### Contrato A (servicios profesionales)
- Plazo: 12 meses, renovación automática
- Honorarios: S/12,000/mes, pago en 5 días hábiles
- Mora: 2% mensual, aplica tras 15 días de atraso
- Confidencialidad: 2 años post-terminación
- PI: Exclusiva del cliente
- Seguro: S/500,000 de responsabilidad civil
- Resolución: 15 días para subsanar
- Jurisdicción: Tribunales de Lima

### Contrato B (locación de servicios - "versión revisada")
| Campo | Contrato A | Contrato B |
|-------|-----------|-----------|
| Plazo | 12 meses + auto-renovación | 6 meses, sin renovación |
| Honorarios | S/12,000 | S/8,500 |
| Pago | 5 días hábiles | 10 días calendario |
| Mora | 2% mensual | 1% mensual |
| Confidencialidad | 2 años | 3 años |
| PI | Exclusiva del cliente | Conjunta |
| Seguro | S/500k | Sin seguro |
| Resolución | 15 días de subsanación | Inmediata |
| Jurisdicción | Tribunales | Arbitraje CCL |

---

## Cobertura de Intenciones por Documento

| Documento | QA | Resumen | Comparar | Contradicciones | Analizar |
|-----------|----|---------|----------|----------------|---------|
| Contrato A | Sí | Sí | Sí (con B) | Sí (con B) | Sí |
| Contrato B | Sí | Sí | Sí (con A) | Sí (con A) | Sí |
| Resolución | Sí | Sí | — | Sí (con informe) | Sí |
| Informe legal | Sí | Sí | — | Sí (con resolución) | Sí |

---

## Estrategia de Validación

1. **QA factual** — Preguntar sobre un dato concreto (ej: "cuánto es el honorario?")
2. **Resumen** — Pedir resumen de cada documento, verificar que mencione todos los puntos clave
3. **Comparación** — Pedir comparar A vs B, verificar que encuentre ≥8 de las 9 contradicciones
4. **Contradicciones** — Pedir detectar contradicciones, verificar que mencione al menos 5
5. **Análisis** — Pedir análisis de riesgos, verificar que identifique los problemas legales
6. **Citas** — Verificar que cada afirmación tenga una cita a la fuente exacta
