# v4.1 — Limpieza de distritos (whitelist) y v4.2 — match por token

Sesión 2026-08-02. Continuación de html_casos_v4. Dos fixes con TDD, ambos
verificados en navegador real (file://). Proyecto: ProcesosConstitucionales.

## v4.1 — Distritos contaminados (bug reportado por el usuario)

### Síntoma
El filtro/tab de distritos mostraba nombres de personas y apellidos
(MAXIMILIANO ECHACCAYA, ZARA ANTONIA ARANGO, IVÁN ANCHI TORRES, KARINA YLIANA
MONTERO PANTA...) además de basura tipo "JUEZ", "ESPECIALISTA", "SENTENCIA DE
VISTA", "BENEFICIARIO".

### Causa raíz (2 capas + 1 descubierta en pruebas)
1. **JSON fuente ya contaminado por el scraper original**: el campo `distrito`
   traía ETIQUETAS de header en vez de valores. "JUEZ" (299 casos),
   "ESPECIALISTA" (42), e incluso el nombre del DEMANDANTE capturado como
   distrito (1 caso). Casi todos eran hábeas corpus de juzgados de Ayacucho con
   header "EXPEDIENTE / JUEZ : X / ESPECIALISTA : Y / BENEFICIARIO : Z".
2. **extraer_distrito heredada de v2 con 2 fallos**:
   a) lista negra DISTRITOS_SUCIOS incompleta (faltaban ESPECIALISTA,
      BENEFICIARIO, SOLICITADO, SENTENCIA DE VISTA, PROCESO, DEMANDA...) →
      pasaban directo al resultado.
   b) fallback de fecha solo matcheaba mes en minúscula ("de abril") pero los
      fallos de Ayacucho escriben "de Abril" → no recuperaba el distrito real.
3. **Bug adicional descubierto durante pruebas**: el loop calculaba
   `dist = extraer_distrito(...)` para datos.js pero NUNCA asignaba
   `d['distrito'] = dist` antes de `generar_caso(d, ...)` → los HTML
   individuales mostraban el campo CRUDO del JSON ("JUEZ") mientras datos.js
   decía "AYACUCHO". Incoherencia datos.js ↔ HTML.

### Fix de 3 capas
```python
DISTRITOS_SUCIOS = {  # capa 1: etiquetas de header que el scraper confundio
    'DEMANDANTE','DEMANDADO','DEMANDADOS','DEMANDADA','JUEZ','JUEZA','MATERIA',
    'PROCEDENCIA','EXPEDIENTE','CORTE','SALA','ESPECIALISTA','BENEFICIARIO',
    'SOLICITADO','SOLICITANTE','SENTENCIA','SENTENCIA DE VISTA','PROCESO',
    'DEMANDA','FAVORECIDO','APELANTE','REGIONAL','DEL','VISTOS','AUTO',
    'RESOLUCION','RESOLUCIÓN','DECISION','DECISIÓN','CONSIDERANDO','FUNDAMENTOS',
    'LOCAL DE HUAMANGA','LOCAL DE VILCASHUAMÁN', ...}
DISTRITOS_REALES = {  # capa 2: whitelist ~60 distritos judiciales del Peru
    'LIMA','LIMA NORTE','LIMA SUR','LIMA ESTE','CALLAO','AREQUIPA','CUSCO',
    'AYACUCHO','LA LIBERTAD','LAMBAYEQUE','PIURA','ANCASH','ICA','JUNÍN','JUNIN',
    'PUNO','LORETO','AMAZONAS','SANTA','PASCO','CAJAMARCA','HUÁNUCO','HUANUCO',
    'CAÑETE','CANETE','TACNA','MADRE DE DIOS','MOQUEGUA','HUANCAVELICA','UCAYALI',
    'SAN MARTIN','TUMBES','APURIMAC','HUANCAYO','SELVA CENTRAL','HUAURA','HUARA',
    'SULLANA','CHIMBOTE','TARAPOTO','JAEN','VENTANILLA','HUANTA','VILCASHUAMÁN',
    'VILCASHUAMAN','SAN MIGUEL','CERCADO DE LIMA','MARISCAL NIETO','CONO NORTE',
    'CONO SUR','CONO ESTE','SAN JUAN DE LURIGANCHO','SANTA CRUZ','CARABAYA',
    'SAN ROMAN','CANCHIS','ANDAHUAYLAS','CHINCHA','PISCO','NAZCA','CANGALLO',
    'HUAMANGA','LA MAR','LUCANAS','PARINACOCHAS','PAUCAR DEL SARA SARA','SUCRE',
    'VICTOR FAJARDO','VÍCTOR FAJARDO','AYMARAES','TAMBOPATA','MANU',
    'SAN ANTONIO DE PUTINA'}

def es_distrito_real(valor):
    return _norm_distrito(valor) in {_norm_distrito(d) for d in DISTRITOS_REALES}

def extraer_distrito(texto, campo):
    c = (campo or '').strip().upper()
    # capa 1+2: el campo solo vale si no es etiqueta sucia Y es distrito real
    if c and c not in DISTRITOS_SUCIOS and es_distrito_real(c):
        return c
    if texto:
        t = re.sub(r'\s+', ' ', texto)
        m = re.search(r'CORTE SUPERIOR DE JUSTICIA DE\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ ]{2,40})', t, re.I)
        if not m:
            m = re.search(r'DISTRITO JUDICIAL DE\s+([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ ]{2,40})', t, re.I)
        if not m:
            # capa 3: fallback fecha, mes con mayuscula o minuscula
            m = re.search(r'([A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜ ]{2,30}),\s*\d{1,2}\s+de\s+[A-Za-záéíóúñü]+', t)
        if m:
            d = m.group(1).strip().upper()
            d = re.split(r'\s+(?:SALA|JUZGADO|CORTE|SEGUNDA|PRIMERA|TERCERA|CUARTA|QUINTA)', d)[0].strip()
            if es_distrito_real(d):
                return d
            # intento parcial: ej 'CORTE SUPERIOR DE JUSTICIA DE LIMA' -> LIMA
            for palabra in reversed(d.split()):
                if es_distrito_real(palabra):
                    return palabra
    return ''
```
Y en el loop principal: `d['distrito'] = dist` antes de `generar_caso(d, stem)`
— EL paso que faltaba y provocaba la incoherencia HTML.

