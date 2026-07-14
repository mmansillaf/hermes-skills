#!/usr/bin/env python3
"""
BATERIA DE PRUEBAS — El Peruano RAG
Template listo para copiar, personalizar preguntas y ejecutar.
Guarda JSON + TXT + MD/HTML en reports/.
"""
import requests, json, time, os
from datetime import datetime

API = "http://localhost:8000"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_DIR = os.path.expanduser("~/el_peruano_rag/PeruanoSearchEngine02/reports")
os.makedirs(REPORT_DIR, exist_ok=True)

QUERIES = [
    ("B01", "pregunta basica aqui", "basico"),
    ("I01", "pregunta intermedia aqui", "intermedio"),
    ("A01", "pregunta avanzada aqui", "avanzado"),
]

def evaluate(conf, ans):
    has_content = len(ans) > 80 and "no se encontr" not in ans[:80]
    if has_content and conf >= 0.50: return "PASS"
    elif has_content: return "WARN"
    return "FAIL"

results = []
full_responses = []
t0 = time.time()

for i, (qid, question, level) in enumerate(QUERIES, 1):
    try:
        tq = time.time()
        resp = requests.post(f"{API}/query",
            json={"question": question, "profile": "abogado", "top_k": 15}, timeout=120)
        d = resp.json()
        elapsed = time.time() - tq
        conf = d["confidence"]
        ans = d.get("answer", "")
        sources = d.get("sources", {})
        sql_n = sources.get("sqlite", {}).get("count", 0)
        neo_n = sources.get("neo4j", {}).get("count", 0)
        web_n = sources.get("serper_web", {}).get("count", 0)
        verdict = evaluate(conf, ans)
        results.append({"id": qid, "level": level, "conf": conf, "verdict": verdict,
                        "sql": sql_n, "neo": neo_n, "web": web_n, "ms": elapsed*1000})
        full_responses.append({"id": qid, "question": question, "answer": ans,
                               "confidence": conf, "sources": sources})
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(verdict, "?")
        print(f"[{i:2d} {icon}] {verdict:4s} {qid:5s} conf={conf:.3f} "
              f"sql={sql_n} neo={neo_n} web={web_n} {elapsed:.0f}s | {question[:55]}...")
    except Exception as e:
        print(f"[{i:2d} 💥] ERROR {qid} — {str(e)[:60]}")
        results.append({"id": qid, "verdict": "ERROR", "level": level})

elapsed_total = time.time() - t0
full_path = os.path.join(REPORT_DIR, f"battery_{TIMESTAMP}.json")
with open(full_path, 'w', encoding='utf-8') as f:
    json.dump(full_responses, f, indent=2, ensure_ascii=False)
txt_path = os.path.join(REPORT_DIR, f"battery_qa_{TIMESTAMP}.txt")
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write(f"BATERIA — El Peruano RAG\nFecha: {TIMESTAMP}\n{'='*60}\n\n")
    for item in full_responses:
        f.write(f"[{item['id']}] CONF={item['confidence']:.3f}\n")
        f.write(f"Q: {item['question']}\nA: {item['answer']}\n{'-'*40}\n\n")

total = len(results)
pass_n = sum(1 for r in results if r["verdict"] == "PASS")
warn_n = sum(1 for r in results if r["verdict"] == "WARN")
fail_n = sum(1 for r in results if r["verdict"] == "FAIL")
print(f"\n{'='*60}")
print(f"  OK: {pass_n+warn_n}/{total} ({100*(pass_n+warn_n)/total:.0f}%)")
print(f"  PASS={pass_n} WARN={warn_n} FAIL={fail_n}")
print(f"  Tiempo: {elapsed_total:.0f}s ({elapsed_total/total:.1f}s/q)")
for level in ["basico", "intermedio", "avanzado"]:
    lr = [r for r in results if r["level"] == level]
    if lr:
        sp = sum(1 for r in lr if r["verdict"] == "PASS")
        sw = sum(1 for r in lr if r["verdict"] == "WARN")
        print(f"  {level}: {sp}P {sw}W")
print(f"\n  JSON: {full_path}")
print(f"  TXT:  {txt_path}")
