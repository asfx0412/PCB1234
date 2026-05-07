# vqa-pcb.py

import os
import json
import random
import requests
import re
import subprocess
import atexit
import threading
import argparse
import shutil
from PIL import Image
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import traceback
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

import config
import image_process
import prompts_i18n as i18n

# --- Configuration (No changes) ---
API_BASE = config.DEFAULT_CONFIG["API_BASE"]
MODEL_PATH = config.DEFAULT_CONFIG["MODEL_PATH"]
ROOT_DIR = config.DEFAULT_CONFIG["ROOT_DIR"]
TEST_MODE_PERCENTAGE = 0
SPECIFIC_DATASETS_TO_RUN: Optional[List[str]] = None
DATASET_CATEGORIES = config.DATASET_CATEGORIES
QUESTION_TYPES_KEYS = config.QUESTION_TYPES # Renamed to avoid conflict, these are the canonical keys
MAX_LLM_QA_ATTEMPTS = 3
MAX_WORKERS = config.DEFAULT_CONFIG["MAX_WORKERS"]
PRIOR_KNOWLEDGE_FILE = config.DEFAULT_CONFIG["PRIOR_KNOWLEDGE_FILE"]
PROJECT_ROOT = config.PROJECT_ROOT
OUTPUT_BASE_DIR = os.path.join(PROJECT_ROOT, "data", "benchmark", "generated", "generate_vqa_bilingual_test")

def to_project_relative_path(path: str) -> str:
    try:
        return os.path.relpath(path, PROJECT_ROOT)
    except ValueError:
        return path

def stream_vllm_logs(pipe) -> None:
    """Stream vLLM logs so startup failures are visible from this script."""
    if pipe is None:
        return
    for line in iter(pipe.readline, b""):
        try:
            print("[vLLM]", line.decode(errors="replace").rstrip(), flush=True)
        except Exception:
            print("[vLLM]", line, flush=True)

def wait_for_vllm_ready(port: int, timeout: int = 1000, process: Optional[subprocess.Popen] = None) -> bool:
    url = f"http://localhost:{port}/v1/models"
    start_time = time.time()
    print(f"[INFO] Waiting for vLLM server on {url} ...")
    while time.time() - start_time < timeout:
        if process is not None and process.poll() is not None:
            raise RuntimeError(
                f"vLLM server process exited before becoming ready (exit code {process.returncode}). "
                "Check the [vLLM] logs above. If the model is stored locally, pass its local path with "
                "--model_path or set UNIPCB_MODEL_PATH."
            )
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[INFO] vLLM server is ready on port {port}.")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(10)
    raise RuntimeError(f"vLLM server failed to start within {timeout} seconds.")

