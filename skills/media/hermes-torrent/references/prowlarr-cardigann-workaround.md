# Prowlarr Indexer Setup — Hallazgos y Workarounds

## Contexto
Prowlarr se configuro via Docker (`linuxserver/prowlarr`) en el stack torrent.
Se descubrio que agregar indexadores via API REST tiene limitaciones.

## API Key
Se obtiene de: `docker exec hermes_indexer cat /config/config.xml | grep -oP '<ApiKey>\K[^<]+'`
O desde el navegador: Settings > General > API Key.

## Indexadores disponibles
Prowlarr tiene 624+ definiciones de indexadores. Consultar via:
```python
req = urllib.request.Request("http://localhost:9696/api/v1/indexer/schema?pageSize=200")
req.add_header("X-Api-Key", API_KEY)
with urllib.request.urlopen(req) as resp:
    defs = json.loads(resp.read())["records"]
```

## Problema: Cardigann-based indexers (fileKey null)
Los indexadores que usan implementacion `Cardigann` (1337x, YTS, The Pirate Bay, etc.)
**NO se pueden agregar via API REST**. Fallan con:
```
500: Value cannot be null. (Parameter 'fileKey')
ArgumentNullException: IndexerDefinitionUpdateService.GetCachedDefinition()
```

### Causa
Prowlarr necesita descargar y cachear las definiciones Cardigann (archivos YAML)
antes de poder instanciar un indexador. La API no tiene endpoint publico para
forzar esta descarga, y el cache no se genera hasta que la UI web lo gatilla.

### Solucion A: Usar indexadores no-Cardigann (via API)
Funcionan sin cache previo. Probado:
- `Anidex` (anime, publico) — implementation: `Anidex` ✅

Ejemplo:
```python
indexer_config = {
    "name": "Anidex",
    "implementation": "Anidex",
    "configContract": "AnidexSettings",
    "fields": [],
    "definitionName": "Anidex",
    "protocol": "torrent",
    "priority": 25,
    "enabled": True,
    "appProfileId": 1
}
# POST /api/v1/indexer con X-Api-Key header
```

Posibles candidatos no-Cardigann publicos adicionales:
- `Knaben` (meta-search engine) — implementation: `Knaben`
- `Internet Archive` — implementation: `Cardigann` (caeria en misma trampa)

### Solucion B: UI web (recomendada para Cardigann)
1. Abrir `http://localhost:9696` en navegador
2. Indexers → Add Indexer
3. Buscar "1337x" (o el que se necesite)
4. Clickear Save — Prowlarr descarga la definicion Cardigann y la cachea
5. Una vez cacheado, la API lo reconoce

## Nota sobre appProfileId
El endpoint `GET /api/v1/appProfile` devuelve los perfiles disponibles:
```json
[{"name": "Standard", "enableRss": true, "enableAutomaticSearch": true,
  "enableInteractiveSearch": true, "minimumSeeders": 1, "id": 1}]
```
Usar `appProfileId: 1` (Standard) para nuevos indexadores.

## Referencia
- Prowlarr API Docs: https://wiki.servarr.com/prowlarr/api
- Cardigann: https://github.com/cardigann/cardigann