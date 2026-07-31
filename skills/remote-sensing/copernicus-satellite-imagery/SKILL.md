---
name: copernicus-satellite-imagery
description: >-
  Obtener, procesar y visualizar imágenes satelitales Sentinel-2 del programa
  Copernicus (ESA) para análisis urbano, topográfico y de infraestructura
  en Perú y Latinoamérica. Cubre autenticación OAuth2, búsqueda STAC,
  descarga vía Process API, generación de índices (NDBI/NDVI) y
  visualizaciones múltiples.
category: remote-sensing
tags:
  - copernicus
  - sentinel
  - satellite-imagery
  - urban-analysis
  - ndbi
  - ndvi
  - esa
---

# Copernicus Satellite Imagery

## Cuándo usar este skill

El usuario pide imágenes satelitales de una ubicación específica para:
- Análisis de desarrollo urbano / expansión
- Evaluación topográfica o de infraestructura vial
- Monitoreo de cambios en cobertura terrestre
- Obtener imágenes actualizadas (gratis) de Sentinel-2

## Workflow

### 1. Obtener ubicación exacta

```bash
# Usar Nominatim para coordenadas exactas
curl -s "https://nominatim.openstreetmap.org/search?q=<DIRECCION>&format=json&limit=1"
# O reverse geocode:
curl -s "https://nominatim.openstreetmap.org/reverse?lat=<LAT>&lon=<LON>&format=json"
```

Definir bbox: `[lon_min, lat_min, lon_max, lat_max]`

### 2. Leer credenciales del .env

```bash
# El .env debe estar en la carpeta del proyecto
# Formato esperado:
#   user=<email>
#   password=<password>
```

Si no existe o falla, pedir al usuario que cree una cuenta en:
`https://dataspace.copernicus.eu/`

**Probar las credenciales inmediatamente** — usar API con `password` grant y reportar resultado claro (200=OK, 401=invalid_grant).

### 3. Autenticación OAuth2

```python
import requests
r = requests.post(
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
    data={
        'client_id': 'cdse-public',
        'username': '<email>',
        'password': '<password>',
        'grant_type': 'password',
        'scope': 'openid email profile'
    },
    timeout=30
)
token = r.json()['access_token']  # Expira en 1800s (30 min)
```

> **IMPORTANTE:** El token CADUCA cada 30 minutos. Si una tarea larga falla con 401, renovar token inmediatamente.

\### 4. Buscar escenas disponibles

```python
headers = {'Authorization': f'Bearer {token}'}
search = requests.post(
    "https://catalogue.dataspace.copernicus.eu/stac/search",
    headers=headers,
    json={
        "collections": ["sentinel-2-l2a"],
        "bbox": [lon_min, lat_min, lon_max, lat_max],
        "datetime": "2026-01-01T00:00:00Z/2026-07-28T23:59:59Z",
        "limit": 20,
        "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}]
    }
)
```

- **Menor cloud cover** → mejor imagen
- Para costa peruana: verano (dic-mar) tiene \<5%, invierno (jun-ago) tiene garúa >60%

### 5. Generar visualizaciones (Process API)

Usar `https://sh.dataspace.copernicus.eu/api/v1/process` con evalscripts:

| Visualización | Evalscript clave | Uso |
|--------------|-----------------|-----|
| **True Color** | `return [B04*3.5, B03*3.5, B02*3.5]` | Vista real |
| **False Color NIR** | `return [B08*3.5, B04*3.5, B03*3.5]` | Vegetación resaltada |
| **NDBI Urbano** | `ndbi=(B11-B08)/(B11+B08); ndvi=(B08-B04)/(B08+B04); return [ndbi*255, ndvi*255, 0]` | **Urbano=rojo, vegetación=verde** |
| **NDVI** | `ndvi=(B08-B04)/(B08+B04); return [ndvi*255]` | Índice vegetación |

Para GeoTIFF en vez de PNG, cambiar `"format": {"type": "image/tiff"}`.

### 6. Productos completos (OData API)

Para escenas individuales completas:

```python
# Buscar por nombre exacto (con .SAFE al final!)
odata_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Name%20eq%20%27<NAME>.SAFE%27"
# Descargar producto completo (~0.6-1GB)
dl_url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
```

## Evalscripts comunes

### VERSION=3 (obligatorio en SH Process API)
```javascript
//VERSION=3
function setup() {
    return {
        input: ["B02", "B03", "B04", "B08", "B11"],
        output: { bands: 3, sampleType: "UINT8" }
    };
}
function evaluatePixel(sample) {
    // ... custom logic
}
```

## Referencias clave

| Endpoint | URL | Uso |
|----------|-----|-----|
| Auth (token) | `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token` | OAuth2 password grant |
| STAC Search | `https://catalogue.dataspace.copernicus.eu/stac/search` | Buscar escenas |
| OData Products | `https://catalogue.dataspace.copernicus.eu/odata/v1/Products` | Catálogo descargable |
| SH Process | `https://sh.dataspace.copernicus.eu/api/v1/process` | Generar visualizaciones |
| SH WMS | `https://sh.dataspace.copernicus.eu/ogc/wms` | WMS para QGIS |

## Limitaciones conocidas

- **VHR 2024 Mosaic**: es capa VISUAL en Copernicus Browser, NO descargable via API STAC
- **CCM (Contributing Missions)**: NO tienen datos para Sudamérica en la mayoría de casos
- **Token expira**: 30 min exactos, renovar antes de tareas largas
- **Browser JS SPA**: Copernicus Browser no renderiza en headless browser (empty page). Usar API en su lugar
- **Piura (costa)**: en invierno peruano (jun-ago) la garúa da >60% nubosidad. Mejor buscar verano (dic-mar)

## Pitfalls

1. **STAC item ID ≠ OData product name**: El STAC devuelve IDs sin `.SAFE`, pero OData los busca CON `.SAFE` al final
2. **S3 URLs no accesibles directamente**: Los assets en `s3://eodata/...` requieren credenciales AWS temporales
3. **Process API requiere evalscript**: Si falta, da 400 "Missing evalscript" o "Missing or empty evalscript"
4. **bbox CRS**: Usar siempre CRS84 (lon/lat WGS84)
5. **Token caducado**: HTTP 401 "AccessToken signature invalid" = renovar token, no reintentar igual
