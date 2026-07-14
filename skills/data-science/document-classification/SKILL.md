---
name: document-classification
description: "Classify large batches of PDF documents by content type using regex + embeddings. Covers sample exploration, calibration, bulk processing with pymupdf, symlink organization, and embedding fallback."
version: 1.0.0
category: data-science
tags:
  - document-classification
  - pdf
  - pymupdf
  - regex
  - embeddings
  - sentence-transformers
  - clustering
created: 2026-06-05
---

# Document Classification (Bulk PDF)

Classify tens-to-hundreds of thousands of PDFs by content type using a two-phase approach: fast regex rules first, then embedding + clustering for the remainder.

## When to Use

- You have a large directory of PDFs (10K+) that need sorting by document type
- The documents share a domain vocabulary (legal, medical, financial, academic)
- You need categorized output folders (symlinks or copies) plus a CSV report
- You need to minimize false positives and catch edge cases

## Do NOT Use This For

- Fewer than ~1000 documents — just use a one-shot script
- Documents needing per-document LLM analysis — this is bulk classification
- Scanned/image PDFs — use marker-pdf OCR first, save as text, then classify

## Workflow

### Phase 1: Sample Exploration & Rule Calibration

Before writing the full classifier, calibrate your regex rules on a representative sample:

```python
import fitz, os, re, random, glob
from collections import Counter

PDF_DIR = "/path/to/pdfs"
random.seed(42)
all_pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
sample = random.sample(all_pdfs, 500)

# Draft tentative patterns — order matters (most specific first)
PATTERNS = {
    "sentencia": [r'\bSENTENCIA\b', r'\bFALLO\b', r'VISTA LA CAUSA'],
    "notificacion": [r'C[EÉ]DULA\s+DE\s+NOTIFICACI[OÓ]N', r'NOTIFIQU[EÉ]SE'],
    # ... add more categories based on document content
}

cats = Counter()
for p in sample:
    doc = fitz.open(p)
    txt = doc[0].get_text()[:1000]  # First page often has title
    doc.close()
    upper = txt.upper()
    found = False
    for cat, patterns in PATTERNS.items():
        for pat in patterns:
            if re.search(pat, upper):
                cats[cat] += 1
                found = True
                break
        if found: break
    if not found:
        cats["no_clasificado"] += 1

for k, v in cats.most_common():
    print(f"  {k}: {v} ({v/len(sample)*100:.1f}%)")
```

**Key calibration steps:**
1. Run the sample — check what % is "no_clasificado"
2. Inspect unclassified docs — read their text to find missed patterns
3. **PITFALL: "Resolución N°" vs "RESOLUCIÓN NÚMERO"** — Peruvian docs use both `N°` and `NÚMERO`. Add both patterns.
4. **PITFALL: Repeated text** — Some PDFs embed text multiple times per page (watermark effect). Strip duplicates in extraction or use case-insensitive match.
5. **Priority matters** — Put `sentencia` before `resolucion_generica` because "SENTENCIA" also appears inside resolutions.

### Phase 2: Bulk Classifier

Structure your script as:

```
src/
  clasificador.py         # Main classifier
data/
  clasificacion_completa.csv   # Output report
  resumen_clasificacion.json   # Summary stats
Clasificados/
  Sentencia/              # Symlinks to classified PDFs
  Resolucion/
  Notificacion/
  ...
```

**Core pattern:**

```python
import fitz, os, re, csv

CATEGORIES = {
    "sentencia": [r'\bSENTENCIA\b', r'\bFALLO\b'],
    "resolucion_generica": [r'RESOLUCI[OÓ]N\s+N[UÚ]MERO', r'RESOLUCI[OÓ]N\s+N[°º]'],
    # ...
}
CATEGORY_NAMES = {
    "sentencia": "Sentencia",
    "resolucion_generica": "Resolución",
    # Friendly names for folders and reports
}

def extraer_texto(pdf_path, max_pages=5):
    doc = fitz.open(pdf_path)
    txt = ""
    for i in range(min(len(doc), max_pages)):
        txt += doc[i].get_text()
    doc.close()
    return txt, len(doc)

def clasificar(texto):
    if len(texto) < 50:
        return "sin_texto", 0.0
    upper = texto.upper()
    for cat, patterns in CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, upper):
                return cat, 1.0
    return "no_clasificado", 0.0

def crear_symlink(origen, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if os.path.islink(destino) or os.path.exists(destino):
        os.remove(destino)
    os.symlink(origen, destino)
```

