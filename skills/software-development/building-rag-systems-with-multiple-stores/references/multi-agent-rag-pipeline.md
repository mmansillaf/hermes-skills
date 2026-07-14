# Multi-Agent RAG Pipeline Architecture

## When to use this pattern

You need a RAG system that goes beyond simple Q&A and handles MULTIPLE query intents: summarization, cross-document comparison, contradiction detection, risk analysis, and factual Q&A — all with **validated source citations**.

This pattern is distinct from flat RAG pipelines because queries are ROUTED through specialized agents rather than a single retrieve-then-generate flow.

## Architecture Overview

```
User Query
    |
    v
[Orchestrator Agent] ── clasifica intencion
    |
    ├── qa             → Retrieval → Generation
    ├── resumen        → Retrieval → Generation (summarize prompt)
    ├── comparar       → Retrieval → Analysis (compare agent) → Generation
    ├── contradicciones → Retrieval → Analysis (contradictions agent) → Generation
    ├── analizar       → Retrieval → Generation (risk/error analysis prompt)
    └── listar         → Direct DB query (no LLM needed)
                            |
                            v
                     [Validation Agent] ── verifica citas
                            |
                            v
                     Response with citations
```

## Agent Definitions

### 1. Intent Classifier Agent
Determines WHAT the user wants to do. Uses LLM classification with keyword fallback:

```python
def classify_intent(query: str, llm) -> Intent:
    # Try LLM first (temperature=0.0 for deterministic output)
    result = llm.generate(system_prompt=INTENT_CLASSIFIER_PROMPT, user_prompt=query)
    # Fallback to keyword matching if LLM fails
    if "compara" in query: return Intent.COMPARE
    if "contradic" in query: return Intent.CONTRADICTIONS
    ...
```

**Classifier prompt** (single-word output, zero-shot):
```
Eres un clasificador de intenciones para un sistema legal RAG.
Clasifica la siguiente consulta en UNA de estas categorias:
- qa: Pregunta factual
- resumen: Pide resumir documentos
- comparar: Pide comparar documentos
- contradicciones: Pide encontrar contradicciones
- analizar: Pide analizar (errores, riesgos, cumplimiento)
- listar: Pide listar documentos

Responde SOLO con el nombre de la categoria.
```

### 2. Retrieval Agent
Hybrid search (vector + keyword) + cross-encoder reranker:

```
Query ──→ Embedding Model ──→ ChromaDB vector search
  └──→ SQLite FTS5 keyword search
              │
              v
         Blend scoring (vector * 0.7 + keyword * 0.3)
              │
              v
         Cross-encoder reranker (re-ordena top-20)
              │
              v
         Top-K chunks with scores
```

**Key implementation details:**
- Vector store: ChromaDB (embedded, no server) with cosine similarity
- Keyword store: SQLite FTS5 with Spanish unicode61 tokenizer
- Reranker: `cross-encoder/ms-marco-MiniLM-L6-v2` (~150MB)
- Embedding model: `intfloat/multilingual-e5-small` (384d, 120MB, good Spanish)
- Hybrid scoring: weighted blend to catch both semantic and literal matches
- Reranker runs on top 20 candidates, returns top 5

**Chunk metadata structure:**
```python
{
    "doc_id": "uuid",
    "doc_name": "contrato.pdf",
    "section": "CLAUSULA TERCERA",
    "sub_section": "",
    "page": 3,
    "line_start": 45,
    "line_end": 52,
    "path": ["doc_uuid", "CLAUSULA TERCERA"],
    "tipo": "texto"  # or "tabla" or "titulo"
}
```

This hierarchical metadata is critical — it enables the LLM to cite EXACT locations.

### 3. Analysis Agents (compare + contradictions)

**Compare Agent**: Takes two+ documents and produces structured comparison:
```
**Comparacion: [TEMA]**
- Documento A: ... [cita]
- Documento B: ... [cita]
- Diferencia: ...
```

Prompt instructs the LLM to list each comparison point with per-document citations.

**Contradictions Agent**: Takes multiple documents and searches for:
1. Clauses that say opposite things on the same topic
2. Inconsistent definitions of the same term
3. Conflicting obligations across documents
4. Mismatched dates, amounts, or conditions

**Pitfall**: The compare/contradictions agents naturally use bullet-format citations (`* Documento A: name, Seccion: name`) instead of bracket format (`[Documento: "name", Seccion: "name"]`). The citation validator must accept BOTH formats.

### Document Name Extraction for Comparison Queries

**Problem**: When a user types "compara el contrato A con el contrato B", the retrieval agent searches by embedding similarity of the full query. It finds semantically similar chunks from UNRELATED documents instead of the specific documents named. The LLM then responds "Lo siento, no tengo acceso a esos documentos" while showing irrelevant sources.

**Solution — Pre-retrieval name extraction**: Before calling the retrieval agent, extract document names from the query and pass them as doc_filter.

#### Implementation Steps

