# AI续写红楼梦 🏮

基于Google ADK的多Agent架构AI续写红楼梦项目，使用GPT-5模型生成古典文学风格的续写内容。

## ✨ 项目特色

- 🤖 **多Agent架构**: 采用5个专门化Agent协同工作
- 📚 **古典文学专家**: 深度理解红楼梦风格和人物特征
- 🎯 **智能续写**: 支持用户自定义理想结局
- 📊 **质量评估**: 多维度质量评分和改进建议
- 🚀 **端到端体验**: 从输入到输出的完整AI创作流程

## 🏗️ 技术架构

### Agent架构
```
用户交互Agent → 协调各Agent工作
    ├── 数据预处理Agent: 文本分析和知识提取
    ├── 续写策略Agent: 情节规划和策略制定
    ├── 内容生成Agent: 古典文学内容创作
    └── 质量校验Agent: 内容审核和评分
```

### 技术栈
- **框架**: Google ADK (Agent Development Kit)
- **模型**: GPT-5 with 100k context window
- **语言**: Python 3.8+
- **存储**: SQLite本地数据库
- **处理**: jieba中文分词, scikit-learn轻量级ML

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip包管理器
- GPT-5 API访问权限

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd AI-Agent-Dream-of-the-Red-Chamber
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置API密钥**
编辑 `config/settings.yaml` 文件：
```yaml
adk:
  base_url: "your-gpt5-base-url"
  api_key: "your-api-key"
```

4. **运行项目**
```bash
python src/main.py
```

## 📖 使用指南

### 基本用法
```python
from src.agents.user_interface import UserInterfaceAgent

# 创建用户交互Agent
ui_agent = UserInterfaceAgent()

# 输入理想结局
ideal_ending = "宝玉和黛玉终成眷属，贾府中兴"

# 开始续写
result = ui_agent.continue_dream_of_red_chamber(ideal_ending)
print(result)
```

### 高级配置
- 修改 `config/settings.yaml` 调整Agent参数
- 查看 `docs/README.md` 了解详细配置选项
- 运行 `python scripts/test_agents.py` 测试各Agent功能

## 📁 项目结构

```
AI-Agent-Dream-of-the-Red-Chamber/
├── config/                 # 配置文件
│   └── settings.yaml      # 主要配置
├── data/                  # 数据文件
│   ├── raw/              # 原始数据
│   └── processed/        # 处理后数据
├── src/                   # 源代码
│   ├── agents/           # Agent实现
│   ├── utils/            # 工具函数
│   └── main.py           # 主入口
├── tests/                 # 测试文件
├── docs/                  # 项目文档
├── scripts/               # 工具脚本
├── memory-bank/           # 项目记忆库
├── output/                # 输出结果
└── requirements.txt       # 依赖列表
```

## 🎯 核心功能

### 1. 智能情节规划
- 基于原著分析自动生成续写大纲
- 支持用户自定义结局倾向
- 确保情节连贯性和逻辑性

### 2. 古典文学风格
- 深度学习红楼梦语言特征
- 生成古风雅致的文学作品
- 保持人物性格的一致性

### 3. 质量保障体系
- 多维度质量评估（风格、人物、情节、文学性）
- 自动生成改进建议
- 可配置的质量阈值

### 4. 用户友好界面
- 简单的命令行接口
- 实时进度显示
- 详细的质量报告

## 📊 质量评估标准

| 维度 | 权重 | 评估内容 |
|------|------|----------|
| 风格一致性 | 30% | 古风文学特点、文辞优雅程度 |
| 人物性格 | 30% | 角色特征准确性、发展合理性 |
| 情节合理性 | 25% | 故事逻辑、与原著符合程度 |
| 文学素养 | 15% | 修辞手法、意境营造 |

## 🗓️ 开发计划

- **Day 1-2**: 技术验证和架构设计 ✅
- **Day 3-5**: 核心Agent开发
- **Day 6-7**: 系统集成和测试
- **Day 8-9**: 优化和完善
- **Day 10**: 最终发布

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- 感谢Google ADK团队提供优秀的Agent开发框架
- 感谢所有为古典文学AI研究做出贡献的研究者
- 特别感谢红楼梦这部伟大著作及其作者曹雪芹

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送 Pull Request
- 邮箱: [your-email@example.com]

---

*"满纸荒唐言，一把辛酸泪。都云作者痴，谁解其中味？"* - 曹雪芹《红楼梦》