**Why symlinks (not copies or moves):**
- Original files stay intact — zero risk
- Zero extra disk space
- If rules are wrong, just delete the symlink dir and re-run
- Backup the original folder once, and all classification is implicitly backed up

### Phase 3: Embeddings Fallback for Unclassified

When regex leaves a tail of unclassified documents:

```python
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')  # Runs on CPU, ~500 docs/s

# Collect texts from unclassified PDFs
texts = []
paths = []
for p in unclassified_pdfs:
    txt, _ = extraer_texto(p, max_pages=3)
    texts.append(txt[:500])  # First 500 chars is enough for clustering
    paths.append(p)

# Vectorize and cluster
embeddings = model.encode(texts, show_progress_bar=True)
n_clusters = min(12, len(embeddings) // 50)  # ~50 docs per cluster
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
labels = kmeans.fit_predict(embeddings)

# For each cluster, show representative docs
for cluster_id in range(n_clusters):
    indices = np.where(labels == cluster_id)[0]
    print(f"\nCluster {cluster_id}: {len(indices)} docs")
    for idx in indices[:3]:
        print(f"  {paths[idx]} — {texts[idx][:200]}")
```

**Hybrid approach (optional):** Use an LLM (via Ollama) to label each cluster by reviewing 1-2 representatives, rather than classifying each document individually.

### Phase 4: Report & Organization

Generate CSV with:
- `filename, categoria, nombre_categoria, confianza, expediente, juzgado, paginas, size_kb, ruta_original`

Generate JSON summary with distribution stats.

## Pitfalls

1. **PDF text duplication** — Some PDF generators repeat text 3-4x per page. Always check raw output before trusting pattern matching. If severe, deduplicate lines in extraction.
2. **Mixed encoding** — Tildes and ñ appear as raw bytes or decomposed forms. Always use `upper()` and search for both `Ó` and `O` in patterns (or remove accents).
3. **Multi-page titles** — Some documents have the title on page 2 (cover page has no classification text). Extract at least 3-5 pages.
4. **Interleaved runs** — A `sentencia` may contain "RESOLUCIÓN NÚMERO: VEINTE" on an earlier page. The most specific category must be checked FIRST to avoid generic matches.
5. **Symlink cleanup** — When re-running, remove old symlink dirs first. Use `find Clasificados -type l -delete` before a fresh run.
6. **File handle leaks** — Always `doc.close()` after `fitz.open()`. With 500K+ files, unclosed handles will exhaust system limits.
7. **Performance** — `pymupdf` at ~130 docs/s on modern CPU. For 500K docs, budget ~65 min. Use background processes and monitor with symlink count or CSV line count.

## Verification

After classification, verify by:
1. Spot-check 10 random symlinks per category — do they actually belong?
2. Check unclassified docs — are they truly ambiguous or did a pattern miss?
3. Run count validation: total symlinks = processed files - errors

## Extending Beyond Classification

This skill covers **classification by type** (sentencia, resolucion, notificacion, etc.).
For **content extraction** (hechos, fallo, entidades) and **RAG indexing** of classified
documents, see the sibling skill:

▶ **`rag-data-ingestion`** — Batch LLM extraction via Groq/OpenAI API + FAISS/BM25/Graph indexing

The typical workflow is: classify with this skill first, then extract content with `rag-data-ingestion`.

## References

- `references/peruvian-judicial-patterns.md` — Regex patterns for classifying Peruvian court resolutions (sentencias, resoluciones, notificaciones, oficios, etc.)
- `scripts/clasificador_referencia.py` — Runnable classifier template (edit PDF_DIR/OUT_BASE, then execute)
