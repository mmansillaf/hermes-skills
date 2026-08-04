---
name: deep-research-paralelo
description: "Deep research via parallel subagents and live validation."
---

# Deep Research Paralelo (patrón apex validado 2026-08-04)

Metodología de investigación profunda para temas de 2+ frentes independientes.
Validada en la investigación de fine-tuning legal + proveedores GPU (4 informes,
~120K tokens, $0). Resultado: verificación cruzada real, sin claims inventados.

## Cuándo usar
- Investigación multi-tema (2-3 frentes independientes: técnica, mercado, precios).
- Panorama de modelos/herramientas/proveedores con precios que cambian.
- Literatura con claims que exigen verificación (papers, benchmarks).
- El usuario pide "investiga a fondo" o espera evidencia, no opinión.
- ROL EN EL STACK APEX: este skill es la EJECUCIÓN por delegación paralela del
  framework. Cargar SIEMPRE junto con: apex-research-framework (estrategia/
  cognición/validación), competitive-research-ai-projects (ejecución API:
  GitHub/Serper/arXiv) y research-synthesis-html-preview (producción HTML).
  Cubre el rol de la skill "web-deep-research" que NO está publicada en
  mmansillaf/hermes-skills. Instalado 2026-08-04 desde ~/.hermes/skills/research/.

## Cuándo NO
- Un solo tema simple -> investigación directa (una llamada web, sin delegar).
- Tareas mecánicas multi-paso -> execute_code.
- Requiere preguntar al usuario en el camino (subagentes no pueden usar clarify).

## Patrón en 5 fases

### Fase 0 — Alcance y descomposición
- Divide el tema en MAX 3 tracks independientes (límite de concurrencia del usuario).
- Cada track = UNA pregunta de investigación autocontenida.
- Anota qué verificar en vivo (precios, papers, existencia de modelos) vs qué
  puede ser conocimiento del modelo (marcar ESTIMADO).

### Fase 1 — Despacho en paralelo (delegate_task, batch mode)
- tasks: array de ≤3 subagentes, cada uno con goal + context.
- CONTEXT obligatorio (los subagentes no ven esta conversación):
  - Quién es el usuario y su stack/corpus/hardware/presupuesto (todo lo relevante).
  - Qué se concluyó ANTES (evita que re-investiguen lo ya sabido).
  - Idioma de salida (español aquí), formato (tablas ASCII, texto plano).
  - Leyenda [V]/[E]: [V] = verificado HOY con curl/API/navegador; [E] = estimado.
  - "No inventes precios/papers/IDs: si no puedes verificar, dilo y márcalo [E]."
  - "Incluye al final tu estimación de tokens usados."
- GOAL: autocontenido, con entregables explícitos (secciones, tablas, ranking).
- role: leaf (no anidan delegación — max_spawn_depth=1 en esta config).

### Fase 2 — Trabajo propio mientras corren
- Mientras los subagentes corren, verifica TÚ datos complementarios que
  alimentarán la síntesis (modelos candidatos, guías oficiales, formatos).
- Monitoreo opcional: tail -f /home/usuario/.hermes/cache/delegation/live/<id>/task-N.log
- NO hacer poll; los resultados entran solos como mensaje.

### Fase 3 — Verificación cruzada (obligatoria, aunque el subagente diga "verificado")
- Los resúmenes de subagentes son SELF-REPORTS. Spot-check 3-4 claims clave:
  - Papers: curl -sL https://arxiv.org/abs/<ID> | grep -oP '(?<=<title>).*?(?=</title>)'
  - Modelos: curl -s "https://huggingface.co/api/models/<org>/<name>" (downloads, tags)
  - Precios: curl a la página; si es JS/anti-bot -> [E], nunca inventar.
- Si el subagente guardó archivos: verifica que existan (ls) y lee el principio.
- CORRECCIÓN DE IDS: los papers tienen IDs canónicos; verifica el /abs/ (ej. InPars
  = 2202.05144, NO 2202.11757). No cites un paper sin confirmar su página.

### Fase 4 — Síntesis y entregables
- Persiste TODO en disco (los subagentes pueden no guardar nada: el informe de
  proveedores GPU solo existía en memoria del subagente -> hubo que re-crearlo).
- Convención del usuario: informe .md + .txt (texto plano sin markdown, mismo
  contenido). Carpeta de proyecto en D:\PyCode\<Proyecto>\.
- Estructura: resumen ejecutivo -> hallazgos por track (con [V]/[E]) -> ranking/
  matriz ponderada si aplica -> plan por días -> auto-crítica (qué NO se pudo
  verificar) -> estimación de tokens totales -> costo económico.
- Actualiza el skill del dominio afectado (ej. llm-finetuning-legal) con lo nuevo.

## Plantilla de task (copia y adapta)

goal: "Investigar A FONDO <tema>. Responder en ESPAÑOL. Entregar informe con:
<secciones>. Marcar [V]/[E] en cada afirmación. Usa curl para verificar <fuentes>.
No inventes <papers/precios>: si no puedes verificar, dilo. Incluye estimación de
tokens usados."

context: "<Perfil usuario + stack + corpus + hardware + presupuesto>. Ya concluido
antes: <resumen>. Formato: texto plano, tablas ASCII, español, URLs de fuentes.
Leyenda: [V]=verificado HOY en vivo, [E]=estimado."

## Pitfalls (lecciones reales)
1. Páginas JS/anti-bot (precios chinos, DeepSeek API, AutoTrain): curl devuelve
   HTML vacío o 432 bytes -> marcar [E], no forzar.
2. Límite de iteraciones del subagente: ~50 api_calls; si no alcanza a verificar
   todo, los no verificados van a la lista [E] explícita.
3. Archivos colaterales: los subagentes pueden crear archivos en la carpeta de
   trabajo (¡apareció un .env con tokens de GitHub!). Tras el batch, lista la
   carpeta (ls -la) y revisa archivos nuevos antes de entregar; avisar al usuario.
4. Descripción de skill <=60 chars (el índice trunca a 57); trigger primero,
   termina en punto. CUIDADO: dos puntos dentro del valor YAML rompen el parseo —
   usar comillas o evitar ": " en la descripción.
5. El resumen consolidado de delegate_task se TRUNCA; leer los archivos:
   /home/usuario/.hermes/cache/delegation/subagent-summary-<N>-<ts>.txt
6. Kaggle/Modal/Vast verificado 2026-08: 30h/sem gratis, $30/mes gratis,
   4090 desde $0.136/h (ver skill llm-finetuning-legal para la tabla completa).

## Referencia de trabajo
- Caso validado: /mnt/d/PyCode/FineTuningLegal/ (4 informes + adenda, 2026-08-04)
- Skills de dominio actualizados con el patrón: llm-finetuning-legal
- Stack apex completo instalado: apex-research-framework (estrategia) +
  competitive-research-ai-projects (ejecución API) + research-synthesis-html-preview
  (producción). Apex exige: red teaming "El Fiscal", checklist de saturación 15
  items, benchmark 0.01% (Musk+Simons+Nobel), matriz de escenarios, BLUF.
