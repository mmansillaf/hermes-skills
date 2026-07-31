---
name: rag-prompt-engineering
category: mlops
tags: [rag, prompt-engineering, retrieval-augmented-generation, llm-patterns, testing]
description: |
  Patterns for designing, optimizing, and testing prompts for RAG (Retrieval-Augmented Generation) systems.
  Covers conditional branching (relevant vs. irrelevant context), mandatory citation rules, negative-case
  handling, and systematic evaluation methodology. Domain-agnostic but includes legal-domain examples.
triggers:
  - User asks to improve RAG response quality, reduce hallucination, or handle "no data found" cases
  - User reports RAG responses are too verbose, repetitive, or useless when context is off-topic
  - Building or debugging a RAG system prompt for the first time
  - User shows a model output that is bloated, hallucinates, or ignores retrieved context
  - Evaluating RAG quality across both positive (found) and negative (not found) queries
usage: |
  Load this skill when designing, reviewing, or debugging a RAG system's prompt template.
  The skill provides reusable patterns, not a specific code snippet.
---

# RAG Prompt Engineering Patterns

## Core Problem

RAG systems face a fundamental tension: the prompt template must work well for **two diametrically opposed scenarios**:

| Scenario | What happens | Risk |
|----------|-------------|------|
| **A — Relevant context found** | Model has good docs to analyze | Bloated structure hides insight |
| **B — No relevant context found** | Model has irrelevant or off-topic docs | Bloat + repetition + useless output |

A single fixed structure (e.g. "always use Síntesis → Análisis → Conclusión") **always fails in one of the two scenarios**. It forces the model to pad negative cases with meaningless repetition.

## Pattern: Conditional Branching

**Instead of one structure, give the model two — and let it decide which to use.**

```
PRIMERO, determina si los documentos recuperados guardan RELACION DIRECTA
con la pregunta del usuario o no.

--- ESCENARIO A: DOCUMENTOS RELEVANTES ---
[Rich analytical structure: Synthesis → Evidence → Graph → Conclusion]

--- ESCENARIO B: DOCUMENTOS NO RELEVANTES O INEXISTENTES ---
[Concise structure: Declaration → What was found → Why it doesn't match]
```

### Key design rules:

1. **The decision is the model's job** — don't pre-classify in code. The LLM is better at deciding relevance than keyword heuristics.

2. **Both scenarios get clear, separate instructions** — not a fallback. Scenario B should feel like a *different template*, not an afterthought.

3. **Scenario B must enforce conciseness explicitly** — add "respond in max 3-4 paragraphs. Do not artificially lengthen" to prevent bloat.

## Pattern: Mandatory Citation Rules

The model will **not** cite the most important content unless you force it.

```python
# Base rule — cite the key field
"Es OBLIGATORIO citar o parafrasear [THE KEY FIELD] de CADA documento
que menciones. Usa el formato: \"[Doc: ID] -- [FIELD]: \\\"texto\\\"\""

# Source path rule — force inclusion of file reference
"NUNCA cites un documento sin su `📄 FUENTE: Jurisprudencia/XXXXX.html` al final."
```

### The Source Path Omission Problem

Even when the context includes the source file path for every chunk, the LLM will sometimes drop it from citations. The model sees:

```
**EXP. N° 05591-2016** | Tribunal Constitucional | Jueces: Blume Fortini
Jurisprudencia/440426.html
{chunk text}
```

But produces: `**EXP. N° 05591-2016** (TC, Jueces: Blume...)` — **omitting the .html path.**

### Fix: Three-Layer Defense

| Layer | What | Where | Impact |
|-------|------|-------|--------|
| 1 — **Format marker** | Prefix source paths with `📄 FUENTE:` instead of bare path | `hybrid_search.py` context builder | Makes path visually distinct and semantically marked as a required field |
| 2 — **Emphatic prompt** | "NUNCA cites sin su `📄 FUENTE:`. Respuesta INVÁLIDA si se omite." | `synthesizer.py` system prompt | Escalates from suggestion to requirement |
| 3 — **Example in prompt** | Show correct citation WITH the `📄 FUENTE:` line as part of the example | `synthesizer.py` system prompt | Gives the LLM a concrete template to copy |

**Before (context format):**
```
**EXP. N° 05591-2016** | Tribunal Constitucional
Jurisprudencia/440426.html
```

**After (context format):**
```
**EXP. N° 05591-2016** | Tribunal Constitucional
📄 FUENTE: Jurisprudencia/440426.html
```

**Verified result:** 15-query battery went from ~25% citation completeness (1 of 4 citations had source path) to 100% (all citations include `📄 FUENTE:`).

Without this rule, models often summarize abstractly rather than quoting the concrete data the RAG system went to the trouble of retrieving.

### When to use:
- **Legal RAG** → mandate the "fallo" (ruling/judgment)
- **Medical RAG** → mandate the "diagnosis" or "treatment"
- **Financial RAG** → mandate the "figure", "ratio", or "date"
- **Academic RAG** → mandate the "finding" or "conclusion"

### Pitfall: LLM Invents Doc IDs Instead of Using Real Ones

Even when the context explicitly prefixes each document with `[Doc: real_id]`, the LLM may **ignore these real IDs and invent its own**. Example:

```
Context provided:
  [Doc: 552066] HECHOS: El caso se refiere a...

LLM response:
  "...según lo dispuesto en el [Doc: TC-001]"  ← TC-001 does not exist!
```

**Why it happens:** The `[Doc: id_documento]` instruction in the prompt acts as a *template placeholder* — the LLM treats "id_documento" as a slot to fill with a plausible-looking ID rather than a directive to copy from the context.

**Symptoms:**
- Grounding score is high (e.g. 0.89) because the response has many `[Doc: X]` citations
- But 0/16 citations are valid because none match a real doc_id
- `verify_response_grounding()` correctly flags them all as invalid
- `fully_grounded` remains False despite high score

**Fix — Three-Part Instruction:**

```python
# Part 1: Explicit prohibition
"CRÍTICO: SOLO puedes usar IDs que YA APARECEN en el contexto proporcionado "
"(ej: [Doc: 552066] o [Doc: 437043.html]). "
"NUNCA inventes ni generes IDs nuevos como \"TC-001\", \"Doc-1\" o similares."

# Part 2: Exact match requirement
"Cada [Doc: X] en tu respuesta debe coincidir EXACTAMENTE con un ID "
"que aparece en los fragmentos del CONTEXTO RECUPERADO."

# Part 3: Multi-source format (if needed)
"Si integras varias fuentes: \"[Doc: id1; Doc: id2]\""
```

**Key difference from basic citation instructions:** The prohibition is framed as a **restriction** ("SOLO puedes usar IDs que YA APARECEN") not a suggestion ("debe estar respaldada por el ID"). The word "NUNCA" plus concrete examples of bad IDs (`TC-001`, `Doc-1`) gives the LLM a clear negative pattern to avoid.

