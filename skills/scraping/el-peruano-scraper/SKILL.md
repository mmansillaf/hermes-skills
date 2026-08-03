---
name: el-peruano-scraper
description: Use when scraping El Peruano (busquedas.elperuano.pe).
category: scraping
triggers:
  - "el peruano scraping"
  - "busquedas.elperuano.pe"
  - "cuadernillo PC procesos constitucionales"
  - "diario oficial peru descarga pdf"
  - "elperuano cuadernillo"
  - "descargar cuadernillos el peruano"
---

# El Peruano (diario oficial) — Scraping de cuadernillos y publicaciones

## Cuándo usar

- Descargar cuadernillos/publicaciones de El Peruano por fecha:
  `https://busquedas.elperuano.pe/cuadernillo/<TIPO>/<YYYYMMDD>`
  (PC = Procesos Constitucionales; existen también CA, JU, DJ, IN...).
- Extraer casos jurídicos individuales (amparo, hábeas corpus,
  cumplimiento, inconstitucionalidad...) desde los PDFs de un cuadernillo.
- Cualquier sitio con WAF Imperva que corte el TLS a clientes no-navegador,
  o SPA React Router v7 con datos del loader en stream embebido.

## Portal

| Atributo | Detalle |
|---|---|
| URL | `https://busquedas.elperuano.pe/cuadernillo/PC/YYYYMMDD` |
| WAF | Imperva/Incapsula (IP 38.187.10.142) — fingerprint de cliente |
| Stack | SPA React Router v7 (Remix-style), data del loader en `streamController.enqueue("...")` |
| Formato | 1 PDF por fecha = cuadernillo completo (8-196 pp; ~1.5 MB típico) |
| 404 | Fecha sin publicación (feriados/fines de semana) → skip silencioso; sábados/domingos nunca publican |
| Costo | $0 — requests + pymupdf + regex, sin APIs pagas |

## Paso 1 — Bypass del WAF Imperva (bloqueo TLS)

**Síntoma**: `SSL_ERROR_SYSCALL` / `UNEXPECTED_EOF_WHILE_READING` al enviar
el request — fallan curl, wget, python-requests y hasta `curl.exe` de Windows
(HTTP 000). Pero `openssl s_client -brief` completa el handshake (no envía
request). El diagnóstico "handshake OK sin request / corte con request" =
fingerprint de cliente, NO problema de red.

**Bypass** (headers COMPLETOS de Chrome + HTTP/2 → 200):

```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none", "Upgrade-Insecure-Requests": "1",
}
requests.Session().headers.update(HEADERS)
```

**Rate limit**: ~2-3 requests seguidas OK, luego bloqueo (~25 s de
recuperación). Descarga masiva:
- delay inicial 1.2-2.5 s + reintentos con backoff [5, 15, 45, 90] s
- auto-regulación: ≥3 errores transitorios en ventana de 20 requests →
  delay ×1.5 (hasta 15 s); 0 bloqueos → bajar hacia 1.2 s
- HTTP 429/5xx reintentan; 403 = challenge puntual
- checkpoint.json reanudable por fecha + verificación pymupdf post-descarga

## Paso 2 — Decodificar el stream de React Router v7

El HTML no trae links; los datos viajan en `streamController.enqueue("...")`:

```python
import json, re
m = re.search(r'streamController\.enqueue\("(.*?)"\)', html, re.S)
s = json.loads('"' + m.group(1) + '"')   # capa 1: string JSON escapado
data = json.loads(s)                     # capa 2: array plano [k1,v1,k2,v2,...]
for i, v in enumerate(data):
    if v == "urlPDF" and i + 1 < len(data):
        url_pdf = data[i + 1]   # /api/archivo/file/<TOKEN>/*/PC<fecha>_<N>.pdf
```

- Campos inline útiles: `urlPDF`, `paginas`, `fechaPublicacion`,
  `tipoPublicacion`, `numeroNormas` (key → elemento siguiente).
- Objetos complejos usan referencias `{"_N": idx}` (single-fetch) — no hace
  falta resolverlas para campos simples.
