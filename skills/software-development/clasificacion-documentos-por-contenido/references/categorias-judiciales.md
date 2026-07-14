# Categorías y Patrones para Documentos Judiciales Peruanos

Basado en clasificación real de **479,817 PDFs** del Poder Judicial del Perú.
Extraídos de juzgados laborales, civiles, contencioso-administrativos a nivel nacional.
Dataset: 72 GB, ejecutado a ~185 docs/s con pymupdf (~43 min en total).

## Patrones Regex por Categoría (orden de prioridad)

### Sentencia (~43.4%)
```python
r'\bSENTENCIA\b'
r'\bFALLO\b'
r'SE RESUELVE\b.*?(?:\n|$)'
# NOTA: "VISTA LA CAUSA" fue movido a acta_audiencia — es más específico allí
```

### Notificación (~8.0%)
```python
r'C[EÉ]DULA\s+DE\s+NOTIFICACI[OÓ]N'
r'CEDULA\s+DE\s+NOTIFICACION'
r'NOTIFIQU[EÉ]SE'
r'NOTIFICACI[OÓ]N\s+ELECTR[OÓ]NICA'
```

### Citación (~0.6%)
```python
r'\bCITO\b'
r'CITACI[OÓ]N\b'
r'C[IÍ]TESE'  # CÍTESE (tildada) y CITESE (sin)
```

### Oficio (~2.8%)
Incluye tanto N° como No. (con punto):
```python
r'OFICIO\s+N[°º]\s*\d+'      # OFICIO N° 2217
r'OFICIO\s+No\.?-?\s*\d+'    # OFICIO No.- 2217-2020 (con guión)
r'OFICIO\s+M[UÚ]LTIPLE'
r'OFICIO\s+CIRCULAR'
```

### Acta de Audiencia (nueva, rescatada de no_clasificados)
```python
r'ACTA\s+DE\s+(?:VISTA|REGISTRO\s+DE\s+AUDIENCIA|AUDIENCIA)'
r'AUDIENCIA\s+(?:ÚNICA|PUBLICA|PROGRAMADA)'
r'VISTA\s+DE\s+LA\s+CAUSA'
r'ACTA\s+DE\s+INFORME\s+ORAL'
```

### Pericia (~1.1%)
```python
r'INFORME\s+PERICIAL'
r'DICTAMEN\s+PERICIAL'
r'PERICIA\b'
```

### Conciliación (~1.3%)
```python
r'ACTA\s+DE\s+CONCILIACI[OÓ]N'
r'AUDIENCIA\s+DE\s+CONCILIACI[OÓ]N'
r'CONCILIACION\s+EXTRAJUDICIAL'
```

### Demanda (~2.7%)
```python
r'INTERPONE\s+DEMANDA'
r'ESCRITO\s+DE\s+DEMANDA'
r'ADMITIR\s+(?:A\s+)?TR[ÁA]MITE\s+LA\s+DEMANDA'
```

### Resolución - Admite Trámite (~0.2%)
```python
r'ADMITIR\s+(?:A\s+)?TR[ÁA]MITE'
r'ADM[IÍ]TASE'
```

### Resolución - Archivo (~0.8%)
```python
r'ARCH[IÍ]VESE'
r'DASE\s+POR\s+CONCLUIDO'
```

### Resolución - Remite/Eleva (~1.5%)
```python
r'REM[IÍ]TASE'
r'ELEVAR\s+LOS\s+AUTOS'
r'ELEVASE'
```

### Resolución Genérica (~34.5%) — VERSION AMPLIADA
Cubre todas las variantes encontradas en 479K+ documentos:

