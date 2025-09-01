# AI续写红楼梦 - 项目文档

## 项目概述
本项目使用人工智能技术续写《红楼梦》的后续情节，致力于保持原著的艺术风格和文化内涵。

## 主要功能
- 基于现有80回文本进行深度分析
- 生成81回及以后的故事内容
- 保持古典文学的语言风格
- 提供多种续写方案

## 使用方法
1. 安装依赖：`pip install -r requirements.txt`
2. 配置参数：修改 `config/settings.yaml`
3. 运行分析：`python src/analyze_text.py`
4. 生成续写：`python src/generate_continuation.py`

## 文件结构
```
├── config/          # 配置文件
├── data/           # 数据文件
├── docs/           # 项目文档
├── memory-bank/    # 项目记忆库
├── scripts/        # 工具脚本
├── src/            # 源代码
└── tests/          # 测试文件
```

## 技术栈
- Python 3.8+
- Transformers
- PyTorch
- YAML配置
