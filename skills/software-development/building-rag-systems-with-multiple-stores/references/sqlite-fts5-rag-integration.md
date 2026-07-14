# SQLite FTS5 Integration for RAG Systems

## Trigger conditions
- Replacing LIKE-based SQLite search with FTS5 full-text search
- FTS5 returning 0 results when you expect matches
- Need to normalize FTS5 BM25 scores to 0-1 relevance
- TEXT primary key causing FTS5 `content_rowid` failures

## Core pattern: FTS5 with OR for bag-of-words search

FTS5 `MATCH` uses **AND by default**. Passing a multi-word query like `"contrataciones del estado OSCE"` requires ALL terms to appear in the same document. For RAG search where any term match is useful, use explicit OR:

```python
import re
# Tokenize and build OR query (max 20 terms)
q_clean = re.sub(r'[^\w\s]', ' ', question)
tokens = [w for w in q_clean.lower().split() if len(w) >= 2]
fts_match = " OR ".join(tokens[:20])

rows = db.execute("""
    SELECT n.*, fts.rank
    FROM normas_fts fts
    JOIN normas n ON n.rowid = fts.rowid
    WHERE normas_fts MATCH ?
    ORDER BY fts.rank
    LIMIT ?
""", (fts_match, limit)).fetchall()
```

## FTS5 table creation

```python
# Use tokenize='unicode61 remove_diacritics 2' for Spanish/Portuguese
# 'remove_diacritics' normalizes accented chars (á→a, ñ→n)
# '2' = minimum token length of 2 chars
db.execute("""
    CREATE VIRTUAL TABLE normas_fts USING fts5(
        sumilla, titulo, materia, numero, emisor,
        tokenize='unicode61 remove_diacritics 2'
    )
""")

# Populate using ROWID (internal integer, always works)
db.execute("""
    INSERT INTO normas_fts(rowid, sumilla, titulo, materia, numero, emisor)
    SELECT rowid, sumilla, titulo, materia, numero, emisor FROM normas
""")
db.commit()
```

## BM25 score normalization

FTS5 `rank` returns **negative** BM25 scores. Lower (more negative) = better match. Normalize to 0-1 relevance scale:

```python
# Extract and convert BM25 ranks
raw_ranks = [abs(r['rank']) for r in rows]  # abs() makes them positive
if raw_ranks:
    min_rank = min(raw_ranks)  # Best match (smallest abs value)
    max_rank = max(raw_ranks)  # Worst match (largest abs value)
    rank_range = max_rank - min_rank if max_rank > min_rank else 1
else:
    min_rank, max_rank, rank_range = 1, 1, 1

for r in rows:
    # Linear normalization: best match → 1.0, worst → ~0.0
    r['relevance'] = round(1.0 - (abs(r['rank']) - min_rank) / rank_range, 4)
```

This maps rank -5 → 1.0 and rank -15 → ~0.1, creating a usable relevance distribution.

```python
raw_ranks = [abs(r['rank']) for r in rows]
min_rank = min(raw_ranks)
max_rank = max(raw_ranks)
rank_range = max_rank - min_rank if max_rank > min_rank else 1

for r in rows:
    r['relevance'] = round(1.0 - (abs(r['rank']) - min_rank) / rank_range, 4)
```

## Pitfalls

### Pitfall 1: MATCH uses AND by default
**Symptom:** FTS5 returns 0 results for multi-word queries when individual words DO exist.
**Fix:** Build explicit `"term1 OR term2 OR term3"` query string.

### Pitfall 2: content_rowid requires INTEGER
**Symptom:** `IntegrityError: datatype mismatch` when using `content='normas', content_rowid='id'` if `id` is TEXT.
**Fix:** Don't use `content=`/`content_rowid=`. Use `rowid` (SQLite's internal integer) and JOIN manually.

### Pitfall 3: FTS5 rank is negative
**Symptom:** All relevance scores are negative or look inverted.
**Fix:** Use `abs(rank)` and normalize across the result set range.

### Pitfall 4: LIKE fallback still needed
**Symptom:** FTS5 may fail on queries with only stop words or special characters.
**Fix:** Wrap FTS5 in try/except with LIKE fallback using parametrized queries.

```python
try:
    # FTS5 search
    ...
except Exception as e:
    logger.warning(f"FTS5 fallback: {e}")
    # LIKE-based fallback
    terms = [w for w in question.lower().split() if len(w) >= 3][:10]
    ...
```

### Pitfall 5: `remove_diacritics` is case-sensitive on output
**Symptom:** Queries with uppercase accented chars don't match.
**Fix:** Always lowercase the query before tokenization. FTS5 tokenizer handles the rest.

## When FTS5 is better than LIKE

- **Speed:** BM25 ranking is faster than manual CASE-WHEN across 5 columns
- **Relevance:** BM25 is TF-IDF based, better than arbitrary weight assignment
- **Stemming:** `remove_diacritics` handles accent normalization automatically
- **Security:** Parametrized `MATCH ?` vs SQL injection via LIKE string concatenation
- **Scaling:** FTS5 uses inverted indexes, O(log n) vs LIKE O(n)