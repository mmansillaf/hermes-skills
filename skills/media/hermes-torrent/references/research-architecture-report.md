# Research: Hermes Agent + BitTorrent Integration Architecture

**Date:** 2026-07-08
**Source documents:** 5 files (`bit0.txt` through `bit4.txt`) in D:\PyCode\hermes-skills\torrent\
**Web verification:** GitHub (libtorrent, rqbit, Gluetun, qbittorrent-api, i2pd, Bitmagnet, Prowlarr), Hermes MCP docs, BEP specifications

## Architectural Decision: Why MCP Server Wins

Three strategies were compared:

| Strategy | Security | Scalability | Isolation | Verdict |
|----------|----------|-------------|-----------|---------|
| MCP Server | Very High | High | Complete | ⭐ RECOMMENDED |
| Hermes Native Skill | Medium | Medium | Low-Med | Advanced users only |
| execute_code Script | Low | Low | Minimal | Prototypes only |

## Recommended Stack (with versions)

| Layer | Technology | Version |
|-------|-----------|---------|
| Agent | Hermes Agent | v0.18.0+ |
| Protocol | MCP (Model Context Protocol) | Stdio or HTTP |
| BT Client | qBittorrent nox (daemon) | v5.2.2 (Web API v2.15.1) |
| Alt BT Client | rqbit (Rust) | Latest |
| Python lib | qbittorrent-api | 2026.7.0 |
| Indexer | Prowlarr | Latest |
| DHT Crawler | Bitmagnet (optional) | Latest, GraphQL API |
| VPN | Gluetun | Latest (Alpine 43MB, 23+ providers) |
| Anonymization | i2pd (I2P) | Latest (preferred over Tor for P2P) |
| Antivirus | ClamAV | Latest (Docker) |
| Pre-scan | VirusTotal API | Optional |

## CRITICAL: VPN Isolation Pattern

```yaml
# The single most important Docker Compose pattern
services:
  gluetun:           # VPN container with kill switch
    image: qmcgaw/gluetun
    cap_add: [NET_ADMIN]
    # ... VPN config ...

  qbittorrent:
    network_mode: "service:gluetun"    # ← FORCES ALL P2P TRAFFIC THROUGH VPN
    # ... rest of config ...
```

Without `network_mode: service:gluetun` on qBittorrent, the real IP leaks.

## Tor vs I2P for P2P

| Factor | Tor | I2P |
|--------|-----|-----|
| DHT over proxy | ⚠️ Buggy (SOCKS5 + UDP issues) | ✅ Native (SAM bridge) |
| De-anonymization | ⚠️ Documented attacks | ✅ More robust |
| Circuit design | Short-lived, web-oriented | Persistent, P2P-oriented |
| qBittorrent support | Manual SOCKS5 proxy | ✅ Native since v4.5+ |
| libtorrent support | Proxy SOCKS5 (bugs with DHT) | ✅ i2p_pex since v2.1.0 |

**Recommendation:** Use I2P for P2P. If using Tor, disable DHT/LSD/UPnP/NAT-PMP and set force_proxy=True.

## Defense in Depth (Post-Download)

| Layer | Tool | When |
|-------|------|------|
| Reputation | VirusTotal API | Before adding magnet |
| Integrity | SHA-256 (BEP-52) / SHA-1 (BEP-51) | During download |
| Antivirus | ClamAV (Docker) | Post-download |
| Sandbox | Docker isolation + quarantine | Before moving to final |

## BitTorrent v2 (BEP-52) Advantages

- SHA-256 replaces SHA-1 (collision-resistant)
- Merkle trees verify at block level, not full piece
- Faster magnet links (only root hash needed)
- Hybrid torrents compatible with v1 and v2
- Supported by libtorrent v2.1.0+ (active development)

## Libraries Comparison

| Library | Lang | BEP-52 | Notes |
|---------|------|--------|-------|
| libtorrent | C++ | ✅ Active | Most mature, full extensions |
| rqbit | Rust | TBD | HTTP API, streaming, SOCKS proxy native |
| rbit | Rust | ✅ | Pure Rust BEP implementations |
| btdht | Python | N/A | DHT-only, useful for Python apps |

## Key Security Settings (qBittorrent)

1. Anonymous Mode: ON
2. Encryption: Required
3. Seeding limits: Ratio 1.0, time 1440 min
4. Blocklist: Auto-update enabled
5. UPnP/NAT-PMP: OFF
6. Incoming port: Random (not 6881)
7. WebUI: Bind to 127.0.0.1 only

## MCP Server Tools (implemented)

| Tool | Function |
|------|----------|
| search_torrents | Query Prowlarr, filter by seeders |
| add_magnet | Validate + add magnet to qBittorrent |
| get_status | All active downloads |
| get_torrent_info | Single torrent detail by hash |
| set_seed_limits | Ratio/time seeding limits |
| verify_download | SHA-256 integrity check |

## Validating Hermes MCP Connection

```bash
hermes mcp list                    # Verify server is enabled
hermes mcp test torrent            # Test connection + tool discovery
# Expected: Connected, Tools discovered: 6
```

## References (External)

- BEP-5 (DHT): https://www.bittorrent.org/beps/bep_0005.html
- BEP-52 (v2): https://www.bittorrent.org/beps/bep_0052.html
- qBittorrent Web API: github.com/qbittorrent/qBittorrent/wiki/Web-API-Documentation
- Gluetun: github.com/qdm12/gluetun
- qbittorrent-api: pypi.org/project/qbittorrent-api/ (v2026.7.0)
- Hermes MCP Docs: hermes-agent.nousresearch.com/docs/user-guide/features/mcp
- i2pd: github.com/PurpleI2P/i2pd
- Bitmagnet: bitmagnet.io
- rqbit: github.com/ikatson/rqbit
- libtorrent changelog (v2.1.0): github.com/arvidn/libtorrent