# RAG Response Legibility Evaluation

## Overview
Methodology for evaluating whether AI-generated RAG responses are clear, direct, and readable for end users. Designed for Spanish-language legal RAG systems but adaptable to any domain.

## Core Metrics

| Metric | Target | Detection |
|--------|--------|-----------|
| Respuesta directa | First sentence answers the question | Check first 200 chars for "La consulta se refiere a...", "Para abordar esta cuestion...", "En el contexto proporcionado..." |
| Jerga tecnica | Zero occurrences | Search for: grafo, nodo, topologia, algoritmo, embedding, vector, FAISS, BM25, reranker, cross-encoder |
| Estructura | Has sections, bold, bullets | Regex for # headers, **bold**, - bullets |
| Citas formales | Has "Jurisprudencia citada:" section | Section header present at end |
| Citas en linea | 2+ inline citations | **bold** text followed by (Jurisprudencia/...) |
| Leyes aplicables | 1+ law/code/article cited | Pattern match Ley, Codigo, Decreto, Articulo |
| Oraciones | < 30 words/sentence average | Split on . ! ? |
| Follow-ups | 3 generated | Count from output |

## Prompt Fixes (by symptom)

| Symptom | Fix |
|---------|-----|
| No responde directo | Add instruction 0: "RESPUESTA DIRECTA: Responde la pregunta del usuario en la PRIMERA FRASE. No empieces con analisis genericos." |
| Jerga tecnica | Add explicit prohibition with terms: "PROHIBIDO: grafos, nodos, topologia, algoritmos [etc]" |
| Sin citas formales | Add "6. FORMATO DE CITAS: Al final agrega seccion '**Jurisprudencia citada:**'" with format example |
| Oraciones muy largas | Add instruction: "Usa oraciones cortas. Maximo 25 palabras por oracion." |
| Respuesta muy larga | Add "Responde en maximo 3-4 parrafos." |

## Python Evaluation Template

```python
import re

def evaluar_legibilidad(texto):
    if not texto:
        return {"error": "sin respuesta"}
    
    palabras = texto.split()
    num_palabras = len(palabras)
    oraciones = re.split(r'[.!?]+', texto)
    oraciones = [o.strip() for o in oraciones if len(o.strip()) > 10]
    num_oraciones = len(oraciones)
    palabras_por_oracion = num_palabras / max(num_oraciones, 1)
    
    tiene_titulos = bool(re.search(r'#{1,3}\s', texto))
    tiene_negritas = '**' in texto
    tiene_vinetas = bool(re.search(r'^\s*[-*]\s', texto, re.MULTILINE))
    tiene_secciones = bool(re.search(r'(Introduccion|Analisis|Conclusion|Precedentes|Jurisprudencia)', texto, re.IGNORECASE))
    tiene_citas_seccion = 'Jurisprudencia citada' in texto
    
    jerga_tecnica = ['nodo', 'grafo', 'topologia', 'algoritmo', 'embedding', 
                     'vector', 'FAISS', 'BM25', 'reranker', 'cross-encoder']
    jerga_encontrada = [j for j in jerga_tecnica if j.lower() in texto.lower()]
    
    primer_parrafo = texto.split('\n\n')[0] if '\n\n' in texto else texto[:300]
    intro_generica = any(p in primer_parrafo.lower()[:150] 
                         for p in ['la consulta se refiere', 'para abordar esta', 
                                    'en el contexto proporcionado', 'a continuacion se'])
    
    responde_directo = bool(re.search(r'(Si|No|Puede|Debe|Es posible|Procede|Cabe|Aplica)', 
                                       texto[:200]))
    
    return {
        "palabras": num_palabras,
        "oraciones": num_oraciones,
        "palabras_por_oracion": round(palabras_por_oracion, 1),
        "tiene_titulos": tiene_titulos,
        "tiene_negritas": tiene_negritas,
        "tiene_vinetas": tiene_vinetas,
        "tiene_secciones": tiene_secciones,
        "tiene_citas_final": tiene_citas_seccion,
        "jerga_tecnica": jerga_encontrada,
        "responde_directo": responde_directo,
        "intro_generica": intro_generica,
    }


def evaluar_citas(texto):
    if not texto:
        return {}
    
    citas_enlinea = re.findall(r'\*\*([^*]+)\*\*\s*\(Jurisprudencia/', texto)
    doc_ids = re.findall(r'[a-f0-9]{20,40}', texto)
    leyes = re.findall(r'(?:Ley|Codigo|Decreto|Constitucion|Articulo)\s[^,.\n]+', texto)
    
    citas_seccion = ""
    if 'Jurisprudencia citada' in texto:
        citas_seccion = texto.split('Jurisprudencia citada')[-1]
        citas_seccion = citas_seccion.split('##')[0] if '##' in citas_seccion else citas_seccion.split('\n\n\n')[0]
    
    return {
        "citas_enlinea": len(citas_enlinea),
        "documentos_citados": len(set(doc_ids)),
        "leyes_mencionadas": len(set(leyes)),
        "seccion_citas_presente": bool(citas_seccion.strip()),
    }
```

## Test Design (10 questions)

```
ALTA (4): Core domain with corpus support
MEDIA (3): Niche or cross-domain topics  
BAJA (3): Peripheral or out-of-corpus topics
```

Always include at least 1 question the corpus cannot answer (tests hallucination).

## Report Format

Save as both .txt and .md:

- Summary table: # | question | time(s) | words | direct | jerga | citas | leyes
- Full transcript of each response
- Before/after comparison when iterating on prompts
- Final conclusion with metric deltas
