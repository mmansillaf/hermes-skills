---
name: rag-citation-audit
description: >
  Audit how a RAG system identifies and cites source documents in its responses.
  Traces metadata from raw documents through indexing, retrieval, context formatting,
  and LLM prompting to find and fix citation quality gaps.
---

# RAG Citation Audit

Use when the LLM's responses lack sufficient detail about source documents — weak identifiers,
missing court/judge/parties, uninformative citations like "según el documento" without specifics.

## When to use

- User asks about improving responses, adding better document references, or richer citations
- LLM cites only a doc_id or file path without meaningful context
- Citations feel incomplete or the LLM seems to "know" more about a case than it's citing
- Metadata from source documents (court, judge, parties, date) isn't appearing in responses

## Audit workflow

### Phase 1: Trace the data flow

Map the full pipeline: **Source → Index → Context → LLM Prompt → Response**

For each stage, inspect:

| Stage | What to check |
|---|---|
| **Source** | What metadata exists in the raw documents? (title, code, court, date, judge, parties, location, matter) |
| **Index** | What metadata is actually stored in the FAISS/BM25/vector index metadata? Is it rich or sparse? |
| **Context** | How is each document presented to the LLM? A header line? A label? Raw text only? |
| **Prompt** | What citation instructions does the LLM receive? Are specific fields named? |
| **Response** | What does the LLM actually output? Compare against what the context gave it. |

### Phase 2: Identify gaps

Common gap patterns:

1. **Missing metadata extraction** — Data exists in the source (HTML, PDF) but was never parsed into structured metadata
2. **Sparse metadata DB** — The metadata store (`metadata_docs.json`, vector index meta) has empty fields or generic placeholders
3. **Weak context header** — Context passes only a doc_id or short label per document, without city, judge, parties
4. **Vague prompt instruction** — Prompt says "cite the identifier" but doesn't name specific fields to include
5. **Siloed data sources** — Judge info in the graph, parties in metadata, case code in a separate DB — the LLM sees them separately and may not connect them

### Phase 3: Propose fixes

Ordered by impact:

1. **Enrich context headers** — Add a rich metadata block per document in the context (court, date, judge, parties, case code). Single biggest improvement.
2. **Extract more from sources** — Parse HTML/PDF for court, judge, parties, location. Often just regex patterns in a preprocessing step.
3. **Update the prompt** — Explicitly list the fields the LLM should include in each citation.
4. **Merge data sources** — Combine graph metadata (judges, laws) into the text context header so the LLM sees everything at once.

### Phase 4: Implement (beyond audit)

Once gaps are identified, apply fixes in this order — each builds on the one before:

| Order | Layer | What to fix | Impact | Risk |
|-------|-------|-------------|--------|------|
| 1 | **Context header** — `hybrid_search.py` | Enrich per-document header with órgano, fecha, materia from metadata DB | HIGH — LLM sees richer data immediately | LOW — safe, no re-indexing needed |
| 1.5 | **Precomputed graph entity lookup** — `scripts/build_doc_entities_lookup.py` | Extract entities from NetworkX into JSON; inject into chunk headers inline | HIGH — every chunk carries juez + partes, no separate section needed | LOW — one-time precompute, then zero overhead at query time |
| 2 | **Graph entity annotation** — `graph_analyst.py` | Annotate each doc's fallo section with jueces, partes, leyes from graph | HIGH — judge/parties appear inline, not siloed | LOW — just text formatting change |
| 3 | **Prompt instruction** — `synthesizer.py` | Explicitly list every field the LLM should include in each citation | MEDIUM — LLM needs instruction to use the enriched data | LOW — single prompt change |
| 4 | **Prompt tone correction** — `synthesizer.py` | Tell the LLM NOT to impersonate the court/judge. No "MAGISTRADO PONENTE", "CORTE SUPREMA", "Lima, [Fecha]" headers | MEDIUM — prevents tacky impersonation artifacts | LOW — single line in the prompt |

**Layer 1: Enrich context headers**

Replace a flat `_doc_label()` with a richer `_doc_header()` that returns (header_string, fecha, materia):

```python
def _doc_header(doc_id):
    meta = _docs_metadata.get(doc_id, {})
    ident = meta.get("identificador", "") or doc_id
    organo = meta.get("organo", "")
    parts = [f"**{ident}**"]
    if organo:
        parts.append(f" | {organo}")
    return "".join(parts), meta.get("fecha", ""), meta.get("materia", "")
```

