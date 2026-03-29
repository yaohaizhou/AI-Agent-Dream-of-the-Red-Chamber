# AI续写红楼梦 · 架构重构设计文档

**日期**：2026-03-29
**目标**：重构现有架构，基于前80回原著内容续写后40回，文风贴近曹雪芹，支持用户一句话引导情节走向
**技术栈**：gpt-5.4 API（OpenAI兼容）+ ChromaDB + BAAI/bge-m3 + Python 3.11

---

## 一、问题诊断

### 当前架构的根本缺陷

现有系统是"流水线式"多Agent架构：Orchestrator 依次调用各 Agent，每个 Agent 的上下文来自**上一步 Agent 的输出**，而非**原著**。

核心问题：
1. **Prompt 描述风格而非展示风格**：用"请用古典文学风格"这类指令替代了真正的 few-shot 原著示例
2. **知识库未被生成层利用**：`knowledge_base.db` 存在但 ContentGeneratorAgent 未在生成时检索它
3. **质量检查器用关键词打分**：`QualityCheckerAgent` 的评分与原著无关，导致虚高（8.9/10 但实际是网文语感）
4. **情节硬编码**：`config/fates/character_fates.yml` 写死了宝黛结局，无法动态调整

### 目标质量标准

生成文本需同时满足：
- **叙事语感**：第三人称全知视角，克制含蓄，字密情深，不出现现代口语词
- **人物声音**：每个角色的对话节奏、用词习惯与原著保持一致
- **情节内在逻辑**：伏笔有埋有收，与原著80回自然衔接

---

## 二、整体架构

### 架构图

```
┌─────────────────────────────────────────────────────┐
│                    用户层                             │
│  用户说一句话 → UserIntentParser → StoryDirector     │
└──────────────────────┬──────────────────────────────┘
                       │ SceneSpec
┌──────────────────────▼──────────────────────────────┐
│                  故事状态层                            │
│  StoryState：当前章节 / 活跃伏笔 / 人物关系动态       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                三层知识库（核心新增）                  │
│                                                      │
│  [风格层] StyleKB   原著段落 → ChromaDB 向量索引      │
│  [人物层] CharacterKB  语言特征卡片 → JSON            │
│  [伏笔层] ForeshadowingKB  原著伏笔+动态伏笔          │
└──────────────────────┬──────────────────────────────┘
                       │ RAG检索结果
┌──────────────────────▼──────────────────────────────┐
│                  生成层                               │
│  ContextAssembler → ContentWriter（gpt-5.4）         │
└──────────────────────┬──────────────────────────────┘
                       │ 原始文本
┌──────────────────────▼──────────────────────────────┐
│                  评判层                               │
│  LiteraryJudge：对照原著RAG片段打分，不过关自动重写   │
└─────────────────────────────────────────────────────┘
```

### 与现有代码的关系

| 现有组件 | 处理方式 | 原因 |
|---------|---------|------|
| `OrchestratorAgent` | 改造 | 调用顺序改为新流程 |
| `FateEngine` | 保留 | 接入 ForeshadowingKB |
| `ForeshadowingManager` | 保留 | 作为动态伏笔后端 |
| `IntentParser` | 保留，被 StoryDirector 调用 | 逻辑可复用 |
| `ContentGeneratorAgent` | 内部重写 prompt 组装 | 改用 ContextAssembler |
| `QualityCheckerAgent` | 替换评分逻辑 | 改用 LiteraryJudge |
| `literary_prompts.py` | 简化 | prompt 模板由 ContextAssembler 接管 |

---

## 三、三层知识库设计

### 3.1 风格层（StyleKnowledgeBase）

**数据来源**：`data/raw/hongloumeng_80.md`
**存储**：ChromaDB，本地持久化于 `data/knowledge_base/style/`
**Embedding模型**：`BAAI/bge-m3`（MPS加速）

**切块策略**：

| 段落类型 tag | 描述 | 典型特征 | 检索时机 |
|------------|------|---------|---------|
| `narrative` | 叙事段落 | "只见……""正说着……" | 写叙述段落时 |
| `dialogue` | 人物对话 | 某某道："……" | 写对话时 |
| `scenery` | 景物描写 | 节气、天气、园景 | 写环境烘托时 |
| `poetry` | 诗词歌赋 | 判词、联句、即景诗 | 写诗词时 |
| `inner_thought` | 心理描写 | "心中想道""不禁想起" | 写内心时 |

