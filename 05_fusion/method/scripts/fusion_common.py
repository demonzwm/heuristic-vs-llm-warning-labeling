from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
METHOD_DIR = SCRIPT_DIR.parent
FUSION_DIR = METHOD_DIR.parent
REPO_ROOT = FUSION_DIR.parent


@dataclass(frozen=True)
class FusionPaths:
    repo_root: Path = REPO_ROOT
    heuristic_labels: Path = REPO_ROOT / "02_heuristic" / "results" / "heuristic_labels_1027.json"
    heuristic_evolution: Path = REPO_ROOT / "02_heuristic" / "results" / "heuristic_evolution_evidence_1027.json"
    deepseek_baseline: Path = REPO_ROOT / "03_llm" / "deepseek" / "results" / "deepseek_v4_flash_semantic_baseline_1027.json"
    gpt_baseline: Path = REPO_ROOT / "03_llm" / "gpt" / "results" / "gpt_ouol_1027.json"
    gpt_stage1_results: Path = FUSION_DIR / "gpt" / "results" / "stage1" / "gpt_stage1_predictions.json"
    inference_input: Path = METHOD_DIR / "data" / "fusion_inference_input_1027.json"
    stage1_results: Path = METHOD_DIR / "stage1" / "stage1_results_1027.json"
    stage1_provenance: Path = METHOD_DIR / "stage1" / "stage1_provenance.json"
    stage1_prompt: Path = METHOD_DIR / "prompts" / "stage1_semantic_analysis_prompt.txt"
    stage2_prompt: Path = METHOD_DIR / "prompts" / "stage2_disagreement_verification_prompt.txt"
    selected_shots: Path = METHOD_DIR / "demonstrations" / "few_shot" / "selected_6shots.json"
    cwe476_schema: Path = METHOD_DIR / "schemas" / "cwe_476_schema.md"
    cwe787_schema: Path = METHOD_DIR / "schemas" / "cwe_787_schema.md"
    generic_schema: Path = METHOD_DIR / "schemas" / "generic_schema.md"
    preflight_report: Path = FUSION_DIR / "analysis" / "preflight_validation.md"


PATHS = FusionPaths()
EVALUATION_FIELD_RE = re.compile(r"(ground[_ -]?truth|manual[_ -]?annotation|expert[_ -]?annotation)", re.I)
HEURISTIC_LABEL_RE = re.compile(r"(heuristic[_ -]?label|heuristic prediction|heuristic predicts)", re.I)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_label(value: Any) -> str:
    label = str(value).strip().upper()
    if label not in {"TP", "FP"}:
        raise ValueError(f"Expected TP/FP label, got {value!r}")
    return label


def primary_cwe(raw: Any) -> str:
    if isinstance(raw, list):
        return str(raw[0]) if raw else "UNAVAILABLE"
    text = str(raw or "UNAVAILABLE")
    return text.split(",")[0].strip() or "UNAVAILABLE"


def schema_for_cwe(raw: Any) -> tuple[str, str]:
    cwe = primary_cwe(raw)
    if cwe == "CWE-476":
        return "CWE-476", PATHS.cwe476_schema.read_text(encoding="utf-8").strip()
    if cwe == "CWE-787":
        return "CWE-787", PATHS.cwe787_schema.read_text(encoding="utf-8").strip()
    return "GENERIC_FALLBACK", PATHS.generic_schema.read_text(encoding="utf-8").strip()


def required_input_paths(model: str | None = None) -> list[Path]:
    paths = [
        PATHS.heuristic_labels,
        PATHS.heuristic_evolution,
        PATHS.inference_input,
        PATHS.stage1_results,
        PATHS.stage1_provenance,
        PATHS.stage1_prompt,
        PATHS.stage2_prompt,
        PATHS.selected_shots,
        PATHS.cwe476_schema,
        PATHS.cwe787_schema,
        PATHS.generic_schema,
    ]
    if model in {None, "deepseek"}:
        paths.append(PATHS.deepseek_baseline)
    if model in {None, "gpt"}:
        paths.append(PATHS.gpt_baseline)
        paths.append(PATHS.gpt_stage1_results)
    return paths


def validate_required_paths(model: str | None = None) -> list[str]:
    missing = [path for path in required_input_paths(model) if not path.exists()]
    if missing:
        return [f"Missing required input: `{path.relative_to(PATHS.repo_root)}`" for path in missing]
    return []


