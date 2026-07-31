#!/bin/bash
# Watchdog v2: relanza spider CEJ automáticamente ante cualquier fallo
# Uso: bash watchdog.sh A   (para Spider A)
#       bash watchdog.sh B   (para Spider B)
#
# Versión 2 (Jun 2026): detecta más patrones de crash que v1:
#   - chrome_dead, radware_blocked (originales)
#   - Remote end closed connection, Connection refused (nuevos)
#   - Max retries exceeded, Connection aborted (nuevos)
#   - chrome not reachable, invalid session (nuevos)
# También limpia Chrome huérfano entre reintentos y verifica
# item_scraped_count para evitar falsos "completado normalmente".

SID="${1:-A}"
PROJ="/mnt/d/PyCode/poder_judicial_results-PY-OK/DescargaPJ_optimizado/poder_judicial_results"
VENV="$HOME/venv_poder/bin/python"
MAX_RETRIES=100
RUN=0

mkdir -p "$PROJ/logs"

echo "[Watchdog v2] Spider $SID iniciado. Max reintentos: $MAX_RETRIES"
echo ""

while [ $RUN -lt $MAX_RETRIES ]; do
    RUN=$((RUN + 1))
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    LOG="$PROJ/logs/spider_${SID}_watchdog_${TIMESTAMP}.log"

    echo "[$(date '+%H:%M:%S')] Intento $RUN/$MAX_RETRIES → lanzando..."

    cd "$PROJ"
    $VENV run_${SID}_wsl.py > "$LOG" 2>&1
    EXIT_CODE=$?

    # Limpiar Chrome huérfano siempre entre reintentos
    pkill -f "pj_perfil_${SID}" 2>/dev/null || true

    # Detectar cualquier fallo de Chrome/WebDriver
    if grep -qE "(chrome_dead|radware_blocked|Connection refused|\
Remote end closed connection|Cannot connect|Max retries exceeded|\
Connection aborted|chrome not reachable|invalid session)" "$LOG"; then
        REASON=$(grep -oE "(chrome_dead|radware_blocked|Connection refused|\
Remote end closed connection|Max retries exceeded|Connection aborted)" \
        "$LOG" | tail -1)
        echo "[$(date '+%H:%M:%S')] Fallo: $REASON (intento $RUN). Relanzando en 5s..."
        sleep 5
        continue
    fi

    # Verificar si se procesaron items realmente
    ITEMS=$(grep "item_scraped_count" "$LOG" 2>/dev/null | grep -oP '\d+' | tail -1)
    if [ -n "$ITEMS" ] && [ "$ITEMS" -gt 0 ] && [ "$EXIT_CODE" -ne 0 ]; then
        echo "[$(date '+%H:%M:%S')] Procesó $ITEMS items pero exit=$EXIT_CODE. Relanzando..."
        sleep 3
        continue
    fi

    # Verificar si el batch se completó (no más items pendientes)
    if grep -q "0 pendientes" "$LOG" 2>/dev/null; then
        echo "[$(date '+%H:%M:%S')] Spider $SID completó su batch (0 pendientes)"
        break
    fi

    # Salida normal
    echo "[$(date '+%H:%M:%S')] Spider $SID terminó (exit=$EXIT_CODE, items=${ITEMS:-0})"
    break
done

echo ""
echo "[Watchdog v2] Spider $SID finalizado tras $RUN intentos."
ITEMS=$(grep "item_scraped_count" "$LOG" 2>/dev/null | grep -oP '\d+' | tail -1)
echo "  Ultimos items scraped: ${ITEMS:-?}"
