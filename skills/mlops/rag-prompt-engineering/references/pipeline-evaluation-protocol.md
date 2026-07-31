# Pipeline Evaluation Protocol — Legal GraphRAG

## Structured Evaluation Battery

### Test Queries by Axes

**Materia + Complejidad:**

| ID | Query | Materia | Complejidad | Tipo esperado |
|----|-------|---------|-------------|---------------|
| P01 | "desnaturalizacion de contratos de trabajo" | Laboral | Simple | LOCAL (Escenario A) |
| P05 | "gastos de viaje deducibles en el impuesto a la renta" | Tributario | Simple | LOCAL (Escenario A/B) |
| P09 | "aplicacion del principio de no confiscatoriedad en tributos" | Constitucional-Tributario | Medium | LOCAL (Escenario A) |
| P13 | "diferencia entre nulidad de cosa juzgada fraudulenta y nulidad de oficio segun la jurisprudencia de la corte suprema" | Civil-Procesal | Complex | LOCAL (Escenario A) |
| P15 | "cual es la tendencia jurisprudencial del tribunal fiscal respecto a la aplicacion del principio de capacidad contributiva en el impuesto a la renta de tercera categoria" | Tributario | Complex | LOCAL (Escenario A con caveat) |
| WEB1 | "ultima Ley 32186 sobre teletrabajo en Peru 2025" | Legislación reciente | Simple | WEB (evento 2025) |
| WEB2 | "ultimas noticias sobre el penal de Castro Castro en Peru 2025" | Actualidad | Simple | WEB (noticias 2025) |

### Evaluation Template (per query)

```markdown
## PXX: "[query]" (Materia - Complejidad)

| Criterio | Resultado |
|----------|-----------|
| Escenario | A / B (N documentos) |
| Router decision | LOCAL / WEB (expected: X) |
| **Veracidad** | ☆ -- comentario |
| **Fidelidad al contexto** | ☆ -- comentario |
| **Tono** | ☆ -- comentario |
| **Explicativo** | ☆ -- SÍ/NO |

**Problemas encontrados:**
- ⚠️ Descripción del problema
```

### Scoring Rubric

| Score | Meaning |
|-------|---------|
| ☆ Excelente | Sin errores, supera expectativas |
| ☆ Buena | Funcional, con pequeñas mejoras posibles |
| ☆ Aceptable | Funciona pero con problemas notables |
| ☆ Deficiente | Errores significativos |
| ☆ Crítico | Falla en lo fundamental |

## Findings from Lex RAG Evaluation (2026-05-18)

### Working Well

1. **Híbrida retrieval (FAISS + BM25 + Graph)**: Finds relevant documents for simple, medium, and complex legal queries across multiple materias (laboral, tributario, civil-procesal, constitucional).
2. **Conditional prompt (Escenario A/B)**: Respected in most cases. The model correctly switches to concise negative-case when docs don't match the query.
3. **Transparency**: In P15, the model honestly reported "no direct jurisprudence found" rather than forcing relevance.
4. **Graph context**: Graph traversal enriches responses with related entities (jueces, leyes, partes vinculadas).

### Problems Found

| # | Problem | Severity | Affected queries | Fix priority |
|---|---------|----------|------------------|-------------|
| 1 | Router doesn't activate WEB for recent laws (Ley 32186/2025) | ALTA | WEB1 | 1 |
| 2 | Docs cited as `[Doc: hash]` instead of RTF N°/CAS. N° | ALTA | P01, P05, P09, P13, P15 | 1 |
| 3 | Falto (ruling) text never quoted verbatim | ALTA | P01, P05, P09, P13, P15 | 1 |
| 4 | "Corte Constitucional" instead of "Tribunal Constitucional" (Peru) | MEDIA | P09 | 2 |
| 5 | Web search activated but results not reflected in final response | MEDIA | WEB2 | 2 |
| 6 | Two different prompts between CLI (graphrag_console.py) and modular (graphrag_pro.py) | BAJA | All | 3 |

### Detailed Failure Analysis

#### Problem 1: Router Blind Spot

The router's rule says: activate WEB for "noticias del 2024+, farándula, clima o datos mundiales ajenos a la ley o a un juzgado/entidad". Ley 32186 (2025) has "Ley N°" prefix which the heuristic associates with legal queries, even though the year 2025 guarantees it's not in a static pre-2024 corpus.

**Fix**: Add a regex trigger to the router: if query contains `año|year 20[2-9]\d|202[5-9]` + `ley|decreto|norma|reglamento`, route to WEB.

```python
import re
current_year = 2026  # or detect dynamically
if re.search(rf'(?:ultima|ultimo|nueva|reciente|20[2-9]\d)\s*(?:ley|decreto|norma)', query, re.I):
    decision = 'WEB'
```

#### Problem 2: Document Identifier Format

The modular pipeline (graphrag_pro.py) uses the `retrieval/hybrid_search.py` module which returns `[Doc: {doc_id}]` labels. The `get_doc_label()` function exists in graphrag_console.py but is NOT used by the modular pipeline.

**Fix**: Either (a) port `get_doc_label()` from graphrag_console.py to the modular pipeline, injecting human-readable labels at context-build time, or (b) add a prompt rule that forces the model to use the metadata mapping.

#### Problem 3: Falto Not Cited

The modular pipeline's synthesizer prompt doesn't mandate quoting the "fallo" (ruling text) verbatim. The graphrag_console.py prompt does include this mandate: "Es OBLIGATORIO citar o parafrasear el texto del 'FALLO PRINCIPAL' de CADA documento."

**Fix**: Port the falto citation rule from graphrag_console.py's prompt to the modular pipeline's synthesizer.

#### Problem 4: Institution Name

