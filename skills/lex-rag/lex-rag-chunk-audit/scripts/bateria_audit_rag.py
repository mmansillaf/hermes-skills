"""
BATERÍA DE 20 PREGUNTAS - Auditoría Granular de Chunks
======================================================
Ejecuta N consultas contra graphrag_pro.py, captura audit JSON,
y genera reporte TXT consolidado con tabla de métricas de retrieval.

USO:
  python3 scripts/bateria_20_audit.py     # ejecuta las 20 queries
  python3 scripts/bateria_20_audit.py --custom-lista queries.json  # lista propia

REQUISITOS:
  - graphrag_pro.py funcional (FAISS+BM25+NetworkX+Groq)
  - Los audit JSON deben generarse en consultas_guardadas/

ESTRUCTURA DEL REPORTE:
  - Tabla resumen: ID | Éxito | T(s) | Nivel | Materia | FAISS | BM25 | RRF
  - Detalle por consulta: métricas de retrieval, top-3 chunks RRF, grafo, respuesta
"""
import os, sys, json, re, time, subprocess, glob
from datetime import datetime

PROJECT_DIR = "/mnt/d/PyCode/ResumenTokensJurisprudencias"
PYTHON_EXE = "python3"
REPORT_DIR = os.path.join(PROJECT_DIR, "consultas_guardadas")

# ─── 20 PREGUNTAS POR DEFECTO (4 niveles × 5) ───
DEFAULT_QUERIES = [
    # Nivel 1: Simple
    {"id": "P01", "nivel": 1, "materia": "Laboral", "desc": "Despido arbitrario",
     "query": "despido arbitrario"},
    {"id": "P02", "nivel": 1, "materia": "Civil", "desc": "Nulidad de cosa juzgada fraudulenta",
     "query": "nulidad de cosa juzgada fraudulenta"},
    {"id": "P03", "nivel": 1, "materia": "Familia", "desc": "Medidas protección violencia familiar",
     "query": "medidas de proteccion en violencia familiar"},
    {"id": "P04", "nivel": 1, "materia": "Tributario", "desc": "Gastos deducibles renta",
     "query": "gastos deducibles impuesto a la renta"},
    {"id": "P05", "nivel": 1, "materia": "Constitucional", "desc": "Procedencia hábeas data",
     "query": "procedencia del habeas data"},
    # Nivel 2: Mediana
    {"id": "P06", "nivel": 2, "materia": "Laboral", "desc": "Reposición + desnaturalización",
     "query": "reposicion por desnaturalizacion de contrato modal"},
    {"id": "P07", "nivel": 2, "materia": "Laboral", "desc": "Horas extras + comisiones",
     "query": "procedencia del pago de horas extras y comisiones"},
    {"id": "P08", "nivel": 2, "materia": "Constitucional-Tributario", "desc": "No confiscatoriedad",
     "query": "aplicacion del principio de no confiscatoriedad en tributos"},
    {"id": "P09", "nivel": 2, "materia": "Civil-Procesal", "desc": "Caducidad civil",
     "query": "excepcion de caducidad en procesos civiles"},
    {"id": "P10", "nivel": 2, "materia": "Penal", "desc": "Prescripción penal",
     "query": "prescripcion de la accion penal en delitos"},
    # Nivel 3: Compleja
    {"id": "P11", "nivel": 3, "materia": "Laboral", "desc": "Reposición contrato servicio específico",
     "query": "cuales son los requisitos para que proceda la reposicion de un trabajador contratado por servicio especifico cuando la empresa extingue el vinculo antes de concluir la obra contratada"},
    {"id": "P12", "nivel": 3, "materia": "Constitucional-Laboral", "desc": "TC + reposición modales",
     "query": "que criterios ha establecido el tribunal constitucional sobre el derecho al trabajo y la reposicion en casos de contratos modales desnaturalizados"},
    {"id": "P13", "nivel": 3, "materia": "Civil-Procesal", "desc": "Nulidad fraude vs nulidad oficio",
     "query": "diferencia entre la nulidad de cosa juzgada fraudulenta y la nulidad de oficio segun la jurisprudencia de la corte suprema"},
    {"id": "P14", "nivel": 3, "materia": "Laboral-Procesal", "desc": "Casación infracción normativa",
     "query": "procedencia del recurso de casacion por infraccion normativa en procesos laborales sobre pago de beneficios sociales"},
    {"id": "P15", "nivel": 3, "materia": "Tributario", "desc": "TF + capacidad contributiva",
     "query": "cual es la tendencia jurisprudencial del tribunal fiscal respecto a la aplicacion del principio de capacidad contributiva en el impuesto a la renta de tercera categoria"},
    # Nivel 4: Estadística / Topológica
    {"id": "P16", "nivel": 4, "materia": "Estadístico", "desc": "Juez con más sentencias",
     "query": "que juez de la corte suprema ha emitido mas sentencias sobre despido arbitrario"},
    {"id": "P17", "nivel": 4, "materia": "Estadístico", "desc": "Leyes más citadas",
     "query": "cuales son las leyes mas citadas en los procesos laborales sobre reposicion"},
    {"id": "P18", "nivel": 4, "materia": "Estadístico", "desc": "Entidad más demandada",
     "query": "que entidad del estado es la mas demandada en procesos de habeas data"},
    {"id": "P19", "nivel": 4, "materia": "Comparativo", "desc": "TC vs Corte Suprema",
     "query": "comparar el tratamiento del despido arbitrario entre el tribunal constitucional y la corte suprema"},
    {"id": "P20", "nivel": 4, "materia": "Hipótesis", "desc": "Despido verbal sin carta",
     "query": "un trabajador fue despedido verbalmente sin carta de preaviso ni comunicacion escrita, que acciones legales proceden segun la jurisprudencia peruana"},
]


