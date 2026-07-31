---
name: p2p-messaging-forensics
title: P2P Messaging Forensics — Signal/WhatsApp/Matrix/Telegram Protocol Analysis
description: Forensic analysis of peer-to-peer messaging protocols — Signal Protocol (X3DH + Double Ratchet), WhatsApp's implementation, Matrix/OLM, Telegram MTProto. Techniques for metadata extraction, traffic confirmation, timing analysis, and de-anonymization vectors.
trigger: User needs to analyze P2P messaging protocol behavior, understand de-anonymization vectors, or research traffic patterns in encrypted messaging apps.
tags: [forensics, p2p-messaging, signal-protocol, whatsapp, matrix, telegram, double-ratchet, metadata, de-anonymization, traffic-confirmation]
domain: security-forensics
---
# P2P Messaging Forensics — Signal/WhatsApp/Matrix/Telegram

## When to Use

- Investigating de-anonymization vectors in P2P messaging protocols
- Analyzing WhatsApp/Signal/Matrix traffic patterns from captured PCAPs
- Understanding the Signal Protocol (X3DH + Double Ratchet) metadata leakage
- Traffic confirmation attacks — correlating observed traffic with known communication events
- Timing analysis to infer message activity despite encryption
- Researching metadata leakage in federated protocols (Matrix, XMPP)

## Protocol Reference

### WhatsApp / Signal Protocol

```
Registration:     Phone# → Auth Token → Signed PreKey Bundle
Message Send:     Sender → WhatsApp Server (Fan-out) → Recipient(s)
Encryption:       X3DH (initial) + Double Ratchet (continuous)
Transport:        Noise Pipes over WSS (WebSocket Secure)
Metadata Leakage: IP/port of server, packet timing, packet sizes, 
                  WebSocket frames, message count inference
```

**Key Papers:**
- Signal Protocol Spec: https://signal.org/docs/specifications/doubleratchet/
- WhatsApp Security Whitepaper: https://www.whatsapp.com/security/WhatsApp-Security-Whitepaper.pdf
- Traffic Confirmation Attacks: "Tearing apart WhatsApp's encrypted communications" (Cowan et al.)

### Matrix / OLM

```
Registration:     Email → Homeserver → Device Keys
Message Send:     Sender → Homeserver → Sync API → Recipient(s)
Encryption:       OLM (1:1, Double Ratchet) + Megolm (group, AES-GCM)
Transport:        HTTPS + Sync API (long-polling)
Metadata Leakage: Homeserver knows all metadata (who talks to whom, when)
                  Room membership, device list, IPs
```

### Telegram MTProto

```
Registration:     Phone# → Cloud Password → 2FA
Message Send:     Sender → Telegram Cloud → Recipient
Encryption:       MTProto 2.0 (custom, not Signal Protocol)
                  Server-client encryption by default
                  End-to-end only in "Secret Chats"
Transport:        Custom protocol over TCP/HTTPS
Metadata Leakage: Server has ALL plaintext by default (non-secret chats)
                  IPs, contacts, group memberships
```

## Forensic Techniques

### Technique 1: WhatsApp WebSocket Traffic Analysis

WhatsApp uses WebSocket Secure (WSS) connections to `wss://{subdomain}.whatsapp.net:443`. The traffic is wrapped in Noise Pipes.

```python
from scapy.all import *

def detect_whatsapp_traffic(path):
    """Detect WhatsApp-related traffic patterns in a PCAP"""
    packets = rdpcap(path)
    whatsapp_ips = set()
    ws_connections = []

    for pkt in packets:
        if TCP in pkt:
            # Detect WhatsApp WebSocket connections by port + TLS
            if pkt[TCP].dport == 443 or pkt[TCP].sport == 443:
                if Raw in pkt:
                    payload = bytes(pkt[Raw])
                    # Noise Protocol handshake detection
                    if len(payload) >= 32 and payload[0] in [0x00, 0x01, 0x02, 0x03]:
                        try:
                            # Noise message patterns
                            noisemsg = payload[:32]
                            whatsapp_ips.add(pkt[IP].src)
                            whatsapp_ips.add(pkt[IP].dst)
                            ws_connections.append({
                                'packet': packets.index(pkt),
                                'src': pkt[IP].src, 'dst': pkt[IP].dst,
                                'sport': pkt[TCP].sport, 'dport': pkt[TCP].dport,
                                'payload_size': len(payload),
                                'timestamp': float(pkt.time)
                            })
                        except: pass

    return {
        'whatsapp_potential_ips': list(whatsapp_ips),
        'noise_connections': ws_connections[:10]  # first 10
    }
```