### When to check for this pitfall:
- Your grounding verification shows high score but 0% valid citations
- The LLM produces IDs that look plausible but don't exist in your index
- You're using a format like `[Doc: id]` without explicit copy-from-context rules
- The verification function compares against `doc_ids` from retrieval and finds no matches

## Pattern: Negative-Case Transparency

When the model finds no relevant documents, the single worst thing it can do is **say nothing useful**. A good negative-case response has exactly three elements:

```
1. Declaracion clara: "No se encontro [topic] en el corpus."
2. Documentos recuperados: lista los IDs con su [KEY FIELD],
   aunque traten materia distinta.
3. Explicacion: que materia tratan y por que no responden
   a la pregunta.
```

This gives the user:
- **Visibility** into what WAS found (even if off-topic)
- **The actual data** to judge for themselves
- **Transparency** — no suspicion that the system is hiding bad results

## Testing Methodology

Always test **both scenarios** before shipping a RAG prompt change:

| Test type | Query choice | Goal |
|-----------|-------------|------|
| A — Relevant | Use a query known to match corpus documents | Verify rich structure works |
| A — Different relevant query | Use a different query that also matches | Verify consistency, not luck |
| B — No match | Use a query for a topic not in the corpus | Verify concise negative case |
| B — Partial match | Use a query similar but not matching found docs | Verify model doesn't force relevance |

### HyDE Query Overspecification Trap

When the query router generates a HyDE (Hypothetical Document Embeddings) expansion, restrictive modifiers can kill retrieval even when the base topic is well-covered in the corpus.

**How it manifests:**
- Query: `"indemnización por despido arbitrario en la administración pública"` → Escenario B (no data found)
- Same base query without modifier: `"indemnización por despido arbitrario"` → Escenario A (good matches)

**Why:** The FAISS/BM25 hybrid search embeds the full HyDE query including modifiers. "Administración pública" acts as a semantic filter that narrows similarity scores below the retrieval threshold, even when the underlying legal concept (despido arbitrario) is well-represented.

**Mitigation strategies:**

| Strategy | When to use | Trade-off |
|----------|-------------|-----------|
| **Strip modifiers in HyDE** — Generate 2 versions (with and without restrictive qualifiers) and merge results via RRF | Routinely | +2× embedding calls, but better recall |
| **Multi-stage retrieval** — First pass without modifiers, second pass filters by entity match | High-precision needs | More complex pipeline |
| **Chunk-level dedup after broad retrieval** — Retrieve top-K*3, then filter by entity match on the doc level | Simple, no extra API calls | Higher latency (more docs to embed) |

**Checklist for diagnosis:**
- [ ] Does the query contain a restrictive qualifier? (e.g., "en la administración pública", "en municipalidades", "del sector privado")
- [ ] Does the same query without the qualifier retrieve relevant documents?
- [ ] If yes → the HyDE expansion is over-specifying. Apply mitigation.

### Semantic Density Testing

Some concepts are well-represented in the corpus, some barely exist at all. Track coverage density as a project metric:

```python
QUERIES = [("P01", "query text"), ...]
for qid, query in QUERIES:
    t0 = time.time()
    await run_query(query)  # imports from the live pipeline
    elapsed = time.time() - t0
    # capture stdout, strip logs, write to file
    log.write(f"CONSULTA [{qid}]: {query}  TIEMPO: {elapsed:.1f}s\n{response}\n\n")
```

The output file becomes a regression artifact — re-run the same script after code changes to compare responses.

### Evaluation criteria:
- **Fallo/field citation**: Does every document mentioned include the mandated field?
- **Conciseness in B**: Is the negative response truly shorter, or does it pad?
- **Hallucination check**: Does the model ever claim relevance for off-topic docs?
- **Graph/relationship use**: When context includes relationships, does the model use them?

## Pattern: Tone Correction for Legal RAG

### Problem

Legal domain prompts often say "Actúa como un Magistrado de la Corte Suprema" or "Actúa como un Juez". This causes the LLM to impersonate the court, producing embarrassing headers:

```
**MAGISTRADO PONENTE: [No identificado]**
**CORTE SUPREMA DE JUSTICIA — SALA LABORAL**
**Lima, [Fecha de emisión del presente dictamen]**
```

The `[No identificado]` and `[Fecha de emisión]` placeholders look unprofessional because the LLM is trying to write a court document template but lacks the specific data.

### Fix

Two changes:

1. **Change the role** from impersonator to analyst:
   - Before: `"Actúa como un Magistrado de la Corte Suprema"`
   - After: `"Actúa como un Analista Jurídico y Asesor Legal experto"`

2. **Explicitly ban impersonation artifacts:**
   ```
   IMPORTANTE: NO escribas encabezados como "MAGISTRADO PONENTE",
   "CORTE SUPREMA", "Lima, [Fecha]" ni firmes como si fueras un tribunal
   emitiendo una resolución. No te hagas pasar por un juez. Eres un analista
   jurídico dando su opinión fundada en la jurisprudencia recuperada.
   ```

### Working example

```python
prompt = f"""Actúa como un Analista Jurídico y Asesor Legal experto en derecho peruano.
Responde a la siguiente consulta jurídica basándote ÚNICA y EXCLUSIVAMENTE
en el contexto recuperado.

CONTEXTO RECUPERADO:
{contexto_raw}

PREGUNTA: {query}

INSTRUCCIONES:
...
4. TONO Y ESTRUCTURA: Adopta un tono profesional, conversacional y didáctico,
   como un abogado asesorando a un colega.
   IMPORTANTE: NO escribas encabezados como "MAGISTRADO PONENTE",
   "CORTE SUPREMA", "Lima, [Fecha]" ni firmes como si fueras un tribunal
   emitiendo una resolución.
"""
```

### When to apply

- Any RAG system where the prompt assigns a judicial role to the LLM
- Particularly important for legal, regulatory, or compliance domains
- Also relevant for any domain where impersonation of an authority figure creates trust issues (medical, financial advising, journalism)

## Pattern: Chat-Style Concision for RAG Responses

### Problem

Legal RAG prompts often produce long, multi-section responses (Síntesis Resolutiva + Análisis de Evidencias + Nexo Jurisprudencial + Conclusiones) that are 3000-4000 characters. Users who want quick answers find this verbose — they prefer "1-2 paragraphs with the gist of the answer" rather than a formal dictamen.

### The Fix

Replace the multi-section structure with a single concise block. No section headers, no formal structure — just a direct answer in 1-2 conversational paragraphs with inline citations.

```python
prompt = f"""Eres un Analista Jurídico experto en derecho peruano.
Responde a la consulta del usuario en 1-2 párrafos, como si fueras
un abogado respondiendo en un chat.

CONTEXTO:
{contexto}

CONSULTA: {query}

INSTRUCCIONES:
1. Responde DIRECTAMENTE a la consulta en 1-2 párrafos.
2. Integra las citas naturalmente en el texto: "según el [Doc: ID]"
3. NO uses secciones ni encabezados (ni "Síntesis Resolutiva",
   ni "Análisis", ni "Nexo Jurisprudencial", ni "Conclusiones").
4. Cada afirmación debe tener su cita correspondiente.
5. Si el contexto no es suficiente, dilo claramente:
   qué encontraste vs qué falta para responder completamente."""
```

