# PCB-GPT Model

## 🤖 模型说明

PCB-GPT 是专为 PCB 质量检测优化的多模态大语言模型。

**⚠️ 注意：模型权重将在论文正式中稿后发布。**

---

## 模型架构

PCB-GPT 采用以下架构设计：

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Input Image   │ ──► │  Vision Encoder  │ ──► │  Vision Projector│
│   (PCB Photo)   │     │   (CLIP ViT)     │     │   (MLP)         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Output Text    │ ◄── │  Language Model  │ ◄── │  Multimodal    │
│  (Analysis)     │     │   (Qwen/Qwen-7B) │     │  Fusion Layer   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## 渐进式课程学习

PCB-GPT 采用三阶段渐进式训练策略，模仿人类专家的学习过程：

### 阶段 1: 基础认知
- **目标**: 学习基本元件识别
- **数据**: 简单场景，单一元件
- **任务**: 分类和基础检测

### 阶段 2: 缺陷感知
- **目标**: 学习缺陷模式识别
- **数据**: 包含常见缺陷的样本
- **任务**: 缺陷检测和定位

### 阶段 3: 综合分析
- **目标**: 学习复杂场景推理
- **数据**: 真实工业场景
- **任务**: 综合质量分析和报告生成

---

## 预期模型规格

| 组件 | 规格 |
|------|------|
| 视觉编码器 | CLIP ViT-L/14 |
| 语言模型 | Qwen-7B |
| 隐藏层维度 | 1024 |
| 查询标记数 | 64 |
| 总参数量 | ~7B |

---

## 模型使用（待发布）

```python
from unipcb.models import PCBGPT

# 加载预训练模型
model = PCBGPT.from_pretrained("pcb-gpt-base")

# 运行检测
result = model.inspect(
    image="pcb_sample.jpg",
    task="Find all soldering defects and analyze quality"
)

print(result)
```

---

## 性能指标

在 UniPCB 基准测试上的预期性能：

| 场景 | 指标 | PCB-GPT | 次优模型 |
|------|------|---------|---------|
| Component Detection | mAP | 待公布 | - |
| Defect Localization | Precision@1 | 待公布 | - |
| Quality Analysis | BLEU | 待公布 | - |

*完整评估结果将在论文中稿后发布*

---

## 下载（暂未开放）

模型权重将在论文中稿后通过以下方式发布：
- Hugging Face Hub
- Google Drive / OneDrive
- 国内镜像（待定）

---

## 引用

```bibtex
@article{sun2026unipcb,
  title={UniPCB: A Unified Vision-Language Benchmark for Open-Ended PCB Quality Inspection},
  author={Sun, Fuxiang and Jiang, Xi and Wu, Jiansheng and Zhang, Haigang and Zheng, Feng and Yang, Jinfeng},
  journal={arXiv preprint arXiv:2601.19222},
  year={2026}
}
```
