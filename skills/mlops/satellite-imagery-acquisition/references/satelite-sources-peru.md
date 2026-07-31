# Satellite Sources for Peru — Knowledge Bank

All free and low-cost satellite imagery sources, URLs, contacts, and technical specs for Peruvian territory.

## 1. PeruSAT-1 (CONIDA)

| Spec | Value |
|------|-------|
| Resolution | 0.7m pan / 2.8m MS (4 bands: B,G,R,NIR) |
| Swath | 14.5 km |
| Revisit | ~3 days (tasking) |
| Archive | >500,000 images |
| Cost | Free for public entities, universities, researchers |

**Access**: COF-NG platform via gob.pe/conida
**Contacts**: atencionalcliente@conida.gob.pe, mespa@conida.gob.pe
**WhatsApp**: 995 952 379
**Phone**: (01) 416-2563 / (01) 416-2539 anexo 101

**Process**: Formal request via Mesa de Partes Virtual. Include polygon coordinates (KML/Shapefile), date range, product type, and project justification.

## 2. Sentinel-2 (Copernicus/ESA)

| Spec | Value |
|------|-------|
| Resolution | 10m (B,G,R,NIR), 20m (SWIR), 60m (coastal) |
| Swath | 290 km |
| Revisit | 5 days (S2A+S2B+S2C) |
| Bands | 13 multispectral |
| Archive | 2014–present |
| Cost | Free, open data (CC-BY) |

**Access**:
- Copernicus Data Space Ecosystem: https://browser.dataspace.copernicus.eu/
- STAC API: https://catalogue.dataspace.copernicus.eu/stac/
- Process API: https://sh.dataspace.copernicus.eu/api/v1/process
- Google Earth Engine: COPERNICUS/S2_SR_HARMONIZED

**Piura coverage**: Tile T17MNQ. Best images Dec–Apr (summer, <5% cloud). Winter Jun–Aug has garúa >60% cloud.

## 3. Sentinel-1 (SAR)

| Spec | Value |
|------|-------|
| Type | C-band SAR (radar) |
| Resolution | 5×20m (IW mode) |
| Revisit | 6 days |
| Cost | Free |
| Best for | Cloud penetration, Amazon/cloudy regions |

## 4. Landsat 8/9 (USGS/NASA)

| Spec | Value |
|------|-------|
| Resolution | 30m MS, 15m pan |
| Revisit | 16 days |
| Archive | 1972–present |
| Cost | Free |

**Access**: https://earthexplorer.usgs.gov/ or Google Earth Engine

## 5. CBERS-4A (INPE Brazil/China)

| Spec | Value |
|------|-------|
| Resolution | 2m pan, 8m MS (WPM camera) |
| Cost | Free |
| Coverage | South America |

**Access**: http://www.dgi.inpe.br/CDSR/

## 6. VHR 2024 Mosaic (NEW — Jul 2026)

Announced 22 July 2026. Very High Resolution mosaic of 2024 imagery available in Copernicus Browser. Check coverage for your AOI via the web interface.

## 7. Other Peruvian Geoportals

| Portal | URL | Key Data |
|--------|-----|----------|
| GeoPerú | visor.geoperu.gob.pe | Multi-source, no registration |
| IDEP | geoidep.gob.pe | WMS/WFS/WMTS catalog |
| IGN | ign.gob.pe | Cartas 1:100,000, ortofotos |
| MINAM Geoservidor | geoservidor.minam.gob.pe | Vegetation, deforestation |
| SIGRID (CENEPRED) | sigrid.cenepred.gob.pe | Orthophotos, risk maps |
| MTC | mtc.gob.pe | National road network (shapefile) |
| GeoBosques | geobosques.minam.gob.pe | Real-time deforestation alerts |

## 8. Asia Low-Cost Options

| Source | Resolution | Approx Cost | Best For |
|--------|-----------|-------------|----------|
| Jilin-1 (China, CGSTL) | 0.5m | ~$2-5/km² | Best price/resolution ratio |
| KOMPSAT (Korea, KARI) | 0.7m + SAR | Low/medium | Cloudy zones + high res |
| Cartosat (India, ISRO) | 0.25m | Low | Cadastre, engineering |
| AW3D (Japan, NTT) | 0.5-5m DEM | Low/medium | High-precision topography |

## Session-specific: Piura Valle Sagrado (Jul 2026)

**Coordinates**: -5.16741, -80.69825 (Carr Interoceánica Nte 27, Urb. 26 de Octubre, Piura)
**Best scene**: S2B_MSIL2A_20260108T155219_N0511_R111_T17MNQ_20260108T205139.SAFE (0.64GB)
**Cloud cover**: 0.01% (8 Jan 2026) — practically cloud-free
**Seasonal pattern**: Piura coast has garúa (coastal fog) Jun–Aug with >60% cloud. Best images are Dec–Apr (summer).
**Download via**: Sentinel Hub Process API with evalscript (true color, B04*3.5 + B03*3.5 + B02*3.5)
**Output formats**: 
  - PNG: `piura_valle_sagrado_8ene2026.png` (1100×1100px, ~5.5×5.5km, 1MB)
  - GeoTIFF: `piura_valle_sagrado_8ene2026.tiff` (164KB, QGIS-ready)
**Consolidated guide**: `CONSOLIDADO_FUENTES_SATELITALES.md` in session SateliteImage/ directory (15KB, 10 sections covering all sources, strategies, and tools)
