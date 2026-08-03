#!/usr/bin/env bash
# verify-legaltech-gateway.sh — Verificación EN VIVO del legaltech-gateway (Go)
# Uso:  SSH_PASS='<password>' ./verify-legaltech-gateway.sh [SERVER] [SSH_USER]
# Defaults: SERVER=192.168.18.152, SSH_USER=cmansilla (VM dev del usuario)
# Salida: tests locales + estado systemd + healthz/readyz/cb-status + métricas registradas
set -uo pipefail

SERVER="${1:-192.168.18.152}"
SSH_USER="${2:-cmansilla}"
GW_DIR="${3:-/mnt/d/PyCode/legaltech-gateway}"
EXPECTED_METRICS=6   # spec SPEC-001: 6 métricas gateway_*

echo "=== 1. TESTS LOCALES (go test ./...) ==="
if [ -d "$GW_DIR" ]; then
  (cd "$GW_DIR" && go test ./... 2>&1 | grep -E '^(ok|FAIL|---)' || true)
else
  echo "⚠️  No existe $GW_DIR — saltando tests locales"
fi

echo
echo "=== 2. SERVICIO systemd + ENDPOINTS ($SERVER) ==="
if ! command -v sshpass >/dev/null 2>&1; then
  echo "⚠️  sshpass no instalado — saltando chequeo remoto (sudo apt install sshpass)"
  exit 0
fi

sshpass -p "${SSH_PASS:-}" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 \
  "$SSH_USER@$SERVER" bash -s <<'REMOTE'
set -uo pipefail
echo "--- systemctl ---"
systemctl is-active legaltech-gateway
systemctl status legaltech-gateway --no-pager 2>/dev/null | grep -E 'Active|Memory|Main PID' | head -3
echo "--- /healthz ---"
curl -s --max-time 5 http://localhost:8080/healthz; echo
echo "--- /readyz ---"
curl -s --max-time 8 http://localhost:8080/readyz; echo
echo "--- /cb-status ---"
curl -s --max-time 5 http://localhost:8080/cb-status; echo
echo "--- métricas registradas (grep '^# HELP' | grep gateway_) ---"
COUNT=$(curl -s --max-time 5 http://localhost:8080/metrics | grep '^# HELP' | grep -c gateway_ || true)
echo "gateway_ metrics: $COUNT"
REMOTE

echo
echo "Nota: si el conteo de métricas < $EXPECTED_METRICS, revisar middleware Prometheus"
echo "      (CounterVec/HistogramVec solo emiten series tras la primera observación)."
