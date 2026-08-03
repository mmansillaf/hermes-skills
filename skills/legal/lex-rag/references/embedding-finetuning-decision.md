# Embedding Fine-Tuning Decision Framework

**Context:** When evaluating whether to fine-tune an embedding model for a legal RAG system, the default answer is **not yet** — not **never**. The order of operations matters more than the technique itself.

## The Correct Sequence (Baseline-First)

```
STEP 1: Get a strong baseline first
  ├── Upgrade from generic embeddings to SOTA base model
  │   (e.g. distiluse → BGE-M3: +17% recall, 8192 tok context)
  ├── Add hybrid search: FAISS (dense) + BM25 (sparse) + RRF fusion
  ├── Add cross-encoder reranker (BGE-reranker-v2-m3)
  └── Measure: recall@5, recall@10, MRR, hallucination rate

STEP 2: Measure and decide
  ├── If recall@10 >= 85% → STOP. Fine-tuning not needed.
  │   The pipeline is strong enough. Invest in other areas.
  │
  └── If recall@10 < 80% → Continue to STEP 3.
      Document specific failure modes: what does the model miss?

STEP 3: Fine-tune (only if baseline is insufficient)
  ├── Generate training pairs (query → positive chunk)
  │   via synthetic generation with DeepSeek / GPT-4o-mini
  │   Cost: ~$20-40 for 10-20K pairs
  ├── Add hard negatives (documents that look relevant but aren't)
  ├── Train with LoRA/QLoRA to limit memory requirements
  ├── Model candidates: BGE-M3, RoBERTalex (legal Spanish)
  ├── Hardware: RunPod RTX 4090 (~$0.60/hr, ~$2-5 total)
  └── Re-measure against baseline. Must justify cost and effort.
```

## Hardware Tiers for Fine-Tuning

| Tier | GPU | VRAM | Methods | Models | Cost |
|------|-----|------|---------|--------|------|
| Local (P53) | Quadro T1000 | 4 GB | LoRA 4-bit, QLoRA, batch=4-8 | MiniLM, small BERT (~100M) | $0 |
| Cloud cheap | RTX 3060 | 12 GB | LoRA, batch=16-32 | BGE-small, E5-small | ~$0.35/hr |
| Cloud sweet | RTX 4090 | 24 GB | Full fine-tune, batch=64-128 | BGE-M3 (560M), E5-large | ~$0.60/hr |
| Cloud pro | A100 80GB | 80 GB | Full fine-tune large batches | 7B-class embeddings | ~$1.09/hr |

For 50K legal docs: cloud sweet-spot costs ~$2-5 per training run.

## When Fine-Tuning IS Worth It

- Recurring queries return vague/generic results even with SOTA base model + reranker
- Vocabulary is genuinely domain-specific and not represented in training data
  (e.g. Peruvian legal terms like "acción de amparo", "recurso de casación")
- High ambiguity between similar norms (need to distinguish Ley 30478 from Ley 31082)
- You can generate 10K+ high-quality synthetic query-document pairs

## When Fine-Tuning is NOT Worth It

- OCR quality is poor — fix OCR first, fine-tuning on garbage is worse
- Documents are poorly structured — fix chunking first
- No way to create training pairs (no queries, no synthetic generation pipeline)
- Haven't compared against a proper baseline (BGE base + hybrid search + reranker)
- The bottleneck is in the LLM synthesis stage, not retrieval

## Known Pitfalls

1. **False improvement illusion**: A fine-tuned model may score higher on synthetic queries
   but perform worse on real user queries. Always validate with human-curated test set.
2. **Catastrophic forgetting**: Too many epochs (3+) on domain data can degrade
   general language understanding. 1 epoch is often optimal for GPL/unsupervised.
3. **Hard negative poisoning**: If your hard negatives are too easy (e.g. random documents),
   the model doesn't learn fine boundaries. Use retrieved hard negatives (BM25 top-100
   excluding positive).
4. **Overfitting to query style**: If all synthetic queries follow the same pattern
   ("¿Qué dice [norma] sobre [tema]?"), the model won't generalize to natural speech.
   Vary query templates.

## Key Papers Referenced

- TSDAE + GPL (Generative Pseudo Labeling) — arXiv 2112.07577
- Unsloth for efficient fine-tuning — unsloth.ai
- MarginMSELoss for cross-encoder distillation — sentence-transformers v3
