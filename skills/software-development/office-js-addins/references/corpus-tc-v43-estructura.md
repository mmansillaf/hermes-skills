# Corpus TC v4.3 — estructura de filas (8,794 casos, Ago 2026)

Fuente: `D:\PyCode\ProcesosConstitucionales\html_casos_v4\datos.js` (`window.CASOS`)
y `indice.js` (`window.INDICE`, delta-encoded). Portado al add-in Word en
`word-addin/` (sesión 2026-08-02).

## Filas: 21 elementos, índices 0-20

| idx | Campo | Tipo | Notas |
|-----|-------|------|-------|
| 0 | numero/expediente | string | ej. "01379-2021-PA/TC" |
| 1 | tipo | string | Amparo, Cumplimiento, Habeas Corpus... |
| 2 | distrito | string | MAYÚSCULAS, whitelist ~60 (fix v4.1) |
| 3 | demandante | string | A menudo vacío "" |
| 4 | sentencia | string | n.° de sentencia |
| 5 | fecha_publicacion | string | ISO "YYYY-MM-DD" |
| 6 | (edicion?) | string | ej. "2257" |
| 7 | archivo | string | nombre base para casos/NNNN.html |
| 8 | fallo | string | FUNDADA/INFUNDADA/IMPROCEDENTE |
| 9 | derechos[] | array | derechos vulnerados |
| 10 | ponentes[] | array | magistrados |
| 11 | citas[] | array | expedientes citados ("01203-2005"...) |
| 12 | texto_completo | string | ⚠️ TRUNCADO en datos.js (a veces solo encabezado); el índice se generó del texto COMPLETO |
| 13 | demandado | string | |
| 14 | materia | string | |
| 15 | juez | string | |
| 16 | parte_resolutiva | string | texto de la parte resolutiva (78% cobertura) |
| 17 | vinculante | 0/1 | precedente vinculante |
| 18 | leyes[] | array | números de ley citados |
| 19 | fecha_resolucion | string | ISO, solo 42% de casos |
| 20 | voto_singular | 0/1 | |

## Mapa campo→idx (usado en motor)

```
numero:0 tipo:1 distrito:2 sentencia:4 año:5(usa c[5]) fallo:8 derecho:9
ponente:10 demandado:13 materia:14 juez:15 vinculante:17 ley:18 ds:18 art:18 voto:20
```

## Errores de mapeo vistos en una implementación paralela (lección)

Una instancia mapeó `sumilla:3` (pero c[3] es demandante, casi siempre vacío) y
`resolutiva:16` OK, pero su motor indexaba solo c[3]+c[8]+c[0] → `buscar("pension")`
= 0 resultados con datos reales. El texto buscable vive en c[12] (vía indice.js,
no por escaneo de datos.js).

## Datos de contexto

- Total casos: 8,794 · Términos en índice: ~varios cientos de miles
- `indice.js` 15.5 MB delta-encoded · `datos.js` 10 MB · `cooc.js` 0.5 MB
  (co-ocurrencias) · `similares.js` 0.7 MB (SIMILARES por índice numérico)
- `cooc.js`: `window.COOC = { término: [[rel, score], ...] }`
- `similares.js`: `window.SIMILARES = { "idx_num": [[idx, score], ...] }` — las
  claves son el índice del caso (0-based) como string, NO el expediente.

## Verificación rápida en Node (motor UMD)

```js
global.window = global;
require('../html_casos_v4/datos.js');
require('../html_casos_v4/indice.js');
const { createEngine } = require('./js/search-engine.js');
const eng = createEngine(window.CASOS, window.INDICE, window.COOC, window.SIMILARES);
eng.buscar('pension');            // → { docs, usadoOR, total } (total ~2706)
eng.sugerirTypo('penssion');      // → 'pension'
eng.similaresDe(0, 3);            // → [{idx, score, caso}]
eng.coocurrenciasDe('pension', 3);// → [['salud', score], ...]
```
