# Ecosistema Open-Source Legal RAG — Catálogo de Proyectos y Referencias

Investigación realizada julio 2026. Fuentes: GitHub topics, Crossref, OpenAlex, navegación directa.

## Proyectos GitHub de Referencia Directa

### NexusRAG ⭐ 323 — EL MÁS RELEVANTE
- **URL**: https://github.com/LeDat98/NexusRAG
- **Stack**: FastAPI + ChromaDB + LightRAG + BAAI/bge-m3 + bge-reranker-v2-m3 + Ollama/Gemini
- **Frontend**: Next.js con sistema de citas inline (IDs de 4 caracteres)
- **Document parsing**: Docling / Marker (switchable)
- **Por qué es relevante**: Stack casi idéntico al objetivo (FastAPI + vector + KG + reranker + Ollama + citas). Forkable y adaptable a dominio legal peruano.
- **Evaluación**: 16 tests hand-crafted (89% score) + 30 tests RAGAS sintéticos (83-87% pass rate)
- **Modelos recomendados**: Gemma 4 e4b (4.5B efectivo, 128K contexto, tool calling nativo), Qwen 3.5 9B

### RAG-VietNam-Traffic-Law ⭐ 4
- **URL**: https://github.com/franceto/RAG-VietNam-Traffic-Law
- **Stack**: FastAPI + BM25 + evidence filtering + HTML/CSS/JS UI
- **Relevancia**: RAG legal con FastAPI, arquitectura simple y funcional

### govrag-copilot ⭐ 1
- **URL**: https://github.com/AlAsiri-Ali/govrag-copilot
- **Stack**: Python + Gradio + TF-IDF/BM25 + Ollama + HuggingFace
- **Relevancia**: RAG regulatorio bilingüe con Ollama, citations, gap detection

### Korean Law MCP ⭐ 2.1k
- **URL**: https://github.com/chrisryugj/korean-law-mcp
- **Stack**: TypeScript + MCP + Claude + 42 Korean legal APIs → 9 MCP tools
- **Features**: legal_research (multi-step) + legal_analysis (citation verification, precedent life/death check, impact graph)
- **Relevancia**: Arquitectura MCP para datos legales, verificación de citas, detección de alucinaciones, impact graph

### Korean Law ALIO MCP ⭐ 11
- **URL**: https://github.com/scvcoder/korean-law-alio-mcp
- **Escala**: 87 leyes + 23 ALIO = 110 MCP tools, 1,600 leyes, 10,000 regulaciones administrativas, 35,000 normas internas

### Lawyer-LLaMA ⭐ 994
- **URL**: https://github.com/AndrewZhe/lawyer-llama
- **Descripción**: LLaMA fine-tuned para dominio legal chino. Referencia de metodología de fine-tuning legal.

### Claude for Legal ZH ⭐ 528
- **URL**: https://github.com/CSlawyer1985/claude-for-legal-ZH
- **Descripción**: Agentes legales, skills y MCP data connectors para Claude Code (derecho chino)

### Claude für Deutsches Recht ⭐ 1.3k
- **URL**: https://github.com/Klotzkette/claude-fuer-deutsches-recht
- **Descripción**: Skills experimentales para derecho alemán (laboral, societario, insolvencia, protección de datos)

### OpenNyAI Datasets
- **URL**: https://github.com/OpenNyAI
- **Descripción**: Datasets de NLP legal indio (sumarización de sentencias, QA, traducción)

### CAIL ⭐ 510
- **URL**: https://github.com/thunlp/CAIL
- **Descripción**: Dataset masivo de juicios legales chinos (predicción de cargos, artículos, sentencias)

## Proyectos LightRAG / GraphRAG

### LightRAG ⭐ 37.3k
- **URL**: https://github.com/HKUDS/LightRAG
- **Paper**: EMNLP 2025 — DOI: https://doi.org/10.18653/v1/2025.findings-emnlp.568
- **Features**: Entity/relationship extraction, hybrid search (local/global/hybrid/naive), Ollama compatible

### Graph-RAG-Agent ⭐ 2.3k
- **URL**: https://github.com/1517005260/graph-rag-agent
- **Descripción**: Integra GraphRAG + LightRAG + Neo4j + DeepSearch + evaluación custom
- **Relevancia**: Framework completo de evaluación para GraphRAG

### EdgeQuake ⭐ 2k
- **URL**: https://github.com/raphaelmansuy/edgequake
- **Descripción**: GraphRAG en Rust inspirado en LightRAG. Alto rendimiento.

