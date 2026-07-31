---
name: obsidian-study-system
description: Build study/knowledge systems in Obsidian — vault organization, MOCs, atomic notes, spaced-repetition flashcards, templates, and daily study notes. Complements the bundled "obsidian" skill (file I/O) with methodology patterns.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [obsidian, study, flashcards, knowledge-management, vault, spaced-repetition]
    related_skills: [obsidian]
---

# Obsidian Study System

Build organized study systems inside an Obsidian vault. Complements the bundled `obsidian` skill (which handles file read/write/search) with methodology patterns for knowledge management.

## When to Use

- User asks to "organize my vault" or "ordenar las notas sueltas"
- User asks to create a study system for a domain (LegalTech, electoral, etc.)
- User wants flashcards for spaced repetition
- User wants to create templates for consistent note-taking
- User asks about using Obsidian for learning/study

## Vault Organization (Reorganizar)

When loose `.md` files accumulate in the vault root:

1. **Scan root**: `search_files(target='files', pattern='*.md', path=<vault_path>)` or `find <vault_path> -maxdepth 1 -name "*.md"`
2. **Categorize**: group by domain — TC_SearchRAG, electoral, projects, tools, etc.
3. **Create folders**: `mkdir -p <vault_path>/TC_SearchRAG <vault_path>/Proyectos ...`
4. **Move files**: `mv '<vault_path>/source.md' '<vault_path>/TargetFolder/'`
5. **Update index**: patch the main MOC/index note adding `[[TargetFolder/NoteName]]` wikilinks
6. **Delete trash**: remove empty files (0 bytes) and non-note artifacts (ask user first)
7. **Verify**: confirm root is clean

### Pitfalls

- Files with spaces in names need shell-safe paths: wrap in quotes
- After moving, update the INDEX — individual notes keep their relative wikilinks intact
- Always ask before deleting files; show what you plan to remove

## Study System Creation

When building a new knowledge domain (e.g., LegalTech):

### Folder Structure

```
Domain/
├── Índice Domain.md              ← MOC principal
├── Conceptos/                    ← One note per concept
├── Flashcards/                   ← Spaced repetition cards
├── Plantillas/                   ← Reusable templates
└── Diario/                       ← Daily study notes (optional)
```

### MOC (Map of Content / Índice)

Root-level note with wikilinks to every note in the domain:

```markdown
# Domain — Mapa de Conocimiento

## Conceptos
- [[Concepto A]] — breve descripción
- [[Concepto B]]

## Flashcards
- [[Flashcards - Domain]]

## Proyectos Relacionados
- [[Proyecto X]]
```

### Atomic Concept Notes

One note per concept in `Conceptos/`:

```markdown
# Concept Name

<!-- 2-3 line description -->

## Detalle Técnico
```
<!-- code, diagram, schema -->
```

## Relacionado
- [[Related Concept 1]]
- [[Related Concept 2]]
```

Keep each note 1-3 KB. If it exceeds 5 KB, split into sub-concepts.

### Flashcards (Spaced Repetition)

Format compatible with **Obsidian Spaced Repetition** plugin:

```markdown
## Question text?
?
Answer text

<!--SR:!2026-07-05,7,270-->
```

The `<!--SR:!YYYY-MM-DD,interval,ease-->` tag tracks review. Generate with a future date ~7 days out so the user gets the first review in one week.

Group by topic file: `Flashcards - Domain.md`, each with tag `#flashcards #<domain>`.

### Templates

Store in `Plantillas/`. Use `{{title}}`, `{{date}}`, `{{tags}}` as placeholders Obsidian fills when creating from template.

## Daily Study Notes

Optional: create a daily note after each study/work session:

```markdown
# YYYY-MM-DD — Estudio

## Aprendido hoy
- Concepto 1
- Concepto 2

## Relacionado
- [[Note from today]]

## Próximo
- What to review tomorrow
```

## Token Estimation

Before creating multiple notes (3+ files or 5+ KB total), tell the user the estimated token cost and ask for approval. Pattern: "Crear ~X archivos (~X KB total, ~X tokens estimados). ¿Procedo?"

## Minimal Viable Study System

When the user is new to this: create just 3 things to start:
1. **MOC** (index with wikilinks)
2. **1-2 atomic concept notes** (most relevant topics)
3. **8-10 flashcards** (to start reviewing immediately)

This gives immediate value without overwhelming the vault.
