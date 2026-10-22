from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[2]
LLM_DIR = ROOT_DIR / "03_llm"
DEEPSEEK_DIR = LLM_DIR / "deepseek"

BENCHMARK_PATH = ROOT_DIR / "01_dataset" / "processed" / "benchmark" / "benchmark_warnings_1027.json"
GROUND_TRUTH_PATH = ROOT_DIR / "04_analysis" / "ground_truth" / "ground_truth_labels_1027.json"
PROMPT_PATH = ROOT_DIR / "03_llm" / "prompts" / "baseline_binary_prompt.py"

OUTPUT_PATH = DEEPSEEK_DIR / "results" / "deepseek_v4_flash_semantic_baseline_1027.json"
CHECKPOINT_PATH = DEEPSEEK_DIR / "results" / "deepseek_v4_flash_semantic_baseline_1027_checkpoint.json"
LOG_PATH = DEEPSEEK_DIR / "results" / "deepseek_v4_flash_semantic_baseline_1027.log"

DEFAULT_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEFAULT_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEFAULT_TEMPERATURE = 0.0
DEFAULT_TOP_P = 1.0
DEFAULT_THINKING_MODE = os.environ.get("DEEPSEEK_THINKING_MODE", "disabled")
DEFAULT_WORKERS = 4
DEFAULT_RETRIES = 3
DEFAULT_TIMEOUT = 180
DEFAULT_SLEEP_SECONDS = 0.0
PROMPT_STRATEGY = "semantic_binary_baseline"

REPAIR_PROMPT = """The previous response was invalid or incomplete.

Return one valid JSON object only, with no Markdown and no extra text.

Required fields:
- id
- llm_label
- llm_label_reason

Rules:
- llm_label must be TP or FP.
- llm_label_reason must be a concise explanation.
- Preserve the original warning id when possible.
"""


