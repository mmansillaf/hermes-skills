# DeepSeek-R1-0528-Qwen3-8B vs Qwen3-8B vs DeepSeek-R1-Distill-Qwen-7B

Comparativa de modelos 7-8B para hardware con VRAM limitada (T1000 4GB, RTX 3000+).

## Benchmarks oficiales (fuente: DeepSeek HF)

| Benchmark | Qwen3-8B | DS-R1-Distill-Qwen-7B | **DS-R1-0528-Qwen3-8B** |
|-----------|----------|----------------------|--------------------------|
| AIME 2024 | 76.0% | 55.5% | **86.0%** |
| AIME 2025 | 67.3% | — | **76.3%** |
| HMMT Feb 25 | — | — | **61.5%** |
| GPQA Diamond | 62.0% | 49.1% | 61.1% |
| LiveCodeBench | — | — | 60.5% |

DS-R1-0528-Qwen3-8B **iguala a Qwen3-235B-A22B** (235B params) en AIME 2024 (86% vs 85.7%).

## Diferencias clave

| Aspecto | Qwen3-8B | DS-R1-Distill-Qwen-7B | DS-R1-0528-Qwen3-8B |
|---------|----------|----------------------|---------------------|
| Base | Qwen3 (2025) | Qwen2.5 (2024) | Qwen3 (2025) |
| Thinking | Híbrido (on/off) | Siempre (~12K tokens) | Siempre (~23K tokens) |
| Contexto | 128K | ~32K | 128K |
| Hallucinaciones | Normal | Normal | -45% |
| System prompt | Sí | No | Sí |
| Function calling | Bueno | Limitado | Tau-Bench 53.5/63.9 |
| GGUF Q4_K_M | ~5.0 GB | ~4.5 GB | ~5.0 GB |

## Recomendación por hardware

### P53 + T1000 4GB (sin Tensor Cores)
- **Ganador:** DS-R1-0528-Qwen3-8B Q4_K_M (-ngl 20, ~8-15 tok/s)
- Alternativa: Qwen3-8B Q4_K_M (si se necesita modo non-thinking para respuestas rápidas)
- **No recomendar:** DS-R1-Distill-Qwen-7B (obsoleto, superado por 30% en AIME)

### P53 + RTX 3000+ (6GB+ VRAM, con Tensor Cores)
- DS-R1-0528-Qwen3-8B Q4_K_M: GPU completo (-ngl 99), ~40-60 tok/s
- DeepSeek-R1-Distill-Qwen-14B Q4_K_M: Offload parcial, ~15-25 tok/s

### T14 Gen 1 (MX330 2GB, CPU only)
- Qwen3-8B Q4_K_M (CPU only): ~2-5 tok/s, modo non-thinking para tareas simples
- DS-R1-0528-Qwen3-8B: Demasiado lento para uso interactivo (~1-2 tok/s CPU only)

## Parámetros recomendados (P53 + T1000 4GB)

```bash
# DS-R1-0528-Qwen3-8B Q4_K_M
llama-server \
  -m DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf \
  --host 0.0.0.0 --port 8080 \
  -ngl 20 \
  -c 16384 \
  -t 6 \
  --temp 0.6 --cache-prompt

# Qwen3-8B Q4_K_M (alternativa versátil)
llama-server \
  -m Qwen3-8B-Q4_K_M.gguf \
  --host 0.0.0.0 --port 8080 \
  -ngl 20 \
  -c 32768 \
  -t 6 \
  --temp 0.6 --cache-prompt
```

## Veredicto

DS-R1-0528-Qwen3-8B es el modelo 8B más inteligente disponible. La desventaja: siempre piensa (23K tokens de pensamiento promedio), sin modo rápido. Qwen3-8B es mejor para uso general por su modo híbrido.

Fuente: https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B
