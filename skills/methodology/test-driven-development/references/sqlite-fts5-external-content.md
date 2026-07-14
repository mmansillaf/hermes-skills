# SQLite FTS5 External Content Table

## The Problem

SQLite FTS5 virtual tables created with `content='table_name'` (external
content tables) do NOT automatically sync with the source table. Data
INSERTed into the source table is invisible to FTS5 searches until the
index is rebuilt.

## The Symptoms

- `search_keyword()` always returns empty results
- FTS5 queries match nothing despite data being in the source table
- ChromaDB vector search works fine, but keyword search is dead

## The Fix

After INSERTing/UPDATEing/DELETing rows in the source table, rebuild the
FTS5 index on the SAME database connection (not a new one):

```python
conn = self._get_sqlite()
# ... insert rows into chunks table ...
conn.commit()

# Rebuild FTS5 index — SAME connection, SAME transaction scope
conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
conn.commit()
conn.close()
```

## Critical Detail

The rebuild MUST happen on the same connection that performed the writes.
If you close the connection and open a new one for the rebuild, WAL mode
may not have flushed and the rebuild operates on stale data.

## Schema Declaration

When declaring the FTS5 virtual table, the `content='table'` and
`content_rowid='rowid'` parameters link it:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
USING fts5(
    content, doc_name, section, sub_section,
    content='chunks',         -- source table name
    content_rowid='rowid'     -- source table rowid column
);
```

## Test Pattern

A characterization test that catches this bug:

```python
def test_fts_rebuild_after_insert(self, vector_store):
    vector_store.add_document("t1", "test.pdf", "hash1", 1)
    chunk = Chunk(doc_id="t1", content="unique_term_xyz")
    vector_store.add_chunks([chunk], [dummy_embedding()])

    results = vector_store.search_keyword("unique_term_xyz")

    assert len(results) >= 1  # Fails if rebuild is missing
```

## Cause

SQLite's FTS5 external content table does NOT automatically maintain a
trigger on the source table. It relies on either:
1. An explicit `INSERT INTO fts_table(fts_table) VALUES('rebuild')`
2. Application-level triggers created by the developer

Most developers assume it auto-syncs. It does not.
