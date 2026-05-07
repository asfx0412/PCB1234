"""Class-name normalization helpers."""

from __future__ import annotations

from typing import Dict


def _clean(text: object) -> str:
    return str(text or "").strip().lower()


def build_type_maps(prior_knowledge: Dict[str, dict]) -> Dict[str, Dict[str, Dict[str, str]]]:
    maps: Dict[str, Dict[str, Dict[str, str]]] = {}
    for dataset, info in (prior_knowledge or {}).items():
        defect_map: Dict[str, str] = {}
        component_map: Dict[str, str] = {}

        for english, chinese in info.get("defect_map_chinese", {}).items():
            canonical = _clean(chinese or english)
            defect_map[_clean(english)] = canonical
            defect_map[_clean(chinese)] = canonical

        for english, chinese in info.get("map_type", {}).items():
            canonical = _clean(chinese or english)
            component_map[_clean(english)] = canonical
            component_map[_clean(chinese)] = canonical

        for _, english in info.get("map", {}).items():
            component_map.setdefault(_clean(english), _clean(english))

        maps[dataset] = {"defect": defect_map, "component": component_map}
    return maps


def normalize_type(name: str, dataset: str, q_type: str, maps: Dict[str, Dict[str, Dict[str, str]]]) -> str:
    clean = _clean(name)
    kind = "defect" if "defect" in str(q_type).lower() else "component"
    return maps.get(dataset, {}).get(kind, {}).get(clean, clean)

