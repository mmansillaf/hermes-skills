---
name: anonymization-protocol-analysis
title: Anonymization Protocol Analysis — Tor, I2P, Mixnets
description: Deep analysis of anonymization protocols — Tor (onion routing), I2P (garlic routing), mixnets (Loopix, Nym). Cell structure analysis, circuit construction, timing attacks, traffic confirmation, and de-anonymization vectors in anonymous communication systems.
trigger: User needs to research anonymization protocols, understand de-anonymization attacks on Tor/I2P, or analyze traffic patterns in anonymity networks.
tags: [anonymization, tor, i2p, mixnets, onion-routing, garlic-routing, traffic-analysis, de-anonymization, timing-attack]
domain: security-forensics
---
# Anonymization Protocol Analysis — Tor, I2P, Mixnets

## When to Use

- Researching de-anonymization vectors in Tor, I2P, or mixnet protocols
- Understanding circuit construction and cell structure in onion routing
- Analyzing timing-based attacks on anonymous communication
- Comparing anonymization properties across protocols
- Investigating traffic confirmation and intersection attacks

## Protocol Reference

### Tor (The Onion Router)

```
Architecture:
  Client → Guard Node → Middle Node → Exit Node → Destination
  
Cell Structure:
  [Circuit ID: 2 bytes][Command/Relay: 1 byte][Payload: 509 bytes] = 512 bytes fixed

Circuit Setup:
  Client ↔ Guard:     CREATE (DH handshake) → CREATED
  Client ↔ Middle:    EXTEND (relayed through Guard) → EXTENDED
  Client ↔ Exit:      EXTEND (relayed through Middle) → EXTENDED
  
Cell Types:
  0x07 = CREATE  0x08 = CREATED
  0x09 = RELAY   0x0A = RELAY_EARLY
  0x0B = DESTROY
  
Relay Cells (inside encrypted layer):
  [Relay command: 1b][Recognized: 2b][Stream ID: 2b]
  [Digest: 4b][Length: 2b][Data: ≤498b][Padding]

De-anonymization Vectors:
  - Traffic Confirmation (end-to-end timing correlation)
  - Guard Discovery (forced circuit creation probes)
  - Website Fingerprinting (packet size/time patterns)
  - Sybil Attacks (run malicious nodes to capture circuits)
  - Cell Counting (correlate cells at entry and exit)
```

### I2P (Invisible Internet Project)

```
Architecture:  Garlic Routing (bundle multiple messages)
  Client → Peers → Destination (no fixed exit node)
  
Tunnel Structure:
  Inbound Tunnel:  Gateway → 0 hops ... → Endpoint → Destination
  Outbound Tunnel: Source → Gateway → 0 hops ... → Endpoint

Key Difference from Tor:
  - Both sender AND receiver build tunnels
  - Messages are garlic cloves (bundled)
  - No public exit node → less monitoring risk
  - But: more complex, higher latency

De-anonymization Vectors:
  - Tunnel timing correlation (inbound/outbound pairing)
  - NetDB lookups (DHT-based, can be monitored)
  - Floodfill node compromise
  - Router fingerprinting (uptime, bandwidth, version)
```

### Mixnets (Loopix, Nym)

```
Architecture:
  Sender → [Mix Node 1] → [Mix Node 2] → [Mix Node 3] → Recipient
  
Key Properties:
  - Cover traffic (dummy messages)
  - Poisson mixing (variable delay per node)
  - Stop-and-go (Sphinx packet format)
  - Continuous mixing (no fixed batch size)

De-anonymization Vectors:
  - Intersection attacks (long-term observation)
  - Cover traffic analysis (dummy vs real message detection)
  - Timing fingerprinting (if cover traffic patterns are detectable)
  - Sybil attacks on mix nodes
```

## Forensic Techniques

### Technique 1: Tor Cell Structure Analysis

```python
from scapy.all import *
import struct

def analyze_tor_cells(path):
    """
    Detect and analyze Tor cells in a PCAP.
    Tor uses fixed 512-byte cells on port 9001, 9090, or 443/80 (obfs4).
    """
    packets = rdpcap(path)
    tor_cells = []

    for i, pkt in enumerate(packets):
        if TCP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw])
            
            # Tor cells are 512 bytes (or 514 with TLS record overhead)
            # Cell format: [CircuitID: 2][Command: 1][Payload: 509]
            if len(payload) == 512 or len(payload) == 514:
                # Try to parse as Tor cell
                if len(payload) >= 3:
                    circ_id = struct.unpack('!H', payload[0:2])[0]
                    cmd = payload[2]
                    
                    # Valid Tor commands
                    if cmd in [0x07, 0x08, 0x09, 0x0A, 0x0B]:
                        cmd_names = {7: 'CREATE', 8: 'CREATED', 
                                     9: 'RELAY', 10: 'RELAY_EARLY', 11: 'DESTROY'}
                        tor_cells.append({
                            'packet': i,
                            'circuit_id': circ_id,
                            'command': cmd_names.get(cmd, f'UNKNOWN_{cmd}'),
                            'src': pkt[IP].src,
                            'dst': pkt[IP].dst,
                            'port': pkt[TCP].dport
                        })

    return {
        'total_tor_cells': len(tor_cells),
        'circuits_found': len(set(c['circuit_id'] for c in tor_cells)),
        'cells': tor_cells[:20]  # first 20
    }
```

### Technique 2: Traffic Confirmation Attack Simulation

