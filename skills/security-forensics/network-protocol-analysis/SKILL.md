---
name: network-protocol-analysis
title: Network Protocol Analysis — PCAP Forensics
description: Deep analysis of network protocols using tshark, scapy, and dpkt — PCAP dissection, traffic fingerprinting, metadata extraction, timing analysis, and protocol reverse engineering. Foundation skill for P2P messaging forensics and de-anonymization research.
trigger: User needs to analyze network traffic, extract protocol metadata, fingerprint communication patterns, or investigate protocol behavior from PCAP captures.
tags: [forensics, network-analysis, pcap, tshark, scapy, metadata, protocol-reverse-engineering, traffic-analysis]
domain: security-forensics
---
# Network Protocol Analysis — PCAP Forensics

## When to Use

- Analyzing captured traffic from messaging apps (WhatsApp, Signal, Telegram, Matrix)
- Extracting metadata (IPs, ports, TLS fingerprints, timing) from PCAPs
- Fingerprinting protocols by packet structure, handshake patterns, or certificate chains
- Reverse engineering unknown or obfuscated protocols
- Traffic confirmation / correlation attacks (de-anonymization research)
- Timing analysis for side-channel attacks

## Prerequisites

```bash
# Tools
tshark (Wireshark CLI), tcpdump, nmap

# Python libs
pip install scapy dpkt colorama
```

PCAP files to analyze (put in project/pcaps/):
- `tls12.pcap` — real TLS 1.2 traffic (31KB+)
- `test_messaging.pcap` — synthetic messaging traffic

## Core Techniques

### Technique 1: Quick Protocol Fingerprinting with tshark

```bash
# Basic protocol hierarchy (what protocols are in the PCAP)
tshark -r file.pcap -q -z io,phs

# Top talkers (IP addresses)
tshark -r file.pcap -q -z ip_hosts,tree

# Conversations (IP pairs + ports)
tshark -r file.pcap -q -z conv,ip

# TLS handshake details
tshark -r file.pcap -Y "tls.handshake" -T fields \
  -e tls.handshake.type \
  -e tls.handshake.ciphersuite \
  -e tls.handshake.extensions_server_name 2>/dev/null

# Export HTTP objects / files transferred
tshark -r file.pcap --export-objects http,./exported/
```

### Technique 2: Metadata Extraction with tshark

```bash
# Extract timing between packets (for timing analysis)
tshark -r file.pcap -T fields -e frame.time_epoch -e ip.src -e ip.dst -e frame.len

# Packet size distribution (fingerprinting)
tshark -r file.pcap -T fields -e frame.len | sort -n | uniq -c | sort -rn

# TLS fingerprinting (JA3 / JA3S)
tshark -r file.pcap -Y "tls.handshake.type == 1" -T fields \
  -e tls.handshake.ciphersuite \
  -e tls.handshake.extensions_supported_group \
  -e tls.handshake.extensions_ec_point_format

# DNS queries (metadata leakage)
tshark -r file.pcap -Y "dns" -T fields -e dns.qry.name -e dns.qry.type
```

### Technique 3: Deep PCAP Analysis with scapy

```python
from scapy.all import *
import json

def analyze_pcap(path):
    packets = rdpcap(path)
    report = {
        'total_packets': len(packets),
        'protocols': {},
        'top_ips': {},
        'packet_sizes': [],
        'timeline': []
    }

    for pkt in packets:
        # Protocol count
        if IP in pkt:
            proto = 'TCP' if TCP in pkt else 'UDP' if UDP in pkt else 'OTHER'
            report['protocols'][proto] = report['protocols'].get(proto, 0) + 1

            # Top IPs
            src = pkt[IP].src
            dst = pkt[IP].dst
            for ip in [src, dst]:
                report['top_ips'][ip] = report['top_ips'].get(ip, 0) + 1

            # Packet sizes
            report['packet_sizes'].append(len(pkt))
            report['timeline'].append(float(pkt.time))

    # Statistics
    sizes = report['packet_sizes']
    report['stats'] = {
        'min_size': min(sizes), 'max_size': max(sizes),
        'avg_size': sum(sizes)/len(sizes),
        'total_bytes': sum(sizes),
        'duration_sec': max(report['timeline']) - min(report['timeline'])
    }

    return report

# Run
report = analyze_pcap('pcaps/tls12.pcap')
print(json.dumps(report, indent=2))
```

### Technique 4: Traffic Timing Analysis