### NexusRAG (ver arriba)
- Integra LightRAG para KG + ChromaDB para vectores + cross-encoder reranking

## Datos Legales Abiertos

### awesome-legal-data ⭐ 263
- **URL**: https://github.com/openlegaldata/awesome-legal-data
- **Descripción**: Colección curada de datasets, corpora, herramientas legales por país/región
- **Cobertura**: Global, EU, UK, DE, FR, IT, ES, NL, FI, PL, CH, AT, CZ, NO, TR, US, CA, MX, IN, CN, JP, KR, RU, BR, AU
- **Perú**: NO LISTADO — vacío identificado, oportunidad de contribuir

### Open Legal Data ⭐ 152
- **URL**: https://github.com/openlegaldata/oldp
- **Descripción**: Plataforma open-source de datos legales alemanes (Django + API)

### Datasets legales globales:
- **Pile-of-Law**: 256GB corpus legal/administrativo en inglés
- **MultiLegalPile**: Corpus multilingüe 24 idiomas para training de LLMs
- **LexGLUE**: Benchmark de comprensión de lenguaje legal
- **CUAD**: Contract Understanding Atticus Dataset (13 categorías de cláusulas)
- **MLEB**: Massive Legal Embedding Benchmark para IR legal

### Diarios oficiales con datos abiertos (referencia):
- **BOE España**: https://www.boe.es/datosabiertos/ (API abierta)
- **DOU Brasil**: https://www.in.gov.br/ (abierto)
- **DOF México**: https://www.dof.gob.mx/ (abierto)
- **El Peruano**: https://diariooficial.elperuano.pe/ — sin API abierta conocida, sin scrapers open-source

## Papers Académicos Relevantes

### LawRAG (2026)
- **Título**: "LawRAG: Indonesian legal document retrieval-augmented generation with specialized chunking and reranking strategies"
- **DOI**: https://doi.org/10.1108/dta-03-2025-0195
- **Relevancia**: Chunking especializado + reranking para dominio legal. El paper más cercano al proyecto.

### LightRAG (EMNLP 2025)
- **DOI**: https://doi.org/10.18653/v1/2025.findings-emnlp.568
- **arXiv**: https://doi.org/10.48550/arxiv.2410.05779

### Hybrid Multi-Agent GraphRAG for E-Government (2025)
- **DOI**: https://doi.org/10.3390/app15116315
- **Relevancia**: GraphRAG aplicado a gobierno electrónico

### Legal Document Analysis and QA using RAG (2026)
- **DOI**: https://doi.org/10.64643/ijirtv12i11-197134-459

### AQACO: Adaptive Query-Aware Chunking Optimization for RAG (2025)
- **DOI**: https://doi.org/10.21275/sr25329182150

### Privacy-First Architecture for Fully Local RAG (2026)
- **DOI**: https://doi.org/10.36227/techrxiv.176800894.46972585/v1

## Scraping de Fuentes Legales Peruanas

### CEJ Peru Scraper (skill existente `cej-peru-scraper`)
- Producción verificada: 2,376 PDFs de 1,440 expedientes
- Stack: Scrapy + Selenium + undetected_chromedriver + 2captcha
- Evasión WAF (Radware/PerfDrive), watchdog para batches largos
- Patrones transferibles a El Peruano

### TC SEDETC Scraper (skill existente `tc-sedetc-scraper`)
- Jurisprudencia del Tribunal Constitucional peruano

### Vacíos identificados:
- No existe scraper open-source para El Peruano
- No existe proyecto de código penal digital peruano con RAG
- Perú no está en awesome-legal-data

## Stack Recomendado (Validado por NexusRAG)

```
PDFs/DOCs → Docling/Marker → BAAI/bge-m3 (1024d) → ChromaDB + LightRAG KG
                                ↓
          FastAPI ← bge-reranker-v2-m3 (cross-encoder) ← over-fetch top-20
                                ↓
          Ollama (Qwen 3.5 9B / Gemma 4 e4b) → Respuestas con citas inline
```

### Embeddings para español legal:
- `BAAI/bge-m3` (1024-dim, multilingüe 100+ idiomas) — base
- `wilfredomartel/BGE-M3-Legal-Spanish` — fine-tuned sobre 600K ejemplos legales españoles

### Reranker:
- `BAAI/bge-reranker-v2-m3` — cross-encoder multilingüe

### LLM local:
- Qwen 3.5 9B (Q4_K_M, ~6GB RAM) — mejor español, function calling
- Gemma 4 e4b (~4.5GB efectivo) — 128K contexto, tool calling nativo