def escape_shell_query(q):
    return q.replace('"', '\\"').replace("'", "\\'")


def run_query(q_item):
    q = q_item["query"]
    safe_q = escape_shell_query(q)
    cmd = f'cd {PROJECT_DIR} && {PYTHON_EXE} graphrag_pro.py --query "{safe_q}"'
    start = time.time()
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                timeout=180, encoding='utf-8', errors='replace')
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        return {"success": True, "output": output, "elapsed": elapsed}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "[TIMEOUT]", "elapsed": 180}
    except Exception as e:
        return {"success": False, "output": f"[ERROR] {e}", "elapsed": time.time() - start}


def find_latest_audit():
    files = sorted(glob.glob(os.path.join(REPORT_DIR, "*_audit.json")), key=os.path.getmtime)
    return files[-1] if files else None


def load_audit(path):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def count_source_distribution(hybrid):
    faiss_docs = set(c["doc_id"] for c in hybrid.get("faiss_raw", []))
    bm25_docs = set(c["doc_id"] for c in hybrid.get("bm25_raw", []))
    return {
        "only_faiss": len(faiss_docs - bm25_docs),
        "only_bm25": len(bm25_docs - faiss_docs),
        "both": len(faiss_docs & bm25_docs),
        "rrf_top": len(hybrid.get("rrf_ranked", [])),
        "filtered_out": len(hybrid.get("chunks_filtered_out", [])),
    }


