# Buscador full-text en archivos locales (file://) — índice invertido JS

Patrón validado 2026-08-01 sobre el corpus TC 2016-2021 (8.794 casos,
156.8 MB de texto) en `D:\PyCode\ProcesosConstitucionales\html_casos\`.
Extiende el índice básico de `casos-json-a-html.md` con búsqueda sobre el
TEXTO COMPLETO de las sentencias.

## Por qué el buscador básico "no funciona" (bug real reportado por el usuario)

El índice inicial solo ponía `data-t` (tipo) y `data-n` (número) en cada
`<li>`. El placeholder prometía "expediente, tipo, distrito o demandante"
pero distrito/demandante NO estaban indexados:

- Buscar `LIMA` (distrito) → 0 resultados.
- Buscar `Vela Albornoz` (demandante completo) → 0 resultados.

Causa doble: (a) el campo `demandante` del JSON está TRUNCADO en el 66% de
los casos ("don Frank", "doña Esther" — 1.838 de 2.800 con campo), el
nombre completo solo vive dentro de `texto`; (b) el texto no estaba
indexado. Además la búsqueda era de frase exacta sin normalizar acentos
(`habeas` no encontraba `hábeas`) y sin filtrar stopwords (la intersección
AND con un token vacío daba 0).

## Arquitectura del buscador full-text (validada)

```
index.html  → UI + JS de búsqueda
datos.js    → window.CASOS  = [ [num, tipo, distrito, demandante, sentencia,
                                fecha, edicion, stem, snippet_1000], ... ]   (~10 MB)
indice.js   → window.INDICE = { token_normalizado: [docIdx, ...], ... }      (~26 MB)
casos/<fecha>/<stem>.html → un HTML por caso (intactos, link desde resultados)
```

- 76.723 términos únicos, 4.19M postings. Tamaño medido: datos.js 10.2 MB,
  indice.js 25.7 MB para 8.794 docs con 12.000 chars de texto indexados por
  caso (límite `tokenize(texto, limite=12000)` para controlar peso).
- Carga inicial ~2-4 s en disco local; búsqueda luego instantánea.
- Metadatos indexados ×3 (peso extra) + texto ×1: los matches en número/
  tipo/distrito/demandante rankean arriba.

## PITFALL CRÍTICO 1 — file:// no permite fetch(), sí <script src>

Con `file://` (doble clic en Windows), `fetch('indice.js')` FALLA por CORS.
Los `<script src>` locales SÍ funcionan. Por eso los datos se exponen como
variables globales:

```html
<script src="datos.js"></script>
<script src="indice.js"></script>
<script>
const CASOS = window.CASOS || [];
const INDICE = window.INDICE || {};
</script>
```

## PITFALL CRÍTICO 2 — stopwords y normalización DEBEN ser idénticas en Python y JS

El índice se construye en Python (tokenize con STOP set); la query se
tokeniza en JS. Si el set de stopwords difiere, la intersección AND
revienta silenciosamente: "abuso del derecho" → tokens JS
`["abuso","del","derecho"]`; `del` no existe en INDICE (filtrado en
Python) → `sets` incluye `[]` → intersección vacía → 0 resultados.

Regla: la MISMA lista STOP y la MISMA normalización en ambos lados.

```python
# Python (build)
def norm(s):
    s = unicodedata.normalize('NFD', s or '')
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower()
def tokenize(s, limite=None):
    t = norm(s)[:limite] if limite else norm(s)
    return [w for w in re.findall(r'[a-z0-9]{3,}', t) if w not in STOP]
```

```javascript
// JS (query) — STOP = misma lista, copiada textualmente
const STOP = new Set('de la el los las y o u a al del ...'.split(' '));
function norm(s){ return (s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,''); }
function tokens(q){ return (norm(q).match(/[a-z0-9]{3,}/g) || []).filter(t => !STOP.has(t)); }
```

Tokens: `[a-z0-9]{3,}` (min 3 chars), stopwords fuera, tildes fuera (NFD).

## PITFALL CRÍTICO 3 — demandante truncado → extraer del texto con regex

El campo JSON `demandante` viene truncado ("don Frank"). El nombre completo
está en el texto. Extraer con patrones antes de indexar:

