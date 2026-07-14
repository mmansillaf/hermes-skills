---
name: project-audit-and-reporting
description: "Systematic codebase audit: inspect structure, read sources, identify issues, and produce structured TXT reports with prioritized improvement plans and impact/effort matrices."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [audit, code-review, reporting, architecture, project-evaluation, codebase-analysis]
    related_skills: [codebase-inspection, systematic-debugging, requesting-code-review, web-security-audit]
prerequisites:
  commands: []
---

# Project Audit and Structured Reporting

Systematic methodology for reviewing a codebase, understanding its architecture, identifying strengths and weaknesses, and producing actionable structured reports — all saved as TXT files for the user's records.

## When to Use

- User asks "revisa este proyecto" / "review this project" / "audit this codebase"
- User wants a comprehensive project assessment before making changes
- User asks for an evaluation of improvements with impacto/esfuerzo/prioridad
- Pre-implementation analysis workflow ("dame tu opinion, evalua, no hagas cambios")
- New project onboarding — understanding the codebase before contributing

## Workflow

### Phase 1: Initial Reconnaissance

```
1. git log --oneline -N     # commit history (N=10-20)
2. git remote -v             # remote URLs
3. git describe --tags       # version tags
```

Then discover the project structure with **broad file searches**:

```
search_files(pattern='*.py',    target='files', limit=100, path='.')
search_files(pattern='*.md',    target='files', path='.')
search_files(pattern='*.txt',   target='files', path='.')
search_files(pattern='*.yaml',  target='files', path='.')
search_files(pattern='*.json',  target='files', path='.')
search_files(pattern='*.toml',  target='files', path='.')
search_files(pattern='*.cfg',   target='files', path='.')
search_files(pattern='Dockerfile*', target='files', path='.')
```

If results are truncated (100+), paginate with `offset=100`.

Also gather filesystem info:

```
du -sh data/                        # data directory size
du -sh .venv/ 2>/dev/null           # virtualenv size
wc -l src/**/*.py src/*.py          # total lines of Python
ls -la <key_directories>/           # check content of key dirs
```

### Phase 2: Deep Source Reading

Read the critical files in order, from highest-level to most detailed:

1. **README.md** — project purpose, setup, usage
2. **IMPLEMENTATION_PLAN.md** or DESIGN.md — original architecture intent
3. **config.py** / settings — technology choices, parameters
4. **Entry points** — krag.py, main.py, app.py, cli.py
5. **Core modules** — vector_store, llm_client, models, database
6. **Pipeline/agents** — orchestration logic
7. **Ingestion** — parsing, chunking, embedding
8. **API layer** — endpoints, UI rendering
9. **requirements.txt** / pyproject.toml — dependencies
10. **.env.example** — expected configuration

**IMPORTANT:** Read ALL source files. Partial reading produces incomplete reports. Each file >=500 lines may need `read_file(path, offset=N)` calls to paginate.

### Phase 3: Identify Strengths and Debilities

For each component, note:

| Aspect | What to evaluate |
|---|---|
| Architecture | Is there clear separation of concerns? Design patterns? |
| Code quality | Error handling, logging, comments, type hints |
| Completeness | What features does it have? What's missing? |
| Documentation | README, inline docs, example configs |
| Dependencies | Are all declared deps actually used? Any unused imports? |
| Testing | Is there a test suite? What's tested? |
| Security | Auth, input validation, data encryption |
| Performance | Caching, lazy loading, batch operations |

### Phase 3.5: Validate via Architecture Diagram (Optional)

