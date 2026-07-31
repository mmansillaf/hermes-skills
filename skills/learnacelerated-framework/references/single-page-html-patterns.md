# Single-Page HTML App Build Patterns

Discovered while building the learnacelerated web app (Jul 2026).

## Critical: `<script>` in JS template literals

**Problem**: Putting literal `</script>` inside a JavaScript template literal that lives inside a `<script>...</script>` block causes the HTML parser to interpret it as closing the parent script block. The JS breaks silently (the rest of the script is treated as HTML).

**Fix**: Never embed `<script>` tags as string content inside JS template literals in an HTML file. Instead:
- Use a post-render initialization function that runs after `innerHTML` is set
- Expose toggle/copy functions via `window._name = fn` so `onclick` attributes work
- Add event listeners in JS (`addEventListener`) instead of inline `onclick` HTML attributes where possible

## Scope: IIFE + window._ exports

**Problem**: Functions defined inside a `DOMContentLoaded` callback or inside an IIFE are not accessible from inline `onclick` attributes in HTML.

**Fix**: Wrap everything in an IIFE to avoid global pollution, then explicitly expose only what's needed:

```js
(function() {
'use strict';

function showModule(idx) { ... }
function toggleItem(mId, li) { ... }
function copyPrompt(id) { ... }

window._show = showModule;
window._toggle = toggleItem;
window._copy = copyPrompt;

document.addEventListener('DOMContentLoaded', function() {
  // initialization here, using addEventListener not onclick
  document.getElementById('start-btn').addEventListener('click', startLearning);
});
})();
```

## Post-render initialization pattern

When generating HTML from JS template literals (innerHTML), embedded `<script>` tags don't execute. Use this pattern instead:

1. Generate all HTML content via template literals
2. Set `container.innerHTML = html`
3. Call `initChecks()` afterward to restore state from localStorage and update UI

```js
function renderModules() {
  // Build all HTML
  container.innerHTML = html;
  // Post-render hook
  initChecks();
}
```

## Checklist persistence (localStorage)

For single-file apps without a backend:
- Store the full state object as JSON in localStorage under a single key
- On page load, check for saved state to restore progress
- Save on every state change (toggle, navigation)

```js
var state = { topic: '', currentModule: 0, completed: {}, checks: {} };
function save() { localStorage.setItem('appState', JSON.stringify(state)); }
function load() {
  var s = localStorage.getItem('appState');
  if (s) { state = JSON.parse(s); return true; }
  return false;
}
```

## Template literal escaping

When building HTML strings inside JS template literals:
- Use `\n` for newlines (not literal newlines inside template strings that span many lines — those work but can be confusing)
- Use `'&apos;'` or HTML entities to avoid quote conflicts in `data-` attributes
- Escape backticks if the template string contains backtick characters
- Never put `</script>` as literal text
