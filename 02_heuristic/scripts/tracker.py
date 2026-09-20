from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from packaging.version import parse as parse_version

from match import Matcher, build_warning_pools, load_json, normalize_cwe_text, is_cppcheck_warning


ROOT_DIR = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = ROOT_DIR / "01_dataset" / "processed" / "benchmark" / "benchmark_warnings_1027.json"
OUTPUT_JSON_PATH = ROOT_DIR / "02_heuristic" / "results" / "heuristic_labels_1027.json"
OUTPUT_CSV_PATH = ROOT_DIR / "02_heuristic" / "results" / "heuristic_labels_1027.csv"


def matched_child_function(child: Optional[dict], function_map: dict[tuple, str], current_is_cppcheck: bool) -> Optional[str]:
    if not child or current_is_cppcheck:
        return None
    return function_map.get(
        (
            str(child["project_name_with_version"]),
            str(child["file_path"]),
            int(child["line_number"]),
        )
    )


def run_labeling(*, matching_threshold: int = 3) -> list[dict]:
    benchmark_rows = load_json(BENCHMARK_PATH)
    source_versions, cppcheck_versions, function_map = build_warning_pools()
    matcher = Matcher(matching_threshold=matching_threshold)

    results: list[dict] = []
    for row in benchmark_rows:
        project = str(row["project_name"])
        current_version = str(row["project_version"])
        version_pool = cppcheck_versions if is_cppcheck_warning(row) else source_versions
        project_versions = version_pool.get(project, {})
        later_versions = [
            version
            for version in project_versions.keys()
            if parse_version(version) > parse_version(current_version)
        ]

        matched = False
        match_type = None
        matched_version = None
        matched_child = None

        for later_version in later_versions:
            for child in project_versions[later_version]:
                current_match_type = matcher.classify_match(row, child)
                if current_match_type:
                    matched = True
                    match_type = current_match_type
                    matched_version = later_version
                    matched_child = child
                    break
            if matched:
                break

        output_row = dict(row)
        output_row["heuristic_label"] = "FP" if matched else "TP"
        output_row["matched"] = matched
        output_row["match_type"] = match_type
        output_row["matched_version"] = matched_version
        output_row["matched_child_file"] = matched_child.get("file_path") if matched_child else None
        output_row["matched_child_rule"] = matched_child.get("rule_id") if matched_child else None
        output_row["matched_child_cwe"] = normalize_cwe_text(matched_child.get("cwe")) if matched_child else None
        output_row["matched_child_function"] = matched_child_function(
            matched_child,
            function_map,
            is_cppcheck_warning(row),
        )
        output_row["location_threshold"] = matching_threshold
        results.append(output_row)

    return results


def save_results(rows: list[dict]) -> None:
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with OUTPUT_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = run_labeling()
    save_results(rows)
    print(f"saved {OUTPUT_JSON_PATH}")
    print(f"saved {OUTPUT_CSV_PATH}")
    print(f"count={len(rows)}")


if __name__ == "__main__":
    main()
