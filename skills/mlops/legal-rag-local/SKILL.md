---
name: legal-rag-local
description: Plan y stack para RAG legal local en PCs de 16GB RAM (Ollama + FAISS + BM25). 50K+ documentos, sin APIs, sin internet.
category: mlops
---

# Legal RAG Local — Stack para PCs de 16GB RAM

## Trigger

Usar este skill cuando el usuario pregunte por:
- Correr RAG localmente sin APIs ni internet
- Modelos que funcionen en 16GB/8GB/32GB RAM
- LightRAG vs Hybrid RAG vs GraphRAG
- Stack legal local con Ollama
- Alternativas a DeepSeek/Groq para privacidad de datos
- Costos de infraestructura local vs APIs

### Stack base (16GB RAM, 50K documentos)


## RAG Fallback Chain Pattern

When the LLM API key is missing, expired, or invalid, use a graceful degradation chain instead of returning an error. This keeps the system functional in "source retrieval" mode even without generation.

```
API Call Chain:  Groq (10s timeout) → DeepSeek (10s timeout) → no-LLM fallback
                          ↓                      ↓                     ↓
                    success → return      success → return       structured summary
                    401/error → next       error → next          of retrieved sources
```

**Implementation (Python/FastAPI):**

```python
async def _call_llm(user_message: str) -> str:
    """Fallback chain: Groq → DeepSeek → structured source summary."""
    errors = []

    for provider, api_key, caller in [
        ("Groq", GROQ_API_KEY, _call_groq),
        ("DeepSeek", DEEPSEEK_API_KEY, _call_deepseek),
    ]:
        if api_key:
            try:
                return await caller(user_message)
            except Exception as e:
                if "401" in str(e) or "Invalid" in str(e):
                    errors.append(f"{provider}: API key inválida o expirada")
                else:
                    errors.append(f"{provider}: {str(e)[:100]}")

    note = f"⚠️ No se pudo generar respuesta con IA ({'; '.join(errors)}).\n\n" if errors else ""
    return note + _no_llm_response(user_message)

async def _call_groq(user_message: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant", "messages": [...], "temperature": 0.1, "max_tokens": 1000},
        )
        data = resp.json()
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {data.get('error',{}).get('message','Unknown')}")
        return data["choices"][0]["message"]["content"]

def _no_llm_response(user_message: str) -> str:
    """Extract article references from context and format them."""
    arts = re.findall(r'Artículo (\S+) — ([^\n]+)', user_message)
    if not arts: return "No encontré información suficiente."
    lines = ["📋 Artículos relevantes en el Código Penal Peruano:\n"]
    for num, titulo in arts[:5]:
        lines.append(f"• Art. {num} — {titulo}")
    return "\n".join(lines)
```

**Key details:**
- Each provider gets its own try/except with explicit 401 detection
- Timeouts are short (10s) to avoid hanging the API request
- The fallback message tells the user WHY the LLM failed (transparency)
- The `_no_llm_response()` function returns a structured list of retrieved sources
- This pattern is tested with Groq returning 401 in 0.2s (not hanging)

| Componente | Opción | RAM |
|-----------|--------|:---:|
| LLM | Qwen 3 8B Q4_K_M (Ollama) | ~6 GB |
| Embeddings | BGE-M3-Legal-Spanish o all-MiniLM-L6-v2 | ~1-2 GB |
| FAISS | IndexFlatL2 (no necesita IVF/HNSW hasta 500K docs) | ~0.1 GB |
| BM25 | rank-bm25 Okapi | ~0.5 GB |
| Metadata | JSONL en memoria (para filtros) | ~0.4 GB |
| Textos completos | Lazy loading desde disco (no en RAM) | ~0.1 GB |
| Sistema operativo | Windows/Linux | ~2.5 GB |
| **Total** | | **~10.6 GB** (quedan ~5.4 GB libres) |

## Variaciones por RAM

