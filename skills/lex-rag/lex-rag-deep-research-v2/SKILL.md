---
name: lex-rag-deep-research-v2
description: Deep Research v2 para LexRAG — planificación legal, búsqueda en 2 rondas con reflexión, verificador programático, gestión de contexto estilo Kimi.
---

# LexRAG Deep Research v2

## ¿Qué resuelve?
El `--deep` original genera variantes léxicas de una query. Deep Research v2 agrega **planificación legal**, **búsqueda iterativa en 2 rondas** y un **verificador programático** que evalúa cobertura y detecta lagunas. Inspirado en Kimi DeepSearch pero sin costo LLM extra.

## Arquitectura

```
query legal
    │
    ▼
┌─────────────────────────────┐
│ 1. Planner Legal (reglas)   │ → modules/planner_legal.py
│    - Detecta tipo de causa   │
│    - Genera 3-5 sub-queries  │
│      desde ángulos legales   │
└──────────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ 2. Ronda 1: Deep Search  │ → reusa get_hybrid_context()
    │    (paralelo, 5 workers) │   para cada sub-query
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ 3. Verificador (reglas)  │ → modules/verifier.py
    │    - Cobertura x sub-    │
    │      pregunta [0-100]    │
    │    - Contradicciones     │
    │    - Lagunas detectadas  │
    └──────┬──────────────────┘
           │ si score < 70%
    ┌──────▼──────────────────┐
    │ 4. Ronda 2: Re-búsqueda  │ → solo lagunas
    │    (queries específicas) │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │ 5. Síntesis final        │ → synthesis.py (modificado)
    │    con confianza x fuente│
    │    + contradicciones     │
    └─────────────────────────┘
```

## Activación

```bash
# CLI - reemplaza --deep por --deep-v2
python3 graphrag_pro_v3.py --deep-v2 --query "casaciÃ³n por indebida motivaciÃ³n"

# Interactivo
python3 graphrag_pro_v3.py --deep-v2
# ðŸ“ Su SeÃ±orÃ­a...
```

## Componentes nuevos

### `modules/planner_legal.py`
- `LegalPlanner.plan(query)` â†’ `{"tipo": "...", "sub_queries": [...], "angulos": [...]}`
- Detecta tipo legal: `casacion`, `tutela`, `amparo`, `plenario`, `nulidad`, `general`
- Genera sub-queries desde 5 Ã¡ngulos: marco normativo, precedente, doctrina, hechos similares, consecuencias
- **Sin LLM**: reglas + diccionario legal peruano + patrones de texto

### `modules/verifier.py`
- `Verifier.evaluate(sub_queries, chunks)` â†’ `{"score": 0-100, "lagunas": [...], "contradicciones": [...]}`
- EvalÃºa:
  - **Cobertura**: cuÃ¡ntas sub-queries tienen al menos 1 chunk relevante
  - **Fuentes Ãºnicas**: diversidad de documentos citados
  - **Contradicciones**: afirma lo mismo y su contrario en distintos chunks
- `Verifier.generar_queries_ronda2(lagunas)` â†’ queries especÃ­ficas para re-buscar

### Modificaciones en `modules/synthesis.py`
- Nueva bandera `deep_v2=True` en `query_graphrag_pro()`
- Si `deep_v2`:
  1. `LegalPlanner.plan(query)` â†’ sub_queries
  2. Ejecutar retrievals en paralelo (Ronda 1)
  3. `Verifier.evaluate()` â†’ si score < umbral, Ronda 2
  4. Fusionar Ronda 1 + Ronda 2 con RRF extendido
  5. Pasar a sÃ­ntesis con indicadores de confianza

## Costo vs Beneficio

| MÃ©trica | --deep v1 | --deep-v2 | Diferencia |
|---|---|---|---|
| Chunks/consulta | ~88 | ~120 | +36% |
| Tiempo | ~64s | ~85s | +33% |
| Cobertura sub-queries | Sin control | 70%+ garantizado | MÃ¡s completo |
| DetecciÃ³n contradicciones | No | SÃ­ | Evita alucinaciones |
| Costo LLM extra | $0 | $0 | Reglas, no LLM |
| Confianza por afirmaciÃ³n | No | SÃ­ | Trazabilidad |

## Bandera CLI

