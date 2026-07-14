# Evaluation Results — KGraphResolucionesV3 (Jun 2026)

Run: 20 preguntas across Laboral (10), Comercial (5), Civil (5)
Index: 77,507 documentos unicos, FAISS + BM25 + NetworkX
Synthesis: Llama 3.3 70B via Groq
Retrieval: Hybrid FAISS/BM25 + Reranker (cross-encoder/ms-marco-MiniLM-L-6-v2)

## Overall

| Metric | Result |
|:-------|:------:|
| Score | 171/200 (85.5%) |
| Average per question | 8.6/10 |
| Average time | 6.1s |

## By Legal Area

| Area | Score |
|:-----|:-----:|
| Civil (5) | 44/50 (88%) |
| Comercial (5) | 43/50 (86%) |
| Laboral (10) | 84/100 (84%) |

## Quality Dimensions

| Dimension | Result |
|:----------|:------:|
| Respuesta directa (sin intro generica) | 20/20 (100%) |
| Sin jerga tecnica | 20/20 (100%) |
| Seccion "Jurisprudencia citada:" | 20/20 (100%) |
| Con citas CAS./EXP./RTF | 7/20 (35%) |
| Tiempo promedio | 6.1s |

## Key Findings

1. **Respuesta directa at 100%** — the prompt instruction "RESPUESTA DIRECTA en la primera frase" is highly effective. No model needed retraining, just a well-phrased system instruction.

2. **Citation rate is the weakest metric (35%)** — The model cannot cite what is not in the source data. Our documents use hash-based doc_ids (MD5 of custom_id) instead of real identifiers like CAS. N° or EXP. N°. To improve: populate `identificador` in metadata_docs.json, or include the case number as an explicit field in the source extraction.

3. **Jerga tecnica at 0%** — The prohibition instruction works perfectly. The model never mentions grafos, nodos, FAISS, BM25, or any backend infrastructure in its answers.

4. **Speed is excellent (6.1s avg)** — Llama 3.3 70B via Groq with hybrid retrieval + reranker finishes in ~6s, well under the 15s target.
