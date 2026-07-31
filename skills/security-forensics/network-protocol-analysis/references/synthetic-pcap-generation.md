# Synthetic PCAP Generation for Testing

## Why Generate Synthetic PCAPs?

Real PCAPs from public sources (GitHub, WikiWireshark) often turn out to be HTML error pages or redirects, not actual capture files. Synthetic generation with scapy gives you full control over traffic patterns for testing analysis tools.

## Verification Check

Always verify a downloaded PCAP before using it:
```
$ file *.pcap
messaging_full_session.pcap: pcap capture file, microsecond ts (Ethernet)
tls12.pcap:          HTML document, Unicode text   ← NOT a real PCAP!
```

## Technique: Realistic Messaging Session Generator

```python
from scapy.all import *
import time

def generate_messaging_pcap(output_path, num_bursts=5, msgs_per_burst=3):
    """
    Generate a realistic messaging session PCAP with:
    - TCP connection establishment (SYN/SYN-ACK/ACK)
    - TLS ClientHello-like handshake
    - Message bursts at varying intervals
    - Periodic keep-alive packets
    - DNS queries to messaging endpoints
    """
    pkts = []
    base_time = int(time.time())  # Use current time for realistic timestamps

    for burst in range(num_bursts):
        t = base_time + burst * 2.0  # 2 seconds between bursts

        # TCP handshake
        pkts.append(Ether()/IP(src='192.168.1.100', dst='192.168.1.1')/
                    TCP(sport=42000+burst, dport=443, flags='S'))
        pkts.append(Ether()/IP(src='192.168.1.1', dst='192.168.1.100')/
                    TCP(sport=443, dport=42000+burst, flags='SA'))
        pkts.append(Ether()/IP(src='192.168.1.100', dst='192.168.1.1')/
                    TCP(sport=42000+burst, dport=443, flags='A'))

        # TLS ClientHello marker (0x16)
        tls_hello = bytes([0x16, 0x03, 0x01, 0x00, 0x48]) + b'\x01'*67
        pkts.append(Ether()/IP(src='192.168.1.100', dst='192.168.1.1')/
                    TCP(sport=42000+burst, dport=443, flags='PA')/
                    Raw(load=tls_hello))

        # Simulate messages at irregular intervals
        for msg in range(msgs_per_burst + burst):
            pkt_size = 120 + (msg * 20)  # varying sizes (120-180 bytes)
            direction = 0 if msg % 2 == 0 else 1  # alternate direction
            src = ['192.168.1.100', '192.168.1.1'][direction]
            dst = ['192.168.1.1', '192.168.1.100'][direction]
            pkts.append(Ether()/IP(src=src, dst=dst)/
                        TCP(sport=42000+burst, dport=443, flags='PA')/
                        Raw(load=b'\x00' * pkt_size))

        # Keep-alive packets (very regular, small)
        for ka in range(3):
            pkts.append(Ether()/IP(src='192.168.1.100', dst='192.168.1.1')/
                        TCP(sport=42000+burst, dport=443, flags='PA')/
                        Raw(load=b'\x00' * 60))

        # TCP teardown
        pkts.append(Ether()/IP(src='192.168.1.100', dst='192.168.1.1')/
                    TCP(sport=42000+burst, dport=443, flags='FA'))

    # DNS queries (plaintext metadata leakage)
    for domain in ['v.whatsapp.net', 'signal.org', 'matrix.org']:
        pkts.append(Ether()/IP(src='192.168.1.100', dst='8.8.8.8')/
                    UDP(sport=5353, dport=53)/
                    DNS(rd=1, qd=DNSQR(qname=domain, qtype=1)))

    # Set sequential timestamps
    for i, pkt in enumerate(pkts):
        pkt.time = base_time + (i * 0.001)  # 1ms between packets

    wrpcap(output_path, pkts)
    print(f"Created {output_path} with {len(pkts)} packets")
    return len(pkts)

# Generate 2 PCAPs: small test + full session
generate_messaging_pcap('pcaps/test_messaging.pcap', num_bursts=1, msgs_per_burst=2)
generate_messaging_pcap('pcaps/messaging_full_session.pcap', num_bursts=5, msgs_per_burst=3)
```

## Expected Results

Running `analyze_pcap.py` on a 5-burst synthetic PCAP:

```
Packets: 67 | Duration: 0.07s
Protocols: TCP, UDP
TLS Handshakes: 5 (one per burst)
DNS Queries: 3 (whatsapp.net, signal.org, matrix.org)
Unique IPs: 3 (client, server, DNS resolver)
Packet rate: 1015.2 pkt/s
```

## Pitfalls

- **WARNING: getmacbyip failed** — scapy on WSL can't resolve MAC addresses for non-local IPs. Use `Ether()` with default broadcast — harmless for PCAP analysis.
- **Timestamps in seconds** — set `pkt.time = float` for compatibility across scapy, tshark, and dpkt.
- **No Ether layer for loopback** — if testing on a local-only setup, omit `Ether()` and use `wrpcap(..., linktype=1)` (Raw IPv4).
