---
name: json-to-offline-fulltext-search
description: Build an offline full-text search UI from JSON docs.
---

# JSON → Buscador offline full-text (HTML + JS, doble-clic)

Convierte N archivos JSON (p. ej. jurisprudencia scrapeada) en una carpeta con:
`index.html` (UI con buscador), `datos.js` (metadatos por doc), `indice.js` (índice invertido comprimido), `casos/` (HTML individuales). Funciona con doble clic en file://, sin servidor.

## Cuándo usar
- Tienes cientos/miles de JSON con metadatos + campo texto multilínea
- Quieres búsqueda full-text local, rápida, offline, sin backend
- El usuario abrirá index.html con doble clic en Windows (WSL: /mnt/...)

## Reglas de oro (pitfalls aprendidos)

1. **file:// NO permite fetch()** (CORS). La única vía para cargar datos es `<script src="datos.js">` / `<script src="indice.js">` que definan `window.CASOS` / `window.INDICE`. Nunca uses fetch para el índice.
2. **NTFS/drvfs es lento** escribiendo archivo por archivo (~64/s en WSL). Estrategia: escribir todo en `/tmp` (ext4, instantáneo) y copiar con `cp -r` al destino (42s para 8,794 archivos). Nunca escribas 8K+ archivos directo a /mnt/d con write_text.
3. **Comprime el índice con delta-encoding**: los postings están ordenados; guarda deltas como chars (`chr(33+d)` para d<90, `~N~` para mayores). 25.7 MB → 15.3 MB. Decodificar lazy en JS (Map cache por término).
4. **Stopwords rompen el AND**: el índice excluye stopwords; el JS de búsqueda DEBE filtrar las mismas stopwords antes de intersectar, o "abuso del derecho" → token "del" → 0 resultados.
5. **Sinónimos como OR, no AND**: si "pension" expande a sinónimos (onp, afp...), únelos al MISMO set del término. Si los agregas como conjuntos AND extra, "pension NOT onp" se vuelve imposible (pension AND onp AND NOT onp = 0).
6. **Frase exacta ("...")**: los tokens de la frase deben participar del AND; el match exacto solo hace boost de ranking (el índice sin posiciones no puede verificar frase real). No filtres por includes sobre el resumen corto → 0 resultados.
7. **Campos con regex greedy**: `fallo:fundada derecho:pension` se comía todo como valor de fallo. El valor de un campo termina cuando aparece otro campo: `([^\s:]+(?:\s+(?!\w+:)[a-z0-9áéíóúñü\-\.]+)*)`.
8. **`fallo:fundada` matchea INFUNDADA** con includes; usa comparación exacta para el campo fallo.
9. **Normalización**: sin tildes (NFD + quitar \u0300-\u036f) y minúsculas en AMBOS lados (índice Python y query JS).
10. **Datos sucios del scraper**: el campo distrito venía "DEMANDANTE"/"JUEZ" (etiquetas mal capturadas). Recupera el valor real del texto con regex ("CORTE SUPERIOR DE JUSTICIA DE X", fallback "Ciudad, N de mes"). Normaliza a mayúsculas para agrupar variantes (Ayacucho vs AYACUCHO).

## Pasos

1. **Inspeccionar el JSON fuente**: estructura, campos, tamaño total del texto (para decidir límite de indexado, p. ej. 12K chars/caso).
2. **Escribir generador Python** (`generar_v2.py`) que por cada JSON:
   - Extrae semántica con regex: fallo (FUNDADA/INFUNDADA/IMPROCEDENTE), demandante completo, derechos vulnerados (diccionario), ponentes, citas STC, resumen (primeras frases tras ASUNTO)
   - Construye `casos[]` (array plano de arrays, no objetos: menos bytes)
   - Construye postings: metadatos ×3 (prioridad) + texto (limitado) + prefijos-5 (`5:xxxxx`) + stems (`s:stem`) para stemming implícito
   - Escribe `datos.js` y `indice.js` (delta-encoded) en /tmp stage
   - Escribe los HTML individuales en /tmp stage
3. **Escribir index.html**: `<script src="datos.js"> <script src="indice.js">`, decoder lazy, parser de query (frase/campos/NOT/OR), ranking por frecuencia, filtros por tipo/año/fallo, tabs (nube, distritos, gráfico años), favoritos localStorage, exportar CSV/JSON.
4. **Ejecutar en background** (`terminal(background=true, notify_on_complete=true)`) porque la lectura NTFS tarda (~3-5 min para 8,794 docs). El wait se clampa a 60s; usa varios wait.
5. **Copiar en lote**: `cp -r stage/casos destino/ && cp datos.js indice.js destino/`.
6. **Probar como persona en navegador** (browser_navigate file://): búsquedas (frase, NOT, OR, campos), filtros, dark mode, tabs, links de citas, resaltado ?q=, notas localStorage, distritos limpios.

## Verificación (siempre)
- Conteo de archivos generados == N JSON procesados
- 0 errores de parseo reportados
- En navegador: "Vela Albornoz" (nombre completo del demandante, campo truncado en JSON) debe devolver resultados → confirma extracción + full-text
- `fallo:fundada` NO debe devolver INFUNDADA
- Un link de "Fallos citados" debe llevar a `../index.html?q=XXXX` y precargar la búsqueda (el index debe leer `URLSearchParams(location.search).get('q')` al init)

## Estructura de datos casos[] (índices usados en JS)
[0]=numero, [1]=tipo, [2]=distrito, [3]=demandante, [4]=sentencia, [5]=fecha, [6]=edicion, [7]=stem archivo, [8]=fallo, [9]=derechos[], [10]=ponentes[], [11]=citas[], [12]=resumen
