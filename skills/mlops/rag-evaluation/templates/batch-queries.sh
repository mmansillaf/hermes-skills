#!/bin/bash
# Template: batch RAG queries with timeout and file output.
# Replace VENV, SCRIPT, OUT, and PREGUNTAS array.
# Each query runs as: timeout N $VENV $SCRIPT --query "$Q" > "$OUT/$TS_$KEY.txt" 2>&1

set -e

VENV=/path/to/venv/bin/python
SCRIPT=/path/to/rag_script.py
OUT=/path/to/output_dir
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p "$OUT"

# Define queries: KEY is "ID_nivel", value is the question
declare -A PREGUNTAS
PREGUNTAS=(
  ["Q01_simple"]="First simple question?"
  ["Q02_medio"]="First medium question?"
  ["Q03_complejo"]="First complex question?"
)

TOTAL=${#PREGUNTAS[@]}
CURRENT=0
OK=0
FAIL=0
START_ALL=$(date +%s)

echo "Batch $TOTAL queries — $(date)"

for KEY in Q01_simple Q02_medio Q03_complejo; do
  CURRENT=$((CURRENT + 1))
  PREGUNTA="${PREGUNTAS[$KEY]}"
  OUTFILE="$OUT/${TS}_${KEY}.txt"
  
  echo "[$CURRENT/$TOTAL] $KEY — ${PREGUNTA:0:80}..."
  
  T0=$(date +%s)
  if timeout 300 $VENV "$SCRIPT" --query "$PREGUNTA" > "$OUTFILE" 2>&1; then
    T1=$(date +%s)
    CHARS=$(wc -c < "$OUTFILE")
    echo "  OK | $((T1-T0))s | ${CHARS}c | $OUTFILE"
    OK=$((OK + 1))
  else
    echo "  FAIL (rc=$?) | $(( $(date +%s) - T0 ))s"
    FAIL=$((FAIL + 1))
  fi
done

END_ALL=$(date +%s)
TOTAL_TIME=$((END_ALL - START_ALL))
echo "Done: $OK OK / $FAIL FAIL | ${TOTAL_TIME}s ($((TOTAL_TIME/60))min)"
