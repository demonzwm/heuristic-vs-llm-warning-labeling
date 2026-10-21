"""Hash the released data, prompts, predictions, and analysis files."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def released_bytes(path):
    """Git stores text in LF form; normalize Windows worktree CRLF first."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def main():
    included = []
    for pattern in (
        "01_dataset/processed/benchmark/benchmark_warnings_1027.json",
        "02_heuristic/scripts/*.py", "02_heuristic/*.json",
        "02_heuristic/results/*.json", "02_heuristic/results/*.csv",
        "03_llm/deepseek/results/deepseek_v4_flash_semantic_baseline_1027.json",
        "03_llm/gpt/inputs/*.json", "03_llm/gpt/results/*.json",
        "04_analysis/ground_truth/*.json", "04_analysis/ground_truth/*.csv",
        "04_analysis/results/**/*.json", "04_analysis/results/**/*.csv",
        "05_fusion/method/**/*.json", "05_fusion/method/**/*.jsonl", "05_fusion/method/**/*.md",
        "05_fusion/method/**/*.txt", "05_fusion/**/results/*.json",
        "05_fusion/analysis/results/*.csv", "05_fusion/analysis/results/*.json",
    ):
        included.extend(ROOT.glob(pattern))
    included = sorted({p for p in included if p.is_file()})
    data = {
        "release": "paper artifact final reproducibility package",
        "warning_count": 1027,
        "ground_truth_counts": {"TP": 54, "FP": 973},
        "methods": {"Heuristic": "cross-version warning matching",
                    "LLM": ["DeepSeek-v4-flash", "gpt-6-luna"],
                    "Fusion": "full Stage 2 verification of all 1,027 warnings"},
        "hash_byte_convention": "SHA-256 after CRLF-to-LF normalization, matching Git repository blobs",
        "gpt_reasoning_effort": "low",
        "selected_ground_truth_changes": {"150": "TP", "161": "TP", "342": "FP",
                                          "596": "TP", "983": "TP"},
        "sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(released_bytes(p)).hexdigest()
                   for p in included},
    }
    (ROOT / "ARTIFACT_MANIFEST.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Hashed {len(included)} release files.")


if __name__ == "__main__":
    main()
