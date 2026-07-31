# Lightweight Legal Search RAG — Patterns (TC_SearchRAG)

For small-to-medium legal corpuses (<20K docs) where documents are self-contained
(no cross-document graph relationships needed).

## Corpus sizing decisions — what to include/exclude

| Component | Include when | Skip when |
|-----------|-------------|-----------|
| FAISS + BM25 + RRF | Always | — |
| Graph (NetworkX) | Docs share entities (judges, laws, parties) | Docs are self-contained TC/HC sentences |
| CriticAgent | >20K docs where LLM might hallucinate | <5K docs, responses cite actual filenames |
| DeepSearcher (multi-query) | Corpus >10K or document chunks <200 words | Corpus <5K, each doc is a complete chunk |
| RetrievalStrategist (adaptive top_k) | Wide variety of query types | All queries similar, top_k=7 works for all |
| Chunking | Documents >1500 words | Documents <1000 words (use 1 doc = 1 chunk) |
| Cache (exact + semantic) | >50 queries/day expected | MVP / low usage |

## Hybrid metadata extraction

Pattern: **regex first, Groq only for ambiguity** (covers 90%+ with $0 cost)

```python
# 30+ regex rules ordered by specificity (most specific first)
MATERIA_RULES = [
    (r"enfermedad profesional|silicosis|neumoconiosis", "Enfermedad Profesional"),
    (r"cosa juzgada|amparo contra amparo", "Procesal Constitucional"),
    (r"pension|jubilacion|ONP|SNP|Comar|AFP", "Pensiones"),
    (r"despido|reposicion laboral|SERVIR", "Laboral"),
    (r"tributo|impuesto|sunat|IGV", "Tributario"),
    (r"libertad|detencion|prision|arresto", "Libertad Personal"),
    # ... 25+ more
]

def extraer_materia(texto):
    matches = [(pat, mat) for pat, mat in MATERIA_RULES if re.search(pat, texto, re.I)]
    if len(matches) == 1:
        return matches[0][1], "regex"        # ✅ Confianza alta, $0
    elif len(matches) > 1:
        return matches[0][1], "regex_multiple"  # ⚠️ Ambiguo → Groq resolverá
    else:
        return "", "no_match"                  # ❌ Sin match → Groq clasificará
```

**Cost**: 10,965/11,483 docs (95%) went to Groq in the TC run, costing ~$0.16 total
for llama-3.1-8b at ~$0.000015/call. The high Groq rate was because most 2005 scanned
PDFs had poor OCR, preventing regex matches. For clean digital PDFs (2024+), regex
would cover >60%.

## Batch embeddings for performance

Instead of encoding one document at a time (~400ms/doc), batch encode 50 at a time:

```python
BATCH_SIZE = 50
batch_textos = []

for i, (ruta, fname, ...) in enumerate(all_pdfs):
    texto = extract_pdf_text(ruta)  # individual PDF reading (I/O bound)
    batch_textos.append(texto)
    
    if len(batch_textos) >= BATCH_SIZE or i == len(all_pdfs) - 1:
        # Batch encode: ~0.6s for 50 docs vs ~20s one-by-one
        vecs = embedder.encode(batch_textos, show_progress_bar=False)
        vecs = np.array(vecs).astype('float32')
        index.add(vecs)
        batch_textos = []
```

**Benchmark**: 11,483 docs in ~145 min (WSL, /mnt/d/ filesystem). Without batching,
estimated ~480 min.

## Multi-source PDF indexing

Discovery pattern for multiple directories:

```python
FUENTES = [
    {"path": "/mnt/d/PyCode/TC_SearchRAG/files", "nombre": "TC 2005"},
    {"path": "/mnt/d/PyCode/TC_SEDETC_Scraper/pdfs", "nombre": "TC SEDETC"},
]

def discover_pdfs():
    for fuente in FUENTES:
        for root, dirs, fnames in os.walk(fuente["path"]):
            for f in fnames:
                if f.endswith(".pdf"):
                    all_pdfs.append((os.path.join(root, f), f, fuente["nombre"]))
```

Support `--append` mode using file checksums (MD5 of first 64KB + filesize):

```python
def file_checksum(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        h.update(f.read(65536))
        h.update(str(os.path.getsize(path)).encode())
    return h.hexdigest()
```

## Filter-based search with structured metadata

After metadata extraction, search results can be filtered instantly (no LLM):

```python
def aplicar_filtros(candidates, metadata, ...):
    for doc_id in candidates:
        m = metadata[doc_id]
        if args.materia and args.materia.lower() not in m["materia"].lower():
            continue
        if args.juez and not any(args.juez.lower() in j.lower() for j in m.get("jueces",[])):
            continue
        if args.anio and str(args.anio) != m.get("anio"):
            continue
        if args.cosa_juzgada is not None and m.get("es_cosa_juzgada") != args.cosa_juzgada:
            continue
        resultado.append(doc_id)
    return resultado
```

Performance: filter-only search (no text query) in ~5-10ms for 11K docs.
Combined with text search: ~50-100ms.

## Narrative/conversational RAG responses

Two distinct response modes:

| Mode | Script | Tone | Use case |
|------|--------|------|----------|
| Legal formal | `ask_tc.py` | Structured, analysis sections, legal terms | Lawyers, researchers |
| Narrative | `narrar_tc.py` | Conversational, analogies, plain language | End users, clients |

Narrative response prompt pattern (see full version in `references/narrative-legal-rag.md`):

```
"Eres un abogado peruano experto en derecho constitucional, pero hablas como una
persona normal. Tu misión es EXPLICAR la jurisprudencia del Tribunal Constitucional
de forma que cualquier persona sin estudios legales lo entienda.

IMPORTANTE: NO uses jerga legal complicada. NO hables como un juez. Habla como un
colega que te está explicando algo en una conversación.

1. Empieza con una respuesta DIRECTA y CLARA. Una frase corta.
2. Explica usando los casos concretos. Menciona números de expediente.
3. Usa analogías y ejemplos cotidianos. "Es como cuando..."
4. Si la respuesta es "depende", explica de qué depende.
5. Termina con un consejo práctico o una pregunta para seguir.
6. Tono: conversación de café, no audiencia en la corte."
```

## Reference project

Project: `D:\PyCode\TC_SearchRAG\` (WSL: `/mnt/d/PyCode/TC_SearchRAG/`)

| File | Purpose | Lines |
|------|---------|-------|
| `src/index_tc.py` | Multi-source PDF indexer with hybrid metadata | 561 |
| `src/search_tc.py` | Search with FAISS+BM25+RRF + filters | 296 |
| `src/narrar_tc.py` | Narrative/conversational query mode | 372 |
| `src/ask_tc.py` | Formal legal query mode (DeepSeek/Groq) | 372 |
| `src/app.py` | FastAPI REST with filter endpoints | 130 |
| `src/auditar.py` | Post-indexing audit + cost report | 186 |

Costs (11,483 doc corpus):
- Indexing: $0 (all local CPU)
- Groq for metadata (~11K ambiguous docs): ~$0.16
- Per NL query (DeepSeek): ~$0.0016
- Per NL query (Groq 70b): ~$0.0043
