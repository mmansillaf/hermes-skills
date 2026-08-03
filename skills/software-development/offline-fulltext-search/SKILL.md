---
name: offline-fulltext-search
description: Offline full-text search over JSON corpora (static HTML+JS).
---

# Offline full-text search (static HTML + JS over file://)

Pattern for turning a local JSON corpus (court rulings, normas, articles) into a
searchable static site that works by double-clicking index.html — no server.

## Architecture (proven shape)
- `generar_*.py` reads the corpus ONCE, enriches each doc (regex-extracted fields),
  writes per-doc HTML + two data files, then you `cp` the lot into place.
- `datos.js`  → `window.CASOS = [[num, tipo, distrito, ..., resumen], ...]` (per-doc metadata + snippet)
- `indice.js` → `window.INDICE = { token: "delta-encoded-postings", ... }` (inverted index)
- `index.html` loads both via `<script src>` and filters in memory. No fetch().

## Critical pitfalls (each one cost a debug cycle — read before building)
1. **file:// blocks fetch()** (CORS). Only `<script src="datos.js">` works with double-click.
   Never design the UI around fetch/XMLHttpRequest for offline use.
2. **Python (index build) and JS (query) MUST share the identical stopword list and
   stemmer.** Classic bug: "abuso del derecho" → tokens [abuso, del, derecho], but "del"
   was filtered in Python and absent from INDICE → AND intersection with empty set = 0 results.
   Ship the SAME literal stopword string in both, or filter in JS exactly like Python.
3. **Sinónimos must join the term's own OR-set, never be added as extra AND conjuntos.**
   "pension NOT onp" broke because sinónimo expansion of "pension" added "onp" as a
   mandatory AND conjunto → pension AND onp AND NOT onp = empty. Merge synonyms into
   `expandirTermino()`'s posting union.
4. **Categorical fields need exact match, not `includes`.** `fallo:fundada` matched
   "INFUNDADA" because "infundada".contains("fundada"). Exact-compare enum fields.
5. **Field-value parser: greedy regex eats the next field.** `fallo:fundada derecho:pension`
   captured "fundada derecho" as the fallo value. Value must terminate at the next
   `word:` token: `(campo):([^\s:]+(?:\s+(?!\w+:)[\w-]+)*)`.
