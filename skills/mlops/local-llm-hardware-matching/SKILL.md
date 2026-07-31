---
name: local-llm-hardware-matching
description: Assess a Linux machine's hardware for local CPU-based LLM inference — RAM bandwidth analysis, model sizing, quant selection, and upgrade planning. Covers the bottleneck hierarchy for CPU inference.
triggers:
  - "User asks 'what models can my machine run locally?'"
  - "User asks 'will a RAM upgrade help local inference?'"
  - "User shares system info (lscpu, free -h, dmidecode) and wants model recommendations"
  - "User asks about Qwen model compatibility with their hardware"
  - "User is considering buying/upgrading hardware for local LLMs"
---

# Local LLM Hardware Matching

Assess a machine and recommend which GGUF models fit and how fast they'll run on CPU inference.

## Core Principle

For CPU-based llama.cpp inference, **RAM bandwidth is the bottleneck, not CPU clock speed**. Single vs dual-channel memory can mean **2× tokens/second** on the same model and CPU. GPU offload on sub-4GB VRAM cards provides negligible benefit.

## Workflow

### Phase 1: Collect Hardware Diagnostics

Run all of these in parallel:

```bash
# CPU threading
nproc

# CPU frequency and throttling check (critical for laptops — inference is unusable on battery)
cat /sys/class/power_supply/AC*/online            # 0=battery → CPU throttled to minimum
cat /sys/devices/system/cpu/intel_pstate/no_turbo  # 1=turbo disabled on battery
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq  # actual MHz; 800 MHz = stuck
cpupower frequency-info | grep "hardware limits"   # "400 MHz - 800 MHz" = throttled

# RAM total + available
free -h

# RAM physical layout (needs sudo or SUDO_PASSWORD in .env)
sudo dmidecode -t memory | grep -E "Size:|Locator:|Speed:|Manufacturer|Part Number|Number Of Devices|Type:"

# Maximum supported RAM
sudo dmidecode -t memory | grep -A5 "Physical Memory Array" | grep "Maximum Capacity"

# GPU
nvidia-smi 2>/dev/null || echo "No NVIDIA GPU"
lspci | grep -iE "vga|3d|display|nvidia|amd"

# Disk for model storage
df -h /home

# Swap
cat /proc/swaps
```

### Phase 2: Identify Memory Channel Mode

| Slot population | Mode | Bandwidth | Impact |
|----------------|------|-----------|--------|
| 1 stick populated | Single-channel | ~12-15 GB/s | Baseline — 7B Q4 at ~4-6 tok/s |
| 2 sticks, matched | Dual-channel | ~22-30 GB/s | ~2× speed — 7B Q4 at ~8-12 tok/s |
| 2 sticks, mismatched capacity | Flex (partial dual) | ~15-20 GB/s | Mixed — first N GB dual, rest single |

Use `sudo dmidecode -t memory`: if one slot says "No Module Installed" → single-channel. If both have the same size → dual-channel. If different sizes → flex mode.

### Phase 3: Estimate Model Fit

Model memory formula:
```
Needed RAM ≈ model_file_size × 1.2 + context_tokens × kv_cache_per_token
```

Where `kv_cache_per_token` ≈ 0.5-2 MB/token depending on quant and context length. For 4K context at Q4_K_M, add ~1.5 GB overhead.

**Model RAM requirements table (Q4_K_M, 4K context):**

| Size | File size | Min free RAM | Recommended total system RAM | Best for |
|------|-----------|-------------|------------------------------|----------|
| 1.5-3B | ~1-2 GB | ~3 GB | 8 GB | Quick questions, code completions |
| 7B | ~4.5 GB | ~6 GB | 16 GB | General chat, code, analysis |
| 14B | ~8.5 GB | ~10 GB | 24 GB | Smarter reasoning, coding |
| 32B (Q3_K_M) | ~13 GB | ~16 GB | 32 GB | Near-frontier quality on CPU |
| 32B (Q4_K_M) | ~18 GB | ~22 GB | 32 GB+ | Max quality for consumer hardware |
| 32B (Q4_K_M) — **40 GB tier** | ~19 GB | ~22 GB | 40 GB+ | 32B comfortable with 32K ctx; 72B Q2_K (~20 GB) also fits at ~3-5 tok/s |

