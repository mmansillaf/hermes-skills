---
name: research-synthesis-html-preview
title: "Research → Synthesis → HTML Preview"
description: "Investigate existing local research materials, supplement with web research for latest findings, cross-reference and synthesize into a structured document, and produce an interactive HTML preview/prototype of the concept. Ideal for exploring new project ideas before building."
tags: [research, synthesis, html-preview, prototyping, investigation, document-generation]
related_skills: [project-audit-and-reporting, generate-devkit-from-spec, writing-plans]
---

# Research → Synthesis → HTML Preview

Investigate a domain by reviewing existing local materials and supplementing with web research, then produce both a structured synthesis document and an interactive HTML preview/prototype.

## When to Use

- User asks to review material in a folder and investigate a topic
- User wants an HTML preview of a concept before coding (per preference)
- Exploring a new project domain (edtech, legal tech, whatever) — research-first approach
- Pre-implementation exploration: "revisa esto, investiga, y dime qué se puede hacer"
- Competitive/domain research that needs to be visualized as a prototype

## NOT When to Use

- User wants actual code implementation — use SDD or generate-devkit-from-spec instead
- Task is pure code review of an existing codebase — use project-audit-and-reporting
- Task is a simple search without analysis — just use web_search directly

## Pre-Flight: Provider Health Check

**Before** starting any research, verify search providers and auxiliary models are healthy. A session that starts blind (403 from Serper, silent fallback failure) wastes turns and frustrates the user.

### Search Provider Check

Test the MCP search provider and native Hermes search in parallel:

```bash
hermes mcp test kindly-web-search 2>&1
```

If MCP responds with 403 Forbidden, the **Serper** API has 0 credits but the MCP wrapper selected it over Tavily.

**Provider priority in kindly-web-search:**
- Original: Serper (if key exists) → Tavily → SearXNG — results in 403 when Serper has no credits even if Tavily key exists
- **Fixed:** Tavily (if key exists) → Serper → SearXNG

**Fix:** Patch `mcp-wrapper.sh` to export both `SERPER_API_KEY` and `TAVILY_API_KEY`, and swap provider priority in `src/kindly_web_search_mcp_server/search/__init__.py`. See `references/mcp-search-provider-fix.md`.

### Auxiliary Provider Check

`google_ai_studio` as auxiliary provider causes silent failures when the API key isn't detected by Hermes' auxiliary system. Fix all at once:

```bash
for svc in vision web_extract compression skills_hub approval mcp \
           title_generation curator session_search tts_audio_tags \
           triage_specifier kanban_decomposer profile_describer \
           monitor background_review; do
  hermes config set auxiliary.$svc.provider auto
  hermes config set auxiliary.$svc.model ""
done
hermes config set auxiliary.title_generation.provider groq
hermes config set auxiliary.title_generation.model llama-3.3-70b-versatile
```

**Always use `hermes config set`** — direct yaml editing of `~/.hermes/config.yaml` is blocked by a safety guard.

### Decision Matrix

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| MCP search → 403 | Serper 0 credits, wrapper only exports SERPER | Fix wrapper, kill MCP processes. Fallback: native `web_search()` |
| MCP search → ClosedResourceError | Old processes killed, watchdog not respawned | Use native `web_search()` — it uses Tavily directly |
| `web_extract` → fails silently | Auxiliary provider broken (google_ai_studio) | Run the `hermes config set` loop above |
| All healthy | Both work | Proceed to Phase 1 |

### Phase 1: Inventory Local Materials

```python
# Find all files in the target folder
search_files(target='files', pattern='*', path='/path/to/folder', limit=50)

# Read each file — batch independent reads in parallel
read_file(path='/path/to/folder/file1')
read_file(path='/path/to/folder/file2')
# etc.
```

**Key assessment questions for each file:**
- What's the format? (markdown, txt, HTML, PDF, code)
- What's the quality? (casual notes, rigorous research, prompt draft)
- What's missing that needs web research?
- Are there contradictions between files to resolve?

### Phase 2: Multi-Vector Research Axis Identification

Before searching, **systematically derive research axes from gaps in the local materials.** This is more targeted than generic "search for the latest."

**Method:** For each gap you identify in Phase 1, map it to a research dimension:

