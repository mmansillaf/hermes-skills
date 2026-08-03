# Hermes Skills — Legal Tech & RAG

Skills personalizados para [Hermes Agent](https://hermes-agent.nousresearch.com): workflow reutilizables para legal tech peruano, RAG, scraping judicial, data science y metodologías de desarrollo.

Creados y mantenidos por [@mmansillaf](https://github.com/mmansillaf).

> **2026-08-03 — Reorganización:** 27 → 20 categorías, 119 → 118 skills. Eliminados duplicados exactos y pares casi-duplicados (plan, sdd, writing-plans, elperuano-rag-mejoras-plan, web-scraping-anti-bot-recon, rag-legal, el-peruano-scraping, paywall-bypass, web-scraping-waf-bypass). Categorías consolidadas: `web-scraping`/`web-scraping-waf-bypass` → `scraping`; `lex-rag`/`tc-searchrag` → `legal`; `*-dev-workflow` → `software-development`.

## Estructura (118 skills · 20 categorías)

```
skills/
├── legal/ (5)                → RAG legal peruano
│   ├── rag-legal             → RAG local Word/PDF (Qdrant + SQLite)
│   ├── lex-rag               → LexRAG: citas, batch, operación
│   ├── lex-rag-chunk-audit   → Trazabilidad granular de chunks + citas
│   ├── lex-rag-deep-research-v2 → Deep research legal multi-etapa
│   └── tc-searchrag          → Buscador jurisprudencia Tribunal Constitucional
├── scraping/ (11)            → Scraping judicial y bypass anti-bot
│   ├── cej-peru-scraper      → Scraper CEJ (Poder Judicial)
│   ├── cej-mcp-server        → MCP server para spiders CEJ
│   ├── el-peruano-scraper    → Scraper El Peruano
│   ├── tc-sedetc-scraper     → Scraper Tribunal Constitucional
│   ├── peruvian-judicial-scraping → Scraping judicial peruano general
│   ├── web-scraping-anti-bot-recon → Reconocimiento de defensas anti-bot
│   ├── web-scraping-waf-bypass → Bypass WAF (Radware/Cloudflare/DataDome)
│   ├── bypass-paywall        → Bypass de paywalls
│   ├── bypass-login-wall     → Bypass de login walls
│   ├── tc-ingesta-lexrag     → Ingesta TC → LexRAG
│   └── web-data-extraction   → Extracción web genérica
├── software-development/ (19)→ Dev, scraping, RAG, apps edu
│   ├── cej-scraper-auditoria → Scraper masivo CEJ (Radware + captcha)
│   ├── building-rag-systems-with-multiple-stores → RAG multi-store
│   ├── rag-data-ingestion    → Ingesta batch (FAISS+BM25+Graph)
│   ├── rag-retrieval-diagnostics → Diagnóstico búsqueda/ranking RAG
│   ├── lexrag-audit-optimize → Auditoría y optimización LexRAG
│   ├── codebase-audit        → Auditoría completa de codebase
│   ├── frontend-dev-workflow → React/TS/Vite: type-check, lint, test
│   ├── python-dev-workflow   → Python: scaffold, lint, test, type
│   ├── rust-dev-workflow     → Rust: build, clippy, fmt, audit
│   ├── html-edu-apps         → Apps educativas HTML/CSS/JS
│   ├── educational-assessment-app → Evaluaciones adaptativas
│   ├── shiny-fastapi-dashboard → Dashboards Shiny + FastAPI
│   ├── research-synthesis-html-preview → Síntesis + HTML preview
│   ├── word-office-integration → Integración Hermes-Word
│   ├── office-js-addins      → Add-ins Office.js
│   ├── offline-fulltext-search → Búsqueda full-text offline
│   ├── clasificacion-documentos-por-contenido → Clasificación PDFs legales
│   ├── laptop-hardware-diagnostics → Diagnóstico hardware
│   └── linux-dev-workstation → Workstation Linux para dev
├── data-science/ (16)        → ML/Estadística
│   ├── statistics-ml         → Guía práctica estadística y ML
│   ├── document-classification → Clasificación PDFs por regex + embeddings
│   ├── inclusion-financiera-territorial → Análisis inclusión financiera
│   ├── time-series-forecasting → Proyección indicadores económicos
│   ├── spatial-network-analysis → Redes espaciales
│   ├── backtest-simulation   → Backtesting
│   ├── ml-pipeline-engine    → Pipelines de Machine Learning
│   ├── scientific-statistical-engine → Motor estadístico 50+ dominios
│   ├── statistical-formula-engine → Fórmulas estadísticas
│   ├── method-selector       → Selección de método estadístico
│   ├── jupyter-live-kernel   → Python iterativo vía kernel Jupyter
│   ├── json-to-offline-fulltext-search → UI búsqueda offline desde JSON
│   ├── offline-search-html-archive → Archivo HTML buscable offline
│   ├── excel-consolidation   → Consolidación Excel
│   ├── extraccion-maxima-contactos → Extracción masiva de contactos
│   └── legal-platform-mvp    → MVP plataforma LegalTech
├── mlops/ (6)                → RAG/LLM ops
│   ├── legal-rag-local       → RAG legal local 16GB RAM
│   ├── local-llm-hardware-matching → Matching hardware → LLM local
│   ├── rag-evaluation        → Evaluación de RAG
│   ├── rag-citation-audit    → Auditoría de citas RAG
│   ├── rag-prompt-engineering → Prompt engineering RAG
│   └── satellite-imagery-acquisition → Imágenes satelitales
├── devops/ (14)              → Pipeline El Peruano e infraestructura
│   ├── elperuano-ingestion-pipeline → Pipeline ingesta normas
│   ├── elperuano-deployment-options → Opciones de despliegue
│   ├── elperuano-rag-backup-restore → Backup multi-nivel + restauración
│   ├── elperuano-rag-mejoras-plan → 3 mejoras arquitectónicas
│   ├── pipeline-status       → Métricas y estado actual
│   ├── api-rest-optimization → Optimizaciones API REST
│   ├── cloudflare-r2-source-hosting → Hosting R2
│   ├── serper-alternatives   → Alternativas a Serper API
│   ├── env-credential-management → Gestión segura de .env
│   ├── go-microservices      → Microservicios Go
│   ├── hermes-maintenance-wsl → Mantenimiento Hermes en WSL
│   ├── hermes-performance-tuning → Tuning rendimiento Hermes
│   ├── linux-system-cleanup  → Limpieza de disco Linux
│   └── windows-disk-cleanup  → Limpieza de disco Windows
├── hermes-config/ (9)        → Configuración de Hermes Agent
│   ├── hermes-agent-operations → Umbrella operaciones Hermes
│   ├── hermes-recovery       → Fix crashes/SQLite WAL
│   ├── hermes-multi-model-routing → Routing entre modelos
│   ├── hermes-multi-provider-config → Configuración multi-provider
│   ├── hermes-performance-optimization → Optimizar memoria/tokens
│   ├── hermes-sdd            → SDD workflow para Hermes
│   ├── hermes-agent-skill-authoring → Authoring de skills
│   ├── skill-consolidation   → Consolidar skills en umbrellas
│   └── skill-maintenance     → Mantenimiento de skills
├── methodology/ (10)         → Metodologías de desarrollo
│   ├── sdd                   → Spec-Driven Development
│   ├── plan                  → Plan mode
│   ├── writing-plans         → Planes accionables
│   ├── subagent-driven-development → Ejecución via subagentes
│   ├── systematic-debugging  → Debugging en 4 fases
│   ├── test-driven-development → TDD estricto
│   ├── project-audit-and-reporting → Auditoría de codebases
│   ├── simplify-code         → Cleanup paralelo de código
│   ├── spike                 → Experimentos descartables
│   └── cognitive-enhancement-plan → Optimización cognitiva
├── research/ (5)             → Investigación
│   ├── apex-research-framework → Marco de investigación profunda
│   ├── competitive-research-ai-projects → Investigación competitiva AI
│   ├── smart-money-research  → Capital inteligente
│   ├── linkedin-forums-research → Investigación LinkedIn/foros
│   └── agentic-ai-services   → Servicios AI agénticos
├── creative/ (5)             → Video, diseño y contenido
│   ├── veo-video             → Google Veo 3/3.1 async
│   ├── veo-video-generation  → Clips promocionales + overlay ffmpeg
│   ├── video-marketing       → Videos de marketing con IA
│   ├── pdf-design-analysis   → Extraer design system de PDFs
│   └── estilo-cb-insights    → Reportes estilo CB Insights
├── security-forensics/ (5)   → Análisis y forense
│   ├── anonymization-protocol-analysis → Tor/anonimización
│   ├── crypto-protocol-analysis → Protocolos criptográficos
│   ├── network-protocol-analysis → Análisis de red (tshark/scapy)
│   ├── p2p-messaging-forensics → Forense P2P messaging
│   └── whatsapp-desanonimizacion-stack → Research P2P messaging
├── productivity/ (4)         → Utilidades
│   ├── busqueda-local        → Buscador local WSL
│   ├── google-drive-shared-download → Descarga Drive compartido
│   ├── search-files-for-emails → Buscar emails en archivos
│   └── marketplace-selling   → Venta en Marketplaces
├── media/ (3)                → Media y entretenimiento
│   ├── hermes-torrent        → Integración con red BitTorrent
│   ├── heartmula             → Generación de canciones estilo Suno
│   └── yuanbao               → Grupos de Yuanbao
├── learnacelerated-framework/ (1) → Framework de aprendizaje acelerado
├── social-media/ (1)         → Automatización
│   └── linkedin-marketing    → LinkedIn marketing B2B legal
├── note-taking/ (1)          → Toma de notas
│   └── obsidian-study-system → Sistemas de estudio en Obsidian
├── remote-sensing/ (1)       → Sensores remotos
│   └── copernicus-satellite-imagery → Imágenes satelitales Copernicus
├── leisure/ (1)              → Ocio
│   └── find-nearby           → Buscar lugares cercanos
└── ux/ (1)                   → UX/UI
    └── english-quiz-designs  → Diseños de quiz de inglés
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
- **lex-rag** — Operación de LexRAG: calidad de citas, batch, troubleshooting
- **rag-data-ingestion** — Pipeline de ingesta batch: Groq Batch API, FAISS + BM25 + NetworkX indexing
- **rag-retrieval-diagnostics** — Trazabilidad completa del pipeline de búsqueda: embedding → retrieval → ranking → reranking
- **cej-scraper-auditoria** — Scraper del CEJ peruano con bypass de Radware, captcha solving, y filtrado inteligente por keywords

### Pipeline El Peruano
- **elperuano-ingestion-pipeline** — Pipeline completo: limpieza HTML → Groq Batch API → SQLite + Qdrant + Neo4j
- **elperuano-deployment-options** — Análisis de opciones de despliegue (Cloudflare Workers, GitHub Pages, VPS, HF Spaces)
- **elperuano-rag-mejoras-plan** — Plan de 3 mejoras arquitectónicas (embeddings 768d, grafo jerárquico, router por complejidad)

## Licencia

MIT
