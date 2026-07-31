# Checkpoint Audit — Detecting Silent Reprocess

## Problem

The spider checkpoint (`checkpoint_opt_A.json` / `checkpoint_opt_B.json`) stores ALL
remaining expedientes. When the spider runs, it loads the full list, processes a few,
but does NOT write back a reduced list. Every subsequent run **re-queries CEJ for
already-downloaded expedientes**, wasting captcha solves and API costs.

## Symptoms from Production (05/06/2026)

| Metric | Spider A | Spider B |
|--------|----------|----------|
| Checkpoint size | 243 (never changes) | 244 (never changes) |
| PDFs on disk | 167 already have PDFs | 139 already have PDFs |
| Fresh data last run | 5 expedientes | 3 expedientes |
| Captcha fails last run | 8 | 7 |
| Total PDFs accumulated | 826 across 334 folders | (shared) |

167 of 243 checkpoint-A expedientes already had PDFs — meaning **69% of captcha
solves are wasted** re-querying already-downloaded expedientes.

## Quick Diagnostic Script

Run this from the spider's working directory to detect the bug:

```bash
python3 -c "
import json, os

for sp in ['A', 'B']:
    cp = f'checkpoint_opt_{sp}.json'
    if not os.path.exists(cp):
        continue
    with open(cp) as f:
        queue = json.load(f)
    
    docs_dir = 'documents'
    folders = set(os.listdir(docs_dir)) if os.path.isdir(docs_dir) else set()
    
    pending = len(queue)
    already_have = sum(1 for item in queue if item.split('|')[0] in folders)
    fresh = pending - already_have
    
    print(f'Spider {sp}: {pending} in checkpoint, {already_have} already have PDFs ({already_have/pending*100:.0f}% wasted), {fresh} truly new')
    
    if already_have > 0.5 * pending:
        print(f'  ⚠️  >50% of checkpoint is redundant — fix checkpoint depopulation')
"
```

## Fix

See "Checkpoint Management" section in the main SKILL.md.

## What to Check After Fix

After adding checkpoint-as-queue logic, verify:

1. Checkpoint file shrinks after each run
2. Same expediente is never re-queried
3. `captcha_fail` line count drops (fewer wasted solves on already-downloaded items)
4. Effective data rate (new PDFs/hour) matches the expected rate, not inflated by re-queries
