---
name: office-js-addins
description: "Office.js add-ins: manifest, UMD modules, TDD, sideload."
---

# Office.js Add-ins (Word/Excel Task Pane)

Clase: construir add-ins de Office 365 con Office.js que integran datos locales
(buscadores, RAG, citas) dentro de Word/Excel. Arquitectura probada: task pane
que carga un motor de búsqueda offline portado a módulos UMD, con TDD en Node
puro y verificación en navegador en "modo demo" antes de probar en Office real.

## Cuándo usar
- El usuario quiere insertar contenido (citas, jurisprudencia, resultados de
  búsqueda) directamente en Word desde un panel lateral
- Tienes un buscador/índice offline (p. ej. generado con el skill
  json-to-offline-fulltext-search) y quieres reutilizarlo dentro de Office
- Requisito típico: 100% offline, datos locales, sin backend

## Arquitectura de referencia (proyecto word-addin TC, Ago 2026)

```
word-addin/
├── manifest.xml            # manifiesto Office add-in
├── package.json            # npm test / build
├── index.html              # task pane (híbrido: denso + drawer de detalle)
├── js/office-utils.js      # Office.onReady, setSelectedDataAsync, getSelectedDataAsync
├── js/query-parser.js      # lógica pura portada (UMD)
├── js/search-engine.js     # motor portado (UMD)
├── js/format-cita.js       # formateo de citas (UMD)
├── js/ui-panel.js          # render, tabs, drawer, A−/A+, tema
├── assets/                 # datos.js + indice.js + cooc.js + similares.js
├── tests/                  # tests Node puros (node --test)
└── dist/                   # salida de build (copia todo + assets)
```

## Pasos (SDD+TDD)

1. **Fase 0 — Mockup visual primero** (preferencia del usuario): 3 variantes
   HTML interactivas, el usuario elige. Ej: denso (tool-first, badges, 2 clics)
   vs split (lista + detalle a la derecha) vs sobrio. Híbrido 2+3 = denso con
   detalle en drawer. Ver DECISION-DISENO.md.
2. **Fase 1 — SPEC**: RF con sintaxis de búsqueda EXACTA (misma del buscador
   offline), formato de cita exacto, estructura de proyecto, criterios de
   aceptación.
3. **Fase 2 — TDD RED**: tests en Node puro (`node --test "tests/*.test.js"`).
   ⚠️ Node 24: el runner necesita el glob ENTRE COMILLAS; `node --test tests/`
   falla con MODULE_NOT_FOUND.
4. **Fase 3 — GREEN**: portar lógica pura a módulos UMD (ver patrón abajo).
5. **Fase 4 — Build**: copiar js/ + index.html + manifest + assets a dist/.
6. **Fase 4.3 — Verificación navegador en modo demo**: abrir dist/index.html
   con file:// — Office.js carga pero avisa "loaded outside of Office client"
   (warning, NO error). Todo debe funcionar excepto la inserción real, que
   muestra toast "modo demo". Probar: búsqueda, drawer, badges, tema, A−/A+.
7. **Fase 5 — Pruebas en Office real**: sideload del manifest (ver abajo),
   verificar botón en cinta, insertar cita, buscar selección, persistencia.

## Patrón UMD (lógica testeable en Node sin DOM)

```js
const modulo = (function () {
  function fn(){ /* lógica pura, sin DOM ni Office */ }
  return { fn };
})();
if (typeof module !== 'undefined' && module.exports) { module.exports = modulo; }
if (typeof window !== 'undefined') { window.Modulo = modulo; }
```

En search-engine: `createEngine(casos, indiceRaw, cooc, similares)` — la fábrica
recibe los datos por parámetro, así los tests cargan los datos reales con
`global.window = global; require('../html_casos_v4/datos.js')` y el motor se
prueba contra el corpus completo, no contra fixtures.

## manifest.xml — puntos críticos

- `<SourceLocation DefaultValue="..."/>` es SELF-CLOSING con el valor en el
  atributo, NO texto entre tags. Los tests que esperan
  `>...index.html...</SourceLocation>` fallan contra el formato real.
