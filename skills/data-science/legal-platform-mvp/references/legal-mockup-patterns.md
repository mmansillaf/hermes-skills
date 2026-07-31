# Legal Platform Mockup Design Patterns

Conventions, data schemas, and visual patterns for building LegalTech platform mockups. Derived from building "CP-Perú IA" — a Peruvian Penal Code platform with AI.

## Visual Design System

```
Primary:    #1a237e (indigo-900) — headers, navbar, CTAs
Secondary:  #1e3a5f (blue-gray)  — sidebar, cards
Accent:     #c9a84c (gold)       — pricing highlight, badges, links
Background: #ffffff / #0f172a    — light/dark
Text:       #1e293b / #e2e8f0    — dark/light mode
```

**Typography:** Georgia/Cambria for legal text (serif, authoritative), system sans-serif for UI. Legal text at 18px+ for readability.

**Dark mode:** Toggle via `class="dark"` on `<html>`. All Tailwind classes use `dark:` variants. Persist preference in `localStorage`.

## 5-Screen Architecture

Every legal platform MVP needs these 5 screens. Each is a standalone HTML file:

### 1. Landing Page (`landing.html`)
- **Hero:** Gradient headline, subtitle explaining the gap in market, 2 CTAs (Free Trial + Demo), 3 stat cards
- **Features grid:** 6 features in 2x3 or 3x2. Each card: emoji icon + title + description
- **How it works:** 3-step visual with numbered circles
- **Pricing:** 3 tiers. Middle tier has "Most Popular" badge. Include edu discount note.
- **Testimonials:** 3 cards with star ratings, quote, name, role, company
- **FAQ:** Accordion (click to expand, others collapse). 5 questions.
- **CTA section:** Dark background, bold text, 2 buttons
- **Footer:** 4-column with product/legal/contact links

### 2. Dashboard / Article Viewer (`dashboard.html`)
- **Top bar:** Logo + search bar (with dropdown suggestions) + navigation icons
- **Left sidebar (320px):** Hierarchical index of legal code (Books → Titles → Chapters → Articles). Expandable sections. Active article highlighted.
- **Center:** Article rendered with: article number badge, title, status badge (vigente/derogado), modification badges, full text with penalty highlighted, incisos in sub-cards, footer with "vigente desde" date and source
- **Timeline below article:** Vertical timeline with dots for each modification. Shows date, law number, description.
- **Right panel (340px):** Jurisprudence cards + doctrine cards. Each with title, description, source. Empty state when none available.
- **Search:** Input with suggestions dropdown. Filter by article number, title, or text content. Enter or click to navigate.
- **Copy citation button** on each article.

### 3. Chat IA (`chat.html`)
- **Top bar:** Logo + mode toggle (lawyer/citizen) + remaining queries counter
- **Welcome card:** Introduction + example quick-ask buttons (pill-shaped)
- **Messages area:** User on right (purple bg), AI on left (gray bg). AI messages show: model icon + timestamp + response time + expandable "Ver análisis" + source badges row + legal disclaimer
- **Source badges:** Colored by type (article=blue, law=amber, jurisprudence=green+verified checkmark). Clickable.
- **Input area:** Textarea (auto-resize, Enter to send, Shift+Enter for newline) + Send button
- **Right panel (320px):** "Fuentes Consultadas" — list of all sources used, each clickable
- **Legal disclaimer modal:** Shown once per session. Must accept to continue.

### 4. Time-Machine Legislativo (`timemachine.html`)
- **Info banner:** Explains purpose (retroactivity analysis)
- **Date selector:** Range slider 1991→2026. Key dates marked with dots on timeline below slider.
- **Quick-jump buttons:** Pre-configured dates for each major modification.
- **Two-column view:** Left = version at selected date, Right = current version always visible
- **Diff panel:** Below the columns. Shows what changed (added in green, removed in red, strikethrough). Hidden when no differences.
- **Data model:** Each article version needs: date, label, type (original/modification/incorporation/nonexistent), full text, penalty, modifications array, diff type.

### 5. Calculadora de Pena (`calculadora.html`)
- **4-step form** (numbered steps with circle indicators):
  1. Select crime from dropdown (shows abstract penalty range)
  2. Check aggravants (Art. 46-A) — 8 checkboxes in 2-column grid
  3. Check mitigants (Art. 46-B) — 6 checkboxes in 2-column grid
  4. Additional rules: recidivism, attempt (Art. 16, Ley 32258), restricted responsibility (Art. 22)
- **Results panel (sticky right):** Highlighted box with estimated range (large bold numbers) + crime name + abstract penalty + tercio location + counts of aggravants/mitigants + applicable rules
- **Tercio visualization:** 3 horizontal bars (inferior=green, medio=yellow, superior=red) showing the thirds. Marker bar showing where the result falls.
- **Legal note:** Disclaimer that final decision is the judge's.

## Cross-Screen Navigation

Every screen has a top bar with:
- Logo link → landing.html
- Icon buttons for: dashboard (📋), chat (💬), timemachine (🕰️), calculator (🧮)
- Theme toggle (🌓)
- User avatar placeholder

## Article Data Schema

For mock data in HTML and the real JSON dataset:

```javascript
{
  id: "art_106",           // unique slug
  numero: 106,             // article number
  titulo: "Homicidio Simple",
  libro: "II",
  titulo_libro: "Parte Especial — Delitos",
  capitulo: "I",
  titulo_capitulo: "Homicidio",
  texto: "full text...",   // HTML allowed for highlights
  incisos: [{numero: 1, texto: "..."}],
  vigencia: {inicio: "1991-04-08", fin: null},
  modificaciones: [
    {fecha: "2018-08-02", ley: "Ley 30819", descripcion: "Eleva pena de 15 a 20 años.", tipo: "modificacion"}
  ],
  status: "vigente",       // vigente | derogado
  jurisprudencia_vinculada: ["Acuerdo Plenario 1-2016/CJ-116"],
  doctrina_relacionada: ["Dr. Bramont-Arias — Manual de Derecho Penal"]
}
```

Modification types: `"original"`, `"modificacion"`, `"incorporacion"`, `"derogacion"`.

## JavaScript Patterns

- **Theme toggle:** `document.documentElement.classList.toggle('dark')` + localStorage
- **FAQ accordion:** Close all others when one opens
- **Search suggestions:** `oninput` handler, dropdown with filtered results, click-outside-to-close
- **Smooth scroll:** `scrollIntoView({behavior:'smooth', block:'end'})` for messages
- **Typing indicator:** CSS animation with 3 dots, staggered delays
- **Range slider:** Map 0-100 to date range, snap to nearest version
- **Real-time calculation:** `onchange` on all inputs triggers recalculation