def build_report(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"{'='*80}", f"BATERÍA DE {len(results)} PREGUNTAS - AUDITORÍA GRANULAR DE CHUNKS",
             f"Generado: {now}", f"Sistema: Lex RAG Pro (FAISS+BM25+NetworkX+Groq)",
             f"{'='*80}", ""]

    total_ok = sum(1 for r in results if r["success"])
    total_time = sum(r["elapsed"] for r in results)
    lines.extend([f"Total consultas: {len(results)}", f"Exitosas: {total_ok}",
                  f"Fallidas: {len(results) - total_ok}", f"Tiempo total: {total_time:.1f}s",
                  f"Promedio: {total_time/len(results):.1f}s", ""])

    for nivel in range(1, 5):
        nq = [r for r in results if r["nivel"] == nivel]
        lines.append(f"  Nivel {nivel}: {len(nq)} consultas, {sum(r['elapsed'] for r in nq):.1f}s total")
    lines.append("")

    lines.append("-" * 80)
    lines.append(f"{'ID':<5} {'T(s)':<7} {'Nivel':<6} {'Materia':<28} {'FAISS':<7} {'BM25':<7} {'RRF':<5} {'Desc':<20}")
    lines.append("-" * 80)

    for r in results:
        audit = r.get("audit")
        if audit and audit.get("retrieval", {}).get("hybrid"):
            d = count_source_distribution(audit["retrieval"]["hybrid"])
            faiss_s, bm25_s, rrf_s = f"{d['only_faiss']}", f"{d['only_bm25']}", f"{d['rrf_top']}"
        else:
            faiss_s = bm25_s = rrf_s = "?"
        lines.append(f"{r['id']:<5} {r['elapsed']:<7.1f} {r['nivel']:<6} {r['materia']:<28} {faiss_s:<7} {bm25_s:<7} {rrf_s:<5} {r['desc'][:20]}")

    lines.extend(["", "=" * 80, "DETALLE POR CONSULTA", "=" * 80, ""])

    for r in results:
        lines.extend(["#" * 80,
                      f"## {r['id']} | Nivel {r['nivel']} | {r['materia']}",
                      f"**Desc:** {r['desc']}", f"**Query:** {r['query'][:100]}",
                      f"**Tiempo:** {r['elapsed']:.1f}s", f"**Estado:** {'✅' if r['success'] else '❌'}"])

        audit = r.get("audit")
        if audit:
            meta = audit["metadata"]
            lines.extend([f"**Router:** {meta.get('decision','?')}",
                          f"**HyDE:** {meta.get('hyde_query','?')[:120]}..."])
            hybrid = audit.get("retrieval", {}).get("hybrid", {})
            if hybrid:
                d = count_source_distribution(hybrid)
                lines.extend(["", "--- RETRIEVAL HÍBRIDO ---",
                              f"FAISS raw: {len(hybrid.get('faiss_raw',[]))} | BM25 raw: {len(hybrid.get('bm25_raw',[]))}",
                              f"Solo FAISS: {d['only_faiss']} | Solo BM25: {d['only_bm25']} | Ambos: {d['both']}",
                              f"RRF top: {d['rrf_top']} | Filtrados: {d['filtered_out']} | Docs finales: {len(hybrid.get('final_docs',[]))}", ""])
                lines.append(f"Top-3 chunks RRF:")
                for c in hybrid.get("rrf_ranked", [])[:3]:
                    lines.append(f"  #{c['rank']} | doc={c['doc_id']} | rrf={c['rrf_score']:.5f}")
                    lines.append(f"    {c['snippet'][:150]}...")

            graph = audit.get("retrieval", {}).get("graph", {})
            if graph:
                lines.extend(["", "--- CONTEXTO DEL GRAFO ---",
                              f"Nodos: {len(graph.get('nodes_with_data',[]))}",
                              f"Vecinos únicos: {len(graph.get('neighbors_found',[]))}",
                              f"Aristas: {graph.get('total_edges_processed',0)}", ""])
        else:
            lines.append("[Sin auditoría]")

        response_text = r.get("response", "")
        lines.extend(["--- RESPUESTA ---", response_text[:1000] if response_text else "[Sin respuesta]", ""])

    lines.extend(["", "=" * 80, "FIN DEL REPORTE", "=" * 80])
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Batería de consultas con auditoría granular")
    parser.add_argument("--custom-lista", type=str, help="Archivo JSON con lista de queries")
    args = parser.parse_args()

    queries = DEFAULT_QUERIES
    if args.custom_lista:
        with open(args.custom_lista, "r", encoding="utf-8") as f:
            queries = json.load(f)

    print(f"{'='*80}")
    print(f"BATERÍA DE {len(queries)} PREGUNTAS - AUDITORÍA GRANULAR")
    print(f"{'='*80}\n")

    results = []
    for i, q in enumerate(queries):
        print(f"[{i+1}/{len(queries)}] {q['id']} | Nivel {q['nivel']} | {q['materia']}")
        print(f"  Query: {q['query'][:80]}...", end=" ")
        sys.stdout.flush()

        prev = find_latest_audit()
        result = run_query(q)
        result.update(q)
        result["response"] = "🏛️ MAGISTRADO IA..."  # simplified
        new_audit = find_latest_audit()
        result["audit"] = load_audit(new_audit) if new_audit and new_audit != prev else None

        print(f"→ {'✅' if result['success'] else '❌'} {result['elapsed']:.1f}s")
        results.append(result)

    print("\nGenerando reporte consolidado...")
    report = build_report(results)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(PROJECT_DIR, f"data/bateria_audit_{ts}.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ Reporte: {path}")
    print(f"Resumen: {sum(1 for r in results if r['success'])}/{len(results)} exitosas, "
          f"{sum(r['elapsed'] for r in results):.1f}s total")


if __name__ == "__main__":
    main()
