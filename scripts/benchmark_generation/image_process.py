# image_process.py

import os
from PIL import Image
import math
import base64
import json
import random
import requests
import time
import re
from typing import List, Dict, Any, Optional, Tuple
import collections
from collections import OrderedDict

import config   
import prompts_i18n as i18n

MODEL_PATH = config.DEFAULT_CONFIG["MODEL_PATH"]
API_BASE = config.DEFAULT_CONFIG["API_BASE"]
ROOT_DIR = config.DEFAULT_CONFIG["ROOT_DIR"]

# ... (smart_resize 和其他未修改的函数保持不变) ...

CLASS_NAME_FIXES = {
    "lark of solder": "lack of solder",
    "soilder bridge": "solder bridge",
}

TEXT_FIXES = {
    "Capacitorcomponents": "Capacitor components",
    "Resistorcomponents": "Resistor components",
    "Transistorcomponents": "Transistor components",
    "Diodecomponents": "Diode components",
    "Transformercomponents": "Transformer components",
    "defectsdefects": "defects",
    "componentscomponents": "components",
    "area area(s)": "area",
    "center area area": "center area",
    "中心区域区域": "中心区域",
    "电阻 元件": "电阻元件",
    "电容 元件": "电容元件",
    "变压器 元件": "变压器元件",
}

def normalize_class_name(name: Any) -> str:
    if name is None:
        return ""
    text = re.sub(r"\s+", " ", str(name)).strip()
    fixed = CLASS_NAME_FIXES.get(text.lower())
    return fixed if fixed else text

def normalize_name_map(mapping: Dict[str, str]) -> Dict[str, str]:
    return {str(k).strip(): normalize_class_name(v) for k, v in (mapping or {}).items()}

def normalize_translation_map(mapping: Dict[str, str]) -> Dict[str, str]:
    normalized = {}
    for key, value in (mapping or {}).items():
        normalized[normalize_class_name(key)] = normalize_class_name(value)
    return normalized

def clean_generated_text(text: Any) -> str:
    if not isinstance(text, str):
        return str(text)
    cleaned = clean_text_for_json(text)
    for bad, good in TEXT_FIXES.items():
        cleaned = cleaned.replace(bad, good)
    cleaned = re.sub(r"\b([A-Za-z][A-Za-z ]+?)(defects|components)\b", r"\1 \2", cleaned)
    cleaned = re.sub(r"\s+([。！？；，,.?;:])", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def smart_resize(height: int, width: int, factor: Optional[int] = None, min_pixels: Optional[int] = None, max_pixels: Optional[int] = None) -> tuple[int, int]:
    if factor is None: factor = config.DEFAULT_CONFIG["IMAGE_FACTOR"]
    if min_pixels is None: min_pixels = config.DEFAULT_CONFIG["MIN_PIXELS"]
    if max_pixels is None: max_pixels = config.DEFAULT_CONFIG["MAX_PIXELS"]
    max_ratio = config.DEFAULT_CONFIG["MAX_RATIO"]
    if width > 0 and height > 0 and max(height, width) / min(height, width) > max_ratio:
        raise ValueError(f"absolute aspect ratio must be smaller than {max_ratio}, got {max(height, width) / min(height, width)}")
    current_pixels = height * width
    if min_pixels <= current_pixels <= max_pixels and height % factor == 0 and width % factor == 0:
        return height, width
    h_bar = max(factor, round(height / factor) * factor) if height > 0 else 0
    w_bar = max(factor, round(width / factor) * factor) if width > 0 else 0
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = math.floor(height / beta / factor) * factor
        w_bar = math.floor(width / beta / factor) * factor
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width)) if height * width > 0 else 1
        h_bar = math.ceil(height * beta / factor) * factor
        w_bar = math.ceil(width * beta / factor) * factor
    return h_bar, w_bar

def resize_and_save_image(image_path: str, target_height: int, target_width: int) -> bool:
    if not os.path.exists(image_path): return False
    try:
        with Image.open(image_path) as img:
            if img.size == (target_width, target_height): return False
            img_resized = img.resize((target_width, target_height), Image.LANCZOS)
            img_resized.save(image_path)
            return True
    except Exception as e:
        print(f"Error resizing image {image_path}: {e}")
        raise

