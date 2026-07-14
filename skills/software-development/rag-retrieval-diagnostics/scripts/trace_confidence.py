#!/usr/bin/env python3
"""Script de traza reutilizable para diagnosticar confidence_score().
Importa la funcion directamente y ejecuta paso a paso con queries reales."""
import sys, os, json, time, requests, sqlite3, re

PROJ = os.path.expanduser("~/el_peruano_rag/PeruanoSearchEngine02")
sys.path.insert(0, PROJ)
os.chdir(PROJ)

import importlib.util
spec = importlib.util.spec_from_file_location("api_rest", os.path.join(PROJ, "api_rest.py"))
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

API = "http://localhost:8000"

def trace_query(question, qid="?"):
    resp = requests.post(f"{API}/query", json={"question": question, "profile": "abogado", "top_k": 15}, timeout=120)
    d = resp.json()
    results = d.get("results", [])
    sqlite_source_count = d.get("sources", {}).get("sqlite", {}).get("count", 0)
    
    conf, debug = api.confidence_score(results, question, sqlite_source_count)
    
    sqlite_scores = [r["relevance"] for r in results if r.get("source") == "sqlite"]
    max_sqlite = max(sqlite_scores) if sqlite_scores else 0.0
    sqlite_quality = max_sqlite * 0.55
    
    qdrant_scores = [r.get("_qdrant_score", 0.0) for r in results 
                     if r.get("source") == "qdrant" or r.get("_qdrant_contributed")]
    max_qdrant = max(qdrant_scores) if qdrant_scores else 0.0
    avg_qdrant = sum(qdrant_scores) / len(qdrant_scores) if qdrant_scores else 0.0
    semantic_quality = (max_qdrant * 0.7 + avg_qdrant * 0.3) * 0.5
    
    count_score = min(len(results) / 15.0, 1.0) * 0.15
    sqlite_boost = 0.1 if len(sqlite_scores) > 2 else 0.0
    base = semantic_quality + count_score + sqlite_boost
    
    print(f"[{qid}] conf={conf:.4f} | base={base:.4f} | sem_q={semantic_quality:.4f}")
    print(f"     debug: {json.dumps(debug, default=str)}")
    print(f"     answer: {d['answer'][:100]}...")
    return conf, debug

if __name__ == "__main__":
    queries = [
        ("B01", "Que numero de resolucion ministerial formaliza la aprobacion del POI 2024 del MINEDU?"),
        ("I30", "Segun el Acuerdo de Concejo N 618, por que motivo tecnico no fueron ratificados 8 derechos de tramite de copias de planos?"),
        ("B15", "Cual es el valor de la UIT vigente utilizada como referencia en el Anexo A del Acuerdo de Concejo N 618?"),
        ("A38", "La RVM N 003-2024-MINEDU menciona implementacion progresiva sujeta a presupuesto. Que tension constitucional existe?"),
    ]
    
    print("=" * 80)
    print("TRACE CONFIDENCE SCORE")
    print("=" * 80)
    for qid, q in queries:
        trace_query(q, qid)
