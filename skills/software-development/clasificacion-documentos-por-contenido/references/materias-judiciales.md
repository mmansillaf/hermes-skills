# Materias (temas) de Documentos Judiciales Peruanos

## Técnica de extracción

Los PDFs judiciales peruanos del Poder Judicial contienen un campo `MATERIA` 
en la carátula (primeras líneas del documento, típicamente línea 3-5 después 
del juzgado). Extraer con:

```python
import re
pat_materia = re.compile(r'MATERIA\s*:?\s*(.+?)(?:\n|$)', re.IGNORECASE)
```

## Variantes encontradas

El campo MATERIA aparece en estos formatos:

```
MATERIA: OBLIGACION DE DAR SUMA DE DINERO          ← formato standard
MATERIA : EJECUCION DE GARANTIAS                    ← con espacio antes de :
MATERIA                                              ← materia en la SIGUIENTE línea
: REPOSICION
MATERIA: PAGO DE BENEFICIOS SOCIALES Y/O
INDEMNIZACION U OTROS BENEFICIOS ECONOMICOS         ← multilinea
```

## Ejemplos de materias por categoría de juzgado

### Juzgados Civiles / Comerciales
- OBLIGACION DE DAR SUMA DE DINERO
- EJECUCION DE GARANTIAS
- INDEMNIZACION
- RESOLUCION DE CONTRATO
- NULIDAD DE ACTO JURIDICO
- PRESCRIPCION ADQUISITIVA
- DESALOJO
- MEJOR DERECHO A LA PROPIEDAD

### Juzgados Laborales
- PAGO DE BENEFICIOS SOCIALES
- REPOSICION
- CESE DE ACTOS DE HOSTILIDAD DEL EMPLEADOR
- PAGO DE REMUNERACIONES
- INDEMNIZACION POR DESPIDO
- DESNATURALIZACION DE CONTRATO

### Juzgados de Familia
- ALIMENTOS
- DIVORCIO
- TENENCIA
- REGIMEN DE VISITAS
- FILIACION

### Juzgados Contencioso Administrativo
- NULIDAD DE RESOLUCION O ACTO ADMINISTRATIVO
- IMPUGNACION DE ACTO ADMINISTRATIVO
- ACCION POPULAR

### Juzgados Constitucionales
- ACCION DE AMPARO
- HABEAS CORPUS

### Penal
- DELITO CONTRA LA ADMINISTRACION PUBLICA
- Violencia Familiar (etiqueta del juzgado)

## Valor para RAG

El campo MATERIA permite filtrado temático de documentos para el RAG:

- Consulta sobre "despido arbitrario" → priorizar REPOSICION, CESE DE ACTOS 
  DE HOSTILIDAD, INDEMNIZACION POR DESPIDO
- Consulta sobre "deuda bancaria" → priorizar OBLIGACION DE DAR SUMA, 
  EJECUCION DE GARANTIAS
- Consulta sobre "proceso administrativo" → priorizar NULIDAD DE RESOLUCION
  O ACTO ADMINISTRATIVO

## Distribución real (jun 2026, 435,404 sentencias + resoluciones)

Extraído con `pdftotext` (página 1) + 8 workers paralelos en ~15 min.
92.8% de los documentos tenían el campo MATERIA detectable.

| Materia | Cantidad | % | Área Legal |
|---|---|---|---|
| OBLIGACION DE DAR SUMA DE DINERO | 81,432 | 18.7% | Civil |
| EJECUCION DE GARANTIAS | 53,252 | 12.2% | Comercial |
| NULIDAD DE RESOLUCIÓN O ACTO ADMINISTRATIVO | 24,919 | 5.7% | Contencioso Admin |
| DERECHOS LABORALES | 16,106 | 3.7% | Laboral |
| REINTEGRO DE REMUNERACIONES | 11,249 | 2.6% | Laboral |
| DESNATURALIZACIÓN DE CONTRATO | 10,273 | 2.4% | Laboral |
| PAGO DE BENEFICIOS SOCIALES Y/O INDEMNIZACION | 9,753 | 2.2% | Laboral |
| REPOSICION | 6,314 | 1.5% | Laboral |
| ACCION DE AMPARO | 5,466 | 1.3% | Constitucional |
| MEDIDA CAUTELAR | 5,152 | 1.2% | Civil |
| PAGO DE UTILIDADES | 4,853 | 1.1% | Laboral |
| ACCION CONTENCIOSA ADMINISTRATIVA | 4,539 | 1.0% | Contencioso Admin |
| OBLIGACIONES DE DAR HASTA 50 URP | 4,956 | 1.1% | Civil |
| INDEM. POR DAÑOS Y PERJUICIOS POR INCUMP. | 4,520 | 1.0% | Civil |
| INCAUTACION DE BIEN MUEBLE | 4,366 | 1.0% | Civil |
| PAGO DE REMUNERACIONES | 2,511 | 0.6% | Laboral |
| IMPUGNACION DE DESPIDO | 2,421 | 0.6% | Laboral |
| CESE DE ACTOS DE HOSTILIDAD DEL EMPLEADOR | 1,348 | 0.3% | Laboral |
| DESALOJO | 1,172 | 0.3% | Civil |
| VIOLENCIA FAMILIAR | 657 | 0.2% | Familia |
| PRESCRIPCION ADQUISITIVA | 668 | 0.2% | Civil |

**9,295 materias únicas** en total (muchas son variantes de una misma, ej: 8 formas de "OBLIGACION DE DAR SUMA DE DINERO"). El JSON completo está en `data/materias_sentencias_resoluciones.json`.

**Para reducir:** agrupar las variantes con normalización: eliminar puntuación, acentos, espacios múltiples, abreviaturas. Las ~9,295 se reducen a ~200-300 materias reales.

## Áreas legales dominantes (estimado)

| Área Legal | % aprox | Materias representativas |
|---|---|---|
| Civil (cobranzas, daños, propiedad) | ~55% | OBLIGACION DE DAR SUMA, MEDIDA CAUTELAR, INDEMNIZACION, DESALOJO, PRESCRIPCION |
| Laboral (beneficios, reposición, despido) | ~20% | DERECHOS LABORALES, REPOSICION, PAGO BENEFICIOS, DESNATURALIZACION |
| Comercial/Bancario (garantías, títulos) | ~15% | EJECUCION DE GARANTIAS, INEFICACIA DE TITULO VALOR |
| Contencioso Administrativo | ~8% | NULIDAD DE RESOLUCION ADMINISTRATIVA, ACCION CONTENCIOSA |
| Constitucional | ~2% | ACCION DE AMPARO, HABEAS DATA |
| Familia | ~1% | VIOLENCIA FAMILIAR, PENSIONES |

## Nota

La distribucion cuantitativa completa de materias (~375K documentos) se 
genera con el script de extraccion batch. Los datos definitivos se 
guardan en data/materias_sentencias_resoluciones.json del proyecto.
