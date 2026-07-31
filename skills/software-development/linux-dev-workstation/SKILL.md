---
title: Linux Dev Workstation Software Setup
name: linux-dev-workstation
description: Audit and provision a Linux machine with modern development tooling — CLI tools, editors, runtimes, databases, and system cleanup. Complementary to linux-performance-tuning (hardware/OS tuning).
category: software-development
triggers:
  - "User asks 'set up this machine for development' or 'install dev tools'"
  - "User says 'this is a fresh install, make it a dev workstation'"
  - "User wants a modern CLI environment (ripgrep, fzf, tmux, etc.)"
  - "After running linux-performance-tuning, user asks about software tooling"
---

# Linux Dev Workstation Software Setup

## Goal

Take a Linux machine (Ubuntu 24.04+) and provision it with a complete, modern development environment. This skill covers **software tooling only** — run `linux-performance-tuning` first for hardware/OS optimizations.

## Workflow

### Phase 1: Audit Existing Tooling

Collect this data in parallel:

```bash
# Runtimes
python3 --version
node --version 2>/dev/null || echo "node not installed"
npm --version 2>/dev/null || echo "npm not installed"
gcc --version 2>/dev/null | head -1 || echo "gcc not installed"
rustc --version 2>/dev/null || echo "rust not installed"
go version 2>/dev/null || echo "go not installed"
java --version 2>/dev/null | head -1 || echo "java not installed"

# Package managers
pip3 --version 2>/dev/null
uv --version 2>/dev/null || echo "uv not installed"

# CLI tools
for cmd in git gh curl wget jq make tmux rg fd fzf bat eza lazygit btop httpie zoxide nvim code; do
  which "$cmd" &>/dev/null && echo "  OK $cmd" || echo "  MISS $cmd"
done

# Editors
which code vim nano nvim cursor 2>/dev/null

# Shell
echo "$SHELL"
which tmux screen fish zsh 2>/dev/null

# Docker
docker --version 2>/dev/null || echo "docker not installed"
docker compose version 2>/dev/null || echo "compose not installed"
groups | grep -q docker && echo "user in docker group" || echo "user NOT in docker group"

# Databases
for cmd in psql mysql redis-cli sqlite3 mongosh; do
  which "$cmd" &>/dev/null && echo "  OK $cmd" || echo "  MISS $cmd"
done

# Git config
git config --global --list 2>/dev/null || echo "git not configured globally"
```

### Phase 2: Categorize Missing Tools

Group into three tiers:

**Essential (🔴)** — core dev workflow:
- `gh` — GitHub CLI (PR review, issues, repos from terminal)
- `tmux` — terminal multiplexer (persistent sessions)
- `ripgrep` (`rg`) — ultra-fast code search
- `fd-find` (`fd`) — fast file finding
- `btop` — system resource monitor
- Editor: VSCode (`snap install code --classic`) or Neovim
- `sqlite3` — embedded DB (useful everywhere)

**Quality of life (🟡)** — serious productivity boost:
- `fzf` — fuzzy finder (history, files, everything)
- `bat` (`batcat` on Ubuntu) — `cat` with syntax highlighting
- `eza` — modern `ls` replacement
- `lazygit` — TUI for git
- `httpie` — curl with JSON formatting
- `zoxide` — smart `cd` replacement
- `lazygit` (if not available in apt, install from GitHub releases)

**System hygiene (🟢)** — reclaim space:
- `sudo apt clean` — clears cached .deb packages
- `sudo journalctl --vacuum-time=7d` — limits journal to 7 days
- Disable unnecessary services: `gnome-remote-desktop`, `bolt`, `kerneloops`, `rsyslog` (if journald is sufficient)
- `snap list` — review snap packages, remove unneeded ones (esp. if not using Firefox via snap)

### Phase 3: Install in a Single Consolidated Script

For 3+ installs, write one script and run with `sudo` once:

