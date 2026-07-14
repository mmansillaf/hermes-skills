# Despliegue en VM Ubuntu Local (Staging)

## Requisitos

- Ubuntu 22.04+ (VM VirtualBox/VMware/QEMU)
- Mínimo 8 GB RAM, 4 cores, 50 GB disco
- Python 3.11+, Docker, git

## Paso a paso

### 1. Preparar la VM

```bash
sudo apt update && sudo apt install -y docker.io docker-compose python3.11 python3-pip git
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Copiar archivos desde el host a la VM

```bash
# Desde el host (tu máquina principal)
cd ~/el_peruano_rag/PeruanoSearchEngine02

# Copiar DB (1 GB — puede tomar varios minutos)
scp data/normas_total.db usuario@192.168.x.x:~/rag/data/

# Copiar código
scp api_rest.py usuario@192.168.x.x:~/rag/
scp -r src/ usuario@192.168.x.x:~/rag/
scp requirements.txt docker-compose.yml .env usuario@192.168.x.x:~/rag/
```

### 3. Instalar dependencias Python

```bash
# En la VM
cd ~/rag
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Levantar servicios Docker

```bash
docker-compose up -d    # Qdrant + Neo4j
docker ps               # Verificar que ambos corren
```

### 5. Vectorizar normas en Qdrant

```bash
python3 scripts/vectorize_total.py    # ~30 min para 97,809 normas
```

### 6. Iniciar API y probar

```bash
python3 api_rest.py &
sleep 10
curl http://localhost:8000/health
python3 test_usuario.py
```

### 7. Verificar todo

```bash
curl http://localhost:8000/token-stats?granularity=total
curl http://localhost:8000/stats
```

## Problemas comunes

- **Puerto ocupado**: `sudo lsof -i :8000` → matar proceso
- **Qdrant no inicia**: verificar `docker logs qdrant`
- **DB no encontrada**: verificar path `data/normas_total.db`
- **Memoria insuficiente**: la vectorización usa ~4 GB RAM. Asignar 8 GB a la VM.
