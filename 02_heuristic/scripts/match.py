from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from hashlib import md5
from json import JSONDecoder
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from packaging.version import parse as parse_version


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "01_dataset" / "processed"
SOURCE_POOL_PATH = DATA_DIR / "normalized" / "warnings_normalized_all_55298.json"
SOURCE_FUNCTION_POOL_PATH = Path(
    os.environ.get("HEURISTIC_SOURCE_FUNCTION_POOL_PATH", ROOT_DIR.parent / "data_with_fcg_and_bfs_55298.json")
)
CPPCHECK_POOL_PATH = Path(
    os.environ.get("HEURISTIC_CPPCHECK_POOL_PATH", ROOT_DIR.parent / "cppcheeck" / "cppcheck_warnings_all.json")
)

CWE_TOP25 = {
    "CWE-79", "CWE-89", "CWE-352", "CWE-862", "CWE-787",
    "CWE-22", "CWE-416", "CWE-125", "CWE-78", "CWE-94",
    "CWE-120", "CWE-434", "CWE-476", "CWE-121", "CWE-502",
    "CWE-122", "CWE-863", "CWE-20", "CWE-284", "CWE-200",
    "CWE-306", "CWE-918", "CWE-77", "CWE-639", "CWE-770",
}


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_cwe_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def normalize_cwe_text(value: object) -> str:
    return "; ".join(normalize_cwe_list(value))


def is_cppcheck_warning(row: dict) -> bool:
    return str(row.get("tool_name")) == "cppcheck"


def filter_cppcheck_pool(rows: list[dict]) -> list[dict]:
    filtered: list[dict] = []
    for row in rows:
        cwes = normalize_cwe_list(row.get("cwe"))
        if not any(cwe in CWE_TOP25 for cwe in cwes):
            continue
        if str(row.get("file_path", "")).startswith("test/"):
            continue
        filtered.append(row)
    return filtered


def group_by_project_version(rows: list[dict]) -> dict[str, dict[str, list[dict]]]:
    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row["project_name"])][str(row["project_version"])].append(row)
    ordered: dict[str, dict[str, list[dict]]] = {}
    for project, versions in grouped.items():
        ordered_versions = sorted(versions.keys(), key=parse_version)
        ordered[project] = {version: versions[version] for version in ordered_versions}
    return ordered


def iter_json_array(path: Path) -> Iterator[dict]:
    decoder = JSONDecoder()
    with path.open("r", encoding="utf-8") as handle:
        buffer = ""
        started = False
        eof = False
        while True:
            if not eof:
                chunk = handle.read(1024 * 1024)
                if chunk:
                    buffer += chunk
                else:
                    eof = True
            idx = 0
            while True:
                while idx < len(buffer) and buffer[idx].isspace():
                    idx += 1
                if not started:
                    if idx < len(buffer) and buffer[idx] == "[":
                        started = True
                        idx += 1
                    else:
                        break
                while idx < len(buffer) and buffer[idx].isspace():
                    idx += 1
                if idx >= len(buffer):
                    break
                if buffer[idx] == ",":
                    idx += 1
                    continue
                if buffer[idx] == "]":
                    return
                try:
                    obj, next_idx = decoder.raw_decode(buffer, idx)
                except json.JSONDecodeError:
                    break
                yield obj
                idx = next_idx
            buffer = buffer[idx:]
            if eof and not buffer.strip():
                break


def build_source_function_map(path: Path) -> dict[tuple, str]:
    function_map: dict[tuple, str] = {}
    for obj in iter_json_array(path):
        try:
            project = obj["project"]
            file_path = obj["defect_file"]
            line_number = obj["defect_line"]
            function_name = (
                obj.get("slice_result", {})
                .get("fcg", {})
                .get("target_function", {})
                .get("function_name")
            )
        except Exception:
            continue
        if function_name:
            function_map[(project, file_path, line_number)] = str(function_name)
    return function_map


