"""Validate that UniPCB benchmark JSON image references resolve locally."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BENCHMARK = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "generated"
    / "generate_vqa_bilingual_test"
    / "all_vqa_data_bilingual_20260426_190307.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate UniPCB image paths.")
    parser.add_argument("--input", default=str(DEFAULT_BENCHMARK), help="Benchmark JSON file.")
    parser.add_argument("--root", default=str(PROJECT_ROOT), help="Repository or unpacked dataset root.")
    parser.add_argument("--max_missing", type=int, default=20, help="Maximum missing paths to print.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]

    image_refs = []
    for sample in data:
        image_refs.extend(path for path in sample.get("images", []) if isinstance(path, str))

    missing = [path for path in image_refs if not (root / path).exists()]
    print(f"records={len(data)}")
    print(f"image_refs={len(image_refs)}")
    print(f"unique_image_refs={len(set(image_refs))}")
    print(f"missing={len(missing)}")

    for path in missing[: args.max_missing]:
        print(path)

    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
