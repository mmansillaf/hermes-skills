# Header Enrichment Session — June 2026

## Contexto

Usuario (abogado litigante peruano, Lex RAG) pidió que las respuestas del sistema identifiquen las resoluciones con más detalle: no solo el código (CAS. N°, RTF N°, EXP. N°), sino también órgano jurisdiccional, lugar, juez ponente, partes procesales y fecha.

## Diagnóstico original

1. **metadata_docs.json muy pobre**: 64,186 entries. ~30% sin órgano, ~79% sin fecha. Muchos identificadores son solo "Exp." sin número real.
2. **HTML sí tiene la info** (lugar, fecha, juez, partes) pero no se extrae como metadata estructurada. El script `scripts/data_prep/extraer_metadata_html.py` existe y parsea HTML, pero no extrae juez/partes.
3. **Grafo NetworkX tiene jueces/demandantes/demandados/leyes** (~59,571 documentos en grafo, 191,871 nodos totales), pero la info iba en sección separada "ANÁLISIS DE PRECEDENTES", no como cabecera del documento.
4. **Prompt del synthesizer** solo pedía "identificador legible" sin mención a órgano, juez o partes.

## Solución: 3 capas

Ver SKILL.md → "Header Enrichment for Rich Citations" para la descripción general.

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `retrieval/hybrid_search.py` | Nueva `_doc_header()` con órgano + fecha + materia; `_doc_label()` mantiene compatibilidad vía lambda |
| `agents/graph_analyst.py` | Sección FALLOS ahora incluye JUECES, PARTES, LEYES por documento |
| `agents/synthesizer.py` | Instrucción #3 expandida con campos obligatorios + ejemplo |

### Ejemplo de salida

**Antes:**
```
**CAS. N° 15-2015 LAMBAYEQUE** → Jurisprudencia/1612215.html
{texto del chunk}
```

**Después:**
```
**CAS. N° 15-2015 LAMBAYEQUE** | Corte Suprema - Sala Laboral
Jurisprudencia/1612215.html
{texto del chunk}
```

Y en la sección del grafo:
```
  [1309310.html] (Jurisprudencia/1309310.html)
    FALTO: La sentencia de primera instancia fue confirmada...
    JUECES: Omar Toledo Toribio
    PARTES: Actor(es): Victor Raul Vasquez Malpica | Demandado(s): Javier Cueva Suarez
    LEYES: Decreto Supremo 003-97-Tr, Art. 22º, 23º Y 24º
```

### Respuesta de prueba

Con la consulta "despido arbitrario en régimen laboral privado peruano", la respuesta ahora cita:

> En el **PROCESO DE AMPARO** (Jurisprudencia/1656988.html), seguido por **Juana Patricia Arriola Gutiérrez** contra la **Derrama Magisterial**...

> En el caso **JUNÍN** (Jurisprudencia/1495259.html), seguido por **Flor de María Puchoc Lara** contra el **Poder Judicial**...

### Estado del push

Commit: `5755740 feat: headers enriquecidos, entidades por doc en grafo, prompt citacional mejorado`
Branch: `feature/deep-research`
Repo: `https://github.com/mmansillaf/KGraphResolucionesV3`
3 files changed, 196 insertions, 151 deletions
