# Citation Format: File Paths in RAG Responses

Implementación realizada en Lex RAG (KGraphResolucionesV3) para que las respuestas incluyan identificador legible + ruta al archivo fuente.

## Files Modified

| File | Change |
|------|--------|
| `core/config.py` | Add `METADATA_DOCS_PATH` and `JURISPRUDENCIA_DIR` constants |
| `retrieval/hybrid_search.py` | Load metadata_docs.json, prepend `**{label}** → Jurisprudencia/{doc_id}` to each chunk |
| `retrieval/graph_search.py` | Show path alongside doc ID in graph context |
| `agents/synthesizer.py` | Update prompt instruction for citation format |

## Prompt Instruction (agents/synthesizer.py)

Before:
```
3. RIGOR CITACIONAL: Cita invariablemente el ID de cada documento que soporte tus afirmaciones (ej. "...según consta en el expediente [Doc: id_documento]").
```

After:
```
3. RIGOR CITACIONAL: Cita invariablemente el identificador legible del documento (RTF N°, CAS. N°, EXP. N°) y la ruta al archivo. Ejemplo: "según **CAS. N° 15-2015 LAMBAYEQUE** (Jurisprudencia/1612215.html)".
```

## Context Format (retrieval/hybrid_search.py)

Before:
```python
texts.append(f"[Doc: {m['doc_id']}]\n{m['text']}")
```

After:
```python
label = _doc_label(m['doc_id'])  # looks up metadata_docs.json
texts.append(f"**{label}** → Jurisprudencia/{m['doc_id']}\n{m['text']}")
```

## Context Format (retrieval/graph_search.py)

Before:
```python
contexto_grafo += f"\n--- [Doc ID: {n}] ---\n"
```

After:
```python
contexto_grafo += f"\n--- [{n}] ({JURISPRUDENCIA_DIR}/{n}) ---\n"
```

## Metadata Loader (retrieval/hybrid_search.py)

```python
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

## Dependencies

- `data/metadata_docs.json` — maps each .html filename to human-readable identifier
- `Jurisprudencia/` — directory with the original HTML files accessible by path
