# Legal RAG at Scale — 10k-20k Word + PDF Documents

## Problem
Indexing 10,000-20,000 legal documents (.docx + .pdf) from a Windows folder and making them searchable with source citations.

## Architecture

```
1. EXTRACTION → 2. CHUNKING → 3. EMBEDDINGS → 4. INDEXING → 5. QUERIES

MarkItDown       Articles/      bge-m3           Qdrant +        DeepSeek
+ pymupdf        clauses        1024-dim         SQLite FTS5     + Groq
```

## Extraction

Primary: **MarkItDown** (Microsoft, ★118k) — handles both .docx and .pdf.
Fallback: **pymupdf** (fitz) — faster for PDFs when MarkItDown fails.

```python
# Strategy: try pymupdf first for PDF (faster), fallback to MarkItDown
def _extract_pdf(path):
    try:
        import fitz
        doc = fitz.open(str(path))
        return "\n\n".join(page.get_text() for page in doc)
    except:
        from markitdown import MarkItDown
        return MarkItDown().convert(str(path)).text_content
```

## Chunking — Legal-Specific

**Critical: DO NOT use fixed-token chunking for legal text.**

Legal documents are structured by articles, clauses, and sections. Chunking must preserve this structure.

```python
# Split by legal section markers
pattern = r'(?=(?:Art[ií]culo|Cl[aá]usula|Secci[oó]n)\s+\w+)'
sections = re.split(pattern, text, flags=re.IGNORECASE)
```

- Each chunk = 1 article/clause (max 4000 chars)
- Overlap 400 chars between consecutive chunks
- Metadata per chunk: filename, section name, page number

## Embeddings

Use **BAAI/bge-m3** (19M downloads, 1024-dim):
- Best multilingual model for Spanish
- Fits in 2GB RAM
- CPU-only viable for batch ingestion (30-60 min for 15k docs)

## Indexing

**Dual-store architecture:**
1. **Qdrant** (file mode, no server): semantic search via cosine similarity
2. **SQLite FTS5**: keyword search with BM25 ranking, accent-insensitive

```python
# Qdrant file mode — no Docker needed
client = QdrantClient(path="data/qdrant")

# SQLite FTS5 — built-in, accent-safe
CREATE VIRTUAL TABLE docs_fts USING fts5(
    doc_id, filename, section, text,
    tokenize='unicode61 remove_diacritics 2'
);
```

## Source Citation

System prompt enforces citation format:
```
[Fuente: nombre_archivo.docx, Articulo X]
```

Response structure:
```json
{
  "answer": "... [Fuente: ley_123.docx, Art. 15] ...",
  "sources": [
    {"filename": "ley_123.docx", "section": "Articulo 15", "relevance": 0.94}
  ]
}
```

## Incremental Indexing

Track indexed files in SQLite to support `--incremental` mode:
```python
# Only process new/modified files
indexed = get_indexed_files()  # from SQLite table
new_files = [f for f in all_files if str(f) not in indexed]
```

## Reference Implementation

https://github.com/mmansillaf/rag-legal-local (~1,100 lines Python)

Key files:
- `utils/extractor.py` — docx/pdf text extraction
- `utils/chunker.py` — legal article-based chunking
- `utils/embedder.py` — bge-m3 singleton
- `utils/indexer.py` — Qdrant + SQLite FTS5
- `utils/retriever.py` — dual-source search + dedup
- `utils/generator.py` — DeepSeek + Groq cloud APIs
- `ingestion_pipeline.py` — batch ingestion with --incremental
- `app.py` — Streamlit web UI for lawyers

## Pitfalls

1. **MarkItDown on large PDFs**: Can be slow. Use pymupdf first for PDFs.
2. **Accent handling**: Spanish accents break LIKE queries. Use FTS5 with `remove_diacritics 2`.
3. **getOoxml() limit**: Office.js has 10MB limit for Word docs. Use python-docx for extraction instead.
4. **Qdrant API change**: v1.10+ uses `query_points()`, not `search()`.
5. **Chunk overlap**: Too small (50 chars) → split sentences. Too large (1000) → duplicates. 400 is sweet spot.
