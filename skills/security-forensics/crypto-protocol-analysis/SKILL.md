---
name: crypto-protocol-analysis
title: Crypto Protocol Analysis — Noise, Double Ratchet, X3DH, TLS 1.3
description: Mathematical and practical analysis of cryptographic protocols used in secure messaging — Noise Protocol Framework, Double Ratchet (Signal), X3DH key agreement, TLS 1.3 handshake. Techniques for protocol verification, timing side-channels, and cryptographic metadata extraction.
trigger: User needs to understand or analyze the cryptographic primitives behind secure messaging protocols, or research side-channel attacks on cryptographic implementations.
tags: [cryptography, protocol-analysis, noise-protocol, double-ratchet, x3dh, tls, side-channel, security-protocols]
domain: security-forensics
---
# Crypto Protocol Analysis — Noise, Double Ratchet, X3DH, TLS 1.3

## When to Use

- Analyzing the Signal Protocol's cryptographic construction (X3DH + Double Ratchet)
- Understanding Noise Protocol patterns in messaging apps (WhatsApp uses Noise Pipes)
- TLS 1.3 handshake analysis and fingerprinting
- Researching timing side-channels in cryptographic implementations
- Protocol verification — does the implementation match the spec?

## Protocol Deep Dives

### Noise Protocol Framework (WhatsApp's Transport)

WhatsApp uses Noise Pipes with the XX pattern (based on the Noise Protocol Framework).

```
Noise XX Pattern:
  → e
  ← e, ee, s, es
  → s, se
  
Where: e=ephemeral key, s=static key, ee=ECDH(e,e), es=ECDH(e,s), se=ECDH(s,e)
```

**Analysis script:**

```python
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import os

def noise_xx_handshake_analysis():
    """
    Simulate and analyze the Noise XX handshake
    to understand what metadata is exchanged.
    """
    # Generate ephemeral keys (simulating both sides)
    initiator_eph = x25519.X25519PrivateKey.generate()
    responder_eph = x25519.X25519PrivateKey.generate()
    
    # In a real handshake, these would be exchanged
    initiator_pub = initiator_eph.public_key()
    responder_pub = responder_eph.public_key()
    
    # ECDH key agreements
    # ee = ECDH(initiator_eph, responder_eph) 
    # es = ECDH(initiator_eph, responder_static)
    # se = ECDH(initiator_static, responder_eph)
    
    print("=== Noise XX Handshake Analysis ===")
    print(f"Initiator ephemeral pubkey: {initiator_pub.public_bytes_raw().hex()[:32]}...")
    print(f"Responder ephemeral pubkey: {responder_pub.public_bytes_raw().hex()[:32]}...")
    print(f"Key size: 32 bytes (X25519)")
    print(f"Public keys are exchanged IN THE CLEAR")
    print(f"→ Unique fingerprint per session (de-anonymization risk)")
    print()
    print("Metadata leaked in Noise handshake:")
    print(" - Ephemeral public keys (unique per session)")
    print(" - Static public key hashes (long-term identity)")
    print(" - Ciphertext length (can infer message type)")
    print(" - Handshake timing (devices, network conditions)")
    
    return {
        'protocol': 'Noise_XX',
        'key_exchange': 'X25519',
        'cipher': 'AES-256-GCM / ChaCha20-Poly1305',
        'hash': 'SHA-256',
        'exchanged_in_clear': ['ephemeral_pubkeys'],
        'derived_secretly': ['handshake_hash', 'chaining_key', 'symmetric_key']
    }
```

### X3DH — Extended Triple Diffie-Hellman (Signal/WhatsApp)

```
Initial key agreement for Signal Protocol:
  DH1 = ECDH(IK_A, SPK_B)
  DH2 = ECDH(EK_A, IK_B)
  DH3 = ECDH(EK_A, SPK_B)
  DH4 = ECDH(EK_A, OPK_B)  # optional
  SK = KDF(DH1 || DH2 || DH3 || DH4)
  
Where: IK=Identity Key, SPK=Signed PreKey, EK=Ephemeral Key, OPK=One-Time PreKey
```

```python
def x3dh_metadata_analysis():
    """
    Analyze what X3DH leaks to the server and to participants.
    """
    print("=== X3DH Metadata Analysis ===")
    print()
    print("PRE-KEY SERVER KNOWS:")
    print(" - Identity Key (IK) of ALL users (long-term)")
    print(" - Signed PreKey (SPK) of ALL users")
    print(" - One-Time PreKeys (OPK) pool → can count users")
    print(" - IK → Phone# mapping (if server has it)")
    print()
    print("SENDER SENDS TO SERVER:")
    print(" - Identity Key IK_A (who you are)")
    print(" - Ephemeral Key EK_A (session identifier)")
    print(" - Which PreKey(s) used → who you're messaging")
    print()
    print("→ THE SERVER KNOWS WHO IS TALKING TO WHOM")
    print("  (despite E2E encryption of message content)")
    print()
    print("DE-ANONYMIZATION VECTORS:")
    vectors = [
        ("PreKey retrieval timing", "Server logs when A fetches B's PreKeys"),
        ("Message delivery timing", "Server knows when messages are delivered"),
        ("Identity key rotation", "Can track devices over time"),
        ("Sealed Sender (WhatsApp)", "Hides sender from server, but not metadata")
    ]
    for name, detail in vectors:
        print(f"  [{name}] {detail}")

x3dh_metadata_analysis()
```

