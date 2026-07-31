---
name: whatsapp-desanonimizacion-stack
title: WhatsApp De-anonymization — Protocol Forensics Stack Setup
description: Complete stack for deep security research on P2P messaging protocols (WhatsApp/Signal Protocol). Creates 4 core skills (pcap analysis, P2P forensics, crypto analysis, anonymization), 3 PoC scripts, MCP server integration, and structured research outputs. Use when starting a thesis or deep-dive on messaging protocol security.
trigger: User wants to set up a complete forensic analysis environment for WhatsApp/Signal/P2P messaging protocol research, de-anonymization vectors, or traffic confirmation analysis.
tags: [forensics, whatsapp, signal-protocol, p2p-messaging, de-anonymization, pcap, traffic-analysis, thesis, network-security]
domain: security-forensics
---
# WhatsApp De-anonymization — Protocol Forensics Stack

## When to Use

- Starting a thesis on security and anonymization in P2P communication protocols
- Setting up a forensic analysis environment for WhatsApp/Signal/Matrix/Telegram
- Researching de-anonymization vectors in encrypted messaging apps
- Building a PCAP analysis pipeline for protocol metadata extraction
- Integrating security MCP servers (RAMparts, AI-Infra-Guard) into the workflow

## Prerequisites

```bash
# CLI tools
sudo apt install tshark tcpdump nmap masscan binwalk foremost yara

# Python libs
pip install scapy dpkt colorama cryptography

# MCP (optional — for security scanning)
npm install -g mcporter   # or npx mcporter
```

## Quick Start — Full Stack in 5 Minutes

### 1. Create project structure

```bash
PROJECT="D:/PyCode/hermes-skills/WhatsappDesanonimizacion"
mkdir -p "$PROJECT"/{scripts,pcaps,informes,skills,references}
```

### 2. Generate test PCAPs

```python
from scapy.all import *
pkts = []
for i in range(5):
    pkts.append(IP(src='10.0.0.1', dst='10.0.0.2')/TCP(sport=443+i, dport=5222, flags='PA')/Raw(load=b'MSG_' + str(i).encode()*20))
wrpcap('pcaps/test_messaging.pcap', pkts)
```

### 3. Create the 3 PoC scripts

See `scripts/` directory in this skill for:
- `analyze_pcap.py` — full PCAP analysis (protocols, IPs, flows, timing, packet sizes)
- `timing_attack.py` — traffic confirmation via temporal correlation
- `metadata_extract.py` — DNS/SNI/TLS metadata leakage extraction

Run them:
```bash
python3 scripts/analyze_pcap.py pcaps/messaging_full_session.pcap
python3 scripts/timing_attack.py pcaps/messaging_full_session.pcap
python3 scripts/metadata_extract.py pcaps/messaging_full_session.pcap
```

### 4. Load the 4 core skills

```bash
# Already installed via skill_manage — just load them in any session:
skill_view(name='network-protocol-analysis')
skill_view(name='p2p-messaging-forensics')
skill_view(name='crypto-protocol-analysis')
skill_view(name='anonymization-protocol-analysis')
```

## Architecture — Multi-Machine Forensic Setup

This stack uses a **two-machine pattern** to overcome WSL limitations:

```
┌──────────────────────┐          ┌───────────────────────────┐
│  WSL (dev)           │  scp     │  P53 / Remote Ubuntu      │
│  ───────────         │ ────────►│  ───────────────────       │
│  Skill authoring     │          │  Raw packet capture       │
│  Script development  │          │  tshark / tcpdump         │
│  Report generation   │ ◄────────│  scapy analysis           │
│  NO raw sniffing     │   scp    │  RAMparts Rust build      │
│  NO long builds      │          │  mitmproxy interception   │
└──────────────────────┘          │  46GB RAM, GPU            │
                                  └───────────────────────────┘
```

**Why not just WSL?** WSL cannot capture raw packets (no libpcap access to physical
interfaces) and kills processes after 300s (Rust builds, FAISS indexing). A real
Ubuntu machine handles all network-level operations.

**Deployment:** Use `scripts/deploy-to-remote.sh` for one-command setup. See
`references/p53-deployment-guide.md` for manual setup.

## Real Capture Workflow (P53)

### Quick capture (30 seconds)

```bash
sshpass -p 'PASS' ssh usuario@192.168.18.80 "
echo 'PASS' | sudo -S timeout 30 tcpdump -i wlp82s0 \\
  -w ~/whatsapp-analysis/capturas/whatsapp_live.pcap \\
  'port 53 or port 443 or port 80 or port 5222'
"
```

### Analyze immediately

```bash
sshpass -p 'PASS' ssh usuario@192.168.18.80 "
cd ~/whatsapp-analysis

# 1. Protocol hierarchy
tshark -r capturas/whatsapp_live.pcap -q -z io,phs

# 2. DNS queries (plaintext leakage)
tshark -r capturas/whatsapp_live.pcap \\
  -Y 'dns.flags.response == 0' -T fields -e dns.qry.name | sort -u

# 3. SNI hostnames (TLS leakage)
tshark -r capturas/whatsapp_live.pcap \\
  -Y 'tls.handshake.extensions_server_name' \\
  -T fields -e tls.handshake.extensions_server_name | sort -u

# 4. Top IPs (infrastructure mapping)
tshark -r capturas/whatsapp_live.pcap -q -z ip_hosts,tree

# 5. Full metadata extraction
python3 scripts/metadata_extract.py capturas/whatsapp_live.pcap
"
```

