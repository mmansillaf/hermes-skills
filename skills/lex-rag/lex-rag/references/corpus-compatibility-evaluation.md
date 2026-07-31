# Corpus Compatibility Evaluation Framework

Methodology for assessing whether a new document set can be ingested into an existing LexRAG pipeline. Developed from the TC SEDETC PDF evaluation session (Jun 2026).

## Evaluation checklist

- [ ] Format — what format are the source documents? (HTML, PDF, DOCX, plain text)
- [ ] Text extractability — scanned images or digital text? Sample ≥30 docs across sizes
- [ ] Text quality — artifacts, garbled chars, watermarks? Check head/mid/tail of samples
- [ ] Metadata — does structured metadata exist (CSV, JSON, API)? Or must be extracted from content?
- [ ] Volume — total docs, total size, distribution across years/types
- [ ] Doc ID scheme — how are documents identified? (filename, expediente, hash)
- [ ] Cost estimate — one-time extraction cost via Groq Batch
- [ ] Pipeline changes — what stays, what changes (decision matrix)
- [ ] Backup — always backup existing indices before modifying

## Text extractability assessment (PDFs)

```python
import pymupdf, os, glob

def assess_pdf_quality(path):
    doc = pymupdf.open(path)
    pages = len(doc)
    chars = sum(len(p.get_text()) for p in doc)
    imgs = sum(len(p.get_images()) for p in doc)
    has_text = chars > 100 * pages  # heuristic: >100 chars/page = real text
    return {"pages": pages, "chars": chars, "images": imgs, "text": has_text}

# Sample across years and sizes
for year_dir in sorted(os.listdir(pdf_base)):
    pdfs = glob.glob(f"{pdf_base}/{year_dir}/*.pdf")
    sizes = [(os.path.getsize(f), f) for f in pdfs]
    sizes.sort()
    samples = [sizes[0], sizes[len(sizes)//2], sizes[-1]]
    for sz, path in samples:
        r = assess_pdf_quality(path)
        print(f"{os.path.basename(path)}: {r['pages']}p {r['chars']}c "
              f"{'TEXT' if r['text'] else 'SCAN'} imgs={r['images']}")
```

⚠️ **PyMuPDF throughput warning**: Opening each PDF individually has high per-file overhead.
For estimation, sample 100-200 PDFs — do NOT run full extraction. Real benchmark (T470p, 6 workers):
- 100 PDFs: ~20s
- 5,000 PDFs: ~15-20 min
- 11,224 PDFs: ~35-40 min

### Classification thresholds

| Chars | Category | Action |
|-------|----------|--------|
| <100 | Scanned/blank | Needs OCR (marker-pdf) or skip |
| 100-500 | Very short | Razón de Relatoría, auto — regex parseable |
| 500-2000 | Short | Low-cost extraction (8B model) |
| 2000-10000 | Medium | Full extraction |
| >10000 | Long | Full extraction (costs more) |

## Metadata conversion pattern

When the new corpus has structured metadata (e.g. CSV from a scraper), convert directly:

```python
import csv, json

TC_ORGANO = "Tribunal Constitucional"
TC_TIPO = "Sentencia TC"

with open("metadata.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    metadata_docs = {}
    for row in reader:
        filename = f"{row['expediente']}.pdf"
        metadata_docs[filename] = {
            "identificador": f"EXP. N° {row['expediente']}/TC",
            "organo": TC_ORGANO,
            "fecha": row.get("fecha_publicacion", ""),
            "materia": "",  # extracted by LLM in batch
            "tipo": f"{TC_TIPO} - {row.get('tipo', '')}",
            "demandante": row.get("demandante", ""),
            "demandado": row.get("demandado", ""),
            "sala": row.get("sala", ""),
        }

with open("data/metadata_docs.json", "w", encoding="utf-8") as f:
    json.dump(metadata_docs, f, ensure_ascii=False, indent=1)
```

This is more accurate and faster than regex extraction from raw HTML.

## Cost estimation formula (Groq Batch API, Jun 2026)

```python
total_docs = 11224
avg_words = 3000  # measured from sample
avg_tokens = avg_words / 0.75  # ~4000 tokens/doc

# Hybrid strategy: short (8B) vs long (70B) based on token count
# Threshold: 1000 tokens
# Short (≤1000t): llama-3.1-8b-instant  ~$0.0002/request (est)
# Long (>1000t):  llama-3.3-70b-versatile ~$0.0011/request (est)

short_ratio = 0.2  # estimate based on document type distribution
long_ratio = 0.8

cost = (total_docs * short_ratio * 0.0002 +
        total_docs * long_ratio * 0.0011)

time_hours = total_docs / 3000  # Groq Batch throughput ~3000 docs/hour
```

For the TC SEDETC corpus (11,224 PDFs): **~$10 USD, ~3-4 hours**.

## Trigger conditions

Load this reference when:
- User has a new set of legal documents to ingest
- User asks "can these files be processed like the originals?"
- User wants a cost/time estimate before committing to full ingestion
- User has PDFs (the original pipeline was HTML-based)
