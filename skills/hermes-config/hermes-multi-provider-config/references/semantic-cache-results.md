# Semantic Cache Configuration — Results

Tested 2026-05-05 with DeepSeek V4-Pro in legal domain (El Peruano RAG).

## Recommended Config

```bash
hermes config set cache.enabled true
hermes config set cache.strategy semantic
hermes config set cache.similarity_threshold 0.96
hermes config set cache.ttl 3600
hermes config set cache.max_size 200MB
```

## Why 0.96 for legal domain

| Threshold | Legal risk | Dev hit rate | Verdict |
|-----------|-----------|-------------|---------|
| 0.94 | "Ley de contrataciones del Estado" vs "Ley de contrataciones laborales" could collide | 20-25% | Too risky |
| 0.96 | Extremely narrow collision window | 12-18% | Best balance |
| 0.97 | Negligible benefit | 5-8% | Not worth it |

## Interaction with RAG systems

RAG systems inject fresh document chunks into prompts. This means even when a user asks two semantically similar questions, if the retrieved documents differ, the full prompt differs → cache miss. This provides an extra safety layer for legal accuracy.

## Cost impact

- DeepSeek V4-Pro: 90% discount on cache hits
- Estimated 12-18% total token savings in development sessions
- ~$0.12-0.25 saved per 50-request session
- $0 setup cost (local embeddings for similarity check)
