#!/usr/bin/env python3
"""
Keep only warnings whose CWE list intersects the curated Top 25 set.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def parse_top25(path: Path) -> set[str]:
    return set(re.findall(r"CWE-\d+", path.read_text(encoding="utf-8")))


def filter_cwe_top25(data: list[dict], top25: set[str]) -> list[dict]:
    return [entry for entry in data if set(entry.get("cwe", [])) & top25]


if __name__ == "__main__":
    raise SystemExit("Import and call filter_cwe_top25 from a controlled pipeline.")
