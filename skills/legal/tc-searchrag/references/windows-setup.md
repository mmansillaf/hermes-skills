# TC SearchRAG — Windows Setup Guide

## Problem: "No module named 'faiss'"

The user has two Python installations:
- WSL (`/usr/bin/python3`) — has faiss ✅
- Windows (`C:\Python314\python.exe`) — missing faiss ❌

**Fix:** Use WSL or create a Windows venv.

## Windows venv setup

```powershell
# Create venv with Windows Python
C:\Python314\python.exe -m venv D:\PyCode\TC_SearchRAG\.venv

# Install deps
D:\PyCode\TC_SearchRAG\.venv\Scripts\pip install -r D:\PyCode\TC_SearchRAG\requirements.txt
```

Requirements.txt:
```
faiss-cpu>=1.13
sentence-transformers>=3.0
rank-bm25>=0.2
numpy>=1.24
python-dotenv>=1.0
groq>=1.0
openai>=1.0
fastapi>=0.100
uvicorn>=0.20
pydantic>=2.0
```

## Encoding fix (emoji crash in cmd.exe)

Windows terminal uses cp1252 which can't encode emojis. 
Error: `UnicodeEncodeError: 'charmap' codec can't encode character`

**Fix in PowerShell:**
```powershell
$env:PYTHONIOENCODING="utf-8"
python src\search_tc.py "pension"
```

**Fix in CMD:**
```cmd
set PYTHONIOENCODING=utf-8
python src\search_tc.py "pension"
```

**Fix permanently (one-time):**
```powershell
python.exe -X utf8 src\search_tc.py "pension"
```

## Activating the venv

```powershell
D:\PyCode\TC_SearchRAG\.venv\Scripts\activate
# Now 'python' uses the venv
python src\search_tc.py "pension"
```

## Búsqueda por fecha (añadido Jun 2026)

```powershell
# Activar entorno primero
.venv\Scripts\activate
$env:PYTHONIOENCODING="utf-8"

# Filtrar por rango de fechas (formato YYYY-MM-DD)
python src\search_tc.py "" --fecha "2025-01-01" --fecha-hasta "2025-03-31"

# Fecha combinada con texto y otros filtros
python src\search_tc.py "pension" --fecha "2024-06-01" --fecha-hasta "2024-12-31"

# Solo desde una fecha (hacia adelante)
python src\search_tc.py "" --fecha "2025-06-01"

# Solo hasta una fecha
python src\search_tc.py "" --fecha-hasta "2020-12-31"

# Fecha + materia + tipo
python src\search_tc.py "" --materia Pensiones --fecha "2024-01-01" --fecha-hasta "2024-12-31"
```

**Nota:** ~95% de documentos tienen fecha (10,918/11,483 después del backfill Jun 2026).
Los ~565 restantes (5%) son documentos con formatos atípicos no capturados por la regex.

La fecha aparece en la línea `| AÑO | FECHA` del output, y como campo `"fecha"` en JSON.