### Phase 4: Speed Estimate

| Setup | 7B Q4 | 14B Q4 | 32B Q3 |
|-------|-------|--------|--------|
| Laptop 8-thread single-channel DDR4 | 4-6 tok/s | 2-3 tok/s | ~1 tok/s |
| Laptop 8-thread dual-channel DDR4 | 8-12 tok/s | 4-6 tok/s | 2-3 tok/s |
| Workstation 6C/12T Xeon dual-channel DDR4 | 13-17 tok/s | 7-10 tok/s | 6-8 tok/s (32B Q4) / 3-5 tok/s (72B Q2) |
| Desktop 16-thread dual-channel DDR5 | 20-30 tok/s | 10-15 tok/s | 5-8 tok/s |
| Apple M-series | 30-50 tok/s | 15-30 tok/s | 8-15 tok/s |

Measured with llama.cpp at 4K context, prompt processing excluded. Real speeds vary by CPU frequency governor, thermals, and system load.

### Phase 5: Recommend Models

**General recommendations:**

| Profile | Best model | Runner-up |
|---------|-----------|-----------|
| 16 GB, single-channel | Qwen2.5-Coder-3B Q4_K_M or Q8_0 | Qwen3-8B Q4_K_M (non-thinking mode, lento pero capaz) |
| 16 GB, dual-channel | Qwen2.5-7B-Instruct Q5_K_M | Qwen3-8B Q4_K_M |
| 16 GB, dual-channel | Qwen2.5-Coder-7B Q5_K_M or Qwen2.5-14B Q4_K_M (tight 8K ctx) | Qwen3-8B Q4_K_M (thinking mode) |
| 32 GB, dual-channel | Qwen2.5-14B Q4_K_M or Qwen2.5-32B Q3_K_M | Qwen3-8B Q4_K_M (agentic tasks) |
| 64 GB+ | Qwen2.5-72B Q4_K_M | Llama-3.3-70B Q4_K_M |

**2026 landscape update:** See **[landscape-2026.md](references/landscape-2026.md)** for the full panorama — June 2026 rankings (Kimi K2.6, Qwen3.6-27B, Devstral, GLM-5.2), UI generation benchmarks, legal multi-agent architectures, hybrid cloud-local cost analysis, fine-tuning costs (<$5) with GRPO, and innovations (80B models on 8GB, agent swarms).

**Qwen-specific recommendations:** (Qwen2.5 is mature, Qwen3 is newer with thinking-mode support and tool-calling)

| Scenario | Model | Quant | Why |
|----------|-------|-------|-----|
| General chat/coding, 8-16 GB RAM | Qwen2.5-Coder-7B-Instruct | Q5_K_M | Better quality than Q4, still fits |
| General chat/coding, 16-32 GB RAM | Qwen2.5-14B-Instruct | Q4_K_M | Significantly smarter, fits dual-channel machines |
| Maximize quality, 32 GB RAM | Qwen2.5-32B-Instruct | Q3_K_M | 32B understanding within 32GB budget (~16 GB) |
| Fast responses, limited RAM | Qwen2.5-Coder-3B-Instruct | Q8_0 | ~3 GB, 15+ tok/s |
| Research, 32 GB+ | Qwen2.5-32B-Coder | Q4_K_M | Largest Qwen coder for consumer hardware |
| **Best reasoning 8B** | **DeepSeek-R1-0528-Qwen3-8B** | **Q4_K_M** | ~5 GB. Destilado de R1-0528 sobre base Qwen3-8B. **86% AIME 2024** (+10% vs Qwen3-8B). Contexto 128K. Siempre piensa (~23K tokens de pensamiento). |
| **New: Hybrid thinking** | **Qwen3-8B** | **Q4_K_M** | 5 GB. Thinking on/off mode. 128K ctx. Más versátil para agente autónomo. 8B-class daily driver. |

### KV Cache Budgeting

Context length consumes additional RAM beyond the model weights. Account for it:

```
Total RAM ≈ model_file_size + KV_cache_size + 2 GB system overhead
```

KV cache formula (approximate):
```
KV_cache_size ≈ context_tokens × hidden_dim × num_layers × bytes_per_element × 2
```

**Practical examples (Q4_K_M):**

