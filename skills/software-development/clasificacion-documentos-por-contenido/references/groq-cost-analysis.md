# Groq vs Local: Análisis de Costos para Extracción Batch

## Creación

- Junio 2026 — datos reales de prueba con Qwen 7B local + Groq API
> Actualización: 6 Jun 2026 — datos reales de 7 docs LABORAL procesados con Qwen 7B

## Datos base (reales de la prueba)

- **Tokens input promedio por doc:** 1,700 (de 7 docs LABORAL reales)
- **Tokens output promedio por doc:** 360 (de 7 docs)
- **Tasa de éxito JSON:** 87.5% (7/8) sin reparador; 100% con reparador

## Costos Groq

### Modelos disponibles

| Modelo | TPS | $/1M input | $/1M output | Ideal para |
|--------|:---:|:--------:|:---------:|-----------|
| **Llama 3.1 8B Instant** | 840 | $0.05 | $0.08 | Mejor balance costo/calidad |
| GPT OSS 20B | 1,000 | $0.075 | $0.30 | Más rápido, más caro |
| Llama 4 Scout 17Bx16E | 594 | $0.11 | $0.34 | MoE, buena calidad |
| Qwen3 32B | 662 | $0.29 | $0.59 | Mejor calidad, mayor costo |

### Costos por escenario (modelo: Llama 3.1 8B Instant)

| Escenario | Docs | **Normal** | **Batch -50%** | Tiempo secuencial | Tiempo paralelo 50x |
|-----------|:----:|:---------:|:-------------:|:----------------:|:------------------:|
| Test (5 docs) | 5 | <$0.01 | — | ~10s | — |
| Batch 100 | 100 | $0.01 | — | ~3 min | ~10s |
| Batch 1,000 | 1,000 | $0.11 | — | ~30 min | ~1 min |
| Solo LABORAL | 111,679 | $12.71 | $6.36 | 62 hr | ~1 hr |
| LAB+COM+FAM | 221,024 | $25.15 | $12.58 | 123 hr | ~2 hr |
| Solo Sentencias | 243,288 | $27.68 | $13.84 | 135 hr | ~1.5 hr |
| CIVIL+LAB+COMERCIAL | 386,259 | $43.96 | $21.98 | 215 hr | ~4 hr |
| **Todo valor jurídico** | **562,297** | **$63.99** | **$31.99** | **312 hr** | **~6 hr** |
| **Todo (PDF+DOC)** | **652,539** | **$74.26** | **$37.13** | **363 hr** | **~7 hr** |

### Costos Batch API de Groq

- 50% descuento sobre precio normal
- Procesamiento asíncrono en 24-48 horas
- Ideal para lotes de 10K+ docs donde no se requiere inmediatez

## Comparativa vs Local

| Opción | 562,297 docs (valor jurídico) | Costo | Tiempo |
|--------|:----------------------------:|:----:|:------:|
| **Groq paralelo 50x** | | **$64** | **~6 hr** |
| **Groq Batch API** | | **$32** | **24-48 hr** |
| Qwen 7B local | | ~$50 electricidad | ~560 días |
| Qwen 3B local | | ~$17 electricidad | ~195 días |

## API Key

Obtener en https://console.groq.com/ (gratis, con crédito inicial).
Formato: `gsk_...`
Configurar como variable de entorno: `export GROQ_API_KEY=gsk_tu_key`

## Diferencia clave: paralelismo

Groq permite 50+ requests concurrentes sin penalización significativa.
El LLM local (Qwen 7B) solo procesa 1 request a la vez por limitación de VRAM.

Factor de diferencia real: **~2,000x** más rápido via Groq para lotes grandes.