**每个分块的元数据**：
```json
{
  "chapter_num": 27,
  "paragraph_type": "dialogue",
  "characters_present": ["林黛玉", "贾宝玉"],
  "location": "潇湘馆",
  "emotional_tone": "哀愁",
  "text": "（原著原文）"
}
```

**检索接口**：
```python
style_kb.search(
    paragraph_type="dialogue",
    characters=["林黛玉"],
    emotional_tone="哀愁",
    top_k=3
) → List[str]  # 返回原著原文段落
```

---

### 3.2 人物层（CharacterVoiceBase）

**数据来源**：自动从原著提取，存储于 `data/knowledge_base/characters/`
**格式**：每个主角一个 JSON 文件

**提取内容**：

```json
{
  "name": "林黛玉",
  "惯用句式": ["……罢了", "……偏要……", "可不是……", "……也是有的"],
  "常见称谓": {"贾宝玉": "你/宝玉", "王熙凤": "凤姐姐", "贾母": "外祖母"},
  "禁用词汇": ["高兴", "开心", "没事", "搞定", "好的"],
  "情绪表达方式": "善用反问、借景抒情、点到即止，少有直白表达",
  "语气特征": "清冷、敏感、多用转折",
  "典型对话示例": [
    "（直接引用原著对话1）",
    "（直接引用原著对话2）",
    "（直接引用原著对话3）"
  ]
}
```

**覆盖人物**：林黛玉、贾宝玉、薛宝钗、王熙凤、贾母、贾探春、史湘云、袭人、紫鹃

**提取方式**：一次性批处理脚本（`knowledge/builder.py`），调用 gpt-5.4 分析原著，人工可二次校对

---

### 3.3 伏笔层（ForeshadowingKnowledgeBase）

**数据来源**：原著已知伏笔（静态）+ 用户引导产生的新伏笔（动态）

**原著静态伏笔索引**（`data/knowledge_base/foreshadowing/canonical.json`）：

```json
[
  {
    "id": "f001",
    "source_chapter": 5,
    "hint_text": "玉带林中挂，金簪雪里埋",
    "character": "林黛玉",
    "expected_payoff_range": [95, 115],
    "payoff_type": "生死关键事件",
    "status": "pending"
  },
  {
    "id": "f002",
    "source_chapter": 5,
    "hint_text": "二十年来辨是非，榴花开处照宫闱",
    "character": "元春",
    "expected_payoff_range": [85, 95],
    "payoff_type": "宫廷事件",
    "status": "pending"
  }
]
```

**检索接口**：
```python
foreshadowing_kb.get_chapter_tasks(chapter_num=81) → {
    "must_payoff": [...],   # 本章必须兑现
    "should_plant": [...],  # 本章建议埋设
    "active_threads": [...]  # 进行中的伏笔线
}
```

---

## 四、生成流程

### 4.1 用户引导机制（StoryDirector）

用户每次运行时可选择性地输入一句话，系统做三件事：

1. **影响分析**：是否与已有伏笔或原著轨迹冲突
2. **强度分级**：
   - 强约束（本章内必须发生）：`"让黛玉在第81回收到一封匿名信"`
   - 弱约束（长期方向）：`"让宝玉最终出家"`
   - 无输入：系统根据原著判词和伏笔层自主推进
3. **写入 StoryState**：记录为活跃方向，影响后续所有章节

### 4.2 ContextAssembler 的 Prompt 结构

这是解决"网文感"的核心——不描述风格，而是展示风格：

