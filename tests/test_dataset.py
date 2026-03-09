"""Tests for UniPCB dataset."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestUniPCBDataset:
    """UniPCB 数据集测试。"""
    
    def test_import_dataset(self):
        """测试数据集导入。"""
        from unipcb.data import UniPCBDataset
        assert UniPCBDataset is not None
    
    def test_invalid_scenario(self):
        """测试无效场景处理。"""
        from unipcb.data import UniPCBDataset
        
        with pytest.raises(ValueError):
            UniPCBDataset(
                data_path="data/",
                scenario="invalid_scenario",
                split="train"
            )
    
    def test_invalid_split(self):
        """测试无效数据划分处理。"""
        from unipcb.data import UniPCBDataset
        
        with pytest.raises(ValueError):
            UniPCBDataset(
                data_path="data/",
                scenario="component_detection",
                split="invalid_split"
            )
    
    def test_dataset_initialization(self, tmp_path):
        """测试数据集初始化。"""
        from unipcb.data import UniPCBDataset
        
        # 创建临时数据目录
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # 创建空标注目录
        annotations_dir = data_dir / "annotations" / "component_detection"
        annotations_dir.mkdir(parents=True)
        
        # 创建空标注文件
        annotation_file = annotations_dir / "train.json"
        annotation_file.write_text('{"samples": []}')
        
        # 初始化数据集
        dataset = UniPCBDataset(
            data_path=str(data_dir),
            scenario="component_detection",
            split="train"
        )
        
        assert len(dataset) == 0
        assert dataset.scenario == "component_detection"
        assert dataset.split == "train"


class TestTransforms:
    """图像变换测试。"""
    
    def test_get_transform(self):
        """测试获取变换。"""
        from unipcb.data import get_transform
        
        train_transform = get_transform(is_training=True)
        val_transform = get_transform(is_training=False)
        
        assert train_transform is not None
        assert val_transform is not None


class TestMetrics:
    """评估指标测试。"""
    
    def test_detection_metrics(self):
        """测试检测指标。"""
        from unipcb.eval import compute_detection_metrics
        
        predictions = []
        ground_truths = []
        
        metrics = compute_detection_metrics(predictions, ground_truths)
        
        assert "mAP" in metrics
        assert "accuracy" in metrics
        assert "f1_score" in metrics
    
    def test_localization_metrics(self):
        """测试定位指标。"""
        from unipcb.eval import compute_localization_metrics
        
        predictions = []
        ground_truths = []
        
        metrics = compute_localization_metrics(predictions, ground_truths)
        
        assert "precision_at_1" in metrics
        assert "iou_mean" in metrics
    
    def test_generation_metrics(self):
        """测试生成指标。"""
        from unipcb.eval import compute_generation_metrics
        
        predictions = []
        ground_truths = []
        
        metrics = compute_generation_metrics(predictions, ground_truths)
        
        assert "bleu" in metrics
        assert "rougeL" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
