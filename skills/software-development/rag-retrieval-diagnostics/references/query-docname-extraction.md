# Extracción de Nombres de Documentos desde la Query del Usuario

## Cuándo usar

Cuando un sistema RAG recibe queries como "compara el contrato A con el contrato B" o "encuentra contradicciones entre la resolucion X y el informe Y", y el retrieval devuelve chunks de documentos **no relevantes** porque busca por embedding semantico de toda la frase en vez de enfocarse en los documentos nombrados.

## Síntoma

El usuario pide comparar documentos especificos pero la respuesta incluye chunks de documentos no relacionados. El LLM responde "no tengo acceso a esos documentos" a pesar de que SÍ existen en la base.

## Causa raíz

El retrieval busca por similitud semantica de la query completa ("compara el contrato de servicios con el de locacion"). El embedding de la frase "compara X con Y" no necesariamente se parece al embedding de los chunks de X e Y. El `doc_filter` llega como `None` porque nadie extrajo los nombres de la query.

## Fix: `_extract_doc_names_from_query(query) -> List[str]`

### Paso 1 — Busqueda entre comillas
Si el usuario escribio `"contrato_servicios.txt"`, usar `re.findall(r'"([^"]+)"', query)`.

### Paso 2 — Split por conectores
Si no hay comillas, partir por `y`, `e`, `vs`, `versus`, `con`, `,`.

### Paso 3 — Filtrar stop words
Remover palabras comunes de la query (compara, documento, entre, el, la, etc.) y palabras < 5 caracteres.

### Paso 4 — Busqueda difusa en la base
Para cada candidato, llamar a un metodo tipo `search_documents_fuzzy(fragment)` que intente variaciones:
- Nombre exacto: `LIKE '%candidato%'`
- Con extension: `LIKE '%candidato.txt%'`, `LIKE '%candidato.pdf%'`
- Palabra por palabra: partir el fragmento en palabras > 3 chars y buscar cada una

### Paso 5 — Pasar como doc_filter al retrieval
Si se encontraron documentos, pasarlos como `doc_filter` al `retrieval_agent`. Si no, hacer retrieval normal sin filtro.

## Pitfalls

- **Stop words incompletas**: palabras como "contrato" son parte del nombre real del documento y tambien palabra de la query. Si pones "contrato" en stop words, nunca encontraras "contrato_servicios.txt". Solucion: solo remover palabras MUY genericas (compara, documento, entre, etc.) y permitir palabras > 4 chars como candidatos.
- **FTS5 no rebuild**: si la busqueda FTS5 da 0 resultados siempre, verificar que se ejecuta `INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')` tras cada `add_chunks()`.
- **top_k insuficiente con filtro**: cuando se usa `doc_filter`, los chunks de los documentos filtrados pueden estar fuera del top 20. Solucion: triplicar `top_k` cuando hay `doc_filter`.
- **Fallback cuando filtro deja 0 resultados**: si tras filtrar no quedan candidatos, re-intentar la busqueda usando los nombres de los documentos como query en vez de la pregunta original.

## Codigo de ejemplo

Ver `src/agents/pipeline.py` clase `Orchestrator`, metodo `_extract_doc_names_from_query()` y `process_query()` paso 1.5.
Ver `src/core/vector_store.py` metodo `search_documents_fuzzy()`.