6. **Phrase search `"..."` without positions:** make the phrase's tokens participate in the
   AND (so results aren't empty), and only use exact-phrase match as a ranking boost.
   A posting-list index has no positions; don't try to hard-filter on it.
7. **Query-less state must render the full list** — when input empties, restore the
   grouped-by-date list; don't leave a stale "0 results" screen.
8. **Placeholder promises = searchable fields.** User's #1 complaint: placeholder said
   "buscar por distrito o demandante" but links only carried data-t/data-n → those searches
   returned 0. Every field named in the placeholder must be in the indexed data attributes.
9. **WSL/NTFS is brutal for many small files** (~64 writes/s to /mnt/d). Generate into
   /tmp (ext4) then `cp -r` once (~42 s for 8.8K files). Never write 8K files one-by-one
   to a Windows mount from Python.
10. **Dirty source fields:** scrape JSON often has mis-mapped values (distrito = "DEMANDANTE").
    Recover from text regex (e.g. "CORTE SUPERIOR DE JUSTICIA DE X" / city in date line)
    and `.upper()`-normalize so variants merge. Report residual counts honestly.
11. **Blacklist is NOT enough for dirty fields — use a WHITELIST.** The scraper stored
    header labels (JUEZ 299×, ESPECIALISTA 42×) AND person names (MAXIMILIANO ECHACCAYA)
    in the distrito field. A blacklist always misses the next invented label. Robust
    3-layer pattern: (a) blacklist of known labels, (b) WHITELIST of real domain values
    (~60 Peruvian judicial districts), (c) text recovery. Rule: a field is accepted ONLY
    if it's in the whitelist; otherwise recover from text AND validate that recovery
    against the whitelist too. Result: 252 values → 42 real ones, 0 junk.
12. **Date-fallback regex must accept month with capital** — "Ayacucho, 14 de Abril"
    didn't match `de [a-z]+` (lowercase-only), so recovery failed and the dirty field
    leaked through. Use `[A-Za-záéíóúñü]+`.
13. **Per-doc HTML must use the CLEANED field, not the raw dict.** If you compute
    `dist = extraer_distrito(...)` for datos.js but never do `d['distrito'] = dist`
    before `generar_caso(d)`, the HTML shows the raw value (datos.js said AYACUCHO,
    the HTML said JUEZ). Re-assign every cleaned field back into the dict. Test BOTH
    outputs — check a real HTML file on disk, not just datos.js.
14. **Header-field extraction: search only the first ~500 chars.** Scanning the whole
    text for "DEMANDADO"/"JUEZ" catches BODY mentions ("...demandado: JUEZ DEL JUZGADO
    ... INDEBIDAMENTE A LA ONP"). The diario header lives at the start; use `texto[:500]`.
15. **TDD: keep the generator importable.** Wrap the main loop in
    `if __name__ == "__main__":` so tests can import the module (importlib.util) and
    call extraction functions without re-running all 8,794 docs (importing the module
    without the guard hangs 120s+). Write tests RED-first for each extraction regex.
16. **rsync STAGE→OUT must NOT use `--delete`.** If STAGE holds only generated artifacts
    (casos/, datos.js, indice.js) but OUT also has project files (index.html,
    generar_*.py, SPEC, tests), `rsync -a --delete` DELETES them. Use plain `rsync -a`.
    (Learned the hard way: lost index.html + generator + tests mid-session.)
17. **`input type="date"` only fires 'change' when the picker closes** — typing gives no
    feedback. Listen to BOTH 'input' and 'change' with ~300ms debounce, plus render a
    visible range badge ("📅 2021-01-01 → hoy ✕") so the applied filter is obvious.
18. **Sort-select listener must call `buscar()`, not `pintarResultados()`.** The sort
    only runs inside buscar(); re-painting without re-searching reorders nothing.
    Same for any control that changes filter semantics: route through buscar().

## Index design (Spanish corpus)
- `norm(s)` = lowercase + NFD strip accents. Store/compare normalized always.
- Tokens: `re.findall(r'[a-z0-9]{3,}')` minus stopwords, limit text window (12K chars/case).
- Stemming without a lib: index 3 key families — raw token, `5:`+first5 prefix, `s:`+stem
  (plural/suffix rules). Query expands a term into all three unions.
- Weight metadata: index `num+tipo+distrito+demandante+sentencia+fecha` tokens x3 → they
  outrank body matches in ranking.
- **Delta-encode postings** (postings are ascending): store `chr(33+delta-1)` per posting,
  `~<delta>~` for deltas >89. 25.7 MB → 15.3 MB. Decode lazily per token in JS (Map cache).
- Autocomplete: `Object.keys(INDICE).filter(k => !k.includes(':') && k.startsWith(prefix))`
  + show `getPostings(k).length` counts. Suggest real terms, not guesses.
- Search result snippet: find first token hit in the stored resumen, slice ±130 chars,
  wrap hits in `<mark>`.

## Verification (mandatory — user requires "prueba como persona")
Open `file://.../index.html` in the browser and exercise EACH feature for real:
- queries: phrase, NOT, OR, combined fields, accented vs unaccented, single word
- filters (tipo/año/fallo pills) alone and combined with text
- autocomplete dropdown appears with counts; Enter selects
- click a result → the per-doc HTML opens; `?q=` highlight marks appear
- dark-mode toggle persists (localStorage); print CSS hides nav
- export CSV/JSON produces a download
- check counts via browser_console against expected corpus stats
Fix anything that returns 0 or wrong-count before declaring done.

## Support files
- `scripts/encode_postings.py` — delta encode/decode for postings lists
- `references/tc-jurisprudencia-html-buscador.md` — worked example: Peru TC rulings
  (8,794 cases, El Peruano 2016-2021), extraction regexes, corpus quirks
- `references/tc-buscador-v3-v4-evolucion.md` — v3/v4 evolution: co-occurrence
  semantics (option A), prefixed field index (ley:/ds:/art:/demandado:), distrito
  whitelist fix (252→42 values), date/badge UX, pagination, TDD import guard, the
  rsync --delete incident
