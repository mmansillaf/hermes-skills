# Fuentes de Datos Legales Peruanos

Investigación realizada el 2026-07-02 sobre datasets, APIs y recursos para construir un RAG del Código Penal Peruano.

## Datasets en HuggingFace

### Específicamente peruanos (legales)
| Dataset | Filas | Descargas | Descripción |
|---------|:-----:|:---------:|-------------|
| `bowang0911/PeruvianConstitutionChunkRetrieval` | 10.4K | 46 | Constitución Peruana en chunks (Parquet). Columnas: chunk_id, chunk, source_url, title, chunk_idx. Subsets: documents-64/128/256/512, queries |
| `pyupeu/social-media-peruvian-sentiment` | 14.6K | 36 | Sentiment en redes sociales peruanas |

### Datasets legales en español (no peruanos)
| Dataset | Filas | Descargas | Descripción |
|---------|:-----:|:---------:|-------------|
| `Ramitha/spanish-legal-data` | 16.9M | 66 | Datos legales españoles masivos |
| `wilfredomartel/small-spanish-legal-dataset` | 11.2K | 25 | Dataset para entrenar embeddings legales (query/pos/neg). JSON, ODC-BY |
| `Pepere45/spanish-boe-legal-corpus` | - | 10 | Corpus del BOE español |
| `hugoramallo/legal-ai-act-spanish-sft-7k` | 7.44K | 20 | AI Act EU en español |
| `mrm8488/spanish_legal_ds_tokenized_and_gropuped` | 1.91M | 34 | Datos legales tokenizados |
| `celsowm/codigo_penal_brasileiro_lei_2848_1940` | 412 | 106 | Código Penal Brasileño (referencia de estructura) |
| `jjovalle99/codigo_penal` | 551 | 3 | Código Penal Colombiano (columnas: articulo, text, tokens) |

## Modelos de Embedding para Español Legal

### Especializados (recomendados para RAG legal)
| Modelo | Params | Dims | Contexto | Licencia |
|--------|:------:|:----:|:--------:|:--------:|
| `wilfredomartel/BGE-M3-Legal-Spanish` ⭐ | 0.6B | 1024 | 8192 | Apache 2.0 |
| `wilfredomartel/embeddinggemma-300m-legal-spanish-300k` | 0.3B | 768 | 2048 | Apache 2.0 |
| `wilfredomartel/embeddinggemma-300m-legal-spanish-420k-v2` | 0.3B | 768 | 2048 | Apache 2.0 |
| `wilfredomartel/embeddinggemma-300m-legal-spanish-200k-v2` | 0.3B | 768 | 2048 | Apache 2.0 |

### Multilingües generalistas
| Modelo | Params | Descargas |
|--------|:------:|:---------:|
| `intfloat/multilingual-e5-large` | 0.6B | 12.2M |
| `intfloat/multilingual-e5-base` | 0.3B | 6.5M |
| `intfloat/multilingual-e5-small` | 0.1B | 10.2M |
| `intfloat/multilingual-e5-large-instruct` | 0.6B | 1.5M |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 0.1B | 48.5M |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 0.3B | 8.1M |

## APIs y Plataformas Peruanas

### SPIJ (Sistema Peruano de Información Jurídica)
- URL: https://spij.minjus.gob.pe
- Acceso: Solo por suscripción/login. **No tiene API pública documentada.**
- Contiene: Texto oficial actualizado del Código Penal y todas las normas peruanas.
- Alternativa: Scraping del HTML desde SPIJ Web o LP Derecho.

### Plataforma Nacional de Datos Abiertos
- URL: https://www.datosabiertos.gob.pe
- API REST disponible. Datasets en CSV/XLSX/DOCX.
- Datasets legales encontrados:
  - "Patrocinios Asumidos por la Defensa Penal" (MINJUSDH, 2023) — CSV/XLSX
  - "Fiscalías" (MPFN) — CSV/XLSX/DOCX
  - "Censo Nacional de Comisarias" (INEI, 2016)
- **No contiene el Código Penal estructurado.**

### Poder Judicial
- URL: https://www.pj.gob.pe
- Buscador de jurisprudencia: https://jurisprudencia.pj.gob.pe
- **Sin API REST documentada.** Solo búsqueda web.

### LP Derecho
- URL: https://lpderecho.pe/codigo-penal-peruano-actualizado/
- Texto HTML del Código Penal con actualizaciones.
- **Candidato para scraping.**

### Diario Oficial El Peruano
- URL: https://diariooficial.elperuano.pe
- Normas legales publicadas. Buscador web, sin API.

## Estrategia Recomendada para Obtener el Código Penal

1. **Scraping desde LP Derecho o SPIJ Web**: Extraer el texto HTML del Código Penal.
2. **Parseo a JSON estructurado**:
   ```json
   {
     "libro": "Libro Primero - Parte General",
     "titulo": "Título I - Del Hecho Punible",
     "capitulo": "Capítulo I - Bases de la Punibilidad",
     "articulo": "Artículo 11.- Delitos dolosos y culposos",
     "texto": "Son delitos dolosos...",
     "modificaciones": ["Ley N° 12345"],
     "epigrafe": "Delitos dolosos y culposos"
   }
   ```
3. **Chunking**: Usar estructura similar a `PeruvianConstitutionChunkRetrieval`:
   - chunks por artículo para búsqueda precisa
   - chunks por sección (capítulo/título) para contexto amplio
4. **Indexación**: FAISS + BM25 con BGE-M3-Legal-Spanish.

## APIs Internacionales de Referencia

| País | Sistema | API |
|------|---------|-----|
| Argentina | SAIJ | http://www.saij.gob.ar — API REST para normas y jurisprudencia |
| México | Semanario Judicial | API del SJF |
| Chile | LegisBot | API de búsqueda legal |

## Limitaciones Identificadas

- **No existe** un dataset público estructurado (JSON/CSV) del Código Penal Peruano.
- **No existe** una API REST gratuita para consultar el Código Penal Peruano.
- **No existen** datasets públicos de jurisprudencia peruana en HuggingFace.
- La Plataforma de Datos Abiertos tiene datos complementarios (fiscalías, defensa penal) pero no el código penal en sí.
- SPIJ es la fuente más completa pero requiere suscripción y no expone API.
