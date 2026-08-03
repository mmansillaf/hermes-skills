---
name: hermes-recovery
description: "Fix crashes, broken installs, and SQLite WAL bugs in Hermes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, wsl]
metadata:
  hermes:
    tags: [hermes, recovery, sqlite, maintenance, wsl, ubuntu]
    category: autonomous-ai-agents
    related_skills: [hermes-agent]
---

# Hermes Recovery

Recover Hermes Agent after a crash, failed update, or broken reinstall. Covers identifying stale installations, fixing the SQLite WAL corruption bug, and cleaning up accumulated cache artifacts.

## When to Use

- Hermes crashed mid-session and the user had to reinstall.
- The SQLite WAL-reset corruption warning appears in logs.
- A `hermes-agent.broken-*` or similar stale directory exists in `~/.hermes/`.
- Hermes logs show `journal_mode=DELETE` fallback due to SQLite version.
- The user asks "can you clean up / optimize Hermes?"

## Diagnosis

```bash
# Check for WAL corruption risk
tail -50 ~/.hermes/logs/agent.log | grep -i "wal\|sqlite\|journal_mode"

# Identify stale installation directories
ls -la ~/.hermes/ | grep -E "broken|old|bak|backup"

# Check SQLite version
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"

# Check sizes of caches and logs
du -sh ~/.hermes/models_dev_cache.json ~/.hermes/config.yaml.bak.* 2>/dev/null
du -sh ~/.hermes/logs/
```

## Fix SQLite WAL Corruption Bug

The WAL-reset corruption bug affects SQLite versions below 3.50.7 (backport) / 3.51.3 (current). Ubuntu 24.04 Noble ships 3.45.1 which is vulnerable. Hermes auto-falls back to `journal_mode=DELETE`, but the warning fires every startup.

### Option A: Compile SQLite from source (recommended — enables WAL mode fully)

```bash
# Download SQLite 3.51.3 amalgamation
cd /tmp
curl -sLO "https://www.sqlite.org/2026/sqlite-amalgamation-3510300.zip"
unzip -o sqlite-amalgamation-3510300.zip -d sqlite_src
cd sqlite_src/sqlite-amalgamation-3510300

# Compile as shared library with essential features
gcc -shared -fPIC -O2 -o libsqlite3.so \
  sqlite3.c \
  -DSQLITE_THREADSAFE=1 \
  -DSQLITE_ENABLE_FTS5 \
  -DSQLITE_ENABLE_JSON1 \
  -DSQLITE_ENABLE_MATH_FUNCTIONS \
  -DSQLITE_ENABLE_COLUMN_METADATA \
  -DSQLITE_ENABLE_DBSTAT_VTAB \
  -DSQLITE_ENABLE_RTREE \
  -DSQLITE_ENABLE_GEOPOLY \
  -lpthread -ldl -lm

# Install to Hermes lib directory
mkdir -p ~/.hermes/lib/
cp libsqlite3.so ~/.hermes/lib/libsqlite3.so
```

### Configure LD_PRELOAD

Edit the Hermes launcher script at `~/.local/bin/hermes` to add the LD_PRELOAD before execution:

```bash
#!/usr/bin/env bash
unset PYTHONPATH
unset PYTHONHOME
export LD_PRELOAD="/home/usuario/.hermes/lib/libsqlite3.so${LD_PRELOAD:+:$LD_PRELOAD}"
exec "/home/usuario/.hermes/hermes-agent/venv/bin/python" "/home/usuario/.hermes/hermes-agent/hermes" "$@"
```

The user's home path must match the actual user. Verify with:
```bash
echo $HOME
```

### Verify

```bash
LD_PRELOAD=~/.hermes/lib/libsqlite3.so python3 -c "
import sqlite3
print('SQLite:', sqlite3.sqlite_version)
print('WAL:', sqlite3.connect(':memory:').execute('PRAGMA journal_mode=WAL').fetchone()[0])
"
# Expected: SQLite: 3.51.3, WAL: wal
```

Then run `hermes doctor` to confirm no more WAL warnings.

### Option B: Accept DELETE mode (simpler, no fix needed)

Set `journal_mode: delete` in `config.yaml` under the `database:` section. This silences the warning but sacrifices WAL concurrency:

```bash
hermes config set database.journal_mode delete
```

## Clean Up Stale Installations

After a crash/reinstall, Hermes may leave stale checkout directories with a `broken-*` suffix:

```bash
# Identify stale directories (check with user before deleting)
du -sh ~/.hermes/hermes-agent.broken-*

# Delete after confirmation
rm -rf ~/.hermes/hermes-agent.broken-*
```

## Clean Up Caches and Backups

These files can be safely removed — they regenerate on demand:

