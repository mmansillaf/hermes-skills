# Obfuscation Recovery — Fixing Corrupted HTML After Build

When the XOR+base64 obfuscation pipeline produces a corrupted file (JS crashes, QB undefined, wrong balance), follow this recovery approach instead of incrementally patching.

## Symptoms of Corruption

| Symptom | Likely Cause |
|---------|-------------|
| `const` redeclaration error (QB undefined) | Old inline array NOT fully removed before decoder injected |
| Brace/paren imbalance | Decoder cleanup removed closing brackets from legitimate functions |
| REINFORCE returns question data instead of explanations | Same base64 blob reused for both QB and REINFORCE |
| `atob()` fails mid-string | Base64 truncated by partial read/write |
| Functions missing after cleanup | Filter removed legitimate `})();` closures (initParticles, IIFEs) |

## Recovery Strategy

### Step 1: Extract surviving base64 blobs

Even if the JS is broken, the base64 strings embedded in the file are likely still valid:

```bash
grep -oP "atob\('([A-Za-z0-9+/=]+)'\)" corrupted.html | head -3
```

Or in Python:

```python
import re, base64, json

with open("corrupted.html") as f:
    content = f.read()

b64_strings = re.findall(r"atob\('([A-Za-z0-9+/=]+)'\)", content)
# Also check for JSON.parse(atob('...'))
b64_strings += re.findall(r"JSON\.parse\(atob\('([A-Za-z0-9+/=]+)'\)\)", content)

# Verify each blob
for i, b64 in enumerate(set(b64_strings)):
    try:
        data = json.loads(base64.b64decode(b64))
        print(f"Blob {i}: {len(data)} items → valid")
        # Check if it's QB data or REINFORCE data
        if isinstance(data, list) and len(data) > 10 and 'i' in data[0]:
            print(f"  → QB data ({len(data)} questions)")
        elif isinstance(data, dict) and len(data) > 10:
            print(f"  → REINFORCE data ({len(data)} entries)")
    except Exception as e:
        print(f"Blob {i}: INVALID — {e}")
```

### Step 2: Identify which base64 is which

- **QB data**: A JSON array where each item has keys `i` (id), `s` (skill), `d` (diff), `t` (text), `o` (options), `c` (XORed correct)
- **REINFORCE data**: A JSON object where keys are question IDs and values have `e` (explanation) and `v` (variants array)

### Step 3: Rebuild from fresh scaffold

Don't keep patching the broken file. Instead:

1. Start with a known-good HTML scaffold (CSS + HTML structure, empty `<script>`)
2. Inject ONLY the decoder + the clean JS body
3. The clean JS body = the original functions (renderQ, showResults, etc.) — **without** any decoder artifacts

```python
# Build decoder with verified blobs
decoder = f"""
const $k = {XOR_KEY};
function $d(s) {{
  try {{
    var r = atob(s), j = JSON.parse(r);
    for (var i = 0; i < j.length; i++)
      if (j[i].c !== undefined) j[i].correct = j[i].c ^ $k;
    return j;
  }} catch(e) {{ return []; }}
}}
const QB = $d("{b64_qb}");
const REINFORCE = JSON.parse(atob("{b64_rf}"));
"""

# Combine with clean JS body
new_script = decoder + clean_js_body
```

### Step 4: Verify before writing

```python
# Balance check
ob = new_script.count('{')
cb = new_script.count('}')
op = new_script.count('(')
cp = new_script.count(')')
assert ob == cb, f"Braces: {ob}/{cb}"
assert op == cp, f"Parens: {op}/{cp}"

# No plaintext correct:N
import re
assert not re.findall(r'correct:\d+', decoder), "correct:N leaked in decoder"

# Count function definitions
func_count = len(re.findall(r'^function (\w+)\(', new_script, re.MULTILINE))
print(f"Functions: {func_count}")
```

### Step 5: Browser verification

1. Open the rebuilt HTML in browser
2. Run `typeof QB, typeof REINFORCE` — both should be defined
3. Run `QB.length` — should match original question count
4. Click through a quiz — render, answer, results should all work
5. Check `localStorage` persistence for results

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Keeping old `const QB = [...]` alongside decoder | Remove the old INLINE array completely |
| REINFORCE b64 same as QB b64 | Generate a SEPARATE base64 from the REINFORCE data |
| Cleanup removed `})()` from legit IIFEs | Use prefix matching, not substring — `})()` matches everywhere |
| Multiple `function` definitions with same name | Remove the first (v1) version, keep the v2 version |
| Wrong key for XOR decode | The XOR key in the decoder must match the key used at encode time |
