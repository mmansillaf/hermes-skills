# SQLite Persistence Hook Pattern

## Problem
Adding a database to an existing Python project without refactoring the entire codebase. The system already saves files and uses in-memory caches. Need persistence without touching existing function signatures.

## Solution: Hook pattern with lazy imports

Add persistence hooks BEFORE and AFTER existing operations using try/except blocks with lazy imports. The DB is optional -- if it fails, the system degrades gracefully.

## Architecture

src/database.py (NEW): all SQLite CRUD functions
src/existing.py (MODIFIED): add hooks at entry/exit points

## database.py structure (no classes, pure functions)

_WRITE_LOCK = threading.RLock()  # RLock, NOT Lock (see deadlock pitfall)

def init_db(path="data.db") -> Connection:  # auto-creates tables
def save_video(url, title="", ...) -> int: ...
def get_or_create_speaker(name, aliases=[]) -> int: ...
def save_claim(claim, speaker_id, video_id) -> tuple[int, bool]: ...
def save_verification(claim_id, result) -> int: ...
def cache_get(query, engine="ddgs") -> list[dict] | None: ...
def cache_set(query, engine, results, ttl_days=7): ...

## Hook placement

BEFORE (check cache / dedup):
  try: from .database import cache_get; cached = cache_get(query)
  except: pass  # DB unavailable

AFTER (save results):
  try: from .database import save_claim; save_claim(claim)
  except: pass  # non-critical

## Key patterns

1. Dedup by hash: SHA256(lowercase(normalized_text))
2. Upsert: INSERT ... ON CONFLICT(col) DO UPDATE SET ...
3. Cache TTL: expires_at column, check against datetime('now')
4. Speaker score: Recalculate on each new verification
5. Auto-init: init_db() called at startup, no manual setup

## Pitfalls

- DEADLOCK: threading.Lock blocks if function A acquires lock then calls function B that also acquires lock. Use threading.RLock().
- AUTOINCREMENT: SQLite creates hidden sqlite_sequence table. Don't count tables -- check names.
- DUAL CACHE: Keep in-memory cache as fallback. SQLite checked first.
- IMPORT IN TRY: from .database import X inside the hook so missing module doesn't crash.
- GITIGNORE: Add *.db to .gitignore. Never commit the database file.
