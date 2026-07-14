# llama.cpp + Qwen 2.5 Setup for ThinkPad P53

Hardware: i7-9850H (6C/12T) | 46GB RAM | NVIDIA Quadro T1000 (4GB VRAM)

## Installation (Ubuntu 24.04)

### 1. Install CUDA Toolkit

```bash
sudo apt-get update
sudo apt-get install -y nvidia-cuda-toolkit
nvcc --version   # Should show CUDA 12.x
```

**Pitfall:** the `cuda-toolkit-12-2` package from NVIDIA's repo requires adding apt sources and won't be found in default Ubuntu repos. The simpler `nvidia-cuda-toolkit` from Ubuntu works fine for llama.cpp. Do NOT install via NVIDIA's developer download + dpkg.

### 2. Build llama.cpp with CUDA

```bash
git clone --depth 1 https://github.com/ggml-org/llama.cpp
cd llama.cpp
mkdir build && cd build
cmake .. -DGGML_CUDA=ON -DGGML_NATIVE=ON -DGGML_AVX2=ON -DGGML_FMA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j$(nproc)
```

**Pitfall:** Do NOT use `-DLLAMA_CURL=ON` unless libcurl4-openssl-dev is installed. Simpler: download GGUF files via `curl` directly from Hugging Face.

**Build time:** ~5-8 minutes on i7-9850H (6C/12T).

### 3. Download Qwen 2.5 7B Q4_K_M

Do NOT use the official Qwen repo (Qwen/Qwen2.5-7B-Instruct-GGUF) — it uses Xet storage with multi-file GGUFs split into 2 parts. llama.cpp cannot load split GGUFs directly.

Use **bartowski's** repackaged single-file version:

```bash
curl -L -o modelos/qwen-7b-q4_k_m.gguf \
  "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf?download=1"
```

**File:** 4.68 GB single GGUF file.

**Pitfall:** Always append `?download=1` for curl downloads from Hugging Face. Without it, you get a 15-byte redirect page.

**Pitfall:** `llama-cli --hf-repo Qwen/... --hf-file qwen2.5-7b-instruct-q4_k_m.gguf` fails — the official repo stores GGUFs as multi-file splits. Use `bartowski/` repo for single-file imports.

## Hardware Configuration

Qwen 2.5 7B has 28 transformer layers. With Q4_K_M (~4.7 GB):

| n_gpu_layers | VRAM used | Result |
|---|---|---|
| 20 | ~3.2 GB | ✅ Works, ~700 MB headroom |
| 24 | ~3.8 GB | ❌ OOM — "ggml_backend_cuda_buffer_type_alloc_buffer: cudaMalloc failed" |
| 28 (all) | ~4.7 GB | ❌ OOM |

**Recommended: `-ngl 20`** — leaves ~700 MB VRAM headroom. Do NOT use 24 layers.

**CPU threading:** `-t 12` (6C/12T i7-9850H)

## Warmup behavior

Critical for batch processing: the first query to a freshly started server takes ~18s to load KV cache into GPU. Subsequent queries run at full speed (~5s).

Always batch queries sequentially in one server session. Do NOT restart server between documents.

## Chunking semántico (nueva recomendación)

NO truncar por posición fija (ej: 7,000 chars). Los documentos judiciales pierden el RESUELVE (fallo) con ese método.

Usar chunking multi-pasada con overlap de ~500 chars que respeta párrafos. Implementado en `scripts/chunking_demo.py`.

## Alternative models

Para ThinkPad P53 + Quadro T1000 4GB, ordenados por velocidad:

1. Gemma 4 E2B Q4_K_M (~3 GB, MoE, 40-50 tok/s) — fastest, cabe completo en GPU
2. Qwen 2.5 3B Q4_K_M (~2 GB, 30-35 tok/s) — conservative choice, same stack as 7B
3. Qwen 2.5 7B Q4_K_M (~4.5 GB, 11 tok/s, ngl=20) — proven quality, partial GPU offload

Gemma 4 note: disable thinking mode with `--reasoning off` (llama.cpp moderno, preferido). Si el build es anterior, usar `--chat-template-kwargs '{"enable_thinking":false}'` (deprecado en builds recientes).

## Performance (tested real: 6 Jun 2026, warmup applied)

Peformance probada con **Qwen 2.5 7B Q4_K_M** (-ngl 20, -t 12, mlock, despues de warmup):

| Documento | Formato | Tokens prompt | Tokens completion | Tok/s | Tiempo |
|---|---|---|---|---|---|
| Resolución laboral (7K chars) | PDF | 2040 | 412 | 11.1 | 37.3s |
| Resolución garantías (7K chars) | PDF | 1959 | 458 | 11.1 | 41.2s |
| Contrato arrendamiento (7K chars) | DOCX | 2044 | 250 | 11.0 | 22.8s |
| Resolución legacy (1.2K chars) | DOC | 498 | 235 | 9.2 | 25.7s |

**Promedio real (con warmup):** **~10.7 tok/s, ~31.8s por documento**

**Efecto warmup (CRITICO para batch):**
- Primera consulta: ~18s, 3.5 tok/s (carga KV cache en GPU)
- Consultas siguientes: ~5s, 12.7 tok/s (cache caliente)
- NO reiniciar server entre documentos

**Resumen:**
| Metrica | Valor real (6 Jun 2026) |
|---|---|
| Tokens/second | **10.7** (no 5-7 como se estimaba antes del warmup) |
| Tiempo por documento (7K chars) | **~32s** |
| Batch de 1K documentos | **~8.8 horas** |
| Batch de 10K documentos | **~3.7 dias** |
| Lote de 500K documentos | **~184 dias** — viable para procesamiento continuo 24/7 |

**Implicación:** Qwen 2.5 7B local es viable para extracción selectiva (cientos, no cientos de miles de documentos). Para lotes masivos, mantener Groq API.

**Alternativa rápida (GPU completa):** Qwen 2.5 3B Q4_K_M (1.9 GB, cabe 100% en VRAM, ~40 tok/s estimado). Recomendado solo si la calidad del 7B es aceptable para la tarea.

### Server startup

```bash
# Iniciar server (necesario tras cada reboot)
cd /ruta/a/QwenLegalExtractor
./llama.cpp/build/bin/llama-server \
  -m modelos/qwen-7b-q4_k_m.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  -ngl 20 \
  -t 12 \
  -c 8192 \
  -ub 512 \
  --mlock \
  --no-webui  2>&1
```

**Check:** `curl -s http://127.0.0.1:8080/health`

**Pitfall:** Si se usa `pty=true` o background en Hermes, monitorear que no OOMee al cargar.

## Dependencies for multi-format extraction

Para extraer texto de archivos .doc (legacy Word):

```bash
sudo apt-get install -y catdoc antiword   # .doc legacy
# python-docx ya se instala via pip (para .docx moderno)
# pdftotext via poppler-utils (para .pdf)
```

### Dependencies (via pip)

```bash
pip install requests python-docx
```

## Notes

- **`--no-webui` flag:** Required when running via Hermes background — without it, the server tries to bind to a web interface that may not be available and logs warnings.
- **`--mlock`:** Prevents model from being swapped to disk; important on systems with 46GB RAM like the P53.
- The script `scripts/extractor.py` implements the full extraction pipeline.
