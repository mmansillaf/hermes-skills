# v4.3 — Votos singulares, casos similares, top-10 leyes, histograma lag, typos + fallback OR

Sesión: 2026-08-02 · html_casos_v4 (SPD: SPEC-v4.3.md · tests/test_v4_3.py · tests/test_typos_or.js)
Todas las features 100% offline (file://, sin servidor, sin APIs).

## datos.js crece a 21 campos
Índices nuevos (además de los 13-19 de v4.1/v4.2):
- `[20]` = voto_singular (0/1)

## extraer_voto_singular
```python
PAT_VOTO_SING = re.compile(r'voto singular|votos singulares|discordia|discrepan', re.I)
def extraer_voto_singular(texto):
    return 1 if (texto and PAT_VOTO_SING.search(texto)) else 0
```
- Cobertura real: 1,891/8,794 (21% — incluye discordia, por eso supera el ~17% estimado).
- Posting `voto:singular` por caso con voto → filtro UI `voto:singular`.
- UI: badge morado `🗳 Voto singular` en tarjetas + badge en la cabecera del caso.
- **Wiring de un campo nuevo en el index.html = 4 puntos**: parseQuery campos dict, regex de alternancia de campos, idxCampo map, y rama de filtro (ej. `if (campo === 'voto')`). Olvidar cualquiera = campo ignorado en silencio.

## computar_similares (coseno, top-términos)
```python
def computar_similares(corpus, top_k=5, max_term_por_doc=40):
    # vectores tf por doc: Counter(tokenize(texto, limite=12000)).most_common(40)
    # filtro discriminación: min_df = min(5, max(1, N//2)); max_df = 300 if N>=300 else N+1
    # normalizar por longitud (norma L2)
    # pares: por término, SOLO top-20 docs por peso (MAX_DOCS_POR_TERMINO=20)
    #   docs_con_t = [(d, vectores[d][t]) ...]; sort(-w)[:20]
    #   for i<j: w = wa*wb; pares[a][b]+=w; pares[b][a]+=w   # SIMÉTRICO
    # score = w / (na*nb); sort desc; out[a] = rels[:top_k]
```
- El bucle O(k²) naive explotó: 12+ min CPU al 90% (término en 3,500 docs = 6M pares).
  Benchmark 2,000 docs = 6.2 s → con las 2 optimizaciones el run completo ≈ 30 s.
- Resultado real: 8,080/8,794 casos con relacionados (92%); los 714 restantes son docs
  cortos sin pares suficientes — el test debe pedir `>= 8000`, no `== 8794`.
- `similares.js` = `window.SIMILARES = {"doc_idx": [[idx, score], ...]}` — 0.7 MB.

## Bloque "⚡ Casos similares" en el HTML individual
- `generar_caso(d, stem, similares=None)` — nuevo parámetro con lista de dicts
  `{"num", "tipo", "fecha", "stem"}`; renderiza `<ul>` de hasta 5 enlaces.
- Cómputo post-loop: `similares = computar_similares(corpus_sim)` se ejecuta DESPUÉS del
  loop principal (necesita todos los docs). **Guardar `corpus_textos[doc_idx] = texto` en
  el primer loop** para la segunda pasada — releer 8,794 JSON es desperdicio puro.
- Segunda pasada reconstruye un `d_min` con los 21 campos + texto y re-escribe el HTML
  con `generar_caso(d_min, stem, similares=s_list)`.
- **Bug de path**: los enlaces salieron `href="2016-08-04/139_....html"` (sin `../`) →
  resolvían a `casos/2016-08-01/2016-08-04/...` (roto). Fix en el generador:
  `href="../{fecha}/{stem}.html"`. Parcheo batch de los 8,080 HTML ya generados:
  `re.subn(r'href="(\d{4}-\d{2}-\d{2}/)', r'href="../\1', html)`.
- Verificado en navegador: caso cumplimiento contra Red de Salud Huamanga → 5 similares
  todos del mismo tipo (cumplimientos 2015-2016) → la similitud temática funciona.

## Top-10 leyes citadas (UI, sin regenerar)
- Dato ya existía en `[18]` (leyes). Agregación en JS:
  `CASOS.forEach(c => (c[18]||[]).forEach(l => freq[l] = (freq[l]||0)+1))`, top 10 por count.
- Render en el tab gráfico, clic → `$('busca').value = 'ley:' + d.dataset.ley; mostrarTab('buscar'); buscar()`.
- Resultado real: Ley 25212 (1,253), 24029 (1,249), 19990 (1,097), 27444 (1,034), 28411 (884).

## Histograma lag resolución→publicación (UI)
- Buckets 0–90 / 91–180 / 181–365 / 366–730 / 730+ días; `(new Date(fp) - new Date(fr)) / 86400000`.
- Cobertura 42% (3,711/8,794 con fecha_resolucion_iso) — nota en la UI.
- Lag medio ~357 días, mediana ~301 (medido en la sesión).

## Typos (Levenshtein ≤ 2)
- `levenshtein(a,b)` DP clásico en JS; `sugerirTypo(termino)` escanea `Object.keys(INDICE_RAW)`
  saltando claves con `:` (prefijos internos 5:/s:/ley:/ds:/art:), devuelve la más cercana si dist ≤ 2.
- **El prefijo-5 da tolerancia implícita**: "jubilasiom" matchea vía `5:jubil` → sin sugerencia
  (y la búsqueda ya funciona). "penssion" (sin prefijo compartido) → sugiere "pension".
  Probar siempore con un typo SIN prefijo-5 en común.
- UI: en `pintarResultados` cuando hay 0 resultados, para cada token no encontrado buscar
  sugerencia y renderizar botones clicables "¿Quisiste decir: X?" (onclick re-set + buscar()).

## Fallback OR
- En `buscar()`: si `!docs.length && P.toks.length >= 2` → unión de postings por término
  (`uniones = P.toks.map(expandirTermino).map(ts => unirVarios(ts))`, `Set` union), `usadoOR = true`.
- **Bug**: el aviso se escribió a `$('info')` pero no existe elemento id="info" (el `.info`
  se genera dentro de `#lista`) → no-op silencioso. Fix: `<div id="aviso-or">` dedicado antes
  de `#lista`, toggle display block/none.
- Tests node: `tests/test_typos_or.js` — levenshtein, sugerirTypo (incluye "termino existente
  no es typo": dist 0 consigo mismo), fallbackOR (AND vacío 1 término = NO OR; 2+ = OR).
  Patrón: lógica como funciones puras + assert node, sin framework.

## Verificación humana (AC10-AC16)
- voto:singular → 1,891 resultados, badge morado visible.
- Top-10 leyes renderiza con conteos; clic filtra (ley:25212 → 1,253).
- Histograma lag renderiza buckets.
- Caso con similares: bloque presente, 5 enlaces, enlaces corregidos con ../.
- "penssion" → "¿Quisiste decir: pension?" clicable.
- "jubilacion zzzyyy" → aviso OR visible; volver a "pension" oculta el aviso.

## Suites finales
- pytest: tests/test_v4_3.py (8) + tests/test_v4.py (9) + tests/test_distritos.py (9) = 29 passed.
- node: test_typos_or.js (GREEN) + test_match_campos.js (GREEN).
- Comando: `python3 -m pytest tests/ -q` + `node tests/test_*.js` por cada archivo.