- Para sideload local: `https://localhost:3000/index.html` (Office exige
  https o localhost; file:// no vale). NUNCA dejar example.com (placeholder
  inservible que no carga).
- `<Permissions>ReadWriteDocument</Permissions>` + `<Host Name="Document"/>`.
- `<Id>` debe ser UUID válido.
- office.js se carga desde CDN: `<script src="https://appsforoffice.microsoft.com/lib/1/hosted/office.js">`.

## office-utils.js — detección de disponibilidad

```js
function officeDisponible(){ return typeof Office !== 'undefined' && Office.context && Office.context.document; }
```
- `insertarTexto(texto)`: `Office.context.document.setSelectedDataAsync(texto, {coercionType: Office.CoercionType.Text}, cb)`.
- `obtenerSeleccion()`: `getSelectedDataAsync(Office.CoercionType.Text, cb)` — para "buscar selección".
- Sin Office: en modo demo copiar a clipboard si existe y lanzar error controlado
  → el UI muestra toast "modo demo" en el catch. La promesa async NO se resuelve
  en el mismo tick del click: al verificar el toast en consola, esperar ~500ms.

## Pitfalls (aprendidos en sesión real)

1. **Verificar el motor contra datos REALES antes de confiar en tests**:
   una instancia paralela pasó 25 tests con un fixture de 2 casos inventados,
   pero su motor daba **0 resultados** con los 8,794 reales (mapeaba sumilla a
   c[3] que en datos reales es demandante vacío; el texto vive en c[12]).
   Siempre correr `buscar("pension")` contra el corpus real y exigir >0.
2. **El índice se genera del texto COMPLETO pero datos.js guarda c[12]
   truncado** (a veces solo el encabezado, ~386 chars): un caso puede matchear
   por el índice y su texto visible no contener el término. Los tests de
   "relevancia" deben verificar índices válidos + total > 0 + sinónimos, NO
   exigir el término en el texto visible del primer resultado.
3. **Regex de campos con ñ**: `(?!\w+:)` no protege `año:` porque `\w` no
   incluye ñ → `distrito:lima año:2021` traga "año" como valor de distrito.
   Usar `(?!\S+:)`.
4. **OR tras frase**: `"abuso del derecho" OR pension` — tras extraer la frase,
   el resto queda " OR pension" y el regex `A OR B` no matchea (no hay token
   antes de OR). Fix: detectar `(?:^|\s)OR\s+(\w+)` suelto y unirlo contra el
   primer token de la frase. (Mejora vs el v4.3 original que lo perdía.)
5. **Task pane real = 350px**: NO usar split permanente (queda ~175px/lado).
   El "detalle a la derecha" del mockup split se adapta como **drawer
   full-width** con slide + "← Volver a resultados".
6. **Carpeta compartida con otra ventana de Hermes**: el usuario corre varias
   ventanas en paralelo que pueden escribir el MISMO proyecto. Antes de
   escribir archivos, verificar actividad reciente:
   `find . -type f -mmin -5` (vacío = seguro). Si detectas colisión, parar
   escrituras y consolidar: leer todo, tomar lo bueno de cada versión, reemplazar
   lo roto. Documentar la colisión al usuario con timestamps.
7. **badges semánticos** por campo: FUNDADA verde, INFUNDADA rojo, ★Vinculante
   ámbar, voto singular morado — el color depende del valor, no del tipo.

## Verificación final
- `npm test` → todos verdes (contra datos reales)
- `npm run build` → dist/ con assets
- Navegador file:// dist/index.html: búsqueda con datos reales, drawer abre
  con parte resolutiva + similares, tema oscuro, A−/A+, 0 errores JS en consola
- En Word real: botón en cinta, insertar cita con formato exacto, buscar selección

## Referencias
- `references/corpus-tc-v43-estructura.md` — estructura de filas del corpus TC
  v4.3 (21 índices 0-20), mapa campo→idx, formato cooc.js/similares.js, errores
  de mapeo vistos en implementaciones paralelas, verificación rápida en Node.

