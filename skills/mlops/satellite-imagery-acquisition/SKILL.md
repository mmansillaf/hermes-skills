---
name: satellite-imagery-acquisition
category: mlops
description: "Acquire free/low-cost satellite imagery for Peru and Latin America — authentication with Copernicus Data Space, STAC/OData search, Sentinel Hub Process API download, duplicate cleanup, and consolidated knowledge of all free satellite sources (PeruSAT-1, Sentinel-2/1, Landsat, CBERS, Planet, Jilin-1, VHR 2024 Mosaic)."
tags: [sentinel, copernicus, landsat, satellite, gis, peru, geospatial, remote-sensing]
triggers:
  - "obtener imágenes satelitales"
  - "descargar imágenes de satélite"
  - "sentinel-2"
  - "copernicus data space"
  - "imágenes satelitales gratis"
  - "satellite imagery download"
  - "peru satelital"
  - "valle sagrado piura"
  - "CONIDA PeruSAT-1"
---

# Satellite Imagery Acquisition

Acquire free/ low-cost satellite imagery for Peru and Latin America — topographical analysis, road/infrastructure planning, urban development assessment. Covers authentication, search, download, and post-processing.

## Authentication (Copernicus Data Space Ecosystem)

### Register
1. Go to https://dataspace.copernicus.eu/ and create a free account
2. Confirm email

### Get OAuth2 Token (password grant)
The `cdse-public` client supports the `password` grant type (verified via `/.well-known/openid-configuration`).

```python
import requests
r = requests.post(
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
    data={
        'client_id': 'cdse-public',
        'username': 'your@email.com',
        'password': 'your_password',
        'grant_type': 'password',
        'scope': 'openid email profile'
    },
    timeout=30
)
token = r.json()['access_token']  # ~2400 chars, expires in 1800s (30 min)
```

## Search for Scenes

### Via STAC API (for scene metadata)
```python
headers = {'Authorization': f'Bearer {token}'}
query = {
    'collections': ['sentinel-2-l2a'],
    'bbox': [west, south, east, north],
    'datetime': '2026-01-01T00:00:00Z/2026-07-28T23:59:59Z',
    'limit': 10
}
r = requests.post(
    "https://catalogue.dataspace.copernicus.eu/stac/search",
    headers=headers, json=query, timeout=30
)
# Key fields: properties.datetime, properties.eo:cloud_cover, id, bbox
```

### Via OData API (product-level, includes file size)
```python
odata_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
params = {
    "$filter": "contains(Name,'T17MNQ') and ContentDate/Start ge 2026-01-01T00:00:00Z",
    "$orderby": "ContentDate/Start desc",
    "$top": 10
}
r = requests.get(odata_url, headers=headers, params=params, timeout=30)
# Each product: Id, Name, ContentLength (bytes), GeoFootprint, ContentDate
```

### Cloud cover filtering
Field: `eo:cloud_cover` (0–100). For coastal Peru (Piura), best images are **Dec–Apr** (summer). Winter (Jun–Aug) has garúa (coastal fog) >60%. Sort by cloud cover ascending to find clearest scenes.

## Credentials

Store credentials in a `.env` file in the project directory:
```
#copernicus login credentials
user=your@email.com
password=your_password
```

Load at runtime:
```python
import os
# Read .env manually (or use python-dotenv)
creds = {}
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            creds[k] = v
```

## Download Best Scene

### Via Sentinel Hub Process API (recommended — downloads only your bbox)
Supports both PNG (preview) and GeoTIFF (QGIS analysis) output from the same API.

```python
payload = {
    "input": {
        "bounds": {
            "bbox": [west, south, east, north],
            "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
        },
        "data": [{
            "type": "sentinel-2-l2a",
            "dataFilter": {
                "timeRange": {
                    "from": "2026-01-08T00:00:00Z",
                    "to": "2026-01-08T23:59:59Z"
                },
                "maxCloudCoverage": 5
            }
        }]
    },
    "evalscript": """
        //VERSION=3
        function setup() {
            return {
                input: ["B02", "B03", "B04"],
                output: { bands: 3, sampleType: "UINT8" }
            };
        }
        function evaluatePixel(sample) {
            return [sample.B04 * 3.5, sample.B03 * 3.5, sample.B02 * 3.5];
        }
    """,
    "output": {
        "width": 1100,
        "height": 1100,
        "responses": [{
            "identifier": "default",
            "format": {"type": "image/png"}   # image/tiff for GeoTIFF
        }]
    }
}
r = requests.post(
    "https://sh.dataspace.copernicus.eu/api/v1/process",
    headers=headers, json=payload, timeout=120
)
if r.status_code == 200:
    with open("output.png", "wb") as f:
        f.write(r.content)
```