```python
from scapy.all import *
import numpy as np

def timing_analysis(path):
    packets = rdpcap(path)
    timestamps = [float(p.time) for p in packets if IP in p]
    intervals = np.diff(timestamps)

    return {
        'packet_count': len(timestamps),
        'duration_sec': timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0,
        'mean_interval_ms': float(np.mean(intervals)) * 1000 if len(intervals) > 0 else 0,
        'std_interval_ms': float(np.std(intervals)) * 1000 if len(intervals) > 0 else 0,
        'min_interval_ms': float(np.min(intervals)) * 1000 if len(intervals) > 0 else 0,
        'max_interval_ms': float(np.max(intervals)) * 1000 if len(intervals) > 0 else 0,
        'packet_rate': len(timestamps) / (timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0
    }
```

### Technique 5: Protocol Pattern Detection

```python
from scapy.all import *
import re

def detect_messaging_patterns(path):
    """Detect patterns typical of messaging/p2p protocols"""
    packets = rdpcap(path)
    findings = []

    for i, pkt in enumerate(packets):
        if TCP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw])

            # Detect XMPP (used by WhatsApp historically)
            if b'<message' in payload or b'<iq' in payload or b'<presence' in payload:
                findings.append({
                    'packet': i,
                    'type': 'XMPP',
                    'preview': payload[:100]
                })

            # Detect JSON-based protocols
            if payload.startswith(b'{') and b'msg' in payload:
                findings.append({
                    'packet': i,
                    'type': 'JSON_MESSAGING',
                    'preview': payload[:100]
                })

            # Detect protobuf (WhatsApp uses protobuf)
            if len(payload) > 10 and payload[0] < 0x20:
                findings.append({
                    'packet': i,
                    'type': 'BINARY_PROTOBUF_CANDIDATE',
                    'preview': payload[:50].hex()
                })

            # Keep-alive / heartbeat detection
            if len(payload) < 10 and i > 0:
                prev_pkt = packets[i-1]
                if TCP in prev_pkt and Raw in prev_pkt:
                    prev_payload = bytes(prev_pkt[Raw])
                    if len(prev_payload) < 10:
                        findings.append({
                            'packet': i,
                            'type': 'HEARTBEAT_PATTERN',
                            'interval': float(pkt.time) - float(prev_pkt.time)
                        })

    return findings
```

## Pitfall: PCAP from URL May Be HTML, Not a Capture

PCAPs downloaded from public URLs (GitHub raw, wiki attachments) frequently return HTML error pages. **Always verify:**

```bash
file pcaps/tls12.pcap
# → "HTML document, Unicode text" means NOT a valid PCAP
capinfos pcaps/file.pcap   # shows stats only for real PCAPs
```

Fix: generate synthetic PCAPs with scapy instead (see `references/synthetic-pcap-generation.md`).

## Debugging & Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| `tshark: unknown capture` | WSL no puede raw sniffing | Usar PCAPs precapturados o sintéticos |
| `scapy: no pcap support` | libpcap no instalado | `sudo apt install libpcap-dev` |
| `dpkt: truncated` | PCAP corrupto | Verificar con `capinfos file.pcap` |
| Payload vacío en scapy | Payload en capa incorrecta | Usar `pkt[Raw]` en vez de `pkt.payload` |
| Timing impreciso | Precisión de microsegundos en PCAP | Redondear a ms para análisis |
| `WARNING: getmacbyip failed` | WSL sin ARP para IPs no locales | Usar `Ether()` con broadcast default — harmless |

## Related Skills

- **p2p-messaging-forensics** — Protocol-specific analysis for WhatsApp/Signal/Matrix/Telegram (feed PCAP metadata into protocol analysis)
- **crypto-protocol-analysis** — Deep dive into Noise, X3DH, Double Ratchet, TLS handshakes detected in PCAPs
- **anonymization-protocol-analysis** — Tor/I2P/mixnet cell structure analysis for anonymous communication traffic

## Reference Files

- `references/synthetic-pcap-generation.md` — Generate realistic PCAPs with scapy when real captures aren't available (avoids the "HTML file as PCAP" pitfall)
- `references/whatsapp-web-capture-methodology.md` — Real-world WhatsApp Web capture methodology including expected DNS/SNI/timing leaks (proven in live test on P53 ThinkPad)

## Verification

```bash
# Verify PCAP is valid
capinfos pcaps/messaging_full_session.pcap

# Test tshark analysis
tshark -r pcaps/messaging_full_session.pcap -q -z io,phs

# Test scapy
python3 -c "
from scapy.all import *; p=rdpcap('pcaps/messaging_full_session.pcap')
print(f'{len(p)} packets, protocols:', {proto for pkt in p for proto in ['TCP','UDP'] if proto in pkt})
"
```

## Output

- `informes/network_analysis_<pcap>.json` — structured protocol report
- `informes/timing_analysis_<pcap>.json` — timing statistics
- `informes/patterns_<pcap>.json` — protocol pattern detections
