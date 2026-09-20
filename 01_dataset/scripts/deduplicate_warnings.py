#!/usr/bin/env python3
"""
Deduplicate warnings using the preserved historical key:

- tool_name
- project_name without version
- rule_id
- file_path
- target source line content
"""

from __future__ import annotations

import re
from pathlib import Path


def project_name_without_version(name: str) -> str:
    return re.sub(r"-[\d][^-]*$", "", name)


def read_line(repository_root: Path, entry: dict) -> str | None:
    source_file = repository_root / entry["project_name_with_version"] / entry["file_path"]
    if not source_file.exists():
        return None
    try:
        with source_file.open("r", encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle, start=1):
                if index == entry["line_number"]:
                    return line.rstrip("\n")
    except OSError:
        return None
    return None


def deduplicate(data: list[dict], repository_root: Path, id_field: str = "id") -> list[dict]:
    seen: dict[tuple, dict] = {}
    for entry in data:
        key = (
            entry.get("tool_name", ""),
            project_name_without_version(entry.get("project_name_with_version", "")),
            entry.get("rule_id", ""),
            entry.get("file_path", ""),
            read_line(repository_root, entry),
        )
        previous = seen.get(key)
        if previous is None or entry.get(id_field, float("inf")) < previous.get(id_field, float("inf")):
            seen[key] = entry
    return sorted(seen.values(), key=lambda item: item.get(id_field, 0))


if __name__ == "__main__":
    raise SystemExit("Import and call deduplicate from a controlled pipeline.")