def start_vllm_server(
    model_path: str,
    port: int = 10029,
    tensor_parallel_size: int = 8,
    pipeline_parallel_size: int = 1,
    limit_mm_per_prompt: str = '{"image": 4}',
    cuda_visible_devices: str = "0,1,2,3,4,5,6,7",
    startup_timeout: int = 1000,
):
    """Start vLLM as a background process and terminate it when this script exits."""
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = cuda_visible_devices

    vllm_executable = os.environ.get("UNIPCB_VLLM_EXECUTABLE")
    if not vllm_executable:
        vllm_executable = shutil.which("vllm")
    if not vllm_executable:
        for candidate in ("/opt/conda/envs/vllm/bin/vllm", "/usr/local/bin/vllm"):
            if os.path.exists(candidate):
                vllm_executable = candidate
                break
    if not vllm_executable:
        raise FileNotFoundError(
            "Could not find the vLLM executable. Set UNIPCB_VLLM_EXECUTABLE to the full path "
            "of your vllm binary, or run this script in an environment where `vllm` is on PATH. "
            "If vLLM is already running, use --no_start_vllm."
        )
    if not os.path.exists(model_path):
        print(
            f"[WARNING] Model path '{model_path}' does not exist locally. vLLM will treat it as a "
            "HuggingFace model id and may try to access the network. For offline runs, pass the "
            "local model directory via --model_path or UNIPCB_MODEL_PATH."
        )

    cmd = [
        vllm_executable, "serve", model_path,
        "--host", "0.0.0.0",
        "--port", str(port),
        "--tensor-parallel-size", str(tensor_parallel_size),
        "--pipeline-parallel-size", str(pipeline_parallel_size),
        "--limit-mm-per-prompt", limit_mm_per_prompt,
    ]

    print(f"[INFO] Starting vLLM server: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    threading.Thread(target=stream_vllm_logs, args=(process.stdout,), daemon=True).start()

    def cleanup() -> None:
        if process.poll() is not None:
            return
        print("[INFO] Shutting down vLLM server...")
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            print("[WARNING] vLLM server did not terminate in time; killing it.")
            process.kill()

    atexit.register(cleanup)
    wait_for_vllm_ready(port=port, timeout=startup_timeout, process=process)
    return process

def parse_args() -> argparse.Namespace:
    default_model_path = MODEL_PATH
    try:
        default_port = urlparse(API_BASE).port or 10029
    except (ValueError, AttributeError):
        default_port = 10029

    parser = argparse.ArgumentParser(
        description="Generate UniPCB benchmark VQA data with an integrated vLLM server."
    )
    parser.add_argument("--model_path", type=str, default=default_model_path, help="Path to the vLLM model.")
    parser.add_argument("--port", type=int, default=default_port, help="Port for the OpenAI-compatible vLLM API.")
    parser.add_argument("--tensor_parallel_size", type=int, default=8, help="vLLM tensor parallel size.")
    parser.add_argument("--pipeline_parallel_size", type=int, default=1, help="vLLM pipeline parallel size.")
    parser.add_argument("--limit_mm_per_prompt", type=str, default='{"image": 4}', help="vLLM --limit-mm-per-prompt value.")
    parser.add_argument("--cuda_visible_devices", type=str, default="0,1,2,3,4,5,6,7", help="CUDA_VISIBLE_DEVICES for vLLM.")
    parser.add_argument("--startup_timeout", type=int, default=1000, help="Seconds to wait for vLLM startup.")
    parser.add_argument("--no_start_vllm", action="store_true", help="Do not start vLLM; use an already running API server.")
    parser.add_argument("--test_mode_percentage", type=float, default=TEST_MODE_PERCENTAGE, help="Percentage of images to process per dataset.")
    parser.add_argument("--max_workers", type=int, default=MAX_WORKERS, help="Thread workers for image processing/API calls.")
    parser.add_argument(
        "--datasets",
        type=str,
        default=None,
        help="Comma-separated dataset names to run. Default runs all configured datasets.",
    )
    return parser.parse_args()

def apply_runtime_args(args: argparse.Namespace) -> None:
    global API_BASE, MODEL_PATH, TEST_MODE_PERCENTAGE, MAX_WORKERS, SPECIFIC_DATASETS_TO_RUN

    MODEL_PATH = args.model_path
    API_BASE = f"http://localhost:{args.port}/v1"
    TEST_MODE_PERCENTAGE = args.test_mode_percentage
    MAX_WORKERS = args.max_workers
    if args.datasets:
        SPECIFIC_DATASETS_TO_RUN = [name.strip() for name in args.datasets.split(",") if name.strip()]

    print(f"[INFO] Using model: {MODEL_PATH}")
    print(f"[INFO] API Base URL: {API_BASE}")
    print(f"[INFO] TEST_MODE_PERCENTAGE: {TEST_MODE_PERCENTAGE}")
    print(f"[INFO] MAX_WORKERS: {MAX_WORKERS}")
    if SPECIFIC_DATASETS_TO_RUN:
        print(f"[INFO] Datasets: {', '.join(SPECIFIC_DATASETS_TO_RUN)}")

def get_prior_knowledge() -> Dict[str, Any]:
    if not os.path.exists(PRIOR_KNOWLEDGE_FILE):
        print(f"Error: Prior knowledge file not found at {PRIOR_KNOWLEDGE_FILE}")
        return {}
    with open(PRIOR_KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_image_filename(filename: str) -> str:
    base, ext = os.path.splitext(filename)
    for prefix in ["labeled_", "bbox_only_"]:
        if base.startswith(prefix):
            base = base[len(prefix):]
    base = re.sub(r"_[a-zA-Z0-9]+\.rf\.[0-9a-zA-Z]{32}_[0-9]+$", "", base)
    return base + ext

def get_localized_class_counts(label_content: List[Dict[str, Any]], is_defect: bool, prior_knowledge_maps: Dict[str, Any], lang: str) -> Counter:
    """Return class counts in the language used by the current sample."""
    counts = Counter()
    if is_defect:
        defect_map_zh = prior_knowledge_maps.get("defect_map_chinese", {})
        for item in label_content:
            class_en = item.get("class")
            if not class_en:
                continue
            class_en = clean_class_name(class_en)
            class_name = defect_map_zh.get(class_en, class_en) if lang == "zh" else class_en
            counts[class_name] += 1
    else:
        component_map_en = prior_knowledge_maps.get("component_map", {})
        component_map_zh = prior_knowledge_maps.get("component_map_type", {})
        for item in label_content:
            class_id = str(item.get("class_id", ""))
            class_en = clean_class_name(item.get("class") or component_map_en.get(class_id))
            if not class_en:
                continue
            class_name = component_map_zh.get(class_en, class_en) if lang == "zh" else class_en
            counts[class_name] += 1
    return counts

def format_class_counts_for_prompt(class_counts: Counter, obj_type_name: str, lang: str) -> str:
    if not class_counts:
        return "无已标注对象。" if lang == "zh" else "No labeled objects."
    if lang == "zh":
        details = "，".join(f"{name}{count}个" for name, count in sorted(class_counts.items()))
        return f"共{sum(class_counts.values())}个{obj_type_name}，其中：{details}。"
    details = ", ".join(f"{name}: {count}" for name, count in sorted(class_counts.items()))
    return f"Total {sum(class_counts.values())} {obj_type_name}s, including: {details}."

def format_expected_class_answer(class_counts: Counter, lang: str) -> str:
    names = sorted(class_counts.keys())
    if not names:
        return "无" if lang == "zh" else "None"
    return "、".join(names) if lang == "zh" else ", ".join(names)

def clean_class_name(name: Any) -> str:
    return image_process.normalize_class_name(name)

def clean_output_text(text: Any) -> str:
    return image_process.clean_generated_text(text)

def bbox_within_dims(label_content: List[Dict[str, Any]], dims_wh: Tuple[int, int]) -> bool:
    img_w, img_h = dims_wh
    if img_w <= 0 or img_h <= 0:
        return False
    for item in label_content:
        bbox = item.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = bbox
        if not (0 <= x1 < x2 <= img_w and 0 <= y1 < y2 <= img_h):
            return False
    return True

def build_structured_fact_block(
    label_content: List[Dict[str, Any]],
    is_defect: bool,
    is_compare: bool,
    prior_knowledge_maps: Dict[str, Any],
    lang: str,
) -> Tuple[str, Counter]:
    """Build strict facts for the LLM. Qwen still writes the QA, but must follow these facts."""
    obj_type_name = i18n.get_text('object_type_names', lang)['defect' if is_defect else 'component']
    class_counts = get_localized_class_counts(label_content, is_defect, prior_knowledge_maps, lang)
    expected_class_answer = format_expected_class_answer(class_counts, lang)
    count_summary = format_class_counts_for_prompt(class_counts, obj_type_name, lang)
    coord_answer = (
        image_process.format_defect_coordinates(
            label_content,
            prior_knowledge_maps.get("defect_map", {}),
            prior_knowledge_maps.get("defect_map_chinese", {}),
            lang,
        )
        if is_defect
        else image_process.format_component_coordinates(
            label_content,
            prior_knowledge_maps.get("component_map_type", {}),
            lang,
        )
    )
    compare_note = ""
    if is_compare:
        compare_note = (
            "所有缺陷事实均对应异常/NG图像，正常/OK图像只能作为对照参考。"
            if lang == "zh"
            else "All defect facts refer to the abnormal/NG image; the normal/OK image is only a comparison reference."
        )

    if lang == "zh":
        fact_block = f"""
【结构化标注事实 - 必须严格遵守】
- 对象类型：{obj_type_name}
- 类别与数量：{count_summary}
- 分类/类型题的答案必须覆盖全部类别，推荐写作：{expected_class_answer}
- 坐标事实：{coord_answer}
- 多类别规则：如果存在多个类别，分类、描述和分析都必须覆盖全部类别，不得只回答其中一种。
- 禁止编造：不得加入未在标注事实中出现的类别、数量或坐标。
{compare_note}
"""
    else:
        fact_block = f"""
[Structured Annotation Facts - Must Follow Strictly]
- Object type: {obj_type_name}
- Classes and counts: {count_summary}
- The classification/type answer must cover every class. Recommended answer: {expected_class_answer}
- Coordinate facts: {coord_answer}
- Multi-class rule: if multiple classes exist, classification, description, and analysis must cover every class, not just one.
- No invention: do not add classes, counts, or coordinates absent from the annotation facts.
{compare_note}
"""
    return fact_block, class_counts

def qa_covers_expected_classes(text: str, class_counts: Counter) -> bool:
    if not class_counts:
        return True
    lowered = text.lower()
    return all(str(name).lower() in lowered for name in class_counts.keys())

def validate_llm_qa_raw(
    qa_raw_json: Dict[str, Any],
    questions_for_llm: List[str],
    class_counts: Counter,
    is_defect: bool,
) -> Tuple[bool, str]:
    """Reject LLM JSON that ignores required keys or collapses multi-class defect answers."""
    bad_questions = {
        "元件描述问题", "缺陷分析问题", "缺陷特征问题", "物体描述问题", "元件分析问题",
        "component description question", "defect analysis question", "defect feature question",
    }
    for q_type in questions_for_llm:
        item = qa_raw_json.get(q_type)
        if not isinstance(item, dict):
            return False, f"missing q_type {q_type}"
        question = item.get("question", "")
        answer = item.get("correct_option", "")
        if not isinstance(question, str) or not question.strip():
            return False, f"empty question for {q_type}"
        if question.strip().lower() in {q.lower() for q in bad_questions}:
            return False, f"placeholder question for {q_type}: {question}"
        if not isinstance(answer, str) or not answer.strip():
            return False, f"empty answer for {q_type}"

    if is_defect and len(class_counts) > 1:
        for q_type in ("defect classification", "defect detail describe", "defect analysis"):
            if q_type in questions_for_llm:
                answer = qa_raw_json.get(q_type, {}).get("correct_option", "")
                if not qa_covers_expected_classes(answer, class_counts):
                    return False, f"{q_type} does not cover all classes: {list(class_counts.keys())}"
    return True, ""

def audit_vqa_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues = []
    question_counter = Counter()
    placeholder_questions = {
        "元件描述问题", "缺陷分析问题", "缺陷特征问题", "物体描述问题", "元件分析问题",
        "component description question", "defect analysis question", "defect feature question",
    }
    bad_text_patterns = [
        "componentscomponents", "defectsdefects", "区域区域", "area area(s)",
        "电阻 元件", "电容 元件", "变压器 元件", "lark of solder", "soilder bridge",
    ]
    count_type_names = {"defect count", "component count", "缺陷计数", "元件计数", "缺陷数量", "元件数量"}

    for record_idx, record in enumerate(records):
        images = record.get("images", [])
        if not isinstance(images, list) or not images:
            issues.append({"record": record_idx, "issue": "missing_images"})
        for image_path in images:
            resolved_image_path = image_path if os.path.isabs(image_path) else os.path.join(PROJECT_ROOT, image_path)
            if os.path.isabs(image_path):
                issues.append({"record": record_idx, "issue": "absolute_image_path", "image": image_path})
            if not os.path.exists(resolved_image_path):
                issues.append({"record": record_idx, "issue": "image_not_found", "image": image_path})

        image_size = record.get("image_size", [])
        img_h = img_w = None
        if isinstance(image_size, list) and len(image_size) == 2:
            img_h, img_w = image_size

        for qa_idx, qa in enumerate(record.get("conversation", [])):
            q = qa.get("question", "")
            a = qa.get("correct_option", "")
            q_type = qa.get("type", "")
            question_counter[q] += 1
            if not q or not a or not q_type:
                issues.append({"record": record_idx, "qa": qa_idx, "issue": "empty_qa_field", "type": q_type})
            if isinstance(q, str) and q.strip().lower() in {x.lower() for x in placeholder_questions}:
                issues.append({"record": record_idx, "qa": qa_idx, "issue": "placeholder_question", "question": q})
            combined = f"{q} {a}"
            for pattern in bad_text_patterns:
                if pattern in combined:
                    issues.append({"record": record_idx, "qa": qa_idx, "issue": "bad_text_pattern", "pattern": pattern})
            options = qa.get("options", [])
            if options:
                option_texts = [re.sub(r"^[A-D]\.\s*", "", str(option)) for option in options]
                if len(option_texts) != len(set(option_texts)):
                    issues.append({"record": record_idx, "qa": qa_idx, "issue": "duplicate_options"})
                if str(a) not in option_texts:
                    issues.append({"record": record_idx, "qa": qa_idx, "issue": "correct_answer_missing_from_options"})
            if "coordinates" in q_type and img_w and img_h:
                nums = [int(n) for n in re.findall(r"-?[0-9]+", str(a))]
                for box_idx in range(0, len(nums), 4):
                    if box_idx + 3 >= len(nums):
                        break
                    x1, y1, x2, y2 = nums[box_idx:box_idx + 4]
                    if not (0 <= x1 < x2 <= img_w and 0 <= y1 < y2 <= img_h):
                        issues.append({
                            "record": record_idx, "qa": qa_idx, "issue": "coordinate_out_of_bounds",
                            "bbox": [x1, y1, x2, y2], "image_size": [img_h, img_w],
                        })
            if q_type in count_type_names or "count" in q_type.lower() or "计数" in q_type or "数量" in q_type:
                for option in qa.get("options", []):
                    option_text = re.sub(r"^[A-D]\.\s*", "", str(option))
                    if not image_process.count_answer_is_consistent(option_text):
                        issues.append({
                            "record": record_idx, "qa": qa_idx, "issue": "count_option_inconsistent",
                            "option": option,
                        })
                    if image_process.count_answer_has_zero_class(option_text):
                        issues.append({
                            "record": record_idx, "qa": qa_idx, "issue": "count_option_zero_class",
                            "option": option,
                        })

    duplicate_questions = [
        {"question": q, "count": count}
        for q, count in question_counter.most_common()
        if count > 1
    ]
    return {
        "total_records": len(records),
        "total_qa": sum(len(record.get("conversation", [])) for record in records),
        "issue_count": len(issues),
        "issues": issues,
        "duplicate_questions": duplicate_questions[:100],
    }

def generate_qa_for_image(
    primary_image_path: str, all_image_paths_dict: Dict[str, Optional[str]], label_content: List[Dict[str, Any]],
    original_dims: Tuple[int, int], resized_dims: Tuple[int, int], dataset_info: Dict[str, Any],
    dataset_config: Dict[str, Any], prior_knowledge_maps: Dict[str, Any], lang: str,
    extracted_resistor_silk_screen: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:

    category_type = dataset_config.get("category_type")
    is_defect = dataset_config.get("is_defect", False)
    # MODIFICATION: Fetch all localizable text at the beginning
    TEXTS = {
        "obj_type_name": i18n.get_text(f'object_type_names.{"defect" if dataset_config["is_defect"] else "component"}', lang),
        "obj_type_generic": i18n.get_text('object_type_names.object', lang),
        "compare_prefix": i18n.get_text('dynamic_questions.compare_prefix', lang),
        "prefix_bbox": i18n.get_text('dynamic_questions.object_prefix_bbox', lang),
        "prefix_default": i18n.get_text('dynamic_questions.object_prefix_default', lang),
        "templates_analysis": i18n.get_text('dynamic_questions.question_templates.analysis', lang),
        "templates_describe": i18n.get_text('dynamic_questions.question_templates.describe', lang),
        "templates_default": i18n.get_text('dynamic_questions.question_templates.default', lang),
        "detection_q_compare": i18n.get_text('dynamic_questions.detection_question_compare', lang),
        "detection_q_standard": i18n.get_text('dynamic_questions.detection_question_standard', lang),
        "has_var": i18n.get_text('has_var', lang),
        "no_var": i18n.get_text('no_var', lang),
    }
    specific_object_prefix = ""
    if category_type == "P3" and label_content:
        unique_class_names = set()
        if is_defect:
            map_to_use = prior_knowledge_maps.get('defect_map_chinese', {})
            for item in label_content:
                class_name_en = clean_class_name(item.get("class"))
                if class_name_en:
                    localized_name = map_to_use.get(class_name_en, class_name_en) if lang == 'zh' else class_name_en
                    unique_class_names.add(localized_name)
        else:  # is_component
            component_map_en = prior_knowledge_maps.get('component_map', {})
            component_map_zh_type = prior_knowledge_maps.get('component_map_type', {})
            for item in label_content:
                class_id = str(item.get("class_id"))
                if class_id in component_map_en:
                    class_name_en = clean_class_name(component_map_en[class_id])
                    localized_name = component_map_zh_type.get(class_name_en, class_name_en) if lang == 'zh' else class_name_en
                    unique_class_names.add(localized_name)

        if unique_class_names:
            if lang == 'zh':
                class_list = '、'.join(sorted(list(unique_class_names)))
                # This creates a specific prefix like: "图中的开路、短路缺陷"
                specific_object_prefix = f"图中的{class_list}{TEXTS['obj_type_name']}"
            else:
                class_list = ', '.join(sorted(list(unique_class_names)))
                plural = "s" if len(unique_class_names) > 1 else ""
                # Creates a prefix like: "the open_circuit, short defects"
                specific_object_prefix = f"the {class_list} {TEXTS['obj_type_name']}{plural}"
    # MODIFICATION FOR P3: Get localized question types and format example
    LOCALIZED_QUESTION_TYPES = i18n.get_text('QUESTION_TYPES', lang)
    QA_FORMAT_EXAMPLE = i18n.get_text('QA_FORMAT_EXAMPLE', lang)
    
    PROGRAMMATIC_Q_TYPES = {
        "defect detection", "defect count", "component count",
        "defect classification", "component type",
        "defect location", "component location", 
        "defect coordinates", "component coordinates"
    }
    LLM_Q_TYPES = {
        "object describe", "defect detail describe", "component describe",
        "defect analysis", "component analysis"
    }
    DIRECT_ANSWER_Q_TYPES = {
        "object describe", "defect analysis", "defect detail describe",
        "component analysis", "component describe",
        "defect coordinates", "component coordinates"
    }

    # category_type = dataset_config.get("category_type")
    # is_defect = dataset_config.get("is_defect", False)
    is_compare = dataset_config.get("is_compare", False)
    is_resistor = dataset_config.get("is_resistor", False)
    is_solder_joint = dataset_config.get("is_solder_joint", False)
    min_resolution_threshold = dataset_config.get("min_resolution_threshold")

    defect_map_en = prior_knowledge_maps.get("defect_map", {})
    defect_map_zh = prior_knowledge_maps.get("defect_map_chinese", {})
    component_map_en = prior_knowledge_maps.get("component_map", {})
    component_map_zh = prior_knowledge_maps.get("component_map_type", {})
    map_for_prompt = (defect_map_zh if is_defect else component_map_zh) if lang == 'zh' else (defect_map_en if is_defect else component_map_en)

    encoded_images_for_llm = []
    if is_compare:
        template_path = all_image_paths_dict.get("TEMPLATE_IMAGE")
        if template_path and os.path.exists(template_path):
            encoded = image_process.encode_image(template_path)
            if encoded: encoded_images_for_llm.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}})
    
    encoded_primary = image_process.encode_image(primary_image_path)
    if not encoded_primary:
        print(f"Error: Failed to encode primary image: {primary_image_path}. Skipping.")
        return None
    encoded_images_for_llm.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_primary}"}})

    for img_type, path in all_image_paths_dict.items():
        if path and path != primary_image_path and img_type != "TEMPLATE_IMAGE" and os.path.exists(path):
             encoded = image_process.encode_image(path)
             if encoded: encoded_images_for_llm.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}})

    obj_type_name = i18n.get_text('object_type_names', lang)['defect' if is_defect else 'component']
    
    object_info_str = ""
    target_object_counts = Counter()
    if label_content:
        # MODIFICATION FOR P3: Use localized intro text
        intro_text = f"The following is a detailed list of identified and labeled {obj_type_name}s...\n"
        if lang == 'zh':
            intro_text = f"以下是已识别并标注的{obj_type_name}的详细列表...\n"
        object_info_str += intro_text

        for i, item in enumerate(label_content):
            item_bbox = item.get("bbox")
            if not item_bbox: continue
            if is_defect:
                item_class_en = clean_class_name(item.get("class", "N/A"))
                item_class_local = defect_map_zh.get(item_class_en, item_class_en) if lang == 'zh' else item_class_en
                target_object_counts[item_class_local] += 1
                object_info_str += f"  - Type: {item_class_local}, BBox: {json.dumps(item_bbox)}\n"
            else:
                item_class_id = str(item.get("class_id", "N/A"))
                item_class_en = clean_class_name(component_map_en.get(item_class_id, "N/A"))
                item_class_local = component_map_zh.get(item_class_en, item_class_en) if lang == 'zh' else item_class_en
                target_object_counts[item_class_local] += 1
                object_info_str += f"  - Component {i+1}: ID {item_class_id} (Name: {item_class_local}), BBox:{json.dumps(item_bbox)}\n"
    else:
        # MODIFICATION FOR P3: Use localized intro text
        no_info_text = f"  No specific {obj_type_name} annotation information provided in the image.\n"
        if lang == 'zh':
            no_info_text = f"  图像中未提供特定的{obj_type_name}标注信息。\n"
        object_info_str = no_info_text

    structured_fact_block, expected_class_counts = build_structured_fact_block(
        label_content=label_content,
        is_defect=is_defect,
        is_compare=dataset_config.get("is_compare", False),
        prior_knowledge_maps=prior_knowledge_maps,
        lang=lang,
    )

    ### MODIFICATION START: Corrected question allocation logic ###
    questions_to_ask_types = []
    if is_defect:
        if category_type == "P1":
            questions_to_ask_types = ["defect detail describe", "defect analysis"]
        elif category_type == "P2":
            questions_to_ask_types = ["defect classification", "defect count", "defect detail describe", "defect analysis"]
        elif category_type == "P3":
            questions_to_ask_types = [
                "object describe", "defect detection", "defect count", 
                "defect location", "defect coordinates", "defect detail describe", 
                "defect analysis"
            ]
    else:  # is_defect = False
        if category_type == "P1":
            questions_to_ask_types = ["component describe", "component analysis"]
        elif category_type == "P2":
            questions_to_ask_types = ["component type", "component count", "component describe", "component analysis"]
        elif category_type == "P3":
            questions_to_ask_types = [
                "object describe", "component count", "component location", 
                "component coordinates", "component describe", "component analysis"
            ]

    skipped_q_types = dataset_config.get("skip_q_types", [])
    if skipped_q_types:
        #original_count = len(questions_to_ask_types)
        questions_to_ask_types = [q for q in questions_to_ask_types if q not in skipped_q_types]
        #if len(questions_to_ask_types) < original_count:
            #print(f"Info: For dataset '{dataset_info['name']}', skipped question types: {skipped_q_types}")

    if not label_content:
        # Define a list of question types that are invalid without labels.
        q_types_requiring_labels = {
            "defect count", "component count",
            "defect location", "component location",
            "defect coordinates", "component coordinates",
            "defect classification", # Cannot classify a non-existent defect
            "component type"         # Cannot determine the type of a non-existent component
        }
        
        # Filter the list of questions to ask, removing those that require labels
        questions_to_ask_types = [q for q in questions_to_ask_types if q not in q_types_requiring_labels]

    questions_for_llm = [q for q in questions_to_ask_types if q in LLM_Q_TYPES]
    qa_raw_json = {}
    if questions_for_llm:
        use_labeled_object_prompt = category_type in ["P1", "P2"]
        # MODIFICATION FOR P3: Use localized question type names in prompt
        questions_list_prompt_str = "".join([f"- {LOCALIZED_QUESTION_TYPES.get(q, q)}\n" for q in questions_for_llm])
        location_prompt_text = i18n.get_text('LOCATION_PROMPT' if is_defect else 'COMPONENT_LOCATION_PROMPT', lang)
        describe_prompt_text = image_process.generate_defect_des(dataset_info, lang) if is_defect else image_process.generate_component_des(dataset_info, lang)
        additional_context_str = (
            f"{structured_fact_block}\n"
            f"[{'Identified ' + obj_type_name + ' Information' if lang == 'en' else '已识别的' + obj_type_name + '信息'}]\n{object_info_str}\n"
            f"[{obj_type_name + ' Location Description Guide' if lang == 'en' else obj_type_name + '位置描述指南'}]\n{location_prompt_text}\n"
            f"[{obj_type_name + ' Naming Convention' if lang == 'en' else obj_type_name + '命名规范'}]\n{describe_prompt_text}\n"
        )
        specific_rules_str = ""
        if category_type == "P1" and not is_defect: specific_rules_str += i18n.get_text('P1_COMPONENT_ANALYSIS_PROMPT', lang)
        if category_type == "P3": specific_rules_str += i18n.get_text('P3_OBJECT_DESCRIBE_PROMPT', lang)
        if is_resistor and extracted_resistor_silk_screen:
            res_val = image_process.calculate_resistor_value(extracted_resistor_silk_screen)
            if res_val: 
                specific_rules_str += i18n.get_text('RESISTOR_HINT_PROMPT', lang).format(
                            silkscreen_code=extracted_resistor_silk_screen, 
                            resistor_value_hint=res_val[0]
                        )
        if is_solder_joint: specific_rules_str += i18n.get_text('SOLDER_JOINT_HINT_PROMPT', lang)
        if category_type == "P2": specific_rules_str += i18n.get_text('P2_DEFECT_BBOX_PROMPT' if is_defect else 'P2_COMPONENT_BBOX_PROMPT', lang)
        if label_content: specific_rules_str += i18n.get_text('LABELED_OBJECT_PROMPT', lang).format(object_type_name=obj_type_name)
        if len(expected_class_counts) > 1:
            if lang == 'zh':
                specific_rules_str += (
                    "\n【多类别强制要求】\n"
                    f"本样本包含多个类别：{format_expected_class_answer(expected_class_counts, lang)}。\n"
                    "你生成的分类、描述和分析答案必须覆盖上述全部类别；如果只覆盖其中一类，本次输出视为错误。\n"
                )
            else:
                specific_rules_str += (
                    "\n[Mandatory Multi-Class Requirement]\n"
                    f"This sample contains multiple classes: {format_expected_class_answer(expected_class_counts, lang)}.\n"
                    "Classification, description, and analysis answers must cover every listed class. If only one class is covered, the output is invalid.\n"
                )
        if not is_defect:
            comp_des_info = image_process.generate_component_des(dataset_info, lang)
            if comp_des_info: specific_rules_str += i18n.get_text('COMPONENT_SUBTYPE_HINT_PROMPT', lang).format(component_describe_info=comp_des_info)
        specific_rules_str += i18n.get_text('ANALYSIS_AND_DESCRIBE_RULES_PROMPT', lang)
        
        map_instruction = i18n.get_text('map_instruction_format', lang).format(map_json=json.dumps(map_for_prompt, ensure_ascii=False))
        prompt_template = i18n.get_text('COMPARE_PROMPT_HEADER' if is_compare else 'LLM_PROMPT_HEADER', lang)
        intro_prompts = i18n.get_text('llm_intro_prompts' if is_defect else 'no_defect_llm_intro_prompts', lang)
        final_prompt = prompt_template.format(
            random_prompt_intro=random.choice(intro_prompts), task_focus=f"Analyze the {obj_type_name}s in the image." if lang == 'en' else f"分析图像中的{obj_type_name}。",
            dataset_description=dataset_info.get("description", "N/A"), original_width=original_dims[0], original_height=original_dims[1],
            resized_width=resized_dims[0], resized_height=resized_dims[1], additional_context=additional_context_str,
            questions_list_prompt=questions_list_prompt_str, qa_format_example=QA_FORMAT_EXAMPLE, map_instruction=map_instruction,
            specific_rules=specific_rules_str, defect_info_str=object_info_str, location_prompt=location_prompt_text
        )

        llm_payload = {"model": MODEL_PATH, "messages": [{"role": "user", "content": encoded_images_for_llm + [{"type": "text", "text": final_prompt}]}], "temperature": 0.8, "max_tokens": 10240}
        
        accepted_llm_json = False
        for attempt in range(MAX_LLM_QA_ATTEMPTS):
            try:
                response = requests.post(f"{API_BASE}/chat/completions", json=llm_payload, timeout=180)
                response.raise_for_status()
                content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    qa_raw_json = image_process.extract_json_from_response(content) or {}
                    is_valid, validation_reason = validate_llm_qa_raw(
                        qa_raw_json,
                        questions_for_llm,
                        expected_class_counts,
                        is_defect,
                    )
                    if is_valid:
                        accepted_llm_json = True
                        break
                    print(f"LLM QA validation failed (Attempt {attempt+1}): {validation_reason}")
            except requests.exceptions.RequestException as e:
                print(f"API request failed (Attempt {attempt+1}): {e}")
                if attempt < MAX_LLM_QA_ATTEMPTS - 1: time.sleep(1)

            # 如果不是最后一次尝试，则等待后重试
            if attempt < MAX_LLM_QA_ATTEMPTS - 1:
                # 指数退避策略：等待时间 progressively longer (1s, 2s, 4s, ...)
                wait_time = 10 ** attempt 
                print(f"Waiting for {wait_time} seconds before retrying...")
                time.sleep(wait_time)

        if not accepted_llm_json:
            print(f"Error: Failed to obtain valid LLM QA for {primary_image_path}. Skipping this image.")
            return None

    if not questions_to_ask_types:
        return None

    all_conversation_pairs = []
    
    for q_type in questions_to_ask_types:
        question_text = ""
        final_correct_option = ""
        
        # --- Part 1: Generate Question and Answer ---
        # A. Handle Programmatically Generated Q&A
        if q_type in PROGRAMMATIC_Q_TYPES:
            if q_type == "defect detection":
                question_text = i18n.get_text('dynamic_questions.detection_question_compare' if is_compare else 'dynamic_questions.detection_question_standard', lang)
                # Answer is determined later in the options section
                final_correct_option = "TBD" 
            
            elif q_type.endswith("count"):
                maps = prior_knowledge_maps
                question_text = image_process.generate_dynamic_count_question(label_content, is_defect, maps, lang)
                
                # Programmatically generate the count answer
                if is_defect:
                    counts = Counter(clean_class_name(item.get("class")) for item in label_content if item.get("class"))
                    map_en = maps.get("defect_map", {})
                    map_zh = maps.get("defect_map_chinese", {})
                    local_map = map_zh if lang == 'zh' else map_en
                    total_count = len(label_content)
                    if not label_content:
                        final_correct_option = i18n.get_text('dynamic_questions.no_defects_detected', lang).format(obj_type=TEXTS["obj_type_name"])
                    else:
                        detail_parts = [f"{local_map.get(k, k)}{v}个" if lang == 'zh' else f"{k} {v}" for k, v in counts.items()]
                        details = "，".join(detail_parts) if lang == 'zh' else ", ".join(detail_parts)
                        final_correct_option = (f"总共{total_count}个{TEXTS['obj_type_name']}，其中：{details}。" if lang == 'zh' 
                                                else f"Total {total_count} {TEXTS['obj_type_name']}s, including: {details}.")
                else: # Component count
                    component_map_zh = prior_knowledge_maps.get("component_map_type", {})
                    
                    # 这里的 counts 的键(key)是英文名，如 'Diode'
                    counts = Counter(clean_class_name(item.get("class")) for item in label_content if item.get("class"))
                    total_count = len(label_content)
                    
                    if not label_content:
                        final_correct_option = f"图中未检测到任何{TEXTS['obj_type_name']}。" if lang == 'zh' else f"No {TEXTS['obj_type_name']}s were detected in the image."
                    else:
                        if lang == 'zh':
                            # 在生成中文描述时，使用 component_map_zh 翻译英文键 (k)
                            # .get(k, k) 是一个安全写法，如果找不到翻译，则使用原始英文名
                            detail_parts = [f"{component_map_zh.get(k, k)}{v}个" for k, v in counts.items()]
                        else:
                            # 英文版本保持不变
                            detail_parts = [f"{k} {v}" for k, v in counts.items()]
                        
                        details = "，".join(detail_parts) if lang == 'zh' else ", ".join(detail_parts)
                        final_correct_option = (f"总共{total_count}个{TEXTS['obj_type_name']}，其中：{details}。" if lang == 'zh'
                                                else f"Total {total_count} {TEXTS['obj_type_name']}s, including: {details}.")

            elif q_type == "component type":
                maps = prior_knowledge_maps
                question_text = (
                    "边界框内的目标元件类型是什么？"
                    if lang == 'zh'
                    else "What component type is marked by the bounding box?"
                )
                class_counts = get_localized_class_counts(label_content, False, maps, lang)
                final_correct_option = format_expected_class_answer(class_counts, lang)

            elif q_type == "defect classification":
                maps = prior_knowledge_maps
                question_text = (
                    "图中标注的缺陷属于哪些类型？"
                    if lang == 'zh'
                    else "Which defect types are annotated in the image?"
                )
                class_counts = get_localized_class_counts(label_content, True, maps, lang)
                final_correct_option = format_expected_class_answer(class_counts, lang)
                        
            elif q_type.endswith("location"):
                 maps = prior_knowledge_maps
                 question_text = image_process.generate_dynamic_location_question(label_content, original_dims, is_defect, is_compare, False, maps, lang)
                 if is_defect:
                     final_correct_option = image_process.format_defect_positions(label_content, original_dims, maps.get("defect_map",{}), maps.get("defect_map_chinese",{}), lang)
                 else:
                     final_correct_option = image_process.format_component_positions(label_content, original_dims, lang)

            elif q_type.endswith("coordinates"):
                maps = prior_knowledge_maps
                question_text = image_process.generate_dynamic_coordinate_question(label_content, is_defect, is_compare, maps, lang)
                if is_defect:
                    final_correct_option = image_process.format_defect_coordinates(label_content, maps.get("defect_map",{}), maps.get("defect_map_chinese",{}), lang)
                else:
                    final_correct_option = image_process.format_component_coordinates(
                        label_content, 
                        maps.get("component_map_type", {}), # 传入英文->中文的映射表
                        lang  # 传入语言参数
                    )

            # B. Handle LLM-Generated Q&A
        else: # q_type is in LLM_Q_TYPES
            qa_item_llm = qa_raw_json.get(q_type, {})
            question_from_llm = qa_item_llm.get("question", "")
            final_correct_option = qa_item_llm.get("correct_option", "")

            if not question_from_llm or not final_correct_option:
                print(f"Warning: LLM did not provide content for q_type '{q_type}'. Skipping.")
                continue

            question_text = question_from_llm.strip()

        # Common post-processing for all question types
        if is_compare and q_type not in LLM_Q_TYPES and q_type != "defect detection" and question_text and q_type != "defect location":
            question_text = TEXTS["compare_prefix"] + question_text

        question_text = clean_output_text(question_text)
        final_correct_option = clean_output_text(final_correct_option)

        if not question_text or not final_correct_option: 
            print(f"Warning: Skipping q_type '{q_type}' after processing due to empty question or answer.")
            continue
        
        # --- Part 2: Generate Options for MCQs ---
        cleaned_correct_option = image_process.clean_text_for_json(final_correct_option)
        current_options, current_answer_letter = [], ""
        
        if q_type not in DIRECT_ANSWER_Q_TYPES:
            all_options = []
            
            # Case 1: Defect detection (binary Yes/No)
            if q_type == "defect detection":
                is_defective_ground_truth = bool(label_content)
                correct_text = random.choice(TEXTS['has_var']) if is_defective_ground_truth else random.choice(TEXTS['no_var'])
                distractor_text = random.choice(TEXTS['no_var']) if is_defective_ground_truth else random.choice(TEXTS['has_var'])
                cleaned_correct_option = correct_text # Override TBD
                all_options = [cleaned_correct_option, distractor_text]
            
            # Case 2: Other MCQ types
            else:
                distractors = []
                # Attempt programmatic distractors first for relevant types
                if q_type.endswith("count"):
                    all_possible_types = []
                    if is_defect:
                        map_for_types = prior_knowledge_maps.get("defect_map_chinese", {}) if lang == 'zh' else prior_knowledge_maps.get("defect_map", {})
                        all_possible_types = list(map_for_types.values())
                    else: # Component
                        map_for_types = prior_knowledge_maps.get("component_map_type", {}) if lang == 'zh' else prior_knowledge_maps.get("component_map", {})
                        all_possible_types = list(map_for_types.values())

                    # 调用新的、更智能的函数
                    distractors.extend(image_process.generate_smarter_count_distractors(
                        cleaned_correct_option, 
                        all_possible_types,
                        lang,
                        is_defect
                    ))
                    
                elif q_type.endswith("location"):
                    distractors.extend(image_process.generate_programmatic_location_distractors(
                        cleaned_correct_option,
                        lang
                    ))

                elif q_type == "defect classification":
                    distractors.extend(image_process.generate_programmatic_classification_distractors(
                        cleaned_correct_option,
                        prior_knowledge_maps['defect_map'],
                        prior_knowledge_maps['defect_map_chinese'],
                        lang,
                    ))

                elif q_type == "component type":
                    map_for_types = prior_knowledge_maps.get("component_map_type", {}) if lang == 'zh' else prior_knowledge_maps.get("component_map", {})
                    generic_component_types = (
                        ["电阻", "电容", "电感", "IC芯片", "二极管", "三极管", "连接器", "变压器", "开关", "焊盘", "测试点"]
                        if lang == 'zh'
                        else ["Resistor", "Capacitor", "Inductor", "IC/Chip", "Diode", "Transistor", "Connector", "Transformer", "Switch", "Pad", "Test Point"]
                    )
                    distractors.extend(image_process.generate_programmatic_type_distractors(
                        cleaned_correct_option,
                        list(map_for_types.values()),
                        lang,
                        fallback_types=generic_component_types,
                        none_label="无标注元件" if lang == 'zh' else "No annotated components",
                    ))
                
                # If programmatic distractors are not enough or not applicable, use API
                hard_fact_mcq_types = {"defect count", "component count", "defect classification", "component type"}
                if len(distractors) < 3 and q_type not in hard_fact_mcq_types:
                    if q_type.endswith("count"):
                        simple_distractors = []
                    else:
                        simple_distractors = image_process.generate_simple_count_distractors(cleaned_correct_option)
                    distractors.extend(d for d in simple_distractors if d not in distractors)

                if len(distractors) < 3 and q_type not in hard_fact_mcq_types:
                    api_distractors = image_process.get_distractors_from_api(
                        image_process.create_distractor_prompt(q_type, question_text, cleaned_correct_option, lang, dataset_config.get("is_solder_joint", False)),
                        config.MAX_MCQ_GENERATION_RETRIES, cleaned_correct_option
                    )
                    distractors.extend(d for d in api_distractors if d not in distractors) # Add new ones

                if q_type.endswith("count"):
                    distractors = [
                        d for d in distractors
                        if image_process.count_answer_is_valid_option(d)
                    ]

                if not distractors:
                    print(f"Warning: Failed to get any distractors for '{q_type}'. Converting to open-ended.")
                else:
                    all_options = [cleaned_correct_option] + list(dict.fromkeys(distractors))[:3]

            # Finalize MCQ options
            if all_options:
                random.shuffle(all_options)
                try:
                    answer_idx = all_options.index(cleaned_correct_option)
                    current_answer_letter = chr(ord('A') + answer_idx)
                    current_options = [f"{chr(ord('A') + i)}. {opt}" for i, opt in enumerate(all_options)]
                except ValueError:
                    print(f"CRITICAL Error: Correct option '{cleaned_correct_option}' not found in options {all_options} for {q_type}.")
                    current_options = [] # Make it open-ended as a fallback

        # --- Part 3: Assemble Final QA Entry ---
        qa_entry = {"question": question_text, "correct_option": cleaned_correct_option, "type": LOCALIZED_QUESTION_TYPES.get(q_type, q_type)}
        if current_options:
            qa_entry["options"] = current_options
            qa_entry["correct_answer_letter"] = current_answer_letter
        
        all_conversation_pairs.append(qa_entry)

        
    if all_conversation_pairs:
        final_images_for_vqa = []
        rep_img_type = dataset_config.get("primary_image_type", config.DATASET_CATEGORIES[category_type]["primary_image_type"])
        rep_img_path = all_image_paths_dict.get(rep_img_type, all_image_paths_dict.get("IMAGE_DIR"))
        if is_compare:
            template_path = all_image_paths_dict.get("TEMPLATE_IMAGE")
            if template_path and os.path.exists(template_path): final_images_for_vqa.append(template_path)
        if rep_img_path and os.path.exists(rep_img_path): final_images_for_vqa.append(rep_img_path)
        
        deduped_images = [to_project_relative_path(path) for path in dict.fromkeys(final_images_for_vqa)]
        return [{"conversation": all_conversation_pairs, "images": deduped_images, "image_size": [original_dims[1], original_dims[0]],
                 "dataset": dataset_info.get("name", "Unknown"), "dataset_type": category_type, "language": lang}]
    return None