Then in the context builder:

```python
header, fecha, materia = _doc_header(m['doc_id'])
extra = ""
if fecha: extra += f" | Fecha: {fecha}"
if materia: extra += f" | Materia: {materia}"
texts.append(f"{header}{extra}\\nJurisprudencia/{m['doc_id']}\\n{m['text']}")
```

**Layer 1.5: Precomputed graph entity lookup**

Instead of relying on the graph analyst to annotate entities at runtime (which happens AFTER context building, in a separate section), precompute a doc→entities JSON lookup from the graph. Then inject juez/partes directly into the context header at build time.

```python
# scripts/build_doc_entities_lookup.py — one-time run
def extract():
    G = pickle.load(open(GRAPH_PATH, 'rb'))
    doc_entities = {}
    for node, data in G.nodes(data=True):
        if data.get('tipo') != 'Documento':
            continue
        entry = {"jueces": [], "actores": [], "demandados": [], "leyes": []}
        for adj in G.neighbors(node):
            tipo = G.nodes[adj].get('tipo', '')
            if tipo == 'Juez':    entry["jueces"].append(adj.replace("Juez: ",""))
            elif tipo == 'Actor': entry["actores"].append(adj.replace("Actor: ",""))
            elif tipo == 'Demandado': entry["demandados"].append(adj.replace("Demandado: ",""))
            elif tipo == 'Ley':   entry["leyes"].append(adj.replace("Ley: ",""))
        doc_entities[node] = entry
    json.dump(doc_entities, open(OUTPUT_PATH, 'w', encoding='utf-8'))
```

At query time, `_doc_header()` loads this JSON and enriches every chunk header:

```python
def _doc_header(doc_id):
    meta = _docs_metadata.get(doc_id, {})
    ent = _docs_entities.get(doc_id, {})
    # ... header with ident + organo ...
    ent_lines = []
    if ent.get("jueces"):
        ent_lines.append(f"Juez: {', '.join(ent['jueces'][:3])}")
    actor_str = ", ".join(ent.get("actores", []))
    dem_str = ", ".join(ent.get("demandados", []))
    if actor_str or dem_str:
        ent_lines.append(f"{actor_str} | vs {dem_str}")
    partes_str = " | ".join(ent_lines)
    return header_str, fecha, materia, partes_str
```

**Context now looks like:**
```
**CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema - Sala Laboral
Juez: Yrivarren Fallaque, Arévalo Vela | Edgardo Hernán Asenjo Tamay | vs Poder Judicial
Jurisprudencia/1612215.html
{chunk text}
```

**Results:** 59,571 docs with entities. 44,824 with judges, 44,638 with actors, 43,698 with defendants. Zero additional latency per query (JSON is loaded once at startup).

**Layer 4: Prompt tone correction**

The LLM will try to impersonate the court if the prompt says "Actúa como un Magistrado". This produces artifacts like:

```
**MAGISTRADO PONENTE: [No identificado]**
**CORTE SUPREMA DE JUSTICIA — SALA LABORAL**
**Lima, [Fecha de emisión del presente dictamen]**
```

Fix: change the role from impersonator to analyst, and explicitly ban impersonation headers:

```python
prompt = """Actúa como un Analista Jurídico y Asesor Legal experto en derecho peruano.
...
4. TONO Y ESTRUCTURA: [...] IMPORTANTE: NO escribas encabezados como
"MAGISTRADO PONENTE", "CORTE SUPREMA", "Lima, [Fecha]" ni firmes como
si fueras un tribunal emitiendo una resolución. No te hagas pasar por un
juez. Eres un analista jurídico dando su opinión fundada en la jurisprudencia.
"""
```

**Layer 2: Graph entity annotation (alternative to Layer 1.5)**

If you don't want a precomputed JSON lookup, the graph analyst can annotate entities at runtime:

```python
lines.append(f"  [{doc}] ({JURISPRUDENCIA_DIR}/{doc})")
lines.append(f"    FALLO: {fallo}")
lines.append(f"    JUECES: {', '.join(jueces)}")
lines.append(f"    PARTES: Actor(es): {actor} | Demandado(s): {dem}")
lines.append(f"    LEYES: {', '.join(leyes[:4])}")
```

Pull this data from `entities[doc]` which is already populated by `_collect_entities()` — no new graph loading needed. Trade-off: entities appear in a separate section, not inline in the chunk header.

