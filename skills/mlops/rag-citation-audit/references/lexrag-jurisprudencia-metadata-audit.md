# LexRAG Jurisprudencia — Metadata Audit + Implementation (2026-06-01)

## Project context

64,186 Peruvian jurisprudence HTML files (Tribunal Fiscal, Corte Suprema, Tribunal Constitucional).
RAG pipeline: FAISS + BM25 + NetworkX → DeepSeek V4 Flash / Groq fallback.
Current branch: `feature/deep-research`.
Last commit: `b5a2fa4` (docs: cabeceras descriptivas en todos los scripts + README actualizado).

## Data flow traced

```
Jurisprudencia/1309310.html → data_raw/*.jsonl → indexer.py → FAISS+BM25+Grafo
                                                          ↓
                                            hybrid_search.py (_doc_header → context)
                                                          ↓
                                            synthesizer.py (LLM prompt → response)
                                                          ↓
                                            GraphAnalyst._format (ANÁLISIS DE PRECEDENTES)
```

## Source HTML content (1309310.html — laboral)

```html
Exp.
2608-2003-BE (S)
Señores: Torres Vega; Toledo Toribio; Nué Bobbio.
Lima, 30 de Octubre del 2003.-
VISTOS; ... interviniendo como Vocal Ponente el señor Omar Toledo Toribio; ...
```

The metadata_docs.json had only `{"identificador": "Exp."}` — stripped of all useful detail.

## metadata_docs.json state BEFORE fix

| Field | In HTML | In metadata_docs.json |
|---|---|---|
| Case code | `2608-2003-BE (S)` | `"Exp."` (truncated) |
| Court | Primer Juzgado Laboral de Lima | empty |
| Location/Date | `Lima, 30 de Octubre del 2003` | empty |
| Judge (Ponente) | `Vocal Ponente el señor Omar Toledo Toribio` | empty |
| Plaintiff | VICTOR RAUL VASQUEZ MALPICA | empty |
| Defendant | JAVIER CUEVA SUAREZ | empty |
| Matter | PAGO DE BENEFICIOS ECONOMICOS | empty |

## Graph data (NetworkX) — richer but siloed

The graph had full entity data (jueces, actores, demandados, leyes) from `data_raw/*.jsonl`, but it went into a SEPARATE section ("ANÁLISIS DE PRECEDENTES Y CONEXIONES"), not linked to the text chunks.

## 3-Layer implementation

### Layer 1: `retrieval/hybrid_search.py` — context headers

Replaced `_doc_label()` which returned only the bare identifier with `_doc_header()` that returns a tuple (header, fecha, materia):

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

Context format changed from:
```
**CAS. N° 15-2015 LAMBAYEQUE** → Jurisprudencia/1612215.html
{chunk}
```
To:
```
**CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema | Fecha: 6 de diciembre de 2016
Jurisprudencia/1612215.html
{chunk}
```

### Layer 2: `agents/graph_analyst.py` — entity annotation per document

In `_format()`, added inline entity lines after each fallo:

```python
# Jueces
lines.append(f"    JUECES: {', '.join(jueces)}")
# Partes
partes = []
if actor_str: partes.append(f"Actor(es): {actor_str}")
if dem_str:   partes.append(f"Demandado(s): {dem_str}")
lines.append(f"    PARTES: {' | '.join(partes)}")
# Leyes
lines.append(f"    LEYES: {', '.join(leyes[:4])} (+{restantes} más)")
```

Output example:
```
  [1309310.html] (Jurisprudencia/1309310.html)
    FALLO: La sentencia de primera instancia fue confirmada...
    JUECES: Omar Toledo Toribio
    PARTES: Actor(es): Victor Raul Vasquez Malpica | Demandado(s): Javier Cueva Suarez
    LEYES: Decreto Supremo 003-97-Tr, Art. 22º, 23º Y 24º
```

### Layer 3: `agents/synthesizer.py` — expanded citation prompt

Replaced the single-line instruction:
```python
"Cita invariablemente el identificador legible del documento (RTF N°, CAS. N°, EXP. N°) y la ruta al archivo."
```

