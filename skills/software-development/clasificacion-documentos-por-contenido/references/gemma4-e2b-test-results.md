# Gemma 4 E2B — Test Results on Quadro T1000 4GB

## Hardware
- GPU: Quadro T1000 (3,903 MiB total, 4,096 MiB physical)
- CPU: i7-9850H (6C/12T)
- RAM: 46 GB
- OS: Ubuntu 24.04

## Modelo
- Repo: `unsloth/gemma-4-E2B-it-GGUF`
- Archivo: `gemma-4-E2B-it-Q4_K_M.gguf`
- Tamaño: 2.9 GB (Q4_K_M, MoE con PLE, ~2.4B params activos, ~5B totales)
- Contexto nativo: 128K

## Pruebas de carga

| Intento | n_gpu_layers | Contexto | VRAM libre | Resultado |
|---------|-------------|----------|-----------|-----------|
| 1 | 30 | 8192 | 3,903 MB total | ❌ OOM: "unable to allocate CUDA0 buffer of size 1295956608" (1.2 GB adicionales) |
| 2 | 20 | 4096 | 3,903 MB total | ❌ OOM: "unable to allocate CUDA0 buffer of size 1028540800" (981 MB adicionales) |
| 3 | 12 | 4096 | 313 MB (Gemma process ocupaba VRAM) | ❌ OOM |
| 4 | 12 | 4096 | 4,090 MB (VRAM limpia) | ✅ Server OK |

**Causa raíz:** El modelo Q4_K_M pesa 2.9 GB, pero llama.cpp necesita buffers CUDA adicionales para:
- KV cache (~500 MB para 4096 contexto)
- Tensores intermedios durante forward pass
- Overhead del servidor

Total necesario para Gemma 4 E2B Q4_K_M con -ngl 30: ~4.5 GB. La Quadro T1000 tiene solo 4 GB.

## Test de inferencia (4 muestras multi-formato)

Server: `-ngl 12 -t 12 -c 4096 -ub 512 --mlock --reasoning off`

| # | Archivo | Formato | Tiempo | Tok/s | JSON |
|---|---------|---------|--------|-------|------|
| 1 | res_costos_procesales.pdf | PDF | 64.4s | 9.6 | ✅ |
| 2 | res_incautacion.pdf | PDF | 64.1s | 9.6 | ✅ |
| 3 | contrato.docx | DOCX | 41.0s | 8.8 | ✅ |
| 4 | res_archivo.doc | DOC | 22.9s | 13.7 | ✅ |

**Métricas:** Promedio: 48.1s/doc | Total: 192.4s/4docs | Tasa éxito JSON: 100%

## Comparativa vs Qwen 7B

| Métrica | Qwen 7B (-ngl 20) | Gemma 4 E2B (-ngl 12) | Diferencia |
|---------|-------------------|----------------------|------------|
| Promedio/doc | 31.8s | 48.1s | Qwen 51% más rápido |
| Tok/s | 10.7 | 9.9 | Qwen 8% más rápido |
| JSON válido | 4/4 (100%) | 4/4 (100%) | Empate |
| Thinking blocks | N/A | 0 (deshabilitado) | — |

## Conclusión

Gemma 4 E2B es **más lento que Qwen 7B** en este hardware porque:
1. Solo 12/~30 layers caben en GPU (offloading mata velocidad MoE)
2. Genera más tokens de completion (~475 vs ~315) — respuestas más detalladas pero más lentas
3. Contexto limitado a 4096 (vs 8192 de Qwen)

**No se recomienda Gemma 4 E2B para Quadro T1000 4GB.** Con GPU de 6 GB+ VRAM (RTX 3060/4060) donde cupiera completo, su arquitectura MoE probablemente sería 2-3x más rápida que Qwen 7B.
