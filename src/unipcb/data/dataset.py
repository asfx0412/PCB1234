"""UniPCB Dataset - Unified Vision-Language Benchmark for PCB Quality Inspection."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
import torch
from torch.utils.data import Dataset


class UniPCBDataset(Dataset):
    """
    UniPCB 数据集类，用于加载 PCB 质量检测的视觉 - 语言数据。
    
    支持三种评估场景：
    - component_detection: 元件检测与识别
    - defect_localization: 缺陷定位
    - quality_analysis: 质量分析
    """
    
    SCENARIOS = ["component_detection", "defect_localization", "quality_analysis"]
    SPLITS = ["train", "val", "test"]
    
    def __init__(
        self,
        data_path: str,
        scenario: str = "component_detection",
        split: str = "train",
        transform: Optional[Any] = None,
        max_length: int = 512,
    ):
        """
        初始化 UniPCB 数据集。
        
        Args:
            data_path: 数据目录路径
            scenario: 评估场景 (component_detection/defect_localization/quality_analysis)
            split: 数据划分 (train/val/test)
            transform: 图像变换
            max_length: 文本最大长度
        """
        self.data_path = Path(data_path)
        self.scenario = scenario
        self.split = split
        self.transform = transform
        self.max_length = max_length
        
        if scenario not in self.SCENARIOS:
            raise ValueError(f"Invalid scenario: {scenario}. Must be one of {self.SCENARIOS}")
        if split not in self.SPLITS:
            raise ValueError(f"Invalid split: {split}. Must be one of {self.SPLITS}")
        
        # 加载数据
        self.samples = self._load_samples()
        
    def _load_samples(self) -> List[Dict]:
        """加载样本数据。"""
        # TODO: 实现实际的数据加载逻辑
        # 这里提供框架，等数据发布后补充
        annotation_file = self.data_path / "annotations" / self.scenario / f"{self.split}.json"
        
        if not annotation_file.exists():
            print(f"Warning: Annotation file not found: {annotation_file}")
            print("Please ensure data is properly downloaded and organized.")
            return []
        
        with open(annotation_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return data.get("samples", [])
    
    def __len__(self) -> int:
        """返回数据集大小。"""
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        获取单个样本。
        
        Returns:
            包含以下键的字典：
            - image: PIL Image 或 Tensor
            - text: 文本描述/问题
            - labels: 标注信息（边界框、类别等）
            - metadata: 元数据
        """
        sample = self.samples[idx]
        
        # 加载图像
        image_path = self.data_path / sample["image_path"]
        image = Image.open(image_path).convert("RGB")
        
        if self.transform:
            image = self.transform(image)
        
        # 构建样本
        result = {
            "image": image,
            "text": sample.get("question", ""),
            "labels": sample.get("annotations", {}),
            "metadata": {
                "sample_id": sample.get("id", idx),
                "scenario": self.scenario,
                "image_path": str(image_path),
            }
        }
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据集统计信息。"""
        stats = {
            "total_samples": len(self),
            "scenario": self.scenario,
            "split": self.split,
        }
        
        # 可以添加更多统计信息
        if len(self.samples) > 0:
            # 计算平均文本长度、类别分布等
            pass
        
        return stats
    
    @classmethod
    def from_config(cls, config_path: str) -> "UniPCBDataset":
        """从配置文件加载数据集。"""
        import yaml
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        return cls(
            data_path=config["data_path"],
            scenario=config["scenario"],
            split=config["split"],
            max_length=config.get("max_length", 512),
        )
