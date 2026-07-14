# Research Reference: Inglés para Hispanohablantes Profesionales (A2→B1)

> Generated: July 2026
> Source: 5 local files + web research

## Key Frameworks Discovered

### 1. Extensive Processing Instruction (EPI) — Conti 2025-2026
- **MARS-EARS Framework**: Modeling → Attending → Repeating → Structuring (receptive) / Expanding → Applying → Recycling → Spontaneous (productive)
- Adopted by >50% of UK language schools (Language Trends England 2026 report)
- Core principle: teach via LEXICAL CHUNKS (not isolated words or grammar rules)
- Grammar introduced AFTER receptive+productive practice
- 14 Staples include: Sentence Builders, Narrow Listening/Reading, Pattern Practice, Fluency Training, Self-regulation, Metacognitive strategies, Affective scaffolding (self-efficacy)

### 2. Neuroeducation Study — Wushcashina-Jacome & Caiza-Jaya (2026)
- 120 adults, quasi-experimental
- Experimental group: **244.8% improvement** in linguistic competencies
- Control group: 82.8% improvement
- Cohen's d: **2.28 to 3.27** (very large effects)
- Components: multisensory stimulation, spaced retrieval, affective feedback, intrinsic motivation (+12.3), self-efficacy (+13.4), anxiety reduction (-11.5)

### 3. Interleaving for Grammar — Pan et al. (2025)
- Interleaving improves verb conjugation, tense identification, language identification
- Nakata & Suzuki (2019): d > 0.7 for grammar learning
- Hwang (2025): "Undesirable Difficulty" — harder during training, superior long-term retention
- **Critical condition**: interleaving works best when concepts are SIMILAR and HARD TO DISTINGUISH (e.g., ser/estar, present perfect/simple past)

### 4. Brain-Inspired Multisensory Learning — Gkintoni et al. (2025)
- Systematic review of 80 studies
- Adult neuroplasticity is GREATER than previously believed
- Minimum 2 sensory modalities per activity for optimal activation
- Key insight: adults can achieve native-like proficiency with structured approach

## Critical Techniques Ranking (Evidence-Based)

| Rank | Technique | Evidence Strength | App Implementation |
|------|-----------|-------------------|-------------------|
| 1 | Spaced Repetition | 200-400% better retention | SM-2 algorithm, intervals 1d/3d/7d/15d/30d |
| 2 | Retrieval Practice | 85% better vs. re-reading | Active quizzes after every lesson |
| 3 | Interleaving | d > 0.7 for grammar | Mix grammar/vocab/listening per session |
| 4 | Comprehensible Input (i+1) | Krashen: strongest predictor | Content filtered by level, EN subs always |
| 5 | Shadowing | 6 weeks for significant gains | Listen-repeat-record-compare loop |
| 6 | Task-Based Language Teaching | d = 0.93 (meta-analysis 2024) | Meeting/call/email simulations |
| 7 | Corrective Feedback | Recast > explicit for fluency | Implicit + explicit combined |
| 8 | Listening-While-Reading | Improves word recognition | Highlight-as-you-hear mode |
| 9 | Dual Coding | Strengthens neural connections | Video + transcript + images |
| 10 | Extensive Reading | Implicit vocabulary gains | Graduated library + professional articles |

## Hispanohablante Error Patterns

### Pronunciation (Phonetic)

| Error | Wrong → Right | Cause | Fix |
|-------|---------------|-------|-----|
| /b/ vs /v/ | "berry good" → "very good" | Spanish allophones | Minimal pairs + waveform feedback |
| /i:/ vs /ɪ/ | "ship" = "sheep" | Single Spanish /i/ | Minimal pairs + recording |
| /θ/ and /ð/ | "tink" → "think" | Don't exist in Spanish | Tongue position video + drills |
| Schwa /ə/ | Over-articulated → /bəˈnænə/ | Doesn't exist in Spanish | Natural reduction audio |
| Final consonants | "walk" → "walks" | Spanish avoids final clusters | Ending sound vibration drills |

### Grammar

| Error | Wrong → Right | Explanation |
|-------|---------------|-------------|
| Subject omission | "Is a nice day" → "It is a nice day" | Spanish is pro-drop |
| 3rd person -s | "She walk" → "She walks" | Spanish doesn't inflect 3rd person for -s |
| Auxiliary "Do" | "Where you work?" → "Where do you work?" | Spanish has no auxiliary in questions |
| Present Perfect vs Past | "I have lived there last year" → "I lived there last year" | Aspectual distinction absent in Spanish |
| Adjective order | "a house beautiful" → "a beautiful house" | Spanish postposes adjectives |
| He/She confusion | "My mother, he works" → "She works" | Grammatical gender interference |
| Prepositions | "depend of" → "depend on" | Literal translation from Spanish |

### Top False Friends (Critical — 15)

| Spanish word | English false friend | Real meaning |
|-------------|---------------------|--------------|
| éxito | exit (salida) | success |
| fábrica | fabric (tela) | factory |
| sensible | sensible (sensato) | sensitive |
| embarazada | embarrassed (avergonzado) | pregnant |
| constipado | constipated (estreñido) | have a cold |
| recordar | record (grabar) | remember |
| realizar | realize (darse cuenta) | carry out / achieve |
| asistir | assist (ayudar) | attend |
| introducir | introduce (presentar) | insert |
| carpeta | carpet (alfombra) | folder |
| librería | library (biblioteca) | bookstore |
| actualmente | actually (en realidad) | currently |
| colegio | college (universidad) | school |
| pretender | pretend (fingir) | intend / plan |
| soportar | support (apoyar) | tolerate / bear |

## App Stack Recommendation (Python-Centric)

```
FRONTEND: Shiny for Python (full-stack) + PWA for offline
BACKEND:  FastAPI + Pydantic + SQLAlchemy + JWT/OAuth2
AI LAYER: Groq (DeepSeek / Llama 3.1) for roleplay + Whisper for STT + Edge TTS
DB:       SQLite (dev) / PostgreSQL (prod) + Redis for cache
SRS:      Custom SM-2 algorithm (pure Python, no GPU)
SEARCH:   FTS5 or pg_trgm for full-text search
FILES:    Cloudflare R2 / S3 for audio + images
```

## Key Papers & Sources

1. Wushcashina-Jacome & Caiza-Jaya (2026) — Neuroeducación en SLA
2. Conti, G. (2025-2026) — EPI / MARS-EARS framework (gianfrancoconti.com)
3. Pan, S.C. et al. (2025) — Interleaved practice enhances grammar skill learning
4. Nakata & Suzuki (2019) — Effects of blocking and interleaving on L2 grammar
5. Gkintoni, E. et al. (2025) — Brain-Inspired Multisensory Learning (80 studies)
6. Krashen, S. — Input Hypothesis (i+1)
7. Roediger & Karpicke — Testing effect / Retrieval practice
8. Knowles, M. — Andragogy: 6 principles of adult learning
9. Duolingo (2024) — Duolingo Max: GPT-4 roleplay + video call
10. Reddit r/languagelearning — Community consensus on effective techniques
