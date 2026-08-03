# v3: co-ocurrencia semántica + recuperación de campos faltantes

Detalle de implementación probado en la v3 del buscador TC (8,794 casos,
html_casos_v3, Ago 2026). Reproducible para cualquier corpus JSON.

## 1. extraer_numero — campo ausente recuperado del texto

Problema: 936/8,794 JSON tenían `numero: None`; el fallback `json_path.stem`
mostraba "039_Cumplimiento_s-n" en títulos, cards y búsquedas.

```python
PAT_EXP_TC = re.compile(
    r'(?:EXP\.?\s*N[°º]?\s*|EXPEDIENTE\s*N[°º]?\s*|EXPEDIENTE\s+:?\s*)'
    r'(\d{4,5}-\d{4}(?:-\d{1,4})?(?:-[A-Z]{2,4})?(?:\s*/\s*[A-Z]{2,4})?)',
    re.I,
)
PAT_EXP_LIBRE = re.compile(r'\b(\d{4,5}-\d{4}-[A-Z]{2,4}/\s*TC)\b', re.I)

def extraer_numero(texto, campo):
    if campo and str(campo).strip() and str(campo).strip().lower() not in ('s-n','none','null'):
        return str(campo).strip()
    if texto:
        t = re.sub(r'\s*/\s*\n\s*', '/', texto)   # une "PC/\nTC" (salto del diario)
        t = re.sub(r'\s+', ' ', t)
        m = PAT_EXP_TC.search(t) or PAT_EXP_LIBRE.search(t)
        if m:
            num = re.sub(r'\s+', '', m.group(1))
            if re.search(r'\d{4,5}-\d{4}', num):   # validar forma antes de aceptar
                return num
    return "s/n"
```

Resultado: 271 recuperados del texto, 665 sin dato → "s/n" limpio (0 leaks de
nombres de archivo). El nombre del archivo (stem) NUNCA debe ser fallback visible.

## 2. computar_coocurrencia — semántica offline sin embeddings

Score = frecuencia de co-ocurrencia (señal principal) + PMI como ajuste log:

```python
score = co * (1.0 + max(0.0, math.log((N * c) / (dfa * dfb))))
```

- `co` = nº de docs donde a y b co-ocurren; `dfa/dfb` = document frequency;
  `N` = total docs. Frecuencia domina; PMI≈0 cuando la co-ocurrencia es la
  esperada al azar (log ≤ 0 → clamp a 0, queda co*1).
- Dos pasadas: (1) df global + filtro de elegibles (df ≥ min(10, N//2) y
  df ≤ 60% de docs — quita ruido y términos ultra-genéricos); (2) pares solo
  entre elegibles, cap 60 términos/doc (los más frecuentes DENTRO del doc con
  Counter) para que el O(n²) sea viable en 8.8K docs.
- Salida SIMÉTRICA: cada par se escribe en ambas direcciones (`out[a]` y
  `out[b]`), ordenada por score desc, top-12 por término.
- Emitir como `window.COOC = {...};` (~0.5 MB, ~1.9K términos para 8.8K docs).

## 3. Filtro de boilerplate — la lección de calidad

Sin filtro, "pension" relacionaba con ["amparo","fecha","fojas","contra",
"recurso","demanda"] — palabras que aparecen en casi todo fallo. Con
STOP_LEGAL (lista de ~90 términos de relleno legal: fojas, recurso, demanda,
agravio, expedida, interpuesto, recurrente, declare, don, doña, juez,
resolucion, articulo, ley, codigo, norma, numeral, inciso, folio, emplazado...)
la calidad saltó a ["salud","normalizacion","cina","previsional","onp"].
Regla: los términos de STOP_LEGAL nunca son "relacionado" (se excluyen del
cálculo de pares, no solo del display).

## 4. UI: chips de términos relacionados

```html
<div class="sug-sem" id="sug-sem" style="display:none"></div>
```

```js
const COOC = window.COOC || {};
function pintarSugSemanticas(){
  // por cada token de la query (expandido: term, 5:prefix, s:stem),
  // acumular (COOC[base] || []) sin duplicar ni repetir tokens ya en query;
  // ordenar por score desc, top 8, renderizar <button class="pill sem">+ rel</button>
  // click → busca.value = q + ' OR ' + rel; buscar();
}
// llamar al final de buscar(), NO en un listener aparte
```

Chips se muestran/ocultan según haya relacionados; el click expande con OR y
re-ejecuta la búsqueda (el OR amplía resultados: verificado "pension" + "+salud"
→ "pension OR salud" con más hits).

## 5. TDD aplicable a este flujo

- `if __name__ == "__main__":` alrededor del loop de build → el módulo se puede
  importar en pytest sin disparar la generación completa.
- Tests RED→GREEN sobre funciones puras: extraer_numero (5 casos: EXP. N° con
  coma, expediente judicial, salto de línea, campo respetado, fallback),
  computar_coocurrencia (términos juntos, JS válido, top-k ordenado), salida
  (ningún HTML con "_s-n").
- Criterios UI (AC): cambiar orden reordena, teclear fecha actualiza conteo,
  chips aparecen al buscar "pension", click expande query.
- Verificación final SIEMPRE en navegador real (browser_navigate file://) —
  los tests unitarios no cubren eventos DOM.

## 6. Incidente rsync --delete (no repetir)

El generador escribía en /tmp stage y cerraba con
`rsync -a --delete stage/ destino/`. Stage NO contiene index.html/scripts →
el --delete borró index.html, generar_v3.py, SPEC y tests del destino.
Fix: `rsync -a stage/ destino/` (sin --delete) o --exclude explícito.
