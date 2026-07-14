# Normalización de Materias Judiciales

> Distribución real extraída de 404,011 sentencias + resoluciones (jun 2026).
> 9,295 materias originales → 3,980 normalizadas → 9 áreas legales.

## Áreas legales (distribución real)

| Área Legal | Docs | % del total |
|---|---|---|
| CIVIL | 116,117 | 28.7% |
| LABORAL | 106,268 | 26.3% |
| COMERCIAL | 62,523 | 15.5% |
| CONTENCIOSO ADMINISTRATIVO | 53,093 | 13.1% |
| OTROS (no normalizadas) | 49,490 | 12.2% |
| CONSTITUCIONAL | 7,465 | 1.8% |
| PENAL | 4,449 | 1.1% |
| FAMILIA | 2,610 | 0.6% |
| SIN CLASIFICAR | 1,002 | 0.2% |

## Materias normalizadas por área legal

### CIVIL (116,117 docs)

| Materia | Docs | % del área |
|---|---|---|
| OBLIGACION DE DAR SUMA DE DINERO | 92,102 | 79.3% |
| MEDIDA CAUTELAR | 6,853 | 5.9% |
| OBLIGACION DE DAR SUMA (HASTA 50 URP) | 4,958 | 4.3% |
| CONSIGNACION | 2,441 | 2.1% |
| INDEMNIZACION | 2,437 | 2.1% |
| OBLIGACION DE DAR BIEN MUEBLE | 1,385 | 1.2% |
| PRUEBA ANTICIPADA | 1,224 | 1.1% |
| DESALOJO | 1,205 | 1.0% |
| TERCERIA | 966 | 0.8% |
| NULIDAD DE ACTO JURIDICO | 811 | 0.7% |
| PRESCRIPCION ADQUISITIVA | 698 | 0.6% |
| REIVINDICACION | 634 | 0.5% |
| MEJOR DERECHO A LA PROPIEDAD | 403 | 0.3% |

### LABORAL (106,268 docs)

| Materia | Docs | % del área |
|---|---|---|
| PAGO DE BENEFICIOS SOCIALES | 37,569 | 35.4% |
| DERECHOS LABORALES | 16,396 | 15.4% |
| REINTEGRO DE REMUNERACIONES | 12,990 | 12.2% |
| DESNATURALIZACION DE CONTRATO | 12,011 | 11.3% |
| REPOSICION | 7,393 | 7.0% |
| PAGO DE UTILIDADES | 4,877 | 4.6% |
| INDEMNIZACION POR DESPIDO ARBITRARIO | 3,120 | 2.9% |
| INCUMPLIMIENTO DE NORMAS LABORALES | 2,807 | 2.6% |
| PAGO DE REMUNERACIONES | 2,620 | 2.5% |
| IMPUGNACION DE DESPIDO | 2,497 | 2.3% |
| CESE DE ACTOS DE HOSTILIDAD | 1,672 | 1.6% |
| NULIDAD DE DESPIDO | 1,536 | 1.4% |
| CREDITOS LABORALES | 780 | 0.7% |

### COMERCIAL (62,523 docs)

| Materia | Docs | % del área |
|---|---|---|
| EJECUCION DE GARANTIAS | 55,753 | 89.2% |
| ANULACION DE LAUDO ARBITRAL | 3,123 | 5.0% |
| EJECUCION DE LAUDOS ARBITRALES | 2,506 | 4.0% |
| INEFICACIA DE TITULO VALOR | 1,141 | 1.8% |

### CONTENCIOSO ADMINISTRATIVO (53,093 docs)

| Materia | Docs | % del área |
|---|---|---|
| NULIDAD DE RESOLUCION O ACTO ADMINISTRATIVO | 35,918 | 67.7% |
| ACCION CONTENCIOSA ADMINISTRATIVA | 8,082 | 15.2% |
| IMPUGNACION DE ACTO O RESOLUCION ADMINISTRATIVA | 4,489 | 8.5% |
| NULIDAD DE ACTO ADMINISTRATIVO | 2,578 | 4.9% |
| IMPUGNACION DE ACTO ADMINISTRATIVO | 1,322 | 2.5% |
| EJECUCION DE RESOLUCION ADMINISTRATIVA | 704 | 1.3% |

### CONSTITUCIONAL (7,465 docs)

| Materia | Docs | % del área |
|---|---|---|
| ACCION DE AMPARO | 6,806 | 91.2% |
| HABEAS DATA | 659 | 8.8% |

### PENAL (4,449 docs)

| Materia | Docs | % del área |
|---|---|---|
| INCAUTACION DE BIEN | 4,449 | 100% |

### FAMILIA (2,610 docs)

| Materia | Docs | % del área |
|---|---|---|
| PENSIONES | 1,952 | 74.8% |
| VIOLENCIA FAMILIAR | 658 | 25.2% |

## Reglas de normalización aplicadas

### Limpieza general
- `Ó` → `O`, `Í` → `I`, `É` → `E`, `Á` → `A`, `Ú` → `U`
- `N°` → `NUMERO`, `NRO` → `NUMERO`, `No.` → `NUMERO`
- Eliminar puntuación extraña: `﹒•·`
- Unificar espacios múltiples

### Agrupación por patrón regex

Las materias se agrupan buscando el primer patrón que matchea (orden de especificidad descendente):

1. **"OBLIGACION DE DAR SUMA DE DINERO"** captura:
   - "OBLIGACION DE DAR SUMA DE DINERO"
   - "OBLIGACION DE DAR SUMA DE DINERO INICIADAS POR AFPS"
   - "OBLIGACIÓN DE DAR SUMA DE DINERO"
   - "OBLIGACION DE DAR SUMA DE"
   - "OBLIGACION DE DAR"

2. **"NULIDAD DE RESOLUCION O ACTO ADMINISTRATIVO"** captura:
   - "NULIDAD DE RESOLUCIÓN O ACTO ADMINISTRATIVO"
   - "NULIDAD DE RESOLUCION ADMINISTRATIVA"
   - "NULIDAD DE RESOLUCIÓN ADMINISTRATIVA."
   - "NULIDAD RESOLUCIÓN O ACTO ADMINISTRATIVO"

3. **"PAGO DE BENEFICIOS SOCIALES"** captura:
   - "PAGO DE BENEFICIOS SOCIALES Y/O INDEMNIZACION"
   - "PAGO DE BENEFICIOS SOCIALES Y/O INDEMNIZACION U OTROS BENEFICIOS ECONOMICOS"
   - "PAGO DE BENEFICIOS SOCIALES Y OTROS"
   - "PAGO DE BENEFICIOS ECONOMICOS"

## Valor para RAG

El lookup table completo está en el JSON de normalización. Para usarlo:

```python
import json

with open('reports/normalizacion_materias.json') as f:
    data = json.load(f)

# Dado el MATERIA de un documento, obtener área legal
area = data['lookup'].get('OBLIGACION DE DAR SUMA DE DINERO')
# → {'materia': 'OBLIGACION DE DAR SUMA DE DINERO', 'area': 'CIVIL'}
```

Esto permite filtrar documentos en el RAG por área legal sin reprocesar:
- Consulta laboral → solo documentos con `lookup[doc.materia]['area'] == 'LABORAL'`
