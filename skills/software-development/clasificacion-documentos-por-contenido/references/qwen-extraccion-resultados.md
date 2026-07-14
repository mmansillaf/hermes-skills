# Resultados de Extracción Estructurada con Qwen 2.5 7B

**Fecha prueba:** 6 Junio 2026
**Hardware:** ThinkPad P53 | i7-9850H (6C/12T) | Quadro T1000 4GB | 46GB RAM
**Modelo:** Qwen 2.5 7B Q4_K_M (4.4 GB, n_gpu_layers=20, n_threads=12, ctx=8192)

## Resultados multi-formato (4 muestras)

| # | Archivo | Formato | Tiempo | Tok/s | JSON |
|---|---------|---------|--------|-------|------|
| 1 | Resolución costos procesales | PDF | 37.3s | 11.1 | ✅ |
| 2 | Resolución incautación garantía | PDF | 41.2s | 11.1 | ✅ |
| 3 | Contrato arrendamiento | DOCX | 22.8s | 11.0 | ✅ |
| 4 | Devolución archivo (legacy) | DOC | 25.7s | 9.2 | ✅ |

**Tasa de éxito JSON: 4/4 (100%)**
**Promedio: 31.8s/doc | 10.7 tok/s**

## Warmup

| Consulta | Tiempo | Tok/s | Nota |
|----------|--------|-------|------|
| #1 | 18.2s | 3.5 | Carga KV cache |
| #2 | 4.9s | 12.7 | Cache caliente |
| #3 | 4.9s | 12.8 | Estable |

## Estimaciones

| Lote | Sin chunking (32s/doc) | Con chunking (64s/doc) |
|------|----------------------|----------------------|
| 1,000 | 8.8 hr | 17.6 hr |
| 10,000 | 3.7 días | 7.4 días |
| 50,000 | 18.4 días | 36.8 días |
| 500,000 | 183.7 días | ~368 días |

## Pitfalls encontrados

1. **n_gpu_layers=24 → OOM.** Forzar 20 para Quadro T1000 4GB.
2. **response_format json_object no funciona en llama.cpp.** Solo OpenAI/Groq.
3. **catdoc no instalado por defecto en Ubuntu 24.04.** `sudo apt-get install -y catdoc antiword`.
4. **python-docx no abre .doc binario.** Usar catdoc o antiword.
5. **Prompt JSON colisiona con .format()** — usar f-strings, no .format().
