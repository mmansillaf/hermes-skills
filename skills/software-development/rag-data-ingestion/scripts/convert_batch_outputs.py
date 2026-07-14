#!/usr/bin/env python3
"""
Convert Groq Batch output JSONL → rag_listo_batch_*.json for the indexer.

Takes one or more Groq batch output files, extracts the structured JSON
from each response, and writes a single rag_listo-format JSON file to data_raw/.

Usage:
    python3 scripts/convert_batch_outputs.py \\
        batch_results/lote1_output.jsonl batch_results/lote2_output.jsonl \\
        --output data_raw/rag_listo_batch_groq_N.json

Field mapping:
    Groq output JSON                         rag_listo field
    ─────────────────────────────────────────────────────────────
    resumen_hechos                           contenido_a_vectorizar.hechos
    resumen_problema                         contenido_a_vectorizar.problema
    resumen_fallo                            contenido_a_vectorizar.fallo
    entidades_clave.jueces_magistrados       metadatos_graphrag.jueces_magistrados
    entidades_clave.demandantes_accionantes  metadatos_graphrag.demandantes_accionantes
    entidades_clave.demandados_accionados    metadatos_graphrag.demandados_accionados
    entidades_clave.leyes_y_articulos_citados  metadatos_graphrag.leyes_y_articulos_citados
    custom_id (hashed via MD5)               id_documento

Deduplication: Automatically skips any id_documento already present in
existing data_raw/rag_listo_batch_*.json files.
"""
import json, hashlib, os, sys, argparse, glob
from collections import Counter


def custom_id_to_doc_id(custom_id):
    """Deterministic doc ID from custom_id."""
    return hashlib.md5(custom_id.encode()).hexdigest()[:32]


def load_existing_ids(data_raw_dir):
    """Load doc IDs already indexed from existing rag_listo files."""
    ids = set()
    for f in sorted(glob.glob(os.path.join(data_raw_dir, "rag_listo_batch_*.json"))):
        with open(f) as fh:
            for doc in json.load(fh):
                did = doc.get("id_documento", "")
                if did:
                    ids.add(did)
    return ids


def extract_doc(item):
    """Extract a single document from a Groq batch output line."""
    body = item.get("response", {}).get("body", {})
    choice = body.get("choices", [{}])[0]
    raw = choice.get("message", {}).get("content", "")
    if not raw:
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    hechos = parsed.get("resumen_hechos", "") or ""
    problema = parsed.get("resumen_problema", "") or ""
    fallo = parsed.get("resumen_fallo", "") or ""
    entidades = parsed.get("entidades_clave", {})

    if not isinstance(entidades, dict):
        entidades = {}

    def ensure_list(v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [v]
        return []

    doc = {
        "id_documento": custom_id_to_doc_id(item.get("custom_id", "")),
        "ruta_local": f"batch_groq/{item.get('custom_id', 'unknown')}",
        "contenido_a_vectorizar": {
            "hechos": hechos,
            "problema": problema,
            "fallo": fallo
        },
        "metadatos_graphrag": {
            "jueces_magistrados": ensure_list(entidades.get("jueces_magistrados", [])),
            "demandantes_accionantes": ensure_list(entidades.get("demandantes_accionantes", [])),
            "demandados_accionados": ensure_list(entidades.get("demandados_accionados", [])),
            "leyes_y_articulos_citados": ensure_list(entidades.get("leyes_y_articulos_citados", [])),
        }
    }
    return doc


def process(input_paths, output_path, data_raw_dir, stats):
    """Process one or more Groq batch output files into a rag_listo JSON."""
    existing_ids = load_existing_ids(data_raw_dir)
    docs = []
    total_lines = 0
    skipped_dup = 0
    skipped_empty = 0
    parse_errors = 0

    for path in input_paths:
        if not os.path.exists(path):
            print(f"  [SKIP] {path} not found")
            continue

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total_lines += 1
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    parse_errors += 1
                    continue

                doc = extract_doc(item)
                if doc is None:
                    skipped_empty += 1
                    continue

                if doc["id_documento"] in existing_ids:
                    skipped_dup += 1
                    continue

                docs.append(doc)
                existing_ids.add(doc["id_documento"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    stats["total_lines"] = total_lines
    stats["parsed"] = len(docs)
    stats["skipped_dup"] = skipped_dup
    stats["skipped_empty"] = skipped_empty
    stats["parse_errors"] = parse_errors
    stats["output"] = output_path
    stats["total_in_raw"] = len(existing_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Groq Batch output JSONL to rag_listo format"
    )
    parser.add_argument("inputs", nargs="+", help="Groq batch output JSONL file(s)")
    parser.add_argument("--output", required=True, help="Output rag_listo JSON path")
    parser.add_argument(
        "--data-raw", default="data_raw",
        help="Directory with existing rag_listo_*.json files (for dedup)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.data_raw):
        os.makedirs(args.data_raw, exist_ok=True)

    stats = {}
    process(args.inputs, args.output, args.data_raw, stats)

    print(f"  Input files: {len(args.inputs)}")
    print(f"  Total lines read: {stats.get('total_lines', 0)}")
    print(f"  Docs extracted: {stats.get('parsed', 0)}")
    print(f"  Skipped (dup): {stats.get('skipped_dup', 0)}")
    print(f"  Skipped (empty): {stats.get('skipped_empty', 0)}")
    print(f"  Parse errors: {stats.get('parse_errors', 0)}")
    print(f"  Output: {stats.get('output', '?')}")
    print(f"  Total in data_raw/ after: {stats.get('total_in_raw', 0)}")