```python
# Formato standard: NÚMERO / N° / Nro. + dígito
r'RESOLUCI[OÓ]N\s+N[UÚ]MERO\s+'
r'RESOLUCION\s+NUMERO\s+'
r'RESOLUCI[OÓ]N\s+N[°º]\s*\d+'
r'RESOLUCION\s+N[°º]\s*\d+'
r'RESOLUCI[OÓ]N\s+NRO\.?\s*\d+'       # Nro. 12 o NRO 10
r'RESOLUCION\s+NRO\.?\s*\d+'

# Variante: No. + dígito
r'RESOLUCI[OÓ]N\s+No\.\s*\d+'         # RESOLUCIÓN No. 04
r'RESOLUCION\s+No\.\s*\d+'

# Variante: Nro/No + número en LETRAS
r'RESOLUCI[OÓ]N\s+(NRO|NO\.?)'        # RESOLUCIÓN Nro Ocho
r'\s+(UNO|DOS|TRES|CUATRO|CINCO|SEIS|SIETE|OCHO|NUEVE|DIEZ'
r'|ONCE|DOCE|TRECE|CATORCE|QUINCE|VEINTE|TREINTA'
r'|PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA'
r'|S[EÉ]PTIMA|OCTAVA|NOVENA|D[EÉ]CIMA)'

# Variante: solo dígito en línea propia (sin N° ni Nro)
r'^RESOLUCI[OÓ]N\s+\d+\s*$'           # "RESOLUCIÓN 19"
r'^RESOLUCION\s+\d+\s*$'

# Variante: número en la SIGUIENTE línea
r'^RESOLUCI[OÓ]N\s*$'                 # "RESOLUCIÓN\n09"
r'^RESOLUCION\s*$'
```

## Ejemplos de texto real de documentos no_clasificados (rescatados)

### 1. Resolución con número en letras
```
Resolución Nro Ocho
Callao, veintidós de febrero del dos mil veintidós
→ Contenido: provee escrito de contestación de demanda. 1 página. INTERLOCUTORIA.

RESOLUCIÓN No. QUINCE
San Isidro, cinco de diciembre de dos mil veintitrés.
→ Contenido: requiere expediente administrativo, cita Resolución Administrativa
  N° 228-2017-CE-PJ, apercibimiento. 1 página. COMPLETA (con fundamentos).

RESOLUCIÓN No. UNO
Lima, veintiséis de abril de dos mil veintidós.
→ Acción de Amparo, analiza nuevo Código Procesal Constitucional (Ley 31307).
  3 páginas con considerandos. COMPLETA. ALTO VALOR.
```

### 2. Resolución con solo dígito (sin N°/Nro)
```
Resolución 3
Lima, seis de abril del dos mil veintidós
→ "Téngase presente". 1 página. INTERLOCUTORIA.

Resolución 24
Lima, nueve de octubre del dos mil diecinueve
→ Provee escrito. 1 página. INTERLOCUTORIA.

Resolución 07
Lima, 14 de julio de dos mil veintidós
→ Sala Laboral, programa vista de causa, cita Ley N° 27584 y D.S. N° 003-2015-JUS.
  3 páginas. COMPLETA.
```

### 3. Acta de Audiencia
```
ACTA DE VISTA DE LA CAUSA
→ [NULIDAD DE RESOLUCIÓN] Corte Superior de Piura, 15 jul 2024. 1 página.

ACTA DE REGISTRO DE AUDIENCIA ÚNICA (VIRTUAL)
→ [REPOSICION] 2° Juzgado Paz Letrado del Santa, 20 oct 2022. 2 páginas.

ACTOS PREPARATORIOS DE LA AUDIENCIA VIRTUAL
→ [NULIDAD ACTO ADMINISTRATIVO] Indecopi vs Aceros Arequipa. 4 páginas.
```

### 4. Oficio con "No." (con punto)
```
OFICIO No.- 2217-2020-CI-7MO JPLL/AAD.
→ Remite expediente a Juzgado correspondiente. 1 página.
```

## Resultados de reclasificación (esta sesión, jun 2026)

La reclasificación de `no_clasificado/` con los patrones ampliados produjo:

