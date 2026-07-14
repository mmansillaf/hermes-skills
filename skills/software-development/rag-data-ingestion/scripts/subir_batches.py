#!/usr/bin/env python3
"""
Upload multiple JSONL batch files to Groq Batch API and create batches.

Usage:
    GROQ_API_KEY=gsk_... python3 scripts/subir_batches.py file1.jsonl file2.jsonl ...

    # Or with .env file in project root:
    python3 scripts/subir_batches.py \
        batch_jsonl/lote_1a.jsonl batch_jsonl/lote_1b.jsonl \
        --labels "Lote 1a (LAB 12K)" "Lote 1b (LAB 12K)"

Output:
    Prints each label + batch ID. Saves all batch IDs to /tmp/groq_batches_<timestamp>.txt
    for downstream monitoring.

PITFALL: Use this script instead of shell curl -F. Python requests handles multipart
file uploads reliably, while curl -F has quoting issues with @file paths in shell scripts.
"""
import requests, json, os, sys, argparse
from datetime import datetime

API_KEY = os.environ.get("GROQ_API_KEY", "")
BASE = "https://api.groq.com/openai/v1"


def upload_and_create_batch(filepath, label=""):
    """Upload a JSONL file and create a Groq batch. Returns batch_id."""
    if not API_KEY:
        print("ERROR: Set GROQ_API_KEY environment variable")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {API_KEY}"}
    label_display = label or os.path.basename(filepath)
    fsize = os.path.getsize(filepath) / 1024**2

    print(f"[{label_display}] Uploading ({fsize:.0f} MB)...")

    # 1. Upload file
    with open(filepath, "rb") as f:
        resp = requests.post(
            f"{BASE}/files",
            headers=headers,
            files={"file": (os.path.basename(filepath), f, "application/jsonl")},
            data={"purpose": "batch"},
            timeout=300
        )

    if resp.status_code != 200:
        print(f"  ERROR uploading: {resp.status_code} {resp.text[:300]}")
        return None

    file_id = resp.json()["id"]
    print(f"  File ID: {file_id}")

    # 2. Create batch
    resp2 = requests.post(
        f"{BASE}/batches",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "input_file_id": file_id,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h"
        },
        timeout=30
    )

    if resp2.status_code != 200:
        print(f"  ERROR creating batch: {resp2.status_code} {resp2.text[:300]}")
        return None

    batch_id = resp2.json()["id"]
    print(f"  Batch ID: {batch_id}")
    return batch_id


def main():
    parser = argparse.ArgumentParser(
        description="Upload JSONL files to Groq Batch API"
    )
    parser.add_argument("files", nargs="+", help="JSONL file(s) to upload")
    parser.add_argument(
        "--labels", nargs="*", default=None,
        help="Labels for each file (same order as files). Defaults to filename."
    )
    args = parser.parse_args()

    if not args.labels:
        args.labels = [os.path.basename(f) for f in args.files]
    elif len(args.labels) != len(args.files):
        print("ERROR: --labels count must match files count")
        sys.exit(1)

    batch_ids = []
    for filepath, label in zip(args.files, args.labels):
        bid = upload_and_create_batch(filepath, label)
        if bid:
            batch_ids.append((label, bid))
        print()

    # Save batch IDs for downstream monitoring
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outpath = f"/tmp/groq_batches_{ts}.txt"
    with open(outpath, "w") as f:
        for label, bid in batch_ids:
            f.write(f"{label}\t{bid}\n")

    print("=" * 60)
    print(f"BATCHES ENVIADOS ({len(batch_ids)}):")
    for label, bid in batch_ids:
        print(f"  {label:30s} {bid}")
    print(f"\nIDs guardados en: {outpath}")
    print(f"\nMonitorear con:\n  cat {outpath}")


if __name__ == "__main__":
    main()
