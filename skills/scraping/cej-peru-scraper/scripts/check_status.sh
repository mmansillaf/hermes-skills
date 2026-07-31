#!/bin/bash
# check_status.sh — Lightweight progress monitor for CEJ spiders
# Usage: bash check_status.sh
# Reads checkpoint files, counts PDFs on disk, checks ps for live processes.
# Simpler than stats.py (25 lines bash vs 155 lines Python).

PROJ="/mnt/d/PyCode/poder_judicial_results-PY-OK/DescargaPJ_optimizado/poder_judicial_results"

CKP_A=$(cat "$PROJ/checkpoint_opt_A.json" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
CKP_B=$(cat "$PROJ/checkpoint_opt_B.json" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")

PDF_COUNT=$(find "$PROJ/documents" -name "*.pdf" 2>/dev/null | wc -l)
EXP_COUNT=$(ls -d "$PROJ/documents"/*/ 2>/dev/null | wc -l)

PID_A=$(ps aux | grep "run_A_wsl.py" | grep -v grep | awk '{print $2}')
PID_B=$(ps aux | grep "run_B_wsl.py" | grep -v grep | awk '{print $2}')
STATUS_A="VIVO (PID $PID_A)"
STATUS_B="VIVO (PID $PID_B)"
[ -z "$PID_A" ] && STATUS_A="DETENIDO"
[ -z "$PID_B" ] && STATUS_B="DETENIDO"

DOCS_SIZE=$(du -sh "$PROJ/documents" 2>/dev/null | cut -f1)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "═══════════════════════════════════════════"
echo "  CEJ SCRAPER - MONITOR $TIMESTAMP"
echo "═══════════════════════════════════════════"
echo ""
echo "  Spider A: $STATUS_A"
echo "    Procesados: $CKP_A registros"
echo ""
echo "  Spider B: $STATUS_B"
echo "    Procesados: $CKP_B registros"
echo ""
echo "  Total procesados: ~$((CKP_A + CKP_B))"
echo "  Expedientes con PDF: $EXP_COUNT"
echo "  PDFs descargados: $PDF_COUNT"
echo "  Tamaño en disco: $DOCS_SIZE"
echo "═══════════════════════════════════════════"
