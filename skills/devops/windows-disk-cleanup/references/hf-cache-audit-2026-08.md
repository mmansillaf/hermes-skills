# HF Cache Audit — Christian's WSL (2026-08-02)

Snapshot of `~/.cache/huggingface/hub` on the WSL whose Ubuntu distro lives at
`D:\Docker\ext4.vhdx`. Total: 8.1 GB. Useful as a reference mapping for future
cleanup decisions on this machine (sizes change; the model→project mapping is stable).

## Inventory (8.1 GB total)

| Model | Size | Status | Used by |
|---|---|---|---|
| BAAI/bge-m3 | 4.3 GB | ⚠️ 2 revisions, 1 obsolete | api-algoritmoConcurrencia main.py (search_vector_pg/hybrid) — server .152 has its own cache; local only for FAISS builds |
| intfloat/multilingual-e5-large | 2.2 GB | ❌ no code hits | nothing found (benchmarks/tests only) |
| sentence-transformers/distiluse-base-multilingual-cased-v2 | 519 MB | ✅ KEEP | LexRAG-Optimizado core/embedding.py, api-algoritmoConcurrencia config.py, TC_SearchRAG index_tc.py |
| Systran/faster-whisper-small | 464 MB | ✅ KEEP | **Hermes local STT** (Documentos/rev040526.txt: "Default STT provider is local (faster-whisper)") |
| sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | 458 MB | ✅ KEEP | SDD_LightRAG light_rag/embedder.py |
| Systran/faster-whisper-tiny | 75 MB | ✅ KEEP | Hermes local STT |
| cross-encoder/ms-marco-MiniLM-L-6-v2 | 88 MB | ⚠️ | api-algoritmoConcurrencia config.py (runs on server .152) |
| sentence-transformers/all-MiniLM-L6-v2 | 88 MB | ✅ | generic default |

## bge-m3 dual-revision detail

- Active revision (from `refs/refs/pr/*`): `9a0624b896d81da7492a910ffa53731274b6cf3d` → model.safetensors
- Obsolete: `5617a9f61b028005a4858fdac845db406aefb181` → pytorch_model.bin (2.2 GB), listed under `.no_exist/`
- Deleting the obsolete blob frees ~2.2 GB without breaking anything.

## Verified project→model grep paths

Where each model string was found (only code, venv/node_modules/docs excluded):

- LexRAG-Optimizado/core/embedding.py → distiluse (SentenceTransformer singleton)
- api-algoritmoConcurrencia/config.py → EMBEDDING_MODEL_NAME=distiluse, CROSS_ENCODER_MODEL_NAME=ms-marco
- api-algoritmoConcurrencia/main.py → "BAAI/bge-m3" literal in search_vector_pg/search_hybrid_pg calls
- TC_SearchRAG/src/index_tc.py → distiluse
- SDD_LightRAG/light_rag/embedder.py → MODELO_EMBEDDING=paraphrase-multilingual-MiniLM-L12-v2
- LexRAG-Optimizado embedding.py: grep "bge-m3|bge_m3|BAAI" gave a false hit earlier (BAAI matched a doc string); direct read of the file shows distiluse — always confirm with a file read, not just grep.

## Recommended cleanup options (as presented to user)

1. Minimal: delete e5-large (2.2G) + obsolete bge-m3 blob (2.2G) = 4.4 GB
2. Move all to C:\Backups\hf-cache + symlink = 8.1 GB freed inside vhdx, all models still resolvable
3. Hybrid (recommended): delete e5-large + obsolete blob, move active models (~3.7 GB) with symlink

All three free space inside the vhdx only — physical D: recovery requires compacting
D:\Docker\ext4.vhdx afterwards (needs wsl --shutdown, kills Hermes).

## Executed outcome (2026-08-02, Option 1 + moves)

User approved: delete only the confirmed-unused models, MOVE everything else to a
new backup folder instead of deleting, and leave active models untouched.

- Deleted from `~/.cache/huggingface/hub`: `models--intfloat--multilingual-e5-large`
  (2.2 GB, zero code hits) and bge-m3 obsolete revision — snapshot `5617a9f…` +
  its exclusive blob `b5e0ce…` (2.2 GB). **Blob exclusivity check first**:
  `find -L ~/.cache/huggingface/hub -samefile <blob>` must list ONLY the obsolete
  snapshot; the active `9a0624b…/model.safetensors` blob `993b224…` was verified
  untouched. Cache went 8.1 GB → 3.8 GB.
- **Backup folder created**: `C:\BackupsWSL` (`/mnt/c/BackupsWSL`) — user's
  canonical name for this (not C:\Backups). Contents after session:
  `NOTA_MODELOS_BORRADOS_20260802.md`, `hermes.bak.20260730_134255.7z` (5.8 GB),
  `Adobe Acrobat Pro DC 2023 v23…+ Fix` (2.2 GB), `Adobe Acrobat Pro DC v2022…`
  (754 MB), `HermesBK` (1.9 GB), `QTorrent` (404 MB), `CBInsight` (246 MB).
- Moves via `robocopy … /MOV` (single file) and `/E /MOVE` (folder trees), each
  verified: destination size == source, then `Test-Path` origin = false.
- Recycle bins C: (1.2 GB!) and D: (142 MB) → 0 via `Clear-RecycleBin -Force`.
  COM Shell.Application enumeration timed out — native cmdlet is the fix.
- Windows Temp 257 MB → 111 MB via `cmd.exe del /f /s /q` (residual = in-use).
- Disk D: 466 GB used (93%) → 455 GB used (91%) +10 GB physical; +4.4 GB more
  lands only after compacting `D:\Docker\ext4.vhdx` (pending — requires
  closing Hermes: `wsl --shutdown` then `Optimize-VHD -Path 'D:\Docker\ext4.vhdx' -Mode Full`).
- Report written to `~/informe_limpieza_D_20260802.md` (+ .txt copy).