| Model | File size | 4K context | 8K context | 32K context | Recommended total |
|-------|-----------|------------|------------|-------------|-------------------|
| 7B | ~4.7 GB | ~1.5 GB | ~2.5 GB | ~7 GB | 16 GB (4K/8K), 32 GB (32K) |
| 14B | ~9 GB | ~2.5 GB | ~4.5 GB | ~14 GB | 24 GB (4K), 32 GB (8K/32K) |
| 32B Q3 | ~16 GB | ~4 GB | ~7 GB | ~22 GB | 32 GB (4K), 64 GB (8K+) |

**Rule of thumb:** For every 1B parameters, expect ~0.3 GB of KV cache per 32K context at Q4. Scale linearly with context length.

### Use-Case-Specific Recommendations

#### Coding & Software Engineering

**Split-Brain Architecture for weak-GPU laptops:** When the laptop has ≤2 GB VRAM but ample RAM, dedicate the GPU to a tiny model (1.5B-3B Q8_0 fits entirely in 2 GB VRAM) for instantaneous autocomplete in the IDE (100+ tok/s), and the CPU to the main model (7B Q5_K_M, ~10 tok/s) for chat and reasoning. The tiny model avoids PCIe transfer overhead by living wholly in VRAM; the main model lives wholly in system RAM. Launch as two independent llama-server instances.

| Hardware | Primary model | Secondary (parallel) |
|----------|--------------|---------------------|
| 16 GB, single-channel | Qwen2.5-Coder-7B Q5_K_M | Qwen2.5-Coder-1.5B Q8_0 on GPU (Split-Brain autocomplete, 100+ tok/s) |
| 16 GB, dual-channel | Qwen2.5-Coder-7B Q5_K_M | Qwen2.5-Coder-1.5B Q8_0 on GPU (Split-Brain) |
| 32 GB, dual-channel | Qwen2.5-Coder-7B Q5_K_M (daily driver) | Qwen2.5-Coder-1.5B Q8_0 on GPU (Split-Brain autocomplete) + API (deepseek-reasoner) for heavy tasks |
| 32 GB+ | Qwen2.5-Coder-7B Q5_K_M + API fallback | Qwen2.5-Coder-1.5B Q8_0 on GPU |

**"Prototype local, review cloud" workflow:** For development work that mixes a local model with a cloud API, pair a **small local model (7B, ~13 tok/s)** for initial code generation with a **powerful cloud model (DeepSeek, GPT, Claude)** for review and refactoring. This saves 60-70% of API tokens while keeping quality on complex projects.

Task delegation matrix:

| Fase | Modelo | Qué delegar |
|------|--------|-------------|
| Esqueleto del proyecto | Local (7B) | Scaffolding, imports, estructura de archivos |
| Endpoints / CRUD | Local (7B) | FastAPI básico, rutas REST |
| Scraping / ETL base | Local (7B) | Lógica de extracción, parsing |
| Pipeline RAG simple | Local (7B) | Chunking, embedding, retrieval básico |
| UI simple (Streamlit) | Local (7B) | Layouts, componentes |
| Arquitectura multi-servicio | **Cloud** | Integración de sistemas, flujos entre agentes |
| Debugging cross-file | **Cloud** | Errores que cruzan módulos, edge cases |
| Refactor mayor | **Cloud** | Reorganización de código |
| Tests y cobertura | **Cloud** | pytest, mocks, fixtures |
| Seguridad / concurrencia | **Cloud** | Validación, límites, locking |

Before recommending, **inspect the user's actual codebase** (GitHub repos, local projects) to assess complexity. A user maintaining multi-agent RAG systems needs a different model tier than one writing single-file scripts. Do not rely solely on model benchmarks — real projects reveal the capability threshold.

#### Legal Text & Document Processing

For legal documents in Spanish (Peruvian law, contracts, regulations):

| Hardware | Model | Quant | Strategy |
|----------|-------|-------|----------|
| 16 GB | Qwen2.5-7B-Instruct | Q5_K_M | Summarize in chunks, structured JSON output |
| 32 GB | Qwen2.5-14B-Instruct | Q4_K_M | Better inference for nuanced clauses, 32K context for long documents |
| 16-32 GB | Qwen3-8B | Q4_K_M | Non-thinking mode for fast extraction, thinking mode for complex legal reasoning |