# ... (rest of the file remains unchanged)
def process_image_universal(image_file: str, dirs: Dict[str, str], dataset_name: str, dataset_config: Dict[str, Any], prior_knowledge: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    lang = random.choice(['zh', 'en'])
    is_defect = dataset_config["is_defect"]
    is_resistor = dataset_config.get("is_resistor", False)

    dataset_info = {"name": dataset_name, **prior_knowledge.get(dataset_name, {})}
    base_image_name = clean_image_filename(image_file)
    base_filename_no_ext = os.path.splitext(base_image_name)[0]
    
    extracted_resistor_silk_screen = None
    if is_resistor:
        match = re.search(r"R([0-9R]+?)(?:_|$|\.)", image_file)
        if match:
            extracted_resistor_silk_screen = match.group(1)
        else:
            extracted_resistor_silk_screen = base_filename_no_ext

    all_image_paths = {key: os.path.join(path, base_image_name) for key, path in dirs.items() if path}
    primary_image_path = all_image_paths.get(dataset_config["primary_image_type"])
    
    if not primary_image_path or not os.path.exists(primary_image_path):
        primary_image_path = all_image_paths.get("IMAGE_DIR")
        if not primary_image_path or not os.path.exists(primary_image_path):
            print(f"Error: Primary image for type '{dataset_config['primary_image_type']}' not found. Skipping.")
            return None
    
    orig_img_path = all_image_paths.get("IMAGE_DIR")
    if not orig_img_path or not os.path.exists(orig_img_path):
        print(f"Error: Original image not found for {image_file}. Cannot get dimensions. Skipping.")
        return None
        
    try:
        with Image.open(orig_img_path) as img:
            orig_w, orig_h = img.size
        resized_w, resized_h = orig_w, orig_h
    except Exception as e:
        print(f"Error opening image {image_file}: {e}. Skipping.")
        return None
        
    label_path = os.path.join(dirs["LABEL_DIR"], base_filename_no_ext + ".txt")
    label_content = []
    prior_knowledge_maps = {}
    
    if is_defect:
        defect_map_en, defect_map_zh = image_process.get_defect_map(dataset_name, prior_knowledge)
        if not defect_map_en: 
            print(f"Error: Missing defect map for {dataset_name}. Skipping.")
            return None
        prior_knowledge_maps = {"defect_map": defect_map_en, "defect_map_chinese": defect_map_zh}
        if os.path.exists(label_path):
            label_content, _ = image_process.get_label_content(label_path, orig_w, orig_h, defect_map_en)
    else:
        comp_map_en, comp_map_zh, comp_describe = image_process.get_component_map(dataset_name, prior_knowledge)
        if not comp_map_en: 
            print(f"Error: Missing component map for {dataset_name}. Skipping.")
            return None
        prior_knowledge_maps = {"component_map": comp_map_en, "component_map_type": comp_map_zh, "component_describe": comp_describe}
        if os.path.exists(label_path):
            label_content, _ = image_process.get_component_label_content(label_path, orig_w, orig_h, comp_map_en)

    if label_content and not bbox_within_dims(label_content, (orig_w, orig_h)):
        print(f"Error: Label coordinates are outside image bounds for {image_file}. Skipping.")
        return None

    try:
        return generate_qa_for_image(
            primary_image_path=primary_image_path, all_image_paths_dict=all_image_paths, label_content=label_content,
            original_dims=(orig_w, orig_h), resized_dims=(resized_w, resized_h), dataset_info=dataset_info,
            dataset_config=dataset_config, prior_knowledge_maps=prior_knowledge_maps, lang=lang,
            extracted_resistor_silk_screen=extracted_resistor_silk_screen
        )
    except Exception as e:
        print(f"Critical error during VQA generation for {image_file}: {e}")
        traceback.print_exc()
        return None

def main():
    print("Starting VQA dataset processing with BILINGUAL support...")
    prior_knowledge = get_prior_knowledge()
    if not prior_knowledge: return
    
    all_vqa_data = []
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    total_start_time = time.time()
    
    datasets_to_run = []
    for category_name, category_info in DATASET_CATEGORIES.items():
        for dataset_name in category_info["datasets"]:
            if not SPECIFIC_DATASETS_TO_RUN or dataset_name in SPECIFIC_DATASETS_TO_RUN:
                current_config = category_info["datasets"][dataset_name].copy()
                current_config["category_type"] = category_name
                current_config["primary_image_type"] = current_config.get("primary_image_type", category_info.get("primary_image_type", "IMAGE_DIR"))
                datasets_to_run.append((dataset_name, current_config))

    for dataset_name, current_dataset_config in datasets_to_run:
        print(f"\n--- Processing Dataset: {dataset_name} ({current_dataset_config['category_type']}) ---")
        dirs = image_process.get_dataset_directories(dataset_name)
        primary_dir = dirs.get(current_dataset_config['primary_image_type'])
        if not primary_dir or not os.path.exists(primary_dir):
            print(f"Error: Primary directory {primary_dir} not found for {dataset_name}. Skipping.")
            continue
        
        image_files = [f for f in os.listdir(primary_dir) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
        if not image_files:
            print(f"No images found for dataset {dataset_name} in {primary_dir}. Skipping.")
            continue
            
        if TEST_MODE_PERCENTAGE and 0 < TEST_MODE_PERCENTAGE <= 100:
            num_to_process = max(1, int(len(image_files) * TEST_MODE_PERCENTAGE / 100))
            image_files = image_files[:num_to_process]
            print(f"TEST MODE: Processing {num_to_process} of {len(image_files)} images.")
            
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(process_image_universal, img_file, dirs, dataset_name, current_dataset_config, prior_knowledge): img_file for img_file in image_files}
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"Processing {dataset_name}"):
                image_filename = futures[future]
                try:
                    result = future.result()
                    if result: all_vqa_data.extend(result)
                except Exception as e:
                    print(f"Error processing future for image {image_filename}: {e}")
                    traceback.print_exc()

    total_elapsed_time = time.time() - total_start_time
    timestamp = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"
    consolidated_path = os.path.join(OUTPUT_BASE_DIR, f"all_vqa_data_bilingual_{timestamp}.json")
    with open(consolidated_path, "w", encoding="utf-8") as f:
        json.dump(all_vqa_data, f, ensure_ascii=False, indent=2)
    audit_report = audit_vqa_records(all_vqa_data)
    audit_path = os.path.join(OUTPUT_BASE_DIR, f"audit_{timestamp}.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, ensure_ascii=False, indent=2)
    print(f"\nSaved consolidated VQA data ({len(all_vqa_data)} items) to {consolidated_path}")
    print(f"Saved audit report ({audit_report['issue_count']} issues) to {audit_path}")
    print(f"Total processing time: {total_elapsed_time:.2f} seconds.")
    print("\nAll datasets processing completed!")

if __name__ == "__main__":
    args = parse_args()
    apply_runtime_args(args)

    if args.no_start_vllm:
        wait_for_vllm_ready(port=args.port, timeout=args.startup_timeout)
    else:
        start_vllm_server(
            model_path=args.model_path,
            port=args.port,
            tensor_parallel_size=args.tensor_parallel_size,
            pipeline_parallel_size=args.pipeline_parallel_size,
            limit_mm_per_prompt=args.limit_mm_per_prompt,
            cuda_visible_devices=args.cuda_visible_devices,
            startup_timeout=args.startup_timeout,
        )

    main()
    print("\n[INFO] Benchmark generation finished.")
