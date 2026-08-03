# Citation Validation Research — Compendio de Papers Jul 2026

Este archivo condensa los hallazgos de 6+ papers sobre validación de citas
y detección de alucinaciones en RAG legal, encontrados durante investigación
de Julio 2026 via arXiv API + Crossref.

## Papers con DOI/arXiv verificados

### 1. Dahl 2025 — Lexis+AI y Westlaw hallucinan 17-33%
**arXiv:2405.20362**
Magesh, Surani, Dahl, Suzgun, Manning, Ho · Mayo 2024

Primer estudio preregistrado de herramientas legales AI comerciales. Evaluación
de Lexis+AI, Westlaw AI-Assisted Research, Ask Practical Law AI.

Hallazgos clave:
- Tasa de alucinación: 17-33% (NINGUN sistema libre)
- RAG reduce pero NO elimina hallucinations
- Proponen tipología: cita inventada / existente irrelevante / parcial / interpretación errónea
- Dataset preregistrado liberado

### 2. DEREK Module — Deep Extraction & Reasoning Engine
**arXiv:2507.15863**
Shi, Li, Liu, Wang, He, Yang, Shi · Julio 2025

Componente clave: LangGraph Verifier que impone CITATION OVERLAP.
Cada afirmación → debe tener chunk recuperado que la respalde.

Métricas:
- Sin verifier: TRACe < 0.30, unsupported > 8%
- Con verifier: TRACe > 0.50, unsupported < 3%

### 3. Reliability by Design — FCR < 0.2%
**arXiv:2601.15476**
Alex Dantart · Enero 2026

Tres paradigmas:
- Creative Oracle (standalone): FCR > 30%, FFR > 25%
- Expert Archivist (basic RAG): FCR ~5-15%, FFR ~3-8%
- Rigorous Archivist (advanced RAG): FCR < 0.2%, FFR < 0.5%

Técnicas para FCR < 0.2%: embedding fine-tune + cross-encoder rerank +
self-correction + programmatic verification (la más efectiva y barata).

Evaluación: 12 LLMs, 75 tareas, 2700 respuestas, revisión doble-ciego.

### 4. Citation Grounding — Verificación contra grafos legales
**arXiv:2606.00898**
Volodymyr Ovcharov · Mayo 2026

Verifica citas contra grafo ground-truth de 100.8M decisiones judiciales
ucranianas (502M edges, 21,736 statute nodes).

3 componentes: Citation Precision, Citation Relevance, Citation Temporality.
Resultados en 5 sistemas: CG 0.791-0.873, 13-21% hallucination rate.

CG-DPO: Preference Optimization con 4 estrategias de corruption →
98.5% precisión en distinguir citas correctas de corrompidas.

### 5. Who Checks the Citations? — Benchmarking detection
**arXiv:2606.21155**
Liu, Stammbach, Henderson · Junio 2026

Taxonomía de 1,000+ escritos con citas fabricadas:
- Caso inexistente: 34%
- Caso real cita incorrecta: 28%
- Jurisdicción incorrecta: 15%
- Cita anacrónica: 12%
- Fusión de casos: 11%

Benchmark: verificador programático (91.2% recall) SUPERA a GPT-5 agentic (82.8%).

### 6. From Judgments to Issues — Citation-hallucination control
**arXiv:2607.03325**
Piccioli et al. · Julio 2026

Pipeline que descompone fallos en issues individuales con XML estructurado
(IRAC framework) y control de alucinaciones de citas.

## Patrón de búsqueda (arXiv API)

```bash
# Buscar papers sobre citation hallucination legal
curl -s "https://export.arxiv.org/api/query?search_query=all:%22legal+citation%22+AND+all:hallucination&max_results=15&sortBy=relevance"

# Buscar citation grounding
curl -s "https://export.arxiv.org/api/query?search_query=all:%22citation+grounding%22+legal+LLM&max_results=10&sortBy=submittedDate"

# Buscar indeterminate citations detection
curl -s "https://export.arxiv.org/api/query?search_query=all:%22indeterminate%22+AND+%28all:%22citation%22+OR+all:%22hallucination%22%29+AND+all:%22legal%22"
```

Crossref fallback cuando arXiv no indexa:
```bash
curl -s "https://api.crossref.org/works?query=Lexis+Westlaw+AI+citation+hallucination+legal&rows=10&filter=from-pub-date:2024-01-01&sort=relevance"
```

## Tasas de alucinación consolidadas

| Sistema | Tasa reportada | Paper | Contexto |
|---------|:-------------:|-------|----------|
| Lexis+AI | 17-33% | Dahl 2025 | Evaluación comercial |
| Westlaw AI-Assisted | 17-33% | Dahl 2025 | Evaluación comercial |
| Claude Haiku 4.5 | 21% | Ovcharov 2026 | Sobre grafo ucraniano |
| Mistral Pixtral Large | 19% | Ovcharov 2026 | Sobre grafo ucraniano |
| Amazon Nova Pro | 13% | Ovcharov 2026 | Sobre grafo ucraniano |
| GPT-4 standalone | > 30% | Dantart 2026 | FCR sin RAG |
| Basic RAG (promedio) | 5-15% | Dantart 2026 | FCR con retrieval básico |
| Advanced RAG | < 0.2% | Dantart 2026 | FCR con pipeline completo |
| RAG-augmented production | 14% | Ovcharov 2026 | Citation Grounding |

## Indeterminate Citations — definición y detección

Una cita indeterminada tiene:
1. Formato legal correcto (EXP. N.°, CAS. N°, RTF N°)
2. Números verosímiles (no absurdos a simple vista)
3. NO existe en el corpus real

Señales de alarma:
- Año futuro (>2026) → ALTO
- Número excesivo (>5000 para CAS, >50000 para EXP) → ALTO
- Mismo dígito repetido (99999, 11111) → ALTO
- Secuencia obvia (12345, 123456) → MEDIO
- 6+ dígitos seguidos → MEDIO
- Ley con número > 50000 → ALTO

Implementación de referencia: `/mnt/c/Users/usuario/rag_citation_validator.py`