| If local materials are weak on... | Research dimension | Example axis question |
|---|---|---|
| Latest paradigm shifts | **Evolution & trajectory** | "Has the field moved past the concepts in these docs?" |
| Debates & criticisms of the core approach | **Controversy & skepticism** | "What do critics say about this methodology?" |
| Security vulnerabilities specific to the domain | **Threat model** | "What new attack vectors exist for this class of system?" |
| Competing tools/frameworks | **Competitive landscape** | "What alternatives exist beyond what's covered here?" |
| Token/resource optimization | **Efficiency techniques** | "What production optimization patterns are emerging?" |
| Community sentiment | **Practitioner consensus** | "What are real practitioners saying about this?" |
| Technical detail depth | **Deep-dive specifics** | "What are the concrete implementation details?" |

Derive **4-6 axes** from what the local materials DON'T cover, not from what they do. The goal is gap filling, not redundancy.

### Phase 2b: Two-Phase Parallel Search Strategy

**Wave 1 — Broad parallel search (4-6 simultaneous):** Launch one search per research axis in a single turn:

```python
# Batch ALL independent searches in ONE response turn
mcp__kindly_web_search__web_search(query="axis 1: query derived from gap", num_results=5)
mcp__kindly_web_search__web_search(query="axis 2: query derived from gap", num_results=5)
mcp__kindly_web_search__web_search(query="axis 3: query derived from gap", num_results=5)
mcp__kindly_web_search__web_search(query="axis 4: query derived from gap", num_results=5)
mcp__kindly_web_search__web_search(query="axis 5: query derived from gap", num_results=5)
```

Wave 1 rapidly identifies which axes have rich findings worth deep-diving and which are dead ends.

**Wave 2 — Targeted deep search (2-3 follow-ups):** After reviewing wave 1 results, identify the axes with the most novel or unexpected findings and launch narrower follow-up queries:

```python
# Narrower, more specific queries from promising leads in wave 1
mcp__kindly_web_search__web_search(query="specific source or claim from wave 1", num_results=3)
mcp__kindly_web_search__web_search(query="related concept discovered in wave 1", num_results=3)
```

Fetch key sources for full detail:
```python
mcp__kindly_web_search__get_content(url="https://key-article.com/report")
```

**Track progress with todo list.** For research with 5+ independent dimensions, use `todo()` to track which axes are searched, which need deep dives, and what's been synthesized. Update status as each wave completes.

**Fallback when MCP search fails:**
- 403 Forbidden → native `web_search()` (Hermes built-in, uses Tavily directly)
- Both fail → browser_navigate as last resort

### Phase 3: Deep Dive on Key Discoveries

When a search result reveals a genuinely novel framework or finding (e.g., EPI/MARS-EARS by Conti, neuroeducation study, interleaving research), fetch the source for detail:

```python
web_extract(urls=["https://key-source.com/article"])
# or if extract fails, use browser_navigate
```

**Tag findings by type:**
| Type | Example | How to handle |
|------|---------|---------------|
| 🔬 Academic study | "244.8% improvement" | Note effect size, sample size, year |
| 📐 Framework/methodology | EPI, MARS-EARS, Spaced Repetition | Extract steps, principles, implementation |
| ❌ Common pitfalls | Foros/Reddit consensus | Capture as "does NOT work" |
| 🛠 Tools & apps | Duolingo Max, BeConfident | Extract features, pricing, strengths/weaknesses |
| ⚠️ User corrections | MCP server errors | Save as reference, note the blocker |

### Phase 4: Cross-Reference & Synthesize

**Identify:**
- What the local materials already cover well
- What new findings fill gaps
- What contradictions exist and how to resolve them
- What the user explicitly values (e.g., Python stack, Shiny, HTML previews)

**Choose the report framing based on the user's goal:**

| User goal | Report framing | Structure emphasis |
|-----------|---------------|-------------------|
| "Investiga este tema y dime qué hay" | **Neutral synthesis** | Balanced overview of everything found |
| "Revisa esto y dime qué le falta" | **Gap analysis** 🎯 | "What's missing" as organizing principle |
| "Dame tu opinión sobre estas ideas" | **Evaluative critique** | Strengths + weaknesses + recommendations |
| "Compara enfoques/tecnologías" | **Competitive benchmark** | Side-by-side comparison tables |

**Structural template for the synthesis document (MD):**

```
# INFORME CONSOLIDADO: <Title>

> Fecha: <date>

---

## ÍNDICE

1. [Resumen Ejecutivo](#)
2. [<First Major Section>](#)
...
N. [Referencias Clave](#)

---

## 1. Resumen Ejecutivo

### El Problema
### La Solución
### Resultados Esperados / KPIs

---

## N. Referencias Clave

1. <reference>
```

