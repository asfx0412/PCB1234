"""Lightweight open-ended text metrics without mandatory model downloads."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Dict


def _tokens(text: str) -> list[str]:
    text = str(text or "").lower()
    zh = re.findall(r"[\u4e00-\u9fff]", text)
    words = re.findall(r"[a-z0-9]+", text)
    return zh + words


def token_f1(pred: str, ref: str) -> float:
    pred_tokens = _tokens(pred)
    ref_tokens = _tokens(ref)
    if not pred_tokens and not ref_tokens:
        return 1.0
    if not pred_tokens or not ref_tokens:
        return 0.0
    ref_counts = {}
    for token in ref_tokens:
        ref_counts[token] = ref_counts.get(token, 0) + 1
    overlap = 0
    for token in pred_tokens:
        if ref_counts.get(token, 0) > 0:
            overlap += 1
            ref_counts[token] -= 1
    precision = overlap / len(pred_tokens)
    recall = overlap / len(ref_tokens)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def char_similarity(pred: str, ref: str) -> float:
    return SequenceMatcher(None, str(pred or ""), str(ref or "")).ratio()


def score_open_text(pred: str, ref: str) -> Dict[str, float]:
    return {
        "token_f1": token_f1(pred, ref),
        "char_similarity": char_similarity(pred, ref),
    }