### Resultados medidos (antes → después)
| Métrica | Antes | Después |
|---|---|---|
| Valores distintos en filtro | 252 | 42 (todos reales) |
| Distritos vacíos | 984 | 193 |
| Casos con basura | 596 | 0 |
| Caso 00711-2016 (era "JUEZ") | JUEZ | AYACUCHO |
| Caso 01276-2016 (era "ESPECIALISTA") | ESPECIALISTA | PUNO |
| Caso 0072-2015 (era nombre persona) | MAXIMILIANO ECHACCAYA | AYACUCHO |

### Tests
- tests/test_distritos.py: 9 tests. RED primero (5 fallaban demostrando los
  bugs). El test clave lee el HTML EN DISCO y verifica la card distrito:
  `re.search(r'<div class="card"><div class="k">Distrito</div><div class="v">([^<]+)</div>', html)`
  — solo así se atrapa el bug del campo no reasignado.

## v4.2 — Match por token en campos discretos

### Síntoma
`distrito:ica` devolvía también HUANCAVELICA (substring "ica" ⊂ "huancavelica").
`ley:5` matcheaba "25212" (substring "5").

### Fix
Token-match (palabra completa) SOLO para campos discretos: distrito, ley, ds, art.
Substring se mantiene en numero, tipo, sentencia, año, derecho, ponente,
demandado, materia, juez, vinculante (allí el substring es deseable o inocuo).

```js
const tokenMatch = ['distrito', 'ley', 'ds', 'art'].includes(campo);
...
if (tokenMatch) {
  const toks = norm(vals.join(' ')).split(/[^a-z0-9]+/).filter(Boolean);
  const campoNorm = ' ' + norm(String(val)).replace(/[^a-z0-9]+/g, ' ') + ' ';
  return toks.every(t => campoNorm.includes(' ' + t + ' '));
}
return vals.every(v => norm(String(val)).includes(v) || (idxCampo === 5 && String(c[5]).includes(v)));
```

Semántica lograda:
- "ica" matchea ICA pero NO HUANCAVELICA
- "lima" matchea LIMA, LIMA NORTE, LIMA SUR, LIMA ESTE (token completo en todos)
- "lima norte" matchea solo LIMA NORTE (ambos tokens presentes)
- "ley:25212" matchea; "ley:5" NO matchea 25212

### Verificación
- tests/test_match_campos.js (node): función pura `matchCampo` + `matchActual`
  (substring) — la lógica substring FALLA 3 checks (demuestra el bug), la nueva
  pasa 12. Correr: `node tests/test_match_campos.js`.
- Navegador real: distrito:ica → 359 resultados, 0 HUANCAVELICA, sí ICA;
  distrito:lima norte → 66 resultados 100% LIMA NORTE; ley:25212 → 1,253;
  regresiones (pension 2,706 + sugerencias, orden fecha antiguo) OK.

## Nota de proceso
- Regenerar los 8,794 HTML + datos.js toma ~5 min (background + waits de 60s).
- Tras un fix del generador hay que REGENERAR (los HTML individuales y datos.js
  deben quedar coherentes; parchear solo datos.js deja los HTML viejos).
- Siempre preguntar antes de tocar datos "sucios": el usuario aprecia el
  diagnóstico con evidencia (contar basura, ejemplos reales) antes del fix.
