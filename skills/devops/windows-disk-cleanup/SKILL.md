---
name: windows-disk-cleanup
description: Use when a Windows drive (D:, C:) is nearly full.
version: "1.0"
author: Hermes curator
metadata:
  hermes:
    tags: [wsl, windows, disk, cleanup, powershell, ntfs]
    category: devops
    related_skills: [hermes-maintenance-wsl]
---

# Windows Disk Cleanup from WSL

Analyze a Windows NTFS drive (`/mnt/d`, `/mnt/c`) for space usage and produce prioritized cleanup options. Proven on a 504 GB drive at 93% usage.

## When to Use

- User reports a Windows drive is "casi llena", "con alertas", or asks to limpiar/aligerar/optimizar a drive
- Need to find what's consuming space on `/mnt/*` before recommending deletions or migrations

## CRITICAL: Scan with PowerShell, NEVER `du` over /mnt

`du` on an NTFS mount through WSL's 9p protocol is pathologically slow: a `du -h --max-depth=1 /mnt/d` on 466 GB did NOT finish in 300+ s, and even per-directory `du -sh` on 4 folders timed out at 300 s. The same scan via native PowerShell completed in **seconds**.

Always delegate size scans to Windows:

```bash
# Top-level dirs by size (D:)
powershell.exe -NoProfile -Command "Get-ChildItem -Path 'D:\' -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object { try { \$size = (Get-ChildItem -Path \$_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; [PSCustomObject]@{Dir=\$_.Name; GB=[math]::Round(\$size/1GB,2)} } catch { [PSCustomObject]@{Dir=\$_.Name; GB='ERR'} } } | Sort-Object GB -Descending | Format-Table -AutoSize" 2>/dev/null
```

Drill-down variants (same skeleton, change the path):
- Subdirs of one big folder: `-Path 'D:\PyCode' -Directory`
- Files > 500 MB anywhere: recurse `-File` and `Where-Object { \$_.Length -gt 500MB }`, output `FullName, @{N='GB';E={[math]::Round(\$_.Length/1GB,2)}}`
- Group by year (finds "old data to archive"): `Group-Object { \$_.LastWriteTime.Year }` then `Select Name, Count, @{N='GB';E={...Sum)/1GB,2}}`
- venv/node_modules weight: `Where-Object { \$_.Name -match '^(venv|\.venv|node_modules|__pycache__|\.git)$' }` and sum each
- Recycle bin + temps, always cheap: `du -sh /mnt/d/'$RECYCLE.BIN'`, `/mnt/c/Users/<user>/AppData/Local/Temp`, `/mnt/c/Windows/Temp`

A ready-to-run wrapper is in `scripts/scan_drive.sh`.

## UTF-16 gotcha

`wsl.exe` and some PowerShell output piped through `powershell.exe` comes back UTF-16 with null bytes (`\u0000` garbage). Fix with `tr -d '\0'` or append `| Out-String` inside the PS command.

## Docker on D: — disambiguate DOCKER DATA vs the UBUNTU DISTRO (critical)

A folder named `D:\Docker` (or `D:\DockerDesktop`) often contains TWO different vhdx files with very different consequences:

- **The Ubuntu WSL distro itself may live there**: `D:\Docker\ext4.vhdx` (e.g. 90.5 GB) with `BasePath = D:\Docker\` in the registry. This is the disk Hermes runs on — compacting it requires `wsl --shutdown`, which KILLS the current session.
- **Docker Desktop data**: `D:\Docker\Data\DockerDesktopWSL\disk\docker_data.vhdx` (images, volumes, build cache) plus a small `main\ext4.vhdx`.

**Always resolve distro locations BEFORE reporting sizes** — never assume `D:\Docker\*.vhdx` is Docker data:

```bash
# Where does each WSL distro actually live? (registry)
powershell.exe -NoProfile -Command "Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object { \$p = Get-ItemProperty \$_.PSPath; [PSCustomObject]@{Distro=\$p.DistributionName; BasePath=\$p.BasePath} } | Format-Table -AutoSize" 2>/dev/null
```

In this user's setup the result was: `Ubuntu -> D:\Docker\` (90.5 GB vhdx!) and `docker-desktop -> D:\Docker\Data\DockerDesktopWSL\main`. So "Docker 173 GB" was really ~90 GB of Ubuntu WSL + ~83 GB of Docker data — and the vhdx compaction headroom (90.5 GB file vs 65 GB `df /`) is Ubuntu's, not Docker's.

Also check `cat /mnt/c/Users/<user>/.wslconfig` (memory/swap limits) and `df -h /` for the vhdx's internal usage vs the physical file size — that gap is the compaction headroom.

### Compaction — which one needs Hermes to be closed?

- `docker_data.vhdx` (Docker Desktop data): prune with Docker Desktop RUNNING (`docker system prune -a`), quit Docker Desktop, then compact. Only terminates the `docker-desktop` distro — **Ubuntu/Hermes survives**. `docker` CLI may be absent from the current distro (integration off); use `docker.exe` from PowerShell or start Docker Desktop.
- Ubuntu's own `ext4.vhdx`: compaction REQUIRES `wsl --shutdown` → Hermes session dies. Sequence for the user: clean caches/data first (Fase 1-2, no shutdown), then do the vhdx compact as the LAST step when they close Hermes. Give them the exact command rather than running it mid-session.
- Moving data out of the vhdx (e.g. HF cache to C:) frees space INSIDE the disk but the physical vhdx file does NOT shrink — the real GB recovery on D: only lands after compaction. Tell the user this explicitly so they don't expect instant gains from a move alone.

## Prioritized-options framework (what the user expects)

Present options in 3 tiers, each with estimated GB recovery and risk:

- **A — Rápida y segura**: recycle bin, Windows temp, stale installers in Descargas, moving backups to a drive with free space (check `df -h /mnt/c` first — a second drive with headroom enables MIGRATION instead of deletion)
- **B — Medio, requiere confirmación**: archiving/compressing old PDF corpora, deleting venvs of inactive projects (regenerable via `pip install -r requirements.txt`). **Do NOT assume PDFs compress well or that they were already extracted to text — measure first** (see "PDF archives: verify extraction + test compression" below).
- **C — Estructural**: moving Docker Desktop data or inactive project dirs to another drive, Windows Disk Cleanup (`cleanmgr`)

Sanity-check the math: sum of scanned dirs + loose files should roughly equal used GB (`df -h`). If it doesn't, note what wasn't scanned — never claim exhaustive coverage.

## Report format

- Write full report to `~/informe_<tema>_<YYYYMMDD>.md` AND `.txt` copy (user prefers both, plain text no heavy markdown)
- State explicitly: what was reviewed, what was NOT inspected, and that **no destructive action was executed** — user approval is required before any deletion
- End with a recommendation (e.g. "run A1-A4 first, recovers X GB, drops usage to ~Y%")

## HuggingFace cache inside WSL (~/.cache/huggingface) — a real cleanup target

When the WSL home dir is on a full drive, `~/.cache/huggingface/hub` can hold 8+ GB of models. Key facts from a live audit:

- Structure: `hub/models--ORG--NAME/{blobs,snapshots,refs}` — blobs are the real files, snapshots are pointers.
- **Obsolete revisions are invisible garbage**: a model can have TWO full-weight blobs (e.g. bge-m3: `pytorch_model.bin` 2.2G in revision `5617a9f` marked `.no_exist`, plus the active `model.safetensors` in `9a0624b`). Check `refs/refs/*` for the ACTIVE hash; blobs referenced only by `.no_exist` entries are deletable (~2.2 GB each).
- **Map models to projects before deleting**: grep the codebase for each model name (`bge-m3`, `faster-whisper`, `e5-large`, `ms-marco`, `all-MiniLM`, `distiluse`, `paraphrase-multilingual`) in `*.py`, `requirements*.txt`, `config.py` — NOT in docs/skills folders which produce false hits. In this user's stack: `distiluse-base-multilingual-cased-v2` is used by LexRAG-Optimizado/api-algoritmoConcurrencia/TC_SearchRAG (KEEP), `faster-whisper` small+tiny is **Hermes' own local STT** (never delete if voice used), `multilingual-e5-large` had ZERO hits (safe delete).
- **Move-to-C: pattern**: relocate the whole `~/.cache/huggingface` to `C:\BackupsWSL\hf-cache` and symlink `~/.cache/huggingface -> /mnt/c/BackupsWSL/hf-cache` so projects + Hermes STT keep finding models without re-downloading 8 GB. (Note: the user's canonical backup folder for this machine is `C:\BackupsWSL` — created 2026-08-02 — not `C:\Backups`.) Caveat: frees space INSIDE the vhdx only; physical D: space returns after vhdx compaction (see Docker section).
- Project→model mapping detail for this machine is in `references/hf-cache-audit-2026-08.md`.

## Execution phase — user's required discipline

Once options are approved, do NOT jump straight into destructive ops. This user explicitly demands:

1. **Numbered action list BEFORE executing** — "haz una lista de lo que harás antes de proceder". Present the exact numbered steps (what gets deleted, what gets moved where, sizes) and get the OK before running anything.
2. **Prefer MOVE over DELETE** — the user asked for a backup folder `C:\BackupsWSL` (create it with `mkdir -p /mnt/c/BackupsWSL`) and to move files there instead of deleting. Only delete what was explicitly confirmed unused (e.g. verified-no-reference HF models). When moving, also drop a `NOTA_<tema>_<YYYYMMDD>.md` note in the backup folder recording what was deleted/moved and why — the user asked for this ("crea una nota o similar").
3. **Verify each op after running it** — destination size matches source, origin folder gone, `df -h` before/after deltas reported. Never claim a move/delete succeeded on trust.

## PDF archives: verify extraction + test compression BEFORE recommending 7z

A large PDF corpus (e.g. 558K legal PDFs, 70 GB) looks like an obvious 7z target — but measure before promising GB:

- **Check whether the "extracted" sibling set actually corresponds.** In ResolucionesSAL (2026-08), `Words/` had 109K .doc files next to 558K PDFs, which looked like the text extraction. Exact-filename matching showed only **417** of 558K PDFs have a corresponding .doc — the .doc set covers just 24% of expedientes (105K of 443K) and is NOT the extraction of the PDFs. So deleting PDFs "because we have the text" would have destroyed data.
- **Test the real compression ratio on a sample before proposing 7z.** Judicial PDFs are already internally compressed (vector text), so 7z gives only ~19%: a 100-file / 1.27 GB sample → 1.03 GB at `-mx=5`, ~2 min CPU. Extrapolated: 70 GB would yield ~13 GB after ~2 h of CPU — not worth it, and the PDFs become inaccessible without decompression. When compression is that poor, **MOVE the old-year files to another drive instead** (e.g. `C:\BackupsWSL` via robocopy /MOVE) — full GB recovery, zero data loss, no CPU burn.
- Sample recipe: `powershell.exe -NoProfile -Command "Get-ChildItem 'D:\X' -File | Sort-Object Length -Descending | Select-Object -First 100 | Copy-Item -Destination 'C:\tmp\sample\' -Force"` then `7z a -t7z -mx=5 <out> .` and compare sizes. Note the C:\tmp vs /tmp-of-WSL path trap — pass an explicit Windows destination to PowerShell and check it there.

## Safe moves — robocopy /MOVE

For moving large files/folders D:→C: (or anywhere), use native robocopy, NOT `mv` over /mnt (9p slow for big trees):

```powershell
# Single file: robocopy <src_dir> <dst_dir> <file> /MOV
powershell.exe -NoProfile -Command "robocopy 'D:\' 'C:\BackupsWSL' 'hermes.bak.20260730_134255.7z' /MOV /NP /NJH /R:2 /W:2"
# Folder tree: robocopy <src> <dst> /E /MOVE /NP /NJH /R:2 /W:2 /NFL /NDL
```

robocopy /MOVE copies fully, then deletes the origin only after the copy succeeded — verification-friendly. After each move, confirm: `Get-ChildItem <dst> -Recurse -File | Measure-Object Length -Sum` (matches source GB) AND `Test-Path <src>` is false. Loop multiple moves in one PowerShell block with per-item OK/MOVED/SKIP output.

## Recycle bin + Windows Temp vacuum

- **Recycle bin**: `Clear-RecycleBin -DriveLetter D -Force` (and `-DriveLetter C`). Do NOT use the COM `Shell.Application` namespace(0xA) approach — on a large recycle bin (tens of thousands of items) it enumerates everything and times out at 300 s without completing. The native cmdlet is instant. Verify with `du -sh /mnt/d/'$RECYCLE.BIN'` → 0.
- **Windows Temp**: PowerShell `Remove-Item -Recurse` on `C:\Users\<user>\AppData\Local\Temp` is too slow (timed out). Use cmd natively — fast, skips in-use files silently:
  `cmd.exe /c "del /f /s /q C:\Users\<user>\AppData\Local\Temp\*.* >nul 2>&1 & for /d %i in (C:\Users\<user>\AppData\Local\Temp\*) do rd /s /q \"%i\" 2>nul"`
  Expect a residual (in-use files) — report before/after sizes, don't claim 0.

## Pitfalls

- Never run `du`/`find -size` on large `/mnt/*` trees — always PowerShell (see CRITICAL above)
- Never run recursive `grep -r` on large `/mnt/*` trees either — same 9p pathology: a `grep -rl --include=*.py --include=requirements.txt` over D:\PyCode timed out at 300 s AND at 600 s. Use `powershell.exe Select-String` with `-notmatch 'node_modules|venv|\.venv|\.git|__pycache__'`, or scope the grep to a short list of candidate project dirs (top-level names you already know are big) and exclude venv/node_modules.
- Don't kill a background `du` mid-scan silently — it leaves a confusing zombie; switch to PowerShell instead
- Never trust "we already extracted those PDFs to text" as license to delete originals — do an exact-filename intersection between the source files and the supposed extraction (ResolucionesSAL's 109K .doc files matched only 417 of 558K PDFs; the Words set was a partial sibling set, not the extraction). Verify before you recommend, and prefer MOVE over DELETE for corpora
- `df -h /mnt/d` shows the drive; verify free space on ALL drives before recommending migrations (C: often has headroom when D: is full)
- Windows username in paths: `/mnt/c/Users/<windowsuser>/` may differ from WSL username

## References

- `scripts/scan_drive.sh` — parameterized top-level scan wrapper (usage: `scan_drive.sh D`)
- `references/hf-cache-audit-2026-08.md` — model→project mapping for this machine's ~/.cache/huggingface (which models are safe to delete/move, bge-m3 dual-revision detail)
- `references/resoluciones-sal-2026-08.md` — ResolucionesSAL corpus audit: 558K PDFs vs 109K .doc mismatch (only 417 exact matches), measured 19% 7z ratio, expediente coverage stats
