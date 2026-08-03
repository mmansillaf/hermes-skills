# SQLite WAL Corruption Bug Fix for Hermes on WSL

## The Problem

Hermes logs show:
```
WARNING hermes_state: state.db: linked SQLite 3.45.1 is vulnerable to the WAL-reset corruption bug
(https://sqlite.org/wal.html#walresetbug) — using journal_mode=DELETE instead of enabling WAL.
```

This means the system SQLite library has a known bug where WAL journal mode can corrupt the database. Hermes auto-falls back to `journal_mode=DELETE`, which avoids corruption but is slower for concurrent access.

## Fix Requirements

- SQLite >= 3.51.3 (or backports 3.50.7 / 3.44.6)
- Ubuntu 24.04 Noble ships SQLite 3.45.1 — too old
- No newer apt package available
- `pysqlite3-binary` won't install due to PEP 668

## Compilation Recipe

```bash
# 1. Download SQLite amalgamation (single-file C source)
cd /tmp
curl -sL "https://www.sqlite.org/2026/sqlite-amalgamation-3510300.zip" -o sqlite.zip
unzip sqlite.zip -d sqlite_src

# 2. Compile as shared library with Hermes-required features
cd sqlite_src/sqlite-amalgamation-3510300
gcc -shared -fPIC -O2 -o libsqlite3.so sqlite3.c \
  -DSQLITE_THREADSAFE=1 \
  -DSQLITE_ENABLE_FTS5 \
  -DSQLITE_ENABLE_JSON1 \
  -DSQLITE_ENABLE_MATH_FUNCTIONS \
  -DSQLITE_ENABLE_COLUMN_METADATA \
  -DSQLITE_ENABLE_DBSTAT_VTAB \
  -DSQLITE_ENABLE_RTREE \
  -DSQLITE_ENABLE_GEOPOLY \
  -lpthread -ldl -lm

# 3. Install to Hermes lib
mkdir -p ~/.hermes/lib/
cp libsqlite3.so ~/.hermes/lib/libsqlite3.so

# 4. Clean temp files
rm -rf /tmp/sqlite.zip /tmp/sqlite_src
```

## LD_PRELOAD Setup

Edit `~/.local/bin/hermes` (the Hermes CLI wrapper):

```bash
#!/usr/bin/env bash
unset PYTHONPATH
unset PYTHONHOME
export LD_PRELOAD="/home/usuario/.hermes/lib/libsqlite3.so${LD_PRELOAD:+:$LD_PRELOAD}"
exec "/home/usuario/.hermes/hermes-agent/venv/bin/python" "/home/usuario/.hermes/hermes-agent/hermes" "$@"
```

**Important:** The path in `LD_PRELOAD` must be absolute. Using `~` won't expand.

## Verification

```bash
# Test that the new SQLite loads correctly
LD_PRELOAD=~/.hermes/lib/libsqlite3.so python3 -c "
import sqlite3
print('SQLite:', sqlite3.sqlite_version)
print('WAL:', sqlite3.connect(':memory:').execute('PRAGMA journal_mode=WAL').fetchone()[0])
"

# Expected output:
# SQLite: 3.51.3
# WAL: wal
```

## Version URL Pattern

SQLite release URLs follow:
- `https://www.sqlite.org/2026/sqlite-amalgamation-3510300.zip` (3.51.3)
- `https://www.sqlite.org/2025/sqlite-amalgamation-3490100.zip` (3.49.1)

The version number encodes as: `{major}{minor:02d}{patch:02d}00` e.g. 3.51.3 → 3510300.

## Config Persistence

The `config.yaml` already uses `journal_mode: wal`. With the fixed SQLite, WAL mode actually works instead of silently falling back to DELETE. No config changes needed.
