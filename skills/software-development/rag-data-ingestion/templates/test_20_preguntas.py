#!/usr/bin/env python3
"""
test_20_preguntas.py — Evalúa el RAG con N preguntas (configurable),
registra respuestas completas, puntúa cada una en 8 dimensiones y guarda reportes.

Personaliza la lista `PREGUNTAS` abajo para tu dominio.
Uso:
    cd /repo && PYTHONPATH=. python3 templates/test_20_preguntas.py
"""
import sys, json, time, glob, os, asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from retrieval.hybrid_search import get_hybrid_context
from agents.router import route_query_and_hyde
from core.llm_clients import groq_client

# ═══════════════════════════════════════════════════════════════
#  CONFIGURACIÓN — edita para tu dominio
# ═══════════════════════════════════════════════════════════════

PREGUNTAS = [
    # (pregunta, área_legal)
    ("indemnizacion por despido arbitrario como se calcula", "Laboral"),
    ("pago de beneficios sociales y gratificaciones truncas", "Laboral"),
    ("reintegro de remuneraciones y bonificaciones", "Laboral"),
    ("desnaturalizacion de contrato de trabajo y reposicion", "Laboral"),
    ("reposicion por despido incausado en regimen privado", "Laboral"),
    ("pago de utilidades a trabajadores", "Laboral"),
    ("pago de compensacion por tiempo de servicios CTS", "Laboral"),
    ("horas extras y trabajo en sobretiempo", "Laboral"),
    ("despido nulo por afiliacion sindical", "Laboral"),
    ("hostigamiento laboral y acoso en el trabajo", "Laboral"),
    ("incautacion de bien por garantia mobiliaria", "Comercial"),
    ("cobro de costos procesales y costas", "Comercial"),
    ("nulidad de remate judicial", "Comercial"),
    ("ejecucion de garantias", "Comercial"),
    ("obligacion de dar suma de dinero", "Comercial"),
    ("medida cautelar fuera del proceso", "Civil"),
    ("nulidad de acto juridico por falta de forma", "Civil"),
    ("desalojo por ocupacion precaria", "Civil"),
    ("indemnizacion por daños y perjuicios", "Civil"),
    ("prescripcion extintiva de la accion", "Civil"),
]

REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"
TOP_K = 7
SYNTHESIS_MODELS = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]

# ═══════════════════════════════════════════════════════════════
#  EVALUACIÓN
# ═══════════════════════════════════════════════════════════════

def evaluar_respuesta(pregunta, respuesta, area, tiempo):
    """Puntúa la respuesta en 8 dimensiones (max 10 puntos)."""
    r = respuesta.lower()
    puntaje = 0
    obs = []

    # 1. Respuesta directa (2 pt)
    intro_gen = any(p in respuesta[:50].lower() for p in [
        "la consulta", "para abordar", "la pregunta", "con respecto a",
        "en relacion a", "en cuanto a", "analizando", "revisando"])
    if not intro_gen:
        puntaje += 2
    else:
        obs.append("Intro generica")

    # 2. Citas (2 pt)
    tiene_cita = any(m in respuesta for m in ["CAS.", "EXP.", "RTF", "Cas.", "Exp."])
    if tiene_cita:
        puntaje += 2
    else:
        obs.append("Sin citas")

    # 3. Sin jerga tecnica (1 pt)
    if not any(w in r for w in ["grafo", "nodos", "topologia", "algoritmo", "vectores", "faiss", "bm25"]):
        puntaje += 1
    else:
        obs.append("Jerga tecnica")

    # 4. Longitud (1 pt)
    palabras = len(respuesta.split())
    if 100 <= palabras <= 600:
        puntaje += 1
    elif palabras < 100:
        obs.append(f"Muy corta ({palabras} pal)")
    else:
        obs.append(f"Muy larga ({palabras} pal)")

    # 5. Seccion jurisprudencia (1 pt)
    if "jurisprudencia citada" in r:
        puntaje += 1

    # 6. Sustantiva (1 pt)
    if len(respuesta) > 50 and "informacion insuficiente" not in r:
        puntaje += 1
    else:
        obs.append("Sin info suficiente")

    # 7. Tiempo (1 pt)
    if tiempo < 30:
        puntaje += 1
    else:
        obs.append(f"Lento ({tiempo:.0f}s)")

    # 8. Tono profesional (1 pt)
    if respuesta.count("###") <= 5 and respuesta.count("**") <= 20:
        puntaje += 1

    return {
        "puntaje": puntaje, "maximo": 10,
        "observaciones": obs, "palabras": palabras,
        "tiempo_s": round(tiempo, 1),
        "tiene_citas": tiene_cita, "intro_generica": intro_gen,
        "jerga_tecnica": any(w in r for w in ["grafo", "nodos"]),
        "tiene_jurisprudencia_seccion": "jurisprudencia citada" in r,
    }