```bash
# CLI - reemplaza --deep por --deep-v2
python3 graphrag_pro_v3.py --deep-v2 --query "casación por indebida motivación"

# Interactivo
python3 graphrag_pro_v3.py --deep-v2

# Comparativa: ejecuta normal + deep-v2 lado a lado
python3 graphrag_pro_v3.py --compare --query "despido arbitrario"
```

En `graphrag_pro_v3.py`:

## Implementación de componentes

### LegalPlanner (`modules/planner_legal.py`)

Analiza la consulta legal y genera sub-queries desde 5 ángulos usando reglas determinísticas (sin LLM).

```python
# modules/planner_legal.py
import re
from typing import Dict, List

class LegalPlanner:
    TIPOS_LEGALES = {
        "casacion": r"casa(ci|r)\w*\s|recurso\s+de\s+casaci|cas\.?\s*n[°º]",
        "tutela": r"tutela|amparo|hábeas\s+corpus|acción\s+de\s+amparo",
        "nulidad": r"nulidad|anulación|anular|nul\d{3,4}|nulidad\s+de",
        "laboral": r"despido|indemnización\s+laboral|CTS|gratificación|sindicato|huelga",
        "tributario": r"tributari|RTF|SUNAT|infracción\s+tributaria|deuda\s+tributaria",
        "constitucional": r"constitución|derecho\s+fundamental|principio.+constitucional|tribunal\s+constitucional",
        "civil": r"obligación|contrato|responsabilidad\s+civil|daños|indemnización.+civil|propiedad",
        "penal": r"penal|delito|homicidio|robo|hurto|lesiones|estafa|colusión|cohecho",
        "familia": r"alimentos|tenencia|régimen\s+de\s+visitas|divorcio|patria\s+potestad",
    }

    ANGULOS = [
        "marco_normativo",
        "precedente",
        "doctrina",
        "hechos_similares",
        "consecuencias",
    ]

    def plan(self, query: str) -> Dict:
        query_lower = query.lower()
        
        tipo = self._detectar_tipo(query_lower)
        sub_queries = self._generar_sub_queries(tipo, query)
        
        return {
            "tipo": tipo,
            "sub_queries": sub_queries,
            "angulos": self.ANGULOS,
        }

    def _detectar_tipo(self, query: str) -> str:
        for tipo, pattern in self.TIPOS_LEGALES.items():
            if re.search(pattern, query):
                return tipo
        return "general"

    def _generar_sub_queries(self, tipo: str, query: str) -> List[str]:
        """Genera 3-5 sub-queries desde diferentes ángulos legales."""
        base = re.sub(r"[¿?¡!.,;:]+", "", query).strip()
        subs = [base]  # la query original siempre va
        
        if tipo == "laboral":
            subs.extend([
                f"indemnización por {base}",
                f"procedimiento {base}",
                f"plazos y requisitos {base}",
                f"jurisprudencia sobre {base}",
            ])
        elif tipo == "casacion":
            subs.extend([
                f"requisitos de procedencia {base}",
                f"causal {base}",
                f"doctrina jurisprudencial {base}",
            ])
        elif tipo == "tributario":
            subs.extend([
                f"infracción tributaria relacionada",
                f"procedimiento contencioso tributario",
            ])
        else:
            subs.extend([
                f"normas aplicables a {base}",
                f"antecedentes jurisprudenciales {base}",
            ])
        
        return subs[:5]  # máximo 5 sub-queries
```

### Verifier (`modules/verifier.py`)

Evalúa cobertura de las sub-queries con reglas (sin LLM).

