# Pain Points: Legal Tech RAG Services

## Contexto
Este archivo mapea los dolores reales de estudios de abogados y departamentos legales
en Perú/LatAm que son clientes potenciales para servicios de RAG legal avanzado.
Basado en research de Thomson Reuters, Northzone, Landbase, y experiencia directa
procesando +800K resoluciones judiciales peruanas.

## Pain Point Matrix

| # | Dolor del Cliente | Síntomas | Tu Solución (RAG Avanzado) | Ángulo de Contenido |
|---|-------------------|----------|---------------------------|---------------------|
| 1 | "Las herramientas AI genéricas (Harvey, Lexis+) no entienden jurisprudencia peruana" | Compraron solución internacional, no funciona con legislación local, abandonaron | RAG entrenado sobre resoluciones judiciales peruanas reales (800K docs) | "Por qué Harvey no sirve en Perú — y qué construir en su lugar" |
| 2 | "Búsqueda manual de jurisprudencia: 8+ horas/semana" | Asociados quemados, partner frustrado, facturación baja | Búsqueda semántica + Knowledge Graph en segundos sobre corpus propio | "De 8 horas a 8 segundos: búsqueda semántica de jurisprudencia" |
| 3 | "No encontramos precedentes relevantes para nuestros casos" | Pierden juicios por falta de doctrina jurisprudencial, research incompleta | NetworkX + ChromaDB conecta resoluciones relacionadas que búsqueda textual nunca encuentra | "El precedente que tu búsqueda booleana nunca encontró" |
| 4 | "Documentos judiciales en PDFs sin estructura" | 90% del tiempo es leer PDFs, extraer datos, clasificar manualmente | Pipeline de clasificación automática (721K docs) + extracción de hechos, problema, fallo | "Procesé 721,000 PDFs judiciales en 3 días. Esto aprendí." |
| 5 | "Queremos AI pero no podemos mandar datos al cloud" | Datos sensibles de clientes, confidencialidad, compliance | Stack 100% local: llama.cpp + Qwen 7B Q4_K_M + ChromaDB en una ThinkPad P53 | "RAG legal 100% local: sin cloud, sin API keys, sin filtraciones" |
| 6 | "Gastamos $500+/mes en APIs externas para AI" | Suscripciones que no se usan, ROI negativo | Groq Batch API ~$51 para 562K documentos, o local $0 en inferencia | "Batch AI: 562K documentos por $51 (vs $500+/mes en APIs)" |
| 7 | "El AI alucina citas legales — no podemos confiar" | Abogados no usan AI porque inventa precedentes, riesgo de malpractice | RAG con retrieval-augmented generation + verificación epistemológica (7 checkpoints) | "Cómo eliminamos las alucinaciones en AI legal (sin magia)" |

## ICP Definition (Ideal Customer Profile)

### Target Firms
- **Estudios de abogados** medianos-grandes en Perú/LatAm (25+ abogados)
  - Práctica: Laboral, Comercial, Familia (alto volumen documental)
  - Señales: Tienen sistema de gestión documental, hired legal ops, creciendo
- **Departamentos legales** en empresas reguladas
  - Sectores: Banca, seguros, retail, mining
  - Dolor: Compliance, contratos masivos, regulación cambiante
- **Despachos que ya intentaron AI genérica**
  - Compraron Harvey/Lexis+/ChatGPT y se frustraron
  - No encuentran valor porque no hay jurisprudencia peruana en los modelos

### Decision Makers
| Rol | Preocupación Principal | Canal |
|-----|----------------------|-------|
| Partner / Socio fundador | Competitividad, eficiencia, diferenciación | LinkedIn posts + DM |
| Head of Legal Ops | Implementación, integración, ROI | LinkedIn + email |
| Director de Innovación Legal | Tech readiness, casos de uso | Posts técnicos + conferencias |
| IT Director | Seguridad, compliance, integración | Documentación técnica |

### Señales de Compra (Intent Signals)
- Hiring para roles de legal operations o innovation
- Implementación o upgrade de document management system
- Crecimiento en prácticas de alto volumen (laboral, comercial)
- Publicaciones sobre "transformación digital" en el estudio
- Comentarios en posts sobre AI legal, RAG, automatización

## Content Angles por Pain Point

### Para dolor #1 (Soluciones genéricas no sirven)
```
"Hace 6 meses un partner me dijo: 'Probamos Harvey. No conoce
ni el Código Civil peruano.' Tenía razón. Los modelos AI entrenados
con Common Law no entienden nuestro sistema. Así que construimos
un RAG sobre 800,000 resoluciones judiciales peruanas reales.
Resultado: búsqueda semántica en segundos, en nuestro idioma legal,
con nuestra jurisprudencia. [thread con arquitectura]"
```

### Para dolor #5 (Stack local)
```
"El CTO de un banco me dijo: 'Nos encantaría usar AI, pero no podemos
mandar nuestros contratos a OpenAI.' Le mostré esto:
- Llama.cpp + Qwen 7B → inferencia local
- ChromaDB → vectores en su servidor
- ThinkPad P53 con 4GB VRAM → suficiente
Costo de inferencia: $0. Datos: nunca salen. Privacidad: intacta.
Ese es el stack que necesitan los estudios que manejan datos sensibles."
```

### Para dolor #7 (Alucinaciones)
```
"Todo abogado que prueba ChatGPT para investigación legal termina
diciendo lo mismo: 'Inventa precedentes.' Y tienen razón.
La solución no es 'mejor prompting'. Es RAG con verificación
epistemológica: 7 checkpoints antes de publicar cualquier cita legal.
[diagrama del pipeline de verificación]
Resultado: 0 alucinaciones en 1,000 consultas de prueba."
```

## Dos & Don'ts

### DO
- Mostrar arquitecturas reales (diagramas que construiste)
- Compartir números reales (800K docs, $51 batch, 3 días de procesamiento)
- Explicar problemas reales que resolviste
- Usar lenguaje técnico preciso (ChromaDB, NetworkX, Qwen 7B, Groq Batch)
- Incluir "el camino" — qué no funcionó antes de funcionar

### DON'T
- No hacer "case studies" genéricos con datos inventados
- No vender directamente en posts ("contrátame")
- No exagerar resultados
- No usar buzzwords sin sustento técnico
- No prometer soluciones mágicas
