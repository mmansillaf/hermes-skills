#!/bin/bash
# Lanza 2 Chromes independientes con puertos de debugging distintos
# Cada uno con su propio perfil para evitar conflictos

CHROME="/usr/bin/google-chrome"

echo "[*] Matando instancias previas..."
pkill -f "chrome.*cej_puerto_9222" 2>/dev/null
pkill -f "chrome.*cej_puerto_9223" 2>/dev/null
sleep 2

echo "[*] Lanzando Chrome A (puerto 9222)..."
mkdir -p /tmp/chrome_cej_A
$CHROME \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome_cej_A \
  --no-first-run \
  --no-default-browser-check \
  --disable-sync \
  --disable-default-apps \
  --no-sandbox \
  --disable-dev-shm-usage \
  https://cej.pj.gob.pe/cej/forms/busquedaform.html \
  > /dev/null 2>&1 &
CHROME_A_PID=$!
echo "  PID: $CHROME_A_PID"

echo "[*] Lanzando Chrome B (puerto 9223)..."
mkdir -p /tmp/chrome_cej_B
$CHROME \
  --remote-debugging-port=9223 \
  --user-data-dir=/tmp/chrome_cej_B \
  --no-first-run \
  --no-default-browser-check \
  --disable-sync \
  --disable-default-apps \
  --no-sandbox \
  --disable-dev-shm-usage \
  https://cej.pj.gob.pe/cej/forms/busquedaform.html \
  > /dev/null 2>&1 &
CHROME_B_PID=$!
echo "  PID: $CHROME_B_PID"

echo ""
echo "[*] Esperando que Chromes arranquen..."
sleep 8

for port in 9222 9223; do
    if ss -tlnp | grep -q ":$port "; then
        echo "  Puerto $port: OK"
    else
        echo "  Puerto $port: NO RESPONDE"
    fi
done

echo ""
echo "Chrome A PID=$CHROME_A_PID en puerto 9222"
echo "Chrome B PID=$CHROME_B_PID en puerto 9223"
echo ""
echo "Para ejecutar los spiders (SECUENCIALMENTE, no simultaneo):"
echo "  python3 run_A_parallel.py  (offset=0, limit=5)"
echo "  python3 run_B_parallel.py  (offset=5, limit=5)"
