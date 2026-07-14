# Document Ingestion & Chunking Strategies

## Auto-Detection of Document Type

Before chunking, scan the first ~100 lines to determine document type. Use a scoring system with weighted patterns:

```python
def detect_doc_type(text: str) -> str:
    scores = {
        "contrato": 0,
        "resolucion": 0,
        "sentencia": 0,
        "libro": 0,
        "informe": 0,
        "norma": 0,
        "generico": 0,
    }
    # Contrato patterns
    if re.search(r"(?i)CLAUSULA\s+(PRIMERA|SEGUNDA|TERCERA|\d+)", text):
        scores["contrato"] += 3
    if re.search(r"(?i)(EL|LA)\s+(CLIENTE|CONSULTOR|LOCADOR|PRESTATARIO)", text[:1000]):
        scores["contrato"] += 2
    # Resolucion / Sentencia patterns
    if re.search(r"(?i)CONSIDERANDO[:]*", text):
        scores["resolucion"] += 3
        scores["sentencia"] += 2
    if re.search(r"(?i)SE\s+RESUELVE", text):
        scores["resolucion"] += 3
    if re.search(r"(?i)(VISTOS|VISTA)\s*:", text):
        scores["sentencia"] += 3
    if re.search(r"(?i)FALLA\s*:", text):
        scores["sentencia"] += 3
    # Libro patterns
    if re.search(r"(?i)CAPITULO\s+(I{1,3}|IV|V|VI|VII|VIII|IX|X|\d+)", text[:2000]):
        scores["libro"] += 3
    if re.search(r"(?i)(INDICE|INTRODUCCION|PROLOGO)", text[:500]):
        scores["libro"] += 1
    # Informe patterns
    if re.search(r"^(I{1,3}|IV|V|VI|VII|VIII|IX|X)\.\s+[A-Z]", text, re.MULTILINE):
        scores["informe"] += 3
    if re.search(r"^(1|2|3|4|5)\.\s+[A-Z]", text, re.MULTILINE):
        scores["informe"] += 2
    # Norma patterns
    if re.search(r"(?i)ARTICULO\s+\d+[°º]?\s*[.-]", text):
        scores["norma"] += 3
    if re.search(r"(?i)(TITULO|LIBRO)\s+(I{1,3}|IV|V|VI|VII|VIII|IX|X|\d+)", text[:2000]):
        scores["norma"] += 2

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "generico"
```

**7 types supported:** contrato, resolucion, sentencia, libro, informe, norma, generico

## Per-Type Chunking Strategies

| Type | Strategy | Regex Pattern |
|------|----------|---------------|
| **contrato** | By clause (`CLÁUSULA PRIMERA`) | `(?i)CLAUSULA\s+(PRIMERA\|\d+\|I{1,3})` |
| **resolucion** | By considering (`CONSIDERANDO Primero`) | `(?i)CONSIDERANDO\s*[:]` + `(?i)SE RESUELVE` |
| **sentencia** | By block (`VISTOS`, `CONSIDERANDO`, `FALLA`) | `(?i)(VISTOS\|FALLA)` — 3 blocks max |
| **libro** | By chapter (`CAPITULO I`) + subsection | `(?i)CAPITULO\s+(I{1,3}\|IV\|V\|\d+)` |
| **informe** | By numbered section (`I.`, `1.`, `A.`) | `^(I{1,3}\|\d+\.\d+\|[A-Z]\.)\s+` |
| **norma** | By article (`ARTICULO 1°`) | `(?i)ARTICULO\s+\d+[°º]?` |
| **generico** | 512-token sliding window, 100-token overlap | N/A — paragraph-based |

### Contract Chunking (contrato)
```
Input: contrato con 12 clausulas
Output: 12 chunks (1 por clausula) + 1 chunk inicial (partes)
Metadata: section="Clausula Primera", tipo="clausula"
```

### Resolution Chunking (resolucion)
```
Input: resolucion con 5 considerandos + 6 articulos
Output: 5 chunks (considerandos) + 1 chunk (parte resolutiva)
Metadata: section="Considerando Primero", tipo="considerando"
```

### Book Chunking (libro)
```
Input: libro con 5 capitulos, cada uno con 3 secciones
Output: 5 chunks (capitulos) + chunks anidados (secciones)
Metadata: path=["doc_id", "Capitulo I", "Seccion 1.1"]
```

### Generic Chunking (generico)
When no structure is detected, use paragraph-based sliding window:
- ~2048 chars (~512 tokens) per chunk
- ~400 char overlap (~100 tokens)
- Preserve paragraph boundaries (don't split mid-paragraph)
- Store line_start/line_end from original text

## Category as Hint

The user-assigned category acts as a HINT, not a rule:

```python
def process_document(file_path, categoria=None):
    text = parse_document(file_path)
    
    # Always auto-detect (category is for organization, not chunking)
    strategy = detect_doc_type(text)
    
    # Only override if category provides a stronger signal
    # (e.g., categoria="Contratos/Prestamos" -> favor "contrato")
    if categoria:
        category_hint = categoria.split("/")[0].lower()
        if category_hint == "contratos":
            strategy = override_if_ambiguous(text, strategy, "contrato")
    
    return chunk_by_strategy(text, strategy)
```

## Hierarchical Categories

Store categories as path strings with "/" separator:

```
Contratos/Prestamos/Hipotecarios
Contratos/Arrendamiento
Resoluciones/Municipales
Libros/Doctrina
```

**Query patterns:**
```sql
-- All docs in "Contratos" and subcategories
SELECT * FROM documents WHERE categoria LIKE 'Contratos/%'

-- Exact match
SELECT * FROM documents WHERE categoria = 'Contratos/Prestamos'

-- First-level categories
SELECT DISTINCT SUBSTR(categoria, 1, INSTR(categoria || '/', '/') - 1) 
FROM documents
```

**UI:** Render as expandable tree:
```html
📁 Contratos
  📁 Prestamos
    📄 contrato_hipotecario.pdf
  📁 Arrendamiento
    📄 contrato_alquiler.pdf
📁 Resoluciones
  📄 resolucion_045.pdf
```

## Ingestion Pipeline Performance

**Parallel ingestion** with ThreadPoolExecutor:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def ingest_folder(folder_path, categoria="General"):
    files = list(Path(folder_path).rglob("*.pdf"))
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(process_document, str(f)): f
            for f in files
        }
        for future in as_completed(futures):
            result = future.result()
            texts = [c.content for c in result["chunks"]]
            embeddings = embedder.embed(texts)
            store.add_document(result["doc_id"], result["doc_name"], 
                             result["doc_hash"], result["num_chunks"],
                             categoria=categoria)
            store.add_chunks(result["chunks"], embeddings)
```

**Expected speedup:** 3-4x on CPU (4 workers). Chunking is regex-bound (Python), embedding is matrix-bound (CPU/GPU).

## Rust Optimization (Future)

Python regex chunking is 5-10x slower than Rust `regex` crate for the same logic. When document volume exceeds ~1000 and ingestion time becomes a bottleneck, port the chunking module to PyO3:

```rust
// lib.rs - PyO3 chunker
use pyo3::prelude::*;
use regex::Regex;

#[pyfunction]
fn chunk_text(text: &str) -> PyResult<Vec<PyObject>> {
    let clause_re = Regex::new(r"(?i)CLAUSULA\s+(PRIMERA|SEGUNDA|\d+)").unwrap();
    // ... chunking logic
}

#[pymodule]
fn krag_chunker(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(chunk_text, m)?)?;
    Ok(())
}
```

Build with `maturin build --release`. Import in Python as `import krag_chunker`.
