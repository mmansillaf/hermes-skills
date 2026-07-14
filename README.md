# Hermes Skills — Legal Tech & RAG

Skills personalizados para [Hermes Agent](https://hermes-agent.nousresearch.com) workflow reutilizables para legal tech peruano, RAG, scraping judicial, y metodologías de desarrollo.

Creados y mantenidos por [@mmansillaf](https://github.com/mmansillaf).

## Estructura

```
skills/
├── legal/                         → RAG legal peruano
│   └── rag-legal                  → RAG local Qdrant + SQLite + DeepSeek/Groq
├── web-scraping/                  → Bypass de protecciones anti-bot
│   ├── web-scraping-waf-bypass    → Radware/Cloudflare/DataDome bypass
│   └── web-scraping-anti-bot-recon→ Reconocimiento de defensas anti-bot
├── devops/                        → Pipeline El Peruano e infraestructura
│   ├── api-rest-optimization      → Optimizaciones API REST
│   ├── cloudflare-r2-source-hosting→ Hosting R2 para fuentes HTML
│   ├── elperuano-deployment-options→ Opciones de despliegue
│   ├── elperuano-ingestion-pipeline→ Pipeline completo de ingesta
│   ├── elperuano-rag-backup-restore→ Backup multi-nivel + restauración
│   ├── elperuano-rag-mejoras-plan → 3 mejoras arquitectónicas
│   ├── pipeline-status            → Métricas y estado actual
│   ├── serper-alternatives        → Alternativas a Serper API
│   └── linux-system-cleanup       → Limpieza de disco en Linux
├── software-development/          → Scraping CEJ, clasificación, RAG, apps edu
│   ├── cej-scraper-auditoria      → Scraper masivo CEJ (Radware + captcha)
│   ├── clasificacion-documentos-por-contenido→ Clasificación masiva PDFs legales
│   ├── rag-data-ingestion         → Pipeline ingesta batch (FAISS+BM25+Graph)
│   ├── rag-retrieval-diagnostics  → Diagnóstico búsqueda y ranking RAG
│   ├── building-rag-systems-with-multiple-stores→ RAG multi-store completo
│   ├── html-edu-apps              → Apps educativas HTML/CSS/JS
│   ├── educational-assessment-app → Evaluaciones adaptativas single-page
│   ├── shiny-fastapi-dashboard    → Dashboards Shiny + FastAPI
│   ├── research-synthesis-html-preview→ Síntesis de investigación + HTML preview
│   └── word-office-integration    → Integración Hermes-Word
├── data-science/                  → ML/Estadística
│   ├── document-classification    → Clasificación PDFs por regex + embeddings
│   └── statistics-ml              → Guía práctica de estadística y ML
├── social-media/                  → Automatización
│   └── linkedin-marketing         → LinkedIn marketing B2B legal
├── creative/                      → Video y contenido
│   ├── veo-video                  → Google Veo 3/3.1 async
│   └── veo-video-generation       → Clips promocionales + overlay ffmpeg
├── hermes-config/                 → Configuración de Hermes Agent
│   ├── hermes-multi-model-routing → Routing entre modelos
│   ├── hermes-multi-provider-config→ Configuración multi-provider
│   ├── hermes-agent-operations    → Diagnóstico y recuperación
│   ├── hermes-agent-skill-authoring→ Authoring de skills in-repo
│   ├── hermes-sdd                 → SDD workflow para Hermes
│   └── skill-maintenance          → Mantenimiento de skills
└── methodology/                   → Metodologías de desarrollo
    ├── sdd                        → Spec-Driven Development
    ├── plan                       → Plan mode
    ├── writing-plans              → Planes accionables
    ├── subagent-driven-development→ Ejecución via subagentes
    ├── systematic-debugging       → Debugging en 4 fases
    ├── test-driven-development    → TDD estricto
    ├── project-audit-and-reporting→ Auditoría de codebases
    ├── simplify-code              → Cleanup paralelo de código
    └── spike                      → Experimentos descartables
```

## Instalación

```bash
# Opción 1: Clonar y copiar
git clone https://github.com/mmansillaf/hermes-skills.git
cp -r hermes-skills/skills/* ~/.hermes/skills/

# Opción 2: Usar directamente (requiere Hermes Agent)
skill_view(name='rag-legal')
```

## Skills destacados

### RAG Legal Peruano
- **rag-legal** — RAG local con Qdrant + SQLite + DeepSeek/Groq para búsqueda de jurisprudencia peruana
- **rag-data-ingestion** — Pipeline de ingesta batch: Groq Batch API, FAISS + BM25 + NetworkX indexing
- **rag-retrieval-diagnostics** — Trazabilidad completa del pipeline de búsqueda: embedding → retrieval → ranking → reranking
- **cej-scraper-auditoria** — Scraper del CEJ peruano con bypass de Radware, captcha solving, y filtrado inteligente por keywords
- **clasificacion-documentos-por-contenido** — Clasificación masiva de PDFs legales usando pymupdf + regex + symlinks + embeddings fallback

### Pipeline El Peruano
- **elperuano-ingestion-pipeline** — Pipeline completo: limpieza HTML → Groq Batch API → SQLite + Qdrant + Neo4j
- **elperuano-deployment-options** — Análisis de opciones de despliegue (Cloudflare Workers, GitHub Pages, VPS, HF Spaces)
- **elperuano-rag-mejoras-plan** — Plan de 3 mejoras arquitectónicas (embeddings 768d, grafo jerárquico, router por complejidad)

## Licencia

MIT