```
[SYSTEM]
你是曹雪芹《红楼梦》的续写传人。你只能使用以下原著范例的语言风格和叙事方式。
绝对禁止出现以下现代词汇：高兴、开心、没事、感觉、其实、然后、所以、但是（用"却"替代）等。

[原著风格范例 · 叙事段落]
（RAG检索到的原著原文，2-3段，与本章场景类型匹配）

[原著风格范例 · 对话段落]
（RAG检索到的对话原文，2-3段，涉及本章出场人物）

[本章出场人物语言约束]
林黛玉：惯用"……罢了"，善用反问，禁用"高兴/开心"
        典型对话：（引用原著1-2句）
贾宝玉：惯用"我偏……"，直白急切，禁用官场礼节用语
        典型对话：（引用原著1-2句）

[本章伏笔指令]
- 必须兑现：（foreshadowing_kb 返回的本章必兑现伏笔）
- 建议埋设：（本章可埋设的新伏笔）

[用户方向]（可选）
"（用户本次输入的一句话）"

[当前故事状态]
已完成：第80回（原著结尾）
当前：第81回
前情提要：（StoryState 中的上一章摘要，约200字）

[续写任务]
请续写第81回，约2500字。
开头自然衔接前情，结尾留下悬念。
```

### 4.3 LiteraryJudge 评分机制

替换现有关键词打分，改为三维度对照评分：

| 维度 | 评分方法 | 权重 |
|-----|---------|------|
| 风格相似度 | 将生成文本与检索到的原著段落做向量余弦相似度计算 | 40% |
| 人物声音准确度 | 检测是否违反各人物的禁用词和惯用句式约束 | 35% |
| 伏笔完成度 | 检查 must_payoff 伏笔是否在文中出现 | 25% |

**自动重写机制**：
- 综合分 < 7.0：带评语重新生成（最多3次）
- 3次仍未达标：保存最高分版本，标记为"需人工审阅"

---

## 五、目录结构

```
src/
├── knowledge/                    # 【新增】三层知识库
│   ├── __init__.py
│   ├── builder.py                # 一次性建库脚本
│   ├── style_kb.py               # 风格层：ChromaDB向量检索
│   ├── character_kb.py           # 人物层：语言特征卡片
│   └── foreshadowing_kb.py       # 伏笔层
│
├── story/                        # 【新增】故事状态管理
│   ├── __init__.py
│   ├── state.py                  # StoryState持久化
│   └── director.py               # StoryDirector：意图→SceneSpec
│
├── generation/                   # 【新增】生成核心
│   ├── __init__.py
│   ├── context_assembler.py      # 拼装最终prompt
│   ├── content_writer.py         # 调用LLM
│   └── literary_judge.py         # 对照原著评分
│
├── agents/                       # 【保留+改造】
│   └── orchestrator.py           # 调用新组件的新流程
│
└── core/                         # 【保留不动】
    ├── fate_engine.py
    ├── foreshadowing.py
    └── intent_parser.py

data/
├── raw/hongloumeng_80.md         # 原著（已有）
├── knowledge_base/               # 【新增】知识库持久化
│   ├── style/                    # ChromaDB索引
│   ├── characters/               # 人物JSON
│   └── foreshadowing/            # 伏笔JSON
└── story_state.json              # 当前故事状态
```

---

## 六、技术依赖

### 新增依赖

```
chromadb>=1.5.0          # 向量数据库（本地）
sentence-transformers    # BAAI/bge-m3 embedding
```

### Embedding配置

```python
# 使用 MPS 加速（Apple Silicon）
model = SentenceTransformer("BAAI/bge-m3", device="mps")
```

---

## 七、实施优先级

### Phase 1：核心质量提升（第81回做到高质量）
1. 建立风格层知识库（`knowledge/builder.py` + `knowledge/style_kb.py`）
2. 提取人物语言特征（`knowledge/character_kb.py`）
3. 实现 ContextAssembler（拼装新 prompt 结构）
4. 实现 LiteraryJudge（RAG 对照评分 + 自动重写）
5. 改造 ContentWriter 使用新 prompt
6. 端到端跑通第81回

### Phase 2：故事连贯性
7. 实现 StoryState（章节状态持久化）
8. 建立伏笔层知识库（`knowledge/foreshadowing_kb.py`）
9. 实现 StoryDirector（用户意图 → SceneSpec）
10. 端到端跑通连续3回，验证前后文衔接

### Phase 3：扩展到40回
11. 完善自动重写机制（最多3次循环）
12. 批量生成81-120回
13. 输出格式整理

---

## 八、成功标准

- **Phase 1**：第81回生成内容，人工阅读时不会立即感到"这是网文"
- **Phase 2**：连续3回读下来，人物声音一致，前后文衔接自然
- **Phase 3**：用户输入一句话，下一回内容明显向该方向倾斜