```python
import numpy as np
from scapy.all import *

def simulate_traffic_confirmation(path):
    """
    Simulate a traffic confirmation attack on Tor-like traffic.
    Correlate packet timing at entry and exit of a circuit.
    """
    packets = rdpcap(path)
    
    # 1. Group packets by IP pair (simulating circuit segments)
    segments = {}
    for pkt in packets:
        if IP in pkt:
            key = (pkt[IP].src, pkt[IP].dst, pkt[IP].dst, pkt[IP].src)
            # Use direction (src→dst)
            pair = (pkt[IP].src, pkt[IP].dst)
            if pair not in segments:
                segments[pair] = {'times': [], 'sizes': []}
            segments[pair]['times'].append(float(pkt.time))
            segments[pair]['sizes'].append(len(pkt))
    
    # 2. Find potential circuit pairs (entry + exit of same circuit)
    # In Tor: entry traffic comes in one side, exits from another
    # We look for correlated timing patterns
    
    if len(segments) < 2:
        return {'message': 'Need at least 2 IP pairs for correlation'}
    
    # Simplest: cross-correlation of packet arrival times
    ip_pairs = list(segments.keys())
    correlations = []
    
    for i in range(len(ip_pairs)):
        for j in range(i+1, len(ip_pairs)):
            t1 = np.array(segments[ip_pairs[i]]['times'])
            t2 = np.array(segments[ip_pairs[j]]['times'])
            
            if len(t1) < 3 or len(t2) < 3:
                continue
            
            # Count how many packets within a small time window (200ms)
            window = 0.2  # 200ms
            correlated = 0
            for t in t1:
                if np.any(np.abs(t2 - t) < window):
                    correlated += 1
            
            corr_score = correlated / max(len(t1), len(t2))
            correlations.append({
                'pair1': f"{ip_pairs[i][0]}→{ip_pairs[i][1]}",
                'pair2': f"{ip_pairs[j][0]}→{ip_pairs[j][1]}",
                'correlation': float(corr_score),
                'matched_packets': correlated,
                'total_packets': min(len(t1), len(t2))
            })
    
    return sorted(correlations, key=lambda x: x['correlation'], reverse=True)[:5]
```

### Technique 3: Website Fingerprinting Analysis

```python
def website_fingerprinting(path):
    """
    Analyze packet sequences for website fingerprinting.
    Tor traffic preserves packet sizes within cells.
    """
    from scapy.all import *
    
    packets = rdpcap(path)
    
    # Extract packet size sequence (direction-aware)
    # + = outgoing, - = incoming
    sequence = []
    first_ip = None
    
    for pkt in packets:
        if IP in pkt:
            if first_ip is None:
                first_ip = pkt[IP].src
            
            direction = 1 if pkt[IP].src == first_ip else -1
            size = len(pkt) * direction
            sequence.append(size)
    
    if not sequence:
        return {'message': 'Empty sequence'}
    
    # Statistical fingerprint
    seq_arr = np.array(sequence)
    pos = seq_arr[seq_arr > 0]
    neg = seq_arr[seq_arr < 0]
    
    fingerprint = {
        'total_packets': len(sequence),
        'outgoing_count': int(np.sum(seq_arr > 0)),
        'incoming_count': int(np.sum(seq_arr < 0)),
        'outgoing_bytes': int(np.sum(pos)),
        'incoming_bytes': int(abs(np.sum(neg))),
        'ratio_out_in': float(len(pos) / max(len(neg), 1)),
        'burst_count': int(np.sum(np.abs(np.diff(seq_arr > 0)))),
        'mean_burst_size': float(np.mean([abs(s) for s in sequence])) if sequence else 0
    }
    
    return fingerprint
```

### Technique 4: Protocol Comparison Matrix

| Property | Tor | I2P | Mixnets (Nym) | Signal/WhatsApp |
|----------|-----|-----|---------------|-----------------|
| **Anonymity set** | Users | Users | Users | None |
| **E2E encryption** | Layer (onion) | Layer (garlic) | Layer (Sphinx) | App-level (Signal) |
| **Metadata protection** | Low (IP known to entry) | Medium (IP known to peers) | High (cover traffic) | None (server knows) |
| **Latency** | ~100ms-2s | ~1s-10s | ~5s-60s | ~100ms-1s |
| **Traffic confirmation** | Vulnerable | Harder | Resistant | Vulnerable |
| **Timing attack** | Vulnerable | Vulnerable | Resistant (cover) | Vulnerable |
| **Message unobservability** | No | Partial | Yes | No |
| **Sender anonymity** | Yes (from destination) | Yes (from destination) | Yes | No |
| **Receiver anonymity** | No | Yes | Yes | No |
| **Deployability** | High (widespread) | Medium | Low (early) | Very High |

## Verification

```bash
# Test Tor cell detection
python3 -c "
from scapy.all import *
p = rdpcap('pcaps/test_messaging.pcap')
print('Tor analysis on test pcap:', len(p), 'packets')
# Most traffic is NOT Tor, so this should return 0 cells
print('Expected: 0 Tor cells (test pcap has synthetic messaging traffic)')
"
```

## Related Skills

- **network-protocol-analysis** — PCAP forensics foundation needed to analyze Tor/I2P traffic captures from real networks
- **p2p-messaging-forensics** — Contrast anonymized vs non-anonymized messaging (WhatsApp leaks grafo social, Tor does not)
- **crypto-protocol-analysis** — Cryptographic primitives used in onion/garlic routing (ntor for Tor, ElGamal for I2P, Sphinx for mixnets)

## Papers & References

- Tor Specification: https://spec.torproject.org/tor-spec/
- I2P Spec: https://geti2p.net/en/docs
- Nym Whitepaper: https://nym.com/docs/whitepaper
- "Traffic Confirmation Attacks" — Danezis & Clayton (2007)
- "Circuit Fingerprinting Attacks" — Kwon et al. (2017)
- "The Loopix Anonymity System" — Piotrowska et al. (2017)
- "Tearing apart WhatsApp" — Cowan et al.
