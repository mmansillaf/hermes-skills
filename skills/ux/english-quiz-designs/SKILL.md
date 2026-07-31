---
name: english-quiz-designs
description: Three B1-B2 English quiz design variants with accessibility features and responsive patterns
tags: [ux, english, design]
related_skills: [popular-web-designs, sketch]
---
## 3 English Quiz Design Variants (B1-B2)

### 1. Sophisticada (Dark Mode Linear/Vercel Style)
```html
<div class='premium-grammar' style='background:#08090a; padding:20px; border-radius:8px'>
  <h3>Exercise: Future Tenses</h3>
  <form>
    <label>Choose correct form: I ____ dinner at 7pm tomorrow.
    <input type='text' size='10' /></label>
    <button type='submit'>Check</button>
  </form>
</div>
```

### 2. Innovative Glassmorphism
```html
<div class="glass-card" style="background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); margin:20px;">
  <h4>Vocabulary Builder</h4>
  <audio controls>
    <source src="audio.mp3" type="audio/mpeg">
  </audio>
</div>
```
### 3. Conservative Institutional
```html
<div class="access-card" role="region" aria-label="Grammar Exercise">
  <h2>Module 2: Verb Tenses</h2>
  <form>
    <label>Question: What is the past tense of 'teach'?
      <select>
        <option>taught</option>
        <option>teach</option>
      </select>
    </label>
  </form>
</div>
```

### Key Differences
| Style          | Color Scheme      | Accessibility Focus         |
|----------------|-------------------|------------------------------|
| Sophisticada     | Dark mode (#08090a) | High contrast text           |
| Innovative     | Glassmorphism       | Audio feedback              |
| Conservative   | Clean white         | ARIA roles for screen readers|