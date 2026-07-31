# Legal Articles Corpus Expansion

## Use case
You have an existing RAG corpus with ~20 hand-curated legal articles, and you
need to expand it to 400+ articles from a public legal blog behind Cloudflare.

## Source: Wayback Machine archive of a WordPress legal blog

When the target site has Cloudflare (HTTP 403 "Just a moment..."), use
Wayback Machine to capture the page content:

```python
import urllib.request, re

url = "https://web.archive.org/web/2025*/https://lpderecho.pe/codigo-penal-peruano-actualizado/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20) as resp:
    html = resp.read().decode('utf-8', errors='replace')
```

Wayback Machine serves archived content without Cloudflare checks.
Expect 1.5–2M chars for a full legal code with 600+ articles.

## Artifacts to clean from a captured HTML

| Artifact | Pattern | Action |
|----------|---------|--------|
| Wayback links | `web.archive.org` (thousands) | Strip via regex after text extraction |
| "Ver jurisprudencia" links | `<p>Ver jurisprudencia <a...>aquí</a></p>` | Remove entire `<p>` block |
| Yellow highlights | `background-color: #ffff99` | Remove inline style only, keep text |
| LP Derecho copyright | `©`, `LP Derecho`, `Propiedad Intelectual` | Strip from cleaned text |
| Wayback toolbar/scripts | `<script>`, `<nav>`, `<header>`, `<iframe>` | Strip before text extraction |

## Cleaning pipeline

```python
import re, html as html_mod

# 1. Remove structural HTML
cleaned = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
cleaned = re.sub(r'<style[^>]*>.*?</style>', '', cleaned, flags=re.DOTALL)
cleaned = re.sub(r'<nav[^>]*>.*?</nav>', '', cleaned, flags=re.DOTALL)
cleaned = re.sub(r'<header[^>]*>.*?</header>', '', cleaned, flags=re.DOTALL)
cleaned = re.sub(r'<footer[^>]*>.*?</footer>', '', cleaned, flags=re.DOTALL)
cleaned = re.sub(r'<iframe[^>]*>.*?</iframe>', '', cleaned, flags=re.DOTALL)

# 2. Remove "Ver jurisprudencia" paragraphs
cleaned = re.sub(r'<p[^>]*>.*?Ver jurisprudencia.*?</p>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)

# 3. Convert block elements to newlines
cleaned = cleaned.replace('<br/>', '\n').replace('</p>', '\n')
cleaned = re.sub(r'</li>', '\n', cleaned)
cleaned = re.sub(r'<li>', '• ', cleaned)

# 4. Strip remaining tags
cleaned = re.sub(r'<[^>]+>', '', cleaned)
cleaned = html_mod.unescape(cleaned)

# 5. Remove Wayback URLs
cleaned = re.sub(r'https?://web\.archive\.org/web/[^/\s]+/[^\s)]+', '', cleaned)

# 6. Normalize whitespace
cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
cleaned = re.sub(r' {3,}', ' ', cleaned)
```

## Parsing legal articles into structured JSON

Legal blogs format articles consistently. The pattern for Peruvian CP:

```
Artículo N.- Título del Artículo
Texto del artículo en uno o más párrafos.

1. Primer inciso
2. Segundo inciso

Modificado por Ley N° 12345
```

### Parser approach

```python
articles = []
lines = cleaned.split('\n')
current_art = None
current_lines = []

for line in lines:
    m = re.match(
        r'Artículo\s+(\d+(?:[-\s][A-Z][a-z0-9]*)?)\s*[\.:]\s*(.*)',
        line.strip()
    )
    if m:
        if current_art:
            articles.append((current_art[0], current_art[1],
                            '\n'.join(current_lines).strip()))
        current_art = (m.group(1).strip(), m.group(2).strip().rstrip('* '))
        current_lines = []
    elif current_art:
        current_lines.append(line.strip())

# Don't forget last
if current_art:
    articles.append(...)
```

### Extracting incisos

```python
inc_matches = re.findall(r'^\s*(\d+|[a-z])[.)]\s+(.+)$', content, re.MULTILINE)
incisos = [{"numero": n, "texto": t.strip()} for n, t in inc_matches]
```

### Detecting modifications

```python
for pat, tipo in [
    (r'Modificado\s+(?:por|mediante)\s+(.+?)(?:\.|$)', 'modificacion'),
    (r'Incorporado\s+(?:por|mediante)\s+(.+?)(?:\.|$)', 'incorporacion'),
    (r'Derogado\s+(?:por|mediante)\s+(.+?)(?:\.|$)', 'derogacion'),
]:
    mod_m = re.search(pat, content, re.IGNORECASE)
    if mod_m:
        modificaciones.append({"tipo": tipo, "ley": mod_m.group(1).strip(), ...})
```

## Merging with existing corpus

When you already have ~20 curated articles with better metadata (vigencia
exacta, capítulos, modificaciones detalladas), merge by article ID or number:

```python
old_by_id = {a['id']: a for a in old_articles}

for new_art in new_articles:
    match = old_by_id.get(new_art['id'])
    if match:
        # Keep old metadata (better curated), update text if newer
        merged.append(match)
    else:
        merged.append(new_art)
```

Then deduplicate by `id` to catch any articles that appeared in both sets
with slightly different IDs (e.g. `art_108b` vs `art_108-b`).

## Rebuilding the FAISS index

After updating `codigo_penal.json`, regenerate the index:

```python
from app.services.embeddings import build_or_load_index
build_or_load_index(force_rebuild=True)
```

This re-encodes all articles with sentence-transformers and writes a new
`faiss_index.bin` + `faiss_metadata.json`. On CPU with ~630 articles and
multilingual-e5-large, expect ~10-15 minutes.

## Known pitfalls

- **Asterisks in titles**: LP Derecho marks some articles with `*`. Strip them:
  `title = title.rstrip('* ').strip()`
- **Leading dash in title**: The `.-` separator can leave a leading `-` in the
  title. Fix: `title = re.sub(r'^[–\-]\s*', '', title)`
- **Alphanumeric article numbers**: Some articles use letters (e.g. "108-B",
  "16-A", "438-A"). The regex must capture `\d+(?:[-\s][A-Z][a-z0-9]*)?`
- **In-text references**: "Artículo 2, incisos 2, 3, 4 y 5" is NOT a new article.
  Filter by checking if the captured title looks like a reference (< 5 chars,
  contains "incisos", starts with "del").
- **Libro III incompleto**: Wayback snapshots of legal blogs often cut off
  the last book (faltas/disposiciones finales). The CP has ~20 articles in
  Libro III but you may only get 1-2.
- **FAISS on CPU is slow**: 630 articles × multilingual-e5-large = 10-15 min.
  For faster iteration, test with a small subset first.
