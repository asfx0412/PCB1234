"""Coordinate parsing and IoU metrics."""

from __future__ import annotations

import ast
import json
import re
from typing import Dict, List, Optional, Tuple

from evaluation.metrics.normalization import normalize_type


BoxObject = Dict[str, object]


def extract_answer_content(response: object) -> str:
    if not isinstance(response, str):
        return str(response or "")
    match = re.search(r"<answer>\s*(.*?)\s*</answer>", response, flags=re.I | re.S)
    if match:
        return match.group(1).strip()
    return re.sub(r"<think>.*?</think>", "", response, flags=re.I | re.S).strip()


def _json_candidates(text: str) -> List[str]:
    text = extract_answer_content(text)
    candidates = [text]
    candidates.extend(re.findall(r"```(?:json)?\s*({[\s\S]*?})\s*```", text, flags=re.I))
    brace = re.search(r"({[\s\S]*})", text)
    if brace:
        candidates.append(brace.group(1))
    return list(dict.fromkeys(candidates))


def _parse_dict(text: str) -> Optional[dict]:
    for candidate in _json_candidates(text):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        try:
            parsed = ast.literal_eval(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return None


def _to_box(coords: object, image_size: Tuple[Optional[int], Optional[int]]) -> Optional[List[int]]:
    if not isinstance(coords, list) or len(coords) != 4:
        return None
    img_w, img_h = image_size
    try:
        values = [float(v) for v in coords]
    except (TypeError, ValueError):
        return None
    if img_w and img_h and all(0 <= v <= 1 for v in values):
        values = [values[0] * img_w, values[1] * img_h, values[2] * img_w, values[3] * img_h]
    box = [int(round(v)) for v in values]
    if box[0] >= box[2] or box[1] >= box[3]:
        return None
    return box


def parse_coordinate_objects(
    text: str,
    image_size: Tuple[Optional[int], Optional[int]],
    dataset: str,
    q_type: str,
    type_maps: Dict[str, Dict[str, Dict[str, str]]],
) -> List[BoxObject]:
    parsed = _parse_dict(text)
    if not isinstance(parsed, dict):
        return []

    objects: List[BoxObject] = []
    for raw_type, raw_boxes in parsed.items():
        type_name = normalize_type(str(raw_type), dataset, q_type, type_maps)
        boxes = raw_boxes
        if isinstance(boxes, list) and len(boxes) == 4 and all(not isinstance(v, list) for v in boxes):
            boxes = [boxes]
        if not isinstance(boxes, list):
            continue
        for item in boxes:
            box = _to_box(item, image_size)
            if box:
                objects.append({"type": type_name, "bbox": box})
    return objects


def iou(box1: List[int], box2: List[int]) -> float:
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
    area2 = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0


def coordinate_metrics(preds: List[BoxObject], gts: List[BoxObject], threshold: float = 0.3) -> Dict[str, float]:
    matched = set()
    tp = 0
    fp = 0

    for pred in preds:
        best_iou = -1.0
        best_idx = -1
        for idx, gt in enumerate(gts):
            if idx in matched or pred.get("type") != gt.get("type"):
                continue
            score = iou(pred["bbox"], gt["bbox"])  # type: ignore[index]
            if score > best_iou:
                best_iou = score
                best_idx = idx
        if best_iou >= threshold and best_idx >= 0:
            tp += 1
            matched.add(best_idx)
        else:
            fp += 1

    fn = len(gts) - len(matched)
    precision = tp / (tp + fp) if tp + fp else (1.0 if not gts else 0.0)
    recall = tp / (tp + fn) if tp + fn else (1.0 if not preds else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}