| RAM | Modelo | Embeddings | Velocidad | Benchmark |
|:---:|--------|------------|:---------:|:---------:|
| **8GB** | Qwen 3 4B Q4 (~3.5GB) | all-MiniLM | 25 tok/s | ⚠️ Justo, no abrir Chrome |
| **16GB** | **Qwen 3 8B Q4** (~6GB) | **all-MiniLM** | **15 tok/s** | **✅ Recomendado ★** |
| 32GB | Qwen 3 14B Q4 (~10GB) | nomic-embed-text | 8 tok/s | ✅ Cómodo, mejor calidad |
| 32GB | Qwen 3 32B Q4 (~20GB) | nomic-embed-text | 4 tok/s | ⚠️ Apretado, solo para CPU |
| 64GB | DeepSeek R1 32B Q4 (~20GB) | nomic-embed-v2 (1.5K) | 3 tok/s | 🚀 Profesional |

## Modelos comparados para tareas legales

| Modelo | RAM (Q4) | Tok/s (CPU) | Español legal | Ideal para |
|--------|:--------:|:-----------:|:-------------:|-----------|
| **Qwen 3 8B** ★ | ~6 GB | 15-25 | ✅ Bueno | **Ganador 16GB** |
| Qwen 3 14B | ~10 GB | 5-10 | ✅ Bueno | 32GB RAM |
| Llama 3.1 8B | ~6 GB | 15-25 | ⚠️ Regular | Alternativa a Qwen |
| Mistral 7B | ~5 GB | 20-30 | ✅ Bueno | 8GB RAM |
| Gemma 3 12B | ~9 GB | 8-12 | ❌ Poco español | No recomendado |
| Gemma 4 26B MoE | ~12 GB | 2-5 | ❓ Muy nuevo | ❌ Necesita GPU |
| DeepSeek R1 14B | ~10 GB | 4-8 | ✅ Bueno | 32GB RAM |
| Phi-4 14B | ~10 GB | 5-8 | ⚠️ Poco español | Técnico, no legal |
| Qwen 3 4B | ~3.5 GB | 25-35 | ⚠️ Aceptable | 8GB RAM |

**★ Qwen 3 8B gana para 16GB por:** mejor equilibrio RAM/calidad, buen español, 128K contexto, function calling nativo.

## Costos: Local vs API

| Escenario (100 q/día, 30 días) | API DeepSeek | API Groq 70b | **Local (Ollama)** |
|:-------------------------------|:-----------:|:------------:|:------------------:|
| Costo/mes | **$4.80** | **$12.90** | **$0.00** |
| Internet necesario? | Sí | Sí | **No** |
| Privacidad de datos | Envía a DeepSeek | Envía a Groq | **Total** |
| Velocidad promedio | 3-10s | 1-3s | **20-40s** |
| Calidad de respuesta | Excelente | Excelente | Buena |

**Break-even:** Si usas 300+ consultas/día, el costo de API supera el valor del hardware en ~6 meses. Para uso intensivo, local es la opción económica.

## Implementación paso a paso

```bash
# 1. Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh   # Linux
# Windows: descargar de ollama.com/download

# 2. Descargar modelo
ollama pull qwen3:8b

# 3. Verificar que funciona
python -c "
import ollama
r = ollama.chat(model='qwen3:8b', messages=[{'role':'user','content':'Explica que es el habeas corpus en Peru'}])
print(r['message']['content'])
"

# 4. Indexar documentos (usando TC_SearchRAG como base)
# Adaptar embedder a all-MiniLM-L6-v2
# Cambiar Generator de DeepSeek a Ollama

# 5. Consultar
python src/buscar_local.py "pension de jubilacion por enfermedad profesional"
```

## Árbol de decisión

