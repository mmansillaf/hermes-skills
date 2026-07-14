# Clasificacion de documentos CEJ: resoluciones vs cedulas

## Problema

En la pagina `detalleform.html` del CEJ, cada item del seguimiento del expediente puede tener uno o mas botones "Descargar". No todos apuntan a documentos con valor legal:

- Las **CÉDULAS DE NOTIFICACION** son constancias de envio de una resolucion a las partes procesales. Prueban que se notifico, pero no contienen el texto de la resolucion.
- Las **RESOLUCIONES / AUTOS / SENTENCIAS** contienen el texto juridico del fallo.
- Ambos tipos se descargan como PDF desde `documentoD.html?nid=...`.

## Metodo de clasificacion

Usar el contexto HTML alrededor de cada enlace `[title="Descargar"]`. El texto circundante contiene los metadatos del item de seguimiento.

### Keywords de exclusion (cedulas — NO descargar)

```
CEDULA, CÉDULA, NOTIFICACION, NOTIFICACIÓN, Pta. Cedula
```

### Keywords de inclusion (resoluciones — SI descargar)

```
SENTENCIA, SENTENCIA DE VISTA, AUTO FINAL, AUTO:
```

### Heuristica en Python

```python
EXCLUDE = ["CEDULA", "CÉDULA", "NOTIFICACION", "NOTIFICACIÓN", "Pta. Cedula"]
INCLUDE = ["SENTENCIA", "AUTO FINAL", "AUTO:"]

def es_importante(contexto):
    ctx_upper = (contexto or "").upper()
    if any(k in ctx_upper for k in EXCLUDE):
        return False
    if any(k in ctx_upper for k in INCLUDE):
        return True
    return False  # criterio: solo bajar resoluciones/sentencias
```

## Ejemplo real: expediente 00060-2021 (RODRIGUEZ CRUZ JUAN CARLOS)

El expediente 00060-2021-0-1801-JR-DC-03 tenia 18 botones "Descargar". La clasificacion real:

### Resoluciones con valor legal (DESCARGADAS)

| # | Fecha | Tipo | Contexto | Tamaño |
|---|---|---|---|---|
| 1 | 31/01/2024 | RESOLUCION CUATRO + AUTO | Concede recurso de agravio constitucional. Folios: 1 | 53 KB |
| 2 | 16/11/2023 | SENTENCIA DE VISTA | CONFIRMARON sentencia que declara IMPROCEDENTE la demanda. Folios: 9 | 370 KB |

### Items del seguimiento SIN boton de descarga

| Fecha | Tipo | Nota |
|---|---|---|
| 25/01/2024 | Resolucion S/N (NOTA) | "El documento de la resolucion no se encuentra anexado" |
| 24/01/2024 | ESCRITO (Recurso de Agravio Constitucional) | "Los escritos no se pueden visualizar por este medio" |
| 20/03/2024 | NOTA | Expediente se remite al Tribunal Constitucional |

### Cedulas de notificacion (SALTADAS — ~16 archivos, varios KB cada una)

Eran constancias de notificacion de las resoluciones CUATRO y TRES a cada parte procesal:
- PAN AMERICAN SILVER HUARON S.A.
- PODER JUDICIAL (Procurador)
- AURORA VALVERDE SILVA (Juez)
- VICTOR ANTONIO CASTILLO LEON (Juez)
- LOLA PERALTA GARCIA (Juez)
- MARIA ANGULO (Juez)
- RODRIGUEZ CRUZ JUAN CARLOS (litisconsorte)

Cada parte recibe su propia cedula de notificacion, de ahi que hayan 16 cedulas para solo 2 resoluciones.

## TRAMPA GRAVE: Filtro por contexto HTML padre FALLA (tanto pre como por fila)

**No confiar en el contexto padre ni en la fila del seguimiento para filtrar via DOM traversal.** Esto se probó exhaustivamente en el expediente 00060-2021 con 18 botones "Descargar" y el resultado fue:

