# DNS Leak Findings: Messaging Protocol Fingerprinting

## Finding

During execution of `metadata_extract.py` against a synthetic messaging session PCAP,
DNS queries to messaging platform domains were detected in **plaintext**:

```
DNS Leak: v.whatsapp.net  (confirms WhatsApp usage)
DNS Leak: signal.org      (confirms Signal usage)
DNS Leak: matrix.org      (confirms Matrix usage)
```

## Impact

An observer on the network path (ISP, WiFi operator, VPN provider, telco)
can determine which messaging application a device is using **before any
encrypted connection is established** — the DNS query happens first.

## Why This Matters

- **No decryption needed** — DNS is text-plain by default (unless DoH/DoT is used)
- **No timing needed** — one packet is sufficient
- **No correlation needed** — direct mapping: domain → application
- **Cannot be mitigated by the messaging app** — DNS resolution is handled by the OS

## Affected Protocols

| Domain | Application | Protocol | Notes |
|--------|-------------|----------|-------|
| `*.whatsapp.net` | WhatsApp | Signal/Noise | v.whatsapp.net (WebSocket), mmg.whatsapp.net (media), web.whatsapp.net |
| `web.whatsapp.com` | WhatsApp Web | WSS | Browser-based portal |
| `*.fbcdn.net` | Meta/Facebook CDN | HTTP/2 | Serves media, stickers, profile pics |
| `signal.org` | Signal | Signal | Also textsecure, whispersystems |
| `matrix.org` | Matrix | OLM/Megolm | Also modular.im, or custom homeserver |
| `telegram.org` | Telegram | MTProto | Also t.me, venus.web.telegram.org |
| `wire.com` | Wire | Proteus | Signal-based |

## Infrastructure Mapping

WhatsApp Web connections hit multiple Meta-owned infrastructure nodes:

| Domain | Purpose | Observable? |
|--------|---------|-------------|
| `web.whatsapp.com` | Portal page (initial load) | ✅ DNS + SNI |
| `web.whatsapp.net` | WebSocket chat endpoint | ✅ DNS + SNI |
| `*.fbcdn.net` | Media/avatar CDN | ✅ DNS + SNI |
| `*.whatsapp.net` | General API | ✅ DNS + SNI |
| `*.facebook.com` | Meta auth (cross-service) | ✅ DNS + SNI |

Without ECH (Encrypted Client Hello), **all SNI hostnames are visible in TLS handshakes**.

## Mitigation

- **DNS over HTTPS (DoH)** — encrypts DNS queries (e.g., Cloudflare 1.1.1.1)
- **DNS over TLS (DoT)** — encrypts DNS queries at transport level
- **Tor** — DNS resolution happens inside Tor, not visible to observer
- **VPN with internal DNS** — queries go to VPN provider, not ISP

## Detection Script

```python
from scapy.all import *

def detect_dns_leaks(path):
    """Extract DNS queries that reveal messaging app usage"""
    packets = rdpcap(path)
    messaging_domains = ['whatsapp', 'signal', 'matrix', 'telegram', 'wire']
    leaks = []

    for pkt in packets:
        if UDP in pkt and pkt.haslayer(DNS) and pkt[DNS].qr == 0:
            qname = pkt[DNS].qd.qname.decode().rstrip('.') if pkt[DNS].qd else ''
            for domain in messaging_domains:
                if domain in qname.lower():
                    leaks.append({
                        'domain': qname,
                        'type': pkt[DNS].qd.qtype,
                        'src': pkt[IP].src,
                        'dst': pkt[IP].dst,
                        'timestamp': float(pkt.time)
                    })
    return leaks
```

## References

- RFC 8484 — DNS Queries over HTTPS (DoH)
- RFC 7858 — DNS over TLS (DoT)
- "DNS Leakage in Mobile Messaging Applications" — various academic papers