**Change `"type": "image/png"` → `"type": "image/tiff"`** for a GeoTIFF ready to open in QGIS. The GeoTIFF is smaller than PNG (~164KB vs 1MB for a 1100×1100px area).

### Evalscript tips
- Must start with `//VERSION=3` or gets 400 error (`COMMON_EXCEPTION`)
- `function setup()`: declares input bands and output format
- `function evaluatePixel(sample)`: pixel-by-pixel transformation
- **Scaling**: L2A reflectance is 0–1. Multiply by 3.5 for true-color display.
- **sampleType**: `"UINT8"` for 8-bit output (0-255), omit for float
- Available bands: B02 (blue,10m), B03 (green,10m), B04 (red,10m), B08 (NIR,10m)

### Bbox sizing
- 0.05° × 0.05° (~5.5×5.5km) at 1100×1100px → ~5m/pixel visual

## Free Satellite Sources for Peru

1. **PeruSAT-1 (CONIDA)** 0.7m — Free for public entities/universities vía COF-NG (solicitud formal)
2. **VHR 2024 Mosaic** submétrica — Free (nuevo Jul 2026 en Copernicus Browser)
3. **Sentinel-2 (Copernicus)** 10m — Free, global, 5 días revisita
4. **Sentinel-1 (SAR)** 5–20m — Free, penetra nubes (Amazonía)
5. **Landsat 8/9 (USGS)** 15–30m — Free, archivo desde 1972
6. **CBERS-4A (INPE)** 2m pan — Free, Sudamérica
7. **PlanetScope** 3m — Free (edu/NGO), diario
8. **Jilin-1 (China)** 0.5m — ~$2-5/km², mejor relación resolución/precio

## DEM Sources
- Copernicus DEM GLO-30 (30m, free) — mejor DEM gratuito general
- ALOS AW3D30 (30m, free) — mejor para Andes
- ALOS PALSAR (12.5m, free) — zonas nubladas

## Duplicate Detection
```python
import hashlib, os
hashes = {}
for f in sorted(os.listdir(folder)):
    if not f.endswith('.txt'): continue
    with open(os.path.join(folder, f), 'rb') as fh:
        h = hashlib.md5(fh.read()).hexdigest()
    hashes.setdefault(h, []).append(f)
for h, flist in hashes.items():
    if len(flist) > 1:
        for f in flist[1:]:
            os.remove(os.path.join(folder, f))
```

## Sentinel-1 SAR (for Cloudy Periods)

When optical imagery is blocked by clouds (Jun–Aug garúa on the coast, or Amazon year-round), use Sentinel-1 SAR radar. The Process API works the same way but with different bands:

```python
payload = {
    "input": {
        "bounds": {"bbox": [west, south, east, north], "properties": {"crs": "..."}},
        "data": [{
            "type": "sentinel-1-grd",
            "dataFilter": {
                "timeRange": {"from": "...", "to": "..."},
                "orbitDirection": "DESCENDING"
            }
        }]
    },
    "evalscript": """
        //VERSION=3
        function setup() {
            return { input: ["VV", "VH"], output: { bands: 3 } };
        }
        function evaluatePixel(sample) {
            return [2*sample.VV, 1.5*sample.VH, 0.5*sample.VV];
        }
    """,
    "output": {"width": 1100, "height": 1100, "responses": [{"identifier": "default", "format": {"type": "image/png"}}]}
}
```

## Project Knowledge Bank

After each session, save extended reference material under the `references/` directory:
- `references/satelite-sources-peru.md` — canonical reference for all Peruvian sources
- Create additional `references/<topic>.md` files for session-specific deep dives

A consolidated master document (`CONSOLIDADO_FUENTES_SATELITALES.md`) with 10 sections covering all sources, strategies, and tools is available for reference in session directories.

## Pitfalls
- **OData download ($value endpoint) returns 401** even with valid token. Use **Sentinel Hub Process API** instead.
- **Cloud cover on coast**: Jun–Aug has garúa. Best images Dec–Apr (check 0.01% cover on 8 Jan for Piura example).
- **Token expiry**: 30 min. Refresh via password grant (same endpoint).
- **PeruSAT-1**: Not self-service. Requires formal solicitud vía Mesa de Partes de CONIDA. Platform is COF-NG (updated Sept 2025).
- **Evalscript**: Must include `//VERSION=3` or gets 400 error (`COMMON_EXCEPTION`).
- **VHR 2024 Mosaic**: Available only as a visual layer in the Copernicus Browser web interface. NOT downloadable via STAC or OData API.
