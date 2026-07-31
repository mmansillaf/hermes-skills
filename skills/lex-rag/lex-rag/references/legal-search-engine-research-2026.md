# Legal Search Engine Research Compendium (Jul 2026)

## Session context
Deep research on a Peruvian legal RAG system (LexRAG-based) covering:
- SAT-Graph RAG + LRMoo ontology for temporal legal reasoning
- Citation validation techniques (DEREK, Dahl 2025, Reliability by Design)
- BGE-M3 + BM25 + RRF hybrid search stack migration
- Fine-tuning of embeddings for legal domain (TSDAE + GPL + LoRA)
- Cross-project diff workflow for multi-version projects

## Papers Discovered (18 total)

### SAT-Graph Ecosystem (Hudson de Martim, JURIX 2025)
| Paper | arXiv | Role |
|-------|-------|------|
| SAT-Graph RAG | 2505.00039 | Framework: 4 node types (F1 Work, F2 Expression, F3 Manifestation, Action Events). Solves 3 legal-RAG pathologies: mereological, diachronic, causal blindness |
| SAT-Graph API | 2510.06002 | Deterministic interface for agents: point-in-time retrieval primitives |
| LRMoo Legal Evolution | 2506.07853 | Temporal ontology LRMoo -> legal domain |
| LRMoo F1 -> schema.org | 2508.00827 | Web semantic mapping |
| Beyond Probabilistic Similarity | 2606.09724 | Theoretical foundation: critique of probabilistic RAG for law |
| CALRK-Bench | 2603.26332 | Temporal reasoning legal benchmark (Korean) |
| Falkor-IRAC | 2605.14665 | Graph-constrained generation with verifier. IRAC pattern (Issue, Rule, Application, Conclusion) |

### Citation Validation
| Paper | arXiv | Finding |
|-------|-------|---------|
| Dahl 2025 | 2405.20362 | Lexis+AI and Westlaw hallucinate 17-33% of citations. First pre-registered study |
| DEREK Module | 2507.15863 | LangGraph verifier enforcing citation overlap. <3% unsupported statements |
| Reliability by Design | 2601.15476 | FCR (False Citation Rate) < 0.2% with advanced RAG + programmatic verification |
| Citation Grounding (CG-DPO) | 2606.00898 | 13-21% hallucination across 5 systems. CG-DPO reaches 98.5% precision |
| Who Checks Citations | 2606.21155 | Programmatic verifier (91.2% recall) BEATS GPT-5 agentic (82.8%). Programmatic > LLM-as-judge |

### Embeddings + Hybrid Search
| Paper / Source | Finding |
|----------------|---------|
| BGE-M3 benchmarks | +17% recall vs distiluse. 8192 tok context. Dense + sparse in 1 model |
| Matryoshka Representation Learning (MRL) | Single model produces variable-dimension embeddings. 98.37% performance at 8.3% size |
| Last Window Slicing (LCS) | Use last document chunk as document representation. Works well for legal (conclusions contain key info) |
| Multilingual Knowledge Distillation (MKD) | Student learns from teacher via translation pairs. Transfer English legal embeddings to Spanish |

### Key Techniques from Fine-Tuning Research

| Technique | Use | Reference |
|-----------|-----|-----------|
| TSDAE | Pre-train embedding on legal vocabulary (denoising autoencoder) | ftem7 |
| GPL (Generative Pseudo Labeling) | Unsupervised fine-tuning: generate synthetic queries + hard negatives + cross-encoder margins | arXiv 2112.07577 |
| MarginMSELoss | Train bi-encoder to emulate cross-encoder margin scores | sentence-transformers v3 |
| LoRA/QLoRA 4-bit | Fine-tune on 4GB VRAM (P53 Quadro T1000) | PEFT + bitsandbytes |
| MNRL (Multiple Negatives Ranking Loss) | Contrastive loss using in-batch negatives | SBERT docs |
| Unsloth | 2-3x speedup, 50% memory reduction for embedding fine-tuning | unsloth.ai |

### LexRAG-Specific Findings (Jul 2026)

**CriticAgent indeterminate citations bypass confirmed:**
- agents/critic.py lines 260-266: citations with only textual identifiers (EXP., CAS., RTF) are set to `hallucinated = False` even when they don't match any document.
- graphrag_pro.py `_needs_rewrite()` only checks `hallucinated > 0`, so indeterminate citations pass silently.
- Fix: 3 changes in 2 files (see SPEC-002_VALIDADOR_CITAS.md Section 3.3)

**Reranker discovered in LexRAG-v2 experimental fork:**
- retrieval/reranker.py uses BAAI/bge-reranker-v2-m3 cross-encoder
- Not present in production (LexRAG-Optimizado) -- merge needed

**Multi-version diff workflow validated:**
1. find + sort both directories
2. Compare module presence checklist: pipeline/, retrieval/, agents/, core/, utils/, tests/, data/
3. Diff critic.py and graphrag_pro.py (identical across versions in this case)
4. Check for unique modules (e.g. reranker.py in v2)
5. Data presence determines production vs experimental

### Stack Recommendation for Legal RAG

| Phase | Stack | Rationale |
|-------|-------|-----------|
| Phase 1 (now) | BGE-M3 + BM25 + RRF (k=80) + cross-encoder | +17% recall vs distiluse. 3 sources. Hierarchical norm weights |
| Phase 2 (next) | PostgreSQL + pgvector temporal engine | SAT-Graph LRMoo schema + exclusion constraints |
| Phase 3 (if needed) | Fine-tune BGE-M3 on RunPod RTX 4090 | Only if recall < 80% post-Phase 1. ~$5/training |

### Decision Rule for Embedding Fine-Tuning
Baseline-first, NOT fine-tune-first:
1. Upgrade to SOTA base (BGE-M3)
2. Add hybrid search + reranker
3. Measure recall@10
4. If >= 85%: stop. If < 80%: fine-tune
