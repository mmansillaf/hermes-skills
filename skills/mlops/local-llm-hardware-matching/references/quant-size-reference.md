# Quant Size Reference Table

Exact GGUF file sizes for popular local LLM model variants, sourced from Hugging Face Hub tree API and local-app pages. Use this table to quickly determine if a model fits available RAM without re-fetching from Hub.

## 7B-class models (~7.6B params, Qwen2.5 architecture)

| Quant | File Size | Min Free RAM | Best for |
|-------|-----------|-------------|----------|
| Q2_K | 3.02 GB | ~5 GB | Tight budgets, quality loss visible |
| Q3_K_M | 3.81 GB | ~6 GB | Usable but degraded |
| Q4_0 | 4.43 GB | ~7 GB | Fast path on some CPUs |
| **Q4_K_M** | **4.68 GB** | **~7.5 GB** | **Best all-around balance** |
| Q5_0 | 5.32 GB | ~8 GB | Good quality |
| **Q5_K_M** | **5.44 GB** | **~8.5 GB** | **Best for coding/technical work** |
| Q6_K | 6.25 GB | ~9.5 GB | Very high quality |
| Q8_0 | 8.10 GB | ~12 GB | Near-lossless |

**Model variants using these sizes:**
- Qwen2.5-7B-Instruct (official: `Qwen/Qwen2.5-7B-Instruct-GGUF`)
- Qwen2.5-Coder-7B-Instruct (official: `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`)

## 8B-class models (Qwen3-8B — 8.2B params, newest generation)

| Quant | File Size | Min Free RAM | Best for |
|-------|-----------|-------------|----------|
| **Q4_K_M** | **5.03 GB** | **~8 GB** | **Default choice** |
| Q5_0 | 5.72 GB | ~9 GB | Good quality |
| Q5_K_M | 5.85 GB | ~9 GB | High quality |
| Q6_K | 6.73 GB | ~10.5 GB | Very high quality |
| Q8_0 | 8.71 GB | ~13 GB | Near-lossless |

**Model variants:** Qwen3-8B (official: `Qwen/Qwen3-8B-GGUF`)

**Why Qwen3-8B instead of Qwen2.5-7B?** Qwen3 supports thinking/non-thinking mode toggle, native tool-calling for agents, and 100+ languages. At Q4_K_M (5 GB), it's only slightly larger than Qwen2.5-7B Q5_K_M (5.4 GB) but significantly more capable.

## 14B-class models (~14.7B params)

| Quant | File Size | Min Free RAM | Best for |
|-------|-----------|-------------|----------|
| Q2_K | 5.77 GB | ~9 GB | Heavily degraded |
| Q3_K_M | 7.34 GB | ~11 GB | Acceptable for 32GB systems |
| **Q4_K_M** | **8.99 GB** | **~13 GB** | **Best balance** |
| Q5_K_M | 10.5 GB | ~15 GB | High quality |
| Q6_K | 12.1 GB | ~17 GB | Very high quality |
| Q8_0 | 15.7 GB | ~21 GB | Near-lossless |
| F16 | 29.5 GB | ~37 GB | Full precision |

**Model variants:**
- Qwen2.5-14B-Instruct (official: `Qwen/Qwen2.5-14B-Instruct-GGUF`)
- Qwen2.5-Coder-14B-Instruct (unsloth: `unsloth/Qwen2.5-Coder-14B-Instruct-GGUF`)

**Note:** 14B at Q4_K_M (~9 GB) plus 32K context KV cache (~14 GB) totals ~23 GB — fits in 32 GB but leaves only ~6 GB for OS. For 8K context the KV cache drops to ~4.5 GB (total ~13.5 GB) which is comfortable.

## 32B-class models (~32.5B params)

| Quant | File Size | Min Free RAM | Best for |
|-------|-----------|-------------|----------|
| Q2_K | 12.3 GB | ~17 GB | Fits 32 GB but quality degraded |
| **Q3_K_M** | **15.9 GB** | **~21 GB** | **Best for 32 GB budget** |
| Q4_K_M | 19.9 GB | ~26 GB | Tight in 32 GB, better for 48 GB+ |

**Model variants:**
- Qwen2.5-32B-Instruct (official: `Qwen/Qwen2.5-32B-Instruct-GGUF`)
- Qwen2.5-Coder-32B-Instruct (unsloth: `unsloth/Qwen2.5-Coder-32B-Instruct-GGUF`)

## 8B-class models (other families)

### Llama-3.1-8B-Instruct

| Quant | File Size | Notes |
|-------|-----------|-------|
| Q4_K_M | ~4.9 GB | Good general model |
| Q5_K_M | ~5.7 GB | Better quality |

### Gemma-2-9B-it

| Quant | File Size | Notes |
|-------|-----------|-------|
| Q4_K_M | 5.76 GB | Google model, very capable |
| Q5_K_M | 6.65 GB | High quality |

**Warning:** Gemma-2 does NOT support system prompts. Use a different model if you need system instructions.

## Quick formula

For any model not in this table, estimate file size as:

```
file_size_GB ≈ params_B × 0.5 + 1.0  (Q4_K_M)
file_size_GB ≈ params_B × 0.6 + 0.5  (Q5_K_M)
file_size_GB ≈ params_B × 0.8 + 0.5  (Q6_K)
file_size_GB ≈ params_B × 1.0        (Q8_0)
```

Then add KV cache:
```
total_RAM_needed ≈ file_size_GB × 1.2 + context_K / 8 × params_B × 0.02
```

Where `context_K` is context length in thousands of tokens.

## Repo source URLs

- Qwen2.5-7B: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF?local-app=llama.cpp
- Qwen2.5-Coder-7B: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF?local-app=llama.cpp  
- Qwen3-8B: https://huggingface.co/Qwen/Qwen3-8B-GGUF?local-app=llama.cpp
- Qwen2.5-14B: https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF?local-app=llama.cpp
- Qwen2.5-Coder-14B: https://huggingface.co/unsloth/Qwen2.5-Coder-14B-Instruct-GGUF?local-app=llama.cpp
- Qwen2.5-32B: https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF?local-app=llama.cpp
- Qwen2.5-Coder-32B: https://huggingface.co/unsloth/Qwen2.5-Coder-32B-Instruct-GGUF?local-app=llama.cpp
- Gemma-2-9B-it: https://huggingface.co/bartowski/gemma-2-9b-it-GGUF?local-app=llama.cpp
