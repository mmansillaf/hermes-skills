---
name: html-edu-apps
description: Build interactive self-contained HTML/CSS/JS single-page educational apps — placement tests, quizzes, assessments with adaptive logic, accessibility controls, answer obfuscation, and data export.
---

# HTML Educational Apps

Build interactive HTML/CSS/JS single-page educational apps (assessment tests, quizzes, placement exams) that are fully self-contained (no backend, no API calls).

## When to use

- User asks for a web-based quiz, test, assessment, or exam as a single HTML file
- Needs adaptive/dynamic question selection
- Needs results to persist or be exportable
- Educational content with answer keys that should not be visible in source
- Must work offline — no backend, no API calls

## Key patterns

### 1. Question Bank with Offuscated Answers

Never store `correct: 0/1/2/3` in plain text in the HTML source. Use base64 + XOR:

```javascript
// Encode (build-time):
// For each question: q.c = originalCorrect ^ XOR_KEY
// Serialize to JSON → base64 → embed in HTML

// Decode (runtime):
const $k = K; // XOR key (e.g. 0xAB = 171)
function $d(s) {
  try {
    var r = atob(s), j = JSON.parse(r);
    for (var i = 0; i < j.length; i++)
      if (j[i].c !== undefined) { j[i].correct = j[i].c ^ $k; delete j[i].c; }
    return j;
  } catch(e) { return []; }
}
const QUESTION_BANK = $d("ENCODED_BASE64_STRING");
```

**Pitfalls**:
- `const` redeclaration = crash. Ensure decoder runs only once.
- Base64 of REINFORCE data must be a **different blob** from QB base64, or the decode function returns questions as "reinforcement data".
- Template literals (backticks `` ` ``) in JS will break heredoc-based Python scripts. Use string concatenation or escape them.
- Validar que el base64 decodifica antes de escribir al archivo.

### 2. Answer Distribution Balancing

**Never** let correct answers cluster on one option. Track distribution:

```javascript
var d = {0:0, 1:0, 2:0, 3:0};
QUESTION_BANK.forEach(function(q) { d[q.correct]++; });
```

Target: each option ~25% (±2%). If off, rotate options/correct by cycling `i % 4`:

```python
# Rotation: shift options[-rot:] + options[:-rot], correct = (correct + rot) % 4
for i in range(len(questions)):
    questions[i].options = questions[i].options[-rot[i]:] + questions[i].options[:-rot[i]]
    questions[i].correct = (questions[i].correct + rot[i]) % 4
```

### 3. Accessibility Controls

Always include:
- **Font size**: A− (shrink) / indicator (100%) / A+ (grow). 4 sizes: 12px/16px/20px/24px. Persist to localStorage.
- **Dark/Light theme**: Store in localStorage, apply `data-theme` attribute on `<html>`.
- Implement via `fontShrink()` / `fontGrow()` / `toggleTheme()` functions.

### 4. Adaptive Question Selection

Distribute questions evenly across 4 skills (grammar, vocab, reading, listening):

```javascript
function pickQuestions(count) {
  var per = Math.floor(count / 4), extra = count % 4;
  var skills = ["grammar","vocab","reading","listening"];
  // Per-skill pool, shuffle, take needed count
  // Then interleave: sort by difficulty, group in blocks of 4, shuffle each block
}
```

### 5. Post-Answer Reinforcement

After each answer, show a panel with:
- ✓/✗ icon (green/red)
- Explanation of the concept
- 3 variant examples of the same pattern

Use a `REINFORCE` map keyed by question ID, or fallback to a `defaultReinforce()` that generates generic content by skill type.

### 6. Results Persistence & Export

- Auto-save to `localStorage` (keep last 20 tests)
- Export JSON button → Blob download
- Export PDF button → open print-friendly HTML in new window → `window.print()`

## References

See `references/offuscation-pitfalls.md` — troubleshooting guide for the base64+XOR obfuscation approach.

## Verification checklist

- [ ] No `correct:N` in plain text (search HTML for pattern)
- [ ] Answer distribution is ~25% per option
- [ ] Font size controls work (A−/A+ change `data-font` on `<html>`)
- [ ] Theme toggle persists across reload
- [ ] Questions are balanced across grammar/vocab/reading/listening
- [ ] Post-answer reinforcement panel shows after selection
- [ ] Results save to localStorage and export buttons work
- [ ] No `correct:N` in plain text source (0 instances, save runtime vars)