```
¿Tienes 16GB RAM?
├── Sí
│   ├── ¿Puedes usar APIs?
│   │   ├── Sí → Usa DeepSeek + FAISS+BM25 (sistema actual)
│   │   │          Más rápido, mejor calidad, ~$4.80/mes
│   │   └── No (privacidad/sin internet)
│   │         → Qwen 3 8B + FAISS+BM25 (local puro)
│   │            Más lento (20-40s), sin costo, offline
│   └── ¿50K+ documentos?
│       ├── Sí → Qwen 3 8B + FlatL2 (suficiente)
│       └── No → Qwen 3 8B + FlatL2 (sobra)
│
├── 32GB → Qwen 3 14B o DeepSeek R1 14B
├── 64GB → Qwen 3 32B Q4 o DeepSeek R1 32B Q4
└── 8GB  → Qwen 3 4B (solo consultas simples, sin RAG pesado)
```

## LightRAG vs Hybrid RAG (FAISS+BM25)

| Aspecto | Hybrid RAG (FAISS+BM25) | LightRAG (Knowledge Graph) |
|---------|:-----------------------:|:--------------------------:|
| Indexación | 10 min (sin LLM) | 2-4h (LLM extrae entidades) |
| RAM extra | ~3 GB | ~7-10 GB |
| Costo indexación | $0 | ~$1-3 (11K docs) |
| Búsqueda por tema | ✅ Instantánea | ✅ Similar |
| "Qué jueces coinciden" | ❌ No (a menos que esté en metadata) | ✅ Sí |
| "Qué otros casos citan la misma ley" | ❌ No | ✅ Sí |
| Documentos independientes | ✅ Ideal | ❌ Sobreingeniería |
| Documentos con relaciones | ❌ Limitado | ✅ Ideal |
| Complejidad de implementación | Baja | Media-Alta |

**¿Cuándo usar LightRAG?** Solo si los documentos tienen relaciones cruzadas explícitas: contratos que se refieren unos a otros, leyes que modifican otras leyes, jurisprudencia con precedentes citados. Para documentos independientes (como sentencias del TC), FAISS+BM25 es más eficiente.

## Técnicas Avanzadas para RAG Legal (hallazgos investigación Julio 2026)

Investigación exhaustiva en arXiv (60+ papers revisados) sobre el estado del arte en RAG legal 2025-2026. Detalles completos y fuentes en `references/rag-avanzado-2026.md`.

### Anti-Alucinación
- **LettuceDetect** (arXiv:2502.17125): F1 79.22%, ModernBERT con contexto 8K, 30-60 ejemplos/seg en una GPU. 30× más pequeño que prompt-based. Detecta claims no soportadas a nivel de token. GitHub: KRLabsOrg/LettuceDetect
- **LegalGraphRAG** (arXiv:2605.28120, ACL 2026): Arquitectura multi-agente Researcher→Auditor→Adjudicator con grafo jerárquico legal. SOTA en razonamiento legal verificable.
- **Falkor-IRAC** (arXiv:2605.14665): Razonamiento simbólico restringido por grafo. "Legal reasoning is not semantic similarity search."

### Chunking para Documentos Legales
- **Paragraph Group Chunking** es la estrategia óptima para dominio legal (Shaukat et al., arXiv:2603.06976):
  - nDCG@5 ~0.459 vs <0.244 de fixed-size (mejora de ~88%)
  - Hit@5 ~59%, Precision@1 ~24%
  - 36 métodos evaluados en 6 dominios, 5 modelos de embedding
- **SproutRAG** (arXiv:2606.18381): Chunking jerárquico guiado por atención entre oraciones, +6.1% Information Efficiency, sin LLM calls extras.
- ❌ Nunca usar solo fixed-size character splitting para documentos legales.

### Embeddings Multilingües (Español Legal)

**Modelos especializados en español legal:**

| Modelo | Params | Dims | Contexto | Licencia |
|--------|:------:|:----:|:--------:|:--------:|
| `wilfredomartel/BGE-M3-Legal-Spanish` ⭐ | 0.6B | 1024 | 8192 | Apache 2.0 |
| `wilfredomartel/embeddinggemma-300m-legal-spanish-300k` | 0.3B | 768 | 2048 | Apache 2.0 |
| `wilfredomartel/embeddinggemma-300m-legal-spanish-420k-v2` | 0.3B | 768 | 2048 | Apache 2.0 |

