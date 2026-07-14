#!/usr/bin/env python3
"""
Consolidate JSON lote files from battery testing into a single readable TXT.

Usage:
    python3 scripts/consolidate_battery_reports.py [--reports-dir PATH]

Looks for files matching bateria_100q_lote[1-4].json in the reports directory,
merges them (handling the lote2 dict/list format AND field name inconsistency),
and writes bateria_100q_completa_YYYYMMDD.txt.

Handles two JSON schemas:
  - Schema A (lotes 1, 3, 4): fields q, conf, ms, quality, web, cached, answer
  - Schema B (lote 2):         fields question, confidence, timing_ms, status
                               (no web/cached — defaults to False)
"""

import json
import os
import re
import sys
from datetime import date


def find_lote_files(reports_dir: str) -> list[str]:
    """Find all bateria_100q_lote*.json files, sorted by lote number."""
    pattern = re.compile(r"bateria_100q_lote(\d+)\.json$")
    files = []
    for f in os.listdir(reports_dir):
        m = pattern.match(f)
        if m:
            files.append((int(m.group(1)), os.path.join(reports_dir, f)))
    files.sort()
    return [p for _, p in files]


def normalize_item(item: dict) -> dict:
    """
    Normalize a single question item to a canonical schema.

    Handles both formats:
      Schema A (lotes 1,3,4): q, conf, ms, quality, web, cached
      Schema B (lote 2):       question, confidence, timing_ms, status
    """
    return {
        "idx": item.get("idx", 0),
        "nivel": item.get("nivel") or item.get("level", "?"),
        # Question: Schema A uses 'q', Schema B uses 'question'
        "q": item.get("q") or item.get("question", "?"),
        "quality": _get_quality(item),
        "conf": item.get("conf") or item.get("confidence", 0),
        "ms": item.get("ms") or item.get("timing_ms", 0),
        "web": item.get("web", False),
        "cached": item.get("cached", False),
        "answer": item.get("answer", ""),
        "answer_len": len(item.get("answer", "")),
    }


def _get_quality(item: dict) -> str:
    """Determine quality, handling both 'quality' and 'status' fields."""
    qual = item.get("quality")
    if qual and qual in ("OK", "WARN", "ERROR", "TIMEOUT"):
        return qual
    status = item.get("status", "")
    if status == "ok":
        return "OK"
    if status:
        return "WARN"
    return "OK"


def load_all_questions(reports_dir: str) -> list[dict]:
    """Load and merge all JSON lote files, normalizing schemas."""
    all_qas = []
    lote_files = find_lote_files(reports_dir)

    if not lote_files:
        print(f"ERROR: No se encontraron archivos bateria_100q_lote*.json en {reports_dir}")
        sys.exit(1)

    for path in lote_files:
        with open(path) as f:
            data = json.load(f)
        # Pitfall: lote2 is dict with 'results' key; others are flat lists
        if isinstance(data, dict):
            items = data.get("results", [])
        else:
            items = data
        for item in items:
            all_qas.append(normalize_item(item))

    return all_qas


def write_report(all_qas: list[dict], outpath: str):
    """Write formatted TXT report with ALL Q&As — no truncation."""
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("BATERIA DE PREGUNTAS — Reporte Consolidado")
    lines.append(f"Total: {len(all_qas)} preguntas")
    lines.append(f"Generado: {date.today().isoformat()}")
    lines.append("=" * 80)
    lines.append("")

    # Summary stats
    ok_count = sum(1 for q in all_qas if q.get("quality") == "OK")
    warn_count = sum(1 for q in all_qas if q.get("quality") == "WARN")
    err_count = sum(1 for q in all_qas if q.get("quality") in ("ERROR", "TIMEOUT"))
    conf_values = [q.get("conf", 0) for q in all_qas if isinstance(q.get("conf"), (int, float))]
    avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0
    ms_values = [q.get("ms", 0) for q in all_qas if isinstance(q.get("ms"), (int, float))]
    avg_ms = sum(ms_values) / len(ms_values) if ms_values else 0
    web_count = sum(1 for q in all_qas if q.get("web"))
    cache_count = sum(1 for q in all_qas if q.get("cached"))

    lines.append(f"Resultado:   OK={ok_count}  WARN={warn_count}  ERROR={err_count}")
    lines.append(f"Confianza:   {avg_conf:.2f} promedio")
    lines.append(f"Tiempo:      {avg_ms:.0f}ms promedio")
    lines.append(f"Web:         {web_count}/{len(all_qas)} fallbacks")
    lines.append(f"Cache:       {cache_count}/{len(all_qas)} hits")
    lines.append("")

    # Per-question detail — NO truncation on answers
    for q in all_qas:
        lines.append("-" * 80)
        idx = q.get("idx", "??")
        nivel = (q.get("nivel", "?") or "?")[0]
        calidad = q.get("quality", "?")
        qconf = q.get("conf", 0)
        qms = q.get("ms", 0)
        web = "Y" if q.get("web") else "N"
        cache = "Y" if q.get("cached") else "N"
        lines.append(f"#{idx:>03d}  [{nivel}]  {calidad:4s}  "
                     f"conf={qconf:.2f}  {qms}ms  web={web}  cache={cache}")

        qtext = q.get("q", "?")
        lines.append(f"  Q: {qtext}")
        lines.append(f"  A: {q.get('answer', '')}")
        lines.append("")

    with open(outpath, "w") as f:
        f.write("\n".join(lines))

    print(f"Created: {outpath}")
    print(f"Size: {os.path.getsize(outpath)} bytes")
    print(f"Q&As: {len(all_qas)}")


if __name__ == "__main__":
    reports_dir = sys.argv[1] if len(sys.argv) > 1 else "reports"
    all_qas = load_all_questions(reports_dir)
    today = date.today().strftime("%Y%m%d")
    outpath = os.path.join(reports_dir, f"bateria_100q_completa_{today}.txt")
    write_report(all_qas, outpath)
