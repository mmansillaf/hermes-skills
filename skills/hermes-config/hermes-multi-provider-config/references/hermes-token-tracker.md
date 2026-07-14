# Hermes Token Tracker

Para medir el consumo de tokens del propio Hermes Agent (no de la app RAG),
existe `hermes_token_tracker.py` en el proyecto El Peruano RAG.

A diferencia del token tracker de la app RAG que mide llamadas a Groq,
este script persiste el consumo de subagentes Hermes (DeepSeek V4-Pro).

## Uso

```bash
cd PeruanoSearchEngine02

# Registrar una sesión
python3 hermes_token_tracker.py add <session_id> <input_tokens> <output_tokens> [notas]

# Ver resumen
python3 hermes_token_tracker.py summary

# Ver total acumulado
python3 hermes_token_tracker.py total

# Simulación de sesión actual
python3 hermes_token_tracker.py simulate
```

## Precios (DeepSeek V4-Pro, mayo 2026)

| Modelo | Input/1M | Output/1M |
|--------|----------|-----------|
| deepseek-v4-pro | $0.89 | $1.79 |

## Notas

Los subagentes (`delegate_task`) reportan sus tokens exactos en `tokens.input` y `tokens.output`.
La conversación principal (turnos del agente) debe estimarse (~500K por sesión de ~50 turnos).

DB: `data/hermes_tokens.db`