```bash
# Model cache (3+ MB, regenerated when next model query is made)
rm -f ~/.hermes/models_dev_cache.json

# Config template backup (88+ KB, just the default template)
rm -f ~/.hermes/config.yaml.bak.*

# Image/audio caches (usually empty, safe to remove)
rm -rf ~/.hermes/image_cache/* ~/.hermes/audio_cache/*
```

## Restore from Backup (.7z on Windows Drive)

After a crash/reinstall, the user may have a backup `.7z` archive on a Windows drive (e.g., `F:\.hermes.bak.<timestamp>.7z`). Extract and examine it from WSL:

### Mount the Windows Drive

```bash
# The F: drive may not be auto-mounted in WSL
sudo mkdir -p /mnt/f
sudo mount -t drvfs F: /mnt/f

# Verify the file
ls -la /mnt/f/".hermes.bak.*.7z"
file /mnt/f/".hermes.bak.*.7z"
# Expected: "7-zip archive data, version 0.4"
```

### Inspect Archive Contents

```bash
# List top-level structure first — slow for multi-GB archives
7z l /mnt/f/".hermes.bak.*.7z" 2>&1 | grep "^2026-" | head -30

# Find key files across the archive
for f in config.yaml .env auth.json SOUL.md .hermes_history state.db; do
  echo "=== $f ==="
  7z l /mnt/f/".hermes.bak.*.7z" 2>&1 | grep "(^|/)$f$" | head -5
done
```

### Extract Specific Files

For large archives (5+ GB), extract only what's needed — don't extract the entire archive:

```bash
# Extract config, SOUL, auth, and history
mkdir -p /tmp/hermes-restore
7z x /mnt/f/".hermes.bak.*.7z" \
  ".hermes.bak.<timestamp>/config.yaml" \
  ".hermes.bak.<timestamp>/SOUL.md" \
  ".hermes.bak.<timestamp>/auth.json" \
  ".hermes.bak.<timestamp>/.hermes_history" \
  -o/tmp/hermes-restore -y
```

### Key Files to Recover

| File | Why Recover |
|------|-------------|
| `config.yaml` | Tool config, model setup, auxiliary providers, display/security settings |
| `.env` | API keys (DeepSeek, OpenRouter, etc.) — DO NOT display or log contents |
| `auth.json` | OAuth tokens for Nous Portal and other auth providers |
| `memories/USER.md` | User profile: name, stack, workflow preferences, project details |
| `memories/MEMORY.md` | Agent's durable notes: configs, IPs, skills created, deployment details |
| `state.db` | All past conversation sessions (can be 400–600 MB) |
| `SOUL.md` | Custom persona prompt (may contain Karpathy rules, style directives) |
| `skills/` directory | Agent-created skills not captured in the bundled/hermes-hub set |

### Compare Configs Before Restoring

```bash
# Side-by-side key values
diff <(grep -v '^\s*#' /tmp/backup/config.yaml | grep -E '^[a-z]') \
     <(grep -v '^\s*#' ~/.hermes/config.yaml | grep -E '^[a-z]') | head -40
```

### State DB Restoration

The `state.db` can be large (400–603 MB). To restore:

```bash
# Stop Hermes first, then swap
cp ~/.hermes/state.db ~/.hermes/state.db.new-install-backup
cp /tmp/extracted/state.db ~/.hermes/state.db
```

Note: Restoring the full state.db brings back all sessions, including session_search capability. The user should be asked before doing this.

## Pitfalls

- **Always confirm before deleting** — the broken directory may contain work-in-progress. Check with the user first.
- **LD_PRELOAD path must be absolute** — the wrapper script runs from a cleaned environment (PYTHONPATH/PYTHONHOME are unset), so `~` expansion may not work depending on the shell. Use the full absolute path.
- **The LD_PRELOAD wrapper only affects `hermes` CLI** — if the user runs `python3 -c "import sqlite3"` directly, it uses the system SQLite. Only the `hermes` launcher script gets the fixed version.
- **WAL mode requires SQLite 3.50.7+ or 3.51.3+** — versions 3.44.x–3.50.7 are still vulnerable. Double-check the compiled version.
- **Python's bundled `pysqlite3-binary` won't work** on Debian/Ubuntu with PEP 668 (externally-managed-environment). Compiling the shared library from source is the reliable path.
- **`models_dev_cache.json` regenerates at ~3.2 MB** — this is normal, it's the provider model catalog cache.
- **7z extraction of huge archives is slow** — `7z l` on a 6 GB archive takes ~30 seconds. `7z x` extracting a few small files from a large solid-compressed archive must still decompress the whole block (another 30–60s). Be patient, don't timeout too aggressively.
- **The `state.db` may be incompatible** if the Hermes version changed — the session schema changes between releases. Check `sqlite3 ~/.hermes/state.db '.schema sessions'` after restoring to verify columns match.
- **`.env` from backup may have stale keys** — always verify with the user before restoring credentials. Ask if they have updated any API keys since the backup was made.
