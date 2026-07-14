# Guía de Despliegue — El Peruano RAG en Linux

## Requisitos

| Recurso | Mínimo |
|---------|--------|
| RAM | 8 GB (16 GB recomendado) |
| Disco | 2 GB (datos) + 300 MB (código) |
| Python | 3.10+ |
| Docker | 20.10+ (para Qdrant + Neo4j) |
| API Keys | Groq + Serper (gratuitas) |

## Instalación

```bash
# 1. Clonar
git clone https://github.com/mmansillaf/GRegElPeruano_v5.1.git
cd GRegElPeruano_v5.1

# 2. Entorno virtual
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Descomprimir datos
gunzip data/normas_2024.db.gz
# Descargar qdrant_storage.tar.gz y neo4j_data.tar.gz de Google Drive
# Descomprimir en data/

# 4. Configurar
cp .env.example .env
# Editar GROQ_API_KEY, SERPER_API_KEY

# 5. Levantar servicios
cd docker && docker-compose up -d && cd ..
sleep 10  # Esperar que Qdrant y Neo4j estén listos

# 6. Iniciar API
python3 api_rest.py
# → http://localhost:8000
```

## Verificación

```bash
curl http://localhost:8000/health
# {"status":"ok","services":{"sqlite":"OK 18694 normas",...}}

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Ley 32108","profile":"abogado"}'
```

## Puertos

| Servicio | Puerto |
|----------|--------|
| API REST | 8000 |
| Qdrant HTTP | 6333 |
| Qdrant gRPC | 6334 |
| Neo4j HTTP | 7474 |
| Neo4j Bolt | 7687 |

## Restauración desde backup

```bash
cp backups/api_rest_TIMESTAMP.py api_rest.py
cp backups/normas_2024_TIMESTAMP.db data/normas_2024.db
python3 api_rest.py
```

## Troubleshooting

**API no inicia:** Limpiar caché Python:
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
```

**Qdrant Broken pipe:** Reiniciar API (no Qdrant):
```bash
pkill -9 -f api_rest.py && python3 api_rest.py
```