**Hybrid local + API strategy (recommended for legal workloads):** When the user has access to an API (DeepSeek, Groq, etc.), prefer using it as a **complement** rather than running a large local model:
- **Local 7B Q5_K_M** for daily coding, quick queries, private documents (no data leaves the machine)
- **API (deepseek-reasoner, 128K context)** for long legal documents where the 7B runs out of context, or for complex legal reasoning that benefits from a frontier model
- **API (deepseek-chat)** when speed matters and the local model is too slow
- Switch between them in Hermes Agent via `hermes config set model` or multiple custom providers
- The API uses pay-per-token (~$0.14/M tokens for DeepSeek), so reserve it for heavy lifting; the local model handles the 80% daily volume for free

This avoids downloading a 9 GB+ 14B local model that barely fits and runs at 4-6 tok/s — the API processes the same documents faster, with better quality, and zero storage cost.

**Spanish multilingual note:** Qwen2.5 and Qwen3 both support Spanish natively (listed among 29+ languages in the training corpus). No Spanish-specific fine-tune needed. For structured output (extracting clauses, generating summaries in JSON), use llama.cpp's grammar-constrained generation.

#### General Chat & Analysis

| Hardware | Model | Quant | When |
|----------|-------|-------|------|
| 8-16 GB | Qwen2.5-7B | Q5_K_M | Daily driver |
| 16-32 GB | Qwen3-8B | Q4_K_M | Thinking mode for reasoning-heavy analysis |
| 32 GB | Qwen2.5-14B | Q4_K_M | Complex multi-step reasoning |

### Phase 6: GPU Offload Assessment

**First check: Tensor Cores.** For NVIDIA GPUs, the presence of Tensor Cores (RTX series, A-series, Tesla T4+) vs pure CUDA cores (Quadro T1000/T2000, GTX series, MX series) makes a huge difference. Tensor Cores provide dedicated mixed-precision matrix math units that accelerate LLM inference 2-4× over CUDA-only at the same VRAM. Run `nvidia-smi -q | grep "Tensor"` to check.

For GPUs with **≤ 4 GB VRAM** (MX330, Quadro T1000/T2000, GTX 1650, etc.):

- **Without Tensor Cores (T1000/T2000/MX):** Standard layer offloading (`-ngl`) provides only **~15-25% improvement** over pure CPU. The GPU has few CUDA cores and no matrix math accelerators. CPU↔GPU transfer overhead eats most potential speedup. Pure CPU inference is often comparable. **The memory channel upgrade (single → dual) gives ~2× the speedup that this GPU would provide.**
- **With Tensor Cores (RTX 2050/3050 4GB):** Offloading is more beneficial, but the 4GB VRAM limit means only 7B models with partial offload (not full). Still ~30-50% faster than CPU-only.

For GPUs with **≥ 6 GB VRAM**:
- **Split-Brain Strategy (use instead of offloading):** When VRAM is too small for layer offload, run a **fully-contained tiny model** (1.5B-3B at Q8_0) entirely on GPU for one task (autocomplete in IDE, fast embedding), and the main model (7B-14B) entirely on CPU for reasoning/chat. The tiny model at ~1.6 GB fits in 2 GB VRAM with headroom and yields 100+ tok/s. This avoids PCIe transfer overhead because the entire tiny model lives in VRAM.
  ```
  GPU (≤2 GB VRAM): Qwen2.5-Coder-1.5B Q8_0 (~1.6 GB) → autocomplete
  CPU (≥16 GB RAM): Qwen2.5-Coder-7B Q5_K_M (~5.5 GB) → chat/reasoning
  ```
  Launch with two llama-server instances:
  ```bash
  # GPU tiny model (autocomplete)
  llama-server -m 1.5b-q8_0.gguf --port 8081 -ngl 99 -c 8192 --temp 0.2

  # CPU main model (chat)
  llama-server -m 7b-q5_k_m.gguf --port 8080 -ngl 0 -c 32768 --temp 0.6
  ```
- **The memory channel upgrade (single → dual) gives ~2× the speedup that GPU offloading would provide**

For GPUs with **≥ 6 GB VRAM**:

- Offload 100% of layers with `-ngl 999` (or all but the last 1-2)
- 7B Q4 fits in 6 GB easily
- 14B Q4 fits in ~12 GB