### What to expect when capturing WhatsApp Web

| Observation | What it reveals | Severity |
|-------------|----------------|----------|
| DNS: `web.whatsapp.com` | You are using WhatsApp | 🔴 Plaintext |
| DNS: `web.whatsapp.net` | WebSocket endpoint | 🔴 Plaintext |
| SNI: `*.fbcdn.net` | Meta CDN servers | 🟡 Visible |
| SNI: `*.whatsapp.net` | WhatsApp servers | 🟡 Visible |
| Packet bursts after silence | Message sent/received | 🟡 Timing |
| Packet sizes vary | Text vs media vs voice | 🟡 Content type |
| Server IP geo | Approximate location | 🔴 Infra leak |
| WebSocket frames count | Number of messages | 🟡 Activity level |
| Keep-alive interval | App background/foreground | 🟢 Device state |

## De-anonymization Vectors (Quick Reference)

| Vector | Protocol | Leakage | Tool |
|--------|----------|---------|------|
| DNS queries | All | Server hostname | metadata_extract.py |
| SNI (TLS) | All | Destination server | metadata_extract.py |
| Traffic confirmation | WhatsApp/Signal | Who talks to whom | timing_attack.py |
| Timing analysis | All | Activity patterns | timing_attack.py |
| Packet size | All | Content type | analyze_pcap.py |
| IP tracking | All | Geolocation | analyze_pcap.py |
| PreKey retrieval | Signal/WhatsApp | Social graph | Manual analysis |

## MCP Server Integration

### AI-Infra-Guard (Tencent) — 4.3k ⭐
Full-stack AI Red Teaming platform. Most relevant for auditing MCP-based AI systems.

```bash
git clone --depth 1 https://github.com/Tencent/AI-Infra-Guard.git
cd AI-Infra-Guard
# See README.md for Docker/Go build instructions
```

### RAMparts (highflame-ai) — Rust-based MCP scanner
Scans MCP servers for vulnerabilities and misconfigurations.

```bash
git clone https://github.com/highflame-ai/ramparts.git
cd ramparts
cargo build --release
./target/release/ramparts --help
```

### Lamda (firerpa) — Android MITM/Frida
Full Android device control with MITM, Frida, VPN. Requires Android device.

```bash
git clone https://github.com/firerpa/lamda.git
cd lamda
python3 setup.py install
# Requires: ADB-connected Android device
```

## P53 Deployment — Real Ubuntu Forensics Workstation

WSL cannot do raw packet sniffing or long Rust builds. Deploy the stack to a local
Ubuntu machine (e.g. ThinkPad P53 with 46GB RAM, Quadro T1000 GPU) for real captures.

See `references/p53-deployment-guide.md` for full setup instructions.
Use `scripts/deploy-to-remote.sh` to deploy in one command:

```bash
# One-command deploy
SSH_PASS='password' bash scripts/deploy-to-remote.sh usuario@192.168.18.80
```

### What the P53 gives you that WSL cannot

| Capability | WSL | Real Ubuntu |
|------------|-----|-------------|
| Raw packet capture | ❌ | ✅ tcpdump on any interface |
| GPU acceleration | ❌ | ✅ CUDA (Quadro T1000) |
| Long Rust builds | ❌ times out | ✅ background (PID nohup) |
| mitmproxy full interception | ❌ | ✅ full networking |

## Workflow Preferences

When executing this stack for the user:

1. **Plan + estimates first** — always present a structured plan with time estimates
   before executing. Get explicit approval ("dale" / "procede") before proceeding.
2. **Concrete demonstrations over theory** — prefer executing real tools against
   actual PCAPs over describing what would happen. Deliver working scripts and
   actual tool output.
3. **Report every 5-10 min** on long tasks — the user should not have to ask
   "cómo vas?". Proactive updates with table + emojis + timings.
4. **Maximum detail** — include what was NOT done as well as what was, tables
   of findings, severity indicators (🔴🟠🟡⚪), and self-critique of limitations.
5. **Prefer patching over rewriting** — when modifying existing code/files, make
   targeted changes rather than full rewrites.

## Pitfalls

### Environment limitations
- **WSL cannot do raw packet sniffing** — deploy to a real Ubuntu machine (P53) via `scripts/deploy-to-remote.sh`
- **Rust builds via SSH timeout in WSL** (300s limit) — clone on the remote machine and build there with `nohup`
- **tcpdump needs sudo** on remote — pipe via `echo 'PASS' | sudo -S`
- **nvidia-smi may fail** even with GPU present — `sudo apt install nvidia-driver-550`

### PCAP analysis
- **scapy `rdpcap` silently fails on non-pcap files** — always `file pcap.pcap` first
- **PCAP downloads from wiki/random URLs may be HTML** — verify with `file` before analysis
- **Timing attack accuracy** depends on PCAP precision — prefer microsecond timestamps
- **TLS SNI parsing** with raw scapy is fragile — use tshark for reliable extraction

### MCP servers
- **MCP servers via npx may fail** on GitHub repos without package.json — use `git clone` + local build instead
- **MCP servers from GitHub may need local build** — `npx github:user/repo` often fails

## Verification

```bash
# Verify tools
tshark --version && nmap --version && python3 -c "import scapy; print(scapy.Version)"

# Verify PCAPs
file pcaps/*.pcap | grep "pcap capture"

# Test scripts
python3 scripts/analyze_pcap.py pcaps/test_messaging.pcap
python3 scripts/metadata_extract.py pcaps/test_messaging.pcap

# Check reports
ls informes/*.json
```