- Via CDP `Runtime.evaluate` subiendo 15-30 niveles parent, **todos los 18 items mostraron "Resolución"** en su contexto, pero tambien mostraron datos de notificación
- El filtro clasificó 17 como CEDULA y solo 1 como AUTO → **falso negativo**: se perdió la Sentencia de Vista (370 KB) y la Sentencia (254 KB)
- La razón: el DOM tree del CEJ agrupa cada resolución con su(s) cédula(s) de notificación en el mismo contenedor HTML. Subir por parentNodes captura TODO el contenido de ese contenedor, mezclando ambos tipos de documento.

**No existe un selector CSS confiable** para distinguir enlaces de resoluciones vs cedulas, porque los botones "Descargar" son idénticos (`<a title="Descargar" href="...">Descargar</a>`). La diferencia está solo en el texto circundante, que al ser extraido por DOM traversal se contamina con texto de items hermanos.

### Estrategia CORRECTA: clasificar POST-DESCARGA por contenido del PDF

**Esta es la unica estrategia confiable comprobada en este sitio:**

1. **Descargar TODOS** los documentos del expediente (usando CDP + cookies + ThreadPoolExecutor para rapidez — la sesion expira en ~5 min)
2. **Clasificar post-descarga** extrayendo texto de cada PDF con pymupdf/pdfplumber
3. Buscar en el texto del PDF:

```python
def clasificar_por_contenido(pdf_bytes):
    """Clasifica un PDF del CEJ por su contenido textual."""
    import pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    text_upper = text.upper()
    
    # Cedula de notificacion
    if "CEDULA DE NOTIFICACION" in text_upper:
        return "CEDULA"
    if "NOTIFICACIÓN" in text_upper and "RESUELVE" not in text_upper:
        return "CEDULA"
    
    # Resoluciones con valor legal
    if "SENTENCIA DE VISTA" in text_upper:
        return "SENTENCIA_VISTA"
    if "SENTENCIA" in text_upper and "CONSENTIDA" not in text_upper:
        return "SENTENCIA"
    if "AUTO" in text_upper and "RESUELVE" in text_upper:
        return "AUTO"
    if "RESUELVE" in text_upper:
        return "RESOLUCION"
    
    # Resolucion consentida (valor legal bajo)
    if "CONSENTIDA" in text_upper:
        return "CONSENTIDA"
    
    return "OTRO"
```

4. **Conservar solo** SENTENCIA, SENTENCIA_VISTA, AUTO, RESOLUCION
5. Mover CEDULA y OTRO a subcarpeta `cedulas/`

**Ventajas de este enfoque:**
- Funciona con cualquier tipo de documento (PDF, HTML)
- NO depende de la estructura HTML del CEJ (que cambia)
- Clasifica por el contenido juridico real del documento
- Se puede automatizar completamente

### Datos reales del expediente 00060-2021

De 18 PDFs descargados (~3.9 MB total):
- ~16 eran **CEDULAS DE NOTIFICACION** (~2.3 MB) → descartar
- **2 eran RESOLUCIONES REALES** (~0.4 MB): Sentencia de Vista (16/11/2023) y Resolucion CUATRO (31/01/2024)
- Ademas habia ~2 resoluciones intermedias (Sentencia 31/07/2023 y Auto abstencion 14/11/2023) que el filtro HTML no detecto pero el PDF las muestra

**La cedula NO tiene valor juridico sustantivo** — solo prueba que se notifico a una parte. Lo valioso son las resoluciones mismas.

## Conclusion

**No usar clasificacion pre-descarga por HTML.** Usar descarga total + clasificacion post-descarga por contenido de PDF. Es mas rapido (ThreadPoolExecutor 5 workers descarga 18 PDFs en ~3s), mas confiable (no falsos negativos), y mas mantenible (no depende de estructura HTML).

El flujo correcto para cualquier expediente CEJ:
1. Conectar al Chrome del usuario via remote-debugging + CDP (page_load_strategy='none')
2. Extraer TODOS los nids via Runtime.evaluate
3. Obtener cookies via Network.getAllCookies
4. Descargar TODOS los PDFs en paralelo (ThreadPoolExecutor)
5. Clasificar post-descarga leyendo texto de PDFs
6. Conservar solo resoluciones/autos/sentencias
