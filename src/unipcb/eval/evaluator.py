"""UniPCB Evaluator - Comprehensive evaluation for PCB quality inspection models."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from dataclasses import dataclass
from .metrics import (
    compute_detection_metrics,
    compute_localization_metrics,
    compute_generation_metrics,
)


@dataclass
class EvaluationResult:
    """评估结果数据结构。"""
    
    scenario: str
    metrics: Dict[str, float]
    samples_evaluated: int
    detailed_results: Optional[List[Dict]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "scenario": self.scenario,
            "metrics": self.metrics,
            "samples_evaluated": self.samples_evaluated,
        }
    
    def summary(self) -> str:
        """生成评估摘要。"""
        lines = [
            f"Evaluation Results for {self.scenario}",
            "=" * 50,
            f"Samples Evaluated: {self.samples_evaluated}",
            "Metrics:",
        ]
        
        for metric, value in self.metrics.items():
            lines.append(f"  {metric}: {value:.4f}")
        
        return "\n".join(lines)


class UniPCBEvaluator:
    """
    UniPCB 基准测试评估器。
    
    支持三种评估场景的自动化评估：
    - component_detection: 元件检测
    - defect_localization: 缺陷定位
    - quality_analysis: 质量分析
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化评估器。
        
        Args:
            output_dir: 结果输出目录
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def evaluate(
        self,
        model: Any,
        dataset: Any,
        scenario: Optional[str] = None,
        batch_size: int = 16,
        save_results: bool = True,
    ) -> EvaluationResult:
        """
        评估模型性能。
        
        Args:
            model: 待评估的模型
            dataset: 测试数据集
            scenario: 评估场景（如果为 None，则从数据集推断）
            batch_size: 批次大小
            save_results: 是否保存结果
        
        Returns:
            EvaluationResult 对象
        """
        scenario = scenario or getattr(dataset, "scenario", "unknown")
        
        print(f"Evaluating model on {scenario} scenario...")
        print(f"Dataset size: {len(dataset)}")
        
        # 收集预测结果
        predictions = []
        ground_truths = []
        
        for idx in range(len(dataset)):
            sample = dataset[idx]
            
            # 获取模型预测
            pred = self._get_prediction(model, sample)
            predictions.append(pred)
            
            # 获取真实标注
            gt = self._get_ground_truth(sample)
            ground_truths.append(gt)
        
        # 计算指标
        metrics = self._compute_metrics(predictions, ground_truths, scenario)
        
        # 创建结果对象
        result = EvaluationResult(
            scenario=scenario,
            metrics=metrics,
            samples_evaluated=len(dataset),
            detailed_results={
                "predictions": predictions,
                "ground_truths": ground_truths,
            } if save_results else None,
        )
        
        # 保存结果
        if save_results and self.output_dir:
            self._save_results(result, scenario)
        
        print(result.summary())
        return result
    
    def _get_prediction(self, model: Any, sample: Dict) -> Dict:
        """获取模型预测。"""
        # 根据场景调用不同的推理方法
        image = sample["image"]
        task = sample["text"]
        
        if hasattr(model, "inspect"):
            prediction_text = model.inspect(image, task)
        else:
            # 通用推理接口
            prediction_text = str(model(image, task))
        
        return {
            "prediction": prediction_text,
            # 可以添加更多结构化输出
        }
    
    def _get_ground_truth(self, sample: Dict) -> Dict:
        """获取真实标注。"""
        return {
            "annotations": sample.get("labels", {}),
            "metadata": sample.get("metadata", {}),
        }
    
    def _compute_metrics(
        self,
        predictions: List[Dict],
        ground_truths: List[Dict],
        scenario: str,
    ) -> Dict[str, float]:
        """
        计算评估指标。
        
        根据不同场景使用不同的指标：
        - component_detection: mAP, Accuracy, F1
        - defect_localization: Precision@K, IoU
        - quality_analysis: BLEU, ROUGE, Domain-Score
        """
        if scenario == "component_detection":
            return compute_detection_metrics(predictions, ground_truths)
        elif scenario == "defect_localization":
            return compute_localization_metrics(predictions, ground_truths)
        elif scenario == "quality_analysis":
            return compute_generation_metrics(predictions, ground_truths)
        else:
            return {"error": f"Unknown scenario: {scenario}"}
    
    def _save_results(self, result: EvaluationResult, scenario: str):
        """保存评估结果。"""
        output_file = self.output_dir / f"eval_results_{scenario}.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to: {output_file}")
    
    def evaluate_all_scenarios(
        self,
        model: Any,
        datasets: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, EvaluationResult]:
        """
        评估所有场景。
        
        Args:
            model: 待评估的模型
            datasets: 场景到数据集的映射
        
        Returns:
            场景到评估结果的映射
        """
        results = {}
        
        for scenario, dataset in datasets.items():
            print(f"\n{'='*60}")
            print(f"Evaluating scenario: {scenario}")
            print(f"{'='*60}")
            
            results[scenario] = self.evaluate(model, dataset, scenario=scenario, **kwargs)
        
        # 打印汇总
        print("\n" + "="*60)
        print("OVERALL SUMMARY")
        print("="*60)
        
        for scenario, result in results.items():
            print(f"\n{scenario}:")
            for metric, value in result.metrics.items():
                print(f"  {metric}: {value:.4f}")
        
        return results
