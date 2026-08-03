# Evaluación del RAG con 20,973 Documentos Indexados

**Fecha:** 7 Junio 2026
**Corpus:** ~21,000 documentos LABORAL extraídos con Groq Batch API + indexados en FAISS + BM25 + NetworkX
**Modelo extracción:** Llama 3.1 8B Instant (max_tokens=1024)
**Modelo embeddings:** sentence-transformers/distiluse-base-multilingual-cased-v2

## Metodología

Se hicieron 10 preguntas (6 laborales, 3 comerciales, 4 de familia) al RAG híbrido (FAISS + BM25).
Cada pregunta recupera 5 documentos. Se evaluó:
- Relevancia del top-1
- Si extrae leyes citadas
- Si el fallo es concreto
- Tiempo de respuesta

## Resultados

| Pregunta | Área | Tiempo | Docs | Relevancia | Leyes | Observación |
|----------|:----:|:------:|:----:|:----------:|:-----:|-------------|
| indemnización por despido arbitrario | Laboral | 0.9s | 5 | Media | NO | Fallo concreto: orden de depósito judicial |
| pago de utilidades a trabajadores | Laboral | 0.6s | 5 | Media | NO | Orden de pago específica a Unacem S.A.A. |
| reintegro de remuneraciones | Laboral | 0.6s | 5 | Media | NO | Depósito judicial |
| ejecución de garantías mobiliarias | **Comercial** | 0.4s | 5 | **Alta** | **SI** | RA 0000185-2020-CE-PJ |
| anulación de laudo arbitral | **Comercial** | 0.3s | 5 | **Alta** | **SI** | Art. 637 CPC |
| obligación de dar suma de dinero | Comercial | 0.4s | 5 | Media | NO | |
| pensión de alimentos para menores | **Familia** | 0.2s | 5 | **Alta** | **SI** | Ley 29497, Art. 1 |
| violencia familiar medidas de protección | Familia | ERROR | — | — | — | Sin documentos de familia en el índice |
| tenencia y custodia de menores | **Familia** | 0.4s | 5 | **Alta** | **SI** | Art. 637 CPC |
| régimen de visitas | Familia | 0.5s | 5 | Media | NO | Documento laboral con palabra "visita" |

## Métricas Clave

| Métrica | Valor |
|---------|-------|
| Fallo concreto (extrajo decisión del tribunal) | **10/10 (100%)** |
| Con leyes citadas | 4/10 (40%) |
| Tiempo promedio por consulta | **0.5s** |
| Relevancia Alta | 4/10 (40%) |
| Relevancia Media | 5/10 (50%) |
| Relevancia Baja / Error | 1/10 (10%) |

## Hallazgos Críticos

### 1. El corpus actual solo tiene LABORAL
Las preguntas de COMERCIAL y FAMILIA encuentran documentos laborales que contienen palabras clave similares ("garantía", "pensión"). **No hay documentos de esas áreas en el índice actual.** Para evaluar realmente COMERCIAL y FAMILIA hay que procesar e indexar esos documentos primero.

### 2. Predominan resoluciones de trámite
La mayoría de los documentos recuperados son resoluciones interlocutorias (programar audiencias, notificar, proveer escritos), no sentencias de fondo. Esto es porque el corpus incluye tanto Sentencias como Resoluciones, y las Resoluciones son mayoría en número. Para mejorar la calidad del RAG:
- Filtrar solo Sentencias en la ingesta
- O aumentar el volumen total para que las sentencias significativas estadísticamente

### 3. Error en pregunta de violencia familiar
La pregunta "violencia familiar medidas de protección" lanzó `Ran out of input` — probablemente porque ningún documento en el corpus tiene esos términos. Es un caso borde: el RAG no encuentra nada y falla silenciosamente. Manejar este caso con una respuesta genérica: "No se encontraron documentos relacionados con este tema en el corpus."

### 4. Cobertura de leyes: 40%
Solo 4 de 10 preguntas recuperaron documentos con leyes citadas. Esto puede mejorar con:
- Prompt más explícito: "SIEMPRE extraer leyes y artículos citados"
- Documentos más completos (menos resoluciones de trámite, más sentencias)
- max_tokens=1024 ya resuelve el truncamiento
