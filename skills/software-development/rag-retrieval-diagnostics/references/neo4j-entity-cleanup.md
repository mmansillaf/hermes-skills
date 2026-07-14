# Neo4j Entity Cleanup: Eliminar Entidades Genéricas

**Problema (02-may-2026):** Graph traversal devuelve resultados poco relevantes porque las normas comparten entidades verbales/genéricas en vez de entidades nombradas. Top entidades: "Aprueban" (10,720 menciones), "Autorizan" (8,544), "Designación" (6,306), "Ministerio" (3,094), "Perú" (2,729).

**Causa:** La extracción original de entidades para Neo4j se hizo sobre títulos de normas (primera línea) sin filtro NER. Cada palabra capitalizada se convirtió en entidad, incluyendo verbos de acción y términos genéricos.

**Fix rápido (02-may-2026, ~30s, $0):**

```cypher
// 1. Eliminar verbos y términos genéricos
MATCH (e:Entidad) 
WHERE e.nombre IN ['Aprueban','Autorizan','Designación','Nombramiento','Ministerio',
                    'Perú','Viajes','República','Reglamento','Estado','Designan',
                    'Modifican','Justicia','Declaran','Prorrogan','Creación','Gobierno',
                    'Nacional','Crean','Salud','Educación','LEY','MINISTERIO','Sistema']
DETACH DELETE e;

// 2. Eliminar entidades muy cortas (< 5 chars)
MATCH (e:Entidad) WHERE size(e.nombre) < 5 DETACH DELETE e;

// 3. Eliminar entidades con 1 sola mención (ruido)
MATCH (:Norma)-[r:MENCIONA]->(e:Entidad) 
WITH e, count(r) as cnt WHERE cnt <= 1 
DETACH DELETE e;
```

**Resultado:**
- Entidades: 32,675 → 16,077 (reducción 51%)
- Relaciones: 436,989 → 336,041 (reducción 23%)
- Top entidades post-limpieza: "Distrito Fiscal" (2,950), "Presupuesto" (1,926), "Resolución" (1,829), "Ministro" (1,730)
- Graph traversal sigue funcionando correctamente

**Limitación:** Las entidades siguen siendo extraídas de títulos, no de texto_completo con NER. Entidades como "Distrito Fiscal" o "Presupuesto" son mejores que verbos pero aún no son entidades nombradas ideales. **Fix definitivo pendiente:** Re-extraer con NER o Groq batch (~$10) usando texto_completo.
