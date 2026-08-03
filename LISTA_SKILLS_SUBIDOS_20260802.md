# Skills subidos al repo — registro de integracion (2026-08-02, noche)

Repo: https://github.com/mmansillaf/hermes-skills.git (main)
Estructura: skills/<categoria>/<skill>/ (reorganizada por otra ventana 21:23,
force-push; se RESPETO y se integro encima — sin force push adicional)

## Estado tras integracion
- 87 skills ya estaban en el remoto (subidos por otra ventana 21:23)
- 32 skills NUEVOS agregados desde ~/.hermes/skills (este commit)
- 1 skill actualizado: p2p-messaging-forensics (version local 15.8K vs remoto 11.6K)
- Total: 119 skills con SKILL.md

## Los 32 agregados (categoria -> skill)
- data-science (11): backtest-simulation, inclusion-financiera-territorial,
  json-to-offline-fulltext-search, jupyter-live-kernel, method-selector,
  ml-pipeline-engine, offline-search-html-archive, scientific-statistical-engine,
  spatial-network-analysis, statistical-formula-engine, time-series-forecasting
- devops (5): env-credential-management, hermes-maintenance-wsl,
  hermes-performance-tuning, windows-disk-cleanup, go-microservices
- scraping (2): el-peruano-scraper, el-peruano-scraping
- lex-rag (1): lex-rag-chunk-audit
- software-development (3): codebase-audit, office-js-addins, offline-fulltext-search
- hermes-config (3): hermes-performance-optimization, hermes-recovery,
  skill-consolidation
- methodology (1): cognitive-enhancement-plan
- creative (2): estilo-cb-insights, pdf-design-analysis
- productivity (1): google-drive-shared-download
- media (2): hermes-torrent, yuanbao
- research (1): linkedin-forums-research

## Notas de seguridad
- go-microservices/references/legaltech-gateway.md: credenciales reales
  (SSH/PG/MySQL/JWT) SANEADAS -> referencian .env local. Verificado 0 hits.
- Repo es PUBLICO: no subir .env, tokens, datos de contacto de terceros.
- EmailScrapingContact/ (171MB OSINT) NO se sube -> agregar a .gitignore.

## Pendientes repo (NO commiteados, decisión usuario)
- untracked top-level: proyectos (Skill2ndBrainLegal, SkillBrochure, AppCeoExp,
  Curso_IA_ML_Practico, SmartMoney, SateliteImage, etc.) — decidir si van al repo
- borrados sin commitear de la estructura vieja (n8n-*, docs/, skills/) — el
  force-push del remoto ya los reemplazo; la estructura vieja vive solo en el
  branch local "main" (respaldo, commit aa2a5c2)
