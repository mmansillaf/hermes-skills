#!/usr/bin/env python3
"""Analyze Groq Batch output JSONL — quality metrics, errors, distribution.

Usage:
    python3 analyze_batch_results.py batch_lote1_output.jsonl --errors batch_lote1_errors.jsonl

Prints: doc counts by materia, JSON validity, finish_reason stats, char/token distribution, error analysis.
"""
import json, sys, argparse
from collections import Counter

def analyze_output(path):
    materias = Counter()
    total = valid_json = stop_reason = length_reason = 0
    min_len, max_len = 999999, 0
    total_len = total_prompt = total_completion = 0

    with open(path) as f:
        for line in f:
            d = json.loads(line)
            cid = d.get('custom_id', '')
            if cid and '_' in cid:
                materias[cid.rsplit('_', 1)[0]] += 1
            elif cid:
                materias[cid] += 1

            body = d['response']['body']
            choice = body['choices'][0]
            msg = choice['message']['content']
            reason = choice.get('finish_reason', '')
            usage = body.get('usage', {})

            total += 1
            total_len += len(msg)
            min_len = min(min_len, len(msg))
            max_len = max(max_len, len(msg))
            total_prompt += usage.get('prompt_tokens', 0)
            total_completion += usage.get('completion_tokens', 0)

            if reason == 'stop':
                stop_reason += 1
            elif reason == 'length':
                length_reason += 1

            try:
                json.loads(msg)
                valid_json += 1
            except json.JSONDecodeError:
                pass

    print('=' * 60)
    print('  BATCH ANALYSIS: %s' % path)
    print('=' * 60)
    print()
    print('  Total registros:    %d' % total)
    print('  JSON valido:        %d (%.1f%%)' % (valid_json, valid_json/total*100))
    print('  finish_reason=stop: %d (%.1f%%)' % (stop_reason, stop_reason/total*100))
    print('  finish_reason=len:  %d (%.1f%%)' % (length_reason, length_reason/total*100))
    print()
    print('  Contenido (chars):  min=%d | max=%d | avg=%.0f' % (min_len, max_len, total_len/total))
    print('  Tokens prompt:      %d' % total_prompt)
    print('  Tokens completion:  %d' % total_completion)
    print('  Tokens total:       %d' % (total_prompt + total_completion))
    if total:
        print('  Tokens/doc (prompt): %.0f | (completion): %.0f' % (total_prompt/total, total_completion/total))
    print()

    if len(materias) > 1:
        print('  Distribucion por materia:')
        for m, cnt in materias.most_common():
            print('    %-20s %6d (%5.1f%%)' % (m, cnt, cnt/total*100))
        print()


def analyze_errors(path):
    if not path:
        return
    codes = Counter()
    print('=' * 60)
    print('  ERROR ANALYSIS: %s' % path)
    print('=' * 60)
    print()
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            codes[d.get('error', {}).get('code', 'unknown')] += 1

    for code, cnt in codes.most_common():
        print('  %-25s %d' % (code, cnt))
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyze Groq Batch results')
    parser.add_argument('output_jsonl', help='Path to batch output JSONL')
    parser.add_argument('--errors', help='Path to batch errors JSONL (optional)')
    args = parser.parse_args()
    analyze_output(args.output_jsonl)
    if args.errors:
        analyze_errors(args.errors)
