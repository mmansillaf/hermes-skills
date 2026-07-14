#!/usr/bin/env python3
"""
Demo de estrategias de chunking semantico para documentos juridicos.
3 estrategias que respetan parrafos y no cortan ideas.

USO:
  python3 scripts/chunking-demo.py

Requiere: pdftotext instalado.
"""
import re, subprocess, json

def extraer_texto(path, max_chars=20000):
    res = subprocess.run(['pdftotext', '-layout', path, '-'],
                         capture_output=True, text=True, timeout=30)
    return res.stdout.strip()[:max_chars]

def detectar_parrafos(texto):
    texto = texto.replace('\r\n', '\n')
    raw = re.split(r'\n\n\n*', texto)
    parrafos = []
    pos = 0
    for p in raw:
        p = p.strip()
        if not p:
            pos += len(p) + 3
            continue
        lines = p.split('\n')
        es_titulo = any(
            line.strip().isupper() and 3 < len(line.strip()) < 80
            for line in lines[:3]
        ) or any(kw in p.upper() for kw in
            ['RESUELVE:', 'CONSIDERANDO:', 'FALLO:', 'S.S.',
             'VISTOS:', 'ASUNTO:', 'MATERIA:', 'EXPEDIENTE',
             'AUTO EMITIDO', 'SENTENCIA'])
        parrafos.append({
            'texto': p, 'start': pos, 'end': pos + len(p),
            'es_titulo': es_titulo, 'lines': len(lines), 'chars': len(p)
        })
        pos += len(p) + 3
    return parrafos

def chunk_por_parrafos(texto, max_chars=6000, overlap_chars=500):
    """Multi-pasada con overlap. Nunca corta un parrafo."""
    parrafos = detectar_parrafos(texto)
    if not parrafos:
        return []
    chunks = []
    current, current_chars = [], 0
    for p in parrafos:
        p_len = p['chars'] + 2
        if current_chars + p_len > max_chars and current:
            chunks.append({'texto': '\n\n'.join(current), 'chars': current_chars,
                          'parrafos': len(current), 'tipo': 'normal'})
            overlap = []
            oc = 0
            for cp in reversed(current):
                cpl = len(cp) + 2
                if oc + cpl > overlap_chars and overlap:
                    break
                overlap.insert(0, cp)
                oc += cpl
            current, current_chars = overlap, oc
        current.append(p['texto'])
        current_chars += p_len
    if current:
        chunks.append({'texto': '\n\n'.join(current), 'chars': current_chars,
                      'parrafos': len(current), 'tipo': 'normal'})
    return chunks

def chunk_priorizar_fallo(texto, max_chars=6000):
    """Toma ultimos parrafos (fallo) + inicio. Pierde el medio."""
    parrafos = detectar_parrafos(texto)
    if not parrafos:
        return []
    seleccionados, chars = [], 0
    for p in reversed(parrafos):
        if chars + p['chars'] + 2 > max_chars:
            break
        seleccionados.insert(0, p)
        chars += p['chars'] + 2
    restantes = [p for p in parrafos if p not in seleccionados]
    for p in restantes:
        if chars + p['chars'] + 2 > max_chars:
            break
        seleccionados.insert(0, p)
        chars += p['chars'] + 2
    return [{'texto': '\n\n'.join(p['texto'] for p in seleccionados),
             'chars': chars, 'parrafos': len(seleccionados),
             'tipo': 'fallo-priorizado',
             'incluye_resuelve': any('RESUELVE' in p['texto'] for p in seleccionados),
             'incluye_ss': any('S.S.' in p['texto'] for p in seleccionados)}]

if __name__ == '__main__':
    # Prueba con un PDF de ejemplo
    import glob
    test_dir = '/home/usuario/Escritorio/PyCode/QwenLegalExtractor/samples_test'
    pdfs = sorted(glob.glob(f'{test_dir}/*.pdf'))
    if not pdfs:
        print("No hay PDFs de prueba. Crea samples_test/ con algunos PDFs.")
        exit(1)
    texto = extraer_texto(pdfs[0])
    print(f"Documento: {pdfs[0]}")
    print(f"Total chars: {len(texto)}")
    print()
    chunks = chunk_por_parrafos(texto, max_chars=3000, overlap_chars=400)
    print(f"Chunking multi-pasada: {len(chunks)} chunks")
    for i, ch in enumerate(chunks):
        print(f"  Chunk {i+1}: {ch['chars']} chars, {ch['parrafos']} parrafos")
    fallo = chunk_priorizar_fallo(texto)
    if fallo:
        print(f"Priorizar fallo: {fallo[0]['parrafos']} parrafos, incluye RESUELVE={fallo[0]['incluye_resuelve']}")
