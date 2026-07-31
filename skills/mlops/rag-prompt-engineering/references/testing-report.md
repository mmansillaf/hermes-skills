# RAG Prompt Testing Report: 4-Query Battery

## System Under Test

Lex RAG (GraphRAG Console)
- FAISS: 4,500 vectors (sentence-transformers/distiluse-base-multilingual-cased-v2)
- Graph: 21,732 nodes, 47,391 edges (NetworkX)
- LLM: Groq llama-3.3-70b-versatile
- Domain: Peruvian legal resolutions (tributary and labor)

## Prompt Version Tested

With conditional branching (Escenario A/B) + mandatory fallo citation
(from `references/pattern-conditional-branching.md`).

## Test Results

### Test 1: Positive — "violencia familiar"

```
que dice la jurisprudencia sobre la violencia familiar y las
medidas de proteccion
```

**Result:** Escenario A (relevant found)
- Documents: 1625727.html, 1654099.html, 1604395.html
- Fallos cited: All three, verbatim
- Graph used: Juez De La Barra Barrera appears in two cases; Ley N° 26260
  (Ley de Proteccion Frente a la Violencia Familiar) cited across all three
- Structure: Full 4-part (Sintesis → Evidencias → Grafo → Conclusion)
- **Veredict: PASS (9/10)**

### Test 2: Positive — "despido arbitrario"

```
cuales son los derechos del trabajador en caso de despido arbitrario
```

**Result:** Escenario A (relevant found)
- Documents: 1309073.html, 1616222.html, 1309231.html
- Fallos cited: All three, verbatim
- Rights identified: reincorporacion + indemnizacion
- Graph used: Juez Rey Terry; Art. 77 TUO DL 728
- Structure: Full 4-part
- **Veredict: PASS (9/10)**

### Test 3: Negative — "amparo"

```
resoluciones relacionadas con amparo
```

**Result:** Escenario B (no relevant context)
- Documents found (all tributary): 408739.html, 408679.html, 409026.html
- Each fallo shown with explanation of why tribunary matter not amparo
- Total length: 3 paragraphs (vs. ~600 words of padding under old prompt)
- **Veredict: PASS (10/10)** — dramatic improvement over old behavior

### Test 4: Negative — "desalojo express"

```
que dice la jurisprudencia peruana sobre el desalojo express
```

**Result:** Escenario B (no relevant context)
- Documents found: 1110810.html, 1602747.html, 962516.html
- Each fallo shown; explained as benefits, property, caducidad — not desalojo
- **Veredict: PASS (9/10)**

## Before vs. After (amparo query)

### BEFORE (old prompt — fixed 4-part structure always)

~600 words, 5 sections all saying "no hay nada" in different phrasing.
No fallos, no document IDs, no useful information. The model was forced
to pad empty content.

### AFTER (new prompt — conditional branching)

~250 words, 3 paragraphs:
1. "No se encontro jurisprudencia sobre amparo"
2. 3 documents listed with their fallos (tributary matters)
3. Explanation of mismatch

Transparent, concise, useful to the domain expert.

## Key Numbers

| Metric | Before | After |
|--------|--------|-------|
| Negative-case response length | ~600 words | ~250 words |
| Fallos cited in negative case | 0/3 | 3/3 |
| Docs shown in negative case | 0 | 3 |
| Graph relationships used in positive | Sometimes | Always |
| Hallucination in negative | Low risk (padding) | No risk (concise) |

## When to Re-run a Test Battery

- After any prompt template change (structure instructions)
- After changing the system message (role/identity)
- After changing the retrieval layer (number of docs, chunking, embedding model)
- After changing the LLM provider or model
