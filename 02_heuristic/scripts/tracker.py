"""Reproduce the released cross-version heuristic without using ground truth.

The complete warning pools and project source checkouts are external inputs.
Pass them explicitly; the 1,027-warning benchmark is kept in this repository.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from packaging.version import parse as version
from match import Matcher, normpath

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / '01_dataset/processed/benchmark/benchmark_warnings_1027.json'
DEFAULT_OUTPUT = ROOT / '02_heuristic/results'
CWE_TOP25 = {'CWE-' + x for x in
             '79 89 352 862 787 22 416 125 78 94 120 434 476 121 502 122 863 20 284 200 306 918 77 639 770'.split()}
STRATEGY_NAMES = {'Exact': 'Exact match', 'Location': 'Location-based match',
                  'Snippet': 'Snippet-based match', 'Hash': 'Token-hash match'}

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, rows):
    Path(path).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def filter_cppcheck(rows):
    return [x for x in rows
            if any(c in CWE_TOP25 for c in (x['cwe'] if isinstance(x.get('cwe'), list) else [x.get('cwe')]))
            and not str(x.get('file_path', '')).startswith('test/')]

def source_directories(pool, source_root):
    names = defaultdict(set)
    for row in pool:
        names[row['project_name'], row['project_version']].add(row['project_name_with_version'])
    dirs = {}
    for (project, ver), input_names in names.items():
        canonical = ('openssl-openssl-' if project == 'openssl' else project + '-') + ver
        candidates = [source_root / canonical, source_root / canonical.replace('.', '_')]
        found = list(dict.fromkeys(x.resolve() for x in candidates if x.is_dir()))
        if len(found) != 1:
            raise ValueError(f'non-unique/missing source directory: {project} {ver} {sorted(input_names)} {found}')
        dirs[project, ver] = found[0]
    return dirs

def preflight(benchmark, groups, dirs):
    ids = [x.get('warning_id') for x in benchmark]
    if len(ids) != len(set(ids)) or len(ids) != 1027:
        raise ValueError('benchmark warning IDs are not exactly 1,027 unique IDs')
    needed = {}
    coverage = []
    for row in benchmark:
        for key in ('tool_name', 'project_name', 'project_version', 'rule_id', 'file_path', 'line_number'):
            if not row.get(key): raise ValueError(f'missing benchmark {key}: {row.get("warning_id")}')
        versions = sorted((v for t, p, rule, v in groups
                           if (t, p, rule) == (row['tool_name'], row['project_name'], row['rule_id'])
                           and version(v) > version(row['project_version'])), key=version)
        coverage.append({'warning_id': row['warning_id'], 'later_versions': versions})
        for candidate in [row] + [child for ver in versions
                                  for _, child in groups[row['tool_name'], row['project_name'], row['rule_id'], ver]]:
            key = candidate['project_name'], candidate['project_version'], normpath(candidate['file_path'])
            needed[key] = candidate
    errors = []
    for (project, ver, relative), row in needed.items():
        path = dirs[project, ver] / relative
        try:
            lines = path.read_text(encoding='utf-8', errors='ignore').split('\n')
            if not 1 <= int(row['line_number']) <= len(lines):
                errors.append({'path': str(path), 'line': row['line_number'], 'available_lines': len(lines)})
        except Exception as exc:
            errors.append({'path': str(path), 'error': str(exc)})
    if errors:
        raise ValueError(f'source preflight failed ({len(errors)}): {errors[:20]}')
    return coverage, len(needed)

def label(source_pool, cppcheck_pool, source_root, output_dir, expect_predictions=None):
    benchmark = read(BENCHMARK)
    source = read(source_pool)
    cpp = filter_cppcheck(read(cppcheck_pool))
    pool = source + cpp
    groups = defaultdict(list)
    for index, row in enumerate(pool):
        for key in ('tool_name', 'project_name', 'project_version', 'rule_id', 'file_path', 'line_number'):
            if not row.get(key): raise ValueError(f'missing pool {key} at index {index}')
        groups[row['tool_name'], row['project_name'], row['rule_id'], row['project_version']].append((index, row))
    dirs = source_directories(pool, source_root)
    coverage, needed_count = preflight(benchmark, groups, dirs)
    matcher = Matcher(dirs, threshold=3, context=2, similarity=.8, hash_size=30)
    results = []
    audit = {'benchmark_count': len(benchmark), 'source_pool_count': len(source),
             'cppcheck_filtered_count': len(cpp), 'needed_source_files': needed_count,
             'later_version_coverage': coverage, 'strategy_counts': {}, 'source_read_errors': 0}
    for row, cov in zip(benchmark, coverage):
        found = None
        for ver in cov['later_versions']:
            found = matcher.match_version(row, groups[row['tool_name'], row['project_name'], row['rule_id'], ver])
            if found: break
        child = found[2] if found else None
        identity = ({k: child.get(k) for k in
                     ('tool_name', 'project_name', 'project_version', 'file_path', 'line_number', 'rule_id', 'cwe')}
                    if child else None)
        if identity is not None: identity['candidate_input_index'] = found[1]
        decision = {'label': 'FP' if found else 'TP', 'matched': bool(found),
                    'match_type': STRATEGY_NAMES[found[0]] if found else None,
                    'matched_version': child['project_version'] if child else None,
                    'matched_child_warning': identity,
                    'match_evidence': found[3] if found else None,
                    'location_threshold': 3}
        results.append({'warning_info': row, 'heuristic_based_labeling': decision})
    if expect_predictions:
        expected = read(expect_predictions)
        if len(expected) != len(results): raise ValueError('expected prediction count differs')
        for actual, source_row in zip(results, expected):
            d = actual['heuristic_based_labeling']
            if (actual['warning_info']['warning_id'] != source_row['warning_id']
                or d['label'] != source_row['heuristic_label']
                or d['matched'] != source_row['matched']
                or d['match_type'] != (STRATEGY_NAMES[source_row['match_type']] if source_row['match_type'] else None)
                or d['matched_version'] != source_row['matched_version']
                or (d['matched_child_warning'] or {}).get('candidate_input_index') != source_row['matched_child_index']
                or d['match_evidence'] != source_row['match_evidence']):
                raise ValueError(f'prediction differs from selected source: {source_row["warning_id"]}')
    output_dir.mkdir(parents=True, exist_ok=True)
    out_json = output_dir / 'heuristic_labels_1027.json'
    write(out_json, results)
    with (output_dir / 'heuristic_labels_1027.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['warning_id', 'heuristic_label', 'matched', 'match_type',
                                                     'matched_version', 'matched_child_warning', 'match_evidence'])
        writer.writeheader()
        for item in results:
            d = item['heuristic_based_labeling']
            writer.writerow({'warning_id': item['warning_info']['warning_id'], 'heuristic_label': d['label'],
                             'matched': d['matched'], 'match_type': d['match_type'],
                             'matched_version': d['matched_version'],
                             'matched_child_warning': json.dumps(d['matched_child_warning'], ensure_ascii=False),
                             'match_evidence': json.dumps(d['match_evidence'], ensure_ascii=False)})
    audit['strategy_counts'] = dict(Counter(item['heuristic_based_labeling']['match_type'] for item in results
                                            if item['heuristic_based_labeling']['matched']))
    audit['prediction_counts'] = dict(Counter(item['heuristic_based_labeling']['label'] for item in results))
    audit['prediction_sha256'] = sha(out_json)
    audit['input_sha256'] = {'benchmark': sha(BENCHMARK), 'source_pool': sha(source_pool),
                             'cppcheck_pool': sha(cppcheck_pool)}
    write(output_dir / 'matching_audit.json', audit)
    return results

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pool', type=Path, required=True)
    parser.add_argument('--cppcheck-pool', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--expect-predictions', type=Path)
    args = parser.parse_args()
    rows = label(args.source_pool, args.cppcheck_pool, args.source_root,
                 args.output_dir, args.expect_predictions)
    print(f'validated {len(rows)} warnings and wrote {args.output_dir}')

if __name__ == '__main__': main()
