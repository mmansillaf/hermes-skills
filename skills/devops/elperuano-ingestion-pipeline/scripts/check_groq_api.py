#!/usr/bin/env python3
"""Check real Groq batch statuses via API — bypass tracking file caching.
The tracking file (groq_batch_tracking_all.json) stores status at upload time
and goes stale. This script queries the Groq API directly for each batch_id.

Usage:
    python3 scripts/check_groq_api.py
"""
import os, json, sys, time, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY", "")
if not API_KEY:
    print("ERROR: GROQ_API_KEY not set")
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
TRACKING = Path(__file__).parent.parent / "data" / "groq_batch_tracking_all.json"

if not TRACKING.exists():
    print("No tracking file found at", TRACKING)
    sys.exit(1)

data = json.loads(TRACKING.read_text())

all_batches = []
for year, entries in data.items():
    for entry in entries:
        entry["_year"] = year
        all_batches.append(entry)

statuses = {}
for b in all_batches:
    job_id = b.get("groq_batch_id", "")
    if not job_id:
        continue
    try:
        r = requests.get(
            f"https://api.groq.com/openai/v1/batches/{job_id}",
            headers=HEADERS, timeout=15
        )
        if r.status_code == 200:
            info = r.json()
            st = info.get("status", "unknown")
            statuses[st] = statuses.get(st, 0) + 1
        else:
            statuses[f"http_{r.status_code}"] = statuses.get(f"http_{r.status_code}", 0) + 1
    except Exception:
        statuses["timeout"] = statuses.get("timeout", 0) + 1
    time.sleep(0.05)

print("=== GROQ BATCH STATUS (API directa) ===")
for st, count in sorted(statuses.items(), key=lambda x: -x[1]):
    print(f"  {st}: {count}")
print(f"  TOTAL: {sum(statuses.values())}")

print("\n=== PER YEAR ===")
for year in sorted(data.keys()):
    batches = data[year]
    year_stats = {}
    for b in batches:
        job_id = b.get("groq_batch_id", "")
        if not job_id:
            continue
        try:
            r = requests.get(
                f"https://api.groq.com/openai/v1/batches/{job_id}",
                headers=HEADERS, timeout=10
            )
            if r.status_code == 200:
                st = r.json().get("status", "?")
                year_stats[st] = year_stats.get(st, 0) + 1
        except:
            year_stats["error"] = year_stats.get("error", 0) + 1
        time.sleep(0.05)
    print(f"  {year}: {len(batches)} total -> {year_stats}")