1. **Stop-word stripping**: Remove query noise (compara, entre, con, vs, y, de, el, la). Split by connectors (y, e, vs, versus, con, comma).
2. **Fuzzy name matching**: For each candidate fragment, search the document store via LIKE patterns: exact match, with-known extensions (.txt/.pdf/.docx), and per-word matches (words > 3 chars). Prioritize exact matches over partial.
3. **Filtered retrieval**: Pass found names as doc_filter=[name1, name2]. When active, triple top_k and filter results by doc_name. If no candidates survive, retry with doc names as search query.
4. **Integration point**: Between intent classification and retrieval — only for COMPARE and CONTRADICTIONS intents.
5. **Fallback**: If no documents match the query, return None and normal retrieval runs unchanged.

#### Pitfalls
- Short words like "contrato" match many documents — prefer full filenames or quoted terms
- Only triggers for COMPARE/CONTRADICTIONS intents (not QA or SUMMARIZE)
- Documents must already be ingested in the store

### 3. Compare Agent

Takes retrieved chunks + analysis results and produces the final answer. Uses task-specific prompts:

- **qa**: Answer using ONLY context. Cite every claim.
- **resumen**: Structured: type/parties → purpose → key points (5-7) → dates/milestones → risks
- **analizar**: Like resumen but focused on risks, errors, compliance issues

**Citation format**: `[Documento: "nombre.pdf", Seccion: "CLAUSULA TERCERA", Lineas: 45-52]`

**Critical prompt rule**: "Si la respuesta no esta en el contexto, di 'No encontre esta informacion en los documentos disponibles.'"

### 5. Validation Agent

Checks every citation in the generated response against the actual chunks used.

**Pattern matching** — must handle multiple citation formats:
```python
# Pattern 1: [Documento: "name", Seccion: "name", Lineas: X-Y]  (bracket, quoted)
# Pattern 2: [Documento: name, Seccion: name, Lineas: X-Y]     (bracket, unquoted)
# Pattern 3: * Documento A: name, Seccion: name,               (bullet from compare agent)
# Pattern 4: [name.txt, Seccion, Lineas X]                     (compact)
```

**Validation logic** (tolerant):
1. Extract all citation-like patterns from the response
2. Build lookup set from actual chunks: `(doc_name, section)`
3. For each extracted citation, check if `(doc_name, section)` exists in lookup
4. If no exact match, try fuzzy: doc_name contains known or vice versa; section contains known or vice versa
5. If no citations found at all, check if any document NAMES appear in the response text
6. Report only first 3 errors to avoid noise

**Pitfall**: The validation will often flag citations as invalid not because the LLM hallucinated, but because the citation FORMAT doesn't match the regex. Always support multiple formats.

## LLM Provider Abstraction

The multi-agent pipeline should be **provider-agnostic**. Implement a unified interface:

```python
class LLMClient:
    def generate(self, system_prompt, user_prompt, temperature=0.3, max_tokens=2048, prefer_cloud=False) -> str
```

Supported backends:
- **Groq** (cloud, fast, free tier available): `LLM_PROVIDER=groq`
- **OpenAI** (ChatGPT): `LLM_PROVIDER=openai` + `OPENAI_API_KEY`
- **Gemini** (Google): `LLM_PROVIDER=gemini` + `GEMINI_API_KEY`
- **Ollama** (local): `LLM_PROVIDER=ollama` + `OLLAMA_MODEL=llama3.2:3b`

Fallback chain: if primary fails → try Groq (if available) → return error message.

## Document Management Layer

The multi-agent pipeline needs CRUD document management:

| Operation | Implementation |
|-----------|---------------|
| Add document | Parse → chunk → embed → store in ChromaDB + SQLite FTS5 |
| Delete document | Remove chunks from ChromaDB by ID + delete from SQLite |
| List documents | SQLite query with optional categoria filter |
| Update metadata | SQLite UPDATE (categoria, etc.) |
| Category management | `categoria` column in documents table |

**Categorization**: Documents can be organized by type (Contratos, Resoluciones, Sentencias, Informes) via a `categoria` field. The UI should support filtering by category.

## Testing Strategy

Always test with KNOWN contradictions between test documents. Create pairs of documents where:
- Same parties, different terms (plazo, monto, tasa)
- Same topic, opposite clauses
- Structured to produce unambiguous comparison

**Example**: Two versions of a service contract where v2 changes:
- Duration: 12 months → 6 months
- Fee: S/12,000 → S/8,500
- Late penalty: 2% → 1% monthly
- Confidentiality: 2 years → 3 years
- Intellectual property: exclusive → joint ownership
- Dispute resolution: courts → arbitration

The system should correctly identify ALL of these differences.

## When NOT to use this pattern

- **Simple Q&A systems**: If users only ask factual questions, the agent overhead adds latency without value. Use flat retrieve-then-generate.
- **Systems with a single corpus and fixed query type**: E.g., searching one regulation per query. No need for intent routing.
- **High-throughput / low-latency required**: Each agent adds ~2-5s (LLM call for classification, cross-encoder for reranking). For sub-second response times, skip the multi-agent orchestration.
