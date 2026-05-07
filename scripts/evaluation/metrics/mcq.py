"""Multiple-choice extraction and scoring."""

from __future__ import annotations

import re
from typing import List, Optional


def strip_option_prefix(option: str) -> str:
    return re.sub(r"^\s*[A-Da-d][\.\)]\s*", "", str(option)).strip()


def correct_letter(correct_option: str, options: List[str], provided: Optional[str] = None) -> Optional[str]:
    if provided and str(provided).strip().upper() in {"A", "B", "C", "D"}:
        return str(provided).strip().upper()
    correct_clean = str(correct_option).strip().lower()
    for idx, option in enumerate(options or []):
        if strip_option_prefix(option).strip().lower() == correct_clean:
            return chr(ord("A") + idx)
    return None


def extract_answer_letter(response: str) -> Optional[str]:
    if not isinstance(response, str):
        return None
    text = response.strip()

    answer_match = re.search(r"<answer>\s*([A-Da-d])\s*</answer>", text, flags=re.I | re.S)
    if answer_match:
        return answer_match.group(1).upper()

    tag_match = re.search(r"<\s*([A-Da-d])\s*/?\s*>", text)
    if tag_match:
        return tag_match.group(1).upper()

    explicit = re.search(r"(?:answer|option|答案|选项)\s*(?:is|为|是|:|：)?\s*([A-Da-d])\b", text, flags=re.I)
    if explicit:
        return explicit.group(1).upper()

    standalone = re.search(r"\b([A-Da-d])\b", text)
    return standalone.group(1).upper() if standalone else None


def score_mcq(response: str, correct_option: str, options: List[str], provided_letter: Optional[str] = None) -> int:
    pred = extract_answer_letter(response)
    gold = correct_letter(correct_option, options, provided_letter)
    return int(bool(pred and gold and pred == gold))