def validate_inference_input() -> list[str]:
    issues: list[str] = []
    data = load_json(PATHS.inference_input)
    if not isinstance(data, list):
        return ["Fusion inference input root is not a list."]
    for index, row in enumerate(data[:1027], start=1):
        keys = set(row)
        leaked = sorted(k for k in keys if EVALUATION_FIELD_RE.search(k))
        if leaked:
            issues.append(f"Record {index} contains evaluation label fields: {', '.join(leaked)}")
        if "heuristic_label_for_routing_only" not in keys:
            issues.append(f"Record {index} is missing heuristic_label_for_routing_only.")
        if "sliced_code" not in keys:
            issues.append(f"Record {index} is missing sliced_code.")
    if len(data) != 1027:
        issues.append(f"Expected 1027 inference records, found {len(data)}.")
    return issues


def build_stage2_prompt(record: dict[str, Any]) -> str:
    schema_name, schema_text = schema_for_cwe(record.get("cwe"))
    stage1 = record.get("stage1", {})
    prompt_template = PATHS.stage2_prompt.read_text(encoding="utf-8").strip()
    payload = {
        "warning": {
            "warning_id": record.get("warning_id"),
            "tool_name": record.get("tool_name"),
            "rule_id": record.get("rule_id"),
            "message": record.get("message"),
            "cwe": record.get("cwe"),
            "file_path": record.get("file_path"),
            "line_number": record.get("line_number"),
            "function_name": record.get("function_name"),
            "sliced_code": record.get("sliced_code"),
        },
        "stage1_output": {
            "initial_semantic_prediction": stage1.get("semantic_prediction"),
            "semantic_confidence": stage1.get("semantic_confidence"),
            "supporting_reasoning": stage1.get("supporting_reasoning"),
            "uncertainty": stage1.get("uncertainty"),
        },
        "structured_warning_evolution": record.get("structured_warning_evolution", {}),
        "cwe_reasoning_schema": {"name": schema_name, "schema": schema_text},
    }
    return prompt_template + "\n\nInput JSON:\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def parse_json_response(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip().lstrip("\ufeff")
    if text.startswith("```"):
        first = text.find("\n")
        last = text.rfind("```")
        if first != -1 and last > first:
            text = text[first + 1:last].strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model response.")
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    parsed = json.loads(text[start:index + 1])
                    if not isinstance(parsed, dict):
                        raise ValueError("Parsed JSON response is not an object.")
                    return parsed
    raise ValueError("No balanced JSON object found in model response.")


def validate_stage2_output(parsed: dict[str, Any]) -> dict[str, Any]:
    final_label = canonical_label(parsed.get("final_label"))
    return {
        "initial_semantic_prediction": parsed.get("initial_semantic_prediction"),
        "cwe_reasoning_schema": parsed.get("cwe_reasoning_schema"),
        "defect_hypothesis": parsed.get("defect_hypothesis", ""),
        "defect_required_premises": parsed.get("defect_required_premises", []),
        "defect_structured_verification": parsed.get("defect_structured_verification", ""),
        "defect_status": parsed.get("defect_hypothesis_status", parsed.get("defect_status", "")),
        "safety_hypothesis": parsed.get("safety_hypothesis", ""),
        "safety_required_premises": parsed.get("safety_required_premises", []),
        "safety_structured_verification": parsed.get("safety_structured_verification", ""),
        "safety_status": parsed.get("safety_hypothesis_status", parsed.get("safety_status", "")),
        "evolution_evidence_reliability": parsed.get("evolution_evidence_reliability", ""),
        "evolution_analysis": parsed.get("evolution_analysis", ""),
        "cross_evidence_resolution": parsed.get("cross_evidence_resolution", ""),
        "final_reasoning": parsed.get("final_reasoning", ""),
        "final_prediction": final_label,
    }


def load_stage1_by_id(stage1_path: Path) -> dict[int, dict[str, Any]]:
    rows = load_json(stage1_path)
    by_id: dict[int, dict[str, Any]] = {}
    for row in rows:
        warning_id = int(row.get("warning_id", row.get("record_id")))
        by_id[warning_id] = {
            "semantic_prediction": canonical_label(row.get("semantic_prediction")),
            "semantic_confidence": row.get("semantic_confidence"),
            "supporting_reasoning": row.get("supporting_reasoning"),
            "uncertainty": row.get("uncertainty", ""),
        }
    return by_id