| Resultado | Cantidad | Destino |
|---|---|---|
| Resoluciones recuperadas | 1,417 | → `Clasificados/Resolución/` |
| Actas de Audiencia | 3,393 | → `Clasificados/Acta_de_Audiencia/` |
| Siguen sin clasificar | 12,248 | permanecen en `no_clasificado/` |
| **Total** | **17,058** | |

De las 1,417 resoluciones recuperadas, ~1,000 son completas (3+ páginas con CONSIDERANDOS, alto valor RAG) y ~400 interlocutorias (1-2 páginas, trámite).

Las 12,248 que siguen sin clasificar son principalmente: metadata SINOE (notificaciones electrónicas), carátulas de 1 página sin texto resolutivo, y oficios con formatos muy atípicos. Su valor jurídico es muy bajo — no vale la pena seguir procesándolas.

## Distribución real (479,817 archivos clasificados, primera pasada + reclasificación)

| Categoría               | Cantidad   | %      |
|-------------------------|-----------|--------|
| Sentencia               | 208,149   | 43.4%  |
| Resolución (genérica)   | 165,388   | 34.5%  |
| Notificación            | 38,366    | 8.0%   |
| no_clasificado          | 17,055    | 3.6%   |
| Oficio                  | 13,454    | 2.8%   |
| Demanda                 | 12,948    | 2.7%   |
| Resolución - Remite     | 6,998     | 1.5%   |
| Conciliación            | 6,255     | 1.3%   |
| Pericia                 | 5,101     | 1.1%   |
| Resolución - Archivo    | 3,865     | 0.8%   |
| Citación                | 2,827     | 0.6%   |
| Resolución - Admite     | 1,052     | 0.2%   |
| Sin texto               | 8         | ~0%    |
| Error lectura           | 3         | ~0%    |
| **Total**               | **479,817** | 100% |

## Desglose de "no_clasificado" (17,058 archivos)

**⚠️ NO confiar en estimaciones de muestra pequeña.** La muestra inicial de 200 sugería ~32% resoluciones atípicas (~5,500), pero la **reclasificación real de los 17,058 completos** demostró que solo ~8.3% (1,417) eran resoluciones. La diferencia se debe a que el clasificador base ya capturaba la mayoría de los casos de "Resolución Nro" con patrones parciales. **Siempre reclasificar el lote completo antes de reportar.**

Resultados reales de la reclasificación:

| Resultado | Cantidad | % real | Valor RAG |
|---|---|---|---|
| Acta de Audiencia | 3,393 | 19.9% | Bajo (actas procesales) |
| Resolución (atípicas recuperadas) | 1,417 | 8.3% | **Alto** (~1,000 completas con considerandos) |
| Aún sin clasificar (carátulas/SINOE) | 12,248 | 71.8% | Nulo (1 página, solo metadata) |
| **Total** | **17,058** | **100%** | |

Las 12,248 que siguen sin clasificar son principalmente: metadata del sistema de notificaciones SINOE (firmas digitales), carátulas de 1 página con solo datos del caso sin texto resolutivo, y oficios con formatos muy atípicos. Su valor jurídico es muy bajo para RAG — no vale la pena seguir procesándolas.

## Naming de archivos detectados

Dos formatos:
1. **Formato expediente** (~130K): `00001-2018-0-1706-JP-LA-01 document_N.pdf`
   - JP=Juzgado Paz, JR=Juzgado Referencia, LA=Laboral, CA=Contencioso Admin
2. **Formato res_id** (~428K): `res_2023106610010109000269153.pdf`

## Notas técnicas

- **Tasa de error en 479,817 PDFs**: solo 8 sin texto extraíble y 3 errores de lectura (~0.002%).
- **Reclasificación**: el script `scripts/reclasificar.py` procesa solo `no_clasificado/` aplicando los patrones expandidos, moviendo symlinks y generando reportes separados.
- **Recomendación**: después de reclasificar con patrones expandidos, el remanente (~29% carátulas/SINOE) probablemente no merece esfuerzo adicional — son documentos de 1 página sin contenido resolutivo.
