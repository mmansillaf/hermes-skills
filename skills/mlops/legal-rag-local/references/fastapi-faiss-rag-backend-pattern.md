# FastAPI + FAISS + RAG MVP Backend Pattern

## Project Structure

```
mvp/
├── data/
│   ├── codigo_penal.json          ← Structured legal dataset (JSON array)
│   ├── faiss_index.bin            ← Built FAISS index
│   └── faiss_metadata.json        ← Index metadata (article_id, titulo, etc.)
│
└── backend/
    ├── app/
    │   ├── main.py                ← FastAPI app, CORS, routers
    │   ├── database.py            ← Load/query legal dataset
    │   ├── routers/
    │   │   ├── articulos.py       ← GET /api/articulos, GET /api/articulos/{id}
    │   │   ├── busqueda.py        ← GET /api/buscar?q= (FAISS semantic search)
    │   │   └── consulta.py        ← POST /api/consultar (RAG generation)
    │   └── services/
    │       ├── embeddings.py      ← sentence-transformers + FAISS build/search
    │       └── rag.py             ← RAG pipeline: search → context → LLM
    ├── .env                       ← GROQ_API_KEY, LLM_PROVIDER
    ├── requirements.txt
    ├── setup.py                   ← Build embeddings + quick test
    └── build_embeddings.py        ← One-shot index builder
```

## Dataset Format (codigo_penal.json)

```json
[
  {
    "id": "art_106",
    "numero": 106,
    "titulo": "Homicidio Simple",
    "libro": "II",
    "titulo_libro": "Parte Especial — Delitos",
    "capitulo": "I",
    "titulo_capitulo": "Homicidio",
    "texto": "El que mata a otro será reprimido con pena privativa de libertad no menor de seis ni mayor de veinte años.",
    "incisos": [],
    "vigencia": {"inicio": "1991-04-08", "fin": null},
    "modificaciones": [
      {"fecha": "1991-04-08", "ley": "Decreto Legislativo 635", "descripcion": "Promulgación original.", "tipo": "original"}
    ],
    "status": "vigente",
    "jurisprudencia_vinculada": ["Acuerdo Plenario 1-2011/CJ-116"],
    "doctrina_relacionada": []
  }
]
```

## Embeddings Service (services/embeddings.py)

Key pattern: **build_or_load_index** with persistent cache.

```python
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

_model = None
_index = None
_metadata = []
_embeddings_ready = False

def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/multilingual-e5-large")
    return _model

def build_or_load_index(articles=None, force_rebuild=False):
    global _index, _metadata, _embeddings_ready

    # Try loading from disk first
    if INDEX_PATH.exists() and not force_rebuild:
        _index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "r") as f:
            _metadata = json.load(f)
        _embeddings_ready = True
        return _index, _metadata

    # Build from scratch
    model = load_model()
    dim = model.get_sentence_embedding_dimension()

    texts = []
    metadata = []
    for art in articles:
        search_text = f"Artículo {art['numero']}: {art['titulo']}. {art['texto']}"
        if art.get("incisos"):
            for inc in art["incisos"]:
                search_text += f" Inciso {inc['numero']}: {inc['texto']}"
        texts.append(search_text)
        metadata.append({"article_id": art["id"], "numero": art["numero"], "titulo": art["titulo"], ...})

    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    _index = faiss.IndexFlatIP(dim)  # Inner Product for cosine similarity
    _index.add(np.array(embeddings).astype(np.float32))

    faiss.write_index(_index, str(INDEX_PATH))
    with open(META_PATH, "w") as f:
        json.dump(metadata, f)

    _metadata = metadata
    _embeddings_ready = True
    return _index, _metadata

def search(query: str, top_k: int = 5):
    if not _embeddings_ready:
        build_or_load_index()
    model = load_model()
    query_vec = model.encode([query], normalize_embeddings=True)
    scores, indices = _index.search(np.array(query_vec).astype(np.float32), top_k)
    return [{"score": float(scores[0][i]), "metadata": _metadata[idx]} for i, idx in enumerate(indices[0]) if idx >= 0]
```

## RAG Service (services/rag.py)

Pattern: Semantic search → Build context → LLM generation → Fallback chain.

```python
async def consultar(pregunta: str, top_k: int = 5) -> dict:
    # Step 1: Semantic search
    search_results = semantic_search(pregunta, top_k=top_k)

    # Step 2: Build context from retrieved articles
    context_parts = []
    fuentes = []
    for sr in search_results:
        article = get_article(sr["metadata"]["article_id"])
        ctx = f"Artículo {article['numero']} — {article['titulo']}\n"
        ctx += f"Vigente desde: {article['vigencia']['inicio']}\n"
        ctx += f"Texto: {article['texto']}\n"
        context_parts.append(ctx)
        fuentes.append({"articulo": f"Art. {article['numero']}", ...})

    context = "\n---\n".join(context_parts)

    # Step 3: Call LLM with context
    user_message = f"FRAGMENTOS DEL CÓDIGO PENAL:\n{context}\n\nPREGUNTA: {pregunta}"
    respuesta = await _call_llm(user_message)

    return {"respuesta": respuesta.strip(), "fuentes": fuentes, "confidence": ...}
```

## FastAPI Router Pattern

### Article list (routers/articulos.py)

```python
@router.get("/articulos")
def list_articulos(libro: str = Query(None), limit: int = Query(50, le=100)):
    arts = search_by_filters(libro=libro, limit=limit)
    return {"total": len(arts), "articulos": [{id, numero, titulo, ...} for a in arts]}

@router.get("/articulos/{article_id}")
def get_articulo(article_id: str):
    art = get_article(article_id)
    if not art: raise HTTPException(status_code=404)
    return art
```

### Semantic search (routers/busqueda.py)

```python
@router.get("/buscar")
def buscar_articulos(q: str = Query(...), top_k: int = Query(5, le=10)):
    if not embeddings_ready():
        build_or_load_index()  # Lazy load
    results = search(q, top_k=top_k)
    return {"query": q, "results": [{score, article_id, numero, titulo} for r in results]}
```

### RAG query (routers/consulta.py)

```python
class ConsultaRequest(BaseModel):
    pregunta: str = Field(..., min_length=5, max_length=1000)
    top_k: int = Field(5, ge=1, le=10)

@router.post("/consultar")
async def consultar_endpoint(req: ConsultaRequest):
    return await consultar(req.pregunta, top_k=req.top_k)
```

## Data Path Resolution

**Critical:** Use `Path(__file__).resolve()` to compute relative paths. Count parent levels carefully.

```python
# From app/database.py (3 levels up to mvp/):
DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "codigo_penal.json"

# From app/services/embeddings.py (4 levels up to mvp/):
DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data"
```

## .env Loading in Submodules

python-dotenv does NOT auto-load. Load explicitly:

```python
from pathlib import Path
from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_ENV_PATH)
```

## Groq API Configuration

| Setting | Value |
|---------|-------|
| Model | `llama-3.1-8b-instant` |
| Endpoint | `https://api.groq.com/openai/v1/chat/completions` |
| Timeout | 10s (short — Groq responds in <3s normally) |
| Temperature | 0.1 (legal responses must be deterministic) |
| Max tokens | 1000 |
| Error pattern | 401 → "Invalid API Key" in 0.2s |

## Dependencies

```
fastapi>=0.110
uvicorn[standard]>=0.27
sentence-transformers>=2.7
faiss-cpu>=1.8
numpy>=1.26
pydantic>=2.0
python-dotenv>=1.0
httpx>=0.27
```
