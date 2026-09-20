#!/usr/bin/env python3
"""
Apply the preserved filtering stages for the final three-tool pipeline:

1. remove irrelevant files such as test/fuzz/benchmark paths
2. remove warnings on #include lines
3. remove latest-version warnings
"""

from __future__ import annotations

import re
from pathlib import Path

from packaging.version import Version


TEST_DIR_SEGMENTS = frozenset(
    ["test", "tests", "fuzz", "fuzzing", "oss-fuzz", "benchmark", "benchmarks", "testdir", "spec"]
)
TEST_EXACT_FILENAMES = frozenset(["conftest.c", "test.c"])
TEST_FILENAME_PATTERNS = re.compile(r"neontest|_fuzzer\.|_fuzz\.|_bench\.", re.IGNORECASE)


def is_irrelevant_file(file_path: str) -> bool:
    parts = Path(file_path).parts
    for segment in parts[:-1]:
        if segment.lower() in TEST_DIR_SEGMENTS:
            return True
    filename = parts[-1].lower() if parts else ""
    if filename in TEST_EXACT_FILENAMES:
        return True
    return bool(TEST_FILENAME_PATTERNS.search(filename))


def filter_irrelevant_files(data: list[dict]) -> list[dict]:
    return [entry for entry in data if not is_irrelevant_file(entry["file_path"])]


def read_source_line(repository_root: Path, entry: dict) -> str | None:
    source_file = repository_root / entry["project_name_with_version"] / entry["file_path"]
    if not source_file.exists():
        return None
    try:
        with source_file.open("r", encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle, start=1):
                if index == entry["line_number"]:
                    return line.strip()
    except OSError:
        return None
    return None


def filter_include_lines(data: list[dict], repository_root: Path) -> list[dict]:
    filtered = []
    for entry in data:
        line = read_source_line(repository_root, entry)
        if line is not None and line.startswith("#include"):
            continue
        filtered.append(entry)
    return filtered


def latest_versions(data: list[dict]) -> dict[str, str]:
    latest: dict[str, str] = {}
    for entry in data:
        project = entry["project_name"]
        version = entry["project_version"]
        if project not in latest or Version(version) > Version(latest[project]):
            latest[project] = version
    return latest


def filter_latest_versions(data: list[dict]) -> list[dict]:
    latest = latest_versions(data)
    return [
        entry
        for entry in data
        if entry["project_version"] != latest.get(entry["project_name"])
    ]


if __name__ == "__main__":
    raise SystemExit("Import and call the filtering helpers from a controlled pipeline.")
