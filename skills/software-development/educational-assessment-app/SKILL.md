---
name: educational-assessment-app
description: Build interactive single-page HTML/CSS/JS educational assessment apps — placement tests, quizzes, adaptive evaluations with CEFR alignment, reinforcement feedback, accessibility controls, and result persistence.
category: software-development
triggers:
  - build a test / exam / evaluation / assessment web app
  - create a quiz app with adaptive difficulty
  - "build an English/Spanish/[lang] placement test"
  - interactive educational single-page application
  - app that evaluates student level and recommends next steps
---

# Educational Assessment App — Build Pattern

## Principles

1. **CEFR or equivalent framework first** — define your levels before writing questions. Each question maps to a level and a skill.
2. **Adaptivity over fixed order** — start easy, progress in difficulty, interleave skills within difficulty blocks.
3. **Feedback is pedagogy** — every answer (right or wrong) should teach: explanation + variants to practice.
4. **Accessibility is not optional** — dark/light theme + font size controls (increase AND decrease, not just cycle) with visible indicator.
5. **Results must be persistable** — auto-save to localStorage + export options (JSON for data, PDF for human-readable).

## Architecture Pattern

```
Single HTML file → All CSS + JS inline
     │
     ├── Design System (CSS custom properties)
     │   ├── Light theme
     │   ├── Dark theme [data-theme="dark"]
     │   └── Font size scale [data-font="small|medium|large|xlarge"]
     │
     ├── Screen Manager (show/hide sections)
     │   ├── Welcome/Start screen
     │   ├── Quiz screen
     │   └── Results screen
     │
     ├── Question Bank
     │   ├── Each question: {id, skill, diff, text, ctx, options[], correct}
     │   ├── Minimum ~1.5× questions needed for any mode (63 for 60 max)
     │   ├── Cover 4 skills: grammar, vocab, reading, listening
     │   └── Difficulty: 1-5 (A1→C1 equivalent)
     │
     ├── Adaptive Algorithm
     │   ├── Pick questions evenly across skills
     │   ├── Sort by difficulty (easy→hard)
     │   └── Shuffle within blocks of 4 for skill interleaving
     │
     ├── Reinforcement System
     │   ├── Database of explanations by question ID
     │   ├── Fallback per-skill generic explanation
     │   └── 3 practice variants shown after each answer
     │
     ├── Results Engine
     │   ├── CEFR level determination (score + avg difficulty)
     │   ├── Per-skill breakdown with animated bars
     │   ├── Personalized recommendations
     │   └── Roadmap/steps by level
     │
     └── Persistence Layer
         ├── localStorage auto-save on finish
         ├── JSON export (data)
         └── PDF export (print-friendly HTML → window.print())
```

## Question Bank Guidelines

### Skill Distribution
- Divide total questions by 4 (grammar, vocab, reading, listening)
- Any remainder goes to the first skills
- Each skill covers all 5 difficulty levels proportionally

### Answer Distribution Rebalancing

**Problem**: when writing questions sequentially, correct answers cluster on early options (A/B). A 63-question bank can end up with 70% on B, 0% on D.

**Fix — rotation algorithm**:
```js
// Target: ~25% per option (A,B,C,D)
// For each question idx 0..N, assign target = idx % 4
// rotation[i] = (target - currentCorrect[i] + 4) % 4
// Apply: options = options[-rot:] + options[:-rot]
//        correct = (correct + rot) % 4
```
After rotation: A=25%, B=25%, C=25%, D=25%. The semantic correctness is preserved because all 4 options rotate together.

**Automated audit**: after building a bank, always check distribution:
```js
var d={0:0,1:0,2:0,3:0};
bank.forEach(q => d[q.correct]++);
console.log(d); // should be ~25% each
```

### Content Suitability
- **Audience-check every question**: would this make sense to a general user?
- Avoid legal jargon, niche specialized terminology UNLESS the test is for that niche
- **Pre-shipping audit**: grep for `court|statute|legal|jurid|counsel|legislative|travaux|ruling` to catch niche legal questions before shipping to general audience
- False friends (embarazada≠embarrassed) are GOOD for Spanish→English tests — they're universal errors
- Reading passages: use general academic/business topics, not field-specific
- When replacing questions, keep the same ID and difficulty tier; swap text, options, and correct index

