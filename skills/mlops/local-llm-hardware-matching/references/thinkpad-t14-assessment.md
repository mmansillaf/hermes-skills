# ThinkPad T14 Gen 1 — Hardware Assessment & Final Setup

Full assessment and recommended model setup for a Lenovo ThinkPad T14 Gen 1 used for local LLM inference + coding + legal document processing.

## Hardware Summary (Current State)

| Component | Detail |
|-----------|--------|
| **CPU** | Intel Core i7-10510U (CometLake-U) — 4 cores / 8 threads, 1.8 GHz base, 4.9 GHz boost |
| **RAM** | 32 GB dual-channel DDR4-3200 (Samsung 16 GB + Micron 16 GB) — runs at 2667 MT/s (CPU limitation) |
| **GPU** | NVIDIA GeForce MX330 — 2 GB VRAM (GP108M, entry-level, 384 CUDA cores) |
| **Storage** | 238.5 GB NVMe (Toshiba KBG30ZMV256G) — ~184 GB free, 14% wear, 0 errors |
| **OS** | Ubuntu 24.04 LTS, kernel 6.17.0-35-generic |
| **ZRAM** | 15.6 GB active (zstd compression) |
| **Swap** | Swapfile, swappiness=10, noatime on SSD |
| **Governor** | performance (locked), TLP active |
| **Max RAM** | 32 GB (both slots occupied) |

## User Profile

Legal-tech engineer from Peru. Projects:
- **KRagLocal** — RAG system for lawyers (Qdrant + bge-m3 embeddings)
- **cej-scraper** — Scraper for Peruvian Judicial Power (CEJ)
- **rag-legal-local** — Local RAG: Qdrant + SQLite + bge-m3 + DeepSeek/Groq
- **hermes-word-addin** — Hermes Agent AI chat panel embedded in Microsoft Word (FastAPI + WebSocket + Office.js)
- **hermes-skills** — Custom skills for Hermes Agent

## Diagnostic Commands

```bash
# CPU
nproc               # → 8
lscpu | grep "MHz"  # → 4900 max, 400 min
cat /proc/cpuinfo | grep "model name" | head -1

# RAM
free -h             # → 31Gi total, ~29Gi available
sudo dmidecode -t memory | grep -E "Size:|Locator:|Speed:|Manufacturer"

# GPU
nvidia-smi          # → MX330, 2048 MiB VRAM, 1996 MiB free

# Storage
df -h /             # → 233G total, 184G available
```

## Performance Estimates (32 GB Dual-Channel, CPU-only)

| Model (Quant) | tok/s | Notes |
|--------------|-------|-------|
| Qwen2.5-Coder-1.5B Q8_0 (on GPU) | 100+ | Fits entirely in 2 GB VRAM |
| Qwen2.5-Coder-7B Q4_K_M (on CPU, AC) | ~3.6 | **Actual measured** on i7-10510U, 4 threads, single-file GGUF |
| Qwen2.5-Coder-7B Q5_K_M (on CPU, AC) | ~10 | Estimated; same BW bottleneck as Q4 |
| Qwen2.5-Coder-7B Q4_K_M (on CPU, battery) | ~1.8 | **Actual measured** — CPU throttled to 800 MHz, `no_turbo=1` |
| Qwen2.5-14B Q4_K_M (on CPU, AC) | 4-6 | Theoretical; replaced by DeepSeek API in final setup |
| Qwen2.5-32B Q3_K_M (on CPU, AC) | 1.5-2.5 | Borderline, not recommended |

**Critical: battery vs AC.** The i7-10510U hard-limits to 800 MHz on battery with `no_turbo=1`, even with `governor=performance`. Always connect AC adapter for LLM inference.

## Model Performance (from Actual Session — Jul 2026)

Tested on this hardware with llama.cpp (AVX2 build), Qwen2.5-Coder-7B-Instruct Q4_K_M single-file GGUF:

| Condition | Prompt proc. | Generation | Notes |
|-----------|-------------|------------|-------|
| AC, -t 8, --flash-attn | 4.4 tok/s | 2.4 tok/s | Flash-attn adds CPU overhead |
| AC, -t 4, no flash-attn | 4.4 tok/s | 2.4 tok/s | Same performance; thread count doesn't matter much |
| **Battery**, -t 4 | **3.5 tok/s** | **1.8 tok/s** | CPU at 800 MHz |