class ParseResponseError(ValueError):
    def __init__(self, message: str, raw_text: str, prompt_length: int, response_model: str) -> None:
        super().__init__(message)
        self.raw_text = raw_text
        self.prompt_length = prompt_length
        self.response_model = response_model


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("deepseek_v4_flash_semantic_baseline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=lambda row: int(row.get("warning_id", 0)))
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_prompt_template(prompt_path: Path) -> str:
    spec = importlib.util.spec_from_file_location(prompt_path.stem, prompt_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load prompt template from {prompt_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    template = getattr(module, "PROMPT_TEMPLATE", None)
    if not isinstance(template, str):
        raise RuntimeError(f"PROMPT_TEMPLATE not found in {prompt_path}")
    return template


def build_dataset() -> list[dict]:
    benchmark_rows = load_json(BENCHMARK_PATH)
    ground_truth_rows = load_json(GROUND_TRUTH_PATH)
    if len(benchmark_rows) != 1027:
        raise RuntimeError(f"Expected 1027 benchmark rows, found {len(benchmark_rows)}")
    if len(ground_truth_rows) != 1027:
        raise RuntimeError(f"Expected 1027 ground-truth rows, found {len(ground_truth_rows)}")

    gt_by_id = {int(row["warning_id"]): row["ground_truth_label"] for row in ground_truth_rows}
    merged: list[dict] = []
    seen_ids: set[int] = set()
    for row in benchmark_rows:
        warning_id = int(row["warning_id"])
        if warning_id in seen_ids:
            raise RuntimeError(f"Duplicate warning_id in benchmark: {warning_id}")
        seen_ids.add(warning_id)
        merged_row = dict(row)
        merged_row["ground_truth_label"] = gt_by_id.get(warning_id)
        if merged_row["ground_truth_label"] not in {"TP", "FP"}:
            raise RuntimeError(f"Missing or invalid ground truth for warning_id={warning_id}")
        merged.append(merged_row)
    return merged


def build_user_payload(item: dict) -> dict:
    return {
        "id": int(item["warning_id"]),
        "tool_name": item.get("tool_name"),
        "project_name_with_version": item.get("project_name_with_version"),
        "project_version": item.get("project_version"),
        "line_number": item.get("line_number"),
        "function_name": item.get("function_name"),
        "rule_id": item.get("rule_id"),
        "message": item.get("message"),
        "sliced_code": item.get("sliced_code"),
        "file_path": item.get("file_path"),
        "cwe": item.get("cwe"),
        "severity": item.get("severity"),
    }


def extract_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Response does not contain a JSON object.")
    return json.loads(cleaned[start : end + 1])


def normalize_label(value: object) -> str:
    text = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    mapping = {
        "TP": "TP",
        "TRUE_POSITIVE": "TP",
        "TRUEPOSITIVE": "TP",
        "FP": "FP",
        "FALSE_POSITIVE": "FP",
        "FALSEPOSITIVE": "FP",
    }
    if text not in mapping:
        raise ValueError(f"Invalid label: {value!r}")
    return mapping[text]


def fallback_parse_malformed_json(text: str) -> dict:
    id_match = re.search(r'"id"\s*:\s*(\d+)', text)
    label_match = re.search(r'"llm_label"\s*:\s*"([^"]+)"', text)
    reason_match = re.search(r'"llm_label_reason"\s*:\s*"(.*)"\s*\}\s*$', text, flags=re.DOTALL)
    if not (id_match and label_match and reason_match):
        raise ValueError("Fallback JSON repair could not recover required fields.")
    return {
        "id": int(id_match.group(1)),
        "llm_label": normalize_label(label_match.group(1)),
        "llm_label_reason": reason_match.group(1),
    }


def parse_response(text: str) -> tuple[dict, list[str]]:
    try:
        result = extract_json_object(text)
        label_value = result.get("llm_label", result.get("label", result.get("final_label")))
        reason_value = result.get("llm_label_reason", result.get("reason", result.get("final_reason", "")))
        parsed = {
            "id": result.get("id", result.get("warning_id")),
            "llm_label": normalize_label(label_value),
            "llm_label_reason": str(reason_value or "").strip(),
        }
    except Exception:
        parsed = fallback_parse_malformed_json(text)
    missing = [field for field in ("id", "llm_label", "llm_label_reason") if not parsed.get(field)]
    return parsed, missing


def call_model(
    session: requests.Session,
    model: str,
    base_url: str,
    api_key: str,
    system_prompt: str,
    item: dict,
    temperature: float,
    top_p: float,
    thinking_mode: str,
    timeout_seconds: int,
) -> tuple[dict, list[str], str, int, str]:
    user_payload = json.dumps(build_user_payload(item), ensure_ascii=False, indent=2)
    api_url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
        "response_format": {"type": "json_object"},
        "stream": False,
        "thinking": {"type": thinking_mode},
    }
    if thinking_mode == "disabled":
        payload["temperature"] = temperature
        payload["top_p"] = top_p
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = session.post(api_url, headers=headers, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    payload_json = response.json()
    raw_text = payload_json["choices"][0]["message"]["content"]
    response_model = str(payload_json.get("model") or model)
    try:
        parsed, missing = parse_response(raw_text)
    except Exception as exc:
        raise ParseResponseError(str(exc), raw_text, len(user_payload), response_model) from exc
    return parsed, missing, raw_text, len(user_payload), response_model


def call_repair_model(
    session: requests.Session,
    model: str,
    base_url: str,
    api_key: str,
    original_response: str,
    temperature: float,
    top_p: float,
    thinking_mode: str,
    timeout_seconds: int,
) -> tuple[dict, list[str], str, str]:
    api_url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": REPAIR_PROMPT},
            {"role": "user", "content": original_response},
        ],
        "response_format": {"type": "json_object"},
        "stream": False,
        "thinking": {"type": thinking_mode},
    }
    if thinking_mode == "disabled":
        payload["temperature"] = temperature
        payload["top_p"] = top_p
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = session.post(api_url, headers=headers, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    payload_json = response.json()
    raw_text = payload_json["choices"][0]["message"]["content"]
    response_model = str(payload_json.get("model") or model)
    parsed, missing = parse_response(raw_text)
    return parsed, missing, raw_text, response_model


def build_success_record(
    item: dict,
    parsed: dict,
    *,
    raw_response: str,
    prompt_length: int,
    response_length: int,
    retry_count: int,
    repair_count: int,
    request_model: str,
    response_model: str,
    base_url: str,
    thinking_mode: str,
    temperature: float,
    top_p: float,
) -> dict:
    return {
        "warning_id": int(item["warning_id"]),
        "final_label": parsed["llm_label"],
        "final_reason": parsed["llm_label_reason"],
        "llm_label": parsed["llm_label"],
        "llm_label_reason": parsed["llm_label_reason"],
        "ground_truth_label": item.get("ground_truth_label"),
        "tool_name": item.get("tool_name"),
        "project_name": item.get("project_name"),
        "project_name_with_version": item.get("project_name_with_version"),
        "project_version": item.get("project_version"),
        "file_path": item.get("file_path"),
        "line_number": item.get("line_number"),
        "function_name": item.get("function_name"),
        "rule_id": item.get("rule_id"),
        "message": item.get("message"),
        "sliced_code": item.get("sliced_code"),
        "cwe": item.get("cwe"),
        "severity": item.get("severity"),
        "source_dataset": item.get("source_dataset"),
        "raw_response": raw_response,
        "parsed_response": parsed,
        "retry_count": retry_count,
        "repair_count": repair_count,
        "prompt_length": prompt_length,
        "response_length": response_length,
        "status": "success",
        "error_message": "",
        "request_model": request_model,
        "response_model": response_model,
        "base_url": base_url,
        "thinking_mode": thinking_mode,
        "temperature": temperature,
        "top_p": top_p,
        "prompt_strategy": PROMPT_STRATEGY,
        "prompt_path": str(PROMPT_PATH),
    }


def build_failure_record(
    item: dict,
    *,
    error_message: str,
    raw_response: str,
    prompt_length: int,
    response_length: int,
    retry_count: int,
    repair_count: int,
    request_model: str,
    response_model: str,
    base_url: str,
    thinking_mode: str,
    temperature: float,
    top_p: float,
) -> dict:
    return {
        "warning_id": int(item["warning_id"]),
        "final_label": "",
        "final_reason": "",
        "llm_label": "",
        "llm_label_reason": "",
        "ground_truth_label": item.get("ground_truth_label"),
        "tool_name": item.get("tool_name"),
        "project_name": item.get("project_name"),
        "project_name_with_version": item.get("project_name_with_version"),
        "project_version": item.get("project_version"),
        "file_path": item.get("file_path"),
        "line_number": item.get("line_number"),
        "function_name": item.get("function_name"),
        "rule_id": item.get("rule_id"),
        "message": item.get("message"),
        "sliced_code": item.get("sliced_code"),
        "cwe": item.get("cwe"),
        "severity": item.get("severity"),
        "source_dataset": item.get("source_dataset"),
        "raw_response": raw_response,
        "parsed_response": {},
        "retry_count": retry_count,
        "repair_count": repair_count,
        "prompt_length": prompt_length,
        "response_length": response_length,
        "status": "failed",
        "error_message": error_message,
        "request_model": request_model,
        "response_model": response_model,
        "base_url": base_url,
        "thinking_mode": thinking_mode,
        "temperature": temperature,
        "top_p": top_p,
        "prompt_strategy": PROMPT_STRATEGY,
        "prompt_path": str(PROMPT_PATH),
    }


def process_one(
    item: dict,
    *,
    model: str,
    base_url: str,
    api_key: str,
    system_prompt: str,
    temperature: float,
    top_p: float,
    thinking_mode: str,
    retries: int,
    timeout_seconds: int,
    sleep_seconds: float,
    logger: logging.Logger,
) -> dict:
    last_error = ""
    last_raw_response = ""
    last_prompt_length = 0
    last_response_length = 0
    total_repairs = 0
    response_model = ""
    with requests.Session() as session:
        session.trust_env = False
        for attempt in range(1, retries + 1):
            try:
                parsed, missing, raw_response, prompt_length, response_model = call_model(
                    session=session,
                    model=model,
                    base_url=base_url,
                    api_key=api_key,
                    system_prompt=system_prompt,
                    item=item,
                    temperature=temperature,
                    top_p=top_p,
                    thinking_mode=thinking_mode,
                    timeout_seconds=timeout_seconds,
                )
                last_raw_response = raw_response
                last_prompt_length = prompt_length
                last_response_length = len(raw_response)
                if missing:
                    parsed, missing, repaired_text, repaired_model = call_repair_model(
                        session=session,
                        model=model,
                        base_url=base_url,
                        api_key=api_key,
                        original_response=raw_response,
                        temperature=temperature,
                        top_p=top_p,
                        thinking_mode=thinking_mode,
                        timeout_seconds=timeout_seconds,
                    )
                    total_repairs += 1
                    last_raw_response = repaired_text
                    last_response_length = len(repaired_text)
                    response_model = repaired_model or response_model
                    if missing:
                        raise ValueError(f"Missing fields after repair: {missing}")
                logger.info(
                    "warning_id=%s status=success final_label=%s retry_count=%s repair_count=%s prompt_length=%s response_length=%s response_model=%s",
                    item["warning_id"],
                    parsed["llm_label"],
                    attempt - 1,
                    total_repairs,
                    last_prompt_length,
                    last_response_length,
                    response_model,
                )
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                return build_success_record(
                    item,
                    parsed,
                    raw_response=last_raw_response,
                    prompt_length=last_prompt_length,
                    response_length=last_response_length,
                    retry_count=attempt - 1,
                    repair_count=total_repairs,
                    request_model=model,
                    response_model=response_model,
                    base_url=base_url,
                    thinking_mode=thinking_mode,
                    temperature=temperature,
                    top_p=top_p,
                )
            except ParseResponseError as exc:
                last_error = str(exc)
                last_raw_response = exc.raw_text
                last_prompt_length = exc.prompt_length
                last_response_length = len(exc.raw_text)
                response_model = exc.response_model
                try:
                    parsed, missing, repaired_text, repaired_model = call_repair_model(
                        session=session,
                        model=model,
                        base_url=base_url,
                        api_key=api_key,
                        original_response=exc.raw_text,
                        temperature=temperature,
                        top_p=top_p,
                        thinking_mode=thinking_mode,
                        timeout_seconds=timeout_seconds,
                    )
                    total_repairs += 1
                    last_raw_response = repaired_text
                    last_response_length = len(repaired_text)
                    response_model = repaired_model or response_model
                    if missing:
                        raise ValueError(f"Missing fields after repair: {missing}")
                    logger.info(
                        "warning_id=%s status=success final_label=%s retry_count=%s repair_count=%s prompt_length=%s response_length=%s response_model=%s",
                        item["warning_id"],
                        parsed["llm_label"],
                        attempt - 1,
                        total_repairs,
                        last_prompt_length,
                        last_response_length,
                        response_model,
                    )
                    if sleep_seconds > 0:
                        time.sleep(sleep_seconds)
                    return build_success_record(
                        item,
                        parsed,
                        raw_response=last_raw_response,
                        prompt_length=last_prompt_length,
                        response_length=last_response_length,
                        retry_count=attempt - 1,
                        repair_count=total_repairs,
                        request_model=model,
                        response_model=response_model,
                        base_url=base_url,
                        thinking_mode=thinking_mode,
                        temperature=temperature,
                        top_p=top_p,
                    )
                except Exception as repair_exc:
                    last_error = f"{exc}; repair_failed: {repair_exc}"
                    logger.warning(
                        "warning_id=%s attempt=%s/%s failed after repair: %s",
                        item["warning_id"],
                        attempt,
                        retries,
                        last_error,
                    )
                    if attempt < retries:
                        time.sleep(5)
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "warning_id=%s attempt=%s/%s failed: %s",
                    item["warning_id"],
                    attempt,
                    retries,
                    exc,
                )
                if attempt < retries:
                    time.sleep(5)
    return build_failure_record(
        item,
        error_message=last_error,
        raw_response=last_raw_response,
        prompt_length=last_prompt_length,
        response_length=last_response_length,
        retry_count=retries,
        repair_count=total_repairs,
        request_model=model,
        response_model=response_model,
        base_url=base_url,
        thinking_mode=thinking_mode,
        temperature=temperature,
        top_p=top_p,
    )


def load_existing_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = load_json(path)
    if not isinstance(rows, list):
        raise RuntimeError(f"Existing output is not a list: {path}")
    return rows


def persist_progress(output_path: Path, checkpoint_path: Path, records: list[dict]) -> None:
    save_json(output_path, records)
    save_json(checkpoint_path, records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--top-p", type=float, default=DEFAULT_TOP_P)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--thinking-mode", choices=("enabled", "disabled"), default=DEFAULT_THINKING_MODE)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sample-ids-path", default="")
    parser.add_argument("--output-path", default=str(OUTPUT_PATH))
    parser.add_argument("--checkpoint-path", default=str(CHECKPOINT_PATH))
    parser.add_argument("--log-path", default=str(LOG_PATH))
    parser.add_argument("--request-sleep-seconds", type=float, default=DEFAULT_SLEEP_SECONDS)
    args = parser.parse_args()

    output_path = Path(args.output_path).resolve()
    checkpoint_path = Path(args.checkpoint_path).resolve()
    log_path = Path(args.log_path).resolve()
    logger = setup_logger(log_path)

    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set.")

    dataset = build_dataset()
    if args.sample_ids_path:
        sample_ids = {
            int(line.strip())
            for line in Path(args.sample_ids_path).read_text(encoding="utf-8").splitlines()
            if line.strip() and line.strip().isdigit()
        }
        dataset = [row for row in dataset if int(row["warning_id"]) in sample_ids]
    if args.limit is not None:
        dataset = dataset[: args.limit]
    if not dataset:
        raise RuntimeError("No dataset rows selected for this run.")

    system_prompt = load_prompt_template(PROMPT_PATH)

    existing_records = load_existing_records(output_path)
    record_by_id = {int(record["warning_id"]): record for record in existing_records if "warning_id" in record}
    done_ids = {
        warning_id
        for warning_id, record in record_by_id.items()
        if record.get("status") == "success" and record.get("final_label") in {"TP", "FP"}
    }
    pending = [row for row in dataset if int(row["warning_id"]) not in done_ids]

    logger.info(
        "starting semantic baseline rerun: model=%s base_url=%s thinking_mode=%s temperature=%s top_p=%s workers=%s total=%s completed=%s pending=%s prompt=%s",
        args.model,
        args.base_url,
        args.thinking_mode,
        args.temperature,
        args.top_p,
        args.workers,
        len(dataset),
        len(done_ids),
        len(pending),
        PROMPT_PATH,
    )

    if not pending:
        logger.info("nothing pending; run is already complete")
        persist_progress(output_path, checkpoint_path, list(record_by_id.values()))
        return

    completed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(
                process_one,
                item,
                model=args.model,
                base_url=args.base_url,
                api_key=api_key,
                system_prompt=system_prompt,
                temperature=args.temperature,
                top_p=args.top_p,
                thinking_mode=args.thinking_mode,
                retries=args.retries,
                timeout_seconds=args.timeout_seconds,
                sleep_seconds=args.request_sleep_seconds,
                logger=logger,
            ): item
            for item in pending
        }
        for future in as_completed(future_map):
            item = future_map[future]
            record = future.result()
            record_by_id[int(item["warning_id"])] = record
            completed += 1
            if completed % 10 == 0 or completed == len(pending):
                persist_progress(output_path, checkpoint_path, list(record_by_id.values()))
                logger.info("checkpoint saved after %s/%s pending items", completed, len(pending))

    persist_progress(output_path, checkpoint_path, list(record_by_id.values()))
    success_count = sum(1 for record in record_by_id.values() if record.get("status") == "success")
    failed_count = sum(1 for record in record_by_id.values() if record.get("status") == "failed")
    repair_total = sum(int(record.get("repair_count", 0) or 0) for record in record_by_id.values())
    logger.info(
        "run finished: total=%s success=%s failed=%s repair_total=%s output=%s checkpoint=%s",
        len(record_by_id),
        success_count,
        failed_count,
        repair_total,
        output_path,
        checkpoint_path,
    )


if __name__ == "__main__":
    main()