### Technique 2: Traffic Confirmation Attack Simulation

The core de-anonymization vector: an adversary who can observe the network (ISP, WiFi operator, telecom) can confirm when two specific users are communicating by correlating traffic patterns.

```python
import numpy as np
from scapy.all import *

def simulate_traffic_confirmation(path, user_a_ip=None, user_b_ip=None):
    """
    Simulate a traffic confirmation attack.
    Given observed encrypted traffic, can we determine if 
    a specific pair of users are communicating?
    """
    packets = rdpcap(path)
    
    # 1. Time-series of packet activity between IP pairs
    ip_pairs = {}
    for pkt in packets:
        if IP in pkt:
            pair = tuple(sorted([pkt[IP].src, pkt[IP].dst]))
            if pair not in ip_pairs:
                ip_pairs[pair] = {'count': 0, 'bytes': 0, 'timestamps': []}
            ip_pairs[pair]['count'] += 1
            ip_pairs[pair]['bytes'] += len(pkt)
            ip_pairs[pair]['timestamps'].append(float(pkt.time))
    
    # 2. For each pair, calculate correlation metrics
    results = []
    for pair, data in ip_pairs.items():
        if data['count'] < 2:
            continue
            
        ts = np.array(data['timestamps'])
        intervals = np.diff(ts)
        
        results.append({
            'ip_pair': f"{pair[0]} <-> {pair[1]}",
            'packet_count': data['count'],
            'total_bytes': data['bytes'],
            'duration_sec': float(ts[-1] - ts[0]) if len(ts) > 1 else 0,
            'mean_interval_ms': float(np.mean(intervals)) * 1000 if len(intervals) > 0 else 0,
            'burstiness': float(np.std(intervals) / np.mean(intervals)) if np.mean(intervals) > 0 else 0,
            'packet_rate': data['count'] / float(ts[-1] - ts[0]) if len(ts) > 1 else 0
        })
    
    return sorted(results, key=lambda x: x['packet_count'], reverse=True)
```

### Technique 3: Protocol Fingerprinting by Packet Size Distribution

Different messaging protocols produce characteristic packet size distributions:

```python
def protocol_fingerprint_packet_sizes(path):
    """
    Generate packet size fingerprints that can identify 
    which messaging protocol is in use from encrypted traffic alone.
    """
    from scapy.all import *
    
    packets = rdpcap(path)
    
    # Separate by flow (ip:port pair)
    flows = {}
    for pkt in packets:
        if IP in pkt and TCP in pkt:
            flow_key = f"{pkt[IP].src}:{pkt[TCP].sport}-{pkt[IP].dst}:{pkt[TCP].dport}"
            if flow_key not in flows:
                flows[flow_key] = {'sizes': [], 'timestamps': []}
            flows[flow_key]['sizes'].append(len(pkt))
            flows[flow_key]['timestamps'].append(float(pkt.time))
    
    # Generate per-flow fingerprint
    fingerprints = {}
    for flow, data in flows.items():
        sizes = np.array(data['sizes'])
        if len(sizes) < 5:
            continue
            
        # Expected patterns:
        # - Keep-alive: very small packets (60-100 bytes) at regular intervals
        # - Messages: medium packets (200-1500 bytes) in bursts
        # - Media: large packets (1500+ bytes, fragmented)
        small = np.sum(sizes < 100) / len(sizes)
        medium = np.sum((sizes >= 100) & (sizes < 500)) / len(sizes)
        large = np.sum(sizes >= 500) / len(sizes)
        
        fingerprints[flow] = {
            'pkt_count': len(sizes),
            'small_ratio': float(small),
            'medium_ratio': float(medium),
            'large_ratio': float(large),
            'mean_size': float(np.mean(sizes)),
            'std_size': float(np.std(sizes)),
            'signature': f"S:{small:.0%} M:{medium:.0%} L:{large:.0%}"
        }
    
    return fingerprints
```

