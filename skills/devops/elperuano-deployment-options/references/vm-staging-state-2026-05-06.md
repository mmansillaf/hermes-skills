# VM Staging — Estado Post-Restauración (2026-05-06)

## Conexión
- IP: 192.168.18.217
- User: cmansilla / u765432
- Hostname: cmansilla-VMware-Virtual-Platform

## Estado Inicial
- Ubuntu 24.04.4 LTS
- Disco: 30G — 28G usados (358 MB libres = 99%)
- Python: 3.12.3 (sistema) + 3.11.15 (en .venv anterior)
- Docker: instalado pero cmansilla no tiene permisos (no en grupo docker)
- API puerto 8000: INACTIVA
- Sin systemd service
- Sin git repo (archivos copiados via SFTP)

## Datos
| Componente | Tamaño |
|-----------|--------|
| data/normas_total.db | 1.1 GB (SQLite, 97,809 normas) |
| data/qdrant_storage | 1.5 GB |
| data/neo4j_data | 850 MB |
| .venv (original con CUDA) | 5.5 GB |
| huggingface cache | 377 MB |

## Acciones Realizadas

### 1. Liberación de disco (358 MB → 6.3 GB libres)
- Eliminado .venv original con CUDA (5.5 GB → ahorro 3.4 GB)
- Eliminadas snap old versions (core22@2292, firefox@7766, snap-store@1270, snapd@25935)
- `sudo apt clean && sudo apt autoremove`
- Eliminado ~/.cache/huggingface/ (377 MB)

### 2. Dependencias del sistema
- Instalado `sshpass` en máquina local (para conexiones SSH automatizadas)
- Instalado `python3-venv` en VM (faltaba, causaba "ensurepip not available" al crear .venv)
  - Comando: `echo 'u765432' | sudo -S apt-get install -y python3-venv python3-pip`

### 3. Sincronización de código
- rsync desde repo local al VM excluyendo: .venv/, data/, __pycache__/, .git/, logs/
- Ahora tiene KAG patterns (src/kag_patterns/), api_rest.py actualizado, scripts/

### 4. Recreación de .venv (EN PROGRESO — background)
- torch CPU-only (sin CUDA): `--index-url https://download.pytorch.org/whl/cpu`
- Dependencies: sentence-transformers, transformers, qdrant-client, neo4j, groq, fastapi, etc.

## Pendiente
- .venv: esperar que termine pip install en background
- Agregar cmansilla al grupo docker: `sudo usermod -aG docker cmansilla`
- Iniciar Docker (Qdrant + Neo4j): `docker compose up -d`
- Crear systemd service para la API
- Iniciar API y verificar health
- Sincronizar .env con API keys correctas
