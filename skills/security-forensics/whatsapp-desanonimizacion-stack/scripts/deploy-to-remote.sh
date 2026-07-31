#!/bin/bash
# deploy-to-remote.sh — Deploy WhatsApp forensics stack from WSL to a remote Ubuntu machine
# Usage: ./deploy-to-remote.sh <USER@HOST> [PASSWORD]
#
# Example:
#   ./deploy-to-remote.sh usuario@192.168.18.80
#   (reads PASSWORD from SSH_PASS env var or prompts)

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <USER@HOST> [PASSWORD]"
    echo "  or set SSH_PASS environment variable"
    exit 1
fi

TARGET="$1"
PASS="${2:-$SSH_PASS}"
PROJECT_DIR="/mnt/d/PyCode/hermes-skills/WhatsappDesanonimizacion"
REMOTE_DIR="~/whatsapp-analysis"

if [ -z "$PASS" ]; then
    read -s -p "Password for $TARGET: " PASS
    echo
fi

SSH_CMD="sshpass -p '$PASS' ssh -o StrictHostKeyChecking=no $TARGET"
SCP_CMD="sshpass -p '$PASS' scp -o StrictHostKeyChecking=no"

echo "=== Deploying WhatsApp Forensics Stack ==="
echo "  From: $PROJECT_DIR"
echo "  To:   $TARGET:$REMOTE_DIR"
echo

# 1. Create remote directory structure
echo "[1/5] Creating remote directories..."
eval "$SSH_CMD" "mkdir -p $REMOTE_DIR/{scripts,pcaps,informes}" 2>/dev/null

# 2. Install remote dependencies
echo "[2/5] Installing system dependencies..."
eval "$SSH_CMD" "
echo '$PASS' | sudo -S apt-get install -y -qq tshark tcpdump nmap masscan 2>&1 | tail -1
pip3 install --break-system-packages -q scapy dpkt colorama 2>&1 | tail -1
" 2>/dev/null

# 3. Copy scripts
echo "[3/5] Copying scripts..."
eval "$SCP_CMD" "$PROJECT_DIR/scripts/"*.py "$TARGET:$REMOTE_DIR/scripts/" 2>/dev/null
echo "  -> $(ls "$PROJECT_DIR"/scripts/*.py | wc -l) scripts copied"

# 4. Copy PCAPs
echo "[4/5] Copying PCAPs..."
eval "$SCP_CMD" "$PROJECT_DIR/pcaps/"*.pcap "$TARGET:$REMOTE_DIR/pcaps/" 2>/dev/null
echo "  -> $(ls "$PROJECT_DIR"/pcaps/*.pcap 2>/dev/null | wc -l) pcaps copied"

# 5. Verify
echo "[5/5] Verifying deployment..."
eval "$SSH_CMD" "
echo '=== Remote Files ==='
find $REMOTE_DIR -type f | sort
echo ''
echo '=== Tools ==='
tshark --version 2>&1 | head -1
python3 -c 'import scapy; print(\"scapy: OK\")'
python3 -c 'import dpkt; print(\"dpkt: OK\")'
" 2>/dev/null

echo
echo "=== Deploy complete ==="
echo "Run scripts: eval \"$SSH_CMD\" \"cd $REMOTE_DIR && python3 scripts/analyze_pcap.py pcaps/messaging_full_session.pcap\""
echo "Live capture: eval \"$SSH_CMD\" \"echo '$PASS' | sudo -S timeout 10 tcpdump -i any -c 10 -nn port 443\""
