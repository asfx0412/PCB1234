# UniPCB Data

## 📊 数据集说明

本目录包含 UniPCB 基准测试的数据集。

**⚠️ 注意：数据和模型权重将在论文正式中稿后发布。**

---

## 预期目录结构

```
data/
├── README.md                    # 本文件
├── annotations/
│   ├── component_detection/
│   │   ├── train.json
│   │   ├── val.json
│   │   └── test.json
│   ├── defect_localization/
│   │   ├── train.json
│   │   ├── val.json
│   │   └── test.json
│   └── quality_analysis/
│       ├── train.json
│       ├── val.json
│       └── test.json
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── models/                      # 预训练模型权重（待发布）
    └── pcb-gpt-base/
```

---

## 数据格式

### 标注文件格式

每个场景的标注文件采用 JSON 格式：

```json
{
  "scenario": "component_detection",
  "split": "train",
  "samples": [
    {
      "id": "sample_001",
      "image_path": "images/train/pcb_001.jpg",
      "question": "How many capacitors are visible in this image?",
      "annotations": {
        "components": [
          {"type": "capacitor", "bbox": [x1, y1, x2, y2], "confidence": 0.95}
        ],
        "text": "There are 3 capacitors visible."
      }
    }
  ]
}
```

---

## 三个评估场景

### 1. Component Detection（元件检测）
- **任务**: 检测和识别 PCB 上的电子元件
- **数据规模**: 待公布
- **评估指标**: mAP, Accuracy, F1 Score

### 2. Defect Localization（缺陷定位）
- **任务**: 定位 PCB 上的制造缺陷
- **数据规模**: 待公布
- **评估指标**: Precision@K, IoU, Localization Accuracy

### 3. Quality Analysis（质量分析）
- **任务**: 生成 PCB 质量分析报告
- **数据规模**: 待公布
- **评估指标**: BLEU, ROUGE, Domain-Score

---

## 数据获取

### 当前状态
🔒 数据暂未公开

### 发布计划
- ✅ 项目框架：已发布
- ⏳ 基准测试代码：进行中
- ⏳ 数据集：论文中稿后发布
- ⏳ 预训练模型：论文中稿后发布

### 获取通知
请关注：
- 📄 arXiv: https://arxiv.org/abs/2601.19222
- 🐙 GitHub: https://github.com/fuxiangSun/UniPCB

---

## 引用

如果您使用了 UniPCB 数据集，请引用我们的论文：

```bibtex
@article{sun2026unipcb,
  title={UniPCB: A Unified Vision-Language Benchmark for Open-Ended PCB Quality Inspection},
  author={Sun, Fuxiang and Jiang, Xi and Wu, Jiansheng and Zhang, Haigang and Zheng, Feng and Yang, Jinfeng},
  journal={arXiv preprint arXiv:2601.19222},
  year={2026}
}
```

---

## 联系方式

如有数据相关问题，请通过 GitHub Issues 联系。