### Key differences from the verbose approach

| Aspect | Verbose (before) | Concise (after) |
|--------|-----------------|-----------------|
| Sections | 4 required sections | None — single block |
| Length | 3000-4000 chars | 800-1500 chars |
| Citations | In separate "Análisis" section | Inline within the response |
| Format | Formal dictamen | Chat-style conversation |
| User perception | Overwhelming, overly formal | Quick, actionable |

### When to use each format

| Situation | Use | Reason |
|-----------|-----|--------|
| Interactive chat / messaging | **Concise** | Users want fast answers, not documents |
| Formal report generation | **Verbose** | Output IS the deliverable document |
| Legal advice to clients | **Concise** | Information density without formality |
| Court filings / memos | **Verbose** | Structure is part of the professional output |
| Quick reference / lookup | **Concise** | Answer the question, stop |

### Signal: when to switch to concise

- User says "es muy largo" / "eres muy verboso"
- User explicitly asks for "1-2 párrafos" or "respuesta tipo chat"
- User says "como serian en el chat" (expects chat-style delivery, not formal documents)
- The delivery channel is messaging (Telegram, WhatsApp, SMS) rather than a document generator
- The query is a simple factual lookup, not a complex multi-arista analysis

### Pitfall: broken Python multi-line string concatenation

When a system prompt is composed of Python adjacent string literals:

```python
"Eres un asistente... Usas 1-2 parrafos maximo..."
"documental proporcionado. Cada afirmación..."
"del cual fue extraída..."
"jurista experimentado dirigiéndose a sus pares."
```

Python **silently concatenates** these into a single string at parse time. If one fragment is stale, leftover from a previous refactor, or missing a leading space, the prompt becomes:

`"...conciso.documental proporcionado..."` — the model sees a single garbled instruction with no syntactic break.

**How it happens:**
1. Original prompt had a long string on one line
2. Someone reformatted to N-char line width, splitting across adjacent `"..."` literals
3. A middle fragment got partially edited but the adjacent fragment wasn't updated
4. The edit left a broken transition invisible in a quick grep

**Detection:**
```bash
# Find multi-line string concatenation in prompt files
grep -n '".*"' synthesis.py | grep '^\s*"' | head -20
```
Better: dump the actual compiled string before sending to the LLM:
```python
system_prompt = (
    "Eres un asistente..."
    "documental proporcionado..."
)
print(repr(system_prompt))  # Check for missing spaces, broken fragments
```

The key symptom: the prompt *looks* correct line-by-line, but the concatenated output is garbled because one fragment doesn't start with a space or has orphan text.

**Fix:** Always write multi-line system prompts with explicit `+` or f-string interpolation, never relying on implicit Python string concatenation for critical prompt text:

```python
# BAD — vulnerable to silent breakage
prompt = (
    "Eres un asistente..."
    "documental proporcionado..."
)

# GOOD — each line is independent
prompt = "Eres un asistente..." + \
         "documental proporcionado..."
```

Or use a single long string — Python doesn't care about 80-char width in prompt code.

### Verification: forbidden-pattern post-check

After changing a RAG prompt (tone, structure, concision rules), don't just trust the model will comply. Verify explicitly:

```python
forbidden = [
    '**sintesis', '**analisis', '**conclusion',
    'sintesis resolutiva', 'analisis de evidencias',
    'nexo jurisprudencial'
]
found = [t for t in forbidden if t in response.lower()]
if found:
    print(f"WARNING: forbidden patterns still present: {found}")
```

