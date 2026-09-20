#!/usr/bin/env python3
"""
Assemble the final benchmark from:

- the preserved non-Cppcheck branch after filtering and deduplication
- the preserved Cppcheck branch `cppcheck_unique_379`

This script documents the assembly contract without overwriting the preserved
benchmark artifact.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_benchmark(non_cppcheck_path: Path, cppcheck_path: Path) -> list[dict]:
    non_cppcheck = load_json(non_cppcheck_path)
    cppcheck = load_json(cppcheck_path)
    return non_cppcheck + cppcheck


if __name__ == "__main__":
    raise SystemExit(
        "This curated script documents benchmark assembly and should not overwrite preserved artifacts by default."
    )