def load_fusion_records(stage1_path: Path) -> list[dict[str, Any]]:
    rows = load_json(PATHS.inference_input)
    stage1 = load_stage1_by_id(stage1_path)
    merged: list[dict[str, Any]] = []
    for row in rows:
        warning_id = int(row["warning_id"])
        if warning_id not in stage1:
            raise RuntimeError(f"Missing Stage 1 output for warning_id={warning_id}")
        item = dict(row)
        item["stage1"] = stage1[warning_id]
        merged.append(item)
    return merged


def make_agreement_prediction(record: dict[str, Any], provider: str) -> dict[str, Any]:
    stage1 = record["stage1"]
    label = canonical_label(stage1["semantic_prediction"])
    return {
        "warning_id": int(record["warning_id"]),
        "record_id": int(record["warning_id"]),
        "routing_status": "AGREEMENT_BYPASS",
        "status": "success",
        "branch": "AGREEMENT",
        "stage1_prediction": label,
        "stage1_confidence": stage1.get("semantic_confidence"),
        "stage1_reasoning": stage1.get("supporting_reasoning"),
        "stage1_uncertainty": stage1.get("uncertainty"),
        "final_prediction": label,
        "response_model": provider,
    }


def make_stage2_prediction(record: dict[str, Any], provider: str, parsed: dict[str, Any], raw_response_path: Path) -> dict[str, Any]:
    stage1 = record["stage1"]
    validated = validate_stage2_output(parsed)
    schema_name, _ = schema_for_cwe(record.get("cwe"))
    return {
        "warning_id": int(record["warning_id"]),
        "record_id": int(record["warning_id"]),
        "tool": record.get("tool_name"),
        "rule": record.get("rule_id"),
        "CWE": record.get("cwe"),
        "project": record.get("project_name"),
        "message": record.get("message"),
        "file_path": record.get("file_path"),
        "function_name": record.get("function_name"),
        "routing_status": "STAGE2_DISAGREEMENT",
        "branch": "BRANCH_A" if canonical_label(stage1["semantic_prediction"]) == "TP" else "BRANCH_B",
        "stage1_prediction": canonical_label(stage1["semantic_prediction"]),
        "stage1_confidence": stage1.get("semantic_confidence"),
        "stage1_reasoning": stage1.get("supporting_reasoning"),
        "stage1_uncertainty": stage1.get("uncertainty"),
        "schema": schema_name,
        "structured_evolution_evidence": record.get("structured_warning_evolution", {}),
        "raw_response_path": str(raw_response_path.relative_to(PATHS.repo_root)),
        "response_model": provider,
        **validated,
    }


def call_chat_completion(*, base_url: str, api_key: str, model: str, prompt: str, timeout: int, temperature: float, top_p: float) -> tuple[str, dict[str, Any]]:
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "top_p": top_p,
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    return content, payload.get("usage", {})


def execute_fusion(
    *,
    provider: str,
    args: argparse.Namespace,
    stage1_path: Path,
) -> None:
    require_execution_env(args)
    records = load_fusion_records(stage1_path)
    if args.limit is not None:
        records = records[: args.limit]
    runtime_dir = Path(args.runtime_dir)
    if not runtime_dir.is_absolute():
        runtime_dir = PATHS.repo_root / runtime_dir
    raw_dir = runtime_dir / "raw_responses"
    checkpoint_path = runtime_dir / "checkpoint.jsonl"
    predictions_path = runtime_dir / "predictions.json"
    raw_dir.mkdir(parents=True, exist_ok=True)

    completed: dict[int, dict[str, Any]] = {}
    if args.resume and checkpoint_path.exists():
        for row in load_jsonl(checkpoint_path):
            completed[int(row["warning_id"])] = row["prediction"]

    api_key = os.environ[args.api_key_env]
    predictions: list[dict[str, Any]] = []
    for record in records:
        warning_id = int(record["warning_id"])
        if warning_id in completed:
            predictions.append(completed[warning_id])
            continue
        stage1_label = canonical_label(record["stage1"]["semantic_prediction"])
        routing_label = canonical_label(record["heuristic_label_for_routing_only"])
        if stage1_label == routing_label:
            prediction = make_agreement_prediction(record, provider)
        else:
            prompt = build_stage2_prompt(record)
            if EVALUATION_FIELD_RE.search(prompt) or HEURISTIC_LABEL_RE.search(prompt):
                raise RuntimeError(f"Prompt isolation failed for warning_id={warning_id}")
            raw_text, usage = call_chat_completion(
                base_url=args.base_url,
                api_key=api_key,
                model=args.model,
                prompt=prompt,
                timeout=args.timeout,
                temperature=args.temperature,
                top_p=args.top_p,
            )
            raw_path = raw_dir / f"{warning_id}.json"
            save_json(raw_path, {"warning_id": warning_id, "raw_response": raw_text, "usage": usage})
            parsed = parse_json_response(raw_text)
            prediction = make_stage2_prediction(record, provider, parsed, raw_path)
            prediction["usage"] = usage
        append_jsonl(
            checkpoint_path,
            {
                "warning_id": warning_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prediction": prediction,
            },
        )
        predictions.append(prediction)
        if args.request_delay:
            time.sleep(args.request_delay)
    save_json(predictions_path, predictions)
    print(f"Wrote runtime predictions to {predictions_path}")