**Layer 3: Update the prompt**

Replace the generic "cite the identifier" instruction with explicit field listing:

```python
3. RIGOR CITACIONAL: Por cada documento que cites, DEBES incluir OBLIGATORIAMENTE:
   - Identificador legible (RTF N°, CAS. N°, EXP. N°)
   - Órgano jurisdiccional (ej: Corte Suprema - Sala Civil, Tribunal Fiscal, Tribunal Constitucional)
   - Fecha y lugar (ej: Lima, 30 de Octubre del 2003)
   - Juez ponente (si está disponible)
   - Partes procesales (Actor vs Demandado, si están disponibles)
```

### Phase 5: Verify

- Run a query that should trigger a citation and check the actual output
- Verify the LLM now includes: case code, court/órgano, date/location, judge, parties, file path
- Check edge cases: documents with empty metadata fields get handled gracefully

**Verification checklist:**

- [ ] Context header shows `**CAS. N° XXXX** | Corte Suprema - Sala X | Fecha: ...` before each chunk
- [ ] Graph section shows `JUECES: ...` and `PARTES: ...` under each doc's fallo
- [ ] LLM response cites full details (not just doc_id)
- [ ] Docs with empty metadata still show a reasonable fallback (filename or generic label)
- [ ] No regression in response quality or structure

## Reference files

- `references/lexrag-jurisprudencia-metadata-audit.md` — Full audit trace of Peruvian jurisprudence RAG: data flow, metadata gaps, HTML extraction opportunities, graph vs text silo issue, and ordered fix recommendations.
- `references/implementation-patterns.md` — Post-audit implementation recipes: graph entity lookup, context header enrichment, response format testing, log suppression, LLM provider acronyms, and silent 403 handling.

## Pitfalls

- **Don't assume the index metadata is rich** — always inspect actual stored fields. `_doc_label()` functions can return stale/sparse data.
- **The LLM can only cite what's in the context** — if you want full citations, put rich info into the context. The prompt alone won't fix missing data.
- **Graph data may exist separately from text chunks** — judges, parties, and laws may be in the graph context section while the hybrid context has only raw text. The LLM sees both but may not connect them. Merge them into a single header.
- **HTML documents may have rich text content but zero metadata extraction** — the title tag often only has a numeric ID. The real case name/code appears mid-way through the HTML body and needs extraction.
- **metadata_docs.json often has empty fields** — verify completeness before trusting it as a citation source.
- **Source path omission by LLM** — The context builder may correctly append `Jurisprudencia/XXXXX.html` to every chunk, but the LLM still drops it from some citations. Fix: use a visual marker prefix (`📄 FUENTE:`) on the source path line AND reinforce in the system prompt with escalated language ("NUNCA cites sin su `📄 FUENTE:` — respuesta INVÁLIDA si se omite"). Verified improvement: from 25% to 100% citation path inclusion in a 15-query legal RAG battery.
- **LLM invents entirely fake doc IDs** — Even when the context provides real `[Doc: actual_id]` prefixes, the LLM may generate completely fictitious IDs like `[Doc: TC-001]`, `[Doc: Ley N.° 27291]`, or `[Doc: 7605954]` that don't exist in the retrieval results. This is different from omitting citations — the LLM actively hallucinates identifiers.

  **Detection:** `verify_response_grounding()` checks every `[Doc: X]` in the response against the actual `doc_ids` list from retrieval. If `valid_citations = 0` despite a high `grounding_score`, the LLM is inventing IDs.

  **Root cause:** The synthesis prompt says "use [Doc: id_documento]" which the LLM treats as a placeholder to fill in creatively. Without explicit constraints, it generates IDs that sound plausible but don't exist.

  **Fix:** Add explicit anti-invention constraints to the synthesis prompt:
  ```
  CRÍTICO: SOLO puedes usar IDs que YA APARECEN en el contexto proporcionado 
  (ej: [Doc: 552066] o [Doc: 437043.html]). NUNCA inventes ni generes IDs nuevos 
  como "TC-001", "Doc-1" o similares. Cada [Doc: X] en tu respuesta debe coincidir 
  EXACTAMENTE con un ID que aparece en los fragmentos del CONTEXTO RECUPERADO.
  ```

  **Verification:** After the prompt fix, check that `valid_citations == total_citations` and `fully_grounded == True`. Without the explicit constraint, even a well-tuned RAG system will generate fake citations ~80% of the time.
