# Context Length: The #1 CPU Inference Bottleneck

Real-world finding from i7-10510U (4C/8T, 15W TDP) + Qwen2.5-Coder-7B Q4_K_M:

## The mistake: `-c 65536` on a CPU-only 7B model

Setting context to 65K on a model this size running CPU-only is catastrophic. The KV cache alone needs ~10-16GB, and the attention mechanism is O(n²) — every generation step must attend over all 65K positions.

## Measured impact on i7-10510U

**With simple prompt (40 tokens → 17 response):**
- Prompt: 3.5 tok/s, Generation: 1.9 tok/s → 14.5s total (acceptable)

**With accumulated conversation context (~19K-21K tokens):**
| Context | Response | Total time | Avg tok/s |
|---------|----------|------------|-----------|
| 19K in → 101 out | 8 min | 485s | ~0.2 out/s |
| 19K in → 371 out | 15 min | 896s | ~0.4 out/s |
| 20K in → 683 out | 67 min | 4002s | ~0.17 out/s |
| 20.5K in → 576 out | 57 min | 3420s | ~0.17 out/s |
| 21K in → 576 out | 45 min | 2683s | ~0.21 out/s |

At 20K+ context, even with 100% KV cache hits, the attention mechanism kills throughput.

## Why context is worse on CPU than GPU

| Factor | CPU | GPU |
|--------|-----|-----|
| Attention O(n²) | Serialized, no parallel | Massively parallel (CUDA cores) |
| Memory bandwidth | ~40 GB/s (DDR4) | 200+ GB/s (GDDR) |
| KV cache access | Contends with model weights | Separate VRAM |

## Recommended context limits by scenario

| Hardware | Model size | Max usable context |
|----------|-----------|-------------------|
| i7-10510U (4C) | 7B Q4 | 2048-4096 |
| i7-10510U (4C) | 3B Q4 | 4096-8192 |
| i7-10510U (4C) | 1.5B Q8 | 8192-16384 |
| i7-10510U (4C) | 0.5B Q8 | 16384+ (maybe) |

## The rule of thumb

**For CPU inference, context length matters MORE than quantization level.** Running Q8_0 with 4K context is far more usable than Q4_K_M with 65K context, even though Q8 is "slower per token." The attention cost dominates.