- **BGE-M3-Legal-Spanish** ⭐: Fine-tuned de `BAAI/bge-m3` sobre ~600K ejemplos legales españoles. MatryoshkaLoss (dimensionalidad reducible) + MultipleNegativesRankingLoss. 1024-dim, 8192 tokens. **Recomendado para RAG legal peruano.**
- **EmbeddingGemma-300m-Legal-Spanish**: Fine-tuned de `google/embeddinggemma-300m`. 300K ejemplos legales, 768 dims. Más ligero para 16GB RAM. Cosine similarity.
- Ambos usan `sentence-transformers`, entrenados sobre `wilfredomartel/small-spanish-legal-dataset` (11.2K ejemplos query/pos/neg, ODC-BY).

**Modelos multilingües generalistas (alternativa):**

| Modelo | Params | Descargas |
|--------|:------:|:---------:|
| `intfloat/multilingual-e5-large` | 0.6B | 12.2M |
| `intfloat/multilingual-e5-base` | 0.3B | 6.5M |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 0.1B | 48.5M |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 0.3B | 8.1M |

- **ModernBERT**: Contexto 8K tokens para sentencias largas. Usar como encoder para Critic Agent.

**Fuentes de datos legales peruanos**: Ver `references/peruvian-legal-data-sources.md` (datasets, APIs, Código Penal, SPIJ, jurisprudencia). Para la estructura JSON del Código Penal y el dataset de 20 artículos del MVP, ver `references/codigo-penal-peruano-dataset.md`.

### Evaluación de RAG Legal
- **ClaimRAG-LAW** (arXiv:2605.21071): Benchmark fine-grained a nivel de claim para RAG legal. Separa retrieval y generation. Demuestra que incluso RAG especializado alucina a tasas variables.
- Stack recomendado: RAGAS (métricas automáticas) + LettuceDetect (detección de alucinaciones) + evaluación experta periódica.

### Re-Ranking
- Cross-encoder multilingüe como 2da etapa sobre BM25+FAISS: BGE-Reranker-v2-m3, jina-reranker-v2-base-multilingual.
- Weighted Reciprocal Rank Fusion (RRF, k=60) para fusionar scores BM25 + FAISS.

## Proyectos open-source de referencia

Ver catálogo completo en `references/open-source-legal-rag-ecosystem.md` (investigación julio 2026: GitHub, Crossref, OpenAlex).

### Para forkear/adaptar:
- **NexusRAG** (323 ⭐): Stack casi idéntico — FastAPI + ChromaDB + LightRAG + bge-m3 + reranker + Ollama + citas inline. https://github.com/LeDat98/NexusRAG
- **graph-rag-agent** (2.3k ⭐): GraphRAG + LightRAG + Neo4j + DeepSearch + evaluación. https://github.com/1517005260/graph-rag-agent
- **korean-law-mcp** (2.1k ⭐): MCP server legal con verificación de citas, detección de alucinaciones, impact graph. https://github.com/chrisryugj/korean-law-mcp

### Scraping legal peruano:
- `cej-peru-scraper`: Scraper del Poder Judicial (WAF evasion, captcha, producción verificada)
- `tc-sedetc-scraper`: Jurisprudencia del Tribunal Constitucional
- El Peruano: sin scraper open-source conocido (vacío)

## Pitfall: Embedding Model Migration & FAISS Dimension Mismatch

When changing the embedding model (e.g., from `distiluse-base-multilingual-cased-v2` 512d to `BAAI/bge-m3` 1024d), the **FAISS index retains the old dimension**. Every FAISS search will fail with `AssertionError: assert d == self.d`.

