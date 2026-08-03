# Legal Search State of the Art — July 2026

Compendio de papers y recursos identificados durante investigación multi-dimensión sobre
mejores prácticas en motores de búsqueda jurídica. 27+ papers con DOI/proyectos verificados,
organizados por dimensión.

---

## 1. Embeddings para Español Legal

| Paper | DOI | Año | Hallazgo clave |
|-------|-----|-----|----------------|
| From Fact Drafts to Operational Systems: Semantic Search in Legal Decisions | [10.3390/bdcc8120185](https://doi.org/10.3390/bdcc8120185) | 2024 | Evalúa 12 modelos de embedding en 1,172 decisiones judiciales. Top: Cohere embed-multilingual-v3, BGE-M3, jina-embeddings-v3, text-embedding-3-large, multilingual-e5-large |
| MultiLegalPile: A 689GB Multilingual Legal Corpus | [10.18653/v1/2024.acl-long.805](https://doi.org/10.18653/v1/2024.acl-long.805) | 2024 | Corpus legal 689GB en 24 idiomas, 17 jurisdicciones. Modelos pre-entrenados superan SotA en LEXTREME y LexGLUE |
| LEXTREME: Multi-Lingual Multi-Task Benchmark for Legal Domain | [10.18653/v1/2023.findings-emnlp.200](https://doi.org/10.18653/v1/2023.findings-emnlp.200) | 2023 | Benchmark multi-idioma para dominio legal. Referencia para evaluar embeddings |
| MMTEB: Massive Multilingual Text Embedding Benchmark | [10.48550/arxiv.2502.13595](https://doi.org/10.48550/arxiv.2502.13595) | 2025 | Evalúa embeddings en 250+ idiomas. BGE-M3 y multilingual-e5 top en categorías multilingües |
| ColBERT-XM: Modular Multi-Vector for Zero-Shot Multilingual IR | [10.48550/arxiv.2402.15059](https://doi.org/10.48550/arxiv.2402.15059) | 2024 | Late interaction multi-vector para IR multilingüe zero-shot |

**Modelos recomendados:** BGE-M3 (BAAI), multilingual-e5-large-instruct (Microsoft), bge-reranker-v2-m3 (cross-encoder companion).

---

## 2. Cross-Encoders y Reranking Legal

| Paper | DOI | Año | Hallazgo clave |
|-------|-----|-----|----------------|
| Mitigating Hallucinations in Discipline Inspection QA: Two-Stage RAG + Reranking | [10.3390/electronics15030541](https://doi.org/10.3390/electronics15030541) | 2026 | Confirma que reranking mejora significativamente precisión en QA legal |
| Simple Yet Effective Neural Ranking and Reranking Baselines for CLIR | [10.48550/arxiv.2304.01019](https://doi.org/10.48550/arxiv.2304.01019) | 2023 | Baseline para reranking cross-lingüe |

**Pipeline:** Hybrid retrieval (dense BGE-M3 + sparse BGE-M3 + BM25) → RRF fusion → cross-encoder reranking (bge-reranker-v2-m3).

---

## 3. Validación de Citas en RAG Legal

| Paper | DOI | Año | Hallazgo clave |
|-------|-----|-----|----------------|
| Hallucination-Free? Assessing Reliability of Leading AI Legal Research Tools | [10.1111/jels.12413](https://doi.org/10.1111/jels.12413) | 2025 | **Paper más importante de la lista.** Lexis+AI y Westlaw alucinan 17-33%. Propone tipología de alucinaciones. 34 citas recibidas |
| Correctness is not Faithfulness in RAG Attributions | [10.48550/arxiv.2412.18004](https://doi.org/10.48550/arxiv.2412.18004) | 2024 | Distingue corrección factual vs. fidelidad al contexto recuperado |
| RAGChecker: Fine-grained Framework for Diagnosing RAG | [10.48550/arxiv.2408.08067](https://doi.org/10.48550/arxiv.2408.08067) | 2024 | Claim extraction + attribution + verification fine-grained |
| SAKA-RAG: Structure-Aware Knowledge Abstraction for Legal Reasoning | [10.2139/ssrn.5413499](https://doi.org/10.2139/ssrn.5413499) | 2025 | Framework de abstracción de conocimiento consciente de estructura legal |

---

## 4. Chunking Strategies para Documentos Legales

| Paper | DOI | Año | Hallazgo clave |
|-------|-----|-----|----------------|
| Impact of Chunking Strategies on Domain-Specific IR in RAG Systems | [10.1109/coins65080.2025.11125724](https://doi.org/10.1109/coins65080.2025.11125724) | 2025 | Evaluó 90 configuraciones chunker-modelo. Sentence split (512 tok, 200 overlap) mejor baseline. Embeddings pequeños más estables que grandes |
| MultiLegalSBD: Multilingual Legal Sentence Boundary Detection | [10.48550/arxiv.2305.01211](https://doi.org/10.48550/arxiv.2305.01211) | 2023 | 130K+ oraciones legales anotadas en 6 idiomas. Modelos multilingües superan baselines en zero-shot. Crítico para SBD legal |
| LEXTREME | [10.18653/v1/2023.findings-emnlp.200](https://doi.org/10.18653/v1/2023.findings-emnlp.200) | 2023 | Benchmarks de tareas legales que informan decisiones de chunking |

---

## 5. Evaluación RAG para Dominio Legal

| Paper | DOI | Año | Hallazgo clave |
|-------|-----|-----|----------------|
| HyPA-RAG: Hybrid Parameter Adaptive RAG for Legal and Policy | [10.18653/v1/2024.customnlp4u-1.18](https://doi.org/10.18653/v1/2024.customnlp4u-1.18) | 2024 | Framework adaptativo: ajusta chunks, threshold, temperatura según consulta legal |
| NitiBench: Benchmarking LLM Frameworks on Thai Legal QA | [10.18653/v1/2025.emnlp-main.1739](https://doi.org/10.18653/v1/2025.emnlp-main.1739) | 2025 | Benchmark para QA legal en idiomas low-resource. Metodología transferible a español peruano |
| RAGBench: Explainable Benchmark for RAG Systems | [10.48550/arxiv.2407.11005](https://doi.org/10.48550/arxiv.2407.11005) | 2024 | Benchmarks explicables para RAG. Útil para validación legal |
| CRUD-RAG: Comprehensive Chinese Benchmark for RAG | [10.48550/arxiv.2401.17043](https://doi.org/10.48550/arxiv.2401.17043) | 2024 | Benchmark que cubre Create/Read/Update/Delete — relevante para actualización de normas |

---

## 6. Filtrado Temporal por Vigencia de Normas

| Paper | DOI | Año | Hallazgo clave |
|-------|-----|-----|----------------|
| **SAT-Graph RAG: Ontology-Driven Graph RAG for Legal Norms** | [10.3233/faia251598](https://doi.org/10.3233/faia251598) | 2025 | **Paper más importante sobre temporalidad legal.** RAGs estándar fallan por ser "ciegos" a estructura jerárquica, diacrónica y causal. Propone LRMoo-inspired ontology: distingue Works (normas abstractas) de Expressions (versiones). Resuelve queries temporales y de procedencia intratables para RAG estándar |
| LEGRA: Graph-Based Polish Court Rulings for RAG | [10.20944/preprints202511.1742.v1](https://doi.org/10.20944/preprints202511.1742.v1) | 2025 | Pipeline Neo4j: documentos, chunks, jueces, cortes, leyes como nodos conectados. Hybrid retrieval semántico + estructural. Aplicable a jurisprudencia TC peruana |
| Caseformer: Pre-training for Legal Case Retrieval | [10.48550/arxiv.2307.12033](https://doi.org/10.48550/arxiv.2307.12033) | 2023 | Pre-training para retrieval de casos legales basado en distinciones entre casos |

---

## 8. Arquitecturas Multi-Agente para Legal RAG

| Paper / Proyecto | DOI / arXiv | Año | Hallazgo clave |
|------------------|-------------|-----|----------------|
| **LegalGraphRAG: Multi-Agent Framework** | ACL 2026 | 2026 | 3-agent pattern: Researcher→Auditor→Adjudicator. Grafo jerárquico 3 niveles. SOTA para RAG legal estructurado |
| **Falkor-IRAC: Legal Reasoning with Graph** | arXiv | 2025 | Razonamiento legal con grafo + patrón Issue-Rule-Application-Conclusion |
| **N2I-RAG: Agentic RAG for Legal Indicators** | arXiv | 2025 | RAG agéntico para indicadores legales |
| **NyayaAI: Multi-Agent Legal QA** | Mastra TS | 2026 | Subagentes especializados, arquitectura TypeScript |

## 9. Verificación de Citas — Nuevos Hallazgos (Jul 2026)

| Paper / Proyecto | DOI / arXiv | Año | Hallazgo clave |
|------------------|-------------|-----|----------------|
| **DEREK Module: Detección de Citas Indeterminadas** | arXiv:2507.15863 | 2026 | Citas "indeterminadas" (bien formateadas pero inventadas) son el mayor punto ciego — pasan desapercibidas incluso con validación |
| **Reliability by Design: FCR < 0.2%** | arXiv:2601.15476 | 2026 | False Citation Rate < 0.2% con pipeline de verificación programática |
| **GPT-5 Citation Hallucination Detection** | arXiv/jun 2026 | 2026 | 82.8% recall en detección de alucinaciones de citas |
| **CourtListener + Claude MCP Integration** | lawnext.com | 2026 | API MCP con Claude (May 2026). MCP es estándar emergente para APIs legales |
| **harvard-lil/olaw** | ⭐162 GitHub | 2026 | Harvard Legal Innovation Lab. "legal AI in a box" con LangChain |
| **justicio (bukosabino)** | ⭐146 GitHub | 2025 | RAG sobre BOE español. Proyecto más cercano cultural/lingüístico al derecho peruano |
| **GraphAugmented-Legal-RAG** | ⭐81 GitHub | 2025 | Grafo de conocimiento (Neo4j) + RAG semántico |
| **CALRK-Bench** | arXiv | 2025 | Benchmark de razonamiento temporal legal. GPT-4/Claude rinden bajo en validez temporal |
| **Beyond Probabilistic Similarity** | arXiv | 2026 | Crítica estructural al RAG legal. Propone arquitecturas deterministas |

## 10. Stack Tecnológico

| Paper | DOI | Año | Hallazgo clave |
|-------|-----|-----|----------------|
| Benchmarking Open Source Vector Databases | [10.54116/jbdai.v4i1.80](https://doi.org/10.54116/jbdai.v4i1.80) | 2026 | Evalúa FAISS, Chroma, Qdrant, Weaviate, Milvus, OpenSearch, PGVector en corpus 175-2.2M vectores. Mide latencia, throughput, cold-start. Chroma: 7.7-8.4ms, 141 QPS. FAISS: ~0.9ms FlatL2 |
| Survey of Vector Database Management Systems | [10.48550/arxiv.2310.14021](https://doi.org/10.48550/arxiv.2310.14021) | 2023 | Survey completo de sistemas de bases de datos vectoriales |
| COLIEE 2024: Legal Information Extraction/Entailment | [10.1007/978-981-97-3076-6_8](https://doi.org/10.1007/978-981-97-3076-6_8) | 2024 | Competencia anual de retrieval y entailment legal. Benchmarks y técnicas estado-del-arte |
| Exploring LLMs Applications in Law | [10.1109/access.2025.3533217](https://doi.org/10.1109/access.2025.3533217) | 2025 | Literature review sobre aplicaciones LLM en derecho. Mapeo completo del ecosistema |

---

## Stack Recomendado por Fase

### Fase 1: MVP (5-20K docs)
FAISS + BM25 + RRF → BGE-M3 → bge-reranker-v2-m3 → SQLite (metadata)

### Fase 2: Producción (50-200K docs)
PGVector (vectores + metadata + filtros) → BGE-M3 → NetworkX (grafos)

### Fase 3: Escala (>200K docs)
Milvus (vectors) + Neo4j (knowledge graph legal) + PostgreSQL (metadata)
Hybrid retrieval en Milvus (dense + sparse BGE-M3)
Graph queries en Neo4j (precedentes, jueces, leyes)
