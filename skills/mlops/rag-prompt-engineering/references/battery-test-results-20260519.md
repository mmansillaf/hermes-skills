# Battery Test Results — 2026-05-19

## Context

14-query battery run against a legal GraphRAG system (FAISS + BM25 + NetworkX + Groq llama-3.3-70b-versatile) after implementing file-path document references.

Corpus: Corte Suprema ~23K, TC ~13K, Tribunal Fiscal ~3K, other ~18K (64K total HTML documents, 59K FAISS vectors, 192K graph nodes).

## Results Summary

| Metric | Value |
|--------|-------|
| Total queries | 14 |
| Total time | 254s (4.2 min) |
| Avg per query | 18.1s |
| Escenario A (data found) | 5/14 (36%) |
| Escenario B (no data) | 9/14 (64%) |
| Web search activated | 0/14 (0%) |
| File path references | 55 total, avg 3.9/query |

## Per-Query Breakdown

| ID | Query | Time | Result | File refs | Notes |
|----|-------|------|--------|-----------|-------|
| C01 | Requisitos amparo vs resoluciones judiciales (TC) | 25.8s | A | 7 | Excellent. Table with 4 requirements, each citing EXPs with paths |
| C02 | Plazo razonable en hábeas corpus (TC) | 24.4s | A | 3 | Good. Identified criteria with TC citations |
| C03 | Debido proceso en sanciones municipales | 12.4s | B | 1 | Found due process docs but from non-municipal organs |
| C04 | Nulidad actos municipales falta motivación | 12.2s | B | 0 | No municipal-specific docs in corpus |
| C05 | Requisitos órdenes de servicio en municipalidades | 21.6s | B | 3 | Found procurement docs but not specifically municipal |
| C06 | Acción popular contra ordenanzas municipales (TC) | 20.9s | A | 8 | Excellent. 8 TC documents with full paths |
| C07 | Despido arbitrario en administración pública | 12.9s | B | 0 | **HyDE overspecification**: same topic without "en la administración pública" works (see P02) |
| C08 | Responsabilidad por contrataciones ilegales | 18.7s | B | 4 | Found contract docs but not specifically about official liability |
| C09 | Principio de tipicidad: TC vs CS comparativo | 21.2s | A | 4 | Good comparative analysis |
| C10 | Proporcionalidad en sanciones admin: TC vs CS | 15.9s | B | 7 | Found 7 docs but LLM judged them non-responsive to the comparison |
| C11 | Plazo máximo en amparo (TC) | 15.6s | B | 7 | Same pattern: docs found but not exactly matching the query |
| C12 | Prescripción en infracciones administrativas (TC) | 21.4s | A | 7 | Good. Developed plazo calculation with TC citations |
| C13 | JNE vacancia regidores 2025 (intentionally absent topic) | 19.2s | B | 4 | Correct. "Información insuficiente" + actionable recommendations |
| C14 | Modificaciones Ley 27972 2025 (should be WEB) | 11.8s | B | 0 | **Router failure**: should have triggered web search. Classified as LOCAL |

## Key Findings

### 1. File Path References Work
55 references to `Jurisprudencia/doc.html` appeared across responses. The LLM follows the prompt instruction to include both the human-readable identifier (CAS. N°, RTF N°) and the file path. Users can Ctrl+click paths from the terminal to open the full resolution.

### 2. Router Does Not Detect Recent Years
C14 ("publicadas en 2025 en el Perú") was routed as LOCAL. The router keyword heuristic looks for "noticias", "farándula", "clima" but has no year-number detection. Any query containing `{current_year}` or `{current_year - 1}` should be a WEB candidate.

### 3. HyDE Overspecification (C07)
Adding "en la administración pública" to a query about "despido arbitrario" killed retrieval entirely. The HyDE expansion embedded the modifier, narrowing similarity scores below threshold. Without the modifier, the same query retrieves well (P02 from earlier battery).

### 4. Escenario B Quality
All 9 Escenario B responses followed the correct pattern:
1. Clear declaration ("No se encontró jurisprudencia en el corpus")
2. List of documents actually found (by ID + identifier)
3. Explanation of why they don't match the query
4. Actionable recommendation where possible (C13 suggested checking the JNE portal directly)

### 5. Comparative Queries Are Brittle
C09 (tipicidad) worked well. C10 (proporcionalidad) found 7 documents but the LLM judged them non-responsive to the comparison task. The prompt doesn't have a "third way" between Escenario A (rich analysis) and B (minimal response) — a comparative query that finds partial data needs a middle ground.

## Router Blind Spot Test Data

| Query | Router decision | Expected | Notes |
|-------|----------------|----------|-------|
| "última Ley 32186 sobre teletrabajo en Perú 2025" | LOCAL | WEB | Router saw "Ley" + number = legal query. Missed the 2025 signal. |
| "últimas noticias sobre el penal de Castro Castro en Perú 2025" | WEB | WEB | Router saw "noticias" = events. Correct. |
| "últimas modificaciones a la ley orgánica de municipalidades ley 27972 publicadas en 2025 en el Perú" | LOCAL | WEB | Same as first case. "modificaciones" + "ley" = legal, not current events. |

**Pattern**: The router triggers WEB only on informal current-events nouns ("noticias", "farándula", "clima"). It does NOT trigger on structured legal references to recent events, even when those references contain explicit year markers.

## Recommendation

1. **Year detection in router**: Add regex `(202[4-9]|2030)` — any query containing year >= (current_year - 1) should default to WEB unless the corpus explicitly covers that year.
2. **HyDE dual pass**: Generate two HyDE expansions — one with full query, one with restrictive modifiers stripped — and merge results via RRF.
3. **Comparative middle ground**: Add an "Escenario C" for queries that find partial data but not enough for full analysis.
