# Docker Volume Transfer — Qdrant + Neo4j entre máquinas

Sesión: 05-may-2026. Técnica para transferir volúmenes Docker (Qdrant 388 MB,
Neo4j 850 MB) desde máquina local a VM staging vía paramiko SFTP.

## Por qué SFTP en vez de SCP/rsync

SCP requiere `sshpass` (no siempre disponible) o ingreso manual de password.
Rsync requiere rsync instalado en ambos extremos. SFTP vía paramiko funciona
con solo Python + paramiko, sin dependencias de sistema.

## Script de transferencia

```python
import paramiko, tarfile, io, os, time

VM_HOST = '192.168.18.217'
VM_USER = 'cmansilla'
VM_PASS = 'u765432'
LOCAL_DATA = '/ruta/local/data'

def create_tar_stream(dirpath):
    """Tar.gz en memoria, devuelve bytes."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        for root, dirs, files in os.walk(dirpath):
            for f in files:
                fullpath = os.path.join(root, f)
                arcname = os.path.relpath(fullpath, os.path.dirname(dirpath))
                tar.add(fullpath, arcname=arcname)
    return buf.getvalue()

# Conectar
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(VM_HOST, username=VM_USER, password=VM_PASS)
sftp = client.open_sftp()

# 1. Parar Docker en VM
client.exec_command("sudo docker compose -f /opt/elperuano/docker-compose.yml stop")

# 2. Transferir Qdrant
qdrant_data = create_tar_stream(os.path.join(LOCAL_DATA, 'qdrant_storage'))
with sftp.file('/tmp/qdrant_data.tar.gz', 'wb') as f:
    f.write(qdrant_data)

# 3. Transferir Neo4j
neo4j_data = create_tar_stream(os.path.join(LOCAL_DATA, 'neo4j_data'))
with sftp.file('/tmp/neo4j_data.tar.gz', 'wb') as f:
    f.write(neo4j_data)

# 4. Extraer en VM
client.exec_command(
    "cd /opt/elperuano && "
    "sudo rm -rf data/qdrant_storage data/neo4j_data && "
    "sudo tar xzf /tmp/qdrant_data.tar.gz -C data/ && "
    "sudo tar xzf /tmp/neo4j_data.tar.gz -C data/"
)

# 5. Arrancar Docker
client.exec_command("sudo docker compose -f /opt/elperuano/docker-compose.yml up -d")
```

## Tamaños típicos

| Dataset | Tamaño | Transferencia SFTP |
|---------|--------|--------------------|
| Qdrant (3 colecciones) | 388 MB comprimido (304 MB gzip) | ~80s en LAN |
| Neo4j (grafo) | 850 MB comprimido (99 MB gzip) | ~26s en LAN |
| SQLite (normas_total.db) | 1.1 GB | Aparte, por SCP |

## Verificación post-transferencia

```bash
# En VM
curl -s http://localhost:6333/collections | python3 -c "import sys,json; print(len(json.load(sys.stdin)['result']['collections']))"
# Debe devolver 3

curl -s -u neo4j:<NEO4J_PASSWORD> -H 'Content-Type: application/json' \
  http://localhost:7474/db/neo4j/tx/commit \
  -d '{"statements":[{"statement":"MATCH (n) RETURN count(n) as c"}]}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['results'][0]['data'][0]['row'][0])"
# Debe devolver 113886
```

## Pitfalls

1. **Disco lleno**: Verificar `df -h /` ANTES de transferir. Mínimo 5 GB libres.
2. **Permisos Docker**: Los volúmenes extraídos deben ser `chown` al usuario correcto.
   Qdrant usa UID 1000, Neo4j usa UID 7474.
3. **Docker debe estar parado**: No extraer datos mientras los containers corren.
4. **Tarballs en /tmp**: Borrarlos después de extraer para liberar espacio.
