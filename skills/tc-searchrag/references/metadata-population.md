# Metadata Population Stats — TC SearchRAG

Verificado contra metadata.jsonl real (11,483 documentos, Jun 2026).

## Por campo

| Campo | Poblado | % | Notas |
|-------|---------|---|-------|
| `archivo` | 11,483 | 100% | Nombre del PDF |
| `materia` | 11,483 | 100% | **Filtro más fiable** |
| `tipo_fallo` | 11,483 | 100% | Sentencia (9,601), Auto (1,659), Desconocido (165), Resolución (58) |
| `snippet` | 11,483 | 100% | Primeros chars del documento |
| `paginas` | 11,483 | 100% | Páginas del PDF |
| `palabras` | 11,483 | 100% | Conteo de palabras |
| `chars` | 11,483 | 100% | Conteo de caracteres |
| `fuente` | 11,483 | 100% | "TC 2005 (Original)" o "TC SEDETC" |
| `materia_confianza` | 11,483 | 100% | "regex", "groq", etc. |
| `anio` | 10,075 | 88% | Rango: 2005→2025. 13 años únicos |
| `tipo` | 10,075 | 88% | AA (5,209), HC (3,698), AC (672), Queja (242), HD (190), AI (54), CC (10) |
| `exp` | 10,075 | 88% | N° expediente (ej: "00001-2005-PA/TC") |
| `fecha` | 10,918 | 95% | **Subió de 78% tras backfill** — se agregó regex para "Lima, X de mes de AÑO" |
| `sala` | 8,371 | 73% | Primera, Segunda, Plena |
| `jueces` | 2,170 | 19% | Solo documentos que mencionan magistrados explícitamente |
| `subtipo` | 994 | 9% | Interlocutoria, Resolución, etc. |
| `departamento` | **2** | **0.02%** | **Filtro inútil** — casi ningún PDF trae ubicación estructurada |

## Top materias

| Materia | Docs |
|---------|:----:|
| Procesal Constitucional | 8,024 |
| Libertad Personal | 919 |
| Pensiones | 527 |
| Debido Proceso | 417 |
| Salud | 316 |
| Administrativo | 306 |
| Civil | 241 |
| Seguridad Social | 140 |
| Electoral | 122 |
| Laboral | 77 |

## Tipos de proceso

| Tipo | Docs |
|------|:----:|
| Acción de Amparo (AA) | 5,209 |
| Hábeas Corpus (HC) | 3,698 |
| Acción de Cumplimiento (AC) | 672 |
| Queja (Q) | 242 |
| Hábeas Data (HD) | 190 |
| Acción de Inconstitucionalidad (AI) | 54 |
| CC | 10 |

## Tipos de fallo

| Fallo | Docs |
|-------|:----:|
| Sentencia | 9,601 |
| Auto | 1,659 |
| Desconocido | 165 |
| Resolución | 58 |

## Fechas

- Rango: 2000-03-29 → 2026-02-25
- 582 valores únicos
- **Dos formatos en PDFs:**
  1. **Formato Pleno** (capturado actualmente): `"En Lima, a los X días del mes de Y de ZZZZ"` — aparece en AI, CC, sentencias de fondo
  2. **Formato estándar** (NO capturado): `"Lima, 5 de marzo de 2019"` — formato común en Autos, Resoluciones, Interlocutorias (mayoría)
- ~2,530 documentos sin fecha, de los cuales la mayoría probablemente tiene formato #2 que la regex no captura

## Años

- 2005 → 2025 (13 años únicos)
- 88% de los documentos tienen año poblado
- El año se extrae del nombre del archivo (directorio/path), no del texto, por eso tiene mayor cobertura que fecha
