#!/usr/bin/env python3
"""Download completed Groq batch results and extract JSON.
Idempotent: skips files that already exist with content >100 bytes.
See skill 'elperuano-ingestion-pipeline' for full workflow.
"""
import os, json, time, requests
from pathlib import Path
from dotenv import load_dotenv; load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY", "")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
TRACKING = Path("data/groq_batch_tracking_all.json")

data = json.loads(TRACKING.read_text())
total = 0

for key, entry in data.items():
    if entry.get("status") != "completed":
        continue
    year = key.split("/")[0]
    batch_name = Path(key).stem
    out_dir = Path("data") / f"json_extracted_{year}"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"results_{batch_name}.jsonl"
    if out_file.exists() and out_file.stat().st_size > 100:
        total += 1; continue
    batch_id = entry.get("batch_id", "")
    if not batch_id: continue
    try:
        r = requests.get(f"https://api.groq.com/openai/v1/batches/{batch_id}", headers=HEADERS, timeout=30)
        if r.status_code != 200: continue
        info = r.json()
        output_file_id = info.get("output_file_id", "")
        if not output_file_id: continue
        r2 = requests.get(f"https://api.groq.com/openai/v1/files/{output_file_id}/content", headers=HEADERS, timeout=120)
        if r2.status_code == 200:
            out_file.write_text(r2.text)
            total += 1
            print(f"  ✅ {key}: {len(r2.text.strip().split(chr(10)))} lines")
    except Exception as e:
        print(f"  ❌ {key}: {e}")
    time.sleep(0.1)

print(f"\n✅ Downloaded: {total} files")
