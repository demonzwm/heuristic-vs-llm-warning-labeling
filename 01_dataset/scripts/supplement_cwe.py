#!/usr/bin/env python3
"""
Supplement missing CWE fields for CodeQL, CSA, and Cppcheck warnings.

This is the three-tool formalized version of the historical CWE supplementation
logic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def int_to_cwe(value: int | str) -> str:
    return f"CWE-{int(value)}"


def build_codeql_mapping(path: Path) -> dict[str, list[str]]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict[str, list[str]] = {}
    for entry in entries:
        rule_id = entry.get("ruleId")
        if not rule_id:
            continue
        cwes = [
            f"CWE-{match}"
            for match in re.findall(
                r"external/cwe/cwe-(\d+)",
                entry.get("rule.properties.tags") or "",
                re.IGNORECASE,
            )
        ]
        if not cwes and entry.get("cwe") is not None:
            cwes = [int_to_cwe(entry["cwe"])]
        if cwes:
            mapping[rule_id] = cwes
    return mapping


def build_cppcheck_mapping(path: Path) -> dict[str, list[str]]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict[str, list[str]] = {}
    for entry in entries:
        rule_id = entry.get("id")
        cwe = entry.get("cwe")
        if rule_id and cwe is not None:
            mapping[rule_id] = [int_to_cwe(cwe)]
    semantic_assignments = {
        "returnImplicitInt": "CWE-758",
    }
    for rule_id, cwe in semantic_assignments.items():
        mapping[rule_id] = [cwe]
    return mapping


def build_csa_mapping(path: Path) -> dict[str, list[str]]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    mapping: dict[str, list[str]] = {}
    for entry in entries:
        bug_type = entry.get("Bug Type")
        cwe_id = entry.get("CWE-ID")
        if bug_type and cwe_id is not None:
            mapping[bug_type] = [int_to_cwe(cwe_id)]
    return mapping


if __name__ == "__main__":
    raise SystemExit(
        "This curated script is intended for controlled reruns with restored CWE reference inputs."
    )
