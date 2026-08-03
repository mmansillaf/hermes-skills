# P53 Deployment — Protocol Forensics on a Real Ubuntu Machine

## Why Deploy to a Local Machine

WSL cannot do raw packet sniffing, has no GPU access for acceleration, and kills
long-running builds on timeout. A local Ubuntu machine (e.g. ThinkPad P53) solves
all three:

| Capability | WSL | P53 (Ubuntu) |
|------------|-----|--------------|
| Raw packet capture (tcpdump) | ❌ | ✅ |
| GPU acceleration (CUDA) | ❌ | ✅ Quadro T1000 |
| Long builds (Rust cargo, FAISS) | ❌ times out at 300s | ✅ background OK |
| Real network interface monitoring | ❌ | ✅ wifi/eth |
| mitmproxy (full HTTPS interception) | ❌ limited | ✅ full |

## P53 Reference Spec (from actual session)

```
Hostname:  usuario-ThinkPad-P53
IP:        192.168.18.80
OS:        Ubuntu 24.04 (kernel 7.0.0-28)
RAM:       46 GB
Disk:      233 GB NVMe (94 GB free after setup)
GPU:       Quadro T1000 (4 GB VRAM) — nvidia driver may need reinstall
User:      usuario / password (store in memory, not in this file)
SSH:       sshpass -p 'PASS' ssh usuario@192.168.18.80
```

## Initial Setup on P53

```bash
# Network tools
sudo apt install -y tshark tcpdump nmap masscan

# Python libs
pip3 install --break-system-packages scapy dpkt colorama cryptography

# Rust (for MCP servers like RAMparts)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Create project directory
mkdir -p ~/whatsapp-analysis/{scripts,pcaps,informes}
```

## WSL → P53 Deployment Workflow

Develop and test scripts in WSL first (fast iteration), then deploy to P53
for real captures and long-running builds:

```bash
# 1. Copy scripts and PCAPs to P53
sshpass -p 'PASS' scp -o StrictHostKeyChecking=no \
  /mnt/d/PyCode/hermes-skills/WhatsappDesanonimizacion/scripts/*.py \
  usuario@192.168.18.80:~/whatsapp-analysis/scripts/

sshpass -p 'PASS' scp -o StrictHostKeyChecking=no \
  /mnt/d/PyCode/hermes-skills/WhatsappDesanonimizacion/pcaps/*.pcap \
  usuario@192.168.18.80:~/whatsapp-analysis/pcaps/

# 2. Run scripts on P53
sshpass -p 'PASS' ssh usuario@192.168.18.80 \
  "cd ~/whatsapp-analysis && python3 scripts/analyze_pcap.py pcaps/messaging_full_session.pcap"

# 3. Fetch results back
sshpass -p 'PASS' scp -r usuario@192.168.18.80:~/whatsapp-analysis/informes/ \
  /mnt/d/PyCode/hermes-skills/WhatsappDesanonimizacion/informes/p53/
```

## Real Packet Capture on P53

```bash
# Capture all HTTPS traffic (WhatsApp uses WSS:443)
sshpass -p 'PASS' ssh usuario@192.168.18.80 "
echo 'PASS' | sudo -S tcpdump -i wlp82s0 -w ~/whatsapp-analysis/pcaps/capture_$(date +%Y%m%d_%H%M).pcap port 443
"

# Or a targeted capture (specific host)
sshpass -p 'PASS' ssh usuario@192.168.18.80 "
echo 'PASS' | sudo -S tcpdump -i wlp82s0 -w ~/whatsapp-analysis/pcaps/whatsapp_only.pcap host whatsapp.net or host facebook.com
"

# Quick test (5 packets, no write)
sshpass -p 'PASS' ssh usuario@192.168.18.80 "
echo 'PASS' | sudo -S timeout 5 tcpdump -i any -c 5 -nn port 443
"
```

## Building RAMparts on P53 (Background)

RAMparts (highflame-ai/ramparts) is a Rust MCP server for scanning agent
infrastructure. First Rust build takes 5-15 minutes (downloads all deps):

```bash
sshpass -p 'PASS' ssh usuario@192.168.18.80 "
cd ~/ramparts && source ~/.cargo/env && \
nohup cargo build --release > ~/ramparts_build.log 2>&1 &
echo 'Build PID: '\$!
"

# Monitor
sshpass -p 'PASS' ssh usuario@192.168.18.80 "tail -f ~/ramparts_build.log"

# Check completion
sshpass -p 'PASS' ssh usuario@192.168.18.80 "ls -lh ~/ramparts/target/release/ramparts"
```

## Pitfalls

- **nvidia-smi may fail** on the P53 even though the GPU is present — run
  `sudo apt install nvidia-driver-550` if needed
- **sshpass shows password in ps aux** — for production, use SSH keys
- **tcpdump needs sudo** — pipe password via `echo 'PASS' | sudo -S`
- **scapy.rdpcap fails on corrupt pcap** — verify with `capinfos file.pcap` first
- **WSL PATH != P53 PATH** — scripts using hardcoded WSL paths won't work on P53;
  use relative paths or environment variables
