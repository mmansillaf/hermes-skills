# ResolucionesSAL Corpus Audit (2026-08-02)

Snapshot of `D:\ResolucionesSAL` — a legal-PDF corpus that looked like a prime
7z-compression target during the D: drive cleanup (466 GB used / 93%). The
measurements below are what a future session should reproduce (sizes change;
the *method* and *conclusions* are the durable part).

## Inventory

| Item | Files | Size |
|---|---|---|
| `PDFs/` | 558,329 | 70.16 GB |
| `Words/` (.doc) | 109,257 | 13.02 GB |

PDF size stats: min 0 KB, avg 132 KB, max 53.8 MB.
Expediente prefixes (name up to " document_N"): 443,270 unique in PDFs,
105,781 unique in Words → Words covers only ~24% of expedientes.

## Critical finding: Words are NOT the PDF extraction

- Exact-filename match (strip `.pdf` / `.doc`, compare sets): only **417** of
  558,329 PDFs have a corresponding .doc. The .doc files are a *partial
  sibling set* (e.g. expediente has document_2.pdf but only document_1.doc +
  document_4.doc), not the extracted text of the PDFs.
- Consequence: "we already extracted these PDFs to text, safe to delete" was
  FALSE for this corpus. Deleting PDFs on that assumption would destroy data.
- Lesson generalizes: before treating a companion format (doc/txt/json) as
  proof the originals are redundant, do an exact-name intersection, not a
  eyeball of the directory listing.

## Measured 7z compression ratio (the myth-buster)

Sample: 100 largest-ish PDFs (1.27 GB), compressed with `7z a -t7z -mx=5`:

- Result: 1,273.7 MB → 1,029 MB = **~19% savings**, ~2 min CPU for 1.27 GB.
- Extrapolation: 70 GB corpus → ~13 GB saved after ~2 h CPU, and PDFs become
  inaccessible until decompressed. Not worth it.
- Why: judicial PDFs are already internally compressed (vector text, embedded
  fonts). High-ratio 7z wins come from *scanned/bitmap* PDFs or mixed
  office files, NOT vector-text PDFs.

## Decision for this corpus

MOVE beats COMPRESS: robocopy `/E /MOVE` the old-year PDFs (2023 = 428K files,
51.7 GB) to `C:\BackupsWSL` (C: had 160 GB free). Full GB recovery on D:,
zero data loss, no CPU burn, files stay directly accessible. Present as tier-B
option B1a; user must confirm which option before executing.

## Method notes

- `Get-ChildItem ... -File | Measure-Object Length -Minimum -Maximum -Average -Sum`
  gives the stats fast in native PowerShell (never `du`/`ls` over /mnt — 9p slow).
- Filename-set intersection in PowerShell: build a `HashSet[string]` from one
  side, loop the other; O(n) instead of the naive per-file `Test-Path`.
- Sample copy path trap: PowerShell `Copy-Item ... -Destination 'C:\tmp\sample'`
  lands on the WINDOWS side — check `/mnt/c/tmp/sample`, not WSL `/tmp/sample`.
  A silent-empty destination usually means the path confusion, not a copy failure.
