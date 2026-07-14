---
name: elperuano-rag-backup-restore
title: Backup y Restauración — El Peruano RAG
description: Procedimiento completo de backup multi-nivel y restauración del sistema El Peruano RAG. Incluye GitHub tags, backup local, y Google Drive.
---

# Backup y Restauración — El Peruano RAG

## Niveles de Backup

### Nivel 1: GitHub Tag (inmutable, semántico)
```bash
cd PeruanoSearchEngine02

# Crear tag con nombre semántico: version + descripcion + fecha
git tag -a "v4.0-pre-optimizacion-20260501" -m "Snapshot pre-optimizacion: streaming + paralelo + cache + router 2 niveles. api_rest.py 1959 lineas, 99% bateria."
git push origin v4.0-pre-optimizacion-20260501
```

Restaurar: `git checkout v4.0-pre-optimizacion-20260501`

**Patrón de nombres:** `v{version}-{fase}-{fecha}` donde fase describe QUÉ viene después, no qué hay ahora. Ej: `v4.0-pre-seguridad-fixes` significa "este es el estado ANTES de aplicar los fixes de seguridad".

**Ver tags existentes:** `git tag -l "v4*"`

**⚠️ Pitfall: git commit puede colgarse con directorios grandes.** Si `GROQ_Invoice/`, `data/` u otros directorios pesados están dentro del repo, `git add -A && git commit` puede tardar minutos o colgar (timeout a 180s). Solución: usar `.gitignore` para excluir directorios de datos, o hacer backup local sin git (Nivel 2). El backup local con checksum es más rápido y confiable para snapshots pre-refactor.

### Nivel 2: Backup Local con Checksum
```bash
BACKUP_DIR=PeruanoSearchEngine02/backups
DATE=$(date +%Y%m%d)

# Backup del archivo crítico
cp api_rest.py $BACKUP_DIR/api_rest_v4.0_${DATE}.py

# Checksum para verificar integridad
sha256sum api_rest.py > $BACKUP_DIR/api_rest_v4.0.sha256

# Backup seguro de .env (nunca commitear)
mkdir -p $BACKUP_DIR/v4.0/
cp .env $BACKUP_DIR/v4.0/.env.backup

# Commitea los backups al repo
git add $BACKUP_DIR/api_rest_v4.0_*.py $BACKUP_DIR/*.sha256
git commit -m "backup: api_rest.py snapshot pre-fixes seguridad"
git push origin main
```

**Verificar integridad:**
```bash
sha256sum -c backups/api_rest_v4.0.sha256
# Debe decir: api_rest.py: OK
```

**Restaurar solo un archivo:**
```bash
cp backups/api_rest_v4.0_pre_seguridad_20260501.py api_rest.py
```

### Nivel 3: Google Drive / R2 (datos comprimidos)
```bash
cd data
tar -czf ~/GoogleDrive/normas_2024.tar.gz normas_2024.db
tar -czf ~/GoogleDrive/qdrant_storage.tar.gz qdrant_storage/
tar -czf ~/GoogleDrive/neo4j_data.tar.gz neo4j_data/
```

## Verificación Post-Restauración
```bash
curl http://localhost:8000/health
# Esperado: {"status":"ok","services":{"sqlite":"OK 18694 normas",...}}

curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Ley 32108","profile":"abogado"}'
# Debe responder con contenido, no "no se encontró"
```


## Backups de Código (Pre-Refactor)

Antes de cualquier refactorización, hacer backup del archivo principal + todo src/:

```bash
DATE=$(date +%Y%m%d)
cp api_rest.py backups/api_rest_v{VERSION}_pre_{FASE}_${DATE}.py
sha256sum api_rest.py > backups/api_rest_v{VERSION}_${DATE}.sha256
cp -r src backups/src_backup_${DATE}/
sha256sum -c backups/api_rest_v{VERSION}_${DATE}.sha256  # verificar
```

Rollback:
```bash
cp backups/api_rest_v{VERSION}_pre_{FASE}_${DATE}.py api_rest.py
cp -r backups/src_backup_${DATE}/* src/
```

Guardar estado en `reports/estado_pre_{fase}_${DATE}.txt` con:
- Versión y fecha
- Archivos backup creados
- DB y servicios (normas, Qdrant, Neo4j)
- Cambios recientes
- Comando de rollback

## Fixes Críticos en api_rest.py

| Línea | Fix | Qué hace |
|-------|-----|----------|
| 822 | Relevance no invertida | `(abs(rank)-min)/range` sin `1.0-` |
| 899 | Texto expandido | `[:2000]→[:4000]` contexto al LLM |
| 545-553 | Confidence queries largas | Penalización reducida para >100 chars |
| 815-917 | extract_structured_metadata() | Extracción regex de DNIs, CAP, registros |
| 574-624 | Búsqueda en leyes.db | Detección de leyes externas + FTS5 en leyes.db |
| 1429-1494 | Router B/I/A | Clasificador + modo directo + modo asistido |
