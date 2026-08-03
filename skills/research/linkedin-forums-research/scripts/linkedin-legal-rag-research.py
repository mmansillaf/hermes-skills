#!/usr/bin/env python3
"""
linkedin-legal-rag-research.py — Investigación de LinkedIn en dominio legal/RAG.

Ejecuta 33 queries Serper en 7 grupos temáticos + HN + Stack Overflow.
Queries cubren: RAG legal, IA+abogados, legal tech dev, jobs, intake automation,
Perú legal tech.

Uso:
  python3 linkedin-legal-rag-research.py

Pre-requisitos:
  - SERPER_API_KEY en .env o variable de entorno
  - pip install requests python-dotenv

Adaptación:
  - Para cambiar dominio, editar el dict QUERIES en la parte superior.
  - Para más/menos resultados, cambiar num=10 en serper_search().
  - Para tiempo personalizado, agregar tbs=qdr:m6 al JSON de Serper.

Ver SKILL.md de linkedin-forums-research para contexto completo.
"""

import requests, json, os, time, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from datetime import datetime

SERPER_URL = "https://google.serper.dev/search"
SERPER_KEY = None

def get_key():
    global SERPER_KEY
    if SERPER_KEY: return SERPER_KEY
    for path in ["/mnt/d/PyCode/PyGraphRAG_MM/.env", os.path.expanduser("~/.env")]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    if line.startswith("SERPER_API_KEY="):
                        SERPER_KEY = line.split("=",1)[1].strip().strip("'\"").strip()
                        return SERPER_KEY
    raise ValueError("SERPER_API_KEY no encontrada")

def serper(query, gl="pe", hl="es", num=10, months=None):
    key = get_key()
    params = {"q": query, "gl": gl, "hl": hl, "num": num}
    if months: params["tbs"] = f"qdr:m{months}"
    try:
        r = requests.post(SERPER_URL, json=params,
            headers={"X-API-KEY": key}, timeout=15)
        return r.json() if r.status_code == 200 else {"organic":[]}
    except: return {"organic":[]}

def is_li(url, pattern): return pattern in str(url).lower()
def is_profile(url): return is_li(url, "linkedin.com/in/")
def is_job(url): return is_li(url, "linkedin.com/jobs/")
def is_pulse(url): return is_li(url, "linkedin.com/pulse/")

QUERIES = {
    "rag_legal": [
        'site:linkedin.com/pulse RAG retrieval augmented generation legal',
        'site:linkedin.com/pulse "retrieval augmented generation" law legal',
        'site:linkedin.com/pulse RAG abogados derecho inteligencia artificial',
        'site:linkedin.com/pulse "adaptive RAG" legal',
        'site:linkedin.com/pulse "graph RAG" legal',
    ],
    "ai_abogados": [
        'site:linkedin.com/pulse "inteligencia artificial" abogados derecho',
        'site:linkedin.com/pulse "artificial intelligence" lawyer legal practice',
        'site:linkedin.com/pulse IA generativa derecho abogados Perú',
        'site:linkedin.com/pulse "AI" "legal profession" ethics regulation',
        'site:linkedin.com/in abogado "inteligencia artificial" legal tech',
    ],
    "legal_tech_dev": [
        'site:linkedin.com/pulse legal tech developer devops engineer AI',
        'site:linkedin.com/pulse legal technology software architecture RAG',
        'site:linkedin.com/pulse n8n automation legal workflow',
        'site:linkedin.com/pulse LLM fine-tuning legal documents',
        'site:linkedin.com/in legal tech developer engineer AI',
    ],
    "jobs_legal_tech": [
        'site:linkedin.com/jobs "legal tech" engineer developer AI',
        'site:linkedin.com/jobs "legal" "machine learning" engineer',
        'site:linkedin.com/jobs "RAG" legal OR law OR attorney',
        'site:linkedin.com/jobs legal technology Peru OR LATAM',
        'site:linkedin.com/jobs "intake automation" legal OR law firm',
    ],
    "intake_automation": [
        'site:linkedin.com/pulse "intake automation" legal OR law firm',
        'site:linkedin.com/pulse client intake AI automation legal',
        'site:linkedin.com/pulse WhatsApp chatbot legal abogados',
        'site:linkedin.com/jobs intake automation legal OR law firm',
    ],
    "peru_legal": [
        'site:linkedin.com/pulse legal tech Perú inteligencia artificial',
        'site:linkedin.com/pulse derecho tecnología Perú innovación legal',
        'site:linkedin.com/in legal tech Perú abogado digital',
        'site:linkedin.com/company legal tech Perú',
        'site:linkedin.com/jobs legal Perú tecnología derecho',
    ],
}

def run_group(group_name, queries, months=None):
    profiles, jobs, pulse, other = [], [], [], []
    seen = set()
    for q in queries:
        time.sleep(0.3)
        data = serper(q, months=months)
        for item in data.get("organic", []):
            link = item.get("link","")
            if link in seen: continue
            seen.add(link)
            if is_profile(link):
                profiles.append({"title":item.get("title",""),"snippet":item.get("snippet",""),"url":link})
            elif is_job(link):
                jobs.append({"title":item.get("title",""),"snippet":item.get("snippet",""),"url":link})
            elif is_pulse(link):
                pulse.append({"title":item.get("title",""),"snippet":item.get("snippet",""),"url":link})
        for item in data.get("jobs",[]):
            link = item.get("link","")
            if link and link not in seen and is_job(link):
                seen.add(link)
                jobs.append({"title":item.get("title",""),"snippet":item.get("snippet",""),"company":item.get("company",""),"url":link})
    return {"group":group_name,"profiles":profiles,"jobs":jobs,"pulse":pulse,
            "total":len(profiles)+len(jobs)+len(pulse)}

def main():
    print("="*65)
    print("  LINKEDIN LEGAL + RAG RESEARCH")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*65)
    all_r = {}
    for gn, qs in QUERIES.items():
        print(f"\n  Grupo: {gn} ({len(qs)} queries)")
        r = run_group(gn, qs)
        all_r[gn] = r
        print(f"    Perfiles: {len(r['profiles'])} | Jobs: {len(r['jobs'])} | Pulse: {len(r['pulse'])} | Total: {r['total']}")
    tp = sum(len(r['profiles']) for r in all_r.values())
    tj = sum(len(r['jobs']) for r in all_r.values())
    tpu = sum(len(r['pulse']) for r in all_r.values())
    print(f"\n  TOTAL: {tp} perfiles + {tj} jobs + {tpu} artículos Pulse = {tp+tj+tpu}")

if __name__ == "__main__":
    main()
