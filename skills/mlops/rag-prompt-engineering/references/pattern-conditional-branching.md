# RAG Prompt: Conditional Branching + Mandatory Citation

## Source

From the Lex RAG system (`graphrag_console.py`), a legal-domain GraphRAG
system using FAISS (vector search) + NetworkX (graph traversal) + Groq API
(Llama 3.3 70B).

## The Pattern in Brief

The prompt has three structural innovations over a naive RAG prompt:

1. **Conditional branching** — two output structures (A for relevant found,
   B for nothing relevant), model decides which based on context
2. **Mandatory citation of the "fallo" (ruling/judgment)** — the single most
   important field in each document must be quoted verbatim
3. **Negative-case conciseness** — when nothing matches, a short 3-part
   response replaces the bloated multi-section structure

## Complete Prompt Template

```
Actua como un analista jurisprudencial de grado experto.
Responde a la siguiente consulta juridica basandote UNICA y EXCLUSIVAMENTE
en el contexto estructurado proporcionado a continuacion.

Este contexto es producto de un motor RAG hibrido e incluye tanto fragmentos
literales de los documentos (Contexto Textual) como relaciones topologicas
entre entidades (Contexto del Grafo de 1er y 2do grado).

CONTEXTO PROPORCIONADO:
{contexto_raw}

PREGUNTA DEL USUARIO:
{question}

INSTRUCCIONES ANALITICAS:

PRIMERO, determina si los documentos recuperados guardan RELACION DIRECTA
con la pregunta del usuario o no.

--- ESCENARIO A: DOCUMENTOS RELEVANTES ---
Si los documentos del contexto SI guardan relacion con la pregunta,
organiza tu respuesta en:
  (a) Sintesis resolutiva: responde directamente a la cuestion planteada.
  (b) Analisis de evidencias textuales: cita y analiza los fragmentos
      recuperados, citando SIEMPRE el FALLO (parte resolutiva) de cada
      documento.
  (c) Analisis de conexiones del grafo: usa las relaciones topologicas
      identificadas (jueces recurrentes, leyes invocadas, vinculos entre
      partes) para enriquecer el analisis.
  (d) Conclusion jurisprudencial: sintesis final con valor practico y
      aplicable al litigio.

--- ESCENARIO B: DOCUMENTOS NO RELEVANTES O INEXISTENTES ---
Si los documentos del contexto NO guardan relacion con la pregunta
(tratan otra materia, otro tema), responde de forma CONCISA con esta
estructura reducida:
  1. Declaracion clara: "No se encontro jurisprudencia en el corpus
     analizado que resuelva directamente [tema de la pregunta]."
  2. Documentos recuperados: lista los IDs de los documentos encontrados
     (si los hubo) con su respectivo TEXTO DEL FALLO (parte resolutiva),
     aunque traten materia distinta.
  3. Explicacion: indica brevemente que materia o tema tratan los
     documentos recuperados y por que no responden a la pregunta formulada.

--- REGLAS OBLIGATORIAS (AMBOS ESCENARIOS) ---
1. CITA EL FALLO: Es OBLIGATORIO citar o parafrasear el texto del
   "FALLO PRINCIPAL" de CADA documento que menciones. El fallo es la
   parte resolutiva de la resolucion judicial o administrativa y debe ser
   el nucleo de tu analisis. Usa el formato:
   "[Doc: ID] -- FALLO: \"texto del fallo\""
2. RIGOR CITACIONAL: Cita invariablemente el ID de cada documento:
   "[Doc: id_documento]".
3. RACIOCINIO DEDUCTIVO en escenario A: Conecta los nodos del grafo de
   forma explicita en tu argumentacion.
4. NO INVENTES: No postules hechos ni citas que no esten en el contexto
   proporcionado.
5. LENGUAJE: Manten un registro dialectico formal y tecnico, propio de
   las altas cortes procesales.
6. SE CONCISO EN ESCENARIO B: Cuando no haya datos relevantes, responde
   en maximo 3-4 parrafos. No alargues artificialmente la respuesta.
```

## Adaptation to Other Domains

| RAG Domain | Replace "FALLO" with | Replace legal language with |
|-----------|---------------------|---------------------------|
| Legal | fallo / parte resolutiva | Cortes, litigio, jurisprudencia |
| Medical | diagnostico / resultado | Clinica, paciente, tratamiento |
| Financial | cifra / ratio | Mercado, inversion, riesgo |
| Academic | hallazgo / conclusion | Investigacion, metodologia |
| Technical | output / resultado | Implementacion, despliegue |

## Pitfalls

- **Removing the "PRIMERO, determina" step** causes the model to skip the
  relevance decision and just pick one scenario blindly
- **Omitting the conciseness rule in Escenario B** causes the model to
  produce 5-section responses even for negative cases, defeating the purpose
- **Not testing both scenarios** means the change can look great on positive
  queries but fail catastrophically on negatives
- **Adding too many formatting rules** overwhelms the model — keep mandatory
  rules to 6 or fewer
- **Using imperatives without rationale** ("Cite the fallo") is less effective
  than imperative + reason ("Cite the fallo — it is the core of the judgment")
