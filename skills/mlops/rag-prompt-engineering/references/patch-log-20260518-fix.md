# Patch Log: Adding File Paths + Human-Readable IDs to Lex RAG Responses

**Date:** 2026-05-18  
**Trigger:** User reported that GraphRAG response cited documents as `[Doc: 1612215]` — opaque internal IDs with no way to open the source document.  
**Goal:** Make every document reference in the response show both a human-readable identifier (RTF N°, CAS. N°, EXP. N°) and a clickable file path.

## Files Modified (4 total)

### 1. `core/config.py` — Two new constants

```python
METADATA_DOCS_PATH = "data/metadata_docs.json"
JURISPRUDENCIA_DIR = "Jurisprudencia"
```

These are project-level path constants used by the retrieval modules. Centralized here so they're easy to find and change.

### 2. `retrieval/hybrid_search.py` — Context formatting (bulk of the work)

**Before:**
```python
texts.append(f"[Doc: {m['doc_id']}]\n{m['text']}")
```

**After:**
```python
label = _doc_label(m['doc_id'])
texts.append(f"**{label}** → Jurisprudencia/{m['doc_id']}\n{m['text']}")
```

**New helper functions added:**
```python
import json
_docs_metadata = {}
def _load_docs_metadata():
    global _docs_metadata
    if not _docs_metadata and METADATA_DOCS_PATH and os.path.exists(METADATA_DOCS_PATH):
        with open(METADATA_DOCS_PATH, 'r', encoding='utf-8') as f:
            _docs_metadata = json.load(f)

def _doc_label(doc_id):
    _load_docs_metadata()
    meta = _docs_metadata.get(doc_id, {})
    if isinstance(meta, dict):
        return meta.get("identificador", "") or doc_id
    return doc_id
```

Key design decisions:
- **Lazy loading**: Metadata JSON only loaded on first call, not at import time (avoids import-time file I/O).
- **Thread-safe for single-thread usage**: This RAG is single-user CLI; no locking needed.
- **Fallback**: If a doc_id has no metadata entry, it returns the raw doc_id — never a crash.

### 3. `retrieval/graph_search.py` — Graph context format

**Before:**
```python
contexto_grafo += f"\n--- [Doc ID: {n}] ---\n"
```

**After:**
```python
contexto_grafo += f"\n--- [{n}] ({JURISPRUDENCIA_DIR}/{n}) ---\n"
```

No metadata lookup here — the synthesizer prompt handles the human-readable label. The graph context just adds the file path so the LLM has it available.

### 4. `agents/synthesizer.py` — Prompt instruction

**Before:**
```
3. RIGOR CITACIONAL: Cita invariablemente el ID de cada documento
que soporte tus afirmaciones (ej. "...según consta en el expediente
[Doc: id_documento]").
```

**After:**
```
3. RIGOR CITACIONAL: Cita invariablemente el identificador legible
del documento (RTF N°, CAS. N°, EXP. N°) y la ruta al archivo.
Ejemplo: "según **CAS. N° 15-2015 LAMBAYEQUE** (Jurisprudencia/1612215.html)".
```

## Verified Behavior

After the fix, running the same query produces:

```
## Dictamen sobre la desnaturalización de contratos de trabajo

| Principio | Fuente |
|-----------|--------|
| Los contratos de servicios no personales pueden desnaturalizarse si se configuran los elementos de una relación laboral. | **CAS. N° 2322-2015-CAÑETE** (Jurisprudencia/1613661.html) |
| La acción de amparo no es vía idónea para resolver controversias sobre desnaturalización laboral. | **Expediente 440981** (Jurisprudencia/440981.html) |
```

The user can Ctrl+click `Jurisprudencia/1613661.html` in their terminal (or `open` / `xdg-open` it) to read the full source document.

## Remaining Issues Not Fixed

These were identified but not addressed in this patch:

1. **Router blind spot**: `ultima Ley 32186 sobre teletrabajo en Peru 2025` classified as LOCAL instead of WEB. The year 2025 guarantees this law is not in the pre-2024 corpus. Fix: add regex trigger for `año 202[5-9]` + `ley|decreto` in the router.

2. **Fallo not cited verbatim**: The modular pipeline's prompt doesn't mandate quoting the "fallo" (ruling) text. The monolithic CLI's prompt does. Fix: port the fallo mandate from `graphrag_console.py` to `agents/synthesizer.py`.

3. **"Corte Constitucional" hallucination**: The model used the Colombian name instead of "Tribunal Constitucional" (Peru). Fix: add a system message correcting institution names for Peru.

4. **Web search results not integrated**: When the router activates WEB mode, the SERPER results don't always reach the final response. The `serper_search()` function returns data but the synthesizer's prompt for WEB mode doesn't instruct the model to use it. Fix: improve the WEB-mode prompt in the synthesizer.

## Git Status After Patch

```
modified:   core/config.py
modified:   retrieval/hybrid_search.py
modified:   retrieval/graph_search.py
new file:   agents/synthesizer.py (was untracked, now tracked)
```