```bash
SCRIPT=$(mktemp)
cat > $SCRIPT << 'SCRIPTEOF'
#!/bin/bash
set -euo pipefail

# --- Essential tools ---
apt-get install -y -qq gh tmux ripgrep fd-find btop sqlite3

# --- Quality of life ---
apt-get install -y -qq fzf bat eza httpie zoxide

# --- lazygit (not always in apt) ---
if ! which lazygit &>/dev/null; then
  LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" \
    | grep -Po '"tag_name": *"v\K[^"]*')
  curl -sLo lazygit.tar.gz \
    "https://github.com/jesseduffield/lazygit/releases/download/v${LAZYGIT_VERSION}/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz"
  tar xf lazygit.tar.gz -C /usr/local/bin lazygit
  rm lazygit.tar.gz
fi

# --- System hygiene ---
apt clean -qq
journalctl --vacuum-time=7d -q

# --- Service disabling (opt-in) ---
# systemctl disable --now gnome-remote-desktop 2>/dev/null || true
# systemctl disable --now bolt 2>/dev/null || true
SCRIPTEOF
chmod +x $SCRIPT
sudo $SCRIPT
```

Install VSCode separately (no sudo needed):
```bash
sudo snap install code --classic
```

### Phase 4: Configure

After installs, set up:

```bash
# Git (required)
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Bat/fd aliases (Ubuntu ships as batcat and fdfind)
cat >> ~/.bash_aliases << 'EOF'
alias bat='batcat'
alias fd='fdfind'
EOF

# fzf integration (key bindings + auto-completion)
# On Ubuntu, fzf installs these to /usr/share/doc/fzf/examples/
# Source them in .bashrc:
# [ -f /usr/share/doc/fzf/examples/key-bindings.bash ] && source /etc/bash_completion.d/fzf 2>/dev/null

# zoxide init
# echo 'eval "$(zoxide init bash)"' >> ~/.bashrc
```

### Phase 5: Databases (Optional)

When the user works with a specific stack:

```bash
# PostgreSQL (Django, Rails, general)
sudo apt install postgresql postgresql-contrib libpq-dev

# Redis (caching, queues, sessions)
sudo apt install redis-server

# MySQL/MariaDB (WordPress, Laravel, legacy)
sudo apt install mariadb-server
```

### Phase 6: Language Runtimes (Optional)

```bash
# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Node version manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash

# Go (via apt, may be older version)
sudo apt install golang-go

# Or download latest from https://go.dev/dl/
```

## Pitfalls

- **`bat` and `fd` have different binary names on Ubuntu.** The packages are `bat` and `fd-find`, but the binaries are `batcat` and `fdfind` (to avoid naming conflicts with other packages). Always create aliases: `alias bat='batcat'` and `alias fd='fdfind'`.
- **`lazygit` is NOT in Ubuntu apt repos.** Install from GitHub releases using the curl+tar pattern above. Check the latest tag on GitHub before running.
- **VSCode via snap needs `--classic`.** Without the classic confinement flag, the snap install fails.
- **Docker group membership requires logout/login.** After `usermod -aG docker`, the current shell still has the old group list. Either run `newgrp docker` or tell the user to log out and back in.
- **nvm adds significant shell startup time.** Only recommend if the user needs multiple Node versions. Prefer using `npm` from the system-installed Node (which is likely already available via uv or similar).
- **PostgreSQL needs a running service.** After install: `sudo systemctl enable --now postgresql`. Also create a user: `sudo -u postgres createuser --interactive`.
- **Don't install VSCode and VSCodium side by side.** The extensions and config clash. Pick one.
- **`apt clean` does NOT require confirmation.** It's safe to run in automated scripts — only removes cached .deb files from `/var/cache/apt/archives/`, never installed packages.
- **`journalctl --vacuum-time=7d` is idempotent.** Running it repeatedly just re-enforces the 7-day boundary; it won't delete current-boot logs.

## Verification

```bash
echo "=== VERSION CHECK ==="
for cmd in python3 node npm git gh rg fd batcat eza fzf tmux btop lazygit httpie zoxide code; do
  ver=$(which $cmd &>/dev/null && ($cmd --version 2>/dev/null || $cmd version 2>/dev/null) | head -1 || echo "NOT FOUND")
  printf "%-12s %s\n" "$cmd" "$ver"
done

echo "=== DOCKER ==="
docker --version
docker compose version

echo "=== GIT CONFIG ==="
git config --global --list

echo "=== ALIASES ==="
alias bat fd 2>/dev/null || echo "aliases not loaded (new terminal needed)"
```

## Related Skills

- `skill_view(name="linux-performance-tuning")` — hardware/OS tuning (run first: CPU governor, swappiness, ZRAM, noatime, firmware updates)
- `skill_view(name="github-code-review")` — code review workflows using gh CLI
- `skill_view(name="python-debugpy")` — Python debugging (requires some of these tools)
