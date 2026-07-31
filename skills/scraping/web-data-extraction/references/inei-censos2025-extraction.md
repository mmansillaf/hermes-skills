# INEI Censos 2025 — Comparativo Territorial Data Extraction

## Source
- URL: `https://censos2025.inei.gob.pe/resultados/comparativo-territorial`
- Blocked: WAF at TLS level (SSL_ERROR_SYSCALL), all IPs from non-Peruvian ranges blocked
- Type: Angular SPA (production build)

## Wayback Capture
- URL: `https://web.archive.org/web/20260611170751/https://censos2025.inei.gob.pe/resultados/comparativo-territorial`
- Config chunk (apiUrl, endpoints): `chunk-4AZRQDRY.js`
  ```js
  apiUrl: "/api/v1"
  apiExternalUrl: "https://multiproyecto.inei.gob.pe/api/v1"
  socketUrl: "https://censos2025.inei.gob.pe/postcensal-resultados-backend/"
  recaptcha: "6LfGjWUrAAAAAAf7xdAtoJgvozGjkvtNKwsIHGn_"
  ```
- Main component chunk: `chunk-PAQZBWLL.js` (ComparativoTerritorial)
- Shared chunks (services): various `chunk-*.js` files ~140KB each

## Page Structure (from route config)
```
/resultados/
  /dashboard         → ResultadosDashboard (Primeros Resultados)
  /comparativo-territorial → ComparativoTerritorial (active tab)
```

## API Endpoints (from service analysis)
- `getCabeceraComparativoTerritorial(tiempo, nivel)` — Returns column headers/config
- `getDataTablaComparativoTerritorial(filtros)` — Returns paginated table data
- `descargarExcel(filtros)` — Returns Excel blob
- Nivel codes: 3=Departamental, 4=Provincial, 5=Distrital

## Data Retrieved from JS Bundle

### National-level stats (hardcoded in globalStats):
- totalPopulation: 35,356,367
- womenPercentage: 51.2%, menPercentage: 48.8%
- limaPopulation: 10,126,052

### Age pyramid data (20 age ranges, percentages):
0-4 through 95+, with male/female percentages per range

### Department stats (embedded in globalStats.departmentStats):
25 departments with: maleCount, femaleCount, malePerc, femalePerc, densityIndex

## Excel Data (manually downloaded by user)
File: `Estructura demográfica y envejecimiento poblacional según departamentos seleccionados del Perú 2025.xlsx`
Sheet: "Comparativa Departamental" | 25 departments + Perú national | 12 columns

### Columns:
1. Departamento
2. Población total
3. Población censada
4. Población omitida
5. Hombres
6. Mujeres
7. Razón hombre-mujer (índice de masculinidad)
8. Edad promedio
9. Edad mediana
10. Personas de 60 y más años
11. Porcentaje de personas de 60 y más años
12. Índice de envejecimiento

### Key findings:
- Perú total: 34,157,732 (vs 35,356,367 in JS bundle — the bundle may include an updated projection)
- Lima Metropolitana: 10,129,708 (29.7% of country), índice envejecimiento 82.6
- Madre de Dios: youngest (7.8% 60+, índice 27.1)
- Puno: highest aging index (87.7)
- Callao excluded as separate entity from Lima

### Path (WSL):
```
/mnt/d/Descargas/UPN-Investigacion/UPN_InclusionFinanciera_Territorial_DesarrolloLocal_Investigacion_ML-main/
  Estructura demográfica y envejecimiento poblacional según departamentos seleccionados del Perú 2025.xlsx
```

## Lesson Learned
The WAF blocks at TLS handshake — no HTTP tool can bypass. Wayback Machine works because it already has the capture. The JS bundles contain substantial static data even without hitting the live API.
