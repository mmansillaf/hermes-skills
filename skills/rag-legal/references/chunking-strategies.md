# Estrategias de Chunking por Tipo de Documento

## Sistema de Puntuación

`detect_doc_type()` usa puntuación acumulativa. Cada tipo suma puntos por patrones encontrados.
Gana el tipo con mayor puntuación. Si hay empate, prioridad: sentencia > resolucion > contrato > norma > libro > informe > generico.

## Patrones por Tipo

### contrato
```
CLÁUSULA PRIMERA|SEGUNDA|TERCERA... (ordinal)
CLÁUSULA 1|2|3... (arábigo)
CLAUSULA (sin tilde) + número
CONTRATO DE ... (título)
```

### resolucion
```
CONSIDERANDO (Primero|Segundo|...)
SE RESUELVE|RESUELVE:
VISTO: (en contexto administrativo)
RESOLUCION (título)
```

### sentencia
```
VISTOS: (al inicio)
FALLA:|FALLO:
PARTE RESOLUTIVA
SENTENCIA (título)
EXPEDIENTE N° (judicial)
```
Desambiguación: si hay VISTOS + FALLA → sentencia (no resolución)
Incluso si también hay CONSIDERANDO (que comparte con resolución).

### libro
```
CAPITULO I|II|III... (romano)
CAPITULO 1|2|3... (arábigo)
ÍNDICE|INDICE
SECCIÓN (con numeración romana)
```

### informe
```
I\. | II\. | III\. | IV\. | V\. (romano con punto)
1\. | 2\. | 3\. (arábigo con punto al inicio de línea)
A\. | B\. | C\. (letra con punto)
```

### norma
```
ARTÍCULO 1°|1|2... 
TÍTULO (I|II|...|PRIMERO|SEGUNDO...)
Arts\.|Artículo (abreviado)
```

### generico
Ninguno de los patrones anteriores → 512 tokens con overlap 100 tokens.

## Pruebas de Regresión

Siempre ejecutar después de modificar patrones:

```python
from src.ingestion.ingest import detect_doc_type

tests = [
    ("CLAUSULA PRIMERA\nCLAUSULA SEGUNDA", "contrato"),
    ("CONSIDERANDO:\nPrimero.\nSE RESUELVE:", "resolucion"),
    ("VISTOS:\nCONSIDERANDO:\nFALLA:", "sentencia"),
    ("CAPITULO I\nCAPITULO II\nINDICE", "libro"),
    ("I. Introduccion\nII. Analisis\nIII. Conclusiones", "informe"),
    ("ARTICULO 1\nARTICULO 2\nTITULO I", "norma"),
    ("Este es un texto sin estructura definida para probar", "generico"),
]
for text, expected in tests:
    result = detect_doc_type(text)
    assert result == expected, f"Expected {expected}, got {result}"
print("7/7 tipos detectados correctamente")
```

## Estrategias de Chunking

### contrato → `_chunk_contrato()`
Cada cláusula es un chunk independiente con:
- `section`: "Clausula Primera"
- `tipo`: "clausula"  
- `path`: [doc_id, "Clausula Primera"]

### resolucion → `_chunk_resolucion()`
Cada considerando y cada artículo resolutivo son chunks:
- `section`: "Considerando Primero" | "Articulo 1"
- `tipo`: "considerando" | "resuelve"
- `path`: [doc_id, "Considerandos", "Considerando Primero"]

### sentencia → `_chunk_sentencia()` (reutiliza resolución)
Mismos patrones que resolución pero con VISTOS como sección inicial.
- `section`: "VISTOS" | "CONSIDERANDO" | "PARTE RESOLUTIVA"
- `tipo`: "sentencia"

### libro → `_chunk_libro()`
Capítulos como chunks padre, subsecciones como chunks hijo:
- `section`: "Capitulo I" | "Seccion 1.1"
- `tipo`: "libro_capitulo" | "libro_seccion"
- `path`: [doc_id, "Capitulo I", "Seccion 1.1"]
- Límite: chunk > 2000 tokens → subdividir por párrafo

### informe → `_chunk_informe()`
Secciones numeradas romanas o arábigas:
- `section`: "I. Introduccion" | "2. Analisis"
- `tipo`: "informe_seccion"
- `path`: [doc_id, "II. Analisis Legal"]

### norma → `_chunk_norma()`
Artículos individuales:
- `section`: "Articulo 1" | "Titulo I"
- `tipo`: "articulo_ley"

### generico → `_chunk_generico()`
Sliding window sobre párrafos:
- 512 tokens (~2048 chars) por chunk
- 100 tokens (~400 chars) overlap
- `section`: "Pagina X" o "Parrafo X"
- `tipo`: "generico"
