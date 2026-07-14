# Integracion CEJ -> KGraphResolucionesV3

## Proyectos

| Proyecto | Ruta |
|---|---|
| Scraper CEJ (spider) | `/home/usuario/Escritorio/PyCode/poder_judicial_results/` |
| KGraph RAG | `/home/usuario/Escritorio/PyCode/KGraphResolucionesV3/` |
| Scraper audit alternativo | `/home/usuario/Escritorio/PyCode/poder_audit/` |
| Virtualenv | `/home/usuario/cej-scraper/` |

## Datos de entrada del spider

El spider `poder_opt.py` lee expedientes desde archivos Excel en `input/`:

| Archivo | Expedientes | Descripcion |
|---|---|---|
| `ExpedienteCodeDownload.xlsx` | 71,560 | Original completo (todas las materias) |
| `LA_DC.xlsx` | 38,242 | Solo materia laboral (LA) |
| `slice_A.xlsx` / `slice_B.xlsx` | 35,779 / 35,780 | Mitades del original |
| `slice_LA_DC_A.xlsx` / `slice_LA_DC_B.xlsx` | 19,121 / 19,121 | Mitades del laboral |
| `filtro_100_200.xlsx` | 101 | Subset de prueba |

**Columnas del Excel:** N° DE DOCUMENTO, TIPO PARTE, PARTE PROCESAL, N° EXPEDIENTE, FECHA DE INICIO, INSTANCIA, ESPECIALIDAD, MOTIVO DE INGRESO, ACTO PROCESAL, MATERIA, ESTADO

**Formato del expediente:** `00060-2021-0-1801-JR-DC-03` (separado por guiones: numero-año-incidente-distrito-organo-especialidad-instancia)

## Formato KGraph (rag_listo_batch_*.json)

El KGraph espera archivos en `data_raw/` con el formato:

```json
{
    "id_documento": "hash_md5_del_custom_id",
    "ruta_local": "batch_groq/custom_id",
    "contenido_a_vectorizar": {
        "hechos": "resumen de hechos del caso",
        "problema": "resumen del problema juridico",
        "fallo": "resumen del fallo/decision"
    },
    "metadatos_graphrag": {
        "jueces_magistrados": ["Juez1", "Juez2"],
        "demandantes_accionantes": ["Demandante"],
        "demandados_accionados": ["Demandado"],
        "leyes_y_articulos_citados": ["Ley X Art. Y"]
    }
}
```

**Pipeline tipico:**
1. PDFs del CEJ -> extraer texto plano (pymupdf)
2. Enviar a Groq Batch API (Llama 3.1 8B para extraccion, Llama 3.3 70B para sintesis)
3. `convertir_outputs.py` convierte JSONL de Groq a `rag_listo_batch_*.json`
4. `graphrag_console.py` indexa los archivos en FAISS/NetworkX

## Flujo completo de descarga + integracion

Para un expediente especifico como 00060-2021 (RODRIGUEZ CRUZ JUAN CARLOS):

```
1. Conectar Chrome usuario (remote-debugging :9225) con CDP
2. Extraer nids + cookies
3. Descargar TODOS los PDFs en paralelo (ThreadPoolExecutor 5 workers)
4. Clasificar post-descarga por contenido del PDF (pymupdf)
   -> Conservar: SENTENCIA, AUTO, RESOLUCION con "RESUELVE"
   -> Descartar: CEDULA DE NOTIFICACION, CONSTANCIA, CARGO
5. Extraer texto de los PDFs importantes
6. Crear rag_listo_batch_cej_XXXXX.json en data_raw/
7. Ejecutar graphrag_console.py para indexar
```

**Nota importante:** El campo `parte` (nombre de la parte procesal) es OBLIGATORIO en la busqueda del CEJ. Los Excel de entrada tienen esta informacion en la columna `PARTE PROCESAL`. Sin el nombre exacto, el captcha correcto no es suficiente para obtener resultados.
