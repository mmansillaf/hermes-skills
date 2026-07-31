---
name: legal-platform-mvp
description: Build a LegalTech platform MVP end-to-end — market research, HTML mockups, structured legal dataset, FastAPI + FAISS + sentence-transformers RAG backend. Covers the full pipeline from idea to functional API. For Peruvian/Spanish-language legal content but patterns are jurisdiction-agnostic.
category: data-science
---

# LegalTech Platform MVP — End-to-End Build

Trigger when the user wants to build a legal research platform, a digital code/law browser, or any LegalTech MVP with RAG. Covers research → mockups → backend.

## Phase 0: Market Research (parallel subagents)

Spawn 3 subagents simultaneously for max speed:
1. **YouTube** — search videos + read comments. What do users ask for, what frustrates them, what do they want to pay for?
2. **Forums/Social** — Reddit, LinkedIn, academic portals. What tools exist, what gaps are mentioned?
3. **Competitors** — direct/indirect competitors, pricing, features, gaps.

Aggregate into a single research report. Key question to answer: *does this idea have a validated gap in the market?*

## Phase 1: HTML Mockups (5 screens)

Build self-contained HTML files with Tailwind CDN + vanilla JS. No frameworks, no build tools. Each mockup opens directly in browser.

**Design system for legal platforms:**
- Primary: azul marino/indigo (#1a237e, #1e3a5f)
- Accent: dorado (#c9a84c)
- Typography: serif (Georgia) for legal text, sans-serif for UI
- Dark/light mode with `class="dark"` on `<html>` + Tailwind `dark:` variants
- Sticky top navbar with anchor links between mockup screens

**5 screens to build:**
1. `landing.html` — Hero, features grid, pricing (3 tiers with one "Most Popular"), testimonials, FAQ accordion, CTA
2. `dashboard.html` — 3-column: sidebar index (Libros→Capítulos→Artículos) + center article viewer + right jurisprudence panel. Include 5-10 real articles with full text, modification history timeline, search bar with suggestions.
3. `chat.html` — Chat interface with mock responses, source citation badges (clickable), mode toggle (lawyer/citizen), typing indicator animation, legal disclaimer modal, quick-ask buttons.
4. `timemachine.html` — Date slider 1991→present, version history with real modification dates, side-by-side diff view (old vs current), quick-jump buttons for key modification dates.
5. `calculadora.html` — Interactive form: crime selector → aggravants checkboxes → mitigants → additional rules (recidivism, attempt). Real-time calculation with tercios visualization bars, result panel with formula breakdown.

**Mock data:** Use real article numbers and text from the target legal code. Each article needs: id, numero, titulo, texto (with penalty range highlighted), vigencia dates, modificaciones array, jurisprudencia_vinculada.

## Phase 2: Structured Dataset

Create a JSON file with 20 real articles. Schema:
```json
{
  "id": "art_106",
  "numero": 106,
  "titulo": "Homicidio Simple",
  "libro": "II",
  "titulo_libro": "Parte Especial — Delitos",
  "capitulo": "I",
  "titulo_capitulo": "Homicidio",
  "texto": "full article text...",
  "incisos": [{"numero": 1, "texto": "..."}],
  "vigencia": {"inicio": "1991-04-08", "fin": null},
  "modificaciones": [{"fecha": "...", "ley": "...", "descripcion": "...", "tipo": "modificacion"}],
  "status": "vigente",
  "jurisprudencia_vinculada": ["Acuerdo Plenario X-20XX/CJ-116"],
  "doctrina_relacionada": []
}
```

For Peruvian law: SPIJ (spijweb.minjus.gob.pe) is the authoritative source. LP Derecho and Juris.pe have the text but with Cloudflare protection. No public JSON dataset exists — must transcribe manually.

## Phase 3: Backend (FastAPI + FAISS + RAG)

### Stack

| Component | Choice | Why |
|-----------|--------|-----|
| API | FastAPI + Uvicorn | Async, auto-docs, Pydantic validation |
| Embeddings | `intfloat/multilingual-e5-large` (1024 dims) | Best multilingual, good Spanish. Alternative: `wilfredomartel/BGE-M3-Legal-Spanish` (legal-specific, 8192 ctx) |
| Vector Index | FAISS (CPU, IndexFlatIP) | 20-500 articles: CPU is enough. No GPU needed. |
| LLM | Groq (free tier, llama-3.1-8b) or DeepSeek API | Groq is free with generous rate limits |
| DB | SQLite or JSON files | No PostgreSQL needed for MVP < 500 articles |

### Project Structure
```
mvp/backend/
├── app/
│   ├── main.py              # FastAPI app + CORS + health
│   ├── database.py          # Load/serve JSON dataset
│   ├── routers/
│   │   ├── articulos.py     # GET /api/articulos, GET /api/articulos/{id}
│   │   ├── busqueda.py      # GET /api/buscar?q= (FAISS semantic)
│   │   └── consulta.py      # POST /api/consultar (RAG)
│   └── services/
│       ├── embeddings.py    # Model loading, FAISS build/search, disk persistence
│       └── rag.py           # RAG pipeline: search → context → LLM
├── setup.py                 # Build embeddings + quick test
├── test_backend.py          # Test suite
├── start.sh                 # One-command startup
├── .env                     # LLM_PROVIDER + API keys (NOT committed)
└── requirements.txt
```

### Embeddings Service (`embeddings.py`)

Key design decisions:
- **Persist FAISS index to disk** (`data/faiss_index.bin` + `data/faiss_metadata.json`)
- **Auto-load on first use**: if index files exist, load from disk instead of rebuilding
- **`force_rebuild=True`** flag for manual rebuilds
- **Normalize embeddings** (`normalize_embeddings=True`) for cosine similarity via inner product
- **Search text format**: `"Artículo {numero}: {titulo}. {texto}. Inciso {n}: {inciso_texto}."` — concatenate all searchable fields

### RAG Pipeline (`rag.py`)

1. **Search**: Get top_k chunks from FAISS
2. **Context building**: For each result, fetch full article from dataset, format as structured context block
3. **LLM call**: System prompt MUST enforce:
   - Only use provided fragments
   - Cite format: `[Art. X, Código Penal, vigente desde DD/MM/AAAA]`
   - If insufficient info: explicit "No encontré información suficiente..."
   - Zero hallucination policy
4. **Fallback**: If no API key configured, return a list of found articles with a note

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Root health check |
| GET | `/api/health` | Detailed health (embeddings loaded, article count) |
| GET | `/api/articulos?libro=II&limit=50` | List articles with filters |
| GET | `/api/articulos/{id}` | Full article with modifications, incisos, jurisprudence |
| GET | `/api/buscar?q=homicidio&top_k=5` | Semantic search via FAISS |
| POST | `/api/consultar` | RAG query: `{"pregunta": "...", "top_k": 5}` |

### System Prompt for RAG

```
Eres un asistente legal especializado en el [CÓDIGO] ([NORMA]).

REGLAS INQUEBRANTABLES:
1. Responde ÚNICA Y EXCLUSIVAMENTE con la información contenida en los fragmentos proporcionados.
2. CITA SIEMPRE el artículo exacto en este formato: [Art. X, Código, vigente desde DD/MM/AAAA].
3. Si la información en los fragmentos no es suficiente: "No encontré información suficiente en el [CÓDIGO] para responder esta consulta."
4. NUNCA inventes artículos, penas, fechas o jurisprudencia.
5. Para cada respuesta, indica la pena aplicable cuando corresponda.
```

## Pitfalls & Fixes

### CUDA kernel mismatch
**Symptom:** `torch.AcceleratorError: CUDA error: no kernel image is available for execution on the device`
**Fix:** Force CPU mode: `CUDA_VISIBLE_DEVICES="" python script.py`. For small datasets (<500 articles), CPU embeddings are fast enough (~30s for 20 articles).

### WSL venv on /mnt/ is too slow
**Symptom:** `python3 -m venv /mnt/d/...` hangs or takes 5+ minutes.
**Fix:** Create venv on Linux home: `python3 -m venv ~/venv_cp_peru`. The Windows filesystem is mounted over 9p/drvfs — avoid heavy I/O there.

### pip install gets blocked by Hermes
**Symptom:** `pip install ... 2>&1 | tail -5` returns "This foreground command appears to start a long-lived server/watch process"
**Fix:** Use `background=true` + `notify_on_complete=true` for pip installs. Then `process(action='wait', timeout=300)` to block until done.

### Path resolution from nested modules
**Symptom:** `Path(__file__).resolve().parent.parent` resolves to wrong directory.
**Fix:** Count parent levels carefully. From `app/services/embeddings.py` to `mvp/data/` = 4 parents (services → app → backend → mvp). Document the expected path in comments. Always test path resolution in a separate script first.

### API key expired
**Symptom:** `401 Authentication Fails, Your api key: ****XXXX is invalid`
**Fix:** API keys expire. Groq free tier (console.groq.com) is a reliable alternative. Store key in `.env`, load with `python-dotenv`, never hardcode.

### DeepSeek API response format
**Symptom:** `'choices'` KeyError on DeepSeek response.
**Fix:** The response shape is `{"choices": [{"message": {"content": "..."}}]}`, same as OpenAI format. If `KeyError`, print `r.status_code` and `r.text` to debug — likely auth failure, not format issue.

## Verification Checklist

After building the backend, run these 5 tests:

```python
# 1. Health
GET /api/health  → {"status": "healthy", "embeddings_loaded": true}

# 2. Article fetch
GET /api/articulos/art_106  → {"numero": 106, "titulo": "Homicidio Simple"}

# 3. Semantic search (test that related concepts cluster)
GET /api/buscar?q=feminicidio  → Feminicidio should be #1, not Homicidio Simple

# 4. Semantic search (test that exact terms match)
GET /api/buscar?q=robo+agravado  → Robo Agravado + Robo in top 3

# 5. RAG query (with valid API key)
POST /api/consultar {"pregunta": "pena por homicidio"} → response cites Art. 106 with score > 0.8
```

## References

- `references/legal-mockup-patterns.md` — Design conventions and data schemas for legal platform mockups
- `references/peru-legaltech-ecosystem.md` — Competitor analysis: DOXS.AI, Juztina, LEXIUS, vLex, SPIJ
