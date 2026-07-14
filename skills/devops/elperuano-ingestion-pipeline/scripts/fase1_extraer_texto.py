#!/usr/bin/env python3
"""Fase 1: Extraer texto_completo de HTML para normas sin texto"""
import sqlite3, os, re, time
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
        self.skip_tags = {'script', 'style', 'meta', 'link', 'head', 'title'}
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags: self.skip = True
    def handle_endtag(self, tag):
        if tag in self.skip_tags: self.skip = False
        if tag in ('p','br','div','h1','h2','h3','h4','h5','h6','li','tr','td'):
            self.text.append('\n')
    def handle_data(self, data):
        if not self.skip:
            t = data.strip()
            if t: self.text.append(t)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE_DIR, "data")
DB = os.path.join(DATA, "normas_total.db")

# Backup
backup_path = DB + f".bak_{int(time.time())}"
print(f"Backup: {backup_path}")
os.system(f"cp {DB} {backup_path}")

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=-64000")
cur = conn.cursor()

cur.execute("SELECT id, source_path FROM normas WHERE texto_completo IS NULL")
rows = cur.fetchall()
total = len(rows)
print(f"Normas sin texto: {total}")

success = fail_missing = fail_parse = 0
batch = []
start = time.time()

for i, (norma_id, source_path) in enumerate(rows):
    html_path = os.path.join(DATA, source_path)
    if not os.path.exists(html_path):
        fail_missing += 1; continue
    try:
        with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
            html = f.read()
        e = TextExtractor(); e.feed(html)
        text = ' '.join(e.text)
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r' +', ' ', text).strip()
        batch.append((text, norma_id))
        success += 1
    except Exception:
        fail_parse += 1
    if len(batch) >= 500 or i == total - 1:
        cur.executemany("UPDATE normas SET texto_completo = ? WHERE id = ?", batch)
        conn.commit()
        batch = []
    if (i + 1) % 10000 == 0 or i == total - 1:
        elapsed = time.time() - start
        rate = (i + 1) / elapsed
        eta = (total - i - 1) / rate
        print(f"  {i+1}/{total} ({round(100*(i+1)/total,1)}%) | {round(rate)}/s | "
              f"ok={success} miss={fail_missing} err={fail_parse} | ETA {round(eta)}s")

elapsed = time.time() - start
conn.close()
print(f"\nFASE 1: {success}/{total} ({round(100*success/total,1)}%) en {round(elapsed,1)}s")
print(f"Missing={fail_missing} ParseErr={fail_parse} Backup={backup_path}")
