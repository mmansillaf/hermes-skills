# Peruvian Judicial Document Classification Patterns

Regex patterns and category definitions for classifying Peruvian court documents (Poder Judicial).
Tested against ~558K PDFs from expedientes laborales, contencioso-administrativos, and civiles.

## Document Types

| Category | Friendly Name | Description |
|----------|--------------|-------------|
| sentencia | Sentencia | Final judgment — "FALLO", "VISTA LA CAUSA", "SE RESUELVE" |
| resolucion_generica | Resolución | Generic ruling — "RESOLUCIÓN NÚMERO", "RESOLUCIÓN N°" |
| notificacion | Notificación | Service of process — "CÉDULA DE NOTIFICACIÓN", "NOTIFIQUESE" |
| citacion | Citación | Summons to appear — "CITO", "CÍTESE" |
| oficio | Oficio | Official communication between courts — "OFICIO N°" |
| pericia | Pericia | Expert report — "INFORME PERICIAL", "DICTAMEN PERICIAL" |
| conciliacion | Conciliación | Settlement/mediation — "ACTA DE CONCILIACIÓN", "AUDIENCIA DE CONCILIACIÓN" |
| demanda | Demanda | Initial complaint filing — "INTERPONE DEMANDA", "ESCRITO DE DEMANDA" |
| resolucion_admite | Admite Trámite | Admit to proceed — "ADMITIR TRÁMITE", "ADMÍTASE" |
| resolucion_archivo | Archivo | File closing — "ARCHÍVESE", "DASE POR CONCLUIDO" |
| resolucion_remite | Remite/Eleva | Send to higher court — "REMÍTASE", "ELEVAR LOS AUTOS" |

## Regex Patterns (ordered by priority — most specific first)

```python
CATEGORIES = {
    "sentencia": [
        r'\bSENTENCIA\b',
        r'\bFALLO\b',
        r'VISTA LA CAUSA',
        r'SE RESUELVE\b.*?(?:\n|$)',
    ],
    "notificacion": [
        r'C[EÉ]DULA\s+DE\s+NOTIFICACI[OÓ]N',
        r'CEDULA\s+DE\s+NOTIFICACION',
        r'NOTIFIQU[EÉ]SE',
        r'NOTIFICACI[OÓ]N\s+ELECTR[OÓ]NICA',
    ],
    "citacion": [
        r'\bCITO\b',
        r'CITACI[OÓ]N\b',
        r'C[IÍ]TESE',
    ],
    "oficio": [
        r'OFICIO\s+N[°º]\s*\d+',
        r'OFICIO\s+M[UÚ]LTIPLE',
        r'OFICIO\s+CIRCULAR',
    ],
    "pericia": [
        r'INFORME\s+PERICIAL',
        r'DICTAMEN\s+PERICIAL',
        r'PERICIA\b',
    ],
    "conciliacion": [
        r'ACTA\s+DE\s+CONCILIACI[OÓ]N',
        r'ACTA\s+DE\s+CONCILIACION',
        r'AUDIENCIA\s+DE\s+CONCILIACI[OÓ]N',
        r'CONCILIACION\s+EXTRAJUDICIAL',
    ],
    "demanda": [
        r'INTERPONE\s+DEMANDA',
        r'ESCRITO\s+DE\s+DEMANDA',
        r'ADMITIR\s+(?:A\s+)?TR[ÁA]MITE\s+LA\s+DEMANDA',
    ],
    "resolucion_archivo": [
        r'ARCH[IÍ]VESE',
        r'DASE\s+POR\s+CONCLUIDO',
    ],
    "resolucion_remite": [
        r'REM[IÍ]TASE',
        r'ELEVAR\s+LOS\s+AUTOS',
        r'ELEVASE',
    ],
    "resolucion_admite": [
        r'ADMITIR\s+(?:A\s+)?TR[ÁA]MITE',
        r'ADM[IÍ]TASE',
    ],
    "resolucion_generica": [
        r'RESOLUCI[OÓ]N\s+N[UÚ]MERO',
        r'RESOLUCION\s+NUMERO',
        r'RESOLUCI[OÓ]N\s+N[°º]',       # "N° 15" or "Nº 15"
        r'RESOLUCION\s+N[°º]',
        r'RESOLUCI[OÓ]N\s+NRO\.',
    ],
}
```

## Observed Distribution (558K Peruvian Labor/Administrative Docs)

| Category | % of Total |
|----------|-----------|
| Sentencia | 43.6% |
| Resolución (genérica) | 34.2% |
| Notificación | 8.0% |
| Oficio | 3.0% |
| Demanda | 2.9% |
| Remite/Eleva | 1.4% |
| Conciliación | 1.4% |
| Pericia | 1.0% |
| Archivo | 0.8% |
| Citación | 0.6% |
| Admite Trámite | 0.2% |
| No clasificado (regex missed) | 3.1% |

## Key Insights from ~558K Document Analysis

1. **Documentos por expediente**: Each case (expediente) has 10-36 separate PDFs — each is a different procedural step.
2. **Dual naming convention**: ~130K use `00001-2018-0-1706-JP-LA-01 document_N.pdf` (expediente format), ~428K use `res_ID.pdf` (unified upload format).
3. **Most common matter**: PAGO DE BENEFICIOS SOCIALES (labor claims).
4. **"Resolución N°" vs "RESOLUCIÓN NÚMERO"**: Both forms appear frequently. Match both.
5. **Text duplication**: Many PDFs repeat every line 2-4x on the same page due to PDF generation artifacts. Case-insensitive regex still works because the pattern appears in each repetition.
