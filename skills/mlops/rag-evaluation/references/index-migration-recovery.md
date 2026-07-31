# Embedding Model Migration — Index Recovery

## Problem

When a RAG system switches embedding models (e.g., `distiluse-base-multilingual-cased-v2` 512d → `BAAI/bge-m3` 1024d), the existing FAISS index becomes incompatible because its vector dimension doesn't match the new model's output dimension.

```
AssertionError: assert d == self.d
  FAISS index: 512 dims (distiluse)
  New model:   1024 dims (bge-m3)
```

The BM25 index may also fail if the bm25s library version differs between save and load time:
```
AttributeError: 'BM25' object has no attribute 'vocab_dict'
```

## FAISS Dimension Mismatch

### Diagnosis

```python
import faiss

faiss_idx = faiss.read_index("datos/faiss_index_pro.bin")
print(f"FAISS dim: {faiss_idx.d}")  # 512
print(f"FAISS ntotal: {faiss_idx.ntotal}")

# Compare with current model
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-m3")
test_emb = model.encode("test query")
print(f"Model dim: {len(test_emb)}")  # 1024
```

### Quick Fix: Fallback Chain in get_hybrid_context()

When FAISS dimensions don't match, use a try-except to fall back to an alternative vector source:

```python
# In get_hybrid_context():
query_vector = embedding_model.encode(hyde_query)
try:
    distances, indices = idx.faiss_index.search(
        np.array([query_vector]).astype('float32'),
        top_k * 2
    )
    faiss_results = [idx.faiss_meta[i]["doc_id"] for i in indices[0] if i != -1]
except AssertionError:
    # Disable FAISS — use BM25-only or pgvector fallback
    faiss_results = []
```

**Two fallback strategies:**

| Strategy | Pros | Cons |
|----------|------|------|
| **BM25-only** | Simple, no DB dependency | Loses semantic search quality |
| **pgvector fallback** | Uses real 1024d vectors from DB | DB query latency, doc ID format mismatch |

### Long-term Fix: Rebuild FAISS

Re-encoding 65K texts with bge-m3 on CPU takes ~1-2 hours (memory-dependent). Two approaches:

**A — From PostgreSQL vectors (fast, ~1 min):**
```python
# Read existing 1024-dim vectors from PG, build FAISS directly
sql = "SELECT id, embedding FROM html_docs WHERE embedding IS NOT NULL"
# Parse embedding strings, build IndexFlatL2(1024)
```

**B — From chunk texts (slow, ~1-2 hours):**
```python
# Re-encode all texts with new model
model = SentenceTransformer("BAAI/bge-m3")
for i in range(0, len(texts), batch_size):
    emb = model.encode(texts[i:i+batch_size])
    index.add(emb.astype('float32'))
```

**Memory constraints on 8GB RAM systems:**
- bge-m3 model: ~2.2GB
- Batch size 8-16 recommended to avoid swap thrashing
- Save checkpoints every 10K vectors
- Use small batch processing with intermediate GC collection

## BM25 API Version Incompatibility

### Symptom

```
AttributeError: 'BM25' object has no attribute 'vocab_dict'
  → in bm25s/__init__.py, get_tokens_ids()
```

### Root Cause

The bm25s library changed its internal structure between versions:
- **v1** (older): required `vocab_dict` attribute, populated by `bm25s.BM25.load()`
- **v2** (newer): uses `retrieve()` API, `get_scores()` may fail if index was saved by different version

### Diagnosis

```python
import bm25s
bm = bm25s.BM25()
bm.load("datos/bm25s_index")

print(f"Has vocab_dict: {hasattr(bm, 'vocab_dict')}")
print(f"Has vocab: {hasattr(bm, 'vocab')}")
print(f"Has scores: {hasattr(bm, 'scores')}")
# If all are False, index was saved by different version
```

### Quick Fix: Fallback in get_hybrid_context()

```python
bm25_results = []
try:
    # Try get_scores (v1 API)
    tokenized_query = tokenize_spanish(hyde_query)
    doc_scores = idx.bm25.get_scores(tokenized_query)
    top_indices = np.argsort(doc_scores)[::-1][:top_k * 2]
    bm25_results = [idx.bm25_meta[i]["doc_id"] for i in top_indices]
except (AttributeError, Exception):
    # Fallback to retrieve (v2 API)
    scores, indices = idx.bm25.retrieve(hyde_query, k=top_k * 2)
    bm25_results = [idx.bm25_meta[i]["doc_id"] for i in scores[0] if i < len(idx.bm25_meta)]
```

### Long-term Fix: Rebuild BM25 Index

Rebuilding 65K texts takes ~8 seconds:

```python
import bm25s
texts = [m["text"] for m in meta]
corpus_tokens = bm25s.tokenize(texts)
bm = bm25s.BM25()
bm.index(corpus_tokens)
bm.save("datos/bm25s_index")
```

## Cache Invalidation After Model Change

After changing the embedding model, OLD cache entries (from previous model or WEB searches) contain stale responses that don't match the current retrieval.

### Symptoms
- Query returns `Cached: True` with old doc IDs
- Grounding score is poor because cited docs don't match current retrieval

### Fix
```bash
rm -rf /opt/api-algoritmo/cache/*
```

Or add a `model_version` field to cache keys so old entries are automatically ignored:

```python
MODEL_VERSION = "bge-m3-20260720"
cache_key = f"{MODEL_VERSION}:{query_hash}"
```

## Preventing Future Migration Pain

1. **Store model version in index metadata** — save a `model_name` and `embedding_dim` alongside each FAISS/BM25 index
2. **Validate on startup** — check that FAISS dim matches model dim before accepting queries
3. **Use pgvector as primary** — if PostgreSQL is already storing vectors, use it instead of FAISS to avoid migration issues entirely
4. **Version your cache keys** — include model name/version in cache hash to auto-invalidate on model change
