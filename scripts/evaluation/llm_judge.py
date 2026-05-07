"""Optional LLM-as-judge evaluation for open-ended UniPCB answers."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from tqdm import tqdm

CURRENT_DIR = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from evaluation.adapters.openai_compatible import OpenAICompatibleAdapter
from evaluation.config import DEFAULTS
from evaluation.metrics.bbox import extract_answer_content
from evaluation.utils.io import load_json, save_json
from evaluation.utils.paths import default_output_path, ensure_dir, resolve_project_path


PROMPT_ZH = """你是严格的评审员。请只基于参考答案和模型回答评分，不要假设图片或额外信息。

请给出 1-10 的整数分，评价维度包括正确性、完整性、相关性、清晰度和简洁性。
只输出一个 JSON 对象：
{"scores":{"correctness":8,"completeness":8,"relevance":9,"clarity":8,"conciseness":8},"overall":8,"comment":"简短说明"}

参考答案：
{ref}

模型回答：
{hyp}
"""

PROMPT_EN = """You are a strict evaluator. Score only from the reference answer and model response, without assuming images or extra information.

Give integer scores from 1 to 10 for correctness, completeness, relevance, clarity, and conciseness.
Output exactly one JSON object:
{"scores":{"correctness":8,"completeness":8,"relevance":9,"clarity":8,"conciseness":8},"overall":8,"comment":"short explanation"}

Reference:
{ref}

Model response:
{hyp}
"""


def is_open_item(qa: dict) -> bool:
    q_type = str(qa.get("type", "")).lower()
    return "options" not in qa and "coordinate" not in q_type and "bbox" not in q_type


def collect_open_items(data: List[dict]) -> List[dict]:
    items = []
    for sample_idx, sample in enumerate(data):
        for qa_idx, qa in enumerate(sample.get("conversation", [])):
            if not is_open_item(qa):
                continue
            items.append(
                {
                    "sample_idx": sample_idx,
                    "qa_idx": qa_idx,
                    "dataset": sample.get("dataset"),
                    "dataset_type": sample.get("dataset_type"),
                    "language": sample.get("language", "en"),
                    "type": qa.get("type"),
                    "question": qa.get("question", ""),
                    "ref": qa.get("correct_option", ""),
                    "hyp": extract_answer_content(qa.get("model_response", "")),
                }
            )
    return items


def parse_score(text: str) -> Dict[str, Any]:
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        parsed = json.loads(match.group(0) if match else text)
        scores = parsed.get("scores", {})
        overall = parsed.get("overall")
        if overall is None and isinstance(scores, dict) and scores:
            overall = sum(float(v) for v in scores.values()) / len(scores)
        overall = float(overall if overall is not None else 1.0)
        overall = min(10.0, max(1.0, overall))
        return {
            "overall_raw": overall,
            "overall": (overall - 1.0) / 9.0,
            "scores": scores,
            "comment": parsed.get("comment", ""),
            "raw": text,
        }
    except Exception:
        return {"overall_raw": 1.0, "overall": 0.0, "scores": {}, "comment": "parse_failed", "raw": text}


def judge_one(adapter: OpenAICompatibleAdapter, item: dict) -> dict:
    is_zh = str(item.get("language", "")).lower().startswith("zh")
    template = PROMPT_ZH if is_zh else PROMPT_EN
    prompt = template.format(ref=item.get("ref", ""), hyp=item.get("hyp", ""))
    content = [{"type": "text", "text": prompt}]
    response = adapter.generate([{"role": "user", "content": content}])
    item = dict(item)
    item["llm_judge"] = parse_score(response)
    return item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run optional LLM-as-judge scoring for open-ended answers.")
    parser.add_argument("--input", required=True, help="Prediction JSON with model_response fields.")
    parser.add_argument("--output", default=None)
    parser.add_argument("--api_base", default=DEFAULTS.api_base)
    parser.add_argument("--model", default=DEFAULTS.model)
    parser.add_argument("--api_key", default=os.environ.get("UNIPCB_API_KEY"))
    parser.add_argument("--sample_fraction", type=float, default=1.0)
    parser.add_argument("--max_items", type=int, default=0)
    parser.add_argument("--max_workers", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = resolve_project_path(args.input)
    data = load_json(input_path)
    if isinstance(data, dict):
        data = [data]
    items = collect_open_items(data)
    if args.sample_fraction < 1.0:
        random.seed(42)
        keep = max(1, int(len(items) * args.sample_fraction))
        items = random.sample(items, keep)
    if args.max_items and args.max_items > 0:
        items = items[: args.max_items]

    adapter = OpenAICompatibleAdapter(args.api_base, args.model, temperature=0.0, max_tokens=1024, api_key=args.api_key)
    results = []
    with ThreadPoolExecutor(max_workers=min(args.max_workers, len(items) or 1)) as executor:
        futures = [executor.submit(judge_one, adapter, item) for item in items]
        for future in tqdm(as_completed(futures), total=len(futures), desc="LLM judge"):
            results.append(future.result())

    avg = sum(item["llm_judge"]["overall"] for item in results) / len(results) if results else 0.0
    output = args.output or default_output_path(os.path.join(DEFAULTS.results_dir, "evaluated"), "llm_judge")
    output = resolve_project_path(output)
    ensure_dir(os.path.dirname(output))
    save_json({"input_file": input_path, "n_items": len(results), "avg_llm_judge": avg, "samples": results}, output)
    print(f"Saved LLM judge report to {output}")
    print(f"avg_llm_judge={avg:.4f}")


if __name__ == "__main__":
    main()