"Tribunal Constitucional" is the correct Peruvian name. The model generated "Corte Constitucional" — a term used in Colombia, Ecuador, and Bolivia but not Peru. This is a model-level hallucination.

**Fix**: Add a system message note: "Todas las referencias a instituciones peruanas deben usar su denominación constitucional exacta: Tribunal Constitucional, Corte Suprema de la República, Tribunal Fiscal."

#### Problem 6: Two-Entry Divergence

The project has two CLI entry points with different prompts:

| Feature | graphrag_console.py | graphrag_pro.py |
|---------|--------------------|-----------------|
| Escenario A/B | ✅ Yes | ✅ Yes |
| Mandatory fallo citation | ✅ Yes | ❌ No |
| get_doc_label() IDs | ✅ Yes | ❌ No |
| Graph context | ✅ Yes | ✅ Yes |
| BM25 hybrid | ❌ No | ✅ Yes |
| Router (WEB/LOCAL) | ❌ No | ✅ Yes |
| Streaming | ✅ Yes | ✅ Yes |

**Fix**: Either fold graphrag_pro.py's features (BM25, router) into graphrag_console.py, or port graphrag_console.py's superior prompt into graphrag_pro.py.

## Reference: Lex RAG Architecture

```
Pregunta -> [Router] -> LOCAL: [FAISS + BM25] top_k -> [Graph traversal] -> [Synthesizer LLM]
                     -> WEB:   [SERPER search] -> [Synthesizer LLM]
```

- **FAISS**: 59,571 vectors (distiluse-base-multilingual-cased-v2)
- **BM25**: Lexical index over same chunks
- **Graph**: 191,871 nodes, 419,504 edges (jueces, leyes, partes, documentos)
- **LLM**: Groq llama-3.3-70b-versatile
- **Router model**: Groq (fallback chain: llama-4-maverick -> gpt-oss-120b -> kimi-k2 -> llama-3.3-70b)

## Post-Fix Validation: 10-Query Test Run (2026-05-18)

After applying the document linking patch (Approach A — file paths), a 10-query battery was executed across simple, medium, and complex queries covering laboral, tributario, civil-procesal, constitucional, and familia materias. The automated test script ran all 10 queries sequentially in a single session (model warm after first query, ~435s total).

**Test script**: `scripts/run_10_queries.py` (in the Lex RAG project root — adjacent to `graphrag_pro.py`)
**Full output**: `data/prueba_10_consultas_20260518.txt` (707 lines, 98 `Jurisprudencia/` path references)

### Results Summary

| ID | Query | Tiempo | Materia | Complexity | Document identifiers & paths in response? |
|----|-------|--------|---------|------------|-------------------------------------------|
| P01 | Desnaturalización contratos | 57s | Laboral | Simple | ✅ — CAS. N° 9325-2016-CUSCO (Jurisprudencia/1628456.html) |
| P02 | Indemnización despido arbitrario | 38s | Laboral | Simple | ✅ — CAS. N° 1612663 (Jurisprudencia/1612663.html) |
| P03 | Medidas protección violencia familiar | 54s | Familia | Simple | ✅ — IDs + paths present in response |
| P04 | Nulidad cosa juzgada fraudulenta | 108s | Civil-Procesal | Simple | ✅ — IDs + paths present |
| P06 | Reposición por desnaturalización | 37s | Laboral | Medium | ✅ — IDs + paths present |
| P07 | Maltrato psicológico violencia familiar | 35s | Familia | Medium | ✅ — IDs + paths present |
| P09 | No confiscatoriedad tributos | 25s | Const-Trib | Medium | ✅ — IDs + paths present |
| P10 | Excepción caducidad procesos civiles | 27s | Civil-Procesal | Medium | ✅ — IDs + paths present |
| P11 | Requisitos reposición servicio específico | 25s | Laboral | Complex | ✅ — IDs + paths present |
| P14 | Casación infracción normativa laboral | 29s | Laboral-Procesal | Complex | ✅ — IDs + paths present |

All 10 responses included both the human-readable identifier (CAS. N°, RTF N°, EXP. N°) and the relative file path (Jurisprudencia/{{id}}.html). The Source-Level Document Identifier Enrichment + Legal Document Linking (Approach A) patterns were validated on real queries across all materias in the corpus.

### Reference: Lex RAG Architecture (post-patch)

```
Pregunta -> [Router] -> LOCAL: [FAISS + BM25] top_k
             |                      |
             |            Hybrid context includes:
             |              **CAS. N° XXXX** -> Jurisprudencia/1612215.html
             |                         |
             |              [Graph traversal] includes:
             |                --- [1612215.html] (Jurisprudencia/1612215.html) ---
             |                         |
             |              [Synthesizer prompt] rule #3:
             |               "Cita el identificador legible + la ruta al archivo"
             v
         Respuesta: "segun **CAS. N° 15-2015 LAMBAYEQUE** (Jurisprudencia/1612215.html)"
```

## References

- Full evaluation report (pre-fix): `/mnt/d/PyCode/ResumenTokensJurisprudencias/data/evaluacion_consultas_20260518.md`
- Fix applied after evaluation: `references/patch-log-20260518-fix.md` in this skill — 4-file patch adding file paths + human-readable IDs
- Post-fix 10-query test output: `/mnt/d/PyCode/ResumenTokensJurisprudencias/data/prueba_10_consultas_20260518.txt`
- Post-fix test script: `/mnt/d/PyCode/ResumenTokensJurisprudencias/scripts/run_10_queries.py`
- Test queries definition: `/mnt/d/PyCode/ResumenTokensJurisprudencias/data/15_preguntas_abogado.txt`
- Previous test results: `/mnt/d/PyCode/ResumenTokensJurisprudencias/data/resultados_15_preguntas.txt`