### Technique 4: Metadata Leakage Analysis

Despite E2E encryption, metadata still leaks:

```bash
# 1. TLS Server Name Indication (SNI) — reveals the messaging server
tshark -r file.pcap -Y "tls.handshake.extensions_server_name" \
  -T fields -e tls.handshake.extensions_server_name 2>/dev/null | sort -u

# 2. DNS queries (may reveal messaging servers even before connection)
tshark -r file.pcap -Y "dns.flags.response == 0" \
  -T fields -e dns.qry.name -e dns.qry.type 2>/dev/null | sort -u

# 3. Certificate chains (reveal CDN / hosting provider)
tshark -r file.pcap -Y "tls.handshake.certificate" \
  -T fields -e x509sat.uTF8String 2>/dev/null | sort -u

# 4. Connection timing (when was the app used?)
tshark -r file.pcap -T fields -e frame.time_epoch \
  -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport \
  -E separator=, 2>/dev/null
```

### Technique 5: De-anonymization Vector Matrix

| Vector | Protocol | Attacker Position | Difficulty | Effectiveness |
|--------|----------|-------------------|------------|---------------|
| **Traffic Confirmation** | All | ISP / Network | Low | High — confirms communication between known parties |
| **Timing Analysis** | All | Network observer | Medium | Medium — infers activity patterns |
| **Packet Size** | All | Network observer | Low | Medium — infers message types (text vs media) |
| **SNI Leakage** | WhatsApp/Matrix | Network observer | None | High — reveals server hostname |
| **DNS Leakage** | All | Network observer | None | High — reveals server infrastructure |
| **Certificate Transparency** | All | Public logs | Low | Medium — links servers across protocols |
| **Social Graph Inference** | Matrix | Homeserver operator | Low | Very High — full graph known to server |
| **Message Count** | Signal/WhatsApp | Server operator | Medium | Medium — knows when messages sent |
| **IP Tracking** | All | Any observer | Low | High — links real IP to messaging account |
| **WebRTC IP Leak** | Telegram/WhatsApp Web | WebRTC peer | Medium | High — leaks real IP in P2P calls |

## Related Skills

- **network-protocol-analysis** — PCAP forensics foundation (extract flows, timing, protocols before running protocol-specific analysis)
- **crypto-protocol-analysis** — Cryptographic primitives (X3DH, Double Ratchet, Noise) that underpin all E2E messaging
- **anonymization-protocol-analysis** — How Tor/I2P/mixnets compare on metadata leakage vs WhatsApp/Signal

## Reference Files

- `references/dns-leak-findings.md` — Verified DNS leak results: `v.whatsapp.net`, `signal.org`, `matrix.org` visible in plaintext queries. Includes domain-to-application mapping table and detection script.

## Scripts

PoC scripts that implement these techniques (see project working directory):
- `scripts/analyze_pcap.py` — Full protocol analysis (flows, TLS, DNS, timing)
- `scripts/timing_attack.py` — Traffic confirmation via flow correlation
- `scripts/metadata_extract.py` — DNS/SNI/IP metadata leakage extraction

## Verification

```bash
# Expected output from metadata_extract.py on a PCAP with DNS queries:
#   DNS: v.whatsapp.net
#   DNS: signal.org
#   🟡 Source/destination IPs visible to all network observers

# Test traffic confirmation
python3 scripts/timing_attack.py pcaps/messaging_full_session.pcap
# Expected: 2 keep-alive patterns, 36 correlated flows
```