### Double Ratchet (Continuous Key Agreement)

```python
def double_ratchet_analysis():
    """
    Analyze the Double Ratchet for side-channel implications.
    """
    print("=== Double Ratchet Analysis ===")
    print()
    print("Ratchets:")
    print("  Root Chain Ratchet: triggered by DH ratchet step")
    print("  Sending Chain Ratchet: triggered by each outgoing message") 
    print("  Receiving Chain Ratchet: triggered by each incoming message")
    print()
    print("SIDE-CHANNEL IMPLICATIONS:")
    print(" - Number of messages sent = number of chain steps")
    print(" - If chain is out of sync, extra DH operations occur")
    print(" - DH operations are ~1ms → visible in timing side-channel")
    print(" - Deleted messages still advance the ratchet (hole)")
    print()
    print("TIMING SIDE-CHANNEL:")
    print("  Normal message: symmetric decryption (~1μs)")
    print("  Out-of-order message: DH computation (~1ms)")
    print("  → An observer can detect out-of-order delivery!")
    
    return True
```

### TLS 1.3 Handshake Fingerprinting

```bash
# 1. Extract TLS version and cipher suites
tshark -r pcaps/tls12.pcap -Y "tls.handshake.type == 1" \
  -T fields -e tls.handshake.version \
  -e tls.handshake.ciphersuite 2>/dev/null | sort -u

# 2. Extract supported groups (key exchange type)
tshark -r pcaps/tls12.pcap -Y "tls.handshake.type == 1" \
  -T fields -e tls.handshake.extensions_supported_group 2>/dev/null

# 3. JA3 fingerprint (identifies client)
# Requires custom script - see Technique 5
```

### TLS Fingerprinting with Python

```python
from scapy.all import *

def tls_fingerprint(path):
    """Generate JA3-style fingerprint from ClientHello"""
    packets = rdpcap(path)
    
    for i, pkt in enumerate(packets):
        if TCP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw])
            # ClientHello marker
            if len(payload) > 5 and payload[0] == 0x16 and payload[5] == 0x01:
                print(f"Packet {i}: TLS ClientHello from {pkt[IP].src}")
                print(f"  Version: 0x{payload[9]:02x}{payload[10]:02x}")
                print(f"  Session ID len: {payload[43]}")
                
                # Extract cipher suites (rough parsing)
                cipher_offset = 44 + payload[43]
                if cipher_offset + 2 < len(payload):
                    cipher_len = (payload[cipher_offset] << 8) | payload[cipher_offset + 1]
                    ciphers = []
                    for j in range(0, cipher_len, 2):
                        cs = (payload[cipher_offset + 2 + j] << 8) | payload[cipher_offset + 3 + j]
                        ciphers.append(hex(cs))
                    print(f"  Cipher suites ({cipher_len//2}): {','.join(ciphers[:5])}...")
                
                return {
                    'packet': i,
                    'src': pkt[IP].src,
                    'dst': pkt[IP].dst,
                    'tls_version': f"0x{payload[9]:02x}{payload[10]:02x}"
                }
    return None
```

## Related Skills

- **network-protocol-analysis** — Extract TLS handshakes and timing from PCAPs before fingerprinting
- **p2p-messaging-forensics** — How X3DH + Double Ratchet are concretely implemented in WhatsApp/Signal/Matrix
- **anonymization-protocol-analysis** — How anonymization protocols handle key exchange differently (Tor's ntor, I2P's ElGamal)

## Reference Files

- `references/side-channel-timing.md` — Timing side-channels in Double Ratchet implementations (DH ops ~1ms vs symmetric ~1μs). Attack model and measurement script with X25519.

## Verification

```bash
# Test TLS fingerprinting on a PCAP with TLS handshakes
python3 -c "
from scapy.all import *
p = rdpcap('pcaps/messaging_full_session.pcap')
print('PCAP:', len(p), 'packets')
tls_pkts = [(i,pkt) for i,pkt in enumerate(p) if TCP in pkt and Raw in pkt and bytes(pkt[Raw])[:1]==b'\\x16']
print('TLS handshakes:', len(tls_pkts))
"

# Test X3DH analysis
python3 -c "
from cryptography.hazmat.primitives.asymmetric import x25519
sk = x25519.X25519PrivateKey.generate()
print('X25519 key:', sk.public_key().public_bytes_raw().hex()[:32], '...')
print('Key exchange: OK')
"
```
