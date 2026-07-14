# Chunking Strategies for Legal Documents

## Problem

Legal documents (sentencias, resoluciones) have a characteristic structure: narrative facts → legal reasoning → **fallo (final ruling)**. Naive truncation-by-position (e.g., first 7,000 chars) systematically **loses the fallo** because it appears at the end. In a test with a 17K-char resolution:

```
Naive 7K truncation:
[EXTRACTO: 7,000 chars...] → ✗ RESUELVE (lost!) ✗ Firmas (lost!) ✗ Notas al pie (lost!)
                                1,659 chars of critical content gone
```

## Strategy 1: Priorizar Fallo (Tail-First)

Takes the **last N paragraphs** first (the fallo), then prepends as many initial paragraphs as fit.

```
Chunk: [contexto inicial... ...parte resolutiva RESUELVE...] ✓
               [fundamentos medios...] ✗ (sacrificed)
```

**Use when:** Single-pass indexing, throughput > completeness. Good for rapid indexing of known document types.

## Strategy 2: Multi-Pass with Overlap (Recommended)

Divide into fixed-size chunks with configurable overlap. Each chunk is processed independently.

```
Chunk 1: [inicio del documento...    ...fundamento 1...]  → Qwen
Chunk 2:        [...fundamento 1...  ...fundamento 2...]  → Qwen  (overlap region)
Chunk 3:                               [...fundamento 2...  ...RESUELVE...]  → Qwen
```

**Parameters:**
- `chunk_size=4000` chars (≈1000 tokens for Spanish legal text)
- `overlap=500` chars (≈125 tokens)
- A 17K-char document produces ~6 chunks

**Pipeline integration:**
```python
from chunking_demo import chunk_multi_pass, extraer_texto

text = extraer_texto(pdf_path)
chunks = chunk_multi_pass(text, chunk_size=4000, overlap=500)
# Process each chunk independently via Groq/LLM
results = [procesar(chunk) for chunk in chunks]
# Merge: last chunk contains fallo, earlier chunks have context
```

**PITFALL:** Chunks are indexed separately in FAISS. A single query may match chunks from different parts of the same document — the synthesizer needs to handle this (de-duplicate by doc_id, merge context).

## Strategy 3: Semantic Paragraph Chunking

Detects structural markers and never splits a paragraph:

```python
import re

SECTION_HEADERS = [
    'RESUELVE', 'CONSIDERANDO', 'VISTOS', 'EXPEDIENTE',
    'S.S.', 'FIRMA', 'NOTIFICACIÓN', 'CORTE SUPREMA'
]

def chunk_semantic(text, max_chars=4000, overlap_paragraphs=2):
    # Split by double newline (paragraph boundaries)
    paragraphs = re.split(r'\n\s*\n', text)
    header_pattern = '|'.join(SECTION_HEADERS)
    
    chunks, current, current_len = [], [], 0
    for i, p in enumerate(paragraphs):
        p_len = len(p) + 1
        
        # Force split at section headers even if under max_chars
        if re.search(header_pattern, p, re.IGNORECASE) and current:
            chunks.append('\n\n'.join(current))
            # Keep overlap_paragraphs from end of previous chunk
            overlap = current[-overlap_paragraphs:] if len(current) >= overlap_paragraphs else current
            current = list(overlap)
            current_len = sum(len(x) + 1 for x in current)
        
        if current_len + p_len > max_chars and current:
            chunks.append('\n\n'.join(current))
            overlap = current[-overlap_paragraphs:] if len(current) >= overlap_paragraphs else current
            current = list(overlap)
            current_len = sum(len(x) + 1 for x in current)
        
        current.append(p)
        current_len += p_len
    
    if current:
        chunks.append('\n\n'.join(current))
    return chunks
```

**PITFALL:** `pdftotext -layout` breaks multi-line paragraphs into separate lines. The double-newline split may produce hundreds of single-line "paragraphs" from columns or indented text. For court documents, section headers are a more reliable boundary than whitespace.

## Benchmark: 3 Strategies on a Real Document

Document: 01_res_2015005400192025000018963.pdf (17,051 chars)

| Strategy | Chunks | Fallo preserved? | Middle content preserved? | Notes |
|----------|:------:|:----------------:|:------------------------:|-------|
| Naive 7K truncation | 1 | ✗ | Partial | Loses last 1,659 chars |
| Priorizar fallo (5.5K) | 1 | ✓ | Partial | Sacrifices ~50% middle |
| Multi-pass overlap (4K+500) | 6 | ✓ | ✓ | Complete coverage |
| Semantic paragraphs | 4 | ✓ | ✓ | Clean boundaries, fewer chunks |

**Recommendation:** Multi-pass with overlap for production. Semantic paragraph for highest-quality indexing where document structure is consistent.
