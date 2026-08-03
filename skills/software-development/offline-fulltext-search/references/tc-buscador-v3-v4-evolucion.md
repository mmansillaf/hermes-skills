# TC buscador: evolución v3 → v4 (workshop real, Ago 2026)

Proyecto: html_casos_v3 / html_casos_v4 en D:\PyCode\ProcesosConstitucionales.
Base: 8,794 sentencias TC (El Peruano 2016-2021) en JSON. Buscador 100% offline
doble-clic file://. Skill madre: offline-fulltext-search.

## v3 — fixes de bugs + semántica opción A (co-ocurrencia offline)

### 3 bugs confirmados y corregidos (cada uno con causa raíz)
1. **Ordenamiento no funcionaba**: listener de `#orden` llamaba `pintarResultados()`
   pero el sort solo se calcula dentro de `buscar()`. Fix: listener → `buscar()`.
2. **Calendario sin feedback**: `input type=date` solo dispara 'change' al cerrar el
   picker; teclear no hace nada. Fix: escuchar 'input' + 'change' con debounce 300ms
   (v4 añade badge visual del rango activo).
3. **"_s-n" en 936 casos**: el JSON fuente tiene `numero: None` (scraper no capturó
   el número; el archivo se llama 039_Cumplimiento_s-n.json). El generador usaba el
   stem del archivo como fallback → mostraba "039_Cumplimiento_s-n". Fix:
   `extraer_numero(texto, campo)` recupera el expediente del texto con regex
   (`EXP. N° 03718-2015-PC/TC`, normalizando saltos de línea `PC/\nTC` → `PC/TC`);
   fallback limpio "s/n". Resultado: 0 casos _s-n; 271 recuperados del texto.

### Semántica opción A — co-ocurrencia offline (sin embeddings, sin servidor)
- Precomputar en Python: para cada término indexado, los top-12 términos que
  co-ocurren en los mismos fallos. Emitir `cooc.js` → `window.COOC = {t: [[rel, score]]}`.
- **Score**: `co * (1 + max(0, log(N*co/(dfa*dfb))))` — frecuencia como señal
  principal, PMI como ajuste (0 si co-ocurrencia aleatoria).
- **Simetría**: escribir cada par en AMBAS direcciones (a→b y b→a), o los tests
  fallan al consultar por cualquiera de los dos términos.
- **Filtro de boilerplate legal** (`STOP_LEGAL`): fojas, recurso, demanda, amparo,
  expediente, agravio, interpuesto... sin esto, "pension" → [amparo, fecha, fojas,
  contra, recurso] (inútil). Con el filtro → [salud, normalizacion, cina, previsional, onp].
- Filtro de frecuencia: quitar términos con df≤2 (ruido) y df>60% de los docs (genéricos).
- UI: chips "✨ Términos relacionados: + salud + onp..." bajo el buscador; clic
  expande la query con OR y re-busca.
- Tamaño real: cooc.js 0.5 MB para 8,794 casos. 100% offline.

## v4 — explotación del JSON + UX

### Campos nuevos en datos.js (20 por caso; el array plano crece a ~10 MB)
Índices: [13]=demandado, [14]=materia, [15]=juez, [16]=resolutiva, [17]=vinculante
(0/1), [18]=leyes[], [19]=fecha_resolucion_iso.

### Extracciones (todas regex en el generador, con tests RED-first)
- `extraer_header(texto)`: DEMANDADO/MATERIA/JUEZ del header. **Buscar SOLO en
  texto[:500]** (el cuerpo contamina: "demandado: JUEZ DEL JUZGADO... INDEBIDAMENTE
  A LA ONP").
- `extraer_normas(texto)`: leyes (`Ley N° 25212`, con N° opcional), D.S.
  (`\d{2,3}-\d{2}-[A-Za-z]{1,4}` — "003-98-SA"), artículos. Indexar con prefijos:
  `ley:25212`, `ds:003-98-sa`, `art:56` → búsqueda `ley:25212` da 1,253 resultados.
- `extraer_resolutiva(texto)`: tramo HA RESUELTO/RESUELVE hasta Publíquese/firmas
  (regex lazy con `re.S`); se muestra como bloque destacado arriba del caso.
- `extraer_vinculante(texto)`: "precedente vinculante"|"carácter vinculante" →
  badge ★ + filtro `vinculante:1`.

### UX añadida (verificada en navegador, no solo en código)
- **Paginación numérica** 1 2 3 … N + ◀▶ (además del "Mostrar más" incremental).
  Pintar páginas: 1, N, act±2, con "…" en medio.
- **Gráfico multi-año**: toggle "Por publicación" (2016-2021, el dataset solo tiene
  publicaciones de esos años) | "Por resolución" (2000-2021, solo 42% de casos tiene
  fecha_resolucion_iso — mostrar la nota de cobertura).
- **Tamaño de fuente A−/A+**: ajusta body font-size (11-18px, base 13), persistido
  en localStorage. El usuario lo pidió explícitamente.
- **Badge de rango de fechas**: "📅 2021-01-01 → hoy ✕" junto a los inputs; el ✕
  limpia el filtro. Sin esto, el usuario "no nota" que el calendario funciona.

## Lección de proceso: rsync SIN --delete (incidente con pérdida)
El generador sincronizaba `/tmp/stage/` → `OUT/` con `rsync -a --delete`. STAGE solo
tiene artefactos generados; OUT también tiene index.html, generar_v4.py, SPEC, tests.
`--delete` borró esos archivos de proyecto. Recuperación: reconstruir todo desde v2 +
re-aplicar patches. Fix: `rsync -a` a secas. Documentado en la skill.

## TDD en este proyecto (cómo se hizo de verdad)
- SPEC-v4.md con criterios AC1-AC17 (aceptación medible).
- tests/test_v4.py + tests/test_distritos.py: RED primero (módulo inexistente o
  regex que falla) → GREEN. Suite total 21 tests.
- **Guard de importabilidad**: `if __name__ == "__main__":` alrededor del loop
  principal — sin esto, importar el módulo en tests ejecuta los 8,794 docs (cuelga).
- Test que atrapó el bug del HTML: verificar la card de distrito EN DISCO de un caso
  real (no solo datos.js). Sin ese test, el HTML mostraba el campo crudo.

## Verificación humana (regla de entrega)
- browser_navigate file:// + browser_console para: paginación (clic pág. 2 →
  "mostrando 101–150"), toggle gráfico (barras cambian), badge de rango aparece,
  A+/A− cambia font-size y persiste, `ley:25212` → 1,253, `demandado:onp` → chips
  limpios, badge ★ vinculante visible, card distrito = AYACUCHO en HTML real.
