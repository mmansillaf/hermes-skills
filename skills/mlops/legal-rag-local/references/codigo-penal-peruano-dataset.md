# Código Penal Peruano — Dataset Estructurado (JSON)

## Estado actual (Julio 2026)

**NO existe un dataset público del Código Penal Peruano en formato JSON/XML/CSV.**

Búsquedas realizadas:
- GitHub: 0 repositorios con "codigo penal peruano json"
- HuggingFace: 0 datasets. Existe `bowang0911/PeruvianConstitutionChunkRetrieval` (Constitución, no Código Penal)
- Plataforma Nacional de Datos Abiertos (datosabiertos.gob.pe): 0 datasets específicos
- awesome-legal-data (263⭐): Perú NO aparece representado

## Estructura JSON recomendada (validada en MVP)

```json
{
  "id": "art_108b",
  "numero": "108-B",
  "titulo": "Feminicidio",
  "libro": "II",
  "titulo_libro": "Parte Especial — Delitos",
  "capitulo": "I",
  "titulo_capitulo": "Homicidio",
  "texto": "Será reprimido con pena privativa de libertad no menor de veinte años...",
  "incisos": [
    {"numero": 1, "texto": "..."}
  ],
  "vigencia": {"inicio": "2013-07-18", "fin": null},
  "modificaciones": [
    {"fecha": "2013-07-18", "ley": "Ley 30068", "descripcion": "Incorporación del artículo.", "tipo": "incorporacion"},
    {"fecha": "2018-08-02", "ley": "Ley 30819", "descripcion": "Eleva la pena mínima de 15 a 20 años.", "tipo": "modificacion"}
  ],
  "status": "vigente",
  "jurisprudencia_vinculada": ["Acuerdo Plenario 1-2016/CJ-116", "Casación 851-2018-Puno"],
  "doctrina_relacionada": ["Dra. Yolanda Doig Díaz — El Feminicidio en el Perú"]
}
```

## Artículos incluidos en el MVP (20 artículos)

| ID | Artículo | Libro | Pena |
|----|----------|:----:|------|
| art_1 | Principio de Legalidad | I | — |
| art_16 | Tentativa | I | Reducción prudencial |
| art_16a | Tentativa en Delitos Graves | I | ≤1/3 del mínimo |
| art_45 | Clases de Pena | I | — |
| art_46 | Determinación Judicial de la Pena | I | Criterios judiciales |
| art_57 | Suspensión de la Ejecución | I | ≤4 años, exclusiones Ley 32258 |
| art_84 | Prescripción de la Acción Penal | I | =máx pena, 3-30 años |
| art_106 | Homicidio Simple | II | 6-20 años |
| art_107 | Parricidio | II | ≥15 años |
| art_108 | Homicidio Calificado | II | ≥15 años |
| art_108b | Feminicidio | II | ≥20 años |
| art_108c | Sicariato | II | ≥25 años |
| art_121 | Lesiones Graves | II | 4-8 años |
| art_185 | Hurto Simple | II | 1-3 años |
| art_186 | Hurto Agravado | II | 3-6 años |
| art_188 | Robo | II | 3-8 años |
| art_189 | Robo Agravado | II | ≥12 años |
| art_196 | Estafa | II | 1-6 años |
| art_384 | Colusión | II | 3-6 años |
| art_387 | Peculado | II | 4-8 años |

## Fuentes de texto verificable

- SPIJ (MINJUS): https://spijweb.minjus.gob.pe — requiere login, sin API
- LP Derecho: https://lpderecho.pe/codigo-penal-peruano-actualizado/ — Cloudflare, requiere bypass
- El Peruano: https://busquedas.elperuano.pe — acceso libre, HTML+PDF
- Congreso: https://www.leyes.congreso.gob.pe — acceso libre

## Chunking para RAG

Para el MVP se usó chunking por artículo completo (text search: "Artículo X: Título. Texto. Inciso 1: texto.").
Para producción con 50K+ documentos, usar Paragraph Group Chunking (nDCG@5 ~0.459 vs <0.244 fixed-size).

## Embeddings usados

MVP: `intfloat/multilingual-e5-large` (1024-dim, CPU, 20 artículos → ~28s encoding)
Recomendado para producción: `wilfredomartel/BGE-M3-Legal-Spanish` (1024-dim, 8192 ctx, fine-tuned español legal)
