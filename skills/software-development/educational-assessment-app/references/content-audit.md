# Content Audit for General-Audience Assessment

## Pre-shipping Audit

Before shipping an assessment to general audience, check for content that's too niche or domain-specific.

### Legal Keywords to Grep

```bash
grep -n 'court\|statute\|legal\|jurid\|counsel\|legislative\|travaux\|ruling\|clause\|liability\|compliance\|jurisdiction\|precedent\|judicial\|attorney\|plaintiff\|defendant' index.html
```

### Other Niche Signals

- Financial: `arbitrage|derivative|hedge|equity (not shares)|dividend yield`
- Medical: `diagnosis|prescription|pathology|contraindication|prognosis`
- Technical: `compiler|kernel|recursion|polymorphism|dependency injection`

### Fix Pattern

When replacing a niche question:
1. Keep the same `id` (so reinforcement DB entries still match)
2. Keep the same `skill` and `diff` tier
3. Replace `text`, `ctx`, `options[]`, and `correct`
4. Add a new `REINFORCE` entry with the new id

### Example Replacement

```js
// BEFORE (legal):
{ id:'V11', skill:'vocab', diff:3, text:'The contract is ___ to approval by the legal team.', correct:0 }

// AFTER (general):
{ id:'V11', skill:'vocab', diff:3, text:'It\'s important to ___ yourself before an important presentation.', correct:0 }
```
