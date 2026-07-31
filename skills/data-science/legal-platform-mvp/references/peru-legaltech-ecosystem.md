# Peru LegalTech Ecosystem — Competitor Analysis

Collected July 2026 via parallel subagent research (YouTube comments, forums, competitor websites, academic portals).

## Direct Competitors (Peruvian LegalTech AI Platforms)

### DOXS.AI
- **URL:** https://doxs.ai
- **Origin:** Cusco, Peru. Founded by Torres brothers. Launched Dec 2025.
- **Users:** 523,000+ consultations
- **Pricing:** Free / Pro S/35/mes / Pro Yape S/100/3months / Institutional custom
- **Features:** Jurisprudence search (TC + Supreme Court + SCIJ), demand/legal writing, expedient analysis (OCR), **intercultural mode (Quechua, Aymara, Awajún by VOICE)**
- **Backing:** Start UPC, Incuba Andina, Ministry of Production, Google for Startups
- **Penal coverage:** Partial — generates criminal demands, indexes criminal plenary rulings. Not specialized in penal law.
- **Metadata:** 5M+ indexed rulings, ~5s response time, 100% official state sources

### Juztina
- **URL:** https://www.juztina.ai
- **Origin:** Kontrata Legaltech S.A.C. Operates in Peru, Chile, Colombia, Argentina, Mexico.
- **Users:** 177,300+ lawyers, 1,890,000+ consultations
- **Pricing:** Not publicly listed (pricing page returns 404). Freemium model.
- **Features:** AI legal assistant, specialized search, branch-specific agents (only Labor available), case organization
- **Complaints:** Users report unauthorized charges, "everything pulled from Google", poor quality. Trust gap = opportunity.
- **Penal coverage:** None visible. Only Labor agent is branch-specific.

### LEXIUS Peru
- **URL:** https://lexius.io/pe
- **Origin:** Latin American platform in 18 countries.
- **Pricing:** S/38/mes, S/94/quarter, S/228/year
- **Features:** Most feature-rich: chat, mind maps, transcription, AI podcasts, PPT generation, songs
- **Penal coverage:** None. Generalist legal information system.

## Indirect Competitors

### vLex
- Global enterprise legal research. Vincent AI assistant. SOC2/ISO 27001. Enterprise pricing.
- Covers Peruvian jurisprudence but no specialized penal focus.
- Not accessible to independent lawyers (enterprise-only).

### SPIJ (Sistema Peruano de Información Jurídica)
- spijweb.minjus.gob.pe — Government platform, free.
- No AI, no semantic search, no API. Traditional database.
- Authoritative but outdated UX.

### LP Derecho & Juris.pe
- Static HTML blogs with the penal code text. Manual updates by human team.
- No AI, no semantic search, no interactivity. Monetized via ads and diploma sales.
- Cloudflare-protected (hard to scrape).
- **LP Derecho is the #1 legal YouTube channel in Peru** — 7.4K views on "Can a lawyer use AI?" Shorts.

## Gaps in the Market

| Gap | Status |
|-----|--------|
| Penal-code-specific AI platform | **No one has this** |
| RAG with granular paragraph-level citations | No one |
| Legislative time-machine (version history) | No one |
| Automatic penalty calculator (tercios, Art. 46) | No one |
| Auto-update from El Peruano in <24h | No one |
| Open-source penal code dataset in JSON | **Does not exist** |
| El Peruano scraper on GitHub | **Does not exist** |

## YouTube Demand Signals

| Video | Views | Signal |
|-------|-------|--------|
| "CÓDIGO PENAL PERUANO (AUDIOLIBRO)" | 23,000 | Massive demand for digital penal code access |
| "Probando IA para abogados" | 18,000 | High interest in AI legal tools |
| "¿Un ABOGADO puede usar IA?" | 7,400 | Debate on AI in Peruvian law |
| "El Poder Judicial del Perú ya usa IA" | 2,100 | Institutional validation |
| "Lanzan aplicativo que calcula prescripción penal" | 1,000 | Demand for penalty calculation tools |

Top comment on the 23K-view audiobook: "recomiendo tener un código actualizado a la mano, para no caer en una desactualización jurídica" (8 likes).

## Academic/Forum Insights

- **Enfoque Derecho** (THĒMIS PUCP): +950 articles. Reports 28 LegalTech providers in Peru.
- **IUS360** (IUS ET VERITAS): Notes that law firm management in Peru is "below the regional average."
- **Key need stated:** Automation of legal documents, digital legal research, desk management.
- **Fernando de Trazegnies** (former Foreign Minister, PUCP professor) wrote foundational paper on AI + judicial reasoning (2013).

## Key Libraries & Repos Found

- **NexusRAG** (323⭐): FastAPI + ChromaDB + LightRAG + Ollama + cross-encoder + citations. **Stack almost identical to ours. Forkable.**
- **LightRAG** (37.3K⭐): Knowledge graph for legal entities. EMNLP 2025.
- **korean-law-mcp** (2.1K⭐): Best reference for verifiable citations and anti-hallucination.
- **BGE-M3-Legal-Spanish** (`wilfredomartel/BGE-M3-Legal-Spanish`): Embedding model specifically fine-tuned on Spanish legal text. 8192 token context, 546K training examples.
- **PeruvianConstitutionChunkRetrieval** (`bowang0911/PeruvianConstitutionChunkRetrieval`): Template dataset for structuring Peruvian legal chunks (10.4K chunks, HuggingFace).

## Pricing Benchmark

| Platform | Monthly Price | Model |
|----------|--------------|-------|
| DOXS.AI | S/35 (~$9) | Freemium |
| LEXIUS | S/38 (~$10) | Paid only |
| Juztina | Not public | Freemium (contact sales) |

**Recommended pricing for new entrant:** S/29/mes Pro, S/0 Free tier (10 queries/day, no advanced features). 50% discount for @edu.pe emails.
