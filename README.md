# AI续写红楼梦 🏮

基于多Agent架构的AI续写《红楼梦》项目，使用Google ADK框架和大语言模型（GPT-5/Gemini）生成古典文学风格的续写内容。

> 🎯 **项目目标**：让AI根据用户提供的理想结局，续写《红楼梦》第81-120回，保持古典文学风格和人物性格一致性。

---

## 📋 目录

- [项目特色](#-项目特色)
- [系统架构](#-系统架构)
- [目录结构](#-目录结构)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [配置说明](#-配置说明)
- [Agent详解](#-agent详解)
- [技术实现](#-技术实现)
- [质量评估](#-质量评估)
- [开发文档](#-开发文档)
- [许可证](#-许可证)

---

## ✨ 项目特色

- 🤖 **多Agent协作架构**：6个专门化Agent协同工作，各司其职
- 📚 **古典文学专家**：深度理解红楼梦风格、人物特征和叙事结构
- 🎯 **智能续写**：支持用户自定义理想结局，AI自动规划情节发展
- 📊 **质量评估**：多维度质量评分和迭代改进机制
- 🔄 **迭代优化**：基于质量反馈自动重新生成，确保输出质量
- 🚀 **双引擎支持**：同时支持自定义Orchestrator和Google ADK标准实现

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户输入                               │
│                   (理想结局 + 续写参数)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   OrchestratorAgent                          │
│                     (总协调器)                                │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  负责协调各Agent的工作流程，管理数据流转和错误恢复      │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ DataProcessor │ │ Strategy      │ │ Chapter       │
│ Agent         │ │ Planner Agent │ │ Planner Agent │
│ (数据预处理)   │ │ (策略规划)     │ │ (章节规划)     │
│               │ │               │ │               │
│ • 分析前80回   │ │ • 兼容性检查   │ │ • 全局结构     │
│ • 提取人物关系 │ │ • 总体策略     │ │ • 章节详情     │
│ • 情节脉络     │ │ • 人物弧线     │ │ • 角色分配     │
└───────────────┘ └───────────────┘ └───────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   ContentGeneratorAgent                      │
│                     (内容生成Agent)                          │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  基于章节规划生成古典文学风格的续写内容                  │   │
│   │  • 保持语言风格一致  • 人物性格准确  • 情节连贯         │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   QualityCheckerAgent                        │
│                     (质量校验Agent)                          │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  多维度评估  →  改进建议  →  迭代优化                   │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        输出结果                               │
│              (续写章节 + 质量报告 + 策略大纲)                  │
└─────────────────────────────────────────────────────────────┘
```

### 数据流转

```
Phase 1: 数据准备     → DataProcessorAgent    → knowledge_base
Phase 2: 策略规划     → StrategyPlannerAgent  → overall_strategy
Phase 3: 章节编排     → ChapterPlannerAgent   → chapters_plan
Phase 4: 内容生成     → ContentGeneratorAgent → chapter_content
Phase 5: 质量检验     → QualityCheckerAgent   → quality_report
Phase 6: 迭代优化     → (质量不达标则重新生成)
```

### Agent通信机制

项目实现了完整的Agent间通信总线（`AgentCommunicationBus`），支持：
- 📨 **反馈消息**：Agent间的质量反馈
- 🔄 **修订请求**：请求其他Agent重新处理
- ⚠️ **质量警报**：质量不达标时的紧急通知
- 📢 **状态广播**：Agent状态更新通知

---

## 📁 目录结构

```
AI-Agent-Dream-of-the-Red-Chamber/
├── config/                          # 配置文件目录
│   ├── .env.example                 # 环境变量示例
│   └── settings.yaml                # 主配置文件
│
├── data/                            # 数据目录
│   ├── raw/                         # 原始数据
│   │   └── hongloumeng_80.md        # 红楼梦前80回原文
│   ├── processed/                   # 处理后的数据
│   │   └── chapters/                # 按章节分割的文件
│   │       ├── chapter_001.md
│   │       ├── chapter_002.md
│   │       └── ... (共80个章节)
│   └── knowledge_base.db            # 知识库数据库
│
├── docs/                            # 项目文档
│   ├── README.md                    # 文档索引
│   ├── CONFIGURATION.md             # 配置说明
│   ├── TECHNICAL_DESIGN_V2.md       # V2技术设计文档
│   ├── CHAPTER_PLANNER_*.md         # 章节规划Agent文档
│   ├── CONTENT_GENERATOR_V2_*.md    # 内容生成Agent文档
│   ├── ORCHESTRATOR_V2_*.md         # 编排Agent文档
│   └── V2_*.md                      # V2版本相关文档
│
├── src/                             # 源代码目录
│   ├── __init__.py
│   ├── __main__.py                  # 程序入口
│   │
│   ├── agents/                      # Agent实现
│   │   ├── __init__.py
│   │   ├── base.py                  # 基础Agent类 & AgentResult
│   │   ├── orchestrator.py          # 编排Agent（总协调器）
│   │   ├── communication.py         # Agent通信总线
│   │   ├── gpt5_client.py           # GPT-5 API客户端
│   │   │
│   │   ├── real/                    # 真实Agent实现
│   │   │   ├── __init__.py
│   │   │   ├── data_processor_agent.py      # 数据预处理Agent
│   │   │   ├── strategy_planner_agent.py    # 策略规划Agent
│   │   │   ├── chapter_planner_agent.py     # 章节规划Agent (V2新增)
│   │   │   ├── content_generator_agent.py   # 内容生成Agent
│   │   │   └── quality_checker_agent.py     # 质量校验Agent
│   │   │
│   │   ├── adk_agents.py            # Google ADK Agent封装
│   │   ├── adk_agents_minimal.py    # 最小化ADK实现
│   │   ├── adk_agents_simple.py     # 简化版ADK实现
│   │   └── adk_agents_standard.py   # 标准ADK实现
│   │
│   ├── cli/                         # 命令行界面
│   │   ├── __init__.py
│   │   └── main.py                  # CLI主程序
│   │
│   ├── config/                      # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py              # Settings配置类
│   │
│   ├── prompts/                     # Prompt模板
│   │   ├── __init__.py
│   │   └── literary_prompts.py      # 古典文学创作Prompt
│   │
│   └── utils/                       # 工具模块
│       └── cache.py                 # 缓存管理器
│
├── tests/                           # 测试文件
│   ├── test_chapter_planner.py      # 章节规划Agent测试
│   ├── test_orchestrator_v2.py      # 编排Agent测试
│   └── test_v2_3_chapters.py        # V2集成测试
│
├── output/                          # 输出目录
│   └── [生成的续写结果]
│
├── requirements.txt                 # Python依赖
├── README.md                        # 项目说明
├── OPTIMIZATION_LOG.md              # 优化日志
└── test_optimization.py             # 优化测试
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器
- OpenAI API 访问权限（或兼容的API服务）

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

创建 `config/.env` 文件：
```bash
cp config/.env.example config/.env
```

编辑 `config/.env`：
```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://your-api-endpoint
```

4. **验证安装**
```bash
python -m src status
```

5. **开始续写**
```bash
python -m src continue-story "宝玉和黛玉终成眷属，贾府中兴"
```

---

## 📖 使用指南

### CLI命令

#### 续写故事（标准模式）
```bash
# 基本用法
python -m src continue-story "你的理想结局"

# 指定参数
python -m src continue-story "宝黛终成眷属" \
    --start-chapter 81 \    # 起始回数（默认81）
    --count 3 \             # 续写回数（默认1）
    --quality 7.5 \         # 质量阈值（默认7.0）
    --verbose               # 详细输出
```

#### 续写故事（Google ADK模式）
```bash
python -m src continue-story-adk "宝黛终成眷属" --count 1
```

#### 交互模式
```bash
python -m src interactive
```

#### 查看系统状态
```bash
python -m src status
```

### Python API

```python
from src.config.settings import Settings
from src.agents.orchestrator import OrchestratorAgent

# 初始化
settings = Settings()
orchestrator = OrchestratorAgent(settings)

# 执行续写
import asyncio

async def main():
    result = await orchestrator.continue_dream_of_red_chamber(
        ending="宝玉和黛玉终成眷属，贾府中兴",
        chapters=3,
        quality_threshold=7.5
    )
    
    if result.success:
        # 保存结果
        output_dir = orchestrator.save_results(result)
        print(f"结果已保存至: {output_dir}")

asyncio.run(main())
```

### 使用Google ADK

```python
from src.config.settings import Settings
from src.agents.adk_agents_standard import create_hongloumeng_adk_system

settings = Settings()
adk_system = create_hongloumeng_adk_system(settings)

async def main():
    result = await adk_system.process_continuation_request(
        user_ending="宝黛终成眷属",
        chapters=1
    )
    print(result)

asyncio.run(main())
```

---

## ⚙️ 配置说明

### 主配置文件 (`config/settings.yaml`)

```yaml
# 项目基本信息
project:
  name: "AI续写红楼梦"
  version: "1.0.0"

# ADK配置
adk:
  enabled: true
  model_provider: "openai"
  context_window: 100000

# Agent配置
agents:
  data_processor:
    name: "数据预处理Agent"
    model: "minimaxai/minimax-m2.1"
    temperature: 0.3
    max_tokens: 2000

  strategy_planner:
    name: "续写策略Agent"
    model: "minimaxai/minimax-m2.1"
    temperature: 0.7
    max_tokens: 4000

  content_generator:
    name: "内容生成Agent"
    model: "minimaxai/minimax-m2.1"
    temperature: 0.8
    max_tokens: 8000

  quality_checker:
    name: "质量校验Agent"
    model: "minimaxai/minimax-m2.1"
    temperature: 0.4
    max_tokens: 3000

# 生成配置
generation:
  chapters_to_generate: 40
  words_per_chapter: 2500
  literary_requirements: "古风文学风格、文辞优雅、人物性格一致"

# 质量评估配置
quality:
  style_weight: 0.3           # 风格一致性权重
  character_weight: 0.3       # 人物性格权重
  plot_weight: 0.25           # 情节合理性权重
  literary_weight: 0.15       # 文学素养权重
  min_score_threshold: 7.0    # 最低通过分数
```

### 环境变量 (`config/.env`)

```env
# OpenAI API配置
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

# 调试模式
DEBUG_MODE=false
LOG_LEVEL=INFO
```

---

## 🤖 Agent详解

### 1. OrchestratorAgent（编排Agent）

**职责**：总协调器，管理整个续写流程

**核心功能**：
- 验证用户输入
- 并行调度数据预处理和策略规划
- 协调章节规划和内容生成
- 管理迭代优化循环
- 保存输出结果

**关键方法**：
```python
async def process(input_data) -> AgentResult     # 执行完整续写流程
async def continue_dream_of_red_chamber(...)     # 主入口方法
def save_results(results) -> str                 # 保存结果到文件
```

### 2. DataProcessorAgent（数据预处理Agent）

**职责**：分析红楼梦前80回，构建知识库

**输出数据**：
```python
{
    "characters": {...},          # 人物信息
    "relationships": {...},       # 人物关系
    "plotlines": {...},          # 情节脉络
    "themes": [...],             # 主题列表
    "text_statistics": {...}     # 文本统计
}
```

### 3. StrategyPlannerAgent（策略规划Agent）

**职责**：制定续写总体策略

**输出数据**：
```python
{
    "user_ending": "...",              # 用户理想结局
    "compatibility_check": {...},      # 兼容性检查
    "overall_strategy": {...},         # 总体策略
    "plot_outline": [...],             # 情节大纲
    "character_arcs": {...},           # 人物发展弧线
    "theme_development": {...}         # 主题发展
}
```

### 4. ChapterPlannerAgent（章节规划Agent）🆕

**职责**：为81-120回设计详细的章节编排方案

**核心模块**：
- 全局结构规划器（四阶段划分）
- 单章详细规划器
- 角色分配器
- 连贯性验证器

**输出数据**：
```python
{
    "metadata": {...},                # 元数据
    "global_structure": {
        "narrative_phases": {...},    # 叙事阶段
        "major_plotlines": [...]      # 主要剧情线
    },
    "chapters": [                     # 各章节详情
        {
            "chapter_number": 81,
            "chapter_title": {...},
            "main_characters": [...],
            "main_plot_points": [...],
            "literary_elements": {...}
        }
    ],
    "character_distribution": {...},   # 角色分布统计
    "validation": {...}               # 连贯性验证结果
}
```

### 5. ContentGeneratorAgent（内容生成Agent）

**职责**：基于章节规划生成古典文学风格内容

**特点**：
- 使用专业的古典文学Prompt
- 支持迭代改进（基于质量反馈）
- 保持语言风格和人物性格一致

### 6. QualityCheckerAgent（质量校验Agent）

**职责**：多维度评估生成内容质量

**评估维度**：

| 维度 | 权重 | 评估内容 |
|------|------|----------|
| 风格一致性 | 30% | 古风文学特点、文辞优雅程度 |
| 人物性格 | 30% | 角色特征准确性、发展合理性 |
| 情节合理性 | 25% | 故事逻辑、与原著符合程度 |
| 文学素养 | 15% | 修辞手法、意境营造 |

---

## 🔧 技术实现

### 核心技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 主要编程语言 |
| Google ADK | Agent开发框架 |
| OpenAI API | 大语言模型调用 |
| jieba | 中文分词 |
| SQLite | 本地知识库 |
| Click | CLI框架 |
| Rich | 终端美化 |
| YAML | 配置文件 |

### 关键设计模式

1. **Agent模式**：每个Agent专注于特定任务，通过统一接口协作
2. **策略模式**：Prompt模板可配置，支持不同的生成策略
3. **观察者模式**：Agent通信总线实现消息发布/订阅
4. **工厂模式**：通过配置动态创建Agent实例

### Prompt管理系统

项目实现了完整的Prompt模板系统（`LiteraryPrompts`），包含：
- `strategy_planner`：续写策略规划
- `content_generator`：古典文学内容创作
- `quality_checker`：文学质量评估
- `data_processor`：红楼梦知识分析
- `chapter_planner_global`：全局章节结构规划
- `chapter_planner_detail`：单章详细规划
- `chapter_planner_detail_v2`：简化版章节规划

---

## 📊 质量评估

### 评分标准

```
优秀 (9-10分)：达到古典文学大师水平
良好 (7-8分) ：符合古典小说基本要求
合格 (5-6分) ：基本可读，但有明显不足
不合格 (0-4分)：严重偏离古典文学标准
```

### 迭代优化机制

1. 生成初始内容
2. 质量评估（多维度评分）
3. 如果分数 < 阈值，基于反馈重新生成
4. 最多迭代3次
5. 返回最终结果和质量报告

### 输出示例

```
output/
└── red_chamber_continuation_20260131_143000/
    ├── summary.json           # 结果摘要
    ├── details.json           # 详细数据
    ├── strategy_outline.md    # 策略大纲
    ├── quality_report.md      # 质量报告
    └── chapters/
        ├── chapter_081.md     # 第81回
        ├── chapter_082.md     # 第82回
        └── ...
```

---

## 📚 开发文档

详细的技术文档请查看 `docs/` 目录：

| 文档 | 说明 |
|------|------|
| [TECHNICAL_DESIGN_V2.md](docs/TECHNICAL_DESIGN_V2.md) | V2技术设计方案 |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | 配置详细说明 |
| [CHAPTER_PLANNER_*.md](docs/) | 章节规划Agent文档 |
| [V2_PLAN_SUMMARY.md](docs/V2_PLAN_SUMMARY.md) | V2计划总结 |

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_chapter_planner.py -v

# 运行V2集成测试
pytest tests/test_v2_3_chapters.py -v
```

---

## 🗓️ 开发计划

- [x] Day 1-2: 技术验证和架构设计
- [x] Day 3-5: 核心Agent开发
- [x] Day 6-7: 系统集成和测试
- [x] V2: 新增ChapterPlannerAgent
- [x] V2: 迭代优化机制
- [ ] 优化Prompt提高质量
- [ ] Web界面开发
- [ ] 完整40回生成测试

---

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- 感谢Google ADK团队提供优秀的Agent开发框架
- 感谢OpenAI提供强大的语言模型能力
- 感谢所有为古典文学AI研究做出贡献的研究者
- 特别感谢《红楼梦》这部伟大著作及其作者曹雪芹

---

*"满纸荒唐言，一把辛酸泪。都云作者痴，谁解其中味？"* — 曹雪芹《红楼梦》
