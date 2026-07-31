# Técnicas Avanzadas para RAG Legal — Investigación Julio 2026

Fuentes: arXiv (60+ papers revisados), Hacker News Algolia. Google, Reddit, Semantic Scholar API, y Bing estuvieron bloqueados.

## Papers Clave

### Anti-Alucinación

1. **LettuceDetect: A Hallucination Detection Framework for RAG Applications**
   - arXiv:2502.17125 (Feb 2025) — Kovács & Recski
   - ModernBERT-based, token-level classification, 8K context window
   - F1 79.22% (ejemplo-level), +14.8% sobre Luna (anterior SOTA encoder)
   - 30-60 ejemplos/segundo en una GPU, 30× más pequeño que modelos prompt-based
   - Repo: github.com/KRLabsOrg/LettuceDetect | HF: KRLabsOrg

2. **LegalGraphRAG: Multi-Agent Graph Retrieval-Augmented Generation for Reliable Legal Reasoning**
   - arXiv:2605.28120 (Mayo 2026) — Chen et al. — ACL 2026 Main Conference
   - Researcher (recupera) → Auditor (verifica contra fuentes) → Adjudicator (sintetiza)
   - Grafo jerárquico legal multi-granular (casos, artículos, interpretaciones)
   - SOTA en razonamiento legal verificable
   - Repo: github.com/XMUDeepLIT/LegalGraphRAG

3. **NeuroSymbolic AI for Legal AI-TRISM**
   - arXiv:2606.15646 (Junio 2026) — Tilwani, Saxena, Padia, Parthasarathy, Gaur
   - Trustworthy, Reliable, Interpretable, Safe Models para dominio legal

4. **Falkor-IRAC: Graph-Constrained Generation for Verified Legal Reasoning in Indian Judicial AI**
   - arXiv:2605.14665 (Mayo 2026) — Joy Bose
   - 20 páginas, 8 figuras, 4 tablas
   - "Legal reasoning is not semantic similarity search"

5. **Citation-Closure Retrieval and Per-Rule Attribution for Real-World Regulatory Compliance QA**
   - arXiv:2605.29742 (Mayo 2026) — Ju & Lee

### Chunking y Retrieval

6. **A Systematic Investigation of Document Chunking Strategies and Embedding Sensitivity**
   - arXiv:2603.06976 (Marzo 2026) — Shaukat, Adnan, Kuhn
   - 36 métodos de segmentación, 6 dominios, 5 modelos de embedding
   - Métricas: nDCG@5, Hit@5, Precision@1, MRR
   - **Hallazgo clave para legal**: Paragraph Group Chunking es óptimo (nDCG@5 ~0.459)
   - Content-aware >> fixed-size; modelos grandes + buen chunking = complementarios

7. **SproutRAG: Attention-Guided Tree Search with Progressive Embeddings for Long-Document RAG**
   - arXiv:2606.18381 (Junio 2026) — Abaskohi, Laradji, West, Carenini
   - Árbol binario de chunking con atención entre oraciones (sin LLM calls)
   - +6.1% Information Efficiency sobre baseline más fuerte
   - Evaluado en dominios científico, legal, y open-domain

8. **PluriHopRAG: Exhaustive, Recall-Sensitive QA Through Corpus-Specific Document Structure Learning**
   - arXiv:2510.14377 (Oct 2025) — Sveistrys & Kunert

### Evaluación

9. **Fine-grained Claim-level RAG Benchmark for Law (ClaimRAG-LAW)**
   - arXiv:2605.21071 (Mayo 2026) — Das, Abualhaija, Bianculli
   - Francés + Inglés, expertos + no-expertos
   - Evaluación claim-level separando retrieval y generation
   - Demuestra que RAG legal especializado aún alucina

10. **Better Call CLAUSE: A Discrepancy Benchmark for Auditing LLMs Legal Reasoning Capabilities**
    - arXiv:2511.00340 (Nov 2025) — Choudhury, Chandramouli, Anand, Gupta
    - 42 páginas, 4 imágenes

### Retrieval Legal (Competitions)

11. **NOWJ@COLIEE 2025: Multi-stage Framework Integrating Embedding Models and LLMs for Legal Retrieval and Entailment**
    - arXiv:2509.08025 (Sep 2025) — Nguyen et al.
    - BM25 + embeddings + LLM re-ranking pipeline

12. **Passage Retrieval of Polish Texts Using OKAPI BM25 and an Ensemble of Cross Encoders**
    - arXiv:2410.04620 — Pokrywka
    - Solución ganadora Poleval 2023 Task 3

### Otros Relevantes

13. **From Norms to Indicators (N2I-RAG): Agentic RAG Framework for Legal Indicator Computation**
    - arXiv:2605.26926 (Mayo 2026) — Al Mouatamid, Bonnin, Zahir

14. **Augmented Question-guided Retrieval (AQgR) of Indian Case Law**
    - arXiv:2508.04710 (Agosto 2025) — Vishnuprabha et al.
    - LLM + RAG + resúmenes estructurados

## Modelos Recomendados

### Embeddings
| Modelo | Dims | Contexto | Notas |
|--------|------|----------|-------|
| BGE-M3 | 1024 | 8192 | ⭐ Mejor multilingüe open-source, dense+sparse+ColBERT |
| ModernBERT-base | 768 | 8192 | Contexto extendido ideal para sentencias largas |
| multilingual-e5-large-instruct | 1024 | 512 | Instruction-tuned |
| jina-embeddings-v3 | 1024 | 8192 | Task-specific LoRA adapters |

### Re-Rankers
- BGE-Reranker-v2-m3 (multilingual)
- Cohere Rerank v3 (API, multilingual)
- jina-reranker-v2-base-multilingual (open-source)

## Benchmarks y Datasets

- RAGTruth: Corpus estándar para entrenar detectores de alucinación
- ClaimRAG-LAW: Benchmark legal fine-grained (FR+EN)
- Better Call CLAUSE: Auditoría de razonamiento legal de LLMs
- COLIEE: Competition on Legal Information Extraction/Entailment

## Herramientas Open-Source

- LettuceDetect: github.com/KRLabsOrg/LettuceDetect
- LegalGraphRAG: github.com/XMUDeepLIT/LegalGraphRAG
- RAGAS: github.com/explodinggradients/ragas
- BGE-M3: HuggingFace BAAI/bge-m3
- ModernBERT: HuggingFace answerdotai/ModernBERT-base
