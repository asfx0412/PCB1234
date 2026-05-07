"""Evaluate UniPCB benchmark predictions."""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

CURRENT_DIR = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from evaluation.config import DEFAULTS
from evaluation.metrics.bbox import coordinate_metrics, parse_coordinate_objects
from evaluation.metrics.mcq import score_mcq
from evaluation.metrics.normalization import build_type_maps
from evaluation.metrics.text_similarity import score_open_text
from evaluation.utils.image import image_size
from evaluation.utils.io import load_json, save_json
from evaluation.utils.paths import default_output_path, ensure_dir, resolve_project_path


def is_coordinate_type(q_type: str) -> bool:
    q = str(q_type or "").lower()
    return "coordinate" in q or "bbox" in q


def sample_image_size(sample: dict) -> Tuple[int | None, int | None]:
    size = sample.get("image_size")
    if isinstance(size, list) and len(size) == 2:
        return int(size[1]), int(size[0])
    for path in sample.get("images", []):
        resolved = resolve_project_path(path)
        width, height = image_size(resolved)
        if width and height:
            return width, height
    return None, None


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize_groups(grouped: Dict[str, dict]) -> Dict[str, dict]:
    summary = {}
    for group, values in sorted(grouped.items()):
        item = {}
        if values["mcq"]:
            item["mcq_accuracy"] = mean(values["mcq"])
            item["mcq_count"] = len(values["mcq"])
        if values["open_token_f1"]:
            item["open_token_f1"] = mean(values["open_token_f1"])
            item["open_char_similarity"] = mean(values["open_char_similarity"])
            item["open_count"] = len(values["open_token_f1"])
        if values["coord_preds"] or values["coord_gts"]:
            item["coordinates"] = coordinate_metrics(values["coord_preds"], values["coord_gts"], values["iou_threshold"])
        summary[group] = item
    return summary


def add_default_group(grouped: Dict[str, dict], key: str, iou_threshold: float) -> dict:
    if key not in grouped:
        grouped[key] = {
            "mcq": [],
            "open_token_f1": [],
            "open_char_similarity": [],
            "coord_preds": [],
            "coord_gts": [],
            "iou_threshold": iou_threshold,
        }
    return grouped[key]


def evaluate_predictions(input_path: str, prior_knowledge_path: str, iou_threshold: float) -> dict:
    input_path = resolve_project_path(input_path)
    prior_knowledge_path = resolve_project_path(prior_knowledge_path)
    data = load_json(input_path)
    if isinstance(data, dict):
        data = [data]
    prior = load_json(prior_knowledge_path)
    type_maps = build_type_maps(prior)

    by_dataset_type: Dict[str, dict] = {}
    by_question_type: Dict[str, dict] = {}
    by_dataset: Dict[str, dict] = {}
    overall_holder: Dict[str, dict] = {}
    overall = add_default_group(overall_holder, "overall", iou_threshold)
    per_item = []

    for sample_idx, sample in enumerate(data):
        dataset_type = sample.get("dataset_type", "Unknown")
        dataset = sample.get("dataset", "Unknown")
        img_size = sample_image_size(sample)
        for qa_idx, qa in enumerate(sample.get("conversation", [])):
            q_type = qa.get("type", "Unknown")
            response = qa.get("model_response", "")
            correct = qa.get("correct_option", "")

            groups = [
                add_default_group(by_dataset_type, dataset_type, iou_threshold),
                add_default_group(by_question_type, q_type, iou_threshold),
                add_default_group(by_dataset, dataset, iou_threshold),
                overall,
            ]

            item_result = {
                "sample_idx": sample_idx,
                "qa_idx": qa_idx,
                "dataset": dataset,
                "dataset_type": dataset_type,
                "type": q_type,
            }

            if isinstance(qa.get("options"), list) and qa.get("options"):
                score = score_mcq(response, correct, qa.get("options", []), qa.get("correct_answer_letter"))
                for group in groups:
                    group["mcq"].append(score)
                item_result["metric"] = "mcq"
                item_result["score"] = score
            elif is_coordinate_type(q_type):
                preds = parse_coordinate_objects(response, img_size, dataset, q_type, type_maps)
                gts = parse_coordinate_objects(correct, img_size, dataset, q_type, type_maps)
                for group in groups:
                    group["coord_preds"].extend(preds)
                    group["coord_gts"].extend(gts)
                item_result["metric"] = "coordinates"
                item_result["pred_count"] = len(preds)
                item_result["gt_count"] = len(gts)
            else:
                scores = score_open_text(response, correct)
                for group in groups:
                    group["open_token_f1"].append(scores["token_f1"])
                    group["open_char_similarity"].append(scores["char_similarity"])
                item_result["metric"] = "open_text"
                item_result.update(scores)

            per_item.append(item_result)

    return {
        "input_file": input_path,
        "total_records": len(data),
        "total_qa": len(per_item),
        "overall": summarize_groups({"overall": overall})["overall"],
        "by_dataset_type": summarize_groups(by_dataset_type),
        "by_dataset": summarize_groups(by_dataset),
        "by_question_type": summarize_groups(by_question_type),
        "per_item": per_item,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate UniPCB benchmark predictions.")
    parser.add_argument("--input", required=True, help="Prediction JSON with model_response fields.")
    parser.add_argument("--output", default=None, help="Evaluation JSON output path.")
    parser.add_argument("--prior_knowledge", default=DEFAULTS.prior_knowledge_file)
    parser.add_argument("--iou_threshold", type=float, default=DEFAULTS.iou_threshold)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or default_output_path(
        os.path.join(DEFAULTS.results_dir, "evaluated"),
        "evaluation",
    )
    output = resolve_project_path(output)
    ensure_dir(os.path.dirname(output))
    report = evaluate_predictions(args.input, args.prior_knowledge, args.iou_threshold)
    save_json(report, output)
    print(f"Saved evaluation report to {output}")
    print(report["overall"])


if __name__ == "__main__":
    main()
