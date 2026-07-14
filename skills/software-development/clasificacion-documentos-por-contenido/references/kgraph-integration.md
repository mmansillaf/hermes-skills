# Integración con KGraphResolucionesV3

## Formato esperado por indexer.py

El indexer (pipeline/indexer.py) busca archivos `data_raw/rag_listo_batch_*.json` con esta estructura:

```python
{
    "id_documento": "hash_md5_16chars",           # unico por documento
    "ruta_local": "/path/al/pdf_o_html",           # ruta absoluta al original
    "contenido_a_vectorizar": {
        "hechos": "Sintesis de los hechos del caso (1-2 parrafos)",
        "problema": "Cuestion juridica central a resolver",
        "fallo": "Decision final del tribunal (parte resolutiva)"
    },
    "metadatos_graphrag": {
        "jueces_magistrados": ["Nombre del juez"],
        "demandantes_accionantes": ["Nombre del demandante"],
        "demandados_accionados": ["Nombre del demandado"],
        "leyes_y_articulos_citados": ["Ley X, Art. Y"],
        "conceptos_legales_clave": ["Concepto juridico relevante"]
    }
}
```

## Flujo completo

1. **Extraer** con extractor_qwen.py:
   ```bash
   cd /home/usuario/Escritorio/PyCode/KGraphResolucionesV3
   PYTHONUNBUFFERED=1 python3 -u extractor_qwen.py --batch 10000 --area LABORAL \
     > /tmp/batch.log 2>&1 &
   tail -f /tmp/batch.log
   ```

2. **Reindexar**:
   ```bash
   cd /home/usuario/Escritorio/PyCode/KGraphResolucionesV3
   python3 pipeline/indexer.py --force
   ```

3. **Consultar** (sin cambios):
   ```bash
   python3 graphrag_pro.py --query "indemnizacion por despido arbitrario"
   python3 graphrag_console.py --query "despido arbitrario reposicion"
   ```

## Campos que genera el LLM vs campos que usa indexer.py

| Campo LLM (de Qwen) | Campo indexer.py | Uso |
|---|---|---|
| resumen_hechos | contenido_a_vectorizar.hechos | FAISS + BM25 |
| resumen_problema | contenido_a_vectorizar.problema | FAISS + BM25 |
| resumen_fallo | contenido_a_vectorizar.fallo | FAISS + BM25 + grafo |
| jueces_magistrados | metadatos_graphrag.jueces_magistrados | Grafo (nodos Juez) |
| demandantes_accionantes | metadatos_graphrag.demandantes_accionantes | Grafo (nodos Actor) |
| demandados_accionados | metadatos_graphrag.demandados_accionados | Grafo (nodos Demandado) |
| leyes_y_articulos_citados | metadatos_graphrag.leyes_y_articulos_citados | Grafo (nodos Ley) |

## Ubicación del extractor

El extractor integrado está en:
```
/home/usuario/Escritorio/PyCode/KGraphResolucionesV3/extractor_qwen.py
```

Dependencias: llama-server en puerto 8080 (Qwen 2.5 7B), pdftotext, catdoc, python-docx.

## Para lotes parciales

El indexer soporta checkpointing: si ya hay índices (FAISS, BM25, grafo), carga los existentes y solo agrega documentos nuevos (por id_documento). Útil para procesar por áreas sin reprocesar todo.

El extractor guarda checkpoints cada 100 documentos en data_raw/rag_listo_batch_qwen_*.json. Cada archivo contiene hasta 100 documentos en el formato esperado.
