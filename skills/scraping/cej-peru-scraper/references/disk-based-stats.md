# Stats Script: Disk-Based Audit vs Checkpoint-Based Audit

## Problem

The original `stats.py` counts checkpoint entries to determine progress. But the checkpoint mixes:
- Expedientes with PDFs (successful downloads)
- Captcha failures (no PDF, but won't be retried)
- Expedientes "sin documentos" (no PDF because there's nothing to download)

This inflates the "processed" count and underestimates pending items by double-counting.

## Correct Approach: Audit `documents/` folder

The `documents/` directory contains one subfolder per expediente that was actually downloaded with PDF files inside. This is the ONLY reliable source of truth for "what's been done."

## Production-Ready Stats Script

This is the `stats.py` from the production project at `DescargaPJ_optimizado/poder_judicial_results/stats.py`:

```python
import json, os, openpyxl, subprocess
from collections import Counter

PROJ = os.path.dirname(os.path.abspath(__file__))

def load_slice(sid):
    """Carga slice A o B, devuelve lista de dicts."""
    path = os.path.join(PROJ, 'input', f'slice_LA_DC_{sid}.xlsx')
    wb = openpyxl.load_workbook(path)
    ws = wb.worksheets[0]
    headers = [c.value for c in ws[1]]
    rows = []
    for row in ws.iter_rows(values_only=True, min_row=2):
        d = dict(zip(headers, row))
        rows.append(d)
    wb.close()
    return rows

def load_ckp(sid):
    path = os.path.join(PROJ, f'checkpoint_opt_{sid}.json')
    try:
        with open(path) as f:
            items = json.load(f)
        exps = set(i.split('|')[0] for i in items)
        return items, exps
    except:
        return [], set()

# ── Expedientes con PDFs en disco ──
doc_dir = os.path.join(PROJ, 'documents')
downloaded_exps = set()
for d in os.listdir(doc_dir):
    dp = os.path.join(doc_dir, d)
    if os.path.isdir(dp):
        downloaded_exps.add(d)

total_pdfs = sum(
    len([f for f in os.listdir(os.path.join(doc_dir, d)) if f.endswith('.pdf')])
    for d in downloaded_exps if os.path.isdir(os.path.join(doc_dir, d))
)

def print_status(slice_rows, ckp_exps, sid_label):
    total = len(slice_rows)
    con_pdf = sum(1 for r in slice_rows
                  if str(r.get('N° EXPEDIENTE', '') or '').strip() in downloaded_exps)
    en_ckp = sum(1 for r in slice_rows
                 if str(r.get('N° EXPEDIENTE', '') or '').strip() in ckp_exps)
    
    # Por especialidad
    esp_total = Counter()
    esp_hecho = Counter()
    for r in slice_rows:
        exp = str(r.get('N° EXPEDIENTE', '') or '').strip()
        esp = r.get('ESPECIALIDAD', '')
        esp_total[esp] += 1
        if exp in downloaded_exps:
            esp_hecho[esp] += 1
    
    print(f'  {"Especialidad":>12}  {"Total":>7}  {"Hecho":>7}  {"%":>5}  {"Pend":>7}')
    print(f'  {"-"*42}')
    for esp in ['LA', 'DC']:
        t = esp_total.get(esp, 0)
        h = esp_hecho.get(esp, 0)
        pct = h / t * 100 if t else 0
        p = t - h
        print(f'  {esp:>12}  {t:>7}  {h:>7}  {pct:>4.1f}%  {p:>7}')
    t2 = sum(esp_total.values())
    h2 = sum(esp_hecho.values())
    pct2 = h2 / t2 * 100 if t2 else 0
    p2 = t2 - h2
    print(f'  {"-"*42}')
    print(f'  {"TOTAL":>12}  {t2:>7}  {h2:>7}  {pct2:>4.1f}%  {p2:>7}')
    print(f'\n  Checkpoint marca {en_ckp} registros como "procesados"')
    print(f'  Pero {total - con_pdf} no tienen PDF en disco')
    return p2

# ... main execution calls print_status() for each spider
```

## Key Differences from Checkpoint-Based Stats

| Aspect | Checkpoint-based | Disk-based |
|--------|-----------------|------------|
| Source of truth | JSON file with processed+failed items | `documents/` folder listing |
| Counts captcha fails | As "processed" | As "pending" (correct) |
| Counts "sin docs" | As "processed" | As "pending" |
| Misses orphan PDFs | Yes (not in checkpoint) | No (reads actual dirs) |
| Shows real progress | No (inflates) | Yes |

## Integration with Checkpoint Cleanup

Disk-based stats naturally expose checkpoint issues, and the recommended practice is to REGULARLY reconcile the checkpoints against the disk state:

```python
# Find checkpoint items that should be cleaned up (already have PDFs)
ckp_a_items, ckp_a_exps = load_ckp('A')
ckp_b_items, ckp_b_exps = load_ckp('B')
en_ckp_sin_pdf = (ckp_a_exps | ckp_b_exps) - downloaded_exps
con_pdf_sin_ckp = downloaded_exps - ckp_a_exps - ckp_b_exps
```

- `en_ckp_sin_pdf`: items in checkpoint but no PDF → captcha fails / sin docs (should stay, they're correctly processed)
- `con_pdf_sin_ckp`: PDFs exist but not in checkpoint → orphans to re-register

### Automated Checkpoint Reconciliation

Run this periodically (e.g., every Nth run) to keep checkpoints in sync with disk:

```python
def reconcile_checkpoint(sid, downloaded_exps):
    \"\"\"Keep checkpoint in sync with actual disk state.\"\"\"
    ckp_path = f'checkpoint_opt_{sid}.json'
    slice_path = f'input/slice_LA_DC_{sid}.xlsx'
    
    # Load current checkpoint
    with open(ckp_path) as f:
        items = json.load(f)
    
    items_set = set(items)
    slice_rows = load_slice(sid)
    
    # Add PDFs not yet in checkpoint
    added = 0
    for r in slice_rows:
        exp = str(r.get('N° EXPEDIENTE', '') or '').strip()
        parte = str(r.get('PARTE PROCESAL', '') or '').strip()
        key = f'{exp}|{parte}'
        if exp in downloaded_exps and key not in items_set:
            items_set.add(key)
            added += 1
    
    # Remove items in checkpoint that now have PDFs
    removed = 0
    clean_set = set()
    for item in items_set:
        exp = item.split('|')[0]
        if exp in downloaded_exps:
            clean_set.add(item)  # keep — already processed
        else:
            removed += 1  # actually still pending (should stay in checkpoint)
    
    # Write back
    with open(ckp_path, 'w') as f:
        json.dump(sorted(items_set), f, indent=2)
    
    return added, removed, len(items_set)
```

This ensures the spider never re-queries CEJ for expedientes already on disk, even if runs were interrupted or checkpoints got out of sync.