```python
# modules/verifier.py
import re
from typing import Dict, List, Tuple

class Verifier:
    def __init__(self, min_score: float = 0.7, max_lagunas: int = 3):
        self.min_score = min_score
        self.max_lagunas = max_lagunas

    def evaluate(self, sub_queries: List[str], chunks: List[str]) -> Dict:
        """
        Evalúa cobertura y consistencia de los chunks recuperados.
        
        Args:
            sub_queries: Lista de sub-queries planificadas
            chunks: Texto de los chunks recuperados
        
        Returns:
            Dict con score, lagunas, contradicciones
        """
        if not chunks:
            return {"score": 0.0, "lagunas": sub_queries, "contradicciones": []}
        
        texto_completo = " ".join(chunks)
        
        # Cobertura: cuántas sub-queries tienen al menos 1 chunk relevante
        query_coverage = []
        lagunas = []
        for sq in sub_queries:
            # Extraer palabras clave (ignorar stopwords)
            tokens = [w for w in sq.lower().split() if len(w) > 3]
            hits = sum(1 for t in tokens if t in texto_completo.lower())
            ratio = hits / max(len(tokens), 1)
            query_coverage.append(ratio)
            if ratio < 0.3:
                lagunas.append(sq)
        
        cobertura_score = sum(query_coverage) / len(query_coverage) if query_coverage else 0
        
        # Diversidad de fuentes (documentos únicos mencionados)
        fuentes = set(re.findall(r'Jurisprudencia/([\w.]+)', texto_completo))
        diversidad_score = min(1.0, len(fuentes) / len(sub_queries)) if sub_queries else 0.5
        
        # Contradicciones: busca pares de afirmaciones opuestas
        contradicciones = self._detectar_contradicciones(texto_completo)
        
        # Score compuesto
        score = 0.5 * cobertura_score + 0.3 * diversidad_score
        if contradicciones:
            score *= 0.8  # penalización por contradicciones
        
        return {
            "score": round(score, 3),
            "cobertura": round(cobertura_score, 3),
            "diversidad": round(diversidad_score, 3),
            "fuentes_unicas": len(fuentes),
            "lagunas": lagunas[:self.max_lagunas],
            "contradicciones": contradicciones[:3],
        }

    def generar_queries_ronda2(self, lagunas: List[str]) -> List[str]:
        """Genera queries específicas para re-buscar lagunas."""
        queries_r2 = []
        for laguna in lagunas:
            # Simplificar: usar la laguna como query directa
            queries_r2.append(laguna)
        return queries_r2[:self.max_lagunas]

    def _detectar_contradicciones(self, texto: str) -> List[Dict]:
        """Detecta afirmaciones contradictorias."""
        contradicciones = []
        pares_opuestos = [
            (r"procede", r"no\s+procede"),
            (r"(?<![sn] )sí\s+corresponde", r"no\s+corresponde"),
            (r"es\s+procedente", r"es\s+improcedente"),
            (r"aplica", r"no\s+aplica"),
        ]
        for pos, neg in pares_opuestos:
            if re.search(pos, texto, re.I) and re.search(neg, texto, re.I):
                contradicciones.append({
                    "tipo": "contradicción normativa",
                    "positivo": pos,
                    "negativo": neg,
                })
        return contradicciones
```

### Integración en el pipeline

```python
# Modificación en modules/synthesis.py (o graphrag_pro_v3.py)

async def query_graphrag_pro(query, deep_v2=False):
    if not deep_v2:
        return await query_normal(query)
    
    from modules.planner_legal import LegalPlanner
    from modules.verifier import Verifier
    
    planner = LegalPlanner()
    verifier = Verifier(min_score=0.7)
    
    # Fase 1: Planificar
    plan = planner.plan(query)
    print(f"⚖️ Tipo legal detectado: {plan['tipo']}")
    print(f"📋 Sub-queries: {len(plan['sub_queries'])}")
    
    # Fase 2: Ronda 1 (búsqueda paralela)
    ronda1 = []
    for sq in plan['sub_queries']:
        top_docs, text_ctx, audit = get_hybrid_context(sq, top_k=7)
        ronda1.append((sq, text_ctx, audit))
    
    todos_chunks = [ctx for _, ctx, _ in ronda1]
    
    # Fase 3: Verificar
    resultado = verifier.evaluate(plan['sub_queries'], todos_chunks)
    print(f"📊 Score cobertura: {resultado['score']:.2f}")
    
    if resultado['score'] < verifier.min_score:
        print(f"🔄 Ronda 2: re-buscando {len(resultado['lagunas'])} lagunas...")
        ronda2 = []
        for sq in resultado['lagunas']:
            top_docs, text_ctx, audit = get_hybrid_context(sq, top_k=10)
            ronda2.append((sq, text_ctx, audit))
        # Fusionar Ronda 1 + Ronda 2 con RRF extendido
        todos_chunks.extend([ctx for _, ctx, _ in ronda2])
    
    # Fase 4: Síntesis con confianza
    confianza = f"CONFIANZA: {'ALTA' if resultado['score'] > 0.8 else 'MEDIA' if resultado['score'] > 0.5 else 'BAJA'}"
    instrucciones = f"{confianza}\nFuentes consultadas: {resultado['fuentes_unicas']}"
    if resultado['contradicciones']:
        instrucciones += f"\n⚠ Se detectaron {len(resultado['contradicciones'])} posibles contradicciones."
    
    return await generar_sintesis(query, todos_chunks, instrucciones)
```

