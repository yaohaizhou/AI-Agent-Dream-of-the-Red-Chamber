# AI续写红楼梦 - 技术方案V2.0

> **文档版本**: V2.0  
> **创建日期**: 2025-09-30  
> **状态**: 设计阶段  
> **作者**: heai

---

## 📋 文档目录

1. [当前系统问题分析](#1-当前系统问题分析)
2. [核心改进方案](#2-核心改进方案)
3. [新增章节规划Agent设计](#3-新增章节规划agent设计)
4. [多Agent架构重构](#4-多agent架构重构)
5. [数据流程设计](#5-数据流程设计)
6. [技术实现细节](#6-技术实现细节)
7. [开发计划](#7-开发计划)

---

## 1. 当前系统问题分析

### 1.1 核心问题识别

#### ❌ **问题1: 缺乏整体章节规划**
- **现象**: 生成的81、82回使用了续写版原有标题
- **根本原因**: 没有独立的章节编排Agent，缺乏全局视野
- **影响**: 
  - 无法保证40回的整体连贯性
  - 无法合理分配主要角色和剧情线
  - 章节标题和内容可能重复或不协调

#### ❌ **问题2: Strategy Planner Agent职责不清**
- **现状**: 当前的`StrategyPlannerAgent`承担了过多职责
- **问题**:
  - 既要做兼容性检查
  - 又要设计情节大纲
  - 还要规划人物弧线
  - 功能耦合度高，难以维护
- **证据**: 从`strategy_outline.md`看到只有一个章节的简单规划

#### ❌ **问题3: 缺乏章节级别的精细规划**
- **当前**: 只有宏观策略，没有每回的详细规划
- **需要**: 
  - 每回的主要角色列表
  - 每回的主要剧情点
  - 每回的情节定位（起承转合）
  - 每回与整体的关联

#### ❌ **问题4: 数据流程不清晰**
- **问题**: Agent之间的数据传递缺乏结构化设计
- **影响**: 后续Agent无法获得足够的上下文信息

---

## 2. 核心改进方案

### 2.1 总体设计思路

```
用户输入理想结局
    ↓
【新增】章节规划Agent (Chapter Planner)
    ↓
生成81-120回完整编排方案
    - 每回标题
    - 每回主要角色
    - 每回主要剧情
    - 每回在整体中的定位
    ↓
内容生成Agent (逐回生成)
    ↓
质量检验Agent (逐回检验)
```

### 2.2 Agent职责重新划分

| Agent | 原职责 | 新职责 | 变化 |
|-------|--------|--------|------|
| **Data Processor** | 分析前80回 | 分析前80回 | ✅ 保持 |
| **Strategy Planner** | 策略+大纲+人物弧线 | 仅制定总体策略方向 | 🔄 简化 |
| **Chapter Planner** | ❌ 不存在 | 详细规划81-120回编排 | ➕ **新增** |
| **Content Generator** | 生成内容 | 基于章节规划生成内容 | 🔄 增强 |
| **Quality Checker** | 质量检验 | 质量检验+章节一致性检查 | 🔄 增强 |

---

## 3. 新增章节规划Agent设计

### 3.1 Agent基本信息

```yaml
名称: ChapterPlannerAgent (章节规划Agent)
定位: 承上启下的核心规划Agent
输入: 
  - 用户理想结局
  - 前80回分析数据
  - 总体续写策略
输出: 
  - 81-120回完整编排方案
  - 每回详细规划数据
```

### 3.2 核心功能模块

#### 模块1: 全局章节编排器 (Global Chapter Organizer)

**职责**: 规划40回的整体结构

**输出结构**:
```python
{
    "total_chapters": 40,
    "start_chapter": 81,
    "end_chapter": 120,
    "narrative_structure": {
        "setup": [81-85],      # 铺垫阶段
        "development": [86-100], # 发展阶段
        "climax": [101-115],    # 高潮阶段
        "resolution": [116-120]  # 结局阶段
    },
    "major_plotlines": [
        {
            "name": "宝黛爱情线",
            "chapters": [81,83,85,88,92,95,98,102,105,110,115],
            "arc": "考验→冲突→高潮→结局"
        },
        {
            "name": "贾府衰败线",
            "chapters": [82,86,90,94,98,103,108,112,117,120],
            "arc": "预兆→危机→崩溃→覆灭"
        }
        // ... 更多剧情线
    ]
}
```

#### 模块2: 单章详细规划器 (Chapter Detail Planner)

**职责**: 为每一回生成详细规划

**输出结构**:
```python
{
    "chapter_number": 81,
    "chapter_title": {
        "first_part": "占旺相四美钓游鱼",
        "second_part": "奉严词两番入家塾"
    },
    "narrative_phase": "setup",  # setup/development/climax/resolution
    "main_characters": [
        {
            "name": "贾宝玉",
            "role": "protagonist",  # protagonist/antagonist/supporting
            "importance": "primary",  # primary/secondary/minor
            "key_scenes": ["游园", "读书"],
            "emotional_arc": "轻松愉悦 → 受到警醒"
        },
        {
            "name": "林黛玉",
            "role": "protagonist",
            "importance": "secondary",
            "key_scenes": ["咏诗", "思念"],
            "emotional_arc": "平静 → 忧虑"
        }
        // ... 3-5个主要角色
    ],
    "main_plot_points": [
        {
            "sequence": 1,
            "event": "宝玉与姐妹们游园钓鱼",
            "type": "daily_life",  # daily_life/conflict/turning_point/climax
            "duration": "半日",
            "location": "大观园",
            "participants": ["贾宝玉", "史湘云", "薛宝钗"]
        },
        {
            "sequence": 2,
            "event": "贾政训斥宝玉，命其进家塾苦读",
            "type": "conflict",
            "duration": "一个时辰",
            "location": "荣禧堂",
            "participants": ["贾宝玉", "贾政"]
        }
        // ... 3-5个主要情节点
    ],
    "subplot_connections": [
        {
            "plotline": "宝黛爱情线",
            "progress": "宝玉读书减少了与黛玉相处时间，埋下矛盾"
        },
        {
            "plotline": "贾府衰败线",
            "progress": "贾政焦虑家族前途，加强对宝玉的管教"
        }
    ],
    "literary_elements": {
        "poetry_count": 2,  # 本回需要的诗词数量
        "symbolism": ["钓鱼象征人生机遇", "家塾象征束缚"],
        "foreshadowing": ["暗示宝玉未来的抉择"],
        "mood": "轻松转严肃"
    },
    "chapter_length_estimate": 2500,  # 预估字数
    "previous_chapter_link": "承接第80回宝玉的日常",
    "next_chapter_setup": "为第82回黛玉的反应做铺垫"
}
```

#### 模块3: 角色分配器 (Character Distributor)

**职责**: 确保主要角色在40回中合理分布

**功能**:
- 统计每个主要角色的出场频率
- 确保重要角色有足够的戏份
- 避免某些角色长期缺席
- 平衡群像戏与主角戏

**输出示例**:
```python
{
    "character_distribution": {
        "贾宝玉": {
            "total_appearances": 40,
            "primary_role_chapters": [81,83,85,88,...],  # 35回
            "secondary_role_chapters": [82,84,86,...],   # 5回
            "absent_chapters": []  # 全勤
        },
        "林黛玉": {
            "total_appearances": 38,
            "primary_role_chapters": [81,83,85,...],  # 30回
            "secondary_role_chapters": [82,87,91,...],  # 8回
            "absent_chapters": [95,103]  # 2回（可能因病或情节需要）
        }
        // ... 其他主要角色
    }
}
```

---

## 4. 多Agent架构重构

### 4.1 新架构流程图

```
┌─────────────────────────────────────────────────────┐
│                  OrchestratorAgent                   │
│                    (总协调器)                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ├─→ Phase 1: 数据准备阶段
                   │   └─→ DataProcessorAgent
                   │       输出: knowledge_base (前80回分析)
                   │
                   ├─→ Phase 2: 策略规划阶段  
                   │   └─→ StrategyPlannerAgent (简化版)
                   │       输入: user_ending + knowledge_base
                   │       输出: overall_strategy (总体策略)
                   │
                   ├─→ Phase 3: 章节编排阶段 【新增】
                   │   └─→ ChapterPlannerAgent
                   │       输入: overall_strategy + knowledge_base
                   │       输出: chapters_plan (81-120回编排)
                   │
                   ├─→ Phase 4: 内容生成阶段 (循环40次)
                   │   └─→ ContentGeneratorAgent
                   │       输入: chapters_plan[i] + previous_content
                   │       输出: chapter_content[i]
                   │
                   └─→ Phase 5: 质量检验阶段 (循环40次)
                       └─→ QualityCheckerAgent
                           输入: chapter_content[i] + chapters_plan[i]
                           输出: quality_report[i]
```

### 4.2 数据流转设计

#### 阶段1: 数据准备
```python
knowledge_base = {
    "characters": {...},
    "relationships": {...},
    "plotlines": {...},
    "themes": {...},
    "style_features": {...}
}
```

#### 阶段2: 策略规划
```python
overall_strategy = {
    "user_ending": "...",
    "compatibility_score": 0.95,
    "narrative_approach": "渐进式发展",
    "major_themes": [...],
    "character_fates": {...}
}
```

#### 阶段3: 章节编排
```python
chapters_plan = {
    "global_structure": {...},  # 全局结构
    "chapters": [
        {chapter_81_detail},
        {chapter_82_detail},
        ...
        {chapter_120_detail}
    ]
}
```

#### 阶段4-5: 逐回生成与检验
```python
for chapter_num in range(81, 121):
    chapter_plan = chapters_plan["chapters"][chapter_num - 81]
    
    # 生成内容
    content = await content_generator.process({
        "chapter_plan": chapter_plan,
        "previous_chapters": generated_chapters,
        "overall_strategy": overall_strategy
    })
    
    # 质量检验
    quality = await quality_checker.process({
        "content": content,
        "chapter_plan": chapter_plan,
        "consistency_check": True
    })
```

---

## 5. 数据流程设计

### 5.1 完整数据流示意图

```
用户输入
   ↓
[Phase 1] DataProcessor
   ↓
knowledge_base.json (保存)
   ↓
[Phase 2] StrategyPlanner
   ↓
overall_strategy.json (保存)
   ↓
[Phase 3] ChapterPlanner ⭐新增
   ↓
chapters_plan.json (保存) ← 核心数据文件
   ↓
[Phase 4] 循环: for chapter in 81..120
   ├─→ ContentGenerator
   │   输入: chapters_plan[chapter] + context
   │   输出: chapter_content.txt
   │
   └─→ QualityChecker
       输入: chapter_content + chapters_plan[chapter]
       输出: quality_report.json
```

### 5.2 核心数据文件设计

#### 文件1: `chapters_plan.json` (新增，最重要)

这是整个系统的核心数据文件，所有后续生成都基于此。

```json
{
  "metadata": {
    "version": "1.0",
    "created_at": "2025-09-30T10:00:00",
    "user_ending": "贾府衰败势如流 往昔繁华化虚无",
    "total_chapters": 40,
    "start_chapter": 81,
    "end_chapter": 120
  },
  "global_structure": {
    "narrative_phases": {
      "setup": {
        "chapters": [81, 82, 83, 84, 85],
        "description": "铺垫阶段：暗流涌动，危机初显"
      },
      "development": {
        "chapters": [86, 87, ..., 100],
        "description": "发展阶段：矛盾激化，命运转折"
      },
      "climax": {
        "chapters": [101, 102, ..., 115],
        "description": "高潮阶段：家族崩塌，人物抉择"
      },
      "resolution": {
        "chapters": [116, 117, 118, 119, 120],
        "description": "结局阶段：尘埃落定，各有归宿"
      }
    },
    "major_plotlines": [
      {
        "id": "plotline_001",
        "name": "宝黛爱情线",
        "priority": "primary",
        "chapters_involved": [81, 83, 85, 88, 92, ...],
        "narrative_arc": "相思→误会→和解→考验→悲剧/圆满",
        "key_turning_points": [
          {"chapter": 92, "event": "黛玉得知宝钗有孕"},
          {"chapter": 105, "event": "宝玉梦中与黛玉诀别"},
          {"chapter": 110, "event": "最终结局"}
        ]
      }
    ]
  },
  "chapters": [
    {
      "chapter_number": 81,
      "chapter_title": {
        "first_part": "占旺相四美钓游鱼",
        "second_part": "奉严词两番入家塾"
      },
      "narrative_phase": "setup",
      "position_in_phase": "第1回/共5回",
      "main_characters": [
        {
          "name": "贾宝玉",
          "role": "protagonist",
          "importance": "primary",
          "key_scenes": [
            {
              "scene_name": "游园钓鱼",
              "emotional_state": "轻松愉悦",
              "interactions": ["史湘云", "薛宝钗", "林黛玉"]
            },
            {
              "scene_name": "被迫读书",
              "emotional_state": "不情愿但顺从",
              "interactions": ["贾政"]
            }
          ],
          "character_development": "从自由自在到受到约束，开始感受到家族责任的压力"
        },
        {
          "name": "林黛玉",
          "role": "protagonist",
          "importance": "secondary",
          "key_scenes": [
            {
              "scene_name": "旁观游园",
              "emotional_state": "欣喜中带着忧虑",
              "interactions": ["贾宝玉（远观）"]
            }
          ],
          "character_development": "感受到宝玉被迫读书后相处时间减少的担忧"
        },
        {
          "name": "贾政",
          "role": "supporting",
          "importance": "secondary",
          "key_scenes": [
            {
              "scene_name": "训斥宝玉",
              "emotional_state": "严厉焦虑",
              "interactions": ["贾宝玉"]
            }
          ],
          "character_development": "开始意识到家族危机，加强对子女的管教"
        }
      ],
      "main_plot_points": [
        {
          "sequence": 1,
          "event": "宝玉与姐妹们在园中钓鱼游玩，一派轻松景象",
          "type": "daily_life",
          "duration": "半日",
          "location": "大观园池塘边",
          "participants": ["贾宝玉", "史湘云", "薛宝钗", "探春"],
          "significance": "表现繁华依旧的表象，实则为后续危机铺垫对比"
        },
        {
          "sequence": 2,
          "event": "贾政因外界风声，严厉训斥宝玉，命其进家塾苦读",
          "type": "conflict",
          "duration": "一个时辰",
          "location": "荣禧堂",
          "participants": ["贾宝玉", "贾政", "王夫人"],
          "significance": "暗示外部压力增大，家族开始受到影响"
        },
        {
          "sequence": 3,
          "event": "宝玉无奈入塾，黛玉独自垂泪",
          "type": "emotional_moment",
          "duration": "傍晚",
          "location": "潇湘馆",
          "participants": ["林黛玉", "紫鹃"],
          "significance": "宝黛相处时间减少，为后续矛盾埋下伏笔"
        }
      ],
      "subplot_connections": [
        {
          "plotline_id": "plotline_001",
          "plotline_name": "宝黛爱情线",
          "progress_description": "宝玉被迫读书，与黛玉相处时间骤减，黛玉心生忧虑"
        },
        {
          "plotline_id": "plotline_002",
          "plotline_name": "贾府衰败线",
          "progress_description": "贾政感受到外部压力，开始严格管教子女，预示危机来临"
        }
      ],
      "literary_elements": {
        "poetry_count": 2,
        "poetry_themes": ["游园之乐", "离别之愁"],
        "symbolism": [
          "钓鱼：象征人生机遇与得失",
          "家塾：象征封建礼教的束缚"
        ],
        "foreshadowing": [
          "贾政的焦虑暗示家族危机",
          "黛玉的忧虑预示情感波折"
        ],
        "mood_progression": "轻松欢快 → 严肃紧张 → 忧伤惆怅",
        "writing_style_notes": "前半段轻松明快，后半段笔锋转折，对比鲜明"
      },
      "chapter_metadata": {
        "estimated_length": 2500,
        "difficulty_level": "medium",
        "key_vocabulary": ["家塾", "钓游", "严词", "旺相"],
        "previous_chapter_link": "承接第80回的日常生活场景",
        "next_chapter_setup": "为第82回黛玉的进一步反应和宝钗的暗中行动做铺垫"
      }
    }
    // ... 81-120共40回的详细规划
  ]
}
```

### 5.3 数据持久化策略

```python
# 保存目录结构
output/
  └── session_20250930_100000/
      ├── 1_knowledge_base.json       # Phase 1 输出
      ├── 2_overall_strategy.json     # Phase 2 输出
      ├── 3_chapters_plan.json        # Phase 3 输出 ⭐核心
      ├── chapters/
      │   ├── chapter_081.txt
      │   ├── chapter_082.txt
      │   └── ...
      ├── quality_reports/
      │   ├── chapter_081_quality.json
      │   ├── chapter_082_quality.json
      │   └── ...
      └── final_summary.json
```

---

## 6. 技术实现细节

### 6.1 ChapterPlannerAgent 类设计

```python
class ChapterPlannerAgent(BaseAgent):
    """章节规划Agent - 负责81-120回的详细编排"""
    
    def __init__(self, settings: Settings):
        super().__init__("章节规划Agent", {"task": "章节编排"})
        self.settings = settings
        self.gpt5_client = get_gpt5_client(settings)
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        主处理流程
        
        输入:
            - overall_strategy: 总体策略
            - knowledge_base: 前80回分析数据
            - user_ending: 用户理想结局
            - chapters_count: 要规划的章节数 (默认40)
            - start_chapter: 起始章节号 (默认81)
        
        输出:
            - chapters_plan: 完整的章节编排方案
        """
        pass
    
    async def _plan_global_structure(self, strategy, knowledge_base):
        """规划全局结构（四阶段划分、主要剧情线）"""
        pass
    
    async def _plan_chapter_details(self, chapter_num, global_structure):
        """规划单个章节的详细内容"""
        pass
    
    async def _distribute_characters(self, chapters_plan):
        """分配角色，确保合理分布"""
        pass
    
    async def _validate_consistency(self, chapters_plan):
        """验证章节间的连贯性"""
        pass
```

### 6.2 Prompt设计要点

#### Prompt 1: 全局结构规划
```python
GLOBAL_STRUCTURE_PROMPT = """
你是一位精通《红楼梦》的文学规划大师。现在需要你为81-120回（共40回）设计一个完整的叙事结构。

【背景信息】
- 前80回分析: {knowledge_base_summary}
- 用户期望结局: {user_ending}
- 总体策略: {overall_strategy}

【任务要求】
1. 将40回划分为4个叙事阶段（铺垫、发展、高潮、结局），每个阶段包含的回数
2. 设计3-5条主要剧情线（如宝黛爱情线、贾府衰败线等）
3. 为每条剧情线标注涉及的章节号
4. 确保所有剧情线最终收束于用户期望的结局

【输出格式】
严格按照JSON格式输出...
"""
```

#### Prompt 2: 单章详细规划
```python
CHAPTER_DETAIL_PROMPT = """
你是一位精通《红楼梦》的章节设计师。现在需要你为第{chapter_num}回设计详细的内容规划。

【上下文信息】
- 全局结构: {global_structure}
- 本回所处阶段: {narrative_phase}
- 涉及的剧情线: {related_plotlines}
- 上一回概要: {previous_chapter_summary}

【任务要求】
1. 设计符合红楼梦风格的回目标题（对仗工整）
2. 选择3-5个主要角色，明确每个角色的戏份和情感变化
3. 设计3-5个主要情节点，确保承上启下
4. 标注文学元素（诗词、象征、伏笔等）

【输出格式】
严格按照JSON格式输出...
"""
```

### 6.3 ContentGeneratorAgent 改造

**改造要点**:
```python
# 原来
async def process(self, input_data):
    # 只有一个简单的prompt
    content = await self._generate_content(user_ending)
    
# 改造后
async def process(self, input_data):
    chapter_plan = input_data["chapter_plan"]  # ⭐详细的章节规划
    previous_chapters = input_data.get("previous_chapters", [])
    
    # 构建包含详细规划信息的prompt
    enhanced_prompt = self._build_enhanced_prompt(
        chapter_plan=chapter_plan,
        previous_summary=previous_chapters[-3:] if previous_chapters else []
    )
    
    content = await self._generate_content(enhanced_prompt)
```

**Enhanced Prompt 示例**:
```python
CONTENT_GENERATION_PROMPT = """
【章节基本信息】
- 回目: 第{chapter_num}回 {chapter_title}
- 叙事阶段: {narrative_phase}

【主要角色】
{for character in main_characters:}
- {character.name} ({character.role}): {character.character_development}
  主要场景: {character.key_scenes}
{endfor}

【主要情节点】
{for plot_point in main_plot_points:}
{plot_point.sequence}. {plot_point.event}
   地点: {plot_point.location}
   参与者: {plot_point.participants}
   意义: {plot_point.significance}
{endfor}

【文学要求】
- 需要诗词: {poetry_count}首，主题为{poetry_themes}
- 象征手法: {symbolism}
- 伏笔设置: {foreshadowing}
- 情绪走向: {mood_progression}

【前后衔接】
- 承接上回: {previous_chapter_link}
- 引出下回: {next_chapter_setup}

请根据以上详细规划，创作一篇完整的第{chapter_num}回内容，保持红楼梦的古典文学风格...
"""
```

### 6.4 QualityCheckerAgent 改造

**新增检查项**:
```python
async def check_consistency_with_plan(self, content, chapter_plan):
    """检查生成内容是否符合章节规划"""
    
    checks = {
        "title_match": self._check_title(content, chapter_plan["chapter_title"]),
        "characters_present": self._check_characters(content, chapter_plan["main_characters"]),
        "plot_points_covered": self._check_plot_points(content, chapter_plan["main_plot_points"]),
        "mood_progression": self._check_mood(content, chapter_plan["literary_elements"]["mood_progression"]),
        "length_appropriate": self._check_length(content, chapter_plan["chapter_metadata"]["estimated_length"])
    }
    
    return checks
```

---

## 7. 开发计划

### 7.1 分阶段实施方案

#### 阶段1: ChapterPlannerAgent开发 (2-3天)

**Day 1: 基础框架**
- [ ] 创建 `chapter_planner_agent.py`
- [ ] 实现基础类结构
- [ ] 设计数据模型（Pydantic）
- [ ] 编写单元测试框架

**Day 2: 核心功能**
- [ ] 实现全局结构规划器
- [ ] 实现单章详细规划器
- [ ] 实现角色分配器
- [ ] 设计并测试Prompt

**Day 3: 集成测试**
- [ ] 与StrategyPlannerAgent集成
- [ ] 生成完整的81-120回规划
- [ ] 验证数据完整性和合理性
- [ ] 调试和优化

#### 阶段2: 现有Agent改造 (1-2天)

**Day 4: Agent改造**
- [ ] 简化StrategyPlannerAgent（移除详细规划功能）
- [ ] 改造ContentGeneratorAgent（使用章节规划）
- [ ] 改造QualityCheckerAgent（增加一致性检查）
- [ ] 更新OrchestratorAgent流程

**Day 5: 测试验证**
- [ ] 端到端测试（生成第81回）
- [ ] 验证改进效果
- [ ] 性能测试

#### 阶段3: 系统优化 (1-2天)

**Day 6-7: 优化完善**
- [ ] 优化Prompt提高质量
- [ ] 添加缓存机制
- [ ] 完善错误处理
- [ ] 更新文档

### 7.2 验收标准

#### 功能验收
- ✅ 能够生成81-120回完整的章节规划
- ✅ 每回规划包含：标题、角色、剧情、文学元素
- ✅ 角色分布合理，主要角色出场频率符合预期
- ✅ 章节间连贯性良好
- ✅ 生成的内容符合章节规划

#### 质量验收
- ✅ 章节标题对仗工整，符合红楼梦风格
- ✅ 剧情发展逻辑合理，符合用户结局
- ✅ 人物性格与原著一致
- ✅ 文学素养达标（诗词、象征、伏笔等）

#### 性能验收
- ✅ 章节规划生成时间 < 5分钟（40回）
- ✅ 单回内容生成时间 < 2分钟
- ✅ 系统稳定性良好，错误率 < 5%

### 7.3 风险评估

| 风险项 | 影响 | 概率 | 应对措施 |
|--------|------|------|----------|
| GPT-5 API调用失败 | 高 | 中 | 添加重试机制和降级方案 |
| 章节规划质量不佳 | 高 | 中 | 多轮迭代优化Prompt |
| 性能问题（生成慢） | 中 | 低 | 添加并发处理和缓存 |
| 数据结构变更影响 | 中 | 低 | 版本控制和向后兼容 |

---

## 8. 总结

### 8.1 改进亮点

1. **✨ 新增ChapterPlannerAgent** - 补齐系统最关键的一环
2. **🎯 职责清晰化** - 每个Agent职责明确，降低耦合
3. **📊 数据结构化** - 完整的章节规划数据支撑后续生成
4. **🔄 流程优化** - 先规划后执行，确保整体连贯性
5. **📈 质量提升** - 基于详细规划的生成质量更高

### 8.2 预期效果

**改进前**:
- ❌ 章节标题重复/雷同
- ❌ 角色分布不均
- ❌ 剧情缺乏整体规划
- ❌ 连贯性差

**改进后**:
- ✅ 每回都有独特的、符合剧情发展的标题
- ✅ 主要角色合理分布在40回中
- ✅ 剧情有整体规划，层层推进
- ✅ 章节间连贯性好，前后呼应

---

**文档结束**

*如有疑问或需要调整，请随时反馈*