class Matcher:
    def __init__(
        self,
        *,
        matching_threshold: int = 3,
        context_lines: int = 2,
        snippet_similarity: float = 0.8,
        hash_size: int = 30,
    ) -> None:
        self.matching_threshold = matching_threshold
        self.context_lines = context_lines
        self.snippet_similarity = snippet_similarity
        self.hash_size = hash_size
        self._repo_dir_cache: Dict[str, Optional[Path]] = {}
        self._file_cache: Dict[Tuple[str, str], Optional[str]] = {}

    def resolve_project_dir(self, project_name_with_version: str) -> Optional[Path]:
        if project_name_with_version in self._repo_dir_cache:
            return self._repo_dir_cache[project_name_with_version]

        repo_base = ROOT_DIR.parent / "repository" / "repository"
        normalized = project_name_with_version.replace(".", "_")
        candidates = [
            repo_base / project_name_with_version,
            repo_base / normalized,
        ]
        for candidate in candidates:
            if candidate.exists():
                self._repo_dir_cache[project_name_with_version] = candidate
                return candidate

        for repo_dir in repo_base.iterdir():
            if not repo_dir.is_dir():
                continue
            name = repo_dir.name
            if name == project_name_with_version or name == normalized:
                self._repo_dir_cache[project_name_with_version] = repo_dir
                return repo_dir
            if name.endswith(project_name_with_version) or name.endswith(normalized):
                self._repo_dir_cache[project_name_with_version] = repo_dir
                return repo_dir

        self._repo_dir_cache[project_name_with_version] = None
        return None

    def get_file_content(self, warning: dict) -> Optional[str]:
        cache_key = (str(warning["project_name_with_version"]), str(warning["file_path"]))
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        project_dir = self.resolve_project_dir(str(warning["project_name_with_version"]))
        if not project_dir:
            self._file_cache[cache_key] = None
            return None

        file_path = project_dir / str(warning["file_path"])
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = None
        self._file_cache[cache_key] = content
        return content

    def is_similar_file(self, path1: str, path2: str) -> bool:
        file1 = os.path.basename(path1)
        file2 = os.path.basename(path2)
        if file1 == file2:
            return True
        norm1 = path1.replace("\\", "/").lower()
        norm2 = path2.replace("\\", "/").lower()
        if norm1 == norm2:
            return True
        if norm1.endswith(norm2) or norm2.endswith(norm1):
            return True
        return False

    def exact_matching(self, parent: dict, child: dict) -> bool:
        if not self.is_similar_file(str(parent["file_path"]), str(child["file_path"])):
            return False
        return int(parent.get("line_number", 0)) == int(child.get("line_number", 0))

    def _get_diff_matches(self, old_lines: List[str], new_lines: List[str]) -> List[Tuple[int, int]]:
        import difflib

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        matches = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for offset in range(i2 - i1):
                    matches.append((i1 + offset + 1, j1 + offset + 1))
        return matches

    def _find_closest_match(self, line_number: int, matches: List[Tuple[int, int]], version: str) -> Optional[int]:
        if not matches:
            return None
        best_distance = float("inf")
        best_line = None
        for old_line, new_line in matches:
            current = old_line if version == "old" else new_line
            distance = abs(current - line_number)
            if distance < best_distance:
                best_distance = distance
                best_line = current
        return best_line

    def location_based_matching(self, parent: dict, child: dict, parent_content: str, child_content: str) -> bool:
        if not self.is_similar_file(str(parent["file_path"]), str(child["file_path"])):
            return False
        if not parent_content or not child_content:
            return False
        parent_line = int(parent.get("line_number", 0))
        child_line = int(child.get("line_number", 0))
        matches = self._get_diff_matches(parent_content.split("\n"), child_content.split("\n"))
        if not matches:
            return False
        parent_closest = self._find_closest_match(parent_line, matches, "old")
        child_closest = self._find_closest_match(child_line, matches, "new")
        if not parent_closest or not child_closest:
            return False
        parent_offset = parent_line - parent_closest
        child_offset = child_line - child_closest
        return abs(parent_offset - child_offset) <= self.matching_threshold

    def get_code_snippet(self, content: str, line_number: int) -> Optional[str]:
        if not content:
            return None
        lines = content.split("\n")
        if line_number < 1 or line_number > len(lines):
            return None
        start_line = max(1, line_number - self.context_lines)
        end_line = min(len(lines), line_number + self.context_lines)
        snippet_lines = lines[start_line - 1 : end_line]
        min_indent = float("inf")
        for line in snippet_lines:
            if line.strip():
                min_indent = min(min_indent, len(line) - len(line.lstrip()))
        normalized = []
        for line in snippet_lines:
            if line.strip() and min_indent != float("inf") and len(line) >= min_indent:
                normalized.append(line[min_indent:])
            else:
                normalized.append(line)
        return "\n".join(normalized)

    def normalize_code(self, code: str) -> str:
        code = re.sub(r"#.*$", "", code or "", flags=re.MULTILINE)
        return "\n".join(line.strip() for line in code.split("\n") if line.strip())

    def calculate_similarity(self, snippet1: str, snippet2: str) -> float:
        import difflib

        norm1 = self.normalize_code(snippet1)
        norm2 = self.normalize_code(snippet2)
        if not norm1 or not norm2:
            return 0.0
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()

    def snippet_based_matching(self, parent: dict, child: dict, parent_content: str, child_content: str) -> bool:
        parent_snippet = self.get_code_snippet(parent_content, int(parent.get("line_number", 0)))
        child_snippet = self.get_code_snippet(child_content, int(child.get("line_number", 0)))
        if not parent_snippet or not child_snippet:
            return False
        return self.calculate_similarity(parent_snippet, child_snippet) >= self.snippet_similarity

    def get_code_line(self, content: str, line_number: int) -> Optional[str]:
        if not content:
            return None
        lines = content.split("\n")
        if line_number < 1 or line_number > len(lines):
            return None
        return lines[line_number - 1]

    def _split_into_tokens(self, text: str) -> List[str]:
        return re.findall(r"\w+", text or "")

    def _hash_first_tokens(self, text: str) -> str:
        tokens = self._split_into_tokens(text)
        return md5(" ".join(tokens[: self.hash_size]).encode()).hexdigest() if tokens else ""

    def _hash_last_tokens(self, text: str) -> str:
        tokens = self._split_into_tokens(text)
        if not tokens:
            return ""
        return md5(" ".join(tokens[-self.hash_size :]).encode()).hexdigest()

    def hash_based_matching(self, parent: dict, child: dict, parent_content: str, child_content: str) -> bool:
        parent_line = self.get_code_line(parent_content, int(parent.get("line_number", 0)))
        child_line = self.get_code_line(child_content, int(child.get("line_number", 0)))
        if not parent_line or not child_line:
            return False
        return (
            self._hash_first_tokens(parent_line) == self._hash_first_tokens(child_line)
            or self._hash_last_tokens(parent_line) == self._hash_last_tokens(child_line)
        )

    def classify_match(self, parent: dict, child: dict) -> Optional[str]:
        if self.exact_matching(parent, child):
            return "Exact match"

        parent_content = self.get_file_content(parent)
        child_content = self.get_file_content(child)

        if parent_content and child_content and self.location_based_matching(parent, child, parent_content, child_content):
            return "Location-based match"
        if parent_content and child_content and self.snippet_based_matching(parent, child, parent_content, child_content):
            return "Snippet-based match"
        if parent_content and child_content and self.hash_based_matching(parent, child, parent_content, child_content):
            return "Token-hash match"
        return None


def build_warning_pools() -> tuple[dict[str, dict[str, list[dict]]], dict[str, dict[str, list[dict]]], dict[tuple, str]]:
    source_pool_rows = load_json(SOURCE_POOL_PATH)
    cppcheck_pool_rows = filter_cppcheck_pool(load_json(CPPCHECK_POOL_PATH))
    source_versions = group_by_project_version(source_pool_rows)
    cppcheck_versions = group_by_project_version(cppcheck_pool_rows)
    function_map = build_source_function_map(SOURCE_FUNCTION_POOL_PATH)
    return source_versions, cppcheck_versions, function_map