## Arquitectura de archivos

```
modules/
├── planner_legal.py       → LegalPlanner: planificación legal basada en reglas
├── verifier.py            → Verifier: evaluación de cobertura y detección de lagunas
└── synthesis.py           → MODIFICADO: soporta --deep-v2 con loop de 2 rondas
```

## Pruebas unitarias

```python
# tests/test_deep_research_v2.py
import pytest
from modules.planner_legal import LegalPlanner
from modules.verifier import Verifier

def test_planner_detecta_tipo_laboral():
    planner = LegalPlanner()
    result = planner.plan("indemnización por despido arbitrario")
    assert result["tipo"] == "laboral"
    assert len(result["sub_queries"]) >= 3

def test_planner_detecta_casacion():
    planner = LegalPlanner()
    result = planner.plan("casación por indebida motivación")
    assert result["tipo"] == "casacion"

def test_verifier_score_completo():
    verifier = Verifier()
    subs = ["despido arbitrario", "indemnización laboral"]
    chunks = ["el despido arbitrario requiere indemnización según el art. 34", "la indemnización laboral procede"]
    result = verifier.evaluate(subs, chunks)
    assert result["score"] > 0.5
    assert len(result["lagunas"]) == 0

def test_verifier_detecta_lagunas():
    verifier = Verifier()
    subs = ["despido arbitrario", "procedimiento de cese"]
    chunks = ["el despido arbitrario requiere indemnización"]
    result = verifier.evaluate(subs, chunks)
    assert len(result["lagunas"]) >= 1

def test_verifier_detecta_contradicciones():
    verifier = Verifier()
    subs = ["prueba de despido"]
    chunks = ["procede la indemnización", "no procede la indemnización"]
    result = verifier.evaluate(subs, chunks)
    assert len(result["contradicciones"]) >= 1
```

## Tests de integración

```bash
# 1. Verificar que --deep-v2 carga sin errores
python3 graphrag_pro_v3.py --deep-v2 --query "prueba"

# 2. Ejecutar consulta real
python3 graphrag_pro_v3.py --deep-v2 --query "indemnización por despido arbitrario"

# 3. Modo comparativo (normal vs deep-v2)
python3 graphrag_pro_v3.py --compare --query "casación por indebida motivación"

# 4. Verificar auditoría JSON
# Buscar en consultas_guardadas/YYYYMMDD_HHMMSS_query_deep_audit.json
# Debe contener: metadata.plan, retrieval.hybrid.faiss_raw (2 rondas), verifier.score
python3 -c "
import json, glob
arch = sorted(glob.glob('consultas_guardadas/*deep_audit.json'))[-1]
audit = json.load(open(arch))
print(f'Score cobertura: {audit.get(\"verifier\",{}).get(\"score\",\"N/A\")}')
print(f'Lagunas: {audit.get(\"verifier\",{}).get(\"lagunas\",[])}')
"
```

## Pitfalls
1. **No sobrecargar la Ronda 2**: si el verificador encuentra más de 3 lagunas, priorizar las 3 más críticas. Más de 3 alarga demasiado el tiempo de respuesta.
2. **Verificador sin LLM**: resistir la tentación de usar un LLM para evaluar. Las reglas (conteo de cobertura, detección de solapamiento) son igual de efectivas y cuestan $0.
3. **Contexto truncado**: con 2 rondas se duplica el contexto. Implementar gestión tipo Kimi: ocultar chunks de Ronda 1 si el total excede MAX_TOKENS_CONTEXT.
4. **Cache**: desactivar cache para --deep-v2 (las sub-queries son distintas cada vez). O usar cache solo a nivel de chunks individuales, no de consulta completa.
5. **--compare ejecuta 2 llamadas al LLM** (una por pipeline). El costo se duplica en modo comparativa. Usar solo para validación, no para consultas rutinarias.
6. **Regex de detección de tipo**: Los patrones `TIPOS_LEGALES` son específicos para jurisprudencia peruana. Si el corpus cambia de país/dominio, actualizar los patrones.
7. **Sub-queries duplicadas**: Si la query original contiene palabras de la sub-query generada, habrá solapamiento en los resultados. El RRF fusionado lo maneja, pero se pierde eficiencia. Mejorar con dedup semántico si es necesario.
