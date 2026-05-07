"""Shared paths and defaults for UniPCB evaluation."""

from __future__ import annotations

import os
from dataclasses import dataclass


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


@dataclass(frozen=True)
class EvalDefaults:
    benchmark_json: str = os.path.join(
        PROJECT_ROOT,
        "data",
        "benchmark",
        "generated",
        "generate_vqa_bilingual_test",
        "all_vqa_data_bilingual_20260426_190307.json",
    )
    results_dir: str = os.path.join(PROJECT_ROOT, "data", "benchmark", "results")
    prior_knowledge_file: str = os.path.join(
        PROJECT_ROOT,
        "scripts",
        "benchmark_generation",
        "test_prior_knowledge.json",
    )
    api_base: str = os.environ.get("UNIPCB_API_BASE", "http://localhost:10029/v1")
    model: str = os.environ.get("UNIPCB_MODEL_PATH", "Qwen2.5-VL-72B-Instruct-AWQ")
    max_workers: int = int(os.environ.get("UNIPCB_EVAL_MAX_WORKERS", "8"))
    iou_threshold: float = float(os.environ.get("UNIPCB_EVAL_IOU", "0.3"))


DEFAULTS = EvalDefaults()

