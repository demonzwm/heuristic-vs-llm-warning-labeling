#!/usr/bin/env python3
"""
Normalize raw CodeQL, CSA, and Cppcheck reports into a unified warning schema.

This script is a curated three-tool consolidation of the audited historical
normalization logic.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from bs4 import BeautifulSoup


def resolve_project_name_with_version(
    repository_root: Path, project_name: str, project_version: str
) -> str:
    candidates = [
        f"{project_name}-{project_version}",
        f"{project_name}-{project_version.replace('.', '_')}",
    ]
    for name in candidates:
        if (repository_root / name).is_dir():
            return name

    prefix = f"{project_name}-"
    for entry in repository_root.iterdir():
        if entry.is_dir() and entry.name.lower().startswith(prefix):
            if entry.name.endswith(f"-{project_version}") or entry.name.endswith(
                f"-{project_version.replace('.', '_')}"
            ):
                return entry.name
    return f"{project_name}-{project_version}"


def parse_project_version_from_name(name: str, tool: str) -> tuple[str, str]:
    stem = name
    for suffix in (f"_{tool}.sarif", ".sarif", ".xml", ".json"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    match = re.match(r"^(.+?)-n?(\d[\d._-]*)$", stem, re.IGNORECASE)
    if not match:
        raise ValueError(f"cannot parse project/version from {name!r}")
    return match.group(1).lower(), match.group(2)


def normalize_file_path(raw_path: str, project_name: str) -> str:
    parts = Path(raw_path).parts
    for i, part in enumerate(parts):
        if part.lower().startswith(project_name.lower() + "-") and any(
            ch.isdigit() for ch in part
        ):
            return str(Path(*parts[i + 1 :])) if i + 1 < len(parts) else raw_path
    return raw_path


def extract_codeql(
    sarif_path: Path, repository_root: Path, project_name: str, project_version: str
) -> list[dict]:
    with sarif_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    project_name_with_version = resolve_project_name_with_version(
        repository_root, project_name, project_version
    )
    run = data["runs"][0]
    rules = {rule["id"]: rule for rule in run["tool"]["driver"].get("rules", [])}
    warnings: list[dict] = []

    for result in run.get("results", []):
        rule_id = result.get("ruleId", "")
        rule = rules.get(rule_id, {})
        tags = rule.get("properties", {}).get("tags", [])
        cwe_list = []
        for tag in tags:
            match = re.match(r"external/cwe/cwe-(\d+)", tag, re.IGNORECASE)
            if match:
                cwe_list.append(f"CWE-{match.group(1)}")

        severity = rule.get("defaultConfiguration", {}).get("level", "note").upper()
        locations = result.get("locations", [])
        if not locations:
            continue
        physical = locations[0].get("physicalLocation", {})
        file_path = physical.get("artifactLocation", {}).get("uri", "")
        line_number = physical.get("region", {}).get("startLine", 0)
        warnings.append(
            {
                "tool_name": "codeql",
                "project_name": project_name,
                "project_name_with_version": project_name_with_version,
                "project_version": project_version,
                "file_path": file_path,
                "line_number": line_number,
                "cwe": cwe_list,
                "rule_id": rule_id,
                "message": result.get("message", {}).get("text", ""),
                "severity": severity,
            }
        )

    return warnings


def extract_cppcheck(
    xml_path: Path, repository_root: Path, project_name: str, project_version: str
) -> list[dict]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    errors = root.find("errors")
    if errors is None:
        return []

    project_name_with_version = resolve_project_name_with_version(
        repository_root, project_name, project_version
    )
    warnings: list[dict] = []
    for error in errors:
        location = error.find("location")
        if location is None:
            continue
        cwe_raw = error.get("cwe", "")
        warnings.append(
            {
                "tool_name": "cppcheck",
                "project_name": project_name,
                "project_name_with_version": project_name_with_version,
                "project_version": project_version,
                "file_path": normalize_file_path(location.get("file", ""), project_name),
                "line_number": int(location.get("line", 0)),
                "cwe": [f"CWE-{cwe_raw}"] if cwe_raw else [],
                "rule_id": error.get("id", ""),
                "message": error.get("msg", ""),
                "severity": error.get("severity", "").upper(),
            }
        )
    return warnings


def extract_csa(
    index_html: Path, repository_root: Path, project_name: str, project_version: str
) -> list[dict]:
    with index_html.open(encoding="utf-8") as handle:
        soup = BeautifulSoup(handle, "lxml")

    project_name_with_version = resolve_project_name_with_version(
        repository_root, project_name, project_version
    )
    warnings: list[dict] = []
    for row in soup.find_all("tr", class_=re.compile(r"^bt_")):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue
        bug_group = cells[0].get_text(strip=True)
        bug_type = cells[1].get_text(strip=True)
        file_name = cells[2].get_text(strip=True)
        line_text = cells[4].get_text(strip=True)
        try:
            line_number = int(line_text)
        except ValueError:
            line_number = 0
        warnings.append(
            {
                "tool_name": "csa",
                "project_name": project_name,
                "project_name_with_version": project_name_with_version,
                "project_version": project_version,
                "file_path": file_name,
                "line_number": line_number,
                "cwe": [],
                "rule_id": bug_type,
                "message": f"{bug_group}: {bug_type}",
                "severity": "WARNING",
            }
        )
    return warnings


def extract_all(input_root: Path, repository_root: Path) -> list[dict]:
    all_warnings: list[dict] = []

    for sarif_file in sorted((input_root / "codeql").glob("*/*.sarif")):
        project, version = parse_project_version_from_name(sarif_file.name, "codeql")
        all_warnings.extend(
            extract_codeql(sarif_file, repository_root, project, version)
        )

    for xml_file in sorted((input_root / "cppcheck").glob("*/*.xml")):
        project, version = parse_project_version_from_name(xml_file.name, "cppcheck")
        all_warnings.extend(
            extract_cppcheck(xml_file, repository_root, project, version)
        )

    for version_dir in sorted((input_root / "csa").glob("*/*")):
        index_html = version_dir / "index.html"
        if not index_html.exists():
            continue
        project, version = parse_project_version_from_name(version_dir.name, "csa")
        all_warnings.extend(extract_csa(index_html, repository_root, project, version))

    return all_warnings


if __name__ == "__main__":
    raise SystemExit(
        "This curated script is intended for controlled reruns with restored raw inputs."
    )