With explicit field listing:
```python
"3. RIGOR CITACIONAL: Por cada documento que cites, DEBES incluir OBLIGATORIAMENTE:
   - Identificador legible (RTF N°, CAS. N°, EXP. N°)
   - Órgano jurisdiccional (ej: Corte Suprema - Sala Civil, Tribunal Fiscal, Tribunal Constitucional)
   - Fecha y lugar (ej: Lima, 30 de Octubre del 2003)
   - Juez ponente (si está disponible)
   - Partes procesales (Actor vs Demandado, si están disponibles)"
```

## Verification results

Test query: `"despido arbitrario en régimen laboral privado"`

### What improved

The response now includes **partes procesales by name** — not just document IDs:

> "En el **PROCESO DE AMPARO** (Jurisprudencia/1656988.html), seguido por **Juana Patricia Arriola Gutiérrez** contra la **Derrama Magisterial**..."

> "En el caso **JUNÍN** (Jurisprudencia/1495259.html), seguido por **Flor de María Puchoc Lara** contra el **Poder Judicial**..."

### What still needs work

- **Whole-case entity extraction from HTML**: The `extraer_metadata_html.py` regex extractor misses the full case code for some documents (e.g., `1309310.html` only gets "Exp." instead of "2608-2003-BE (S)"). The graph has this data but the metadata_docs.json doesn't. A full HTML re-extraction phase with better regex patterns could fix this.
- **LLM still uses pre-existing response structure**: The LLM started responding as "MAGISTRADO PONENTE: [No identificado]" — that's a pre-existing template behavior, not related to our changes.
- **Some docs lack graph data**: ~46K of 64K docs have graph nodes, so about 18K docs won't have entity annotation.

## Pre-existing reference files

- `scripts/data_prep/extraer_metadata_html.py` — regex-based metadata extraction from HTML files (run once, 8 threads)
- `data/metadata_docs.json` — 64,186 entries, ~7.5 MB
- `data/indices/graph_juris_pro.pkl` — NetworkX graph with 191,871 nodes (59,571 docs + jueces, leyes, actores, demandados)

---

## Layer 1.5 addition (2026-06-01): Precomputed graph entity lookup

### Problem

Layer 2 (GraphAnalyst entity annotation) puts juez/partes in a separate "ANÁLISIS DE PRECEDENTES" section. The LLM sees them but they're not inline with the chunk content. This means the LLM must mentally connect: "chunk from doc X" → "graph section says doc X has juez Y" → "I should mention juez Y". Sometimes it makes this connection, sometimes not.

### Solution

Precompute a `doc_entities.json` from the graph, then inject entities directly into the chunk header at context-building time. No runtime graph traversal needed.

### Implementation

**Script:** `scripts/build_doc_entities_lookup.py`

```python
def extract():
    G = pickle.load(open(GRAPH_PATH, 'rb'))
    doc_entities = {}
    for node, data in G.nodes(data=True):
        if data.get('tipo') != 'Documento':
            continue
        entry = {"jueces": [], "actores": [], "demandados": [], "leyes": []}
        for adj in G.neighbors(node):
            tipo = G.nodes[adj].get('tipo', '')
            if tipo == 'Juez':
                entry["jueces"].append(adj.replace("Juez: ", ""))
            elif tipo == 'Actor':
                entry["actores"].append(adj.replace("Actor: ", ""))
            elif tipo == 'Demandado':
                entry["demandados"].append(adj.replace("Demandado: ", ""))
            elif tipo == 'Ley':
                entry["leyes"].append(adj.replace("Ley: ", ""))
        doc_entities[node] = entry
    json.dump(doc_entities, open(OUTPUT_PATH, 'w', encoding='utf-8'))
```

**Timing:** 2.6s for 59,571 document nodes. 19.5 MB JSON file.

**Coverage:**

| Entity type | Docs with data |
|-------------|---------------|
| Judges | 44,824 (75%) |
| Actors | 44,638 (75%) |
| Defendants | 43,698 (73%) |
| Laws | 44,712 (75%) |

**Integration in `hybrid_search.py`:**

`_doc_header()` now loads the entities lookup and returns a 4th value — `partes_str`:

