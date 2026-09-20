from __future__ import annotations

import argparse

from fusion_common import PATHS, add_common_args, execute_fusion, write_preflight_report


def main() -> None:
    parser = argparse.ArgumentParser(description="DeepSeek fusion runner for the final paper method.")
    add_common_args(
        parser,
        model_env="DEEPSEEK_MODEL",
        key_env="DEEPSEEK_API_KEY",
        base_url_env="DEEPSEEK_BASE_URL",
    )
    args = parser.parse_args()
    if args.runtime_dir is None:
        args.runtime_dir = "05_fusion/runtime/deepseek"

    ok = write_preflight_report("deepseek", PATHS.stage1_results)
    print(f"Preflight report: 05_fusion/analysis/preflight_validation.md ({'PASS' if ok else 'FAIL'})")
    if not ok:
        raise SystemExit(1)
    if not args.execute:
        print("No API calls made. Pass --execute explicitly to run predictions.")
        return
    execute_fusion(provider="deepseek", args=args, stage1_path=PATHS.stage1_results)


if __name__ == "__main__":
    main()