def validate_stage2_prompt_isolation(stage1_path: Path | None = None) -> list[str]:
    issues: list[str] = []
    data = load_fusion_records(stage1_path or PATHS.stage1_results)
    for row in data:
        stage1_label = canonical_label(row.get("stage1", {}).get("semantic_prediction", "FP"))
        routing_label = canonical_label(row.get("heuristic_label_for_routing_only", "FP"))
        if stage1_label == routing_label:
            continue
        prompt = build_stage2_prompt(row)
        if EVALUATION_FIELD_RE.search(prompt):
            issues.append(f"Stage 2 prompt for warning {row.get('warning_id')} contains evaluation label text.")
        if HEURISTIC_LABEL_RE.search(prompt):
            issues.append(f"Stage 2 prompt for warning {row.get('warning_id')} contains heuristic-label text.")
        if issues:
            break
    return issues


def write_preflight_report(model: str | None = None, stage1_path: Path | None = None) -> bool:
    checks: list[tuple[str, bool, str]] = []
    path_issues = validate_required_paths(model)
    checks.append(("Required input files", not path_issues, "; ".join(path_issues) or "All required paths exist."))
    input_issues = [] if path_issues else validate_inference_input()
    checks.append(("Inference input has no evaluation label fields", not input_issues, "; ".join(input_issues[:5]) or "No evaluation label fields found."))
    prompt_issues = [] if path_issues or input_issues else validate_stage2_prompt_isolation(stage1_path)
    checks.append(("Stage 2 prompt isolation", not prompt_issues, "; ".join(prompt_issues[:5]) or "No heuristic label or evaluation label leakage detected."))

    lines = [
        "# Fusion Preflight Validation",
        "",
        "- Repository layout validated.",
        f"- Model scope: `{model or 'all'}`",
        "",
        "| Check | Result | Detail |",
        "| --- | --- | --- |",
    ]
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    lines.extend(["", "## Input Hashes", ""])
    for path in required_input_paths(model):
        if path.exists():
            lines.append(f"- `{path.relative_to(PATHS.repo_root)}`: `{sha256_file(path)}`")
    PATHS.preflight_report.parent.mkdir(parents=True, exist_ok=True)
    PATHS.preflight_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return all(ok for _, ok, _ in checks)


def add_common_args(parser: argparse.ArgumentParser, *, model_env: str, key_env: str, base_url_env: str) -> None:
    parser.add_argument("--preflight", action="store_true", help="Validate paths and prompt isolation without API calls.")
    parser.add_argument("--execute", action="store_true", help="Run model requests for the final fusion method.")
    parser.add_argument("--model", default=os.environ.get(model_env, ""))
    parser.add_argument("--api-key-env", default=key_env)
    parser.add_argument("--base-url", default=os.environ.get(base_url_env, ""))
    parser.add_argument("--runtime-dir", default=None, help="Ignored local runtime output directory.")
    parser.add_argument("--resume", action="store_true", help="Reuse entries from runtime checkpoint.jsonl.")
    parser.add_argument("--limit", type=int, default=None, help="Optional local execution limit.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--request-delay", type=float, default=0.0)


def require_execution_env(args: argparse.Namespace) -> None:
    if not args.execute:
        return
    if not args.model:
        raise RuntimeError("A model must be provided through the CLI or environment.")
    if not args.base_url:
        raise RuntimeError("A base URL must be provided through the CLI or environment.")
    if not os.environ.get(args.api_key_env):
        raise RuntimeError(f"Missing API key environment variable: {args.api_key_env}")