**Verdict:** The i7-10510U at 15W is bandwidth-limited for 7B Q4 inference. Expect ~3.6 tok/s on AC with 4 threads. The 800 MHz battery throttle effectively halves performance.
  Qwen2.5-Coder-1.5B-Instruct Q8_0 (~1.6 GB)
  → Autocomplete in IDE at 100+ tok/s
  → Entire model fits in VRAM → zero PCIe transfer overhead
  → llama-server on port 8081, -ngl 99

CPU (i7-10510U, 32 GB RAM):
  Qwen2.5-Coder-7B-Instruct Q5_K_M (~5.44 GB)
  → Daily driver for coding and chat
  → ~10 tok/s, 32K context
  → llama-server on port 8080, -ngl 0

DeepSeek API (via Hermes custom provider):
  deepseek-reasoner → Long legal documents, complex reasoning
  deepseek-chat     → Speed when local is insufficient
```

### Models Discarded

| Model | Reason |
|-------|--------|
| Qwen2.5-14B Q4_K_M (8.99 GB) | Replaced by DeepSeek API for legal docs — better quality, 128K context, no storage cost |
| Qwen2.5-Coder-32B Q3_K_M (15.9 GB) | Impractical at ~2 tok/s on CPU |
| Qwen3-8B Q4_K_M (5.03 GB) | Thinking mode covered by DeepSeek-R1 API |

### Disk Usage

- Qwen2.5-Coder-1.5B Q8_0: ~1.6 GB
- Qwen2.5-Coder-7B Q5_K_M: ~5.44 GB
- **Total: ~7 GB** (of 184 GB free)

### Hermes Agent Configuration

```yaml
# ~/.hermes/config.yaml
custom_providers:
  local-llama:
    base_url: "http://localhost:8080/v1"
    api_key: "sk-no-key-required"
    models:
      - "qwen2.5-coder-7b-q5"

  deepseek-api:
    base_url: "https://api.deepseek.com/v1"
    api_key: "<sk-your-deepseek-key>"
    models:
      - "deepseek-chat"
      - "deepseek-reasoner"
```

Switch between them:
```bash
hermes config set model local-llama/qwen2.5-coder-7b-q5     # Daily coding
hermes config set model deepseek-api/deepseek-reasoner        # Legal documents
```

### Launch Commands

```bash
# 1. Compile llama.cpp with AVX2 optimization
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DGGML_AVX2=ON -DGGML_F16C=ON -DGGML_FMA=ON -DGGML_NATIVE=ON
cmake --build build --config Release -j $(nproc)

# 2. Download models
huggingface-cli download Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF \
  --include "qwen2.5-coder-1.5b-instruct-q8_0.gguf" \
  --local-dir ./models

huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF \
  --include "qwen2.5-coder-7b-instruct-q5_k_m*.gguf" \
  --local-dir ./models

# 3. Terminal 1 — tiny model on GPU (autocomplete)
./llama-server \
  -m models/qwen2.5-coder-1.5b-instruct-q8_0.gguf \
  --host 0.0.0.0 --port 8081 \
  -ngl 99 -c 8192 --temp 0.2

# 4. Terminal 2 — main model on CPU (chat)
./llama-server \
  -m models/qwen2.5-coder-7b-instruct-q5_k_m.gguf \
  --host 0.0.0.0 --port 8080 \
  -ngl 0 -c 32768 --temp 0.6
```

### Kernel Tuning

```bash
# Add to /etc/sysctl.conf
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.max_map_count = 262144
```

## Upgrade History

| Date | Change | Impact |
|------|--------|--------|
| Original | 1× 16 GB Samsung single-channel DDR4 | 4-6 tok/s (7B Q4) |
| After RAM upgrade | 2× 16 GB (Samsung + Micron) dual-channel DDR4 | 8-12 tok/s (7B Q4) ~2× speedup |
| Current | + Split-Brain (tiny model on GPU) + DeepSeek API hybrid | Instant autocomplete + cloud for heavy lifting |

## Model Performance (from Actual Session)

Tested on this hardware with llama.cpp (AVX2 build):
- Qwen2.5-Coder-7B Q5_K_M: ~10 tok/s, 32K context, comfortable fit in 32 GB RAM
- Tiny model on GPU: 100+ tok/s for autocomplete, negligible VRAM pressure
- No thermal throttling observed with governor=performance
