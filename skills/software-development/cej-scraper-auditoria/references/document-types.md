# CEJ - Tipos de documentos y su obtencion

## Estructura de documentos en detalleform.html

La pagina `detalleform.html` (seguimiento del expediente) contiene dos tipos de elementos con enlaces "Descargar":

### 1. Notificaciones / Cedulas (HTML, ~15KB)
- **Endpoint:** `GET /cej/forms/documentoD.html?nid=<hash>`
- **Clase:** `aDescarg`
- **Contenido:** Pagina HTML con detalles de la notificacion (destinatario, fecha de envio, anexos)
- **Tamano:** ~15,060 bytes
- **Valor juridico:** BAJO (solo prueba de notificacion)
- **NO requieren cookies ni auth**
- **NO tienen rate limiting** — descargables en paralelo

### 2. Resoluciones / Sentencias (PDF)
- **Donde estan?:** NO identificado directamente en detalleform.html
- Los enlaces `documentoD.html` en el seguimiento NO apuntan a PDFs
- Probablemente requieren navegacion adicional (click en el item de resolucion, o via otro endpoint)

## Paginacion del seguimiento

El seguimiento tiene **3 paginas** navegables. Cada pagina tiene ~5-35 items. Los enlaces "Descargar" se distribuyen entre las paginas.

| Pagina | Items aprox | Documentos |
|--------|------------|------------|
| 1 (Principal) | 5 | ~18 Descargar |
| 2 | ~35 | ~18 Descargar |
| 3 | ~35 | ~18 Descargar (estimado) |

**El script actual solo captura pagina 1.** Para capturar todos:
- Click en "2" → esperar 4s → extraer nids
- Click en "3" → esperar 4s → extraer nids
- Combinar y descargar todo en paralelo

Ver `references/paginacion-seguimiento.md`.

## Problema: Filtro de keywords sobre-estima

El filtro marca documentos como "valiosos" porque las palabras clave aparecen en el TEXTO del item de seguimiento, pero el enlace "Descargar" asociado no apunta a ese documento — apunta a la notificacion de ese documento.

**Ejemplo:**
```
Item: "SENTENCIA DE VISTA - Confirmaron la sentencia..."
Link: documentoD.html?nid=XXX  →  Esto es la NOTIFICACION de la sentencia, no la sentencia misma
```

## Output tipico del scraper actual
```
36 documentos encontrados (en 3 paginas)
36/36 valiosos (keyword match)
36 HTML descargados (notificaciones)
0 PDFs
```
