# SentenceTransformer API Notes

## Version-conditional method names

`sentence-transformers` renamed `get_embedding_dimension()` to `get_sentence_embedding_dimension()` between v4.x and v5.x.

| Version | Method | Notes |
|---------|--------|-------|
| v3.x+   | `get_sentence_embedding_dimension()` | Works on all v3+ |
| v4.x    | `get_embedding_dimension()` | Works on v4.x only |
| v5.x    | `get_sentence_embedding_dimension()` | Required; `get_embedding_dimension()` removed |

**Safe approach**: Use `get_sentence_embedding_dimension()` — it's been available since v3.0.0 and is the canonical API in v5.x.

## How to verify installed version

```powershell
python -c "import sentence_transformers; print(sentence_transformers.__version__)"
# e.g. 5.2.3
```

## How to discover available methods

```python
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2', device='cpu')
print([a for a in dir(m) if 'dimension' in a.lower()])
# Expected: ['get_sentence_embedding_dimension']
```

## Error symptom

```
File "d:\PyCode\ResumenTokensJurisprudencias\graphrag_pro.py", line 14, in <module>
    from pipeline.indexer import ingest_data, FAISS_INDEX_PATH
  File "d:\PyCode\ResumenTokensJurisprudencias\pipeline\indexer.py", line 14, in <module>
    from core.embedding import embedding_model, emb_dim
ImportError: cannot import name 'emb_dim' from 'core.embedding' (d:\PyCode\ResumenTokensJurisprudencias\core\embedding.py)
```

Despite looking like a missing-export error, the root cause is that `get_embedding_dimension()` raised `AttributeError` inside the `try` block of `core/embedding.py`, so `emb_dim` was never assigned as a module-level variable. The `except` clause logs the error but doesn't set a fallback value.

## Fix pattern

In `core/embedding.py`:

```python
try:
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2', device='cpu')
    emb_dim = embedding_model.get_sentence_embedding_dimension()  # NOT get_embedding_dimension()
except Exception as e:
    logger.error(f"Error cargando el modelo de embeddings: {e}")
    embedding_model = None
    emb_dim = 512  # fallback for distiluse-base-multilingual-cased-v2
```

The fallback value for `distiluse-base-multilingual-cased-v2` is 512.
