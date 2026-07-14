#!/usr/bin/env python3
"""Monitor Groq batches for a year — status + auto-download completed ones.

Usage: modify YEAR and run from project root.
  cd PeruanoSearchEngine02 && python3 scripts/monitor_YYYY_groq.py

For cron: schedule every 30-60 min. Cancel cron when output shows ALL_DONE: true.
"""
import json, os, sys
from pathlib import Path
from dotenv import load_dotenv

YEAR = "2021"  # CHANGE THIS

PROJECT = Path(__file__).parent.parent
load_dotenv(PROJECT / ".env")

from groq import Groq

TRACKING = PROJECT / "data" / f"groq_batch_tracking_{YEAR}.json"
OUTPUT_DIR = PROJECT / "data" / f"json_extracted_{YEAR}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(TRACKING) as f:
    tracking = json.load(f)

client = Groq(
    api_key=os.getenv("GROQ_API_KEY") or os.getenv("GROQ"),
    timeout=30,
    max_retries=2,
)

statuses = {}
downloaded = 0
errors_detail = []

for filename, data in sorted(tracking.items()):
    bid = data["batch_id"]
    try:
        job = client.batches.retrieve(bid)
        new_status = job.status
        data["status"] = new_status
        statuses[new_status] = statuses.get(new_status, 0) + 1

        if new_status == "completed" and not data.get("downloaded"):
            output_file_id = job.output_file_id
            if output_file_id:
                response = client.files.content(output_file_id)
                content = response.read().decode("utf-8")
                out_path = OUTPUT_DIR / filename
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)
                lines = [l for l in content.strip().split("\n") if l.strip()]
                data["downloaded"] = True
                data["lines"] = len(lines)
                downloaded += 1
                print(f"  OK descargado: {filename} ({len(lines)} lineas)")
    except Exception as e:
        statuses["error"] = statuses.get("error", 0) + 1
        errors_detail.append(f"{filename}: {e}")

# Save tracking
with open(TRACKING, "w") as f:
    json.dump(tracking, f, indent=2, ensure_ascii=False)

total = len(tracking)
done = statuses.get("completed", 0)

print()
print(f"{YEAR} Groq: {done}/{total} completed | {downloaded} descargados esta ronda")
print(f"  Estados: {statuses}")
if errors_detail:
    print(f"  Errores (primeros 5): {errors_detail[:5]}")

all_done = done == total
if all_done:
    all_dl = all(d.get("downloaded", False) for d in tracking.values())
    if all_dl:
        print("ALL_DONE: true")
        print(f"Pipeline {YEAR} finalizado.")
    else:
        not_dl = [
            k for k, v in tracking.items()
            if v.get("status") == "completed" and not v.get("downloaded")
        ]
        print(f"Completados sin descargar: {not_dl}")
        print("ALL_DONE: false")
else:
    print("ALL_DONE: false")
