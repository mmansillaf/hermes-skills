# JSON de casos El Peruano → HTML legible + índice con buscador

Patrón validado 2026-08-01 en `D:\PyCode\ProcesosConstitucionales`.
Convierte los JSON por caso (salida del pipeline de extracción) en HTML
legible para consumo humano, con un índice navegable.

## Corpus y salida

- Origen: `D:\PyCode\ProcesosConstitucionales\data\casos_2016_2021\`
  — una subcarpeta por fecha (`YYYY-MM-DD/`), ~8.794 JSON / 830 fechas.
- Destino: `D:\PyCode\ProcesosConstitucionales\html_casos\`
  - `index.html` (~1.8 MB) — índice con buscador
  - `casos/<fecha>/<stem>.html` — un HTML por caso
  - `generar_todo.py` — generador reutilizable

## Schema del JSON (campos que existen)

`fecha_publicacion, edicion, tipo, numero, sentencia, distrito, corte,
fecha_resolucion, fecha_resolucion_iso, demandante, texto`.

- `texto` es el cuerpo íntegro de la sentencia con `\n` literales
  (líneas rotas por el ancho de columna del PDF original).
- `tipo` ∈ {Amparo, Habeas Data, Cumplimiento, Habeas Corpus,
  Accion Popular} — el `numero` lleva sufijo (PA/TC, PHD/TC, PC/TC…).

## Detección de secciones — la regla que evita falsos positivos

NO usar heurística de "línea en MAYÚSCULAS" (marca nombres de magistrados,
"SS.", códigos de edición "W-1972663-34"). Usar lista exacta + prefijos:

```python
SECCIONES_EXACTAS = {
    "asunto", "antecedentes", "fundamentos", "análisis", "analisis",
    "considerando", "resuelve", "parte resolutiva", "ha resuelto",
    "razón de relatoría", "razon de relatoria", "petitorio",
    "delimitación del petitorio", "análisis de la controversia",
    "por tales consideraciones", "publíquese y notifíquese",
    "publiquese y notifiquese", "costos procesales",
    "sentencia del tribunal constitucional",
}
SECCIONES_PREFIX = ("proceso de ", "exp. ", "voto ", "los magistrados", "el tribunal")

def es_titulo_seccion(linea):
    low = linea.strip().lower()
    return low in SECCIONES_EXACTAS or any(low.startswith(p) for p in SECCIONES_PREFIX)
```

PITFALL CRÍTICO: evaluar cada LÍNEA antes de unir párrafos. Si primero se
juntan las líneas en párrafos y después se busca el título, "ASUNTO" queda
pegado al párrafo siguiente ("ASUNTO Recurso de agravio..."). Patrón:

```python
def texto_a_html(texto):
    out, actual = [], []
    def flush():
        if actual:
            out.append(f"<p>{esc(' '.join(actual))}</p>")
            actual.clear()
    for linea in texto.split("\n"):
        l = linea.strip()
        if not l: flush(); continue
        if es_titulo_seccion(l):
            flush(); out.append(f'<h3 class="seccion">{esc(l)}</h3>')
        else: actual.append(l)
    flush(); return "\n".join(out)
```

Resultado real del corpus: secciones PROCESO DE…, EXP. N°…, SENTENCIA DEL
TRIBUNAL CONSTITUCIONAL, ASUNTO, ANTECEDENTES, FUNDAMENTOS, HA RESUELTO,
VOTO DE LOS MAGISTRADOS…, RAZÓN DE RELATORÍA — y los nombres de magistrados
quedan como texto normal.

## Índice (index.html) — buscador en vivo + pills por tipo

- Stats por tipo de proceso (Contador por `tipo`): Cumplimiento 3.291,
  Amparo 3.165, Habeas Corpus 1.453, Habeas Data 635, Accion Popular 250.
- `<input type="search">` que filtra en vivo sobre `data-t` (tipo) +
  `data-n` (número) + fecha de cada `<li>`. Se verifica con
  `browser_console` evaluando cuántos `<li>` quedan visibles.
- Pills de filtro por tipo (`data-f`), combinables con el buscador;
  toggle activo = fondo azul (`pill.act`).
- Agrupación por fecha en `<details class="grupo">` plegables, cada uno
  con contador de casos; cada caso = link a `casos/<fecha>/<stem>.html`.
- Cada HTML de caso lleva link "← Volver al índice" (`../index.html`).

## CSS — preferencia del usuario

- Base 13px, NUNCA menos (rechazó fuentes pequeñas explícitamente).
- Paleta "azul judicial": gradiente cabecera `#1e3a8a → #1d4ed8`,
  acento `#1d4ed8`, fondo `#f4f6fb`, tinta `#17233b`, líneas `#e2e8f0`.
  (Primera versión usó violeta `#7c3aed`; el usuario no objetó, pero el
  azul quedó como estándar del proyecto.)
- Título caso 24px, metadatos 14px, secciones 13px uppercase, cuerpo
  13px justificado, `max-width: 900px`, responsive a 600px.
- Metadatos en grid `repeat(auto-fit, minmax(190px,1fr))` de tarjetas.

## Rendimiento — WSL/NTFS (pitfall medido)

Escribir 8.794 archivos pequeños con `Path.write_text()` directo a
`/mnt/d` (drvfs/NTFS) corre a ~17-64 archivos/s → >9 min total y el
proceso muere con timeout de 300 s.

Solución validada: **staging en /tmp (ext4 local) + cp -r en lote**.

1. Generar todos los HTML + index en `/tmp/html_casos_stage/` (8.794
   archivos en segundos).
2. `cp -r /tmp/html_casos_stage/casos /mnt/d/.../html_casos/` → 42 s
   para los 8.794 (buffers del kernel, no write_text uno a uno).
3. `rm -rf /tmp/html_casos_stage` al terminar.

Benchmark: NTFS directo 100 archivos = 1.56 s; /tmp 100 = 0.01 s.

## Verificación (regla de entrega del usuario: probar como humano)

- `browser_navigate` a `file:///.../index.html` y a un caso individual.
- Buscar un expediente conocido ("01379" → 1 resultado exacto).
- Clic en pill de tipo → contar `<li>` visibles coincide con el total
  del tipo (3.165 Amparo).
- Limpiar la carpeta vieja de ejemplos (`.../2021-07-30/html/`) al
  centralizar en `html_casos/` para no duplicar.
