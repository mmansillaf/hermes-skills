# Semantic Cache — Domain-Specific Threshold Tuning

## The Decision Framework

When configuring semantic caching in Hermes, the threshold must balance cache-hit rate against false-positive risk. The optimal threshold depends on the domain:

### Threshold comparison

| Threshold | False positive risk | Hit rate (dev) | Hit rate (legal) | Verdict |
|-----------|-------------------|----------------|------------------|---------|
| 0.94 | Low but real for legal | 20-25% | 15-20% | Too lax for mixed legal/dev |
| **0.96** | **Near zero** | **12-18%** | **8-12%** | **Recommended for legal domain** |
| 0.97 | Zero | 5-8% | 3-5% | Not worth the overhead |

### Legal domain: why 0.96 not 0.94

In legal queries, semantically close phrases can be juridically opposite:
- "Ley de contrataciones del Estado" vs "Ley de contrataciones laborales"
- "Régimen laboral de servidores públicos" vs "Régimen disciplinario de servidores públicos"

At 0.94, these pairs could trigger cache hits returning wrong answers. At 0.96, the gap is wide enough to prevent false positives while still capturing genuine paraphrases.

### TTL: why 1h not 2h for legal

Legal information has higher staleness risk. A cached answer about "la ley más reciente sobre X" could be outdated within hours. 1h TTL + threshold 0.96 = safe balance.

### The 0.97 trap

At 0.97, only near-identical prompts hit the cache (one word difference). In iterative development, the 2nd and 3rd reformulations of a bug fix request differ enough to miss. The savings drop to ~$0.04/session — not worth the config overhead.

## Applied configuration (May 2026)

```yaml
cache:
  enabled: true
  strategy: semantic
  similarity_threshold: 0.96
  ttl: 3600   # 1 hour
  max_size: 200MB
```

## Key insight: RAG context changes prevent stale hits

Even if the user's question is semantically identical, the RAG system injects fresh document chunks from SQLite/Qdrant into the prompt. If the DB content changed, the full prompt changes → no cache hit. This is a natural safety net that reduces the risk of serving stale legal information from cache.