def get_label_content(label_path: str, img_width: int, img_height: int, defect_map: Dict[str, str]) -> Tuple[List[Dict[str, Any]], Tuple[int, int]]:
    defects = []
    if img_width <= 0 or img_height <= 0: return defects, (img_width, img_height)
    seen_defects = set()
    if os.path.exists(label_path):
        with open(label_path, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 5:
                    try:
                        class_id_str, p1_str, p2_str, p3_str, p4_str = parts
                        class_name = normalize_class_name(defect_map.get(class_id_str, f"Unknown_{class_id_str}"))
                        p1, p2, p3, p4 = float(p1_str), float(p2_str), float(p3_str), float(p4_str)
                        is_normalized = max(p1, p2, p3, p4) <= 1.01
                        if is_normalized:
                            x_center, y_center, w, h = p1 * img_width, p2 * img_height, p3 * img_width, p4 * img_height
                            x_min, y_min = x_center - w / 2, y_center - h / 2
                            x_max, y_max = x_center + w / 2, y_center + h / 2
                        else:
                            x_min, y_min, x_max, y_max = p1, p2, p3, p4
                        
                        bbox = [max(0, int(x_min)), max(0, int(y_min)), min(img_width, int(x_max)), min(img_height, int(y_max))]
                        
                        # MODIFICATION FOR P1: Add strong validation for coordinates
                        if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                            continue  # Skip invalid bbox with zero or negative area.

                        defect_tuple = (class_name, *bbox)
                        if defect_tuple not in seen_defects:
                            defects.append({"class": class_name, "bbox": bbox, "class_id": class_id_str})
                            seen_defects.add(defect_tuple)
                    except (ValueError, IndexError): 
                        continue
    return defects, (img_width, img_height)

def get_component_label_content(label_path: str, img_width: int, img_height: int, component_map: Dict[str, str]) -> Tuple[List[Dict[str, Any]], Tuple[int, int]]:
    components = []
    if img_width <= 0 or img_height <= 0: return components, (img_width, img_height)
    seen_components = set()
    if os.path.exists(label_path):
        with open(label_path, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 5:
                    try:
                        class_id_str, p1_str, p2_str, p3_str, p4_str = parts
                        component_name = normalize_class_name(component_map.get(class_id_str, f"Unknown_{class_id_str}"))
                        p1, p2, p3, p4 = float(p1_str), float(p2_str), float(p3_str), float(p4_str)
                        is_normalized = max(p1, p2, p3, p4) <= 1.01
                        if is_normalized:
                            x_center, y_center, w, h = p1 * img_width, p2 * img_height, p3 * img_width, p4 * img_height
                            x_min, y_min = x_center - w / 2, y_center - h / 2
                            x_max, y_max = x_center + w / 2, y_center + h / 2
                        else:
                            x_min, y_min, x_max, y_max = p1, p2, p3, p4
                            
                        bbox = [max(0, int(x_min)), max(0, int(y_min)), min(img_width, int(x_max)), min(img_height, int(y_max))]
                        
                        # MODIFICATION FOR P1: Add strong validation for coordinates
                        if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                            continue # Skip invalid bbox with zero or negative area.

                        component_tuple = (component_name, *bbox)
                        if component_tuple not in seen_components:
                            components.append({"class": component_name, "bbox": bbox, "class_id": class_id_str})
                            seen_components.add(component_tuple)
                    except (ValueError, IndexError): 
                        continue
    return components, (img_width, img_height)

def encode_image(image_path: Optional[str]) -> Optional[str]:
    if not image_path or not os.path.exists(image_path): return None
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

def calculate_resistor_value(model: str) -> Optional[Tuple[str, str]]:
    """
    Calculates the resistance value from an SMD resistor code.
    Handles 3-digit, 4-digit, EIA-96, and R-notation codes.
    """
    model = model.upper()
    value_ohms = None
    tolerance_str = "N/A" # Default tolerance

    # Zero-ohm resistor (jumper)
    if model in ('0', '000', '0000'):
        value_ohms, tolerance_str = 0.0, "Jumper"
    # R-notation (e.g., R47 = 0.47, 4R7 = 4.7)
    elif 'R' in model and len(model) > 1:
        try:
            parts = model.split('R')
            if len(parts) == 2:
                if not parts[0]: value_ohms = float(f"0.{parts[1]}")
                elif not parts[1]: value_ohms = float(parts[0])
                else: value_ohms = float(f"{parts[0]}.{parts[1]}")
                if value_ohms is not None: tolerance_str = "5%"
        except (ValueError, IndexError):
            return None # Invalid R notation
    # 4-digit code (e.g., 1201 -> 120 * 10^1 = 1200 ohms)
    elif len(model) == 4 and model.isdigit():
        try:
            significant = int(model[:3])
            multiplier = 10 ** int(model[3])
            value_ohms = significant * multiplier
            tolerance_str = "1%"
        except ValueError:
            return None
    # 3-digit code (e.g., 102 -> 10 * 10^2 = 1000 ohms)
    elif len(model) == 3 and model.isdigit():
        try:
            significant = int(model[:2])
            multiplier = 10 ** int(model[2])
            value_ohms = significant * multiplier
            tolerance_str = "5%"
        except ValueError:
            return None
    else:
        # Potentially other codes like EIA-96, but we'll stick to the common ones for now.
        return None

    if value_ohms is None:
        return None

    # Format the output string
    if value_ohms >= 1e6:
        value_str = f"{value_ohms / 1e6:.10g} MΩ"
    elif value_ohms >= 1e3:
        value_str = f"{value_ohms / 1e3:.10g} kΩ"
    else:
        value_str = f"{value_ohms:.10g} Ω"
        
    # Clean up trailing ".0" for whole numbers
    value_str = re.sub(r"\.0( [kM]?Ω)$", r"\1", value_str)
    
    return value_str, tolerance_str

def extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', response_text, re.IGNORECASE)
    json_str = match.group(1) if match else response_text[response_text.find('{'):response_text.rfind('}') + 1]
    json_str = json_str.strip()
    if not json_str: return None
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    try:
        parsed = json.loads(json_str)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError: return None

def clean_text_for_json(text: str) -> str:
    if isinstance(text, str) and text.strip().startswith('{') and text.strip().endswith('}'):
        try:
            return json.dumps(json.loads(text), ensure_ascii=False, separators=(',', ':'))
        except json.JSONDecodeError:
            pass
    if not isinstance(text, str): return str(text)
    return re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()

# ... (Rest of the file is unchanged)
def get_dataset_directories(dataset_name: str) -> Dict[str, str]:
    dataset_path = os.path.join(ROOT_DIR, dataset_name)
    return {
        "IMAGE_DIR": os.path.join(dataset_path, "images"), "LABEL_DIR": os.path.join(dataset_path, "labels"),
        "IMAGE_BBOX_DIR": os.path.join(dataset_path, "bbox_class"), "IMAGE_BBOX_NOCLASS_DIR": os.path.join(dataset_path, "bbox_noclass"),
        "TEMPLATE_IMAGE": os.path.join(dataset_path, "TemplateImages"),
    }

def get_defect_map(dataset_name: str, prior_knowledge: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str]]:
    dataset_info = prior_knowledge.get(dataset_name, {})
    defect_map = normalize_name_map(dataset_info.get("defect_map", {}))
    defect_map_chinese = normalize_translation_map(dataset_info.get("defect_map_chinese", {}))
    if not defect_map_chinese and defect_map: defect_map_chinese = {v: v for v in defect_map.values()}
    return defect_map, defect_map_chinese

def get_component_map(dataset_name: str, prior_knowledge: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    dataset_info = prior_knowledge.get(dataset_name, {})
    component_map = normalize_name_map(dataset_info.get("map", {}))
    component_map_type = normalize_translation_map(dataset_info.get("map_type", {}))
    component_describe = normalize_translation_map(dataset_info.get("describe", {}))
    if not component_map_type and component_map: component_map_type = {v: f"Desc missing for {v}" for v in component_map.values()}
    if not component_describe and component_map: component_describe = {v: f"Appearance missing for {v}" for v in component_map.values()}
    return component_map, component_map_type, component_describe

def format_defect_coordinates(label_content: List[Dict[str, Any]], defect_map_en: Dict[str, str], defect_map_zh: Dict[str, str], lang: str) -> str:
    """
    Formats defect coordinates into a JSON string, grouping all bboxes by class name.
    This version is guaranteed to list all coordinates.
    """
    if not label_content:
        return json.dumps({})
        
    coords_by_class = collections.defaultdict(list)
    for defect in label_content:
        class_name_en = defect.get("class")
        if not class_name_en or 'bbox' not in defect:
            continue
            
        class_name_en = normalize_class_name(class_name_en)
        key_name = defect_map_zh.get(class_name_en, class_name_en) if lang == 'zh' else class_name_en
        coords_by_class[key_name].append(defect["bbox"])
        
    return json.dumps(coords_by_class, ensure_ascii=False, separators=(',', ':'))

def generate_simple_coordinate_question(is_defect: bool, is_compare: bool, lang: str) -> str:
    """Generates a simple, fallback question for coordinates."""
    obj_type = i18n.get_text('object_type_names', lang)['defect' if is_defect else 'component']
    compare_prefix = i18n.get_text('dynamic_questions.compare_prefix', lang) if is_compare else ""
    
    if lang == 'zh':
        return f"{compare_prefix}请提供图中所有{obj_type}的边界框坐标。".strip()
    else:
        return f"{compare_prefix}Please provide the bounding box coordinates for all {obj_type}s in the image.".strip()


def format_component_coordinates(components: List[Dict[str, Any]], component_map_en_to_zh: Dict[str, str], lang: str) -> str:
    """
    Formats component coordinates into a JSON string, grouping all bboxes by class name.
    This version supports multiple languages for the keys.
    """
    if not components:
        return json.dumps({})
        
    coords_by_class = collections.defaultdict(list)
    for comp in components:
        # 'class' 字段在 get_component_label_content 中已被设为英文名, e.g., "Resistor"
        class_name_en = comp.get("class")
        if class_name_en and 'bbox' in comp:
            # 如果语言是中文，就用映射表翻译成中文名；否则，直接用英文名
            class_name_en = normalize_class_name(class_name_en)
            key_name = component_map_en_to_zh.get(class_name_en, class_name_en) if lang == 'zh' else class_name_en
            coords_by_class[key_name].append(comp["bbox"])
            
    return json.dumps(coords_by_class, ensure_ascii=False, separators=(',', ':'))
    

def create_distractor_prompt(question_type: str, question: str, correct_option: str, lang: str, is_solder_joint: bool = False) -> str:
    base_prompt = i18n.get_text('DISTRACTOR_BASE_PROMPT', lang).format(question=question, correct_option=correct_option)

    if question_type in ["defect location", "component location"]:
        # 强制使用我们新的、结构化的prompt
        guidance_key = "location_structured"
    else:
        # 对于其他类型，使用原有的逻辑
        guidance_key = question_type.replace(" ", "_")
        if question_type == "object describe":
            if is_solder_joint and ("焊点" in correct_option or "solder joint" in correct_option.lower()):
                guidance_key = "object_describe_solder"
            elif "pcb" in correct_option.lower() or "印刷电路板" in correct_option or "元件" in correct_option or "component" in correct_option.lower():
                guidance_key = "object_describe_pcb"
            else:
                guidance_key = "object_describe_default"

    specific_guidance = i18n.get_text(f'DISTRACTOR_GUIDANCE.{guidance_key}', lang).format(correct_option=correct_option)
    if "[[Text not found" in specific_guidance: 
        specific_guidance = i18n.get_text('DISTRACTOR_GUIDANCE.default', lang)

    return base_prompt + specific_guidance

def get_distractors_from_api(prompt: str, max_retries: int, correct_option: str) -> List[str]:
    data = {"model": MODEL_PATH, "messages": [{"role": "user", "content": prompt}], "temperature": 0.8, "max_tokens": 20480}
    for attempt in range(max_retries):
        try:
            response = requests.post(f"{API_BASE}/chat/completions", json=data, timeout=120)
            response.raise_for_status()
            content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                distractors = [clean_text_for_json(re.sub(r'^\s*([A-Da-d][\.\)]|[1-9][\.\)]|[一二三四][\.\uff0e\uff09]?|[个\-*❖➢])\s*', '', line).strip()) for line in content.strip().split('\n')]
                valid_distractors = [d for d in distractors if len(d) > 1 and d.lower() != correct_option.lower()]
                if len(valid_distractors) >= 3: 
                    return valid_distractors[:3]
                # --- ADD THIS LOGGING ---
                #else:
                #    print(f"DEBUG: API (Attempt {attempt+1}) returned insufficient valid distractors. Got: {valid_distractors}. Full content: {content[:100]}...")
            # --- ADD THIS LOGGING ---
            #else:
            #    print(f"DEBUG: API (Attempt {attempt+1}) returned empty content.")

        except requests.exceptions.RequestException as e:
            # --- IMPROVE THIS LOGGING ---
            print(f"DEBUG: API request failed (Attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1) # sleep before retry
    return [] # Return empty list if all retries fail

def generate_programmatic_classification_distractors(
    correct_option: str,
    defect_map_en: Dict[str, str],
    defect_map_zh: Dict[str, str],
    lang: str,
    num_distractors: int = 3
) -> list:
    """
    Generates plausible but incorrect distractors for defect classification questions.
    This version correctly uses the provided maps and has robust fallbacks.
    """
    all_possible_localized_names = list(defect_map_zh.values()) if lang == 'zh' else list(defect_map_en.values())
    generic_defect_types = (
        ["开路", "短路", "鼠咬", "缺孔", "焊桥", "缺焊", "划痕", "污染", "烧焦", "缺少元件", "多余元件", "错误位置"]
        if lang == 'zh'
        else ["open circuit", "short", "mouse bite", "missing hole", "solder bridge", "lack of solder", "scratch", "contamination", "burnt", "missing components", "extra", "wrong place"]
    )
    none_label = "无标注缺陷" if lang == 'zh' else "No annotated defects"
    return generate_programmatic_type_distractors(
        correct_option,
        all_possible_localized_names,
        lang,
        num_distractors,
        fallback_types=generic_defect_types,
        none_label=none_label,
    )

def split_type_answer(answer: str, lang: str) -> List[str]:
    if not answer:
        return []
    separator_pattern = r'[、,，]'
    return [normalize_class_name(part) for part in re.split(separator_pattern, answer) if normalize_class_name(part)]

def join_type_answer(types: List[str], lang: str) -> str:
    cleaned = [normalize_class_name(t) for t in types if normalize_class_name(t)]
    return "、".join(cleaned) if lang == 'zh' else ", ".join(cleaned)

def generate_programmatic_type_distractors(
    correct_option: str,
    all_possible_types: List[str],
    lang: str,
    num_distractors: int = 3,
    fallback_types: Optional[List[str]] = None,
    none_label: Optional[str] = None,
) -> List[str]:
    correct_types = split_type_answer(correct_option, lang)
    possible = []
    for item in list(all_possible_types or []) + list(fallback_types or []):
        name = normalize_class_name(item)
        if name and name not in possible:
            possible.append(name)
    other_types = [t for t in possible if t not in correct_types]
    if not correct_types:
        return []

    distractors = []

    def add_candidate(candidate: List[str]) -> None:
        cleaned = []
        for item in candidate:
            name = normalize_class_name(item)
            if name and name not in cleaned:
                cleaned.append(name)
        if not cleaned:
            return
        distractor = join_type_answer(cleaned, lang)
        if distractor != correct_option and distractor not in distractors:
            distractors.append(distractor)

    # Omission distractors are especially important when the correct answer has
    # multiple classes and the dataset vocabulary contains only those classes.
    if len(correct_types) > 1:
        for idx in range(len(correct_types)):
            add_candidate([t for j, t in enumerate(correct_types) if j != idx])
            if len(distractors) >= num_distractors:
                return distractors[:num_distractors]

    if none_label:
        add_candidate([none_label])
        if len(distractors) >= num_distractors:
            return distractors[:num_distractors]

    if not other_types:
        return distractors[:num_distractors]

    target_len = len(correct_types)
    for _ in range(num_distractors * 20):
        if len(distractors) >= num_distractors:
            break
        candidate = correct_types[:]
        replace_count = random.randint(1, min(target_len, len(other_types)))
        replace_positions = random.sample(range(target_len), replace_count)
        replacements = random.sample(other_types, replace_count)
        for pos, repl in zip(replace_positions, replacements):
            candidate[pos] = repl
        # Preserve the number of listed classes and avoid duplicates inside an option.
        if len(set(candidate)) != len(candidate):
            continue
        add_candidate(candidate)

    for other_type in other_types:
        if len(distractors) >= num_distractors:
            break
        add_candidate(correct_types + [other_type])

    return distractors[:num_distractors]

def generate_programmatic_location_distractors(correct_answer: str, lang: str, num_distractors: int = 3) -> List[str]:
    """
    为位置描述类问题确定性地生成干扰项。
    例如: "开路: 左上角" -> "开路: 右下角"
    """
    # 1. 定义所有可能的位置
    locations_zh = ["左上角", "中上", "右上角", "左侧中部", "中心", "右侧中部", "左下角", "中下", "右下角"]
    locations_en = ["top-left", "top-center", "top-right", "middle-left", "middle-center", "middle-right", "bottom-left", "bottom-center", "bottom-right"]
    all_locations = locations_zh if lang == 'zh' else locations_en

    # 2. 从正确答案中提取出已使用的位置
    used_locations = [loc for loc in all_locations if loc in correct_answer]
    
    # 3. 找出所有未被使用的、可用于生成干扰项的位置
    available_distractor_locs = [loc for loc in all_locations if loc not in used_locations]
    
    # 如果没有可用的新位置（例如正确答案包含了所有位置），则无法生成，返回空列表
    if not available_distractor_locs:
        return []

    generated_distractors = set()

    # 4. 生成干扰项
    # 策略：随机替换掉一个正确的位置
    if used_locations:
        for _ in range(num_distractors * 2): # 循环多次以获得不同结果
            if len(generated_distractors) >= num_distractors:
                break
            
            # 随机选择一个要替换的正确位置和一个新的错误位置
            loc_to_replace = random.choice(used_locations)
            new_loc = random.choice(available_distractor_locs)
            
            # 生成新的干扰项字符串
            distractor = correct_answer.replace(loc_to_replace, new_loc, 1) # 只替换一次
            
            if distractor != correct_answer:
                generated_distractors.add(distractor)

    return list(generated_distractors)


def generate_programmatic_count_distractors(correct_answer: str, lang: str, num_distractors: int = 3) -> List[str]:
    original_nums_str = re.findall(r'\d+', correct_answer)
    if not original_nums_str:
        return []
    original_nums = [int(n) for n in original_nums_str]
    generated_distractors = set()
    for _ in range(num_distractors * 5):
        if len(generated_distractors) >= num_distractors:
            break
        new_nums = []
        if len(original_nums) == 1:
            num = original_nums[0]
            distractor_pool = {max(0, num - 2), max(0, num - 1), num + 1, num + 2, num + 5}
            distractor_pool.discard(num)
            if distractor_pool:
                new_nums = [random.choice(list(distractor_pool))]
            else:
                new_nums = [num + 1]
        else:
            if random.random() > 0.4:
                 new_total = max(0, original_nums[0] + random.choice([-2, -1, 1, 2]))
                 while new_total == original_nums[0]:
                     new_total = max(0, original_nums[0] + random.choice([-2, -1, 1, 2]))
                 new_nums.append(new_total)
                 for i in range(1, len(original_nums)):
                     new_nums.append(max(0, original_nums[i] + random.choice([-1, 1, 0])))
            else:
                new_nums.append(original_nums[0])
                if len(original_nums) > 2:
                    parts_to_change = original_nums[1:]
                    idx_to_inc = random.randrange(len(parts_to_change))
                    idx_to_dec = random.randrange(len(parts_to_change))
                    while len(parts_to_change) > 1 and idx_to_inc == idx_to_dec:
                        idx_to_dec = random.randrange(len(parts_to_change))
                    changed_parts = list(parts_to_change)
                    if changed_parts[idx_to_dec] > 0:
                        changed_parts[idx_to_inc] += 1
                        changed_parts[idx_to_dec] -= 1
                    else:
                        changed_parts[idx_to_inc] += 1
                    new_nums.extend(changed_parts)
                elif len(original_nums) == 2:
                    new_nums.append(max(0, original_nums[1] + random.choice([-1, 1])))
                else:
                    new_nums.extend(original_nums[1:])
        it = iter(map(str, new_nums))
        distractor_str = re.sub(r'\d+', lambda m: next(it, m.group()), correct_answer)
        if distractor_str != correct_answer:
            generated_distractors.add(distractor_str)
    return list(generated_distractors)

def generate_defect_des(dataset_info: Dict[str, Any], lang: str) -> str:
    defects_describe = dataset_info.get("defects_describe", {})
    if not defects_describe: return ""
    if lang == 'zh':
        lines = ["请严格按照以下标准命名缺陷,确保用词准确,不使用任何其他描述："]
        lines.extend([f'- "{defect}"：{desc.split(".")[0].replace("缺陷", "")}' for defect, desc in defects_describe.items()])
    else:
        lines = ["Please name defects strictly according to the following standards, ensuring accurate terminology:"]
        lines.extend([f'- "{defect}": Refers to a {defect.lower()}.' for defect in defects_describe.keys()])
    return "\n".join(lines)

def generate_component_des(dataset_info: Dict[str, Any], lang: str) -> str:
    component_describes = dataset_info.get("describe", {})
    if not component_describes: return ""
    if lang == 'zh':
        lines = ["请参考以下元件外观特征描述（请注意这些是元件名称，非类别，请用中文名称命名）："]
        lines.extend([f'- "{name}"：{desc}' for name, desc in component_describes.items()])
    else:
        lines = ["Please refer to the following component appearance feature descriptions:"]
        lines.extend([f'- "{name}": {desc}' for name, desc in component_describes.items()])
    return "\n".join(lines)

def _get_location_name(y: float, x: float, h: int, w: int, lang: str) -> str:
    loc_map = i18n.get_text('location_map', lang)
    if y < h / 3: v_zone = "top"
    elif y < h * 2 / 3: v_zone = "middle"
    else: v_zone = "bottom"
    if x < w / 3: h_zone = "left"
    elif x < w * 2 / 3: h_zone = "center"
    else: h_zone = "right"
    key = f"{v_zone}-{h_zone}"
    return loc_map.get(key, f"{v_zone} {h_zone}")

def format_defect_positions(label_content: List[Dict[str, Any]], img_dims: Tuple[int, int], defect_map_en: Dict[str, str], defect_map_zh: Dict[str, str], lang: str) -> str:
    obj_type_name = i18n.get_text('object_type_names', lang)['defect']
    if not label_content:
        return i18n.get_text('dynamic_questions.no_defects_detected', lang).format(obj_type=obj_type_name)

    img_w, img_h = img_dims
    if img_h <= 0 or img_w <= 0: return "Position info unavailable (invalid image dimensions)"

    positions_by_type = collections.defaultdict(list)
    for defect in label_content:
        bbox = defect.get("bbox")
        class_en = defect.get("class")
        if not bbox or not class_en: continue
        class_en = normalize_class_name(class_en)
        type_name = defect_map_zh.get(class_en, class_en) if lang == 'zh' else class_en
        center_x, center_y = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
        positions_by_type[type_name].append(_get_location_name(center_y, center_x, img_h, img_w, lang))

    if not positions_by_type:
        return "Failed to summarize defect positions"

    output_parts = []
    for type_name, positions in sorted(positions_by_type.items()):
        # 获取所有不重复的位置名称
        unique_locations = sorted(list(set(positions)))
        if lang == 'zh':
            location_str = '、'.join(unique_locations)
            output_parts.append(f"{type_name}缺陷主要位于{location_str}")
        else:
            location_str = ' and '.join(unique_locations)
            output_parts.append(f"The {type_name} defect is primarily located in the {location_str}")

    if lang == 'zh':
        return '；'.join(output_parts) + '。'
    else:
        return '. '.join(output_parts) + '.'

def format_component_positions(components: List[Dict[str, Any]], img_dims: Tuple[int, int], lang: str) -> str:
    if not components: return "No specified components"
    img_w, img_h = img_dims
    if img_h <= 0 or img_w <= 0: return "Position info unavailable (invalid image dimensions)"

    positions = [_get_location_name((c['bbox'][1] + c['bbox'][3]) / 2, (c['bbox'][0] + c['bbox'][2]) / 2, img_h, img_w, lang) for c in components if 'bbox' in c]
    if not positions: return "Position info unavailable (no valid coordinates)"

    # 获取所有不重复的位置名称
    unique_pos = sorted(list(set(positions)))
    if lang == 'zh':
        location_str = '、'.join(unique_pos)
        return f"图中的元件主要分布在{location_str}。"
    else:
        location_str = ', '.join(unique_pos)
        return f"The components in the image are primarily distributed in the {location_str}."

def generate_dynamic_coordinate_question(label_content: List[Dict[str, Any]], is_defect: bool, is_compare: bool, maps: Dict, lang: str) -> str:
    """
    Generates a direct question specifying the exact class names for which coordinates are requested,
    based on the user's final clarification.
    """
    obj_type_generic = i18n.get_text('object_type_names', lang)['defect' if is_defect else 'component']

    # If there are no labels, we cannot specify class names, so we must ask a general question.
    if not label_content:
        if lang == 'zh':
            return f"找到图像中{obj_type_generic}的边界框坐标。"
        else:
            return f"Find the bounding box coordinates of {obj_type_generic} in the image."

    # 1. Extract the unique, localized class names from the label content.
    unique_class_names = set()
    if is_defect:
        map_to_use = maps.get('defect_map_chinese', {})
        for item in label_content:
            class_name_en = item.get("class")
            if class_name_en:
                class_name_en = normalize_class_name(class_name_en)
                localized_name = map_to_use.get(class_name_en, class_name_en) if lang == 'zh' else class_name_en
                unique_class_names.add(localized_name)
    else:  # is_component
        component_map_en = maps.get('component_map', {})
        component_map_zh_type = maps.get('component_map_type', {})
        for item in label_content:
            class_id = str(item.get("class_id"))
            if class_id in component_map_en:
                class_name_en = normalize_class_name(component_map_en[class_id])
                localized_name = component_map_zh_type.get(class_name_en, class_name_en) if lang == 'zh' else class_name_en
                unique_class_names.add(localized_name)

    # 2. If names were found, build the question string with them.
    if unique_class_names:
        # Format the list of names, e.g., "开路、短路" or "Resistor, Capacitor"
        class_list_str = '、'.join(sorted(list(unique_class_names))) if lang == 'zh' else ', '.join(sorted(list(unique_class_names)))
        
        # Construct the final, direct question.
        if lang == 'zh':
            return f"找到图像中{class_list_str}{obj_type_generic}的边界框坐标。"
        else:
            # Adding "s" for plural might be tricky with all component names, so we keep it general.
            plural = "defects" if is_defect else "components"
            return f"Find the bounding box coordinates for the {class_list_str} {plural} in the image."
    
    # Fallback in case loop completes without finding names
    if lang == 'zh':
        return f"找到图像中{obj_type_generic}的边界框坐标。"
    else:
        return f"Find the bounding box coordinates for all {obj_type_generic}s in the image."
    
def generate_dynamic_location_question(label_content: List[Dict[str, Any]], img_dims: Tuple[int, int], is_defect: bool, is_compare: bool, exclude_hint: bool, maps: Dict, lang: str) -> str:
    obj_type = i18n.get_text('object_type_names', lang)['defect' if is_defect else 'component']
    compare_prefix = i18n.get_text('dynamic_questions.compare_prefix', lang) if is_compare else ""

    specific_object_str = ""
    # Try to identify specific object types from the labels
    if label_content:
        unique_class_names = set()
        if is_defect:
            map_to_use = maps.get('defect_map_chinese', {})
            for item in label_content:
                class_name_en = item.get("class")
                if class_name_en:
                    class_name_en = normalize_class_name(class_name_en)
                    localized_name = map_to_use.get(class_name_en, class_name_en) if lang == 'zh' else class_name_en
                    unique_class_names.add(localized_name)
        else: # is_component
            component_map_en = maps.get('component_map', {})
            component_map_zh_type = maps.get('component_map_type', {})
            for item in label_content:
                class_id = str(item.get("class_id"))
                if class_id in component_map_en:
                    class_name_en = normalize_class_name(component_map_en[class_id])
                    localized_name = component_map_zh_type.get(class_name_en, class_name_en) if lang == 'zh' else class_name_en
                    unique_class_names.add(localized_name)

        if unique_class_names:
            class_list = '、'.join(sorted(list(unique_class_names))) if lang == 'zh' else ', '.join(sorted(list(unique_class_names)))
            specific_object_str = class_list + obj_type

    # Build the question
    if specific_object_str:
        # If we have specific names, create a specific question
        if lang == 'zh':
            base_question = f"请简述图中{specific_object_str}的位置。"
        else:
            plural = "defects" if is_defect else "components"
            base_question = f"Please briefly describe the location of the {specific_object_str} {plural} in the image."
    else:
        # Otherwise, create a general question
        base_question = i18n.get_text('dynamic_questions.location_question_intro', lang).format(obj_type=obj_type)

    return f"{compare_prefix}{base_question}".strip()


def generate_dynamic_count_question(label_content: List[Dict[str, Any]], is_defect: bool, maps: Dict, lang: str) -> str:
    obj_type = i18n.get_text('object_type_names', lang)['defect' if is_defect else 'component']
    if not label_content: return i18n.get_text('dynamic_questions.count_question_default', lang).format(obj_type=obj_type)
    if is_defect:
        if len({d.get("class") for d in label_content if d.get("class")}) > 1:
            return i18n.get_text('dynamic_questions.count_question_multi_defect', lang)
    else:
        if label_content:
            first_comp_id = str(label_content[0].get("class_id"))
            first_comp_name_en = maps['component_map'].get(first_comp_id, first_comp_id)
            first_comp_name_en = normalize_class_name(first_comp_name_en)
            type_name = maps['component_map_type'].get(first_comp_name_en, first_comp_name_en) if lang == 'zh' else first_comp_name_en
            return i18n.get_text('dynamic_questions.count_question_component', lang).format(type=type_name, obj_type=obj_type)
    return i18n.get_text('dynamic_questions.count_question_default', lang).format(obj_type=obj_type)

def generate_smarter_count_distractors(correct_answer: str, all_possible_types: list, lang: str, is_defect: bool, num_distractors: int = 3) -> List[str]:
    """
    生成逻辑更严谨的计数类问题干扰项。
    遵循以下策略：
    1. 保持总数和分项数逻辑一致。
    2. 类别正确，但数量错误。
    3. 总数错误，但分项数之和等于新的总数。
    4. 类别错误，但数量结构模仿正确答案。
    """
    
    # 1. 解析正确答案字符串
    # 例: "总共4个元件，其中：Capacitor2个，Resistor2个。"
    # 解析为: {'total': 4, 'Capacitor': 2, 'Resistor': 2}
    
    total_match = re.search(r'(\d+)', correct_answer)
    if not total_match:
        return [] # 无法解析，返回空
    
    correct_total = int(total_match.group(1))
    
    details_str = correct_answer.split('其中：')[-1].split('including:')[-1]
    # Extract (class, count) pairs while supporting spaces, slashes, hyphens, and mixed
    # Chinese/English names such as "open circuit 1" or "Crystal/Oscillator 2".
    if lang == 'zh':
        parts = re.findall(r'([^，。,:;]+?)\s*(\d+)\s*个', details_str)
    else:
        parts = re.findall(r'([^,.;:]+?)\s+(\d+)(?=\s*(?:,|\.|$))', details_str)
    
    correct_counts = OrderedDict({normalize_class_name(name): int(num) for name, num in parts})

    # 如果解析出的分项总和与总数不符，说明解析有误或答案本身有问题
    if sum(correct_counts.values()) != correct_total and correct_counts:
        # print(f"Warning: Parsed counts do not sum to total in '{correct_answer}'")
        return [] # 避免基于错误输入生成

    generated_distractors = set()
    
    # 定义生成策略
    strategies = []
    
    # 策略1: 类别正确，数量错误 (内部调换) - 对应您的"⚖️"
    # 例: Total 4, A 2, B 2 -> Total 4, A 3, B 1
    if len(correct_counts) > 1:
        strategies.append("swap_counts")

    # 策略2: 总数错误，但内部分配逻辑自洽
    # 例: Total 4, A 2, B 2 -> Total 3, A 1, B 2
    if correct_total > 0:
        strategies.append("wrong_total_consistent")

    # 策略3: 错类但数量一致 (需要所有可能的类别) - 对应您的"🔁"
    # 例: Total 2, A 2 -> Total 2, C 2 (C是另一个有效类别)
    all_possible_types = [normalize_class_name(t) for t in all_possible_types if normalize_class_name(t)]
    other_types = [t for t in all_possible_types if t not in correct_counts]
    if len(correct_counts) > 0 and len(other_types) > 0:
        strategies.append("wrong_class")
        
    if not strategies: # 如果没有任何可用策略 (例如答案是 "总共0个")
        return []

    # 循环生成，直到满足数量或尝试次数过多
    for _ in range(num_distractors * 20): # 尝试更多次以获得多样性
        if len(generated_distractors) >= num_distractors:
            break
        
        strategy = random.choice(strategies)
        new_counts = correct_counts.copy()
        new_total = correct_total

        if strategy == "swap_counts":
            k1, k2 = random.sample(list(new_counts.keys()), 2)
            if new_counts[k1] > 1:
                new_counts[k1] -= 1
                new_counts[k2] += 1
            else:
                continue
        
        elif strategy == "wrong_total_consistent":
            delta = random.choice([-2, -1, 1, 2])
            new_total = max(0, correct_total + delta)
            if new_total == correct_total: continue # 确保总数真的改变了

            # 重新分配分项数量，使其总和等于新的总数
            keys = list(new_counts.keys())
            if not keys: continue

            remaining = new_total
            rebuilt = OrderedDict()
            shuffled_keys = keys[:]
            random.shuffle(shuffled_keys)
            for idx, key in enumerate(shuffled_keys):
                if idx == len(shuffled_keys) - 1:
                    value = remaining
                else:
                    min_left = max(0, len(shuffled_keys) - idx - 1)
                    max_value = max(0, remaining - min_left)
                    value = random.randint(1 if remaining > min_left else 0, max_value)
                rebuilt[key] = value
                remaining -= value
            new_counts = OrderedDict((key, rebuilt[key]) for key in keys)


        elif strategy == "wrong_class":
            key_to_replace = random.choice(list(new_counts.keys()))
            new_type = random.choice(other_types)
            
            # 替换类别
            original_value = new_counts.pop(key_to_replace)
            new_counts[new_type] = original_value
            # 保持字典有序性，将新项插入
            new_counts = OrderedDict(sorted(new_counts.items()))

        obj_type_name = i18n.get_text('object_type_names', lang)['defect' if is_defect else 'component']
        new_total = sum(new_counts.values())

        # 格式化成字符串
        if lang == 'zh':
            visible_counts = OrderedDict((name, num) for name, num in new_counts.items() if num > 0)
            if not visible_counts:
                distractor_str = f"总共{new_total}个{obj_type_name}。"
            else:
                details = "，".join([f"{name}{num}个" for name, num in visible_counts.items()])
                distractor_str = f"总共{new_total}个{obj_type_name}，其中：{details}。"
        else: # 英文
            obj_type_name_plural = obj_type_name + "s"
            visible_counts = OrderedDict((name, num) for name, num in new_counts.items() if num > 0)
            if not visible_counts:
                distractor_str = f"Total {new_total} {obj_type_name_plural}."
            else:
                details = ", ".join([f"{name} {num}" for name, num in visible_counts.items()])
                distractor_str = f"Total {new_total} {obj_type_name_plural}, including: {details}."
        
        if (
            distractor_str != correct_answer
            and count_answer_is_consistent(distractor_str)
            and not count_answer_has_zero_class(distractor_str)
        ):
            generated_distractors.add(distractor_str)
                
    return list(generated_distractors)[:num_distractors]

def count_answer_is_consistent(answer: str) -> bool:
    nums = [int(n) for n in re.findall(r'\d+', answer)]
    return len(nums) < 2 or nums[0] == sum(nums[1:])

def count_answer_has_zero_class(answer: str) -> bool:
    """Return True when an option explicitly lists a class with zero instances."""
    details = answer
    for marker in ("其中：", "including:"):
        if marker in details:
            details = details.split(marker, 1)[1]
            break
    if "其中：" not in answer and "including:" not in answer:
        return False
    if re.search(r'[^，。,:;]+?\s*(\d+)\s*个', details):
        return any(int(num) == 0 for num in re.findall(r'[^，。,:;]+?\s*(\d+)\s*个', details))
    if re.search(r'[^,.;:]+?\s+(\d+)(?=\s*(?:,|\.|$))', details):
        return any(int(num) == 0 for num in re.findall(r'[^,.;:]+?\s+(\d+)(?=\s*(?:,|\.|$))', details))
    return False

def count_answer_is_valid_option(answer: str) -> bool:
    return count_answer_is_consistent(answer) and not count_answer_has_zero_class(answer)

def generate_simple_count_distractors(correct_answer: str, num_distractors: int = 3) -> list:
    """
    一个简单的、鲁棒的计数类问题干扰项生成器（作为备用方案）。
    它不关心复杂的逻辑，只负责找到所有数字并进行简单的增减，确保总能生成结果。
    """
    original_nums_str = re.findall(r'\d+', correct_answer)
    if not original_nums_str:
        return [] # 如果正确答案中没有数字，则无法生成

    original_nums = [int(n) for n in original_nums_str]
    generated_distractors = set()

    for _ in range(num_distractors * 5): # 尝试更多次以获得多样性
        if len(generated_distractors) >= num_distractors:
            break

        new_nums = []
        for num in original_nums:
            # 随机选择一个偏移量，0也可能，增加多样性
            delta = random.choice([-2, -1, 1, 2, 0, 0]) 
            new_num = max(0, num + delta) # 确保数字不为负
            new_nums.append(new_num)

        # 如果所有数字都没变，强制改变第一个数字
        if new_nums == original_nums and new_nums:
            new_nums[0] = max(0, new_nums[0] + random.choice([-1, 1]))

        # 使用迭代器替换字符串中的所有数字
        it = iter(map(str, new_nums))
        distractor_str = re.sub(r'\d+', lambda m: next(it, m.group()), correct_answer)

        if distractor_str != correct_answer:
            generated_distractors.add(distractor_str)

    return list(generated_distractors)

    
