# Answer Key Obfuscation — Reference

## Problem

Single-page assessment apps embed `correct` answer indices in the QUESTION_BANK array. Anyone can open DevTools or view source and see `correct:0`, `correct:1`, `correct:2`, `correct:3` in plaintext — trivial to cheat. Reinforcement/study content (recommendations, next steps) should also not be readable in plain source.

## Solution

Use a local Python pipeline to:
1. Parse the JS array literal from the HTML
2. XOR each `correct` value with a secret byte key
3. Serialize to JSON, base64-encode
4. Inject inline decode functions using only `atob()` + `JSON.parse()` — no `eval`, no `new Function()`
5. Repeat for reinforcement data (steps/recommendation dicts)

## Pipeline

### Step 1: Parse JS object literals from HTML

```python
import base64, json, re

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Find array bounds
qb_start_match = re.search(r'const QUESTION_BANK\s*=\s*\[', html)
start_pos = qb_start_match.end()
qb_end_match = re.search(r'\];\s*\n', html[start_pos:])
end_pos = start_pos + qb_end_match.start() + 2

qb_raw = html[qb_start_match.start():end_pos]
arr_body = qb_raw[qb_raw.index('[')+1 : qb_raw.rindex(']')]

# Extract each { ... } object with proper string-awareness
objs_text = []
depth = 0
obj_start = -1
in_str = False
str_ch = None
esc = False

for i, ch in enumerate(arr_body):
    if esc:
        esc = False
        continue
    if in_str:
        if ch == '\\':
            esc = True
        elif ch == str_ch:
            in_str = False
        continue
    if ch in ('"', "'"):
        in_str = True; str_ch = ch
        continue
    if ch == '{':
        if depth == 0:
            obj_start = i
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0 and obj_start >= 0:
            objs_text.append(arr_body[obj_start:i+1])
            obj_start = -1
```

### Step 2: Convert JS objects to Python dicts

