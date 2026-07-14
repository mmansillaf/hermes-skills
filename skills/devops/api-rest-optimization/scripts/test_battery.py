#!/usr/bin/env python3
"""
Test battery multinivel para El Peruano RAG API.
Ejecuta 12 queries en 4 niveles (BASICO, INTERMEDIO, AVANZADO_ANALISIS, AVANZADO_CREACION).
Guarda reporte en reports/test_battery_YYYYMMDD.txt
Requiere: API corriendo en http://localhost:8000
"""

import urllib.request
import json
import time
import os
from pathlib import Path

API = os.getenv("API_URL", "http://localhost:8000")
OUTPUT_DIR = Path(__file__).parent.parent / "reports"

def query(question, profile="abogado", top_k=10):
    data = json.dumps({"question": question, "profile": profile, "top_k": top_k}).encode()
    req = urllib.request.Request(f"{API}/query", data=data,
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        elapsed = round((time.time() - t0) * 1000)
        return result, elapsed, None
    except Exception as e:
        return None, 0, str(e)

TESTS = [
    ("BASICO", "¿Cuál es la Ley 32108?"),
    ("BASICO", "¿Qué número tiene la ley de contrataciones del Estado?"),
    ("BASICO", "¿Cuántos artículos tiene el Decreto Supremo 004-2019-JUS?"),
    ("INTERMEDIO", "¿Qué requisitos establece el TUPA del Ministerio de Transportes?"),
    ("INTERMEDIO", "Explícame las normas sobre teletrabajo en Perú"),
    ("INTERMEDIO", "¿Qué dice la normativa sobre protección de datos personales?"),
    ("AVANZADO_ANALISIS", "Analiza la evolución normativa del régimen disciplinario de servidores públicos en Perú"),
    ("AVANZADO_ANALISIS", "Compara los regímenes laborales del sector público y privado según la normativa peruana"),
    ("AVANZADO_ANALISIS", "Evalúa la constitucionalidad de los decretos de urgencia en materia económica"),
    ("AVANZADO_CREACION", "Proponga un proyecto de ley para regular la inteligencia artificial en el sector público peruano"),
    ("AVANZADO_CREACION", "Redacte un dictamen jurídico sobre la viabilidad de implementar un sistema de voto electrónico"),
    ("AVANZADO_CREACION", "Formule una hipótesis sobre el impacto de la digitalización notarial en la seguridad jurídica"),
]

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d")
    output_path = OUTPUT_DIR / f"test_battery_{timestamp}.txt"

    results = []
    pass_count = 0
    fail_count = 0
    total_time = 0

    print(f"Test battery — {len(TESTS)} queries ({API})")
    print("=" * 60)

    for i, (nivel, question) in enumerate(TESTS, 1):
        print(f"[{i}/{len(TESTS)}] {nivel}: {question[:60]}...")
        result, elapsed, error = query(question)

        if error:
            print(f"  ❌ ERROR: {error}")
            fail_count += 1
            results.append({"nivel": nivel, "question": question, "error": error})
            continue

        confidence = result.get("confidence", 0)
        answer = result.get("answer", "")
        n_results = len(result.get("results", []))
        sources = list(result.get("sources", {}).keys())
        web_fallback = result.get("web_fallback_used", False)
        timing = result.get("timing_ms", elapsed)
        classification = result.get("classification", {})
        qtype = classification.get("query_type", "N/A") if classification else "N/A"

        status = "PASS" if answer and len(answer) > 50 else "FAIL"
        if status == "PASS":
            pass_count += 1
        else:
            fail_count += 1

        print(f"  {'✅' if status == 'PASS' else '⚠️'} conf={confidence:.2f} results={n_results} time={timing}ms web={web_fallback}")
        results.append({
            "nivel": nivel, "question": question, "confidence": confidence,
            "n_results": n_results, "timing_ms": timing, "web_fallback": web_fallback,
            "classification_type": qtype, "sources": sources, "answer": answer,
            "status": status
        })
        total_time += timing

    # Generate report
    api_lines = "?"
    try:
        api_py = Path(__file__).parent.parent / "api_rest.py"
        api_lines = str(len(api_py.read_text().splitlines()))
    except Exception:
        pass

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"TEST BATTERY — El Peruano RAG API\n")
        f.write(f"Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"api_rest.py: {api_lines} líneas\n")
        f.write("=" * 80 + "\n\n")

        for r in results:
            f.write(f"{'─' * 80}\n")
            f.write(f"NIVEL: {r['nivel']} | STATUS: {r.get('status','?')}\n")
            f.write(f"Pregunta: {r['question']}\n")
            f.write(f"Confianza: {r.get('confidence',0):.2f} | Resultados: {r.get('n_results',0)} | Tiempo: {r.get('timing_ms',0)}ms\n")
            f.write(f"Web fallback: {r.get('web_fallback',False)} | Tipo: {r.get('classification_type','N/A')}\n")
            f.write(f"Sources: {r.get('sources',[])}\n")
            f.write(f"\nRESPUESTA:\n{r.get('answer','ERROR')}\n\n")

        avg_time = total_time // len(TESTS) if len(TESTS) else 0
        f.write(f"\n{'=' * 80}\n")
        f.write(f"RESUMEN: {pass_count}/{len(TESTS)} PASS | {fail_count}/{len(TESTS)} FAIL | Promedio: {avg_time}ms\n")

    print(f"\n{'=' * 60}")
    print(f"RESUMEN: {pass_count}/{len(TESTS)} PASS | Promedio: {avg_time}ms")
    print(f"Reporte: {output_path}")


if __name__ == "__main__":
    main()