- El TOKEN del PDF es estable (server-side); descargar directo con los
  mismos headers. Nombre de archivo: 2021 `PC20210730.pdf` vs 2026
  `PC20260729_4381.pdf`; a veces extensión `.PDF` (normalizar a .pdf).

## Paso 3 — Parser multi-formato de casos (los PDFs mezclan 3 formatos)

| Formato | Cabecera | Años |
|---|---|---|
| PJ Corte Suprema | `PROCESO DE AMPARO N° 25738-2024` o `AMPARO N° 32405-2024` (prefijo opcional) | 2024-2026 |
| PJ Cortes Superiores | `PROCESO DE HÁBEAS CORPUS` + `EXPEDIENTE : 01676-2021-0-1401-JR-PE-03` (también "Expediente :") | 2022+ |
| TC | `PROCESO DE AMPARO` + `EXP. N.° 01739-2018-PA/TC` (o `Expediente 0019-2015-PI/TC` sin N°) | 2021-2023+ |

Sufijos TC: PA/TC=amparo, PHC/TC y HC/TC=hábeas corpus, PC/TC=cumplimiento,
PHD/TC=hábeas data, PI/TC=inconstitucionalidad, CC/TC y PCC/TC=competencia,
AA/TC=acción popular.

### Cabecera real vs cita interna (regla de oro)

Un match de cabecera es un caso real si la **línea anterior** es el bloque
de órgano en MAYÚSCULAS (`PERMANENTE`, `SALA...`, `CORTE...`,
`PODER JUDICIAL`, `TRIBUNAL CONSTITUCIONAL`, `PLENO JURISDICCIONAL`) o
`Pleno/Sala X. Sentencia NNN/AAAA`. Reglas: ≥8 chars, no empezar con "(",
sin puntuación final. Las citas internas van precedidas por minúsculas o
números de página (`(STC expediente 3179-2004-AA/TC` = cita;
`Casación N° 2693-2023` en medio del texto = cita). Los casos NO empiezan
necesariamente en página nueva.

### Distrito judicial: validar contra lista oficial (~35 distritos)

Nunca aceptar "primera línea en mayúsculas" sin validar — captura nombres
de demandantes ("ALEXANDER MARTÍN KOURI"). Normalizar ñ→n y comparar contra
la lista (AMAZONAS...VENTANILLA + CORONEL PORTILLO, SELVA CENTRAL, HUAURA,
HUARAZ, LIMA NORESTE). Orden de fallbacks: (1) inline tras el EXP
(`...PHC/TC LIMA`), (2) línea siguiente, (3) mención en cuerpo[:500]
(`– Huaura, en audiencia`). Digitalización 2021 inyecta espacios:
`J UNÍN`→JUNIN, `P IURA`→PIURA, `LI MA`→LIMA (matchear sin espacios);
`LIBERTAD`→LA LIBERTAD; `AMAZONA`→AMAZONAS; alias `DEL SANTA`→SANTA,
`CHANCHAMAYO`→SELVA CENTRAL. Límite real: palabra partida en 2 líneas
(`LI\nMA`) no es rescatable.

### Fecha de sentencia → ISO

- En letras: `siete de abril de dos mil veintiséis` → 2026-04-07; tolerar
  `del año` (`siete de octubre del año dos mil veintiuno`).
- Numérica: `30 de noviembre de 2022`, `a los 19 días del mes de octubre de 2022`.
- Años en letras `dos mil X` → 2000+X; backtracking de tokens para cortar
  palabras extra (`dos mil veinticuatro lima` → 2024). Meses: setiembre Y
  septiembre. Días 1-31 en letras (incl. `treinta y uno`).

## Paso 4 — Render HTML legible de casos (JSON → HTML)

Tras extraer los casos a JSON, presentarlos como HTML legible:

```python
# caso.json = {"fecha_publicacion","edicion","tipo","numero","sentencia",
#              "distrito","corte","fecha_resolucion","fecha_resolucion_iso",
#              "demandante","texto"}  # texto = multilinea con \n
```