```python
def _doc_header(doc_id):
    _load_docs_metadata()
    _load_docs_entities()
    meta = _docs_metadata.get(doc_id, {})
    ent = _docs_entities.get(doc_id, {})
    # header with ident + organo
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

### Resulting context format

```
**CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema - Sala Laboral | Fecha: ...
Juez: Yrivarren Fallaque, Arévalo Vela | Edgardo Hernán Asenjo Tamay | vs Poder Judicial
Jurisprudencia/1612215.html
El Tribunal analizó la desnaturalización de contratos de trabajo...
```

The LLM sees juez AND partes inline with every chunk — no separate section to cross-reference.

---

## Layer 4 addition (2026-06-01): Prompt tone correction

### Problem

The original prompt said: `"Actúa como un Magistrado de la Corte Suprema..."`. This caused the LLM to impersonate the court, producing embarrassing headers:

```
**MAGISTRADO PONENTE: [No identificado]**
**CORTE SUPREMA DE JUSTICIA — SALA DE DERECHO CONSTITUCIONAL Y SOCIAL**
**Lima, [Fecha de emisión del presente dictamen]**
```

The `[No identificado]` and `[Fecha de emisión]` look unprofessional because they're obviously template fill-ins.

### Fix

Changed role and added explicit ban:

```python
prompt = """Actúa como un Analista Jurídico y Asesor Legal experto en derecho peruano.
...
4. TONO Y ESTRUCTURA: [...] IMPORTANTE: NO escribas encabezados como
"MAGISTRADO PONENTE", "CORTE SUPREMA", "Lima, [Fecha]" ni firmes como
si fueras un tribunal emitiendo una resolución. No te hagas pasar por un
juez. Eres un analista jurídico dando su opinión fundada en la jurisprudencia.
"""
```

### Result

Before: Response starts with impersonation headers and template fill-ins.
After: Response starts professionally — "A continuación, presento un análisis jurídico detallado..."

---

## Tests (2026-06-01)

Created `test_formato_respuesta.py` with 5 tests:

1. **test_doc_header_has_organo** — Verifies headers include `| Corte Suprema` etc.
2. **test_doc_header_has_entities** — Verifies `Juez:` and `vs` appear in headers for docs with graph data
3. **test_metadata_extraction** — Verifies metadata_docs.json has 64K+ entries
4. **test_entities_lookup** — Verifies doc_entities.json has 59K+ docs with entity data
5. **test_get_hybrid_context_format** — Verifies actual query context has `**` headers + `Jurisprudencia/` paths

All 5 pass. Run with: `python test_formato_respuesta.py`

---

## extraer_metadata_html.py improvement (2026-06-01)

### CAS. LAB. sala detection

Added sala detection from prefix before the regex that already captures the case code:

```python
cas_match = re.search(r'CAS\.\s*(CIV|LAB|CONST)\b', header, re.IGNORECASE)
if cas_match:
    sala_code = cas_match.group(1).upper()
    if sala_code == 'LAB':
        result["organo"] = 'Corte Suprema - Sala Laboral'
    elif sala_code == 'CIV':
        result["organo"] = 'Corte Suprema - Sala Civil'
    elif sala_code == 'CONST':
        result["organo"] = 'Corte Suprema - Sala Constitucional'
```

Previously, `1612215.html` (CAS. LAB. Nº 15-2015 LAMBAYEQUE) got `"Corte Suprema"` — now it gets `"Corte Suprema - Sala Laboral"` even without the text "SALA LABORAL" in the HTML body.

### Bare EXP pattern

Added pattern for documents where `Exp.` appears on one line and the number on the next (format used by laboral cases like 1309310.html):

```python
# Bare "Exp." on line N, number on line N+1
m = re.search(r'^Exp\.\s*$\s*^([\d]+-[\d]+-[\w]+\s*\([^)]*\))', header, re.MULTILINE)
```

This catches formats like:
```
Exp.
2608-2003-BE (S)
```

Note: Full re-extraction was not re-run (64K HTMLs × BeautifulSoup = ~50 min). The improvements are available for the next full extraction run.
