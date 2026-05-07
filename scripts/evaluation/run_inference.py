"""Run model inference on a UniPCB benchmark JSON file."""

from __future__ import annotations

import argparse
import copy
import os
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

from tqdm import tqdm

CURRENT_DIR = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from evaluation.adapters.openai_compatible import OpenAICompatibleAdapter
from evaluation.config import DEFAULTS
from evaluation.utils.image import encode_image_base64
from evaluation.utils.io import load_json, save_json
from evaluation.utils.paths import default_output_path, ensure_dir, resolve_project_path


def build_instruction(language: str, q_type: str, has_options: bool) -> str:
    is_zh = str(language or "").lower().startswith("zh")
    q_type_lower = str(q_type or "").lower()
    if is_zh:
        base = "请仔细阅读问题并回答。最终回复必须只包含：<think>...</think><answer>...</answer>。"
        if has_options:
            return base + " <answer> 内只能输出 A/B/C/D 单个字母。"
        if "coord" in q_type_lower or "bbox" in q_type_lower:
            return base + " <answer> 内仅输出严格 JSON 坐标，不要输出自然语言或代码块。"
        return base + " <answer> 内只输出最终答案。"

    base = "Read the question carefully and answer. The final reply must contain only: <think>...</think><answer>...</answer>."
    if has_options:
        return base + " Inside <answer>, output only one letter A/B/C/D."
    if "coord" in q_type_lower or "bbox" in q_type_lower:
        return base + " Inside <answer>, output strict JSON coordinates only, with no natural language or code fences."
    return base + " Inside <answer>, write only the final answer."


def format_prompt(question: str, options: Optional[List[str]], q_type: str, language: str) -> str:
    has_options = bool(options)
    if has_options:
        option_block = "\n".join(options or [])
        if str(language or "").lower().startswith("zh"):
            body = f"{question}\n\n选项：\n{option_block}"
        else:
            body = f"{question}\n\nOptions:\n{option_block}"
    else:
        body = str(question or "")
    return f"{body.strip()}\n\n{build_instruction(language, q_type, has_options)}"


def image_message(path: str) -> Optional[Dict[str, object]]:
    encoded = encode_image_base64(path)
    if not encoded:
        return None
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
    }


def process_sample(sample: dict, adapter: OpenAICompatibleAdapter) -> Optional[dict]:
    result = copy.deepcopy(sample)
    image_paths = [resolve_project_path(p) for p in result.get("images", []) if isinstance(p, str)]
    image_messages = [msg for path in image_paths if (msg := image_message(path))]
    if result.get("images") and not image_messages:
        return None

    history: List[Dict[str, object]] = []
    language = result.get("language", "en")
    for turn_idx, item in enumerate(result.get("conversation", [])):
        question = item.get("question", "")
        q_type = item.get("type", "")
        options = item.get("options")
        prompt = format_prompt(question, options if isinstance(options, list) else None, q_type, language)

        content: List[Dict[str, object]] = []
        if turn_idx == 0:
            content.extend(image_messages)
        content.append({"type": "text", "text": prompt})

        history.append({"role": "user", "content": content})
        try:
            response = adapter.generate(history)
        except Exception as exc:
            response = f"API Request Error: {exc}"
        history.append({"role": "assistant", "content": response})
        item["model_response"] = response
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run UniPCB benchmark inference.")
    parser.add_argument("--input", default=DEFAULTS.benchmark_json, help="Benchmark JSON file.")
    parser.add_argument("--output", default=None, help="Prediction JSON output path.")
    parser.add_argument("--api_base", default=DEFAULTS.api_base, help="OpenAI-compatible API base URL.")
    parser.add_argument("--model", default=DEFAULTS.model, help="Model name or path served by the API.")
    parser.add_argument("--api_key", default=os.environ.get("UNIPCB_API_KEY"), help="Optional API key.")
    parser.add_argument("--max_workers", type=int, default=DEFAULTS.max_workers)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max_tokens", type=int, default=8192)
    parser.add_argument("--limit", type=int, default=0, help="Optional maximum number of samples.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = resolve_project_path(args.input)
    data = load_json(input_path)
    if isinstance(data, dict):
        data = [data]
    if args.limit and args.limit > 0:
        data = data[: args.limit]

    output = args.output or default_output_path(
        os.path.join(DEFAULTS.results_dir, "raw_predictions"),
        "predictions",
    )
    output = resolve_project_path(output)
    ensure_dir(os.path.dirname(output))

    adapter = OpenAICompatibleAdapter(
        api_base=args.api_base,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        api_key=args.api_key,
    )

    results = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_idx = {executor.submit(process_sample, sample, adapter): idx for idx, sample in enumerate(data)}
        for future in tqdm(as_completed(future_to_idx), total=len(future_to_idx), desc="Inference"):
            try:
                item = future.result()
                if item:
                    results.append(item)
            except Exception:
                idx = future_to_idx[future]
                print(f"Error processing sample {idx}", file=sys.stderr)
                traceback.print_exc()

    save_json(results, output)
    print(f"Saved predictions to {output}")


if __name__ == "__main__":
    main()