**Procedure:**
1. Apply the prompt change (both system + user prompt layers)
2. Clear ALL caches (`rm -rf cache/* datos/query_cache/*.json`)
3. Restart the service
4. Run a **fresh** query (must take >5s — if <1s, it's cached and using the old prompt)
5. Check the response length (should be 800-1500 chars, not 3000-4000)
6. Check for forbidden title/section patterns
7. If forbidden patterns found: the system prompt role is overriding again, or the change wasn't saved

### Critical Pitfall: System Prompt Role Overrides User-Prompt Format

**The most common reason concise instructions fail:** the system prompt assigns a role that
contradicts conciseness, and the system prompt ALWAYS wins.

| Prompt layer | Text | Effect |
|-------------|------|--------|
| **System** (role) | `"Eres un Magistrado de la Corte Suprema... emitir dictámenes técnico-jurídicos con el rigor, la estructura y el lenguaje propios de la judicatura peruana"` | LLM produces 3000-4000 char formal dictamen with 4 sections |
| **User** (instruction) | `"RESPONDE EN 1-2 PÁRRAFOS: estilo conversacional tipo chat"` | **Ignored** — the system role overrides it |

**Why:** The system message sets the LLM's *identity* ("quién eres"), which controls tone,
length, and structure at a deeper level than the user message. A "Magistrado de la Corte
Suprema" naturally writes long formal documents regardless of what the user prompt says.

**Fix — both layers must align:**

```python
# System prompt — must match the desired conciseness
"Eres un asistente legal experto en derecho peruano. Respondes consultas juridicas "
"de forma directa y conversacional, como un abogado explicando a un colega. "
"Usas 1-2 parrafos maximo, citando cada afirmacion con [Doc: ID_REAL]. "
"Tu tono es profesional pero conciso."

# User prompt — reinforces, doesn't introduce new role
"Responde en 1-2 párrafos. No uses secciones ni encabezados. "
"Cada afirmación con su cita."
```

**Verification:** After changing the prompt, clear ALL caches (`rm -rf cache/*
datos/query_cache/*.json`) and run a fresh query (must take >5s, not <1s)
to confirm the new prompt took effect. Old cached responses with the verbose
format will persist indefinitely otherwise.

## Pattern: Grounding Feedback Loop

### Problem

Even with good citation instructions (see "Pattern: Mandatory Citation Rules"), the LLM sometimes generates sentences without backing citations. The response is factually correct but unverifiable per-sentence, producing grounding scores below 0.8.

The root cause is **instruction placement** — in a long prompt, the citation rule is just one of many instructions. The LLM treats it as a suggestion, not a hard constraint.

### Solution: Auto-Regenerate on Low Grounding

After generating the first response, run the grounding verifier. If score < 0.8, re-generate with a STRONGER instruction:

```python
def generate_with_feedback(query, context, doc_ids, max_attempts=2):
    for attempt in range(max_attempts):
        response = call_llm(prompt, attempt=attempt)
        grounding = verify_response_grounding(response, doc_ids)
        
        if grounding["grounding_score"] >= 0.8:
            return response, grounding
        
        # On low grounding, add stricter instruction for retry
        if attempt == 0:
            prompt += """
⚠️ REINSTRUCCIÓN: Tu respuesta anterior tuvo citas insuficientes.
CADA oración que exprese un hecho jurídico DEBE terminar con [Doc: ID].
Si escribes 2 oraciones seguidas sin una cita, la respuesta es inválida.
No uses secciones, solo responde en 1-2 párrafos con cada afirmación citada."""
    
    return response, grounding  # Return best effort
```

### Design Rules

1. **Max 2 attempts** — beyond this, latency penalty outweighs quality gain. Each retry doubles LLM time (5s → 10s).
2. **Grounding threshold at 0.8** — below this, response isn't verifiable per-sentence (too many unsupported claims).
3. **The feedback instruction must be STRONGER** on retry, not identical — escalate from suggestion to requirement. Use "REINSTRUCCIÓN" or "ADVERTENCIA" as a visual signal.
4. **Log both attempts** — track how often the feedback loop fires. If it fires >20% of the time, fix the base prompt instead.
5. **Consider model speed** — on slow models (Mixtral, full-size Llama), this doubles latency noticeably. Limit to 1 retry or skip on slow providers.
6. **Keep concision in the retry** — if the user wants 1-2 paragraph chat style, enforce it again in the retry instruction. A verbose retry with better citations still fails the user's format preference.

### Metrics to track

| Metric | What it tells you | Action if bad |
|--------|------------------|---------------|
| % of queries needing retry | Base prompt weakness | Improve citation rules in main prompt |
| Average grounding score after retry | Feedback loop effectiveness | If still < 0.8, deeper issue |
| Average latency per query | Cost of feedback loop | Reduce max_attempts or switch to faster model |
| Valid vs invalid citations on retry | LLM compliance with Doc IDs | Check if real IDs are in context (invented IDs count as invalid) |

## Pattern: Tone Adaptation for Educational/Teen RAG

### The Problem

Educational RAG systems for teen audiences (12-17) face a **polarity problem**:

| Approach | Result | Why it fails |
|----------|--------|-------------|
| "Actúa como un profesor" | Boring, feels like homework | Teens disengage from lecture tone |
| "Actúa como un amigo" | Unprofessional, may feel fake | Slang overdose feels patronising |
| "Actúa como un historiador" | Too formal, loses teen interest | Walls of text with no hook |

A generic formal tone produces responses that look like Wikipedia articles — correct but **unreadable** for the target audience. The teen brain filters out anything that sounds like a textbook.

### The Fix: Three-Layer Tone Stack

Layer 1 — **Role framing** (not impersonation, not professor):
```
Eres un asistente educativo que enseña historia a adolescentes (12-17 años).
Habla como un amigo mayor que sabe del tema, no como profesor aburrido.
NO te hagas pasar por historiador, juez, ni ninguna autoridad.
```

Layer 2 — **Language guardrails** (not too formal, not cringe):
```
REGLAS DE LENGUAJE:
- Usa lenguaje formal pero con chispa: "papa", "chévere", "datazo"
- Incluye 1 dato curioso por respuesta ("¿Sabías que...?")
- Referencias a cultura que les suene: TikTok, Minecraft, Fortnite, anime
- NO inventes datos. Si no hay info en el corpus, dilo honesto
```

Layer 3 — **Response structure** (scannable, visual):
```
ESTRUCTURA DE RESPUESTA:
1. Título con emoji — ⚔️ 📖 🎨 👤 según el tema
2. Respuesta directa: 2-3 párrafos cortos (no más de 4-5 líneas cada uno)
3. Un "dato freak" destacado visualmente: "🎨 ¿Sabías que..."
4. Fuentes o contexto al final si aplica
```

### Working Example

```python
SYSTEM_PROMPT = """Eres "Historia Encantada", un asistente peruano que enseña historia 
y literatura a adolescentes (12-17 años).

REGLAS DE TONO:
1. Habla como un amigo mayor que sabe del tema, no como profesor aburrido
2. Usa lenguaje formal pero con chispa: "papa", "chévere", "datazo"
3. Incluye 1 dato curioso por respuesta
4. Referencias a cosas que les suenen: TikTok, Minecraft, Fortnite, anime
5. NO inventes datos históricos. Si no hay info en el corpus, dilo honesto

ESTRUCTURA DE RESPUESTA:
1. Título con emoji
2. Respuesta directa (2-3 párrafos)
3. Dato curioso: "🎨 Dato freak:" o "💡 ¿Sabías que..."
4. Fuentes usadas al final

CONTEXTO RECUPERADO:
{contexto}

PREGUNTA: {query}

Responde en máximo 4 párrafos. Sé conciso pero entretenido."""
```

### When to apply

- Any RAG system targeting teens or young adults
- Educational content (history, literature, science for K-12)
- Gamified learning, quiz bots, interactive storytelling
- NOT for adult/professional education (university, corporate training)

### Signal: Overcorrection

If the teen response comes out as **too informal** (slang-heavy, meme-stuffed, feels fake), tighten the language guardrails by adding:

```
IMPORTANTE: No exageres con el slang. No uses "XD", "lol", ni emojis excesivos.
Sé natural — como un hermano mayor conversando, no como un adulto 
intentando sonar "cool".
```

The sweet spot is **formal vocabulary + casual delivery** — like a well-written magazine for teens, not a group chat.

## Pattern: RAG with Visual Output (Image + Animation)

### The Problem

A standard RAG pipeline outputs text-only responses. For educational/teen audiences, text-only is the lowest-engagement format. Adding a generated image or short animation to each response drastically improves retention and enjoyment — but introduces latency, cost, and integration complexity.

### Architecture Pattern

```
RAG text response ──→ extract subject/topic
                          │
                          ▼
                   Select visual style
                   (sketch, crayon, pixel_8bit, acuarela)
                          │
                          ▼
                   Image generation API
                   (Gemini 2.5 Flash Image → Together AI → Placeholder)
                          │
                          ▼
                   Animation (optional)
                   (Ken Burns always → Parallax/Breathing → SVD if GPU)
                          │
                          ▼
                   Compose: text + image + GIF/MP4
```

### Provider Fallback Chain (No GPU)

When the host has no ML-capable GPU, use this priority:

| Tier | Provider | Model | Cost/img | Notes |
|------|----------|-------|----------|-------|
| 1 (primary) | Gemini API | gemini-2.5-flash-image | Free tier (quota-limited) | Best quality, natural language prompts, pixel art native |
| 2 | Together AI | Dreamshaper / SDXL | $0.0006-$0.0019 | Reliable, cheap, LoRA support |
| 3 | Replicate | FLUX Schnell | $0.003 | Premium fallback |
| 4 (local) | PIL placeholder | N/A | $0 | Text-on-image placeholder when all APIs fail |

### Pixel Art for Teen Appeal

Teens respond strongly to retro/pixel aesthetics (Stardew Valley, Minecraft, indie games). Add two dedicated styles:

```
"pixel_8bit": {
    prompt: "8-bit pixel art, retro NES game, limited color palette, 
             blocky 8x8 pixels, cute, no shading, {scene}",
    best_for: "simple concepts, characters, icons"
}
"pixel_16bit": {
    prompt: "16-bit pixel art, Super Nintendo aesthetic, vibrant colors, 
             detailed pixel art, retro game style, {scene}",  
    best_for: "scenes, landscapes, detailed illustrations"
}
```

These pixel styles are **forgiving of lower quality** (the output is supposed to look lo-fi) and run well on any API.

### Hardware Detection Pattern

Before deciding on local vs API image generation, probe the environment:

```python
import torch

def has_usable_gpu():
    if not torch.cuda.is_available():
        return False, "No CUDA"
    cc = torch.cuda.get_device_properties(0).major * 10 + \
         torch.cuda.get_device_properties(0).minor
    if cc < 75:  # PyTorch modern requires CC >= 7.5
        return False, f"GPU CC {cc/10} too old for PyTorch"
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    if vram < 6:
        return False, f"Only {vram:.1f}GB VRAM (need 6GB+ for SD)"
    return True, f"GPU OK: CC {cc/10}, {vram:.1f}GB VRAM"
```

Key reality: NVIDIA GeForce 940MX (CC 5.0, 2GB VRAM) is **not usable** for any diffusion model even though CUDA reports available. Always check CC before attempting local inference.

### Text Chunking for Narrative (Not Legal)

Educational/narrative content needs different chunking than legal or technical documents:

```python
def chunk_narrativo(texto, chunk_size=800, overlap=100):
    """Divide by paragraphs (semantic units), not by token count.
    Respects chapter/scene boundaries."""
    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    chunks = []
    actual = ""
    for p in parrafos:
        if len(actual) + len(p) > chunk_size and actual:
            chunks.append(actual.strip())
            # overlap from end of previous chunk
            words = actual.split()
            overlap_text = " ".join(words[-overlap//5:])
            actual = overlap_text + "\n\n" + p
        else:
            actual += "\n\n" + p if actual else p
    if actual:
        chunks.append(actual.strip())
    return chunks
```

| Aspect | Legal/Narrative chunking | Educational/Narrative chunking |
|--------|------------------------|--------------------------------|
| Unit | Token count | Paragraph / scene |
| Overlap | 10-15% fixed | ~12% semantic (last N words) |
| Metadata | Case number, judge, court | Characters, epoch, location, emotion |
| Retrieval mode | Semantic only | Semantic + chronological (for timelines) |

### When to apply

- Any RAG system targeting K-12 or teen audiences
- Systems integrating text + image output
- Projects running on laptops without ML-capable GPUs
- Educational storytelling, interactive history, literature companions

## Pattern: Graph Entity Precomputed Lookup for Context Headers

When a RAG system has a knowledge graph (NetworkX, Neo4j, etc.) with entity data (judges, parties, laws, diagnoses, products) that is separate from the text chunks, the LLM sees both in separate sections and may not connect them.

### The Problem

```
Hybrid context (text chunks):
  **CAS. N° XXXX** | Corte Suprema
  {chunk text about the case}

Graph context (entities):
  [1612215.html]
    FALLO: ...
    JUECES: Yrivarren Fallaque, Arévalo Vela
    PARTES: Edgardo Hernán Asenjo Tamay vs Poder Judicial
```

The LLM needs to mentally cross-reference: "this chunk is from doc 1612215.html → the graph says doc 1612215.html has juez X → I should mention juez X". This connection is fragile.

### The Fix: Precompute and Merge

Extract entities from the graph into a flat JSON lookup in one offline step, then inject them directly into each chunk's header at query time.

```python
# Step 1: One-time extraction from graph
G = pickle.load(open(GRAPH_PATH, 'rb'))
doc_entities = {}
for node, data in G.nodes(data=True):
    if data.get('tipo') != 'Documento':
        continue
    entry = {"jueces": [], "actores": [], "demandados": [], "leyes": []}
    for adj in G.neighbors(node):
        tipo = G.nodes[adj].get('tipo', '')
        if tipo == 'Juez':
            entry["jueces"].append(adj.replace("Juez: ", ""))
        elif tipo == 'Actor':
            entry["actores"].append(adj.replace("Actor: ", ""))
        elif tipo == 'Demandado':
            entry["demandados"].append(adj.replace("Demandado: ", ""))
        elif tipo == 'Ley':
            entry["leyes"].append(adj.replace("Ley: ", ""))
    doc_entities[node] = entry
json.dump(doc_entities, open("data/indices/doc_entities.json", 'w', encoding='utf-8'))
```

```python
# Step 2: Load at query time and enrich headers
_docs_entities = json.load(open("data/indices/doc_entities.json"))

def enrich_header(doc_id, ident, organo):
    ent = _docs_entities.get(doc_id, {})
    parts = [f"**{ident}**"]
    if organo:
        parts.append(f" | {organo}")
    ent_lines = []
    if ent.get("jueces"):
        ent_lines.append(f"Juez: {', '.join(ent['jueces'][:3])}")
    actor_str = ", ".join(ent.get("actores", []))
    dem_str = ", ".join(ent.get("demandados", []))
    if actor_str or dem_str:
        ent_lines.append(f"{actor_str} | vs {dem_str}")
    return "".join(parts), " | ".join(ent_lines)
```

### Result: every chunk carries its entities inline

```
**CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema - Sala Laboral
Juez: Yrivarren Fallaque, Arévalo Vela | Edgardo Hernán Asenjo Tamay | vs Poder Judicial
Jurisprudencia/1612215.html
{chunk text}
```

The LLM no longer has to cross-reference sections — everything is in one place.

### Performance

- 59,571 docs extracted from graph in 2.6 seconds
- 19.5 MB JSON, loaded once at startup
- Zero per-query overhead beyond a dict lookup

### When to use

- Your system has a knowledge graph (NetworkX, Neo4j, etc.) and a separate text index
- Entity data (judges, parties, products, diagnoses) is stored in the graph but text is separate
- The LLM is expected to cite entity information alongside document content
- The graph-to-doc mapping is static (doesn't change between queries)

## Pattern: Source-Level Document Identifier Enrichment

RAG systems often reference documents by internal IDs (filenames, hashes, database keys)
that are meaningless to end users. You can enrich responses with human-readable identifiers
**without reprocessing through the LLM** by extracting metadata directly from source files.

### The Approach

| Step | What | Cost |
|------|------|------|
| 1 | Parse source documents once (regex from HTML/PDF/XML headers) | Zero (no API) |
| 2 | Build a static mapping: internal_id → {identificador, source, date, topic} | Zero |
| 3 | Load mapping at RAG startup alongside the index | Memory only |
| 4 | At context-building time, inject the human-readable label | Inline |

### Implementation Sketch

```python
# Build mapping once (offline)
docs_metadata = {}  # filename -> {identificador, organo, fecha}
for html_file in glob("documents/*.html"):
    text = extract_header_text(html_file)
    docs_metadata[basename] = extract_identifiers_via_regex(text)

# Use at query time
def get_doc_label(doc_id):
    meta = docs_metadata.get(doc_id, {})
    if meta.get("identificador"):
        return f"{meta['identificador']} | {meta.get('organo', '')}"
    return doc_id  # fallback

# Inject into the prompt context
ctx += f" [{get_doc_label(doc_id)}] {chunk_text}"
```

### When This Fits

- Your source documents have structured headers (RTF numbers, case numbers, docket IDs, ISBNs)
- You cannot afford re-ingestion through an LLM (cost, time, rate limits)
- You want identifiers to appear in the context the LLM sees, not as a post-processing step
- The mapping is static (it only changes when source documents are added)

### When NOT to Use

- Source documents have no structured identifiers — you'd need the LLM to extract them
- The metadata changes frequently — the mapping becomes stale
- You need fuzzy matching or disambiguation — regex from headers is exact-match only

### File Extension Consistency Trap

When the RAG system's internal IDs include file extensions (`1612215.html`) but downstream code strips them inconsistently, the `get_doc_label()` mapping fails silently.

**Checklist:**
- [ ] Are FAISS metadata doc_ids consistent with the metadata JSON keys? (e.g., `"1612215.html"` vs `"1612215"`)
- [ ] Are graph node IDs the same format as FAISS doc_ids?
- [ ] If source files exist on disk, does their path match the ID? (e.g., `Jurisprudencia/1612215.html`)
- [ ] The key pattern must be **identical across all three stores** (FAISS metadata, NetworkX nodes, metadata_docs.json). A single `.html` suffix mismatch breaks the link chain.

If the formats differ, apply a normalization wrapper:

```python
def normalize_doc_id(raw_id):
    \"\"\"Strip .html if present, or add it — whichever makes all stores consistent.\"\"\"
    return raw_id.replace('.html', '')  # or raw_id + '.html'

# Use at every boundary:
label = get_doc_label(normalize_doc_id(meta['doc_id']))
```

## Pattern: Legal Document Linking

Once documents have human-readable identifiers in the response, the next step is making them **clickable** — so the user can open the full source document. The right approach depends on where the source files live and whether you want a server.

### Three Approaches

| Approach | Infrastructure | Link format | User experience | Best for |
|----------|---------------|-------------|-----------------|----------|
| **A — File paths** | None (files on disk) | `Jurisprudencia/1612215.html` | User opens in browser from terminal | Single‑machine, no‑server setup |
| **B — FastAPI endpoint** | Existing FastAPI server + new route | `http://localhost:8000/docs/1612215.html` | Clickable link in browser | Multi‑user, web‑frontend RAG |
| **C — HTML index** | Pre‑generated static site | `file:///.../index.html#1612215` | Searchable explorer | Offline reference corpus |

### Approach A: Local File Path

Inject the file path at context‑building time, alongside the human-readable identifier:

```python
SOURCE_BASE = "Jurisprudencia"  # relative to project root

def get_doc_path(doc_id):
    \"\"\"Return the relative path to the source HTML file.\"\"\"
    filename = doc_id if doc_id.endswith('.html') else f'{doc_id}.html'
    return f'{SOURCE_BASE}/{filename}'

# In the context builder:
label = get_doc_label(doc_id)
path  = get_doc_path(doc_id)
ctx += f"[{label}] (→ {path}): {chunk_text}"
```

The response then shows:
```
CAS. N° 15-2015 LAMBAYEQUE | Corte Suprema
→ Jurisprudencia/1612215.html
```

The user opens the path in their browser (Ctrl+click in most terminals, or `open`/`xdg-open`).

### Approach B: FastAPI Endpoint

If the project already has a FastAPI server (like this one's `api.py`), add a static file route:

```python
from fastapi.staticfiles import StaticFiles

# Serve HTML files at /docs/...
app.mount("/docs", StaticFiles(directory="Jurisprudencia"), name="docs")
```

Then inject URL paths instead of filesystem paths:

```python
DOCS_BASE_URL = "http://localhost:8000/docs"

def get_doc_url(doc_id):
    filename = doc_id if doc_id.endswith('.html') else f'{doc_id}.html'
    return f'{DOCS_BASE_URL}/{filename}'
```

### Approach C: Static HTML Index

For a searchable offline corpus, generate an `index.html` that lists all documents grouped by type (RTF, CAS, EXP) with a search input:

```bash
# One-time script: iterate metadata_docs.json, generate a lightweight
# client-side searchable HTML table.
python3 -c "
import json
with open('data/metadata_docs.json') as f:
    meta = json.load(f)
# Generate an HTML page with searchable table
# Columns: Identificador | Órgano | Fecha | File
# Each row links to the corresponding Jurisprudencia/{filename}
"
```

### Source File Checklist

Before implementing any linking approach, verify that source files still exist on disk:

- [ ] Are the original HTML/PDF documents present? (`find . -name "*.html" | wc -l`)
- [ ] Do filenames match the internal IDs? (`.html` extension, same numeric prefix)
- [ ] Are there directories that need indexing? (e.g., `Jurisprudencia/`, `data_raw/`)
- [ ] If documents were moved or archived, update `SOURCE_BASE` accordingly
- [ ] For web links, check that the FastAPI static route doesn't conflict with existing routes

### See Also

- `references/document-linking-approaches.md` — Concrete implementation example for a 64K‑document legal RAG system, including the metadata‑to‑path mapping table and URL vs. filepath decision guide.

## Pattern: Multi-Provider LLM Support

RAG systems benefit from letting users choose their preferred LLM provider (cost, latency, availability). The OpenAI-compatible Python client (`openai` library) acts as a universal adapter — most providers (Groq, OpenRouter, DeepSeek, Together, OpenAI) share the same protocol.

### Configuration Pattern

```python
from openai import OpenAI
import os

PROVEEDORES = {
    "groq":       ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "openrouter": ("https://openrouter.ai/api/v1",   "meta-llama/llama-3.3-70b-instruct"),
    "deepseek":   ("https://api.deepseek.com/v1",    "deepseek-chat"),
    "together":   ("https://api.together.xyz/v1",    "meta-llama/Llama-3.3-70B-Instruct"),
    "openai":     ("https://api.openai.com/v1",      "gpt-4o-mini"),
}

provider = os.getenv("PROVEEDOR", "groq")
api_key  = os.getenv("API_KEY")
base_url = os.getenv("API_BASE_URL") or PROVEEDORES[provider][0]
model    = os.getenv("MODELO") or PROVEEDORES[provider][1]

llm_client = OpenAI(api_key=api_key, base_url=base_url)
```

### Design Rules

1. **Document in `.env.example`** — give colleagues 3-5 provider options with registration links and typical pricing
2. **Do NOT default to a paid-only provider** without documenting cheaper alternatives (e.g., DeepSeek v4-flash at $0.28/1M output tokens)
3. **Respect environment over code** — `API_BASE_URL` and `MODELO` overrides should work without editing source

### Failover Chain Pattern

For production systems, use **multiple providers in a failover chain** rather than a single provider. This gives both cost optimization (cheaper primary) and reliability (fallback if primary is down).

```python
# Pseudo-code for a two-provider failover chain

PRIMARY_CLIENT   = OpenAI(api_key=DS_KEY, base_url="https://api.deepseek.com")
PRIMARY_MODEL    = "deepseek-chat"
PRIMARY_LABEL    = "DeepSeek V4 Flash"

FALLBACK_CLIENT  = Groq(api_key=GROQ_KEY)
FALLBACK_MODELS  = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama-3.1-8b-instant"]

ans = ""
if PRIMARY_CLIENT:
    try:
        response = PRIMARY_CLIENT.chat.completions.create(
            model=PRIMARY_MODEL, messages=messages, stream=True
        )
        for chunk in response: ...
        ans = collected
    except Exception as e:
        logger.warning(f"{PRIMARY_LABEL} failed: {e}. Falling back...")
        ans = ""

if not ans and FALLBACK_CLIENT:
    for model in FALLBACK_MODELS:
        try:
            response = FALLBACK_CLIENT.chat.completions.create(...)
            ...
            break
        except: continue
```

**Recommended chain for cost + reliability:**

| Tier | Provider | Model | Cost/1M output | Notes |
|------|----------|-------|----------------|-------|
| 1 (primary) | DeepSeek | deepseek-v4-flash | $0.28 | Best value, good quality, 1M context |
| 2 | Groq | llama-3.3-70b-versatile | $0.79 | Reliable, fast, solid Spanish |
| 3 | Groq | mixtral-8x7b-32768 | ~$0.40 | Budget fallback |
| 4 | Groq | llama-3.1-8b-instant | ~$0.05 | Last resort, low quality |

**Keep follow-up/side tasks on the cheapest provider.** Question generation, summarization, and routing decisions don't need the primary model — route them to a small fast model (e.g., llama-3.1-8b-instant) on the fallback provider.

#### Pitfall: Phantom Models in Failover Lists

Model availability changes without notice. A model that worked last month may return 404 today. If you hardcode it in a failover list, each query wastes ~0.3-0.5s on a failed attempt.

```python
# BAD — these models returned 404 on Groq as of 2026-05:
models_to_try = [
    "meta-llama/llama-4-maverick-17b-128e-instruct",  # 404 — does not exist
    "openai/gpt-oss-120b",                              # 404 — does not exist
    ...
]
```

**Mitigation:**

1. **Test the entire list at startup** — before accepting queries, try each model with a minimal prompt and log which ones succeed
2. **Bootstrap the live list** — at deploy time, probe all candidate models and keep only the ones that return 200
3. **Fall back to a known-good shortlist** — keep 2-3 models that are known to work regardless of upstream changes (e.g., `llama-3.3-70b-versatile` has been stable on Groq for months)
4. **Audit periodically** — review failover lists every 2-3 months; remove models that consistently 404

## Pattern: Streaming Responses

All OpenAI-compatible providers support `stream=True`. Add as a CLI flag or config toggle:

```python
for chunk in llm_client.chat.completions.create(
    messages=[...], model=..., stream=True
):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### When to Use Streaming

| Use case | Reason |
|----------|--------|
| Interactive CLI / chat | Users appreciate seeing response build in real-time |
| Long responses (legal, medical) | Reduces perceived latency for multi-paragraph answers |
| Debugging | See where the model starts hallucinating or repeating |
| Batch evaluation | Turn OFF streaming for consistent timing |

## Pattern: RAG Project Organization & Distribution

RAG projects accumulate many scripts (ingestion, evaluation, admin, experiments). Keep the query engine lean with these rules.

### Source Hygiene

Every `.py` file should have a header docstring: what it does, how to invoke it, and any architecture notes. Archive inactive scripts preserving category structure:

```
project/
├── query_engine.py          # [ACTIVE] one file, self-contained
├── README.md
├── requirements.txt
├── scripts/
│   ├── batch_test_suite.sh  # [ACTIVE] evaluation
│   └── data_prep/           # [ACTIVE] preprocessing
└── _archive/                # Stale scripts, not deleted
    ├── scripts/
    │   ├── admin/
    │   └── benchmarks/
    └── frontend/
```

### Distributable Package Pattern

When sharing a RAG system with a colleague so they can test immediately, create a **self-contained subset** with runtime files only:

```
RAGApp_v3/
├── query_engine.py           # Multi-provider, self-contained
├── README.md                 # Step-by-step install + provider guide
├── requirements.txt
├── .env.example              # 5 documented provider options
└── data/
    ├── indices/*             # Pre-built vector/graph indexes
    └── metadata.json         # Document labels
```

**Exclude** from distribution:
- Source documents (HTMLs, raw JSON, PDFs)
- Ingestion/preprocessing scripts
- Large alternate or experimental indexes
- `.env` (secrets), `venv/`, `__pycache__/`
- Old reports, benchmarks, experiment outputs

The recipient should need only: `pip install -r requirements.txt` + their own API key.

### Parallel Processing for Large Corpora

When processing 10K+ source documents (HTML extraction, chunking, embedding), use `ThreadPoolExecutor`:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(process_file, f): f for f in all_files}
    for future in as_completed(futures):
        result = future.result()
```

Report progress every N items and avoid loading all results into memory at once. For 64K files at 8 threads, expect ~4 min wall time vs. 30+ min single-threaded.

## Pattern: Pipeline-Level Evaluation (Beyond the Prompt)

A RAG system can have a perfect prompt but still fail due to **downstream pipeline issues**. You must test the full pipeline end-to-end, not just the LLM's output format.

### The 6-Dimension Checklist

Evaluate every pipeline component, not just the final response:

| Dimension | What to check | Failure signal | Severity |
|-----------|--------------|----------------|----------|
| **Router classification** | Does the query router correctly classify LOCAL vs WEB queries? | A query about a 2025 law routed to local index instead of web | HIGH |
| **Document identifier quality** | Are docs cited with human-readable IDs (RTF N°, CAS. N°) or opaque internal IDs? | `[Doc: 1612215]` instead of `CAS. N° 517-2016-ICA | Corte Suprema` | HIGH |
| **Mandated field citation** | Does each response include the mandated field (fallo, diagnosis, finding)? | Model summarizes abstractly, never quotes the actual ruling | HIGH |
| **Institution name hallucination** | Does the model use the correct jurisdiction-specific names? | "Corte Constitucional" in Peru (correct: "Tribunal Constitucional") | MEDIUM |
| **Web search integration** | When WEB is activated, do the results actually appear in the final response? | Router says "Searching web..." but response says "No info found" | MEDIUM |
| **Prompt divergence** | If the project has multiple entry points (CLI, API), do they use the same prompt? | CLI has Escenario A/B + fallo + IDs; API has weaker prompt without those | LOW |

### Test Suite Diversity

Select test queries across **three axes**:

1. **Materia** — laboral, tributario, civil-procesal, constitucional, familia
2. **Complejidad** — simple (1 concepto), medium (2-3 conceptos), complex (multi-arista, 15+ palabras)
3. **Necesidad web** — queries explícitamente sobre eventos 2024+ / leyes recientes / farándula

Minimum battery: 6 queries — 2 simples, 2 medias, 2 complejas. Include at least 2 that SHOULD trigger web search.

### Router Testing Protocol

Test the router explicitly, not just the final response. The router is a separate LLM call with its own failure modes.

```python
# Pseudo-code for router testing
for query in test_suite:
    decision, hyde = route_query_and_hyde(query)
    expected = "WEB" if query_covers_recent_events(query) else "LOCAL"
    if decision != expected:
        # Router failure — capture query, expected, actual
        log_failure(query, expected, decision)
```

**Known router blind spots:**
- Recent laws (2024+ year) get classified as LOCAL because "ley N°" looks like a legal query
- Current events questions without explicit "2024+" year marker
- "tendencia" or "última" queries about fast-changing legal topics
- **Year number detection**: The router does NOT parse numeric years (e.g. "2025") as a signal for WEB. A query containing "publicadas en 2025 en el Perú" gets routed as LOCAL because surrounding words ("ley", "modificaciones") look like legal research. Fix: add explicit date-range detection — if the query contains a year >= (current_year - 1), force WEB.
- **Query structure > content**: "Ley 32186 sobre teletrabajo 2025" → LOCAL (router sees "Ley" + number = legal). "últimas noticias penal de Castro Castro" → WEB (router sees "noticias"). The router keyword-heuristic is biased toward nouns like "noticias", "farándula", "clima" and misses structured legal references to recent events.

### Alternative: LOCAL-First Routing (Post-Retrieval Fallback)

An alternative to decision-based routing (classify query → pick source) is **retrieval-based routing** (always LOCAL first → fall back to WEB only if empty):

```
1. ALWAYS retrieve from LOCAL (FAISS + BM25 + RRF)
2. If LOCAL returns ≥1 relevant document (score > threshold) → use LOCAL
3. If LOCAL returns 0 results or max score < threshold → try WEB search
4. If WEB also returns nothing → say "no encontré información sobre este tema"
```

**When to use this approach:**
- Your LOCAL corpus is large and covers most user queries (>80% hit rate expected)
- You have high-quality embeddings and the LOCAL index is trustworthy
- Users ask about specific known documents ("sentencia TC sobre X", "ley Y")
- The penalty for a wrong WEB answer (hallucinated sources, no grounding) outweighs the benefit

**When NOT to use this approach:**
- Your LOCAL corpus is small or sparse (many queries will hit WEB anyway)
- The corpus covers only specific domains and users regularly ask about unrelated topics
- WEB routing is needed for time-sensitive queries that the corpus can't answer (news, recent rulings)
- Latency is critical — LOCAL retrieval + possible web fallback adds extra time on every query

**Implementation sketch:**

```python
# Retrieval-based routing — pseudo-code
def route_and_retrieve(query):
    # Step 1: Always try LOCAL first
    local_docs, context = get_hybrid_context(query, top_k=7)
    
    if local_docs and max_score(local_docs) > RELEVANCE_THRESHOLD:
        # LOCAL found relevant results — use them
        return "LOCAL", local_docs, context
    
    # Step 2: LOCAL had nothing relevant — fall back to WEB
    web_context = serper_search(query)
    return "WEB", [], web_context
```

**Trade-off compared to decision-based routing:**

| Aspect | Decision-based (classify first) | Retrieval-based (always LOCAL) |
|--------|-------------------------------|-------------------------------|
| Latency when LOCAL is wrong | ~1s (just the router) | ~3-10s (retrieval + router) |
| Latency when LOCAL is right | ~1s router + ~3s retrieval | ~3s retrieval (no router) |
| Miss rate | Router may send valid queries to WEB | Never misses LOCAL content |
| Extra API calls | 1 extra LLM call (router) | Retrieval on every query |

The retrieval-based approach is better when the corpus has high coverage. Decision-based is better when users frequently ask about topics outside the corpus.

### Multi-Prompt Audit

When a project has multiple entry points, verify they share the same prompt:

1. Collect all prompt templates across CLI, API, and any web interface
2. Compare on these elements:
   - Escenario A/B conditional logic
   - Mandatory field citation rules (fallo, etc.)
   - Document identifier format (get_doc_label or equivalent)
   - Concision rules for negative-case (Escenario B)
3. Differences silently degrade the user experience on one interface

## Factual Extraction Testing (Criminal Case Corpus)

Most RAG testing focuses on **semantic retrieval** — queries about legal concepts (principios, doctrina). A harder dimension is **factual extraction**: retrieving specific numeric facts (pena years, montos reparación civil), names (partes, testigos, jueces), and article citations from specific case files.

### How to test

1. Identify a set of case files (e.g., `Jurisprudencia/1014875.html` through `1014898.html`)
2. Extract known facts by reading the actual HTML files
3. Build queries that demand those exact facts
4. Run through the RAG pipeline and measure:
   - **Factual accuracy** — did it get the number/name/article correct or hallucinate?
   - **Citation presence** — did it include the document path?
   - **Chunk coverage** — is the needed fact within a single chunk or split across boundaries?

### Known limitation

The FAISS index chunks at 512 words/50 overlap. Facts that cross chunk boundaries or belong to semantically weak chunks (procedural boilerplate) are hard to retrieve. This is a **pipeline limitation**, not a prompt problem — factual extraction improvements require changes to chunking strategy, not the LLM prompt.

### Reference

- `references/factual-extraction-test-resource.md` — Full file-to-case mapping for the criminal corpus, query templates, success rate estimates, and chunking caveats.

## References

### Pattern References

- `references/document-linking-approaches.md` — Three approaches for making RAG document references clickable (file paths, FastAPI, static HTML index), with the metadata-to-path mapping table and decision guide for a 64K-document legal corpus.
- `references/patch-log-20260518-fix.md` — Concrete 4-file patch adding file paths + human-readable identifiers (RTF N°/CAS. N°) to a legal GraphRAG system, with before/after code, design decisions, and remaining issues.
- `references/battery-test-results-20260519.md` — 14-query battery test results across 5 materias, with router blind spot analysis, HyDE overspecification diagnosis, and monitoring data showing 36% Escenario A hit rate.
- `references/pattern-conditional-branching.md` — Complete prompt template implementing conditional branching + mandatory citation + negative-case transparency for a legal-domain RAG system.
- `references/testing-report.md` — 4-query test battery (2 positive, 2 negative) with before/after comparisons.
- `references/document-identifier-enrichment.md` — Case study of enriching 64K legal documents with RTF/CAS/EXP identifiers from HTML headers, including regex patterns and FAISS + NetworkX integration.
- `references/pipeline-evaluation-protocol.md` — Full 6-query evaluation battery across materia x complejidad, with router testing, identifier audit, and web search integration checks. Includes a worked example from evaluating a Peruvian legal GraphRAG system.
- `references/batch-speed-optimization.md` — Direct function call vs subprocess pattern for batch RAG queries. Achieves 5.5× speedup by sharing the loaded model across queries. Covers async generator stdout pitfalls and HF_TOKEN authentication.
- `references/stale-credential-detective-pattern.md` — Debugging pattern for mismatched database passwords across files. When `.env` has a stale password but build scripts have the correct one, use this detective technique to find and sync all credential sources in a RAG project.

### Domain-Specific Implementations

- `references/legal-domain-implementation.md` — Peruvian jurisprudence regex patterns, 15-question lawyer-oriented test suite, provider pricing comparison, gitignore templates, and parallel processing recipes for legal RAG.
