# WhatsApp Web Live Capture — Real-World Metadata Leakage Test

## Overview

WhatsApp Web (`web.whatsapp.com`) uses WebSocket Secure (WSS) connections
for real-time messaging. The browser establishes a persistent WSS tunnel
to `wss://web.whatsapp.net/ws/chat` after QR-code authentication.

Even with WSS encryption, significant metadata leaks to any network observer
(ISP, WiFi operator, router admin):

## Setup

**Requirements:**
- A Linux machine with `tcpdump` and `tshark` (WSL cannot do this — use
  a real Ubuntu machine like P53)
- Phone with WhatsApp (to scan QR code)
- Browser on the capture machine

**Capture command (30 seconds):**
```bash
sudo timeout 30 tcpdump -i wlp82s0 \
  -w ~/whatsapp-analysis/capturas/whatsapp_live.pcap \
  "port 53 or port 443 or port 80 or port 5222"
```

**After capture, run this analysis:**
```bash
echo "=== DNS (plaintext) ==="
tshark -r capture.pcap -Y "dns.flags.response == 0" \
  -T fields -e dns.qry.name | sort -u

echo "=== SNI (TLS) ==="
tshark -r capture.pcap -Y "tls.handshake.extensions_server_name" \
  -T fields -e tls.handshake.extensions_server_name | sort -u

echo "=== IPs contacted ==="
tshark -r capture.pcap -q -z ip_hosts,tree | head -20

echo "=== Protocol hierarchy ==="
tshark -r capture.pcap -q -z io,phs

echo "=== Timing bursts ==="
tshark -r capture.pcap -T fields -e frame.time_epoch \
  -e ip.src -e frame.len | head -30
```

## Expected Observations

| What leaks | Example | Risk |
|------------|---------|------|
| DNS query | `web.whatsapp.com` | 🔴 Confirms WhatsApp use |
| DNS query | `web.whatsapp.net` | 🔴 Confirms WebSocket endpoint |
| SNI | `*.fbcdn.net` | 🟡 Meta CDN infrastructure |
| SNI | `*.whatsapp.net` | 🟡 WhatsApp server |
| Packet burst | Activity spike after silence | 🟡 Message timing |
| Packet size variance | Text ~200B vs media ~10KB | 🟡 Content type inference |
| Server IPs | Meta's AS32934 IPs | 🟡 Infrastructure mapping |
| WebSocket frames | Count correlates to msgs | 🟡 Activity level |
| Keep-alive | Regular ~45s pings | 🟢 Device state (foreground/bg) |
| TLS handshake | Encryption parameters | 🟢 Client fingerprint (OS/browser) |

## What Does NOT Leak (E2E Encryption)

- Message content (text, media)
- Contact names/phone numbers
- Group names/membership (from traffic)
- Media files sent/received

## De-anonymization Vectors Demonstrated

1. **Identity confirmation** — DNS+SNI+IPs confirm the user is on WhatsApp
2. **Timing correlation** — Burst patterns correlate to message activity
3. **Infrastructure mapping** — Server IPs reveal Meta's infrastructure
4. **Traffic confirmation** — If both parties' traffic is observable, timing
   correlation can confirm they're communicating (requires both ends observable)

## Ethics Note

This captures metadata that any network operator (ISP, WiFi provider) can
observe. No decryption of message content is attempted or needed. For a
thesis on de-anonymization, this demonstrates what an adversary with network
access can learn without breaking encryption.
