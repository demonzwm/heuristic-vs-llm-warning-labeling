from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
LLM_DIR = SCRIPT_DIR.parents[1]
REPO_ROOT = LLM_DIR.parent

INPUT_PATH = REPO_ROOT / "01_dataset" / "processed" / "benchmark" / "benchmark_warnings_1027.json"
PROMPT_PATH = LLM_DIR / "prompts" / "baseline_binary_prompt.py"
OUTPUT_PATH = LLM_DIR / "gpt" / "results" / "gpt_ouol_1027.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_prompt_template(path: Path) -> str:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load prompt template from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    template = getattr(module, "PROMPT_TEMPLATE", None)
    if not isinstance(template, str):
        raise RuntimeError(f"PROMPT_TEMPLATE not found in {path}")
    return template


def sanitize_warning(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("warning_id", row.get("id")),
        "tool_name": row.get("tool_name"),
        "rule_id": row.get("rule_id"),
        "message": row.get("message"),
        "file_path": row.get("file_path"),
        "line_number": row.get("line_number"),
        "function_name": row.get("function_name"),
        "sliced_code": row.get("sliced_code"),
    }


def build_prompt(row: dict[str, Any]) -> str:
    return load_prompt_template(PROMPT_PATH) + json.dumps(sanitize_warning(row), ensure_ascii=False, indent=2)


def validate_inputs() -> list[str]:
    issues: list[str] = []
    for path in [INPUT_PATH, PROMPT_PATH, OUTPUT_PATH]:
        if not path.exists():
            issues.append(f"Missing required path: {path.relative_to(REPO_ROOT)}")
    if issues:
        return issues
    rows = load_json(INPUT_PATH)
    if not isinstance(rows, list) or len(rows) != 1027:
        issues.append(f"Expected 1027 benchmark rows, found {len(rows) if isinstance(rows, list) else 'non-list'}.")
    forbidden = {"heuristic_label", "ground_truth_label", "ground_truth", "correct"}
    for index, row in enumerate(rows[:1027], start=1):
        present = sorted(forbidden.intersection(row))
        if present:
            issues.append(f"Input row {index} contains non-baseline fields: {', '.join(present)}")
            break
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="GPT binary baseline runner for the final paper artifact.")
    parser.add_argument("--preflight", action="store_true", help="Validate paths and prompt shape without API calls.")
    parser.add_argument("--execute", action="store_true", help="Run model requests. Not used for artifact validation.")
    parser.add_argument("--model", default=os.environ.get("GPT_MODEL", ""))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", ""))
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    args = parser.parse_args()

    issues = validate_inputs()
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        raise SystemExit(1)
    print("PASS: GPT baseline paths and inference input are valid.")
    print("No API calls made.")
    if not args.execute:
        return
    if not args.model:
        raise RuntimeError("Set GPT_MODEL before execution.")
    if not args.base_url:
        raise RuntimeError("Set OPENAI_BASE_URL before execution.")
    if not os.environ.get(args.api_key_env):
        raise RuntimeError(f"Missing API key environment variable: {args.api_key_env}")
    raise NotImplementedError("Prediction execution is intentionally disabled in the release artifact.")


if __name__ == "__main__":
    main()
