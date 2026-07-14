# Batch Processing Statistics — Real-World Runs

## Groq Batch API — 4-Batch Campaign (June 2026)

### Batch Configuration

All batches used **Llama 3.1 8B Instant** with `max_tokens=1024` and the structured extraction prompt.

| Batch | Docs Sent | Label | File Size | Upload Time |
|:------|:---------:|:------|:---------:|:-----------:|
| Lote 1a | 12,500 | LABORAL | ~151 MB | ~5 min |
| Lote 1b | 12,499 | LABORAL | ~149 MB | ~5 min |
| Lote 2 | 25,000 | LABORAL | ~156 MB | ~5 min |
| Lote 3 | 7,935 | COMERCIAL+LABORAL | ~41 MB | ~2 min |
| **Total** | **57,934** | | **~497 MB** | **~17 min** |

### Completion Timing

| Batch | Created | Completed | Elapsed | Notes |
|:------|:-------:|:---------:|:-------:|:------|
| Lote 1a | 08:50 | 13:30 | **4h 40m** | Fastest |
| Lote 1b | 08:50 | ~14:20 | **~5h 30m** | |
| Lote 2 | 08:50 | ~16:00 | **~7h** | Slower (largest batch) |
| Lote 3 | 08:50 | ~16:00 | **~7h** | Same window as L2 |

Note: Timing is highly variable. Groq Batch has a 24h window. Actual completion depends on total platform load.

### Yield & Dedup

| Batch | Sent | Completed | Failed | % Failed | Useful | % Useful |
|:------|:----:|:---------:|:-----:|:--------:|:-----:|:--------:|
| Lote 1a | 12,500 | 12,453 | 47 | 0.4% | **12,443** | 99.5% |
| Lote 1b | 12,499 | 12,418 | 81 | 0.6% | **12,418** | 99.4% |
| Lote 2 | 25,000 | 24,978 | 22 | 0.1% | **935** (new) | 3.7% |
| Lote 3 | 7,935 | 7,935 | 0 | 0.0% | **270** (new) | 3.4% |
| **Total** | **57,934** | **57,784** | **150** | **0.3%** | **26,066** | |

**KEY INSIGHT — Batch overlap dedup:** Lotes 2 and 3 re-processed documents from the same source corpus as earlier batches. After dedup against the ~51K docs already in `data_raw/`, only **935 of 24,978** (3.7%) and **270 of 7,935** (3.4%) were actually new. When you submit overlapping document sets to Groq Batch, plan for ~96% dedup rate against existing processed IDs.

This is NOT an error — it's expected when covering the same corpus across multiple experimental runs or batch configurations.

### Indexing Performance

| Component | Model | Throughput | Time per 12K | Time per 50K |
|-----------|:-----:|:----------:|:------------:|:------------:|
| Embedding | `distiluse-base-multilingual-cased-v2` (512d) | **5 docs/s** | ~40 min | ~3h |
| Checkpoints | auto-save every 1,000 docs | | adds ~5s per save | negligible |

The embedding model is the bottleneck. Throughput is CPU-bound on consumer hardware. GPU acceleration would help significantly.

### Cumulative Pipeline Stats

| Metric | This campaign | Grand total |
|:-------|:------------:|:-----------:|
| Docs submitted to Groq | 57,934 | 57,934 |
| Failed (capacity_exhausted) | 150 (0.3%) | 150 |
| JSON parse errors | 44 (0.08%) | 44 |
| **Useful extraction outputs** | **57,590** | **57,590** |
| New unique docs after dedup | 26,066 | 76,302 |
| FAISS vectors (after chunking) | — | 76,302 |
| BM25 chunks | — | 76,302 |
| NetworkX nodes (docs + entities) | — | 123,519 |
| Total index size | — | ~386 MB |

### Cost Summary

| Model | Input/doc | Output/doc | Cost/doc | Total cost |
|:------|:---------:|:----------:|:--------:|:----------:|
| Llama 3.1 8B Instant | ~1,257 tok | ~322 tok | **$0.000088** | **~$5.10** |

Batch API pricing: 50% discount over real-time pricing. Actual cost was ~$5.10 for 57,934 docs.

### Practical Lessons

1. **Completion is unpredictable** — 4h to 7h for batches of similar size. Don't watch the clock.
2. **Dedup is aggressive** — If re-processing a corpus, most docs are already processed. Check `processed_ids` count before estimating yield.
3. **JSON validity with Llama 3.1 8B + max_tokens=1024**: ~99.9%. Only 44/57,590 (0.08%) failed JSON parsing.
4. **capacity_exhausted is ~0.3%** on a good day with Llama 3.1 8B (much lower than the earlier 3-4% estimate for busier periods).
5. **Indexing dominates real time** — Groq completes in 4-7h, but embedding 50K docs takes ~3h of CPU time.
