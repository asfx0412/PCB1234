# 贡献指南

感谢你对 UniPCB 项目的兴趣！我们欢迎各种形式的贡献。

---

## 🤝 如何贡献

### 1. 报告问题
发现 Bug 或有功能建议？请创建 [Issue](https://github.com/fuxiangSun/UniPCB/issues)。

### 2. 提交代码
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 3. 改进文档
文档同样重要！帮助改进 README、教程或 API 文档。

---

## 📋 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/fuxiangSun/UniPCB.git
cd UniPCB

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装开发依赖
pip install -e ".[dev]"
```

---

## 🧪 代码质量

### 运行测试
```bash
pytest tests/ -v
```

### 代码格式化
```bash
# 格式化代码
black src/ examples/ tests/

# 排序导入
isort src/ examples/ tests/

# 检查代码风格
flake8 src/ examples/ tests/
```

### 类型检查
```bash
mypy src/
```

---

## 📝 提交规范

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式（不影响功能）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```bash
git commit -m "feat: add defect localization metrics"
git commit -m "fix: resolve data loading bug"
```

---

## 📖 文档贡献

### 添加示例
在 `examples/` 目录添加使用示例：
```python
"""
Example: Component Detection

Demonstrates how to use UniPCB for component detection.
"""
```

### 改进文档
在 `docs/` 目录添加或更新文档。

---

## 🔍 代码审查流程

1. 所有 PR 需要至少一位维护者审查
2. 确保所有测试通过
3. 代码符合风格指南
4. 添加必要的文档和测试

---

## 💬 社区准则

- 保持友好和尊重
- 欢迎不同背景的贡献者
- 建设性反馈
- 遵守 [Code of Conduct](CODE_OF_CONDUCT.md)

---

## 📧 联系方式

- Issues: [GitHub Issues](https://github.com/fuxiangSun/UniPCB/issues)
- Email: sfx076@163.com

---

感谢你的贡献！🎉