async def test_pregunta(pregunta, area, idx):
    """Procesa una pregunta: router -> hybrid_search -> synthesis."""
    print(f"\n{'='*70}", flush=True)
    print(f"  [{idx+1}/{len(PREGUNTAS)}] {area}: \"{pregunta}\"", flush=True)
    print(f"{'='*70}", flush=True)

    t_start = time.time()

    decision, hyde = route_query_and_hyde(pregunta)
    print(f"  Router: {decision} | HyDE: {hyde[:70]}...", flush=True)

    top_docs = []
    hybrid_context = "Sin contexto"
    try:
        top_docs, hybrid_context, _ = get_hybrid_context(hyde, top_k=TOP_K)
        print(f"  Hybrid: {len(top_docs)} docs", flush=True)
    except Exception as e:
        print(f"  Error en hybrid_search: {e}", flush=True)

    prompt = (
        "Actua como un Magistrado de la Corte Suprema. Responde a la consulta "
        "basandote UNICA y EXCLUSIVAMENTE en el contexto recuperado.\n\n"
        f"CONTEXTO:\n{hybrid_context}\n\n"
        f"PREGUNTA: {pregunta}\n\n"
        "INSTRUCCIONES:\n"
        "0. RESPUESTA DIRECTA: Responde en la PRIMERA FRASE.\n"
        "1. Lenguaje juridico claro, CERO jerga tecnica.\n"
        "2. Cita identificadores de sentencias (CAS. N, EXP. N, RTF N).\n"
        "3. Tono profesional, abogado a colega.\n"
        "4. Al final, agrega '**Jurisprudencia citada:**' con lista."
    )

    respuesta = ""
    if groq_client:
        for model in SYNTHESIS_MODELS:
            try:
                resp = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Eres un Agente RAG Legal."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1, max_tokens=2000,
                )
                respuesta = resp.choices[0].message.content.strip()
                break
            except Exception as e:
                print(f"  Error con {model}: {e}", flush=True)

    t_elapsed = time.time() - t_start
    eval_res = evaluar_respuesta(pregunta, respuesta, area, t_elapsed)

    preview = respuesta[:200].replace('\n', ' | ')
    print(f"\n  [{eval_res['puntaje']}/{eval_res['maximo']}] {preview}...", flush=True)
    if eval_res["observaciones"]:
        print(f"  Obs: {', '.join(eval_res['observaciones'])}", flush=True)

    return {
        "idx": idx + 1, "area": area, "pregunta": pregunta,
        "respuesta": respuesta, "tiempo_s": round(t_elapsed, 1),
        "evaluacion": eval_res, "decision": decision, "hyde": hyde,
        "top_docs": len(top_docs) if isinstance(top_docs, list) else 0,
    }


