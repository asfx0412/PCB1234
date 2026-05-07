"""Path helpers that keep public JSON files project-relative."""

from __future__ import annotations

import os
from typing import Optional

from evaluation.config import PROJECT_ROOT


def resolve_project_path(path: str, must_exist: bool = False) -> str:
    """Resolve a project-relative or absolute path to an absolute local path."""
    if not path:
        return path
    resolved = path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)
    if must_exist and not os.path.exists(resolved):
        raise FileNotFoundError(f"Path not found: {path}")
    return resolved


def to_project_relative(path: str) -> str:
    """Convert an absolute path under the project root to a stable relative path."""
    if not path:
        return path
    try:
        rel = os.path.relpath(path, PROJECT_ROOT)
    except ValueError:
        return path
    return rel if not rel.startswith("..") else path


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def default_output_path(directory: str, stem: str, suffix: str = ".json") -> str:
    import datetime

    ensure_dir(directory)
    timestamp = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"
    return os.path.join(directory, f"{stem}_{timestamp}{suffix}")