### Phase 7: Provide Upgrade Guidance

When asked about upgrading for local inference, prioritize in this order:

1. **Add a second RAM stick** (activate dual-channel) — cheapest, biggest speedup
2. **Increase total RAM** — allows larger models (14B, 32B)
3. **Replace GPU with ≥ 6 GB VRAM** — enables full GPU offload
4. **Faster CPU** — helps but less than RAM bandwidth for CPU inference

## Pitfalls

- **Do not confuse total system RAM with free RAM.** Always check `free -h` for available memory after OS overhead.
- **ZRAM and swap count as RAM for model loading.** If the system has 16 GB RAM + 8 GB ZRAM, the model can use up to ~24 GB effective (with slowdown when hitting compressed swap).
- **ZRAM can hurt inference speed** because decompression competes for CPU cycles with the inference engine. Prefer real RAM for model memory.
- **Dual-channel requires two sticks.** A single 32 GB stick is still single-channel. Two 16 GB sticks enable dual-channel.
- **RAM speed (MT/s) matters less than channel count.** 2667 MT/s dual-channel outperforms 3200 MT/s single-channel for inference.
- **GPU with shared memory (Intel UHD, AMD iGPU) doesn't help.** The shared memory counts against the same RAM pool; no bandwidth benefit.
- **Thermal throttling is real on laptops.** A sustained inference run can push the CPU to 90°C+, causing throttling. `sensors` or `s-tui` during inference confirm this. Consider `auto-cpufreq` or a laptop cooling pad.
- **Battery power kills inference speed (laptop-specific).** Even with `governor=performance`, Intel mobile CPUs may hard-limit to 800 MHz on battery with `no_turbo=1`. This halves inference speed (e.g., 7B Q4 goes from ~3.6 tok/s to ~1.8 tok/s on i7-10510U). The limit is hardware/firmware-enforced; software governor changes cannot override it. Always recommend connecting the AC adapter for LLM inference. Check `cat /sys/class/power_supply/AC*/online` and `cat /sys/devices/system/cpu/intel_pstate/no_turbo`.

- **Context length (`-c`) is the #1 bottleneck on CPU inference, not quantization.** Setting `-c 65536` on a 7B model running CPU-only on a low-power U-series CPU (i7-10510U, 15W) makes it unusable: ~1.9 tok/s generation and 8-67 minutes per turn with accumulated context. The KV cache allocation and O(n²) attention dominate. A 1.5B model with 8K context is far more usable than a 7B model with 65K context. See [context-length-bottleneck.md](references/context-length-bottleneck.md) for real benchmark data.

## References

- **[ds-r1-0528-qwen3-8b-comparison.md](references/ds-r1-0528-qwen3-8b-comparison.md)** — Comparativa Qwen3-8B vs DeepSeek-R1-Distill-Qwen-7B vs DS-R1-0528-Qwen3-8B. Benchmarks, recomendaciones por hardware, parámetros llama-server.
- **[thinkpad-t14-assessment.md](references/thinkpad-t14-assessment.md)** — Full assessment of a ThinkPad T14 Gen 1 (i7-10510U, MX330, 32 GB dual-channel DDR4) with the final recommended setup: Split-Brain (1.5B GPU + 7B CPU), hybrid local+DeepSeek API, and Hermes Agent provider configuration.
- **[thinkpad-p53-assessment.md](references/thinkpad-p53-assessment.md)** — Assessment of a ThinkPad P53 (Xeon 6C/12T, 40 GB RAM) split by GPU variant: T1000 4GB (7B-8B models, ~8-15 tok/s) vs RTX 3000+ (14B-32B models, ~6-8 tok/s). Includes Qwen3-8B vs DeepSeek-R1-Distill-Qwen-7B comparison.
- **[quant-size-reference.md](references/quant-size-reference.md)** — Exact GGUF file sizes by quant for the most popular local model families (Qwen2.5, Qwen3, Llama, Gemma). KV cache budgeting formulas included.
- **[hermes-custom-provider-config.md](references/hermes-custom-provider-config.md)** — Configuración de custom providers en Hermes: formato lista con `- name:`, patrón provider+model separados, pitfalls comunes (dict obsoleto, provider no cambia con `set model`).
