# config.py

import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# --- General Settings ---
DEFAULT_CONFIG = {
    "API_BASE": os.environ.get("UNIPCB_API_BASE", "http://localhost:10029/v1"),
    "MODEL_PATH": os.environ.get("UNIPCB_MODEL_PATH", "Qwen2.5-VL-72B-Instruct-AWQ"),
    "ROOT_DIR": os.path.join(PROJECT_ROOT, "data", "benchmark", "raw"),
    "IMAGE_FACTOR": 28,
    "MIN_PIXELS": 4 * 28 * 28,
    "MAX_PIXELS": 3000000,
    "MAX_RATIO": 200,
    "MAX_WORKERS": 10,
    "PRIOR_KNOWLEDGE_FILE": os.path.join(PROJECT_ROOT, "scripts", "benchmark_generation", "test_prior_knowledge.json"),
}
MAX_MCQ_GENERATION_RETRIES = 3
# --- New Dataset Categories and their properties ---
DATASET_CATEGORIES = {
    "P1": {
        "description": "Primary: bbox_class image. Questions: defect analysis, defect detail describe, component analysis, component describe.",
        "primary_image_type": "IMAGE_BBOX_DIR",
        "datasets": {
            "PCBA": {"is_defect": True, "is_compare": False, "min_resolution_threshold": None},
            "PCB-electric-resistance-Dataset_nodefect": {
                "is_defect": False,
                "is_resistor": True,
                "is_compare": False,
                "min_resolution_threshold": None,
                "primary_image_type": "IMAGE_BBOX_DIR"
            },
        }
    },
    "P2": {
        "description": "Primary: bbox_noclass image. Adds defect/component classification, conditionally count.",
        "primary_image_type": "IMAGE_BBOX_NOCLASS_DIR",
        "datasets": {
            "FPIC": {"is_defect": False, "is_compare": False, "min_resolution_threshold": None},
            "Dataset-PCB-CNN": {"is_defect": True, "is_compare": False, "min_resolution_threshold": None},
            "AoI": {"is_defect": True, "is_compare": False, "min_resolution_threshold": None}
        }
    },
    "P3": {
        "description": "Primary: original image. Adds detection, location, coordinates. Conditional count skip for low res. Includes compare types.",
        "primary_image_type": "IMAGE_DIR",
        "datasets": {
            "DeepPCB": {"is_defect": True, "is_compare": True, "min_resolution_threshold": None},
            "PCB-Defect-Detection-using-Image-Registration-master": {"is_defect": True, "is_compare": True, "min_resolution_threshold": None},
            "VisA": {"is_defect": True, "is_compare": True, "min_resolution_threshold": None},
            "solder-joint-dataset-main": {
                "is_defect": True, 
                "is_compare": False, 
                "min_resolution_threshold": 90000, 
                "is_solder_joint": True,
                "skip_q_types": ["defect count", "defect coordinates", "defect location"]
            },
            "pcb-component-detection": {"is_defect": False, "is_compare": False, "min_resolution_threshold": None}
        }

    }
}   

# --- Question Type Keys (Unified) ---
# MODIFICATION FOR P3: These are now canonical keys. The display text is in prompts_i18n.
QUESTION_TYPES = {
    "object describe": "object describe",
    "defect detection": "defect detection",
    "defect classification": "defect classification",
    "defect count": "defect count",
    "defect location": "defect location",
    "defect detail describe": "defect detail describe",
    "defect coordinates": "defect coordinates",
    "defect analysis": "defect analysis",

    "component count": "component count",
    "component type": "component type",
    "component location": "component location",
    "component describe": "component describe",
    "component coordinates": "component coordinates",
    "component analysis": "component analysis",
}
