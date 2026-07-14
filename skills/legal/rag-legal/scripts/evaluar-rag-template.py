#!/usr/bin/env python3
"""
evaluar_rag.py - Template para evaluar un RAG con N preguntas.
Mide: tiempo, docs recuperados, relevancia, presencia de leyes, calidad del fallo.
Genera reporte JSON y tabla resumen.

USO:
  cd /path/to/KGraphResolucionesV3
  PYTHONPATH=. python3 evaluar_rag.py

Personalizar:
  - preguntas: lista de (consulta, area_legal)
  - doc_map: cargar desde data_raw/rag_listo_batch_*.json
  - get_hybrid_context: adaptar a tu pipeline de retrieval
"""
import sys, json, time, glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from retrieval.hybrid_search import get_hybrid_context

# Cargar docs indexados
docs_data = []
for json_file in sorted(glob.glob("data_raw/rag_listo_batch_*.json")):
    with open(json_file) as f:
        docs_data.extend(json.load(f))

doc_map = {d.get("id_documento", ""): d for d in docs_data}

preguntas = [
    ("indemnizacion por despido arbitrario", "Laboral"),
    ("pago de beneficios sociales", "Laboral"),
    ("reintegro de remuneraciones", "Laboral"),
    ("desnaturalizacion de contrato de trabajo", "Laboral"),
    ("reposicion por despido incausado", "Laboral"),
    ("pago de utilidades", "Laboral"),
    ("cobro de costos procesales", "Transversal"),
    ("nulidad de resolucion administrativa", "Contencioso Admin"),
    ("incautacion de bien mueble por garantia mobiliaria", "Comercial"),
    ("medida cautelar fuera del proceso", "Civil"),
]

resultados = []
for q, area in preguntas:
    t0 = time.time()
    top_docs, _, _ = get_hybrid_context(q, top_k=5)
    elapsed = time.time() - t0

    r = {"pregunta": q, "area": area, "tiempo_s": round(elapsed, 1), "docs_recuperados": 0,
         "relevancia": "N/A", "fallo_concreto": False, "tiene_leyes": False}

    if isinstance(top_docs, list) and top_docs:
        r["docs_recuperados"] = len(top_docs)
        info = doc_map.get(top_docs[0], {})
        cv = info.get("contenido_a_vectorizar", {})
        mg = info.get("metadatos_graphrag", {})
        fallo = cv.get("fallo", "")
        leyes = mg.get("leyes_y_articulos_citados", [])

        r["fallo_concreto"] = bool(fallo and len(fallo) > 30 and "No se" not in fallo[:15])
        r["tiene_leyes"] = bool(leyes)
        r["top1_fallo"] = fallo[:200]
        r["top1_leyes"] = leyes[:5]
        r["top1_hechos"] = cv.get("hechos", "")[:150]

        if r["fallo_concreto"] and r["tiene_leyes"]:
            r["relevancia"] = "Alta"
        elif r["fallo_concreto"]:
            r["relevancia"] = "Media"
        else:
            r["relevancia"] = "Baja"

    resultados.append(r)
    print(f"  {q[:45]:45s} {r['relevancia']:>6s} | {elapsed:.1f}s | {r['docs_recuperados']} docs")

# Guardar
with open("reports/evaluacion_rag.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)
print(f"\nResultados: reports/evaluacion_rag.json")

# Resumen
altas = sum(1 for r in resultados if r["relevancia"] == "Alta")
print(f"\nResumen: {altas}/10 Alta | {sum(1 for r in resultados if r['relevancia']=='Media')}/10 Media | "
      f"{sum(1 for r in resultados if r['fallo_concreto'])}/10 fallo concreto | "
      f"{sum(1 for r in resultados if r['tiene_leyes'])}/10 con leyes")
