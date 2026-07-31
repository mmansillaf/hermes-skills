# Legal Document Linking Approaches

## Context

Lex RAG: a GraphRAG system for 64,186 Peruvian legal resolutions.
The source HTML files live at `Jurisprudencia/{filename}.html`.
The metadata mapping is at `data/metadata_docs.json`.

## Metadata-to-Path Mapping

The `data/metadata_docs.json` maps every HTML filename to a human-readable label.
This mapping is the bridge between internal IDs and clickable links:

```json
{
  "1612215.html": {
    "identificador": "CAS. N° 15-2015 LAMBAYEQUE",
    "organo": "Corte Suprema",
    "fecha": ""
  },
  "1660735.html": {
    "identificador": "RTF N° 12613-3-2015",
    "organo": "Tribunal Fiscal",
    "fecha": ""
  }
}
```

Every key in metadata_docs.json has a corresponding file at `Jurisprudencia/{key}`.
Key pattern: all lowercase, `.html` suffix, numeric prefix.

## Internal ID Format Consistency

Lex RAG has **three stores** that reference documents, and they differ in format:

| Store | Format | Example |
|-------|--------|---------|
| FAISS metadata (`faiss_meta_pro.pkl`) | `doc_id` with `.html` | `"1612215.html"` |
| NetworkX graph nodes (`graph_juris_pro.pkl`) | Node names with `.html` | `"1612215.html"` |
| Metadata JSON (`metadata_docs.json`) | Keys with `.html` | `"1612215.html"` |
| Source files on disk | Filenames with `.html` | `Jurisprudencia/1612215.html` |
| **MODULAR PIPELINE response** | Strips `.html` | `[Doc: 1660735.html]` (some kept, some stripped) |
| **MONOLITHIC CLI response** | Uses `get_doc_label()` | `[CAS. N° 15-2015 LAMBAYEQUE]` |

**All stores are consistent** (all use `.html` suffix). The inconsistency only appears when the modular pipeline (`graphrag_pro.py`) formats the context — it sometimes shows the raw doc_id (which may or may not carry `.html` depending on how the context builder handles it).

## Approach Selection Guide

### Choose A (File Paths) when:
- Running on a single machine (CLI only)
- No web server running
- User opens files from terminal
- Zero infrastructure overhead desired

**Implementation**: inject `get_doc_path()` next to `get_doc_label()` at context-build time.

### Choose B (FastAPI) when:
- The FastAPI server is already running (`api.py`)
- Multiple users access via web frontend
- Browser-based UX needed (clickable links in HTML)
- Existing `uvicorn` process on a fixed port

**Implementation**: add `app.mount("/docs", StaticFiles(directory="Jurisprudencia"), name="docs")` to `api.py`.

### Choose C (Static Index) when:
- No server will run
- Need a searchable offline reference
- Want to browse all 64K documents by court/type
- Can run a one-time generation script

**Implementation**: one `python3` script to emit a self-contained HTML file with search + filter.

## Concrete File Path Generation (Approach A)

```python
SOURCE_BASE = "Jurisprudencia"
METADATA_PATH = "data/metadata_docs.json"

def get_doc_label(doc_id):
    """Human-readable label for a document ID."""
    meta = docs_metadata.get(doc_id, {})
    if meta.get("identificador"):
        parts = [meta["identificador"]]
        if meta.get("organo"):
            parts.append(meta["organo"])
        return " | ".join(parts)
    return doc_id

def get_doc_path(doc_id):
    """Relative path to the source HTML file."""
    # Ensure the .html extension matches disk convention
    filename = doc_id if doc_id.endswith('.html') else f'{doc_id}.html'
    return f'{SOURCE_BASE}/{filename}'

# Both functions are called at context-build time, injected into the prompt.
# The response then shows:
#   CAS. N° 15-2015 LAMBAYEQUE | Corte Suprema
#   → Jurisprudencia/1612215.html
```

## Integration Points in Lex RAG

### Monolithic CLI (`graphrag_console.py`)
Already has `get_doc_label()`. Add `get_doc_path()` and inject into the context alongside the label. No prompt changes needed — the model already receives labels and will naturally display them.

### Modular Pipeline (`graphrag_pro.py`)
Does NOT use `get_doc_label()`. Currently shows bare `[Doc: filename]` format.
The patch points are:

1. **`retrieval/hybrid_search.py`** — injects `[Doc: {doc_id}]` into context. Replace with `[get_doc_label(doc_id)] (→ {get_doc_path(doc_id)})`.
2. **`retrieval/graph_search.py`** — injects `[Doc ID: {n}]` in graph context. Replace with the same label+path format.
3. **`agents/synthesizer.py`** — the prompt should tell the model to use the new format for citations.

### API (`api.py`)
Same as modular pipeline — the context is built by `get_hybrid_context()` and `get_graph_context()`.

## Verifying Links Work

After implementing, run this test across all found document IDs:

```python
import os
SOURCE_BASE = "Jurisprudencia"

# Test that every doc_id in FAISS metadata resolves to a real file
import pickle
with open('data/indices/faiss_meta_pro.pkl', 'rb') as f:
    meta = pickle.load(f)

all_doc_ids = set(m['doc_id'] for m in meta)
missing = [d for d in all_doc_ids if not os.path.exists(f'{SOURCE_BASE}/{d}')]
print(f'Total unique docs: {len(all_doc_ids)}')
print(f'Missing files: {len(missing)}')
if missing:
    print(f'Sample missing: {missing[:5]}')
```

If source files are missing, implement the link anyway but note the gap to the user.