Formato que funcionó (verificado en navegador):
- Cabecera con gradiente violeta: tipo + expediente como `<h1>`
- Grid de tarjetas de metadatos: expediente, sentencia, tipo, distrito,
  publicación, edición, corte, demandante, fecha resolución (filtrar null)
- Cuerpo: texto → `<p>` justificados + títulos de sección como `<h3>`
- Fuente base 13px (preferencia del usuario; nunca <12px)
- Escapar HTML (`html.escape`) y salida a subcarpeta `html/`

### Pitfall: detección de títulos de sección (2 errores corregidos)

1. **Detectar ANTES de unir líneas en párrafos.** Si se unen las líneas
   primero, los títulos (`ASUNTO`, `ANTECEDENTES`, `FUNDAMENTOS`,
   `HA RESUELTO`) quedan pegados al texto del párrafo siguiente. Detectar
   el título a nivel de línea, hacer flush del párrafo acumulado, emitir
   el `<h3>`, y seguir.
2. **NO usar heurística "línea en MAYÚSCULAS corta"** — marca falsos
   positivos: nombres de magistrados (`MIRANDA CANALES`, `SARDÓN DE
   TABOADA`), firmas (`SS.`), códigos de imprenta (`W-1972663-34`).
   Usar lista de títulos exactos (case-insensitive: asunto, antecedentes,
   fundamentos, ha resuelto, voto singular del magistrado, razón de
   relatoría, delimitación del petitorio...) + prefijos conocidos
   (`proceso de `, `exp. `, `voto `, `los magistrados`, `el tribunal`).
   Los nombres/firmas quedan como texto normal.

Script listo: `scripts/generar_html_casos.py` (genera HTML de todos los
JSON de una carpeta; editar `ARCHIVOS`/`BASE` al inicio).

## Pitfalls de implementación

1. **rf-string + cuantificador regex**: `rf"...{0,4}..."` convierte `{0,4}`
   en placeholder de formato → el cuantificador desaparece en silencio.
   Usar `{{0,4}}` en rf-strings.
2. **Año en letras glotón**: `([a-zñ]+(?:\s+[a-zñ]+){0,4})` captura la "i"
   de "I. VISTA" (`dos mil veintiseis\ni`) → tokens de ≥2 chars.
3. **NTFS/WSL + glob**: `glob("*.pdf")` es case-sensitive aunque NTFS no
   distinga mayúsculas → `PC20231222.PDF` NO matchea. Usar `*.[pP][dD][fF]`.
4. **IDs de archivo**: sanitizar `/` del expediente (`PHC/TC`→`PHC_TC`);
   id = `{fecha}_{expediente}_{tipo}`.
5. **Conteo vs unicidad**: la extracción puede contar el mismo id 2 veces
   (2 anclas); la metadata maestra es la fuente de verdad — verificar
   metadata↔archivos con sets (deben dar 0/0).
6. **Verificar tras fixes del parser**: re-procesar solo los PDFs de casos
   afectados (script de reparación dirigida) y actualizar JSONs + metadata;
   no re-correr todo el corpus si el fix es puntual.

## Archivos de soporte

- `references/elperuano-cuadernillo-pc.md` — detalle de sesión: resultados
  reales (842 PDFs, 14,564 casos), inventario de scripts reutilizables,
  cronología de fixes (298 distritos corregidos, 78 OTRO reclasificados).
- `scripts/generar_html_casos.py` — genera HTML legible de los JSON de
  casos (Paso 4): cabecera + tarjetas de metadatos + texto en párrafos con
  títulos de sección. Uso: `python3 generar_html_casos.py [carpeta]`.

## Nota de solapamiento

El umbrella `peruvian-judicial-scraping` (user-owned, no editable aquí)
cubre CEJ/PJ, SEDETC/TC e Indecopi; este skill cubre El Peruano. Si se
adopta aquel (`hermes curator adopt peruvian-judicial-scraping`), conviene
mover esta referencia bajo él como patrón adicional.