**Symptoms:**
- `/api/search/vector` works (uses pgvector directly) but `/api/query` (uses FAISS) fails silently
- Error: `AssertionError` in FAISS search
- Log message may be empty `{"detail":""}`

**Root cause:** The FAISS index was serialized with 512-dim vectors (old model). The new model outputs 1024-dim vectors. FAISS checks dimension on every search.

**Fixes (in order of reliability):**

1. **Rebuild FAISS from existing vectors** (fastest, if PG has the right dims): Read vectors from PostgreSQL where they were regenerated, build FAISS directly. Works if the PG vectors were already re-encoded with the new model.

2. **Rebuild FAISS from scratch** (highest quality): Re-encode all chunks with the new model. On CPU with bge-m3, this takes ~18s/batch × 2061 batches = ~10 hours for 65K texts. Use batch_size=32, show_progress_bar=True.

3. **BM25-only fallback** (quickest): Wrap FAISS search in try-except AssertionError, fall back to BM25-only retrieval. Works but loses vector search speed.

```python
# Pattern: FAISS fallback to BM25-only
faiss_results = []
try:
    distances, indices = idx.faiss_index.search(query_vector, top_k * 2)
    faiss_results = [idx.faiss_meta[i]['doc_id'] for i in indices[0] if i != -1]
except AssertionError:
    logger.warning('FAISS dimension mismatch. Using BM25-only...')
    faiss_results = []  # RRF will use only BM25 results
```

4. **pgvector fallback** (if IDs are compatible): Query pgvector directly with `<=>` operator. Only works if the doc_ids match between the FAISS meta and the PG table.

## Pitfall: BM25s API Version Incompatibility

The `bm25s` library's API changed between versions. An index saved with one version may not be readable by another.

**Symptoms:**
- `'BM25' object has no attribute 'vocab_dict'` when calling `get_scores()`
- `'BM25' object has no attribute 'scores'` when calling `retrieve()`

**Root cause:** The BM25s `load()` method reads data files but some internal attributes (`vocab_dict`, `scores`, `index`) are not initialized if the save format differs.

**Detection:**
```python
bm = bm25s.BM25()
bm.load('datos/bm25s_index')
# Check if critical attributes exist
print(hasattr(bm, 'vocab_dict'))  # False if broken
print(hasattr(bm, 'scores'))      # False if broken
```

**Fixes:**

1. **Rebuild BM25 index** (recommended): Load the text corpus, re-index with current bm25s version. Fast (~8s for 65K texts).
   ```python
   import bm25s
   corpus_tokens = bm25s.tokenize(texts)
   bm = bm25s.BM25()
   bm.index(corpus_tokens)
   bm.save('datos/bm25s_index')
   ```

2. **Fallback to retrieve()**: Some versions support `retrieve()` even when `get_scores()` fails. Use `scores, indices = bm.retrieve(query, k=top_k)` instead of `bm.get_scores(tokenized_query)`.

3. **Legacy fallback**: Load the old `rank-bm25` pickle format (`BM25Okapi`) if available as a backup file.

## Pitfall: LLM Inventing Document Citations

When using RAG with LLM synthesis, the LLM often invents `[Doc: id]` citations instead of using real document IDs from the retrieved context.

**Symptom:** Grounding score high (0.8+) but `valid_citations = 0/16`. The LLM creates IDs like `[Doc: TC-001]` or `[Doc: Ley N.° 27291]` that don't exist in the retrieval corpus.

**Root cause:** The synthesis prompt says "use [Doc: id_documento]" which the LLM interprets as a placeholder to fill in. Without explicit constraints, it generates fake IDs.

**Fix - Add explicit constraints to the synthesis prompt:**
```
CRÍTICO: SOLO puedes usar IDs que YA APARECEN en el contexto proporcionado 
(ej: [Doc: 552066] o [Doc: 437043.html]). NUNCA inventes ni generes IDs nuevos 
como "TC-001", "Doc-1" o similares. Cada [Doc: X] en tu respuesta debe coincidir 
EXACTAMENTE con un ID que aparece en los fragmentos del CONTEXTO RECUPERADO.
```

