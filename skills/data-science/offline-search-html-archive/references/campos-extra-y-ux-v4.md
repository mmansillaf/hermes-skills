# v4 — Campos extra del JSON + mejoras UX (html_casos_v4)

Sesión 2026-08-02. Base: v3 (fixes + co-ocurrencia). Carpeta nueva `html_casos_v4/`; v2/v3 intactas.
SDD (SPEC-v4.md, AC1-AC17) + TDD (tests/test_v4.py, 12 tests RED→GREEN) + verificación manual en navegador.

## Cobertura real medida (8,794 JSON)

| Campo extra | Cobertura | Ejemplo |
|-------------|-----------|---------|
| demandado (header) | 4,055 (46%) | "ONP" |
| materia (header) | 88% | "ACCION DE CUMPLIMIENTO" |
| juez (header) | 71% | "JUAN PEREZ" |
| leyes citadas | 6,081 (69%) | Ley 25212 → 1,253 casos |
| parte resolutiva | 6,869 (78%) | tramo HA RESUELTO |
| precedente vinculante | 2,848 (32%) | badge ★ |
| fecha_resolucion_iso | 3,711 (42%) | 2000-2021 |

## Estructura datos.js v4 (20 campos/caso)

[0..12] = como v2/v3 (num,tipo,dist,demandante,sentencia,fecha,edicion,stem,fallo,derechos,ponentes,citas,resumen)
[13] = demandado · [14] = materia · [15] = juez · [16] = resolutiva (texto, cap 800) · [17] = vinculante (0/1) · [18] = leyes [array] · [19] = fecha_resolucion_iso ("YYYY-MM-DD" o "")

Crecimiento: datos.js 5.3 → 10.0 MB (resolutiva es texto largo). indice.js 15.5 MB, cooc.js 0.5 MB.

## Prefijos de índice para normas

`ley:25212`, `ds:003-98-sa`, `art:56`, `vinculante`, `demandado:<norm(demandado)>` — se indexan como
postings normales; el parser de query ya soporta `campo:valor`, solo hay que añadir los nombres de campo
a la regex y mapearlos a los índices 13-19 (arrays: idx 9 y 18 se join(' ') antes de comparar).

## Regex clave (v4)

```python
PAT_HEADER = {'demandado': re.compile(r'\bDEMANDADO\s*:?\s*([^\n|]{2,80})', re.I), ...}
# OJO: extraer_header usa (texto or '')[:500] — el cuerpo contamina (pitfall confirmado)
PAT_LEY = re.compile(r'\b(?:LEY|L\.)\s*(?:N[°º]\s*)?(\d{3,5})', re.I)   # N° opcional: "Ley 26790"
PAT_DS  = re.compile(r'\bD\.?S\.?\s*(?:N[°º]\s*)?(\d{2,3}-\d{2}-[A-Za-z]{1,4})', re.I)  # conserva "SA"
PAT_ART = re.compile(r'\bart[ií]culo\s+(\d{1,3}[a-z]?)', re.I)
PAT_RESOLUTIVA = re.compile(r'\b(?:HA RESUELTO|RESUELVE)\s*:?\s*(.*?)(?:\bPubl[ií]quese|\bSS\.|\bS\.\s|\Z)', re.I | re.S)
PAT_VINC = re.compile(r'precedente vinculante|car[aá]cter vinculante', re.I)
```

## Gráfico: publicación vs resolución (por qué "solo 2016-2021")

El corpus son publicaciones de El Peruano → años de publicación acotados a 2016-2021.
PERO la fecha de resolución (campo del JSON, 42% cobertura) va de 2000 a 2021:
- publicación: {2016:1181, 2017:2259, 2018:1935, 2019:2510, 2020:251, 2021:658}
- resolución: {2000:2, 2004:1, 2013:3, 2014:86, 2015:458, 2016:594, 2017:949, 2018:922, 2019:327, 2020:248, 2021:121}
Fix UX: `<select>` toggle en el gráfico + nota de cobertura ("solo 42% tiene fecha de resolución").
Lección general: si el usuario dice "el gráfico solo muestra X años", primero mide si es un hecho del corpus
(publicación) antes de asumir bug; la segunda fecha del JSON suele ampliar el rango.

## UX v4 (patrones reutilizables)

- **Paginación numérica**: `◀ 1 2 3 … N ▶` (ventana ±2 alrededor del actual, elipsis en huecos).
  `pintarPag(total, desde, hasta)` construye botones; clic → `pagina = p; pintarResultados(); scrollTo(top)`.
  Mantener "Mostrar más" como complemento.
- **Badge de filtro de fechas**: junto a los inputs date, `<span class="badge-rango">📅 desde → hasta ✕</span>`
  visible solo con filtro activo; el ✕ limpia ambos inputs y re-busca. Sin esto el usuario "no nota cambios"
  aunque el filtro funcione.
- **Fuente A−/A+**: `document.body.style.fontSize` (base 13px, clamp 11-18), localStorage `tc-fuente`, aplicar al init.
- **Badge vinculante**: `★ Precedente vinculante` (ámbar #f59e0b) en tarjetas y cabecera del caso.

## Tests TDD (12)

AC1-AC5 extraer_normas/extraer_header/extraer_resolutiva/extraer_vinculante (unit) ·
AC6 generar_caso incluye bloque resolutiva · AC7 datos.js real 8,794×20 campos ·
AC8 regresión co-ocurrencia v3. Nota: tests importan generar_v4.py como módulo → el guard
`if __name__ == "__main__"` es obligatorio (pitfall de importación, ver SKILL.md).

## Incidentes de la sesión

1. rsync --delete del generador borró index.html/generar_v4.py/SPEC/tests de v3 (STAGE no es espejo de OUT).
   Fix: rsync SIN --delete + reconstrucción de archivos de proyecto. (Ya documentado en v3; se repitió la
   reconstrucción en v4 — confirmado como patrón a evitar.)
2. extraer_header sin límite de 500 chars → demandado = "INDEBIDAMENTE A LA ONP, SE DECLARE NULO TODO..."
   (captura del cuerpo). Fix: `texto[:500]`. Verificado 0 sucios tras regenerar.
3. PAT_LEY inicial exigía "N°" → "Ley 26790" no matcheaba. PAT_DS inicial cortaba "003-98-SA" → "003-98-".
   Ambos corregidos con N° opcional y letras finales en el patrón.
