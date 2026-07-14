# System Prompt Anti-Derrotismo — Rewrite (02-may-2026)

## Problema

13/100 queries en la batería contenían frases prohibidas: "no se encontró", "no hay información", "lamentablemente", "desafortunadamente". El LLM respondía con derrota incluso cuando SÍ había datos relevantes.

## Causa raíz

DOS prompts tenían instrucciones de "honestidad" que el LLM interpretaba como permiso para lenguaje derrotista:

**Prompt 1** (`api_rest.py` línea 1360):
```
- Si no hay normas relevantes, dilo honestamente.
```

**Prompt 2** (`orchestrator_rag_v3.py` línea 820):
```
1. Si el contexto no contiene la respuesta, indícalo claramente
```

Las reglas ANTI-CONTRADICCIÓN existentes eran reactivas (no digas X si tienes Y) — insuficientes.

## Fix: Reemplazar por estrategia constructiva

### Prompt 1 (`api_rest.py`) — Antes vs Después

**Antes:**
```
- Si no hay normas relevantes, dilo honestamente.
```

**Después:**
```
- SIEMPRE intenta responder con la información disponible, aunque sea parcial.
- NUNCA uses frases como: "no se encontró", "no hay información", "lamentablemente", "desafortunadamente", "no está disponible", "no se proporciona".
- Si la información es limitada, usa: "Según los datos disponibles..." y describe lo que SÍ hay.
- Si genuinamente no hay NINGUNA norma relacionada, responde ÚNICAMENTE: "No se encontraron normas específicas sobre este tema en la base de datos de El Peruano."
```

### Prompt 2 (`orchestrator_rag_v3.py`) — Antes vs Después

**Antes:**
```
REGLAS IMPORTANTES:
1. Si el contexto no contiene la respuesta, indícalo claramente
5. Si hay información insuficiente, indica qué información adicional necesitarías
```

**Después:**
```
REGLAS IMPORTANTES:
1. SIEMPRE intenta construir una respuesta con los datos disponibles, aunque sean parciales
5. Si hay poca información, enfócate en describir lo que SÍ está disponible

FRASES PROHIBIDAS — NUNCA uses ninguna de estas:
- "no se encontró" / "no se encuentra"
- "no hay información" / "no tengo información"
- "lamentablemente" / "desafortunadamente" / "por desgracia"
- "no está disponible" / "no se proporciona"
- "no puedo proporcionar" / "no es posible determinar"

En su lugar, SIEMPRE comienza con:
- "Según las normas encontradas..." o "Los datos disponibles muestran..."
- Si el contexto es limitado: "La información disponible indica que..."
```

## Resultado

| Query | Antes | Después |
|-------|-------|---------|
| "renuncias Poder Judicial" | "no se encontró información" (fin) | "Según los datos disponibles... Sin embargo, se encontraron normas relacionadas..." + cita |
| "sanciones Contraloría" | "no hay información suficiente" | "Según los datos disponibles, la Contraloría ha establecido..." + Resolución Nº 709-2024-CG |
| "minería asteroides" (trampa) | "no se encontró" (fin) | "no se encontraron normas específicas... Sin embargo, DS 003-2025-IN..." |

El patrón cambió de **derrota → silencio** a **"no hay específico PERO sí hay relacionado"**.

## Bonus: max_tokens aumentados

```python
# orchestrator_rag_v3.py línea 851
max_tokens=1200 if complexity == "high" else 800  # antes: 1000/600
```
