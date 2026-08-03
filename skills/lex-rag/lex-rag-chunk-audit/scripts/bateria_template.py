#!/usr/bin/env python3
"""Plantilla de batería de consultas para LexRAG — modelo compartido (sin subprocess).
Usa import directo de run_console_query(). NO usar redirect_stdout — rompe el async generator.
Personalizar: OUTDIR, PREGUNTAS, timeout."""
import os, sys, json, time, asyncio
from datetime import datetime

sys.path.insert(0, "/mnt/d/PyCode/ResumenTokensJurisprudencias")
from graphrag_pro import run_console_query

OUTDIR = "/mnt/d/PyCode/ResumenTokensJurisprudencias/consultas_guardadas"
os.makedirs(OUTDIR, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

PREGUNTAS = [
    ("Q01", "simple", "¿Qué es el amparo?"),
    ("Q02", "medio", "¿Cómo se configura el despido arbitrario?"),
    ("Q03", "complejo", "Análisis de la evolución del criterio del TC sobre..."),
]

RESULTADOS = []

async def run_one(cid, nivel, pregunta, i, total):
    t0 = time.time()
    try:
        respuesta, follow_ups, _ = await asyncio.wait_for(
            run_console_query(pregunta),
            timeout=300
        )
        elapsed = time.time() - t0
        
        safe_id = f"{TIMESTAMP}_{cid}_{nivel}"
        txt_path = f"{OUTDIR}/{safe_id}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"ID: {cid} | Nivel: {nivel}\nDuración: {elapsed:.1f}s\n\n")
            f.write(f"=== PREGUNTA ===\n{pregunta}\n\n=== RESPUESTA ===\n{respuesta}\n")
        
        import re
        fuentes = re.findall(r'📄 FUENTE: (Jurisprudencia/\S+\.html)', respuesta)
        
        print(f"  [{i}/{total}] ✅ {cid} ({nivel}) | {elapsed:.0f}s | {len(respuesta)}c | {len(fuentes)}📄", flush=True)
        return {"id": cid, "nivel": nivel, "status": "OK", "duracion_seg": round(elapsed,1),
                "archivo": txt_path, "respuesta_len": len(respuesta), "fuentes": len(fuentes)}
    except Exception as e:
        print(f"  [{i}/{total}] ❌ {cid} {str(e)[:80]}", flush=True)
        return {"id": cid, "nivel": nivel, "status": str(e)[:100], "duracion_seg": 0}

async def main():
    t0 = time.time()
    for i, (cid, nivel, pregunta) in enumerate(PREGUNTAS, 1):
        RESULTADOS.append(await run_one(cid, nivel, pregunta, i, len(PREGUNTAS)))
    
    total_t = time.time() - t0
    summary = f"{OUTDIR}/{TIMESTAMP}_resumen.json"
    with open(summary, "w", encoding="utf-8") as f:
        json.dump(RESULTADOS, f, ensure_ascii=False, indent=2)
    
    ok = sum(1 for r in RESULTADOS if r['status'] == 'OK')
    total_c = sum(r.get('respuesta_len',0) for r in RESULTADOS)
    print(f"\n{'═'*50}\n  {ok}/{len(PREGUNTAS)} OK | {total_t:.0f}s | {total_c:,} chars\n  {summary}\n{'═'*50}")

if __name__ == "__main__":
    asyncio.run(main())
