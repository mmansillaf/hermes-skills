# TC / El Peruano — caso de estudio (Jul-Ago 2026)

Sesión real: 8,794 sentencias del Tribunal Constitucional peruano publicadas en
El Peruano (2016-2021), convertidas de JSON a un archivo HTML navegable + buscador
full-text offline. Resultado en `D:\PyCode\ProcesosConstitucionales\html_casos_v2\`.

## Corpus (origen: D:\PyCode\ProcesosConstitucionales\data\casos_2016_2021\)
- 855 fechas (carpetas YYYY-MM-DD), 8,794 archivos JSON (uno por caso).
- Texto total 156.8 MB (promedio 17,830 chars/caso, máx 316,345).
- Tipos: Cumplimiento 3,291 · Amparo 3,165 · Habeas Corpus 1,453 · Habeas Data 635 · Accion Popular 250.
- JSON: campos planos `{fecha_publicacion, edicion, tipo, numero, sentencia, distrito,
  corte, fecha_resolucion, demandante, texto}` — `texto` con saltos de línea `\n` dentro del string.

## Producto final (html_casos_v2)
| Archivo | Tamaño | Contenido |
|---|---|---|
| index.html | 12.6 KB | UI buscador v2 (vanilla JS) |
| datos.js | 5.4 MB | `window.CASOS`: 13 campos/caso + resumen |
| indice.js | 15.3 MB | `window.INDICE`: 99,903 términos, 7.95M postings, delta-encoded |
| casos/ | 8,794 HTML | uno por sentencia, en carpetas por fecha |
| generar_v2.py | | generador reutilizable (en la misma carpeta) |

v1 (primera iteración) tenía indice.js sin comprimir a 25.7 MB; delta-encoding lo
bajó a 15.3 MB. El usuario confirmó que "se ve muy bien" — la legibilidad del JSON
estructurado es lo que hace posible todo esto.

## Extracción semántica (campos derivados del texto)
- **fallo**: regex cerca de "declar..." → FUNDADA (2,085) / INFUNDADA (1,619) / IMPROCEDENTE (5,038).
- **derechos** (12 categorías): diccionario keyword→categoría (pensión, salud, acceso a
  información, debido proceso, educación, propiedad, trabajo, libertad de expresión,
  igualdad, vida e integridad, libertad personal, debido procedimiento admin.). Máx 3 por caso.
- **ponentes**: `PONENTE <NAME>` o `VOTO DE LOS MAGISTRADOS <NAMES>`.
- **citas**: `STC 00296-2007-PA/TC` o `Expediente NNNNN-YYYY-ZZ/TC` (máx 12, ordenadas).
- **resumen**: primeras ~420 chars tras "ASUNTO" (o inicio del texto).
- **demandante completo**: `interpuesto por don/doña X` — el campo JSON suele venir
  truncado ("don Frank" en 1,838 de 2,800 casos con campo).

## Distritos sucios (hallazgo de calidad de datos)
El scraper original capturó etiquetas en vez del distrito: 959 casos con distrito
"DEMANDANTE", 299 "JUEZ", 98 "DEMANDADO", 3 "PROCEDENCIA"; 3,521 vacíos.
Recuperación en 3 pasadas:
1. `CORTE SUPERIOR DE JUSTICIA DE <X>` en el texto (recuperó ~1,357 "AYACUCHO").
2. Fallback: `<Ciudad>, <día> de <mes>` en la línea de fecha ("Ayacucho, 13 de abril...").
3. `.upper()` para agrupar "Ayacucho" y "AYACUCHO".
Lección: reportar los conteos sucios al usuario — es un hallazgo del pipeline, no un bug de UI.

## Bugs encontrados y corregidos (transcripciones)
1. **Buscador v1 "no funciona"**: links del índice solo tenían `data-t` (tipo) y
   `data-n` (número); distrito y demandante no estaban indexados → "LIMA" daba 0
   resultados. Fix: 4 data attributes + buscarlos todos.
2. **Stopwords asimétricas**: Python filtraba "del" al construir el índice; JS no al
   consultar → `"abuso del derecho"` hacía AND con set vacío → 0 resultados.
3. **Frase exacta**: al extraer `"..."` del query quedaban 0 tokens para el AND.
   Fix: los tokens de la frase se SUMAN al AND; el match exacto es solo boost de ranking
   (el snippet es corto; la frase puede no aparecer en él aunque el doc matchee).
4. **Sinónimos como AND extra**: sinónimo de "pension" incluía "onp"; `pension NOT onp`
   → "pension AND onp AND NOT onp" → vacío. Fix: sinónimos se unen al MISMO conjunto
   del término (unión OR), no como conjunción adicional.
5. **Regex greedy de campos**: `(fallo|...):([a-z0-9\s\-\.]+)` se comía
   `fallo:fundada derecho:pension` entero como valor de fallo. Fix:
   `[^\s:]+(?:\s+(?!\w+:)[...]+)*` — un campo termina cuando aparece otro `palabra:`.
6. **Campo enum con includes**: `fallo:fundada` matcheaba "INFUNDADA" (substring).
   Fix: comparación de igualdad exacta.
7. **Pills de año rotas**: se agrupaba con `c[2]` (distrito) en vez de `c[5]` (fecha) →
   aparecían "ABEL", "AREQ"... Fix: índice correcto de array.
8. **Links de citas**: apuntaban a `?q=...` en la misma página del caso; deben ser
   `../index.html?q=...` Y el index debe leer `new URLSearchParams(location.search)`
   al iniciar, o el clic no hace nada.
9. **CSS.escape()**: al re-seleccionar pills con keys con espacios vía querySelector
   con selector CSS dinámico, falla sin escape.

## Datos de rendimiento (WSL + NTFS)
- Escritura directa a /mnt/d (drvfs): ~17-64 archivos/s → 8,794 HTML = ~9 min.
- Stage en /tmp (ext4): generación completa en segundos; `cp -r` a /mnt/d = 42 s.
- Regla: SIEMPRE escribir a /tmp y copiar en lote.
- Búsqueda en navegador: carga ~2-4 s (parsing de 20 MB JS), luego instantánea.

## UI features verificadas (v2)
Frase exacta `"..."` · OR/NOT · campos numero:/tipo:/distrito:/año:/sentencia:/fallo:/
derecho:/ponente: · autocompletado con conteos · sin tildes · stem (pension→pensiones) ·
sinónimos · rango fechas · orden (relevancia/fecha/expte) · paginación "Mostrar más" ·
tabs (nube de términos, distritos, gráfico por año, favoritos localStorage) ·
export CSV/JSON (BOM UTF-8 para Excel) · dark mode persistente · caso individual con
TOC lateral, breadcrumb, badges, fallos citados clickables, resaltado ?q=, notas
(subrayar selección → localStorage), @media print.