```python
PAT_DEM = [
    re.compile(r'interpuesto por (don|doña|d\.|dña\.?)\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü\.\'\-]+(?:\s+[A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü\.\'\-]+){1,6})', re.I),
    re.compile(r'demandante (don|doña|d\.|dña\.?)\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü\.\'\-]+(?:\s+[A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü\.\'\-]+){1,6})', re.I),
]
def extraer_demandante(texto, campo):
    if campo and len(campo.strip()) >= 25:   # campo ya completo
        return campo.strip()
    for rx in PAT_DEM:
        m = rx.search(texto)
        if m and len(m.group(2)) >= 8:
            return f"{m.group(1).capitalize()} {m.group(2).strip()}"
    return (campo or "").strip()
```

## Intersección AND + ranking + snippet (JS)

```javascript
const noEncontrados = toks.filter(tok => !(INDICE[tok] && INDICE[tok].length));
const sets = toks.map(tok => INDICE[tok] || []);
let inter = null;
sets.forEach(s => { const set = new Set(s);
  inter = inter === null ? set : new Set([...inter].filter(x => set.has(x))); });
let docs = inter === null ? [] : [...inter];
// ranking por frecuencia de tokens
const freq = new Map();
docs.forEach(d => { let f=0; sets.forEach(s => { if (s.includes(d)) f++; }); freq.set(d,f); });
docs.sort((a,b) => (freq.get(b)-freq.get(a)) || CASOS[a][0].localeCompare(CASOS[b][0]));
```

- Snippet: `snippetAlrededor(idx, toks)` busca el primer match dentro de los
  1.000 chars guardados y recorta ±130 chars alrededor, con `<mark>` en los
  términos (highlight amarillo). Si el match cae más allá del snippet, se
  muestra el inicio igual — el link abre el HTML completo.
- MAX 60 resultados + aviso "… y N resultados más. Afina la búsqueda".
- Términos no encontrados → aviso explícito ("Los términos «X» no aparecen
  en ningún fallo") en vez de vacío mudo.
- Filtros combinables: pills por tipo (5) + pills por año (2016-2021) +
  texto; se aplican post-intersección con `CASOS[d][1]===tipoAct` y
  `CASOS[d][5].slice(0,4)===anioAct`.

## Bugs de índice detectados y corregidos (lección: verificar con JS real)

- Pills de año generadas con `c[2]` (distrito) en vez de `c[5]` (fecha):
  mostraban "ABEL", "AREQ", "LIMA" truncados. Los índices de array de
  CASOS deben verificarse contra el orden real del generador.
- Link de caso construido con el campo equivocado: usar el `stem` del JSON
  (`030_Amparo_01379-2021-PA-TC`), no recomponer el nombre desde campos.
  Guardar `stem` explícitamente en CASOS[7].

## Generación y rendimiento

- `generar_fulltext.py`: lee los 8.794 JSON desde NTFS (~2.5 min, el cuello
  ahora es la LECTURA no la escritura), genera datos.js + indice.js en
  `/tmp/html_ft_stage/` y `cp` al destino (mismo patrón de staging que el
  corpus HTML).
- El índice invertido reduce 156.8 MB de texto → ~36 MB de JS (datos+índice)
  porque: solo 12K chars/caso, stopwords fuera, tokens únicos por doc.
- Estimación rápida del tamaño del índice ANTES de generar (script de una
  línea con Counter + sys.getsizeof) evita sorpresas de peso.

## Verificación — probar como persona (directiva explícita del usuario)

El usuario reportó "el buscador no funciona" y ordenó: "revisa el buscador,
has pruebas como si fueras persona". El set de pruebas que de verdad
detecta regresiones:

1. `LIMA` (distrito) → debe dar ~1.259 resultados, no 0.
2. `Vela Albornoz` (demandante completo, antes truncado) → 7 resultados.
3. `habeas corpus` sin tilde → 1.746 (normalización de acentos).
4. `abuso del derecho` (con stopword "del") → 147, no 0 (sync de stopwords).
5. `pensión` + pill "Amparo" → 1.596 (filtro combinado).
6. Clic en un resultado → abre el HTML correcto (verificar href).
7. `xqzz` (término inexistente) → aviso explícito, no vacío mudo.

Verificar con `browser_console` contando `.resultado` visibles y leyendo
`.info` (contiene "N resultados para «query»").
