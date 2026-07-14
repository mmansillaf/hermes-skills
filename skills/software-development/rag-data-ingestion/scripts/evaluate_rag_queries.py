#!/usr/bin/env python3
"""
evaluate_rag_queries.py — Run a structured query evaluation against a RAG system.
Measures: time, citation rate, legal references, entity extraction, follow-ups.
Output: TXT + MD reports in reports/evaluacion_rag_*.{txt,md}

Usage:
    cd /repo && PYTHONPATH=. python3 scripts/evaluate_rag_queries.py
"""
import asyncio, sys, json, time, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from graphrag_pro import run_console_query

QUESTIONS = [
    ("Mi empleador no me pago las utilidades del ultimo ano, puedo demandarlo?", "Alta", "Laboral"),
    ("Cual es el monto de indemnizacion por despido arbitrario en Peru?", "Alta", "Laboral"),
    ("Como se calcula el reintegro de remuneraciones para pescadores?", "Media", "Laboral"),
    ("Cual es la diferencia entre despido arbitrario y despido incausado?", "Alta", "Laboral"),
    ("Que dice el Codigo Procesal Civil sobre ejecucion de garantias?", "Media", "Comercial"),
    ("Como se tramita una obligacion de dar suma de dinero en via ejecutiva?", "Media", "Comercial"),
    ("Como se calcula la pension de alimentos para un menor de edad?", "Alta", "Familia"),
    ("Que requisitos se necesitan para demanda de tenencia y custodia?", "Media", "Familia"),
    ("Que entidad regula el pago de utilidades a trabajadores en Peru?", "Baja", "Laboral"),
    ("Donde puedo ver el estado de mi expediente judicial en el PJ?", "Baja", "Transversal"),
]

OUTPUT_DIR = Path(__file__).parent.parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)

def measure(response_text):
    return {
        "palabras": len(response_text.split()), "caracteres": len(response_text),
        "tiene_citas": "Jurisprudencia citada" in response_text,
        "tiene_juez": "Juez" in response_text or "Magistrado" in response_text,
        "tiene_ley": any(kw in response_text for kw in ["Ley", "Codigo", "articulo"]),
    }

async def ejecutar():
    print("=" * 80)
    print(f"  RAG EVALUATION — {len(QUESTIONS)} preguntas    {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    resultados = []

    for i, (q, nivel, area) in enumerate(QUESTIONS, 1):
        t0 = time.time()
        respuesta = ""
        try:
            respuesta, follow_ups, _ = await run_console_query(q)
        except Exception as e:
            respuesta = f"[ERROR] {e}"
        elapsed = time.time() - t0
        m = measure(respuesta)
        resultados.append({**m, "n": i, "pregunta": q, "nivel": nivel, "area": area,
                          "tiempo_seg": round(elapsed,1), "respuesta": respuesta,
                          "follow_ups": len(follow_ups) if follow_ups else 0})
        print(f"  [{i}] {nivel:4s} {area:10s} {elapsed:5.1f}s  {m['palabras']:3d}pal  Citas={'S' if m['tiene_citas'] else 'N'}  Ley={'S' if m['tiene_ley'] else 'N'}")

    # Summary
    t = [r["tiempo_seg"] for r in resultados]
    print(f"\n  Promedio: {sum(t)/len(t):.1f}s  Citas: {sum(1 for r in resultados if r['tiene_citas'])}/{len(resultados)}  Leyes: {sum(1 for r in resultados if r['tiene_ley'])}/{len(resultados)}")
    print(f"  Follow-ups: {sum(r['follow_ups'] for r in resultados)}")

    # Save TXT
    ts = time.strftime("%Y%m%d_%H%M%S")
    with open(OUTPUT_DIR / f"evaluacion_rag_{ts}.txt", "w") as f:
        for r in resultados:
            f.write(f"[{r['n']}] {r['pregunta']}  ({r['nivel']}/{r['area']})  {r['tiempo_seg']}s\n")
            f.write(f"    Pal={r['palabras']} Citas={'S' if r['tiene_citas'] else 'N'}\n")
            f.write(f"    RESPUESTA:\n{r['respuesta']}\n{'='*60}\n\n")
    # Save MD
    with open(OUTPUT_DIR / f"evaluacion_rag_{ts}.md", "w") as f:
        f.write(f"# Evaluacion RAG - {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| # | Pregunta | Nivel | Area | T(s) | Pal | Citas | Leyes |\n|---|---|---|---|---|---|---|---|\n")
        for r in resultados:
            f.write(f"| {r['n']} | {r['pregunta'][:60]} | {r['nivel']} | {r['area']} | {r['tiempo_seg']} | {r['palabras']} | {'S' if r['tiene_citas'] else 'N'} | {'S' if r['tiene_ley'] else 'N'} |\n")
        f.write(f"\n## Resumen\nPromedio: {sum(t)/len(t):.1f}s  Citas: {sum(1 for r in resultados if r['tiene_citas'])}/{len(resultados)}")

    print(f"\n  Reportes: {OUTPUT_DIR / f'evaluacion_rag_{ts}.txt'}")

if __name__ == "__main__":
    asyncio.run(ejecutar())
