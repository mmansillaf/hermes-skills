# Timing Side-Channels in Messaging Protocol Implementations

## Core Insight

The Double Ratchet algorithm has two distinct operations with vastly different
timing profiles:
- **Symmetric operations** (AES-GCM, ChaCha20): ~1 microsecond
- **DH operations** (X25519 key exchange): ~1 millisecond

This 1000x timing difference is observable by a network adversary.

## Where Timing Differentials Occur

### 1. Out-of-Order Message Delivery

When messages arrive out of order, the recipient must:
1. Attempt decryption with the current chain key → fails (~1μs)
2. Search skipped message keys (~1μs per key)
3. If not found, perform a DH ratchet step (~1ms)

**Leaked information:** An observer can tell when messages are out of order.

### 2. New Session Establishment

The X3DH handshake involves:
1. Fetching PreKeys from server (network round-trip)
2. Computing 3-4 ECDH operations (~3-4ms total)
3. HKDF key derivation (~10μs)

**Leaked information:** Session establishment is visibly different from message exchange.

### 3. Chain Ratchet Steps

Each message advances the sending or receiving chain:
- Normal: symmetric decryption only (~1μs)
- Ratchet step: includes DH computation (~1ms)

**Leaked information:** The DH ratchet frequency can be estimated from timing.

## Attack Model

```
Adversary position:   Network observer (ISP, WiFi, backbone tap)
What they see:        Encrypted packets at specific times
What they infer:      1. Session establishment events
                      2. Out-of-order delivery
                      3. Message volume (via chain steps)
```

## Practical Measurement

```python
import time
from cryptography.hazmat.primitives.asymmetric import x25519

def measure_timing_differential():
    """Demonstrate the 1000x timing difference"""
    
    # Symmetric timing (AES-GCM simulated)
    data = b'A' * 256  # typical message size
    key = b'K' * 32
    
    symmetric_times = []
    for _ in range(1000):
        start = time.perf_counter()
        _ = bytes([a ^ b for a, b in zip(data, key)])  # XOR proxy for symmetric
        symmetric_times.append(time.perf_counter() - start)
    
    # DH timing (real X25519)
    dh_times = []
    for _ in range(100):
        start = time.perf_counter()
        sk = x25519.X25519PrivateKey.generate()
        pk = sk.public_key()
        dh_times.append(time.perf_counter() - start)
    
    print(f"Symmetric (XOR): mean={np.mean(symmetric_times)*1e6:.1f}μs")
    print(f"DH (X25519):     mean={np.mean(dh_times)*1e6:.1f}μs")
    print(f"Ratio:           {np.mean(dh_times)/max(np.mean(symmetric_times), 1e-9):.0f}x")
```

## Mitigation

- **Constant-time operations** — pad all crypto operations to the same duration
- **Cover traffic** — send dummy messages at random intervals to confuse timing
- **Batched decryption** — delay decryption to hide per-message timing

## References

- "Timing Attacks on the Signal Protocol" — various researchers
- "A Formal Security Analysis of the Signal Messaging Protocol" — Cohn-Gordon et al.
- X25519 timing safety: https://cr.yp.to/ecdh.html