**Must include sections:**
- **Resumen Ejecutivo** — problem + solution + expected outcomes
- **Findings with ranking/evidence** — table format preferred
- **Benchmarking/comparison** — if applicable
- **Specific recommendations** for the target audience (e.g., Spanish speakers)
- **Referencias** with source URLs and study details

**Gap-Analysis variant** (use when the user wants to know what's missing from existing materials):

Structure the report as "areas not covered" rather than "neutral summary." Each section = one gap:

```markdown
## ÁREA N: <Gap Title — what's missing>

### ¿Qué falta en los materiales actuales?
- Specific concepts, frameworks, or findings absent from the local docs

### Hallazgos clave de la investigación
- What the web research revealed, with source citations

### Implicaciones
- Why this matters — what changes if you incorporate this

### Fuentes:
- bullet list with URLs
```

End with a **Priority Recommendations** section:

```markdown
## Recomendaciones para Actualizar tus Documentos

### Prioridad Alta (más impacto inmediato):
N. **<Recommendation>** — <why, 1 sentence>

### Prioridad Media:
N. ...

### Prioridad Baja / Nice-to-have:
N. ...
```

**Gap analysis reports must include a "what's well-covered" section** too — acknowledging existing strengths balances the critique and shows you read the materials thoroughly.

### Phase 5a: Generate Interactive HTML Preview (Visual Prototype)

The HTML preview is a **visual prototype** of the proposed concept/solution — NOT a data report with charts. It shows UI, flows, interactions. Use this when the user wants to "see the concept" before coding.

**Structure:**

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><ProjectName> — Preview</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* Dark theme */
        :root {
            --bg: #0f1117;
            --bg-card: #1a1d27;
            --border: #2a2e3f;
            --text: #e2e4ed;
            --text-secondary: #8b8fa6;
            --accent: #6c5ce7;
            --accent-light: #a29bfe;
            --success: #00b894;
            --warning: #fdcb6e;
            --danger: #e17055;
            --info: #74b9ff;
        }
        /* Mobile-first responsive, no JS required for layout */
    </style>
</head>
<body>
```

**Required components for a concept preview:**
1. **Header/Nav** — project name, level/status badge, user badge
2. **Dashboard grid** — sidebar + main content + right panel
3. **Welcome card** — contextual greeting, streak/progress visuals
4. **Stats row** — 4 key metrics in cards
5. **Current lesson/activity card** — step-by-step workflow with visual indicators
6. **Supplementary cards** — pronunciation, vocabulary review, quick actions
7. **Error examples** — domain-specific corrections (Spanish speakers' English errors, etc.)
8. **Footer** — attribution, date, methodology note

**Design rules:**
- Dark theme with purple accent (`#6c5ce7`)
- CSS variables for all colors
- No external CSS/JS frameworks — pure HTML+CSS inline
- Google Fonts only (Inter preferred)
- Responsive: 1-col mobile → multi-col desktop via CSS Grid
- Cards with subtle border and hover lift effect
- Progress bars with gradient fills
- All interactive elements should look clickable (hover states)
- No Chart.js or data-heavy charts — this is a UI prototype, not a report
- Include concrete domain-specific content (not lorem ipsum)

### Phase 5b: Build Functional Web App

Use this when the user asks for a **working tool** (quiz, evaluator, calculator, game) — not just a visual prototype. The output is a self-contained single-file HTML with full JavaScript logic, not static UI.

#### Decision: Visual Prototype vs Functional App

| Signal from user | Phase | Output |
|-----------------|-------|--------|
| "preview", "prototipo", "interfaz", "UI", "mockup" | Phase 5a | Static HTML with sample data, no backend logic |
| "app", "funcional", "evaluación", "quiz", "test", "examen", "herramienta" | Phase 5b | Single-file HTML with full JS engine, question bank, scoring, results |
| Both ("preview y luego la app") | Phase 5a then iterate | Prototype → validated → convert to functional |

#### Architecture for a Functional Single-File App

```html
<!DOCTYPE html>
<html lang="es" data-theme="light">
<head>
  <!-- Design system via CSS custom properties with dark mode -->
  <!-- Font-size accessibility (4 levels: small/medium/large/xlarge) -->
  <!-- Viewport, no external dependencies -->
</head>
<body>
  <!-- Sticky top-bar with logo + controls (theme toggle, font toggle) -->
  <!-- Section-based screens: welcome → quiz → results -->
  <!-- Toast container for notifications -->
</body>
</html>
```

**Required components for a functional app:**
1. **Design System** — CSS custom properties on `:root` + `[data-theme="dark"]`, covering: bg, bg-card, text, text-secondary, border, primary, primary-hover, primary-light, primary-glow, success/warning/danger/info + their light variants, `--radius-*`, `--transition`, `--shadow-*`, `--font-size` (scalable via `html { font-size: var(--font-size) }`)
2. **Question Bank** — 60+ items array, each with: id, skill (grammar/vocab/reading/listening), diff (1-5 CEFR), text, ctx, options[], correct (index)
3. **Adaptive Selection Algorithm** — distribute questions evenly across 4 skills, sort by difficulty progressive, interleave within blocks
4. **Quiz Engine** — lifecycle: render → select option (immediate feedback: correct/wrong highlight) → lock → next → results
5. **Results Dashboard** — score circle (SVG circumference animation), CEFR level with avg difficulty weighting, skill breakdown bars, personalized recommendations, next-steps roadmap
6. **Mode Selector** — 20/40/60 question modes with time estimates
7. **Theme persistence** — localStorage for data-theme and data-font
8. **Zero external dependencies** — no libraries, no frameworks, no CDN

#### Dual-Version Pattern: V1 Professional + V2 Disruptive

When the user asks for a second "más innovadora y disruptiva" version:

| Aspect | V1 (Professional) | V2 (Disruptive) |
|--------|-------------------|-----------------|
| **Design** | Clean, minimal, card-based, proven UX patterns | Experimental layouts, particle backgrounds, unconventional components |
| **Quiz UX** | Standard progress bar + option cards | Accelerometer dots (per-question colored indicators), card-in animations, difficulty badges |
| **Results** | Score circle + skill grid + rec list | Profile card with gradient level circle, skill radar bars, diagnosis cards with border-color per skill, numbered roadmap |
| **Visual hook** | Clean professional | Ambient particles, glow effects, gradient text, pulse dots |
| **Naming** | Descriptive ("EnglishLevel") | Evocative/branded ("FluentScan") |
| **Tone** | "Evaluación de Inglés para Hispanohablantes" | "Evaluación Neurolingüística" |
| **Flow** | Same question bank, same logic | Same question bank, same logic, different UX layer |

**Rule:** V2 uses the same question bank and engine — only the UX layer (CSS, animations, layout, transitions) changes. This makes the comparison fair and the effort proportional.

#### Browser-Based Audit (Post-Creation)

After writing both HTML files, verify them in a real browser:

```javascript
// 1. Navigate and click through
browser_navigate(url)
browser_click(selector)  // Start button

// 2. Check for JS errors
browser_console()  // Read console output — any error messages?

// 3. Verify all critical functions exist
// In browser console, run:
`(function audit() {
  let errors = [];
  if (typeof startQuiz !== 'function') errors.push('startQuiz missing');
  if (typeof renderQuestion !== 'function') errors.push('renderQuestion missing');
  // ... etc
  return errors.length ? errors.join(', ') : 'ALL OK';
})()`

// 4. Test theme toggle
browser_click(themeButton)
browser_console({expression: "document.documentElement.getAttribute('data-theme')"})
// Expect: "dark" or "light"

// 5. Verify question bank size
browser_console({expression: "QUESTION_BANK.length"})
// Expect: >= 60

// 6. Test quiz flow: pick answer → next → results
browser_click(optionRef)
browser_click(nextRef)
// Repeat several times, check results screen loads
```

**Minimum passing criteria:**
- No console errors (ReferenceError, TypeError, undefined)
- All navigation flows work (welcome → quiz → results → reset)
- Theme toggle persists across page reload
- Font size toggle changes scale
- All 3 question-length modes work (20/40/60)
- At least one answer selected shows correct/wrong feedback
- Results screen renders with score, skills, recommendations

### Phase 6: Save & Report

Save files in the project folder:

```
<project-folder>/INFORME_CONSOLIDADO.md
```

**For visual prototypes (Phase 5a):**
```
<project-folder>/preview-app.html
```

**For functional apps (Phase 5b):**
```
<project-folder>/index.html              (V1 — professional)
<project-folder>/index-v2-<brand>.html   (V2 — disruptive, if requested)
```

Report to the user:
```markdown
✅ Archivos generados:

1. **INFORME_CONSOLIDADO.md** (XX KB) — X secciones: <sections>

2. **index.html** (XX KB) — V1: Evaluación completa con X preguntas
   → Modos: 20/40/60 preguntas · Dark/light mode · Font size adjustable
   → Abrir con: <browser> <absolute-path>

3. **index-v2-<brand>.html** (XX KB) — V2: Versión disruptiva con <UX innovations>
   → Mismo banco de preguntas, experiencia radicalmente diferente
```

If only the research document was requested (no Phase 5), report just the INFORME path.

## Pitfalls

1. **MCP search fails with 403 — provider priority mismatch** — The kindly-web-search server selects Serper before Tavily, but Serper commonly has 0 credits. Run the pre-flight check first. If you discover the 403 mid-session, fall back to native `web_search()` immediately. Fix permanently with the recipe in `references/mcp-search-provider-fix.md`.

2. **Auxiliary provider `google_ai_studio` breaks web_extract** — If `web_extract` fails silently during Phase 3, check `hermes config get auxiliary.web_extract.provider`. Fix: `hermes config set auxiliary.web_extract.provider auto`. Always use `hermes config set`, never direct yaml edits.

3. **`hermes config set` is the only way to change config** — Direct `patch` to `~/.hermes/config.yaml` is blocked by a safety guard. Discover this BEFORE trying to edit it, not after.

4. **Don't synthesize opinions as facts** — Keep clear separation between researched evidence, community consensus, and your own analysis. Label each.

5. **Distinguish Phase 5a (visual prototype) from Phase 5b (functional app)** — Visual prototypes are static UI mockups. Functional apps have a real JS engine: question banks, scoring, state management, localStorage. Don't add functional logic to a prototype (bloated, misleading). Don't make a functional app look half-baked (needs full polish: dark mode, font size, loading states, edge cases).

6. **Don't produce visual prototypes the user didn't ask for** — Only use Phase 5a when the task involves "preview", "prototipo", "interfaz", "UI". For "app", "quiz", "test", "herramienta" signals, jump directly to Phase 5b. For pure research tasks, the MD document alone is sufficient.

7. **Always include all 3 question-count modes (20/40/60)** — The user expects flexibility. Hardcode 40 as default. The selector is part of the welcome screen, not a settings panel.

8. **The dual-version pattern produces 2 INDEPENDENT HTML files** — Do NOT combine V1 and V2 into one file with tabs. They are separate UX experiments. Name them `index.html` (V1) and `index-v2-<brand>.html` (V2). Both must be fully functional standalone files.

9. **Browser-verify each version independently** — Navigate to each file, click through the full flow, check console for errors. A function that works in V1 may be renamed/missing in V2 (different codebases).

10. **Parallel reads and searches first, sequential writes second** — Read and research calls should be batched in the same turn. Writes (document + HTML) happen after all research is complete.

11. **Character limits on research files** — Large source files may truncate at 500 lines. Use `offset=N` to paginate through long files. Missing context = bad synthesis.

12. **No user-visible compilation/rendering** — Don't suggest the user needs a special viewer or build step for the HTML. It's self-contained and opens in any browser.

13. **The INFORME should stand alone** — Don't "see preview-app.html for details" in the document. Each artifact should be independently useful.

14. **Reddit/forums block automated access** — Reddit, Hacker News, and many forums have aggressive anti-bot protection. `web_extract` of Reddit URLs will return a "blocked by network security" page. Alternative approaches:
    - Search for syndicated/cached versions (Reddit posts are often mirrored on reveddit.com, unddit.com, or Google cache)
    - Use MCP `get_content` on known-working Reddit mirrors
    - Hacker News content is accessible via `news.ycombinator.com/item?id=N` — extract works for the original article + top comments
    - Search for blog summaries of Reddit/HN threads instead
    - When specific forum sentiment is important, note the limitation in your report rather than fabricating data

15. **No Phase 5 for pure research** — When the task is "read + research + report" (no mockup or prototype requested), stop after Phase 6. Do not build HTML previews or functional apps unless the user explicitly asked for a visual/concept prototype.

## References

- `references/multi-vector-gap-analysis-sdd-2026.md` — Real-world example: multi-vector gap analysis on SDD/agentic engineering documents. Shows the full research pipeline: gap identification → 5-axis parallel search → two-wave strategy → deep dives → gap-analysis report with priority recommendations. Use as a template for similar "review this folder" tasks.
- `references/inglés-hispanohablantes-research.md` — Real-world example: research on English learning for Spanish speakers, covering pedagogical frameworks (EPI/MARS-EARS, neuroeducation), error-specific analysis, benchmarking, and solution architecture.
- `references/mcp-search-provider-fix.md` — Exact patch recipe for kindly-web-search: wrapper exports both SERPER + TAVILY keys, server code swaps provider priority to use Tavily (with credits) over Serper (0 credits). Includes restart and verification steps.
