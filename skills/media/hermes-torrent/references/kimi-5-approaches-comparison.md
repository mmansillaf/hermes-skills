# Comparison: 5 Approaches for Hermes + BitTorrent Integration

Source: Kimi conversation "Hermes 连接暗网与BT" (2026-07-08)
Evaluated against actual project state at `D:\PyCode\hermes-skills\torrent\`

## The 5 Approaches

| # | Approach | Complexity | Security | Status | Recommendation |
|---|----------|-----------|----------|--------|---------------|
| 1 | **Hermes Skill** (SKILL.md that tell agent to use web_search/web_extract/terminal) | Very Low | Low | ❌ Not implemented | Quick one-off searches |
| 2 | **Python scraper script + Skill with execute_code** (requests/BeautifulSoup scraping 1337x etc.) | Low | Low-Medium | ❌ Not implemented (scripts/ dir empty) | Prototyping only |
| 3 | **torrent-search-mcp** (existing MCP server pkg: philogicae/torrent-search-mcp) | Medium | Medium | ⚠️ Not evaluated | Evaluate before writing custom MCP |
| 4 | **torrfetch PyPI library** (`pip install torrfetch`, search_torrents() API) | Very Low | Low | ❌ Not installed/tested | Quickest path to working search |
| 5 | **Native Hermes tool** (@register_tool in Python Registry) | High | Medium | ❌ Not implemented | For deep integration only |

## What IS Implemented

| Component | Status | Path |
|-----------|--------|------|
| Custom MCP Server (6 tools) | ✅ Complete, 536 lines | `mcp/mcp_torrent_server.py` |
| Research docs (bit0-bit4.txt) | ✅ 5 documents | `bit*.txt` |
| Comprehensive report | ✅ Covers all architecture | `report/informe-integracion-hermes-bittorrent.md` |

## Gap Analysis: What's Missing

### 🔴 Critical (blocking actual use)
1. **MCP Server not wired in config.yaml** — `~/.hermes/config.yaml` lacks `mcp_servers.torrent` entry
2. **No docker-compose.yml** — Docker stack (Gluetun + qBittorrent + Prowlarr) not deployable
3. **No SKILL.md for Hermes** — agent has no procedural memory of how to use the MCP tools

### 🟡 Medium (nice to have for v1)
4. **Prowlarr API key not configured** — mock search fallback exists but no real search
5. **ClamAV not wired into MCP** — post-download scanning is manual
6. **qBittorrent not running** — cannot test add_magnet, get_status, etc.

### 🟢 Low (future improvements)
7. **I2P bridge** — not configured (recommended over Tor for P2P)
8. **Bitmagnet DHT crawler** — not deployed
9. **rqbit (Rust client)** — not evaluated
10. **VirusTotal API** — not integrated in MCP server
11. **BitTorrent v2 (BEP-52)** — not tested (libtorrent support exists but untested)

## Decision Matrix: Which Approach When

| Your need | Pick this | Why |
|-----------|-----------|-----|
| "Quick search, no infra setup" | **torrfetch** (Op. 4) | `pip install torrfetch && python -c "import torrfetch; print(torrfetch.search_torrents('ubuntu'))"` |
| "Hermes should just search" | **SKILL.md** (Op. 1) + **torrfetch** | Tell agent to `pip install torrfetch && python -c "import torrfetch..."` |
| "Full download pipeline" | **Custom MCP Server** (implemented) | Needs Docker stack + VPN + qBittorrent |
| "Want community-maintained" | **torrent-search-mcp** (Op. 3) | Check if philogicae/torrent-search-mcp covers your needs |
| "Deep Hermes integration" | **@register_tool** (Op. 5) | Only if you need the tool in every conversation permanently |

## Pitfalls

- **Overengineering**: The full Docker stack (Gluetun + qBittorrent + Prowlarr + ClamAV) is heavy. For simple searches, `torrfetch` does it in one line. Don't default to the MCP Server for every query.
- **WSL path confusion**: The project lives at `D:\PyCode\hermes-skills\torrent\`, NOT `~/hermes-torrent/`. Options 1 (SKILL.md) and 5 (@register_tool) need paths adjusted accordingly.
- **VPN is mandatory for downloading**: If you're actually downloading (not just searching), you MUST route through VPN/I2P or Gluetun. Searching with torrfetch is read-only and lower risk.