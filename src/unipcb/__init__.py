"""
UniPCB: A Unified Vision-Language Benchmark for PCB Quality Inspection

This package provides tools and models for PCB quality inspection using
multimodal large language models.
"""

__version__ = "0.1.0"
__author__ = "UniPCB Authors"

from .data import UniPCBDataset
from .eval import UniPCBEvaluator

__all__ = ["UniPCBDataset", "UniPCBEvaluator"]
