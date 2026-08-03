# SQLite / state.db Health Check — recipe and expected output

## Context (WSL, Hermes)

- `~/.hermes/state.db` = full conversation history (can be 500-600MB), FTS5-indexed for `session_search`.
- Ubuntu 24.04 ships SQLite 3.45.1 which has the WAL-reset corruption bug; Hermes was fixed by compiling 3.51.3 to `~/.hermes/lib/libsqlite3.so` and LD_PRELOAD-ing it in `~/.local/bin/hermes`. Verify with `ls ~/.hermes/lib/`.

## Read-only check (safe while Hermes is running)

```bash
export LD_PRELOAD="/home/usuario/.hermes/lib/libsqlite3.so${LD_PRELOAD:+:$LD_PRELOAD}"
python3 -c "
import sqlite3
c = sqlite3.connect('file:/home/usuario/.hermes/state.db?mode=ro', uri=True)
print('SQLite:', sqlite3.sqlite_version)
print('journal_mode:', c.execute('PRAGMA journal_mode').fetchone()[0])
print('page_size:', c.execute('PRAGMA page_size').fetchone()[0])
print('page_count:', c.execute('PRAGMA page_count').fetchone()[0])
print('freelist_count:', c.execute('PRAGMA freelist_count').fetchone()[0])
"
```

Observed healthy output (2026-07-30): SQLite 3.51.3, journal_mode wal, page_size 4096, page_count 147366, freelist_count 0.

## Interpretation

- `journal_mode: wal` + SQLite ≥ 3.50.7 → healthy. Small WAL file (e.g. 2.5MB) next to a 600MB db is NORMAL in WAL mode — the WAL holds only un-checkpointed writes.
- `freelist_count × page_size` = reclaimable space. `freelist_count = 0` → VACUUM gains nothing; the db is compact and the size is real session history. Report this honestly instead of running a pointless VACUUM.
- VACUUM on a live db can hit "database is locked" — only worth attempting when freelist is meaningfully > 0 and Hermes is stopped.

## Related

- `hermes-recovery` skill (bundled): WAL corruption fix, stale-install cleanup, `.7z` restore.
- `hermes-maintenance-wsl` (user-owned): recovery procedures, drive mounting, backups.