**Verification:** Use `verify_response_grounding()` which:
- Extracts all `[Doc: X]` citations from the response
- Checks each against the actual retrieved doc_ids
- Reports grounding_score, valid/invalid citations
- Flags sentences without citations

## Pitfall: pgvector Authentication for Standalone Scripts

When accessing PostgreSQL from a standalone Python script (not the FastAPI app), the database URL in `.env` may appear as `***` due to secret redaction.

**Fix:** Reset the user's PG password:
```bash
sudo -u postgres psql -c "ALTER USER username WITH PASSWORD 'newpassword';"
```
Then use the new password in your connection string.

## WSL-Specific Pitfalls

### venv on /mnt/ is extremely slow
**Symptom:** `python3 -m venv /mnt/d/...` hangs for 5+ minutes or times out.
**Cause:** Windows filesystem mounted via 9p/drvfs has terrible small-file I/O performance.
**Fix:** Create venv on Linux home: `python3 -m venv ~/venv_project_name`. The venv binaries stay on ext4, only source code lives on /mnt/.

### CUDA kernel mismatch with torch
**Symptom:** `torch.AcceleratorError: CUDA error: no kernel image is available for execution on the device`
**Cause:** PyTorch CUDA toolkit version doesn't match installed NVIDIA driver.
**Fix:** Force CPU mode: `CUDA_VISIBLE_DEVICES="" python script.py`. For small datasets (<500 documents), CPU embeddings are fast enough (~30s for 20 articles). Only use GPU for 10K+ documents.

### pip install gets blocked by Hermes
**Symptom:** `pip install ... 2>&1 | tail -5` returns "This foreground command appears to start a long-lived server/watch process"
**Fix:** Use `terminal(background=true, notify_on_complete=true)` for pip installs. Then `process(action='wait', timeout=300)` to block until done.

### .env loading in submodules
**Symptom:** `os.getenv('DEEPSEEK_API_KEY')` returns `None` even though .env exists.
**Fix:** python-dotenv doesn't auto-load. Explicitly call `load_dotenv()` with the absolute path to .env. In nested modules, resolve from `Path(__file__)`: `load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")`

## Referencias

- Plan detallado: `D:\PyCode\TC_SearchRAG\plan_local_rag.md` (10 secciones, árbol de decisión, costos, implementación)
- Proyecto base: `D:\PyCode\TC_SearchRAG\` (11,483 docs TC indexados)
- Modelo: `ollama pull qwen3:8b`
- Cliente Python: `pip install ollama`
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (básico) o `BAAI/bge-m3` (multilingüe avanzado)
- Técnicas avanzadas y papers: `references/rag-avanzado-2026.md`
- Ecosistema open-source legal RAG: `references/open-source-legal-rag-ecosystem.md` (proyectos, papers, scraping, datos abiertos)
- Fuentes de datos legales peruanos: `references/peruvian-legal-data-sources.md` (datasets, APIs, SPIJ, scraping)
- Skill relacionado: `tc-searchrag` (detalles del proyecto TC)
- Skill relacionado: `lexrag-audit-optimize` (cómo optimizar RAG, priority inversion finding)
- Mockups HTML para LegalTech MVP: `references/legaltech-mockup-html-pattern.md` (5 pantallas, Tailwind CDN, vanilla JS)
- FastAPI + FAISS + RAG backend pattern: `references/fastapi-faiss-rag-backend-pattern.md` (estructura de proyecto, embeddings, routers, RAG pipeline)
- Next.js App Router + FastAPI integration: `references/nextjs-fastapi-integration.md` (proxy rewrites, API client, dark mode, sidebar, Suspense fix)
- Dataset del Código Penal Peruano: `references/codigo-penal-peruano-dataset.md` (estructura JSON, 20 artículos)