Before writing prose, optionally create a visual architecture diagram to **validate your understanding** of the codebase. If the diagram reveals gaps (components you can't place, unclear data flows), go back and read the missing source files before drafting the report.

When the user asks *specifically* for a diagram ("haz un diagrama", "draw the architecture", "describe the system visually"):

1. Load the `architecture-diagram` skill
2. Build the SVG from your source reading — every box and arrow must be traceable to real code
3. Save as `<project-dir>/arquitectura.html` alongside any TXT reports

**Do NOT produce a diagram unless the user asks for it.** The default deliverable for project audits is the TXT report (Phase 4). Diagrams are a supplementary option for when visual comprehension is explicitly requested.

### Phase 3.75: Missing-Component Recovery Plan

When audit reveals broken imports, referenced-but-missing modules, or incomplete data files that prevent the codebase from running, create a structured recovery plan before writing the final report.

**Trigger conditions:** Entry point crashes with `ImportError`/`ModuleNotFoundError`, config references paths that don't exist on disk, README describes files missing from repo, imports reference modules that don't exist in the repo.

**Steps:**

1. **Diagnose broken imports.** Run the entry point and capture the error. Trace each failing import. Use `search_files(target='content', pattern='function_name')` to find if the referenced function exists elsewhere in the codebase.

2. **Cross-reference expected vs. actual index/data files.** For every file path in `config.py` or hardcoded constants, check existence:
   ```
   Expected: data/indices/faiss_index_pro.bin  → exists? YES  8.8 MB
   Expected: data/indices/bm25_index_pro.pkl   → exists? NO   MISSING
   ```

3. **Check for referenced-but-empty directories.** Look for directories mentioned in README or imports (`pipeline/`, `scripts/data_prep/`) that don't exist or are empty.

4. **Build the recovery hierarchy.** Assign each missing component:

   | Priority | Meaning |
   |---|---|
   | 🔴 Critical | Entry point won't run without it (import, required index) |
   | 🟡 Important | Feature degradation (secondary index, optional module) |
   | 🟢 Optional | Regeneration only (source data, test scripts, pre-processing) |

5. **Produce a recovery file.** Write `<project-dir>/ARCHIVOS_A_BUSCAR.txt` with group headers by priority: what references each file, what it contains, and concrete `find`/`ls` commands the user can run on the source machine.

6. **Optionally cross-reference with architecture diagram.** If Phase 3.5 produced a diagram, missing components will show as boxes-without-data — use this to validate the recovery plan covers everything.

### Phase 4: Generate Structured Report (TXT)

Structure the report with these sections:

```
==========================================================================
<TITLE>
==========================================================================

1. DESCRIPCION
   - One-paragraph summary of the project

2. ESTRUCTURA DEL PROYECTO
   - Tree with file sizes, line counts per source file
   - Total lines of Python

3. STACK TECNOLOGICO
   - Table: Component | Technology | Status

4. ARQUITECTURA / PIPELINE
   - ASCII diagram or bullet list of data flow

5. CARACTERISTICAS CLAVE
   - Bullet list of what works

6. DEBILIDADES ENCONTRADAS
   - Numbered list with severity (P1/P2/P3)

7. METRICAS
   - LOC, file count, dependencies, doc count, data size, RAM

8. CONCLUSION
   - Summary assessment
```

### Phase 5: Generate Improvement Evaluation (TXT)

Each mejora gets this structure:

```
MEJORA N: <TITLE>
  Prioridad:    P1 (CRITICO) / P2 (ALTO) / P3 (MEDIO/BAJO)
  Impacto:      Alto / Medio / Bajo
  Esfuerzo:     Alto / Medio / Bajo
  Dependencias: Python packages or system deps
  Descripcion:
    <detailed explanation of what to implement and why>
  Archivos a modificar:
    - src/...
  Archivos a crear:
    - (if any)
  Efecto:
    - <benefits>
  Riesgos:
    - <caveats>
```

Then include two summary sections:

```
RESUMEN DE PRIORIDADES

  P1 (CRITICO):
    N. <title>
  P2 (ALTO):
    ...
  P3 (MEDIO):
    ...

MATRIZ IMPACTO VS ESFUERZO

                       ALTO IMPACTO  |  MEDIO IMPACTO  |  BAJO IMPACTO
  ------------------------------------------------------------------------
  BAJO ESFUERZO        ...           | ...             | ...
  MEDIO ESFUERZO       ...           | ...             | ...
  ALTO ESFUERZO        ...           | ...             | ...
```

### Phase 6: Save Both as TXT

Save to the user's `reports/` directory if it exists, or project root:

```
reports/informe_proyecto_<YYYY-MM-DD>.txt
reports/evaluacion_mejoras_<YYYY-MM-DD>.txt
```

### Phase 7: Evaluate RAG Response Legibility (Optional)

When the user asks to test or evaluate a **RAG system's responses** (not code quality but answer quality), use this methodology.

**Triggers:** User says "revisa si las respuestas son legibles", "haz prueba de legibilidad", "evalua las respuestas", "son entendibles para humanos", or asks to test N questions.

**Steps:**

1. **Design the test set.** Create 10 questions spanning 3-4 ALTA (core domain), 3-4 MEDIA (niche), 2-3 BAJA (out-of-corpus). Include some the corpus CANNOT answer (tests hallucination resistance).

2. **Run each through the pipeline.** Record time, response text, follow-ups.

3. **Score legibility:** First-sentence directness (no "La consulta se refiere a..."), jerga tecnica (grafos/nodos/FAISS), structure (headers/bold/bullets), citation format ("Jurisprudencia citada:" section), inline citations, laws mentioned, words-per-sentence target < 30, follow-up generation.

4. **Identify prompt-level fixes.** Indirect responses = fix synthesizer prompt. Add "0. RESPUESTA DIRECTA: Responde en la PRIMERA FRASE." Jerga = add explicit prohibition. Missing citations = add format example.

5. **Before/after comparison.** Re-test after prompt fix. Same questions + new prompt = measurable delta.

6. **Save results.** Both .txt (transcripts) and .md (summary table) to reports/.

See references/rag-response-legibility-evaluation.md for working Python template.

### Phase 8: Web Application Security Audit (External)

When the user asks to audit a live website (not code) for vulnerabilities, bypass methods, or configuration issues, use this methodology.

**Triggers:** User says "revisa este sitio", "audita esta pagina", "busca vulnerabilidades", "analiza la seguridad de", or asks to investigate a website's anti-bot protection or API.

**Steps:**

1. **Initial probe with curl.** Check HTTP headers, server signature, response codes, redirects:
   ```
   curl -sI https://target.com/ | grep -i 'server\|x-powered\|x-frame\|csp\|hsts\|set-cookie'
   curl -s -o /dev/null -w '%{http_code} %{size_download}' https://target.com/path
   ```

2. **Browser navigation test.** Use `browser_navigate` to check if Radware/Cloudflare/DataDome blocks. If blocked, note the type of anti-bot:
   - Radware: validates via `perfdrive.com`, shows "We apologize for the inconvenience..."
   - Cloudflare: shows challenge page, uses Turnstile
   - hCaptcha: checkbox or image challenge
   - reCAPTCHA: Google-branded checkbox

3. **Technology stack detection.** From HTML, scripts, and headers:
   - JSF: `javax.faces.ViewState`, `jakarta.faces`, `j_idt` prefixed IDs, `formBusqueda` naming
   - Angular: compiled `main.*.js`, `runtime.*.js`
   - Java: `JBWEB` in error pages, `JSESSIONID` cookies
   - Framework: check for jQuery version, PrimeFaces, Bootstrap

4. **Endpoint discovery.** Probe paths systematically:
   ```
   /robots.txt, /sitemap.xml, /.env, /backup, /api/, /swagger, /docs
   ```
   For JSF apps, try direct access to `.html` forms and check for HTTP 405 (POST-only) vs 200 (accessible).

5. **Form analysis.** Extract all forms, hidden fields, CSRF tokens, and submit actions. Check if CSRF tokens are empty or predictable.

6. **Security scanner (wapiti).** Install and run against the target scope:
   ```
   wapiti --url https://target.com/ --scope domain --module "sql,xss,crlf,csrf,backup,htaccess,exec" -o /path/to/report -f html
   ```
   Review: backup files found, CSRF vulnerabilities, missing security headers (CSP, HSTS, X-Frame-Options).

7. **Radware bypass testing.** If Radware blocks, test these approaches in order:
   - **rebrowser-playwright** (patched playwright, bypasses Runtime.enable detection) — most effective
   - Headless mode + stealth init scripts (remove `navigator.webdriver`, add plugins/languages)
   - Navigate to less-protected entry points first (main page, not direct form access)
   - User-Agent rotation with real Chrome strings
   - Headed mode + real Chrome browser (`channel: 'chrome'`)
   - Changing order: sometimes Radware only triggers on specific paths

8. **Captcha analysis.** Identify captcha type and extract sitekey:
   - hCaptcha: look for iframes with `hcaptcha.com` and `sitekey=` param in URL fragment
   - reCAPTCHA: look for `recaptcha` in frame URLs with `?k=` param
   - Text captcha: look for `<img id="captcha_image">` with dynamic source URL
   - Extract sitekey from frame URL or DOM `[data-sitekey]` attribute
   - For 2Captcha: use `solver.hcaptcha(sitekey=..., url=...)` for hCaptcha, or `ImageToTextTask` for text captchas via API v2

9. **API proxy discovery.** Beyond browser-based forms, probe for REST/JSON endpoints:
   ```
   curl -X POST https://target.com/api/search -H "Content-Type: application/json" -d '{"query":"test"}'
   ```
   JSF apps sometimes have internal REST endpoints not protected by Radware.

10. **Proxy/VPN recommendations.** Based on findings, recommend:
    - No anti-bot or mild: datacenter proxies suffice
    - Cloudflare/Radware: residential rotating proxies required
    - High volume: DataImpulse ($1/GB), Decodo, Bright Data
    - Peruvian targets: Byteful and Bright Data have Peru-specific IP pools

11. **Document findings.** Save to `reports/informe_auditoria_web_<YYYY-MM-DD>.md` with:
    - Stack tecnologico
    - Vulnerabilidades encontradas (con severidad)
    - Bypass de proteccion (si aplica)
    - Captcha info (tipo, sitekey)
    - Endpoints mapeados
    - Recomendaciones

See `references/web-security-audit-ejemplo-cej.md` for a real-world example.

### Phase 9: Scraping Project Audit (Codebase + Metrics)

When the user asks to review an existing scraper/data-extraction project (not just code quality but also operational metrics), use this methodology after completing Phases 1-4.

**Triggers:** User shares a ZIP/7z of a scraper project, asks "revisalo", "evaluá el proyecto", "qué problemas ves", or needs a throughput/cost assessment.

**Additional metrics to gather beyond Phase 3:**

1. **Input data analysis.** Read source Excel/CSV files:
   - Total records count
   - Distribution by category (especialidad, distrito, año)
   - Column structure and field naming conventions

2. **Captcha performance analysis.** From logs and checkpoints:
   - Total captcha attempts vs successes vs fails
   - Captcha fail rate (e.g., 65% fail = critical problem)
   - Cost per captcha (2Captcha charges per attempt, fails still cost)
   - Time lost to captcha retries

3. **Throughput calculation:**
   ```
   rate = successful_records / total_runtime_hours
   total_time_estimate = remaining_records / rate
   ```
   Factor in: captcha retry time, cooldown between records, document download time, anti-bot sleep delays.

4. **Anti-bot strategy review.** Evaluate:
   - Cooldown between requests (duration, randomness)
   - Parallel download strategy (ThreadPoolExecutor generates detectable burst patterns)
   - Browser fingerprinting countermeasures
   - Session/cookie management
   - What triggers Radware/Cloudflare in current approach

5. **Architecture anti-patterns to flag:**
   - Scrapy used as task scheduler vs actual HTTP spider (common when Selenium does all the work)
   - `items.py` empty (fields not defined in Scrapy Item)
   - Hardcoded Chrome/driver binary paths
   - Mixed logging (`logger.info` + `print()`)
   - Missing retry logic on network calls
   - No exponential backoff on captcha failure

6. **Improvement prioritization:**

   | Prioridad | Criterio |
   |---|---|
   | P1-CRITICO | Blocking throughput entirely (captcha fail rate > 50%, anti-bot consistently blocking) |
   | P2-ALTO | Significant efficiency loss (slow cooldowns, missing retries, parallel bottlenecks) |
   | P3-MEDIO | Code quality, missing tests, hardcoded config |

7. **Generate dual report.** Save both:
   - `informe_proyecto_scraper_<YYYY-MM-DD>.txt` — code quality audit (Phases 1-4 format)
   - `evaluacion_rendimiento_scraper_<YYYY-MM-DD>.txt` — performance analysis with throughput table, bottleneck analysis, prioritized recommendations

## Pitfalls

1. **Do NOT modify any project files during the audit.** The user expects analysis, not implementation. If they wanted changes, they'd ask.

2. **Finish the active audit before starting a new task.** If the user asked you to audit a live website AND review a codebase ZIP in the same session, complete the website audit fully (headers, endpoints, wapiti scan, captcha analysis, proxy recommendations) before switching to the ZIP. Switching mid-stream forces the user to remind you what you still owe them.

3. **Read ALL source files.**
3. **Don't skip non-Python files.** Check for shell scripts, Docker configs, Makefiles — they reveal deployment strategy.
4. **Verify dependency usage.** Just because a package is in requirements.txt doesn't mean it's imported. Cross-reference with actual imports.
5. **Report format: TXT only.** The user prefers plain text files. Do not save as .md unless explicitly asked.
6. **Every debilidad needs severity (P1/P2/P3).** Vague issues without priority are skipped.
7. **Every mejora needs impacto + esfuerzo + prioridad.** Without the matrix, the user can't decide what to implement.
8. **Dead dependencies in requirements.txt** are a common finding (packages declared but never imported). Flag them.
9. **Check for empty/wasted directories** (e.g., `static/` with no files) and flag unused structure.
10. **Check for scripts referenced in docs but missing from disk** (e.g., README says `./start.sh` but no start.sh exists). — If the codebase has broken imports or missing data files, proceed to **Phase 3.75: Missing-Component Recovery Plan**.

11. **Web app security audit: wapiti false positives** — Backup file alerts from wapiti are often false positives when the server returns 403 (blocked by Radware/Cloudflare). Verify by checking HTTP status code, not just detection.

12. **Radware bypass is path-dependent** — A site may be accessible via one path (`busquedaform.html`) but blocked on another (`busquedacodform.html`). Always test multiple entry points.

13. **Scraper projects: separate code audit from performance audit** — A scraper can have clean code but crippling throughput. Address both dimensions separately with dual reports.

14. **Excel input files in scrapers can be large** — Reading 38K+ row Excel files with openpyxl can timeout. Use header-only reads or row counting without loading all data.

## References

- `references/report-template.txt` — Suggested report structure template (codebase)
- `references/evaluation-template.txt` — Suggested improvement evaluation template
- `references/multi-agent-graphrag-example.md` — Reference architecture: multi-agent GraphRAG (FAISS+BM25+NetworkX+DeepSeek/Groq) for legal document retrieval
- `references/web-security-audit-ejemplo-cej.md` — Real-world web security audit: cej.pj.gob.pe (Radware bypass, hCaptcha, JSF forms, wapiti scan)
