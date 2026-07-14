# Hermes Token Tracking — Patrón de monitoreo de consumo

## Motivación

Hermes no expone una API para consultar cuántos tokens ha consumido en una sesión. Los subagentes (`delegate_task`) sí reportan `input` y `output` al completar, pero la conversación principal (turnos usuario↔agente, razonamiento interno) no es medible directamente.

## Solución: Tracker SQLite manual

Script `hermes_token_tracker.py` que persiste sesiones en SQLite:

```python
# Registrar sesión
python3 hermes_token_tracker.py add <session_id> <modelo> <input_tokens> <output_tokens> [notas]

# Ver resumen
python3 hermes_token_tracker.py summary

# Ver total acumulado
python3 hermes_token_tracker.py total
```

## Flujo por sesión

1. Al inicio: el agente anota el modelo primario (ej: `deepseek-v4-pro`)
2. Durante: acumula tokens de subagentes (reportados por `delegate_task`)
3. Al final: estima tokens de conversación principal (~10-15K por turno) y guarda

## Precios de referencia (DeepSeek, mayo 2026)

| Modelo | Input / 1M | Output / 1M |
|--------|-----------|-------------|
| deepseek-v4-pro | $0.89 | $1.79 |

## Ejemplo real — Sesión 2026-05-05

```
Subagentes:  4,208,173 input + 98,757 output = 4,306,930 tokens
Conversación:   500,000 input + 50,000 output =   550,000 tokens (est)
TOTAL:       4,708,173 input + 148,757 output = 4,856,930 tokens
Costo: $4.46 USD
```

## Paths

- Script: `hermes_token_tracker.py` (raíz del proyecto)
- DB: `data/hermes_tokens.db`