Parse each object literal manually (ast.literal_eval won't handle JS syntax). Key-value parser must handle:
- Nested arrays for `options`
- Escaped quotes (`\\"`, `\\'`)
- Unicode/emoji in strings
- Mixed quote styles (`'` or `"`)

See the `js_obj_to_dict()` function in the session transcript — it processes colon-separated pairs, splits on top-level commas (not inside strings/arrays), and handles types: string, int, array-of-strings, boolean.

### Step 3: XOR + base64 encode

**Option A — single-byte XOR** (simpler, weaker):

```python
XOR_KEY = 0xAB  # Single byte — any value 0x01..0xFE works

encoded_questions = []
for q in questions:
    eq = dict(q)
    eq['c'] = eq.pop('correct') ^ XOR_KEY  # rename field for transport
    encoded_questions.append(eq)

full_json = json.dumps(encoded_questions, separators=(',', ':'), ensure_ascii=False)
encoded_b64 = base64.b64encode(full_json.encode('utf-8')).decode('ascii')
```

**Option B — multi-byte XOR key** (recommended, stronger):

```python
import secrets

XOR_KEY = secrets.token_hex(4)  # e.g. "a3f8c2d1" — 4 bytes, 8 hex chars

def xor_encode(data_str: str, key: str) -> str:
    """XOR-encrypt a string with a multi-byte key, return base64."""
    encoded = bytes(data_str, 'utf-8')
    k = key.encode('utf-8')
    xored = bytes(encoded[i] ^ k[i % len(k)] for i in range(len(encoded)))
    return base64.b64encode(xored).decode('ascii')

# Encode correct values BEFORE JSON serialization
for q in questions:
    q['correct'] = xor_encode(str(q['correct']), XOR_KEY)

full_json = json.dumps(questions, separators=(',', ':'), ensure_ascii=False)
encoded_b64 = base64.b64encode(full_json.encode('utf-8')).decode('ascii')
```

Multi-byte XOR is harder to brute-force: a single-byte key has only 255 possibilities to test; a 4-byte hex key has 2^32. The key is still visible in the JS source, so this is still obfuscation, but it adds meaningful friction.

### Step 4: Replace with obfuscated JS in HTML

**Option A — single-byte key:**

Replace original array definition with:

```js
const $k=0xAB;
function $d(s){
  try{
    var r=atob(s),j=JSON.parse(r);
    for(var i=0;i<j.length;i++){
      if(j[i].c!==undefined) j[i].correct=j[i].c^$k;
      delete j[i].c
    }
    return j
  }catch(e){return[]}
}
const QUESTION_BANK=$d("// base64 blob here");
```

**Option B — multi-byte key:** (runtime decoder must match the Python encoder):

```js
// Multi-byte XOR decoder
var _K='a3f8c2d1';
function _X(s){
  var d=atob(s),r='';
  for(var i=0;i<d.length;i++)
    r+=String.fromCharCode(d.charCodeAt(i)^_K.charCodeAt(i%_K.length));
  return r
}

// QB: correct values XOR-encoded inside JSON → decode on parse
var QB=JSON.parse(atob("// base64 blob here"))
  .map(function(q){q.correct=parseInt(_X(q.correct));return q});

// REINFORCE / steps data: entire object base64-encoded (no XOR needed for study content)
var REINFORCE=JSON.parse(atob("// base64 blob here"));
```

### Step 4b: Obfuscate reinforcement/study content (Python)

Parse the REINFORCE object literal from HTML using the same string-aware approach as Step 1, then encode:

```python
# Parse REINFORCE entries: each is 'KEY': {exp:'...', vars:['...','...']}
reinforce_entries = re.findall(
    r"'([^']+)'\s*:\s*\{([\s\S]*?)\}(?=\s*[,}])", rf_body
)
reinforce = {}
for key, val_body in reinforce_entries:
    exp_m = re.search(r"exp\s*:\s*'((?:[^'\\]|\\.)*)'", val_body)
    vars_arr = re.findall(r"'((?:[^'\\]|\\.)*)'",
        re.search(r"vars\s*:\s*\[([^\]]*)\]", val_body).group(1)
        if re.search(r"vars\s*:\s*\[([^\]]*)\]", val_body) else '')
    reinforce[key] = {'exp': exp_m.group(1) if exp_m else '',
                       'vars': vars_arr}

reinforce_json = json.dumps(reinforce, ensure_ascii=False, indent=None)
reinforce_b64 = base64.b64encode(reinforce_json.encode('utf-8')).decode('ascii')

# Replace in HTML
html = html.replace(
    'const REINFORCE = ' + original_object_literal + ';',
    f"var REINFORCE=JSON.parse(atob('{reinforce_b64}'));"
)
```

### Step 5: Verify in browser

```js
// Check bank loads correctly
QUESTION_BANK.length
QUESTION_BANK[0].correct  // should be the original int, not XORed

// Check no plaintext correct:N in source
document.querySelector('script').innerText.match(/correct:\d/g)
// → null or empty
```

## Constraints / Pitfalls

- **No `eval()` / `new Function()`**: These trigger CSP violations and are security red flags. `atob()` + `JSON.parse()` use only standard browser APIs.
- **No external dependencies**: The pipeline runs entirely in Python (standard library) and the decode runs in the browser with no imports.
- **Double-encoding pitfall**: The JSON is base64-encoded, but the `correct` values are XORed BEFORE serialization, so even base64-decoded text doesn't reveal the numbers.
- **XOR key storage**: The key is a `const` in JS source. It's not "secure" against a determined attacker (they can read the key and run the decode manually), but it stops casual inspection and Ctrl+F cheaters. This is obfuscation, not encryption.
- **CSP compliance**: `atob()` is a built-in — no `unsafe-eval` directive needed.
- **Steps data**: Obfuscate recommendation/study content the same way — it's not sensitive like answers, but it keeps the source clean and discourages copying.
- **Function/var naming**: Use short, non-descriptive names like `$d`, `$s`, `$k` to make manual inspection slightly harder. Avoid names like `_decodeAnswers`, `_xorKey`.

## When Not to Use

- If the app has a server backend, store answer keys server-side and serve via API. Client-side obfuscation is only for fully offline / single-file apps.
- If you need real security (e.g., paid exam), use server-side validation. This technique only prevents casual cheating.
