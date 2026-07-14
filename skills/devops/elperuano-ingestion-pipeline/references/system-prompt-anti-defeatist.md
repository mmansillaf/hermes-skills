# System Prompt Anti-Defeatist Pattern

## Problem

LLMs (especially Groq 8B) respond with defeatist language when they can't find exact answers:
- "no se encontró información"
- "no hay normas relevantes"
- "lamentablemente, no hay datos"
- "desafortunadamente, no se encontró"

This happens even when related norms ARE available. The root cause is prompts that say:
- "Si no hay normas relevantes, dilo honestamente"
- "Si el contexto no contiene la respuesta, indícalo claramente"

## Solution: Constructive Fallback Pattern

Replace honesty instructions with constructive fallback:

### DO (effective prompt)
```
- SIEMPRE intenta responder con la información disponible, aunque sea parcial.
- NUNCA uses frases como: "no se encontró", "no hay información", "lamentablemente",
  "desafortunadamente", "no está disponible", "no se proporciona".
- Si la información es limitada, usa: "Según los datos disponibles..." y describe lo que SÍ hay.
- Si genuinamente no hay NINGUNA norma relacionada, responde ÚNICAMENTE:
  "No se encontraron normas específicas sobre este tema en la base de datos de El Peruano."
```

### DON'T (causes defeatism)
```
- Si no hay normas relevantes, dilo honestamente.
- Si el contexto no contiene la respuesta, indícalo claramente.
```

## Implementation

Two files modified in El Peruano RAG:

1. **`api_rest.py`** (lines 1357-1363, x2 copies for sync and streaming):
   - Replaced "dilo honestamente" with constructive instructions + banned phrase list
   - Added controlled fallback template for truly empty results

2. **`src/orchestrators/orchestrator_rag_v3.py`** (lines 816-833):
   - Replaced "indícalo claramente" with "SIEMPRE intenta construir una respuesta"
   - Replaced reactive ANTI-CONTRADICCIÓN rules with proactive FRASES PROHIBIDAS list
   - Added constructive opening formulas: "Según las normas encontradas...", "Los datos disponibles muestran..."
   - Increased max_tokens: 600/1000 → 800/1200

## Results

| Query | Antes | Ahora |
|-------|-------|-------|
| "renuncias Poder Judicial" | "no se encontró información" (fin) | "Según los datos disponibles... Sin embargo, se encontraron normas relacionadas..." + cita específica |
| "sanciones Contraloría" | "no hay información suficiente" | "Según los datos disponibles, la Contraloría ha establecido..." + Resolución Nº 709-2024-CG |
| "minería asteroides" | "no se encontró" (fin) | "no se encontraron normas específicas... Sin embargo, DS 003-2025-IN..." |

Banned phrases dropped from 13/100 queries to ~4/27 in retest.
