# Post-Audit Implementation Patterns

Patterns and recipes for implementing the fixes diagnosed by the RAG Citation Audit workflow.
Use AFTER the audit identifies gaps in context headers, metadata extraction, or prompt instructions.

## 1. Build doc entities lookup from graph

If the system has a NetworkX graph with Document nodes connected to Juez/Actor/Demandado/Ley:

```python
"""scripts/build_doc_entities_lookup.py — one-time precompute (~2s for 60K docs)"""
import pickle, json

GRAPH_PATH = "data/indices/graph_juris_pro.pkl"
OUTPUT_PATH = "data/indices/doc_entities.json"

with open(GRAPH_PATH, 'rb') as f:
    G = pickle.load(f)

doc_entities = {}
for node, data in G.nodes(data=True):
    if data.get('tipo') != 'Documento':
        continue
    entry = {"jueces": [], "actores": [], "demandados": [], "leyes": []}
    for adj in G.neighbors(node):
        tipo = G.nodes[adj].get('tipo', '')
        if tipo == 'Juez':
            entry["jueces"].append(adj.replace("Juez: ", "").strip())
        elif tipo == 'Actor':
            entry["actores"].append(adj.replace("Actor: ", "").strip())
        elif tipo == 'Demandado':
            entry["demandados"].append(adj.replace("Demandado: ", "").strip())
        elif tipo == 'Ley':
            entry["leyes"].append(adj.replace("Ley: ", "").strip())
    doc_entities[node] = entry

json.dump(doc_entities, open(OUTPUT_PATH, 'w', ensure_ascii=False), indent=1)
```

**Stats from a 191K-node legal graph**: 59,571 docs with entities; 44,824 with jueces; 44,638 with actores; 43,698 with demandados.

## 2. Inject entities into context header

Modify `_doc_header()` to load the JSON once (lazy cache), then enrich every chunk:

```python
_docs_entities = {}
def _load_docs_entities():
    global _docs_entities
    if not _docs_entities and os.path.exists(ENTITIES_PATH):
        _docs_entities = json.load(open(ENTITIES_PATH, 'r', encoding='utf-8'))

def _doc_header(doc_id):
    _load_docs_metadata()
    _load_docs_entities()
    meta = _docs_metadata.get(doc_id, {})
    ent = _docs_entities.get(doc_id, {})

    ident = meta.get("identificador", "") or doc_id
    organo = meta.get("organo", "")
    header_str = f"**{ident}**" + (f" | {organo}" if organo else "")

    ent_lines = []
    if ent.get("jueces"):
        ent_lines.append(f"Juez: {', '.join(ent['jueces'][:3])}")
    actor_str = ", ".join(ent.get("actores", []))
    dem_str = ", ".join(ent.get("demandados", []))
    if actor_str or dem_str:
        partes = []
        if actor_str: partes.append(actor_str)
        if dem_str: partes.append(f"vs {dem_str}")
        ent_lines.append(" | ".join(partes))
    partes_str = " | ".join(ent_lines)

    return header_str, meta.get("fecha",""), meta.get("materia",""), partes_str
```

Then in the context text builder:

```python
header, fecha, materia, partes = _doc_header(m['doc_id'])
extra = ""
if fecha:  extra += f" | Fecha: {fecha}"
if materia: extra += f" | Materia: {materia}"
header_block = f"{header}{extra}"
if partes: header_block += f"\n{partes}"
header_block += f"\nJurisprudencia/{m['doc_id']}"
texts.append(f"{header_block}\n{m['text']}")
```

**Result** — each chunk header now looks like:
```
**CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema - Sala Laboral
Juez: Yrivarren Fallaque, Arévalo Vela | Edgardo Hernán Asenjo Tamay vs Poder Judicial
Jurisprudencia/1612215.html
{chunk text}
```

## 3. Testing response format quality

Create a test suite that verifies headers, entities, and context format:

```python
def test_doc_header_has_organo():
    header, _, _, _ = _doc_header("1612215.html")
    assert "|" in header

def test_doc_header_has_entities():
    _, _, _, partes = _doc_header("1309310.html")
    assert "Juez:" in partes or "vs" in partes

def test_metadata_extraction():
    with open("data/metadata_docs.json") as f:
        meta = json.load(f)
    assert len(meta) > 60000

def test_entities_lookup():
    with open("data/indices/doc_entities.json") as f:
        entities = json.load(f)
    assert len(entities) > 50000

def test_get_hybrid_context_format():
    top_docs, ctx, _ = get_hybrid_context("despido arbitrario", top_k=2)
    assert "**" in ctx
    assert "Jurisprudencia/" in ctx
```

## 4. Clean up noisy ML logs

Library logs (httpx, sentence_transformers, huggingface_hub) produce lines like:
```
HTTP Request: POST https://api.deepseek.com/chat/completions "HTTP/1.1 200 OK"
```

Suppress in app config:

```python
import logging
NOISY_LOGGERS = [
    "httpx", "httpcore", "urllib3", "openai",
    "sentence_transformers", "requests", "filelock",
    "huggingface_hub", "asyncio"
]
for lib in NOISY_LOGGERS:
    logging.getLogger(lib).setLevel(logging.WARNING)
```

Also move non-critical save logs to DEBUG:
```python
# Before
logger.info(f"Consulta guardada en {path}")
logger.info(f"Auditoría guardada en {path}")
# After
logger.debug(f"Consulta guardada en {path}")
logger.debug(f"Auditoría guardada en {path}")
```

## 5. Acronyms for LLM providers in logs

| Provider | Acronym |
|----------|---------|
| DeepSeek | DPK |
| Groq | GRQ |
| OpenAI | OAI |
| Anthropic | ANT |

Replace in synthesizer.py and any output:
```python
logger.info("Intentando DPK...")
# instead of "Intentando DeepSeek V4 Flash..."
yield {"data": {"type": "info", "content": "⚠️ DPK no disponible, usando GRQ..."}}
```

## 6. Silent failure for non-critical API calls

When an API call is for non-critical features (follow-up questions, critic rewrite, feedback loop), catch errors silently to avoid noisy terminal output:

```python
try:
    result = api_call()
    # process result
except Exception:
    pass  # Fallo silencioso — funcionalidad no crítica
```

This applies to:
- Follow-up question generation (GROQ llama-3.1-8b)
- Critic rewrite/feedback loop (GROQ llama-3.1-8b)
- Any optional enrichment API