### Difficulty Mapping (CEFR)
| diff | CEFR | Description |
|------|------|-------------|
| 1 | A1 | Basic grammar, simple vocab, literal reading/listening |
| 2 | A2 | Past tense, comparatives, numbers, schedules |
| 3 | B1 | Conditionals, present perfect, phrasal verbs, inference |
| 4 | B2 | Inversions, passive, formal vocab, nuanced reading |
| 5 | C1 | Subjunctive, cleft sentences, academic/formal register |

## Reinforcement System

### Requirements
- Every question needs an **explanation** (in the user's native language)
- Every question needs **3 practice variants** (fill-in-the-blank exercises on same concept)
- Show IMMEDIATELY after user answers, before they click "next"
- Use a dedicated panel below options, not a modal/overlay

### Fallback Strategy
If a question ID has no custom entry in the reinforcement DB, generate a per-skill generic explanation that:
- States the correct answer
- Explains the general concept
- Gives 3 generic practice tips

## Accessibility Controls

### Font Size
```html
<!-- Instead of cycling Aa button, use A− / indicator / A+ -->
<button onclick="fontShrink()">A−</button>
<span id="fontDisplay">100</span><span class="size-label">%</span>
<button onclick="fontGrow()">A+</button>
```
```js
const fontSizes = ['small','medium','large','xlarge'];
const fontPx = { small:12, medium:16, large:20, xlarge:24 };
let fontIdx = fontSizes.indexOf(savedFont);
if (fontIdx < 0) fontIdx = 1;

function updateFontDisplay() {
  const pct = Math.round((fontPx[fontSizes[fontIdx]] / 16) * 100);
  const el = document.getElementById('fontDisplay');
  if (el) el.textContent = pct;
}
function fontGrow() {
  if (fontIdx < fontSizes.length - 1) fontIdx++;
  html.setAttribute('data-font', fontSizes[fontIdx]);
  localStorage.setItem('app-font', fontSizes[fontIdx]);
  updateFontDisplay();
}
function fontShrink() {
  if (fontIdx > 0) fontIdx--;
  html.setAttribute('data-font', fontSizes[fontIdx]);
  localStorage.setItem('app-font', fontSizes[fontIdx]);
  updateFontDisplay();
}
```
- Sizes: 12px (75%), 16px (100%), 20px (125%), 24px (150%)
- Persist choice in localStorage
- Show current percentage clearly in the indicator
- Initialize: call `updateFontDisplay()` once on page load in case indicator element shows stale value

### Theme
- `data-theme="light|dark"` on `<html>`
- All colors as CSS custom properties with both themes
- Persist in localStorage

## Result Export

### Auto-save (localStorage)
```js
const resultData = {
  date: new Date().toISOString(),
  totalQuestions,
  correct, pct,
  level, levelFull,
  breakdown: { grammar: {correct, total, pct}, ... }
};
const saved = JSON.parse(localStorage.getItem('app-results') || '[]');
saved.push(resultData);
localStorage.setItem('app-results', JSON.stringify(saved));
```
- Keep last 20 results max
- Each new result auto-appends

### JSON Export
- Create Blob from resultData
- Filename: `appname-{level}-{date}.json`
- Trigger download via hidden `<a>` click

### PDF Export
- Build self-contained HTML string with inline styles
- Open in new window, call `window.print()`
- User selects "Save as PDF" from print dialog
- Include: level, score, per-skill breakdown with bars, recommendations table

## Answer Key Protection (Obfuscation)

**Problem**: When embedding a `QUESTION_BANK` with `correct` answer indices in a single-page HTML app, anyone can view source (Ctrl+U or DevTools) and read `correct:0`, `correct:1` in plaintext. For shipped/distributed assessment apps, this lets test-takers cheat trivially. Same concern applies to reinforcement/study content (recommendation text, next-step roadmaps).

**Solution — XOR + base64 pipeline** (Python, standard library only):

```
index.html (plaintext) → Python script → index.html (obfuscated)
                           ├── Parse JS array literal from HTML
                           ├── XOR each correct value with secret key
                           ├── Serialize to JSON → base64
                           ├── Inject inline decoder: atob() + JSON.parse()
                           └── Replace original array with encoded blob
```

### Key Requirements

1. **No `eval()` / `new Function()`** — CSP violation risk and overkill for this use case
2. **`atob()` + `JSON.parse()` only** — standard browser APIs, no CSP directives needed
3. **Local transformation** — Python script runs during build, not at runtime
4. **XOR applied before JSON serialization** — even if someone base64-decodes, they see XORed bytes, not plain numbers

### Runtime Decoder Pattern

```js
// XOR key (single byte, stored as const)
const $k = 0xAB;

// Decode question bank
function $d(s) {
  try {
    var r = atob(s), j = JSON.parse(r);
    for (var i = 0; i < j.length; i++) {
      if (j[i].c !== undefined) j[i].correct = j[i].c ^ $k;
      delete j[i].c;
    }
    return j;
  } catch(e) { return []; }
}

const QUESTION_BANK = $d("base64-encoded-blob");
```

### Decode Verification (browser console)

```js
QUESTION_BANK.length;            // Should match original count
QUESTION_BANK[0].correct;        // Should be original number, not XORed
document.querySelector('script').innerText.match(/correct:\d/g);  // null or empty
```

### Important Caveats

- This is **obfuscation, not encryption**. A determined developer can extract the key and decode manually. It stops casual cheating and Ctrl+F fishing.
- Only appropriate for **fully offline / single-file apps**. Apps with a backend should serve answers via API.
- The XOR key is visible in JS source as a `const`. Consider making it a computed value or embedding it in a less obvious place.
- For higher stakes, add server-side answer validation. This technique is a deterrent, not a security boundary.

### Reference Files

- `references/answer-key-obfuscation.md` — Full Python pipeline: JS literal parsing, object conversion, XOR encoding, base64 serialization, and HTML replacement.
- `references/obfuscation-recovery.md` — Recovery strategy when the obfuscation pipeline produces a corrupted file: extract surviving b64 blobs, rebuild from fresh scaffold, verify balance.
- `references/question-bank-rotation.md` — Rotation algorithm for balancing answer distribution.
- `references/content-audit.md` — Pre-shipping audit for niche/legal content leaking into general-audience tests.

**Note**: A companion skill `html-edu-apps` (same category) has overlapping scope with additional coverage of edge cases (const redeclaration, template literals in heredocs, REINFORCE b64 deduplication). If stuck on a build, check its `references/obfuscation-pitfalls.md`.

## Pitfalls

- **Not enough questions**: if bank has < questions needed, selection fails. Always have 1.5× surplus.
- **Legal/niche questions leak**: when adapting for general audience, grep for `court|statute|legal|jurid|counsel|legislative` before shipping.
- **Font cycle only increases**: user wants to both increase AND decrease. Always provide both buttons + indicator.
- **Correct-answer clustering**: 70% of correct answers land on option B, 0% on D. Always audit distribution with `bank.forEach(q => d[q.correct]++)` and rotate if any option exceeds 35%. Apply circular shift to both options AND correct index.
- **No feedback until end**: users learn more from immediate per-question feedback. Always show explanation right after selection.
- **No persistence**: results vanish on refresh without localStorage auto-save. Always save automatically.
- **PDF via popup only**: some browsers block popups. Offer JSON as fallback.
- **Answer keys in plaintext**: If you ship a single-file assessment app without obfuscation, students can view source and read `correct:0`. Always run the XOR+base64 pipeline before distribution. Verify with `grep 'correct:\\d' index.html` after build.
- **Mixed quote types break JS parsing**: When parsing JS object literals from Python, strings can use either `'` or `"` quotes (e.g., `"don't"` uses double quotes because the text contains an apostrophe). The parser must handle both, plus escaped quotes (`'I\\'ve'`). A string-unaware bracket-depth counter will miscount — always track string state (`in_single`, `in_double`) when counting `{`/`[` depth.
- **REINFORCE data also needs protection**: Explanations and practice variants should be obfuscated too. They're not answer keys but make the source cleaner and prevent casual content scraping. Use the same base64 approach (no XOR needed unless sensitive).

## Verification Checklist

- [ ] All 4 skills represented in question selection
- [ ] Reinforcement panel appears after each answer
- [ ] Theme toggle persists across refresh
- [ ] Font controls can both increase and decrease
- [ ] Results auto-save to localStorage
- [ ] JSON download produces valid file
- [ ] PDF export opens print dialog
- [ ] No niche/legal content in general-audience questions
- [ ] Answer-key obfuscation applied (grep `correct:\d` returns 0 matches outside CSS)
- [ ] Reinforcement/study content also obfuscated (not readable in plain source)
- [ ] Works at all 3 question counts (20/40/60)
