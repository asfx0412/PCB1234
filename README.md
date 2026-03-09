# UniPCB

[![arXiv](https://img.shields.io/badge/arXiv-2601.19222-b31b1b.svg)](https://arxiv.org/abs/2601.19222)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**UniPCB: A Unified Vision-Language Benchmark for Open-Ended PCB Quality Inspection**

首个统一的视觉 - 语言基准测试，用于开放式印刷电路板（PCB）质量检测。

---

## 📖 简介

多模态大语言模型（MLLMs）在通用工业质量检测中展现出潜力，但在复杂场景（如 PCB 检测）中表现不足。PCB 检测由于组件密集、布线结构复杂和缺陷模式细微，需要专门的领域专业知识。

**UniPCB** 填补了这一空白，提供：
- 🎯 首个统一的 PCB 视觉 - 语言基准测试
- 📊 三个标注场景的系统化数据集
- 🤖 PCB-GPT：专为 PCB 检测优化的多模态大语言模型
- 📈 细粒度缺陷定位评估框架

## 🚀 主要特性

- **统一基准**：标准化来自不同来源的 PCB 检测数据
- **渐进式课程学习**：模仿人类专家学习过程的训练策略
- **多任务评估**：支持缺陷检测、定位、分析等多种任务
- **开放接口**：易于扩展和自定义

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/fuxiangSun/UniPCB.git
cd UniPCB

# 安装依赖
pip install -r requirements.txt

# 安装为可编辑包（可选）
pip install -e .
```

## 🎯 快速开始

### 1. 数据准备

```python
from unipcb.data import UniPCBDataset

# 加载数据集
dataset = UniPCBDataset(
    data_path="data/",
    scenario="component_detection",  # 或 "defect_localization", "quality_analysis"
    split="train"
)
```

### 2. 模型推理

```python
from unipcb.models import PCBGPT

# 加载模型（模型权重将在论文中稿后发布）
model = PCBGPT.from_pretrained("pcb-gpt-base")

# 推理示例
result = model.inspect(
    image="examples/pcb_sample.jpg",
    task="Find all soldering defects"
)
```

### 3. 评估

```python
from unipcb.eval import UniPCBEvaluator

# 运行评估
evaluator = UniPCBEvaluator()
metrics = evaluator.evaluate(
    model=model,
    dataset=test_dataset
)
```

更多示例请查看 [examples/](examples/) 目录。

## 📊 基准测试

UniPCB 包含三个核心评估场景：

| 场景 | 任务类型 | 评估指标 |
|------|---------|---------|
| Component Detection | 元件检测与识别 | mAP, Accuracy |
| Defect Localization | 缺陷定位 | Precision@K, IoU |
| Quality Analysis | 质量分析 | BLEU, ROUGE, Domain-Score |

## 📁 项目结构

```
UniPCB/
├── README.md              # 本文件
├── LICENSE                # MIT 许可证
├── requirements.txt       # Python 依赖
├── setup.py               # 安装包配置
├── src/
│   └── unipcb/
│       ├── models/        # 模型定义（PCB-GPT 等）
│       ├── data/          # 数据加载与处理
│       ├── eval/          # 评估脚本
│       └── utils/         # 工具函数
├── examples/              # 使用示例
├── docs/                  # 详细文档
├── configs/               # 配置文件
├── data/                  # 数据目录
│   ├── README.md          # 数据说明（待补充）
│   └── models/            # 模型权重（待补充）
└── tests/                 # 单元测试
```

## 📝 引用

如果您在研究中使用了 UniPCB，请引用我们的论文：

```bibtex
@article{sun2026unipcb,
  title={UniPCB: A Unified Vision-Language Benchmark for Open-Ended PCB Quality Inspection},
  author={Sun, Fuxiang and Jiang, Xi and Wu, Jiansheng and Zhang, Haigang and Zheng, Feng and Yang, Jinfeng},
  journal={arXiv preprint arXiv:2601.19222},
  year={2026}
}
```

## 📅 发布计划

- [x] 项目框架与文档
- [ ] 基准测试评估代码
- [ ] 数据处理管道
- [ ] PCB-GPT 模型代码（待论文中稿后发布）
- [ ] 预训练模型权重（待论文中稿后发布）
- [ ] 完整指令数据集（待论文中稿后发布）

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与。

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 📧 Email: sfx076@163.com
- 🐛 Issues: [GitHub Issues](https://github.com/fuxiangSun/UniPCB/issues)

## 📜 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

<p align="center">
  <i>⭐ 如果这个项目对你有帮助，请给一个 Star！</i>
</p>
