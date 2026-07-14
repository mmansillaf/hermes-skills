# Groq Batch Extraction Results — Jun 2026

## Test realizado: 100 docs LABORAL vía Groq Llama 3.1 8B Instant

**Fecha:** 6 Junio 2026
**API Key:** Groq Developer Plan
**Modelo:** `llama-3.1-8b-instant`
**Prompt:** Mismo que Qwen 7B local (SYSTEM_PROMPT + PROMPT_TPL con JSON schema)
**Timeout:** 60s por request
**Parser:** Mismo reparador de JSON que el local

## Resultados

| Métrica | Valor |
|---------|-------|
| Documentos procesados | 98/100 (98%) |
| Tiempo total | 118.8s (1.9 min) |
| Promedio por doc | 1.2s |
| Velocidad | 49.5 docs/min |
| Errores | 2 (JSON truncado, reparador no atrapó) |
| Costo estimado | ~$0.01 |

## Comparación local vs Groq

| Métrica | Qwen 7B local | Groq Llama 3.1 8B | Mejora |
|---------|:-------------:|:-----------------:|:------:|
| 100 docs | ~2.4 hr | **1.9 min** | **76x** |
| Tiempo/doc | 86s | **1.2s** | **71x** |
| Tasa éxito JSON | 87% | **98%** | **+11%** |
| Costo 100 docs | $0 (elec.) | **~$0.01** | — |

## Costos proyectados

Basado en tokens reales: ~1,700 input + ~360 output por doc.

| Escenario | Docs | Costo normal | Batch -50% | Tiempo paralelo 50x |
|-----------|:----:|:------------:|:----------:|:-------------------:|
| LABORAL | 111,679 | $13 | $7 | ~3 min |
| LAB+COM+FAM | 221,024 | $25 | $13 | ~5 min |
| Solo Sentencias | 243,288 | $28 | $14 | ~6 min |
| Todo valor (562K) | 562,297 | $64 | $32 | ~14 min |

## API Key segura

Usar variable de entorno, nunca hardcodear:
```bash
export GROQ_API_KEY="gsk_..."
```

## Modelos disponibles en Groq (Jun 2026)

| Model ID | TPS | Input $/1M | Output $/1M | Tipo |
|----------|:---:|:----------:|:-----------:|:----:|
| llama-3.1-8b-instant | 560 | $0.05 | $0.08 | Producción |
| openai/gpt-oss-20b | 1,000 | $0.075 | $0.30 | Producción |
| meta-llama/llama-4-scout-17b-16e-instruct | 750 | $0.11 | $0.34 | Preview |
| llama-3.3-70b-versatile | 280 | $0.59 | $0.79 | Producción |
| qwen/qwen3-32b | 400 | $0.29 | $0.59 | Preview |
