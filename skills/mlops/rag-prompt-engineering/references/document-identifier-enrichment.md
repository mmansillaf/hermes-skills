# Document Identifier Enrichment: Case Study

## Context

Lex RAG: a GraphRAG system for 64,186 Peruvian legal resolutions (HTML files).
The system originally referenced documents by HTML filename (`[Doc: 408739.html]`),
which is meaningless to lawyers. Each HTML file had a structured header with
a human-readable identifier, but this metadata was never extracted.

## The Fix: One-Time Regex Extraction from Source

Instead of reprocessing all 64K documents through the LLM (costly, slow),
we wrote a parallel extraction script that reads just the first 30 lines of
each HTML file and extracts identifiers using regex patterns.

### Pattern Set (Peruvian Legal Domain)

```python
# Tribunal Fiscal (Tax Court)
# Header: "RTF N°\n09457-5-2004"  (cross-line)
re.search(r'RTF\s*N[°º]?\s*\n?\s*([\d\-]+)', header)
# Result: "RTF N° 09457-5-2004 | Tribunal Fiscal"

# Corte Suprema - Casacion (Supreme Court - Appeal)
# Header: "CAS. N° 517-2016-ICA (02/05/2017)"
re.search(r'(?:CAS|Cas)[\.\s]*(?:LAB[\.\s]*)?N[°º]?\s*([\d\-]+\s*[\-\w]*\s*[\w]*)', header)
# Result: "CAS. N° 517-2016-ICA | Corte Suprema - Sala Civil"

# Tribunal Constitucional (Constitutional Court)
# Header: "EXP. N°\n1397-2001-AA/TC"  (cross-line)
re.search(r'EXP[\.\s]*N[°º]?\s*\n?\s*([\d]+(?:-[\d]+)*(?:/[A-Za-z0-9]+)*)', header)
# Result: "EXP. N° 1397-2001 | Tribunal Constitucional"
```

### Results

| Metric | Value |
|--------|-------|
| Files processed | 64,186 |
| Time (8 threads) | 4.3 min |
| With identifier | 100% |
| With court name | 70% |
| With date | 21% |
| API calls | 0 (zero) |
| Storage | 10 MB JSON |

## Integration in the RAG Pipeline

The metadata mapping is loaded at startup alongside FAISS and NetworkX:

```python
# At module level (one-time load)
with open("metadata_docs.json") as f:
    docs_metadata = json.load(f)

def get_doc_label(doc_id):
    """Returns 'RTF N° 09457-5-2004 | Tribunal Fiscal' or fallback."""
    meta = docs_metadata.get(doc_id, {})
    if meta.get("identificador"):
        parts = [meta["identificador"]]
        if meta.get("organo"): parts.append(meta["organo"])
        if meta.get("fecha"):  parts.append(meta["fecha"][:35])
        return " | ".join(parts)
    return doc_id
```

Then injected at context-building time, before the prompt reaches the LLM:

```python
# Before (useless):
ctx += " [Doc: 408739.html] El Tribunal Fiscal revoco..."

# After (meaningful):
ctx += " [RTF N° 09457-5-2004 | Tribunal Fiscal] El Tribunal Fiscal revoco..."
```

The prompt template is then updated to tell the model to use these identifiers
in its citations, replacing the old `[Doc: filename]` format.

## Lessons

1. **Check the source format first** — regex from HTML headers is 100x faster and zero-cost
   compared to LLM reprocessing
2. **Parallelize** — 64K files at 8 threads took 4 min; single-threaded would be 30+
3. **Fallback matters** — the ~30% of documents where court name wasn't detected still
   show a partial identifier; better than a bare filename
4. **Inject at context time** — no need to re-index FAISS or rebuild the graph; the
   metadata is applied when building the LLM prompt, not when building the index
5. **Update the prompt instructions** — the LLM needs to know the new format exists
   or it will keep using the old internals IDs
