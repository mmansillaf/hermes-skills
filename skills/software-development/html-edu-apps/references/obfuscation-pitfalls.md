# Offuscation Pitfalls — base64 + XOR for Answer Keys

## The core pattern

```javascript
// Build: store correct as (original ^ XOR_KEY), serialize to JSON, base64
// Runtime:
const $k = 171;
const QB = (function() {
  try {
    var _d = JSON.parse(atob("B64_STRING"));
    return _d.map(function(q) {
      return { id: q.i, skill: q.s, ..., correct: q.c ^ $k };
    });
  } catch(e) { return []; }
})();
```

## Pitfalls encountered

### 1. Const redeclaration
If you have TWO `const QB = ...` declarations (old inline array + new decoder), the script **crashes immediately** and nothing after it executes. `const` does not allow redeclaration.

**Fix**: Ensure exactly one `const QB = ` in the final file. Remove the old inline array entirely.

### 2. REINFORCE data corruption
If you encode both QB and REINFORCE to base64, ensure they are **different blobs**. Using the same base64 string for both means the decode function tries to read question objects as reinforcement data → runtime errors.

### 3. Template literals in heredoc scripts
When generating HTML via Python heredocs (`<< 'EOF'`), backticks `` ` `` in JS template literals will terminate the heredoc early.

**Fix**: Avoid backticks in inline JS. Use string concatenation, or write the JS to a file first, then inject.

### 4. Balance issues after concatenation
When combining JS from two sources (v1 decoder + v2 functions), brace/paren balance gets off. Always verify:

```python
ob = new_script.count('{')
cb = new_script.count('}')
op = new_script.count('(')
cp = new_script.count(')')
assert ob == cb and op == cp
```

### 5. Filtering out decoder lines too aggressively
When cleaning old decoder artifacts from a script:
- Use **prefix matching**, not substring matching
- `return _d` matches `return _d.map(...)` but NOT `return document.getElementById(...)`
- Be careful: `})();` appears in both decoder closures AND legitimate function IIFEs (like `initParticles`)

### 6. Double execution from IIFE + alias
If the decoder is an IIFE `(() => {...})()` and you also export `const QB = $d;`, make sure `$d` is the array (return value), not the IIFE again.

### 7. Browser console doesn't show all errors
When testing `file://` HTML files, some JS errors may not appear in `browser_console`. Test with:
```javascript
try { var result = riskyOperation(); } catch(e) { console.error("ERR:", e.message); }
```

## Fix strategy when file is corrupted

1. Extract base64 strings from the corrupted file (they're likely still valid)
2. Rebuild the HTML scaffold from a known-good template
3. Inject decoder + clean JS body (remove all decoder artifacts first)
4. Verify balance before writing