async def main():
    resultados = []
    for i, (q, area) in enumerate(PREGUNTAS):
        try:
            r = await test_pregunta(q, area, i)
            resultados.append(r)
        except Exception as e:
            print(f"  ERROR en pregunta {i+1}: {e}", flush=True)
            resultados.append({
                "idx": i+1, "area": area, "pregunta": q,
                "respuesta": f"ERROR: {e}", "tiempo_s": 0,
                "evaluacion": {"puntaje": 0, "maximo": 10,
                               "observaciones": ["Error de ejecucion"]},
                "decision": "ERROR", "hyde": q, "top_docs": 0,
            })

    # ── Resumen ──
    total_puntaje = sum(r["evaluacion"]["puntaje"] for r in resultados)
    max_posible = sum(r["evaluacion"]["maximo"] for r in resultados)
    n = len(resultados)
    promedio = total_puntaje / n if n else 0

    areas = {}
    for r in resultados:
        a = r["area"]
        areas.setdefault(a, {"total": 0, "count": 0})
        areas[a]["total"] += r["evaluacion"]["puntaje"]
        areas[a]["count"] += 1

    metricas = {
        "citas": sum(1 for r in resultados if r["evaluacion"]["tiene_citas"]),
        "intro_gen": sum(1 for r in resultados if r["evaluacion"]["intro_generica"]),
        "jerga": sum(1 for r in resultados if r["evaluacion"]["jerga_tecnica"]),
        "sec_juris": sum(1 for r in resultados if r["evaluacion"]["tiene_jurisprudencia_seccion"]),
    }

    print("\n\n" + "=" * 70)
    print(f"  REPORTE FINAL — {n} PREGUNTAS")
    print(f"  Puntaje: {total_puntaje}/{max_posible} ({total_puntaje/max_posible*100:.1f}%)")
    print(f"  Promedio: {promedio:.1f}/10")
    for area, d in sorted(areas.items()):
        print(f"  {area:25s}: {d['total']}/{d['count']*10} ({d['total']/(d['count']*10)*100:.1f}%)")
    print(f"  Respuesta directa: {n - metricas['intro_gen']}/{n} ({(n-metricas['intro_gen'])/n*100:.0f}%)")
    print(f"  Con citas: {metricas['citas']}/{n} ({metricas['citas']/n*100:.0f}%)")
    print(f"  Sin jerga: {n - metricas['jerga']}/{n} ({(n-metricas['jerga'])/n*100:.0f}%)")
    print(f"  Seccion jurisprudencia: {metricas['sec_juris']}/{n} ({metricas['sec_juris']/n*100:.0f}%)")
    print(f"  Tiempo promedio: {sum(r['tiempo_s'] for r in resultados)/n:.1f}s")

    # ── Guardar reportes ──
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")

    # Resumen
    lines = []
    lines.append("=" * 70)
    lines.append(f"  REPORTE — {n} PREGUNTAS ({ts})")
    lines.append("=" * 70)
    for r in resultados:
        ev = r["evaluacion"]
        lines.append(f"[{r['idx']:2d}] {r['area']:20s} | {ev['puntaje']}/{ev['maximo']} | {ev['tiempo_s']:5.1f}s | {ev['palabras']:4d}pal")
        lines.append(f"     Pregunta: {r['pregunta']}")
        lines.append(f"     Obs: {', '.join(ev['observaciones']) or 'Ninguna'}")
    lines.append(f"\nTotal: {total_puntaje}/{max_posible} ({total_puntaje/max_posible*100:.1f}%)")
    (REPORT_DIR / f"test_preguntas_resumen_{ts}.txt").write_text("\n".join(lines), encoding="utf-8")

    # Respuestas completas
    lines2 = ["=" * 70,
              f"  RESPUESTAS COMPLETAS — {n} PREGUNTAS ({ts})",
              "=" * 70]
    for r in resultados:
        ev = r["evaluacion"]
        lines2.append(f"\n[{r['idx']:2d}] {r['area']:20s} | {ev['puntaje']}/{ev['maximo']} | {ev['tiempo_s']:.1f}s")
        lines2.append(f"PREGUNTA: {r['pregunta']}")
        lines2.append(f"RESPUESTA:\n{r['respuesta']}")
        if ev["observaciones"]:
            lines2.append(f"OBS: {', '.join(ev['observaciones'])}")
        lines2.append("-" * 70)
    (REPORT_DIR / f"test_preguntas_completas_{ts}.txt").write_text("\n".join(lines2), encoding="utf-8")

    # JSON
    (REPORT_DIR / f"test_preguntas_raw_{ts}.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  Reportes en {REPORT_DIR}/")
    print(f"  test_preguntas_resumen_{ts}.txt")
    print(f"  test_preguntas_completas_{ts}.txt")
    print(f"  test_preguntas_raw_{ts}.json")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
