# Implementation Session — LexRAG Deep Research v2

## Date
Mayo 23, 2026. Implementado en una sesión completa: análisis de Kimi DeepSearch → diseño → implementación → prueba.

## Project Location
`/mnt/d/PyCode/PyGraphRAG_MM/` — LexRAG Proyecto v3 (GraphRAG Legal peruano)

## Architecture Decision: All-in-One Script (Web Deep Research)
The `web_deep_research.py` script bundles planificador, buscador, verificador and sintetizador in one file with 4 classes. Rationale: fewer files to maintain, clearer dependency chain. The LexRAG v2 modules (`planner_legal.py`, `verifier.py`) are separate because they integrate with an existing modular codebase.

## Files Created

### New
- `modules/planner_legal.py` — LegalPlanner class. 10 legal types detected via regex (casación, amparo, nulidad, penal, laboral, constitucional, familia, procesal, debido_proceso, plenario + generic fallback). Generates 3-5 sub-queries from legal angles. Zero LLM cost. ~200 lines.
- `modules/verifier.py` — Verifier class. `evaluate()` computes coverage score (0-100), detects contradictions via negation-pair matching on shared concepts, identifies lagunas. `generar_queries_ronda2()` produces targeted re-queries. ~250 lines.
- `web_deep_research.py` — Standalone web research agent. 4 internal classes: WebPlanner, WebSearcher, WebVerifier, WebSynthesizer. Uses Serper API (google.serper.dev) + requests for content extraction. ~400 lines.

### Modified
- `modules/synthesis.py` — `query_graphrag_pro()` now accepts `deep_v2=True`. New internal `_deep_search_v2()` orchestrates: plan → ronda1 (parallel) → verify → ronda2 (if needed) → RRF fusion → context management (Kimi-style). The `prompt_magistrado` template gained coverage indicators, contradiction warnings, and confidence levels per claim. ~400 lines.
- `graphrag_pro_v3.py` — Added `--deep-v2` flag, `--compare` flag (runs normal + deep-v2 side by side), `--deep` backward compatibility alias. ~130 lines.

## Test Results

### planner_legal.py
Query: "casación por indebida motivación de resoluciones judiciales"
→ Type: casacion → 5 sub-queries: [original, marco normativo, precedentes vinculantes, doctrina aplicable, requisitos de procedencia]

Query: "nulidad de cosa juzgada fraudulenta"
→ Type: nulidad → 3 sub-queries

Query: "despido arbitrario en el régimen laboral privado"
→ Type: laboral → 5 sub-queries

Query: "divorcio por causal de separación de hecho"
→ Type: familia → 4 sub-queries

All 5 test queries correctly classified. Sub-queries are in Spanish legal language.

### verifier.py
Test with one empty sub-query → score 19.3% → detected laguna → generated 3 ronda2 queries. Correct.

### web_deep_research.py (WebPlanner only)
Query: "reforma pensional Perú" → 5 sub-queries: [original, qué es, quiénes involucrados, últimas noticias, análisis y contexto] → Correct.

## User Preferences Applied
- **Zero LLM cost**: all planning, verification, and detection uses rules, not LLM calls
- **Simple code**: all new modules have clear header blocks, short functions, Spanish variable names
- **Trade-offs documented**: every skill has a cost/benefit table comparing old vs new
- **Comparison mode**: `--compare` flag lets user see normal vs deep-v2 side by side
- **Incremental**: v2 builds on existing get_hybrid_context(), IndexManager, and graph infrastructure

## Key Design Decisions
1. `--deep-v2` flag (not `--deep v2`) — keeps CLI parsing simple, no positional args
2. RRF extended over both rounds — documents found in ronda 1 AND ronda 2 compete fairly
3. Kimi-style context management — when context > MAX_TOKENS_CONTEXT, round 2 chunks are prioritized, round 1 chunks are selectively hidden
4. Max 5 sub-queries, max 3 lagunas for ronda 2 — keeps each query under 90s total

## Pitfalls Discovered
- LegalPlanner needs periodic updates as new legal types emerge (e.g., "hábeas data", "acción popular")
- The contradiction detector uses simple negation-pair matching; real jurisprudential contradictions may need deeper semantic analysis
- Serper API key is required for web-deep-research; the user's `.env` file controls availability
