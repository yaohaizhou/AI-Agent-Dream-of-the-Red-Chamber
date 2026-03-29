# StoryState 故事状态机 · 设计文档

**日期：** 2026-03-29
**作者：** Claude (Brainstorming)
**状态：** 已确认，待实现

---

## 一、目标

在《红楼梦》第 81–120 回的自动续写流程中，引入一个**跨章节的故事状态层**，使每一章的生成不再是独立的"单次请求"，而是在感知过去、朝向命运的语境中写作。

StoryState 的核心职责是：
- 向 `ContextAssembler` 提供上一章的语境、当前激活的文学意象、以及急需兑现的伏笔信息；
- 在每章生成后，接收 Prophecy Analyst 的反馈并自动更新自身；
- 支持导演（用户）随时通过指令干预故事走向。

---

## 二、架构定位

```
StoryState
    ↓ 提供语境
ContextAssembler → ContentWriter → 生成文本
                                        ↓
                              Prophecy Analyst（自动分析）
                                        ↓ 反馈 + 用户干预
                                   StoryState（更新）
                                        ↓
                               持久化 state_ch{N}.json
```

StoryState 是 Phase 2（多章连续生成）的核心枢纽，连接：
- **上游**：`StoryDirector`（Task 11，决定下一章的 SceneSpec）
- **下游**：`ContextAssembler`（Task 5，将状态转换为 prompt）
- **旁路**：`ForeshadowingKnowledgeBase`（Task 10，伏笔检索与兑现）

---

## 三、数据结构

StoryState 由五个层次构成，以 JSON 格式持久化存储。

### L1：判词意象层 (Prophecy Anchors)

```json
"prophecy_anchors": {
  "active_prophecies": [
    {
      "character": "林黛玉",
      "prophecy_fragment": "玉带林中挂",
      "keywords": ["玉带", "林", "挂", "泪尽", "还债"],
      "activated_at_chapter": 85,
      "urgency": "building"
    },
    {
      "character": "王熙凤",
      "prophecy_fragment": "哭向金陵事更哀",
      "keywords": ["金陵", "哭", "衰", "落魄"],
      "activated_at_chapter": 90,
      "urgency": "dormant"
    }
  ],
  "current_thematic_keywords": ["秋", "竹影", "药香", "残荷", "支绌"]
}
```

- `urgency` 可取值：`dormant`（潜伏）、`building`（逐渐渗入）、`peak`（高密度暗示）、`resolved`（已兑现）
- `current_thematic_keywords` 由 Prophecy Analyst 每章刷新，直接注入下一章的 `SceneSpec.foreshadowing_should_plant`

### L2：剧情旗帜层 (Plot Flags)

```json
"plot_flags": {
  "milestones": {
    "宝玉丢玉": false,
    "大观园抄检": true,
    "黛玉焚稿": false,
    "金玉良缘订立": false,
    "贾府获罪抄家": false,
    "宝玉出家": false
  },
  "chapter_summary": "秋气渐深，贾府表面如常而内里支绌，宝黛在潇湘馆相遇，二人无多话却都感世事难凭。远处忽有急信传来，园中静气一变。",
  "last_chapter_num": 81
}
```

- `milestones` 里的 flag 一旦翻转为 `true`，后续所有章节的 SceneSpec 将自动感知此变化
- `chapter_summary` 始终保存上一章的精简摘要，作为本章的前情衔接

### L3：人物概况层 (Character State)

```json
"character_states": {
  "林黛玉": {
    "health_trend": "衰退",
    "emotional_center": "凄婉",
    "last_scene_chapter": 81,
    "notes": "咳嗽加重，药未停"
  },
  "贾宝玉": {
    "health_trend": "平稳",
    "emotional_center": "怅惘",
    "last_scene_chapter": 81,
    "notes": "丢玉征兆隐现"
  },
  "王熙凤": {
    "health_trend": "暗中衰退",
    "emotional_center": "强撑",
    "last_scene_chapter": 80,
    "notes": "身体每况愈下，仍强撑家政"
  }
}
```

- `health_trend`：`"平稳"` / `"衰退"` / `"危急"` / `"已逝"`（定性，不用数字）
- `emotional_center`：当前章节中该人物的主导情绪词（直接影响 prompt 中的 `emotional_tone`）
- `last_scene_chapter`：防止某人物连续多章"消失"

### L4：叙事节奏层 (Narrative Pacing)

```json
"narrative_pacing": {
  "recent_tone_streak": [
    {"chapter": 79, "tone": "热闹"},
    {"chapter": 80, "tone": "衰寂"},
    {"chapter": 81, "tone": "衰寂"}
  ],
  "last_chapter_ending": "悬念",
  "suggested_next_tone": "过渡",
  "notes": "连续两章衰寂，下章宜有一笔闲趣或小热闹作缓冲，防止读者疲惫"
}
```

- `recent_tone_streak`：保留最近 3 章的基调记录
- `last_chapter_ending`：`"悬念"` / `"收束"` / `"过渡"`
- `suggested_next_tone`：由系统根据节奏规律自动推算，导演可覆盖
- **节奏规律**（参考原著）：连续 2 章衰寂后，宜插入 1 章闲笔或小热闹；大事件后必跟 1 章情绪沉淀

### L5：伏笔债务层 (Foreshadowing Debt Ledger)

```json
"foreshadowing_debts": [
  {
    "id": "fd_001",
    "description": "第五回黛玉判词'还泪'，需写出黛玉泪尽而逝",
    "source": "原著第5回",
    "keywords": ["泪尽", "还债", "香消"],
    "planted_at_chapter": 5,
    "last_hinted_chapter": 81,
    "chapters_since_hint": 0,
    "urgency_weight": 0.3,
    "status": "pending"
  },
  {
    "id": "fd_002",
    "description": "第十三回秦可卿托梦凤姐，预言'树倒猢狲散'",
    "source": "原著第13回",
    "keywords": ["树倒", "猢狲散", "家败"],
    "planted_at_chapter": 13,
    "last_hinted_chapter": 75,
    "chapters_since_hint": 6,
    "urgency_weight": 0.6,
    "status": "pending"
  }
]
```

- `chapters_since_hint`：每章生成后自动递增；当值超过阈值（默认 8 章），自动将该伏笔加权注入下一章 SceneSpec
- `urgency_weight`：0.0–1.0，越高在 prompt 中的渗透力越强
- `status`：`"pending"` / `"hinting"` / `"resolved"`

---

## 四、运作流程

### Pre-Chapter（生成前）

1. `StoryState.to_scene_hints()` 将状态转换为 `SceneSpec` 的附加参数：
   - `foreshadowing_should_plant` ← `current_thematic_keywords` + 高权重债务伏笔
   - `emotional_tone` ← 主要人物的 `emotional_center`
   - `previous_summary` ← `chapter_summary`
   - 节奏建议写入 `scene_description` 的语气提示

### Post-Chapter（生成后）

1. **Prophecy Analyst（自动）**：
   - 检测本章文本是否命中 `active_prophecies` 中的关键词
   - 如果命中，将对应 `urgency` 升级（`dormant` → `building` → `peak`）
   - 更新 `current_thematic_keywords`
   - 检测 `foreshadowing_debts` 是否有被兑现的条目，更新 `status` 为 `"resolved"`
   - 递增所有 `pending` 债务的 `chapters_since_hint`
   - 分析本章基调（`tone`）和结尾类型，更新 `narrative_pacing`

2. **导演干预（用户可选）**：
   - 通过 CLI 指令直接修改 `StoryState` 中的任意字段
   - 例如：`> 下章开始激活王熙凤的'哭向金陵'意象`
   - 对应操作：将该条目的 `urgency` 改为 `"building"`

3. **持久化**：
   - 将更新后的完整 `StoryState` 保存为 `outputs/state/state_ch{N}.json`
   - 同时保留上一章的快照，支持"退到上一章重写"

---

## 五、关键设计决策

### 为什么不用数字血条？

红楼梦的人物命运是由意象和氛围堆砌而成，而非数值驱动。使用"健康值 = 20"会让 AI 把黛玉写得像 RPG 游戏角色；使用"health_trend = 衰退 + emotional_center = 凄婉"则是给 LLM 提供文学语境，让它在这个框架内自由表达。

### 为什么 Prophecy Analyst 是自动 + 导演干预的混合模式？

纯自动难以感知细腻的文学节奏（LLM 可能误判"泪"字的出现是否真正呼应了判词）；纯手动则失去了 AI 的优势。混合模式让系统"自动感知 + 人工校准"。

### 伏笔债务的阈值为什么是 8 章？

参考原著，重要伏笔通常在 5–10 章内会有一次回响。8 章作为默认值，既不会催得太急，也不会让读者遗忘。

---

## 六、文件结构

```
src/
  story/
    __init__.py
    story_state.py          # StoryState 主类
    prophecy_analyst.py     # 自动分析 + 状态更新
    state_schema.py         # 数据结构定义 (dataclasses)

outputs/
  state/
    state_ch81.json         # 第 81 回生成后的状态快照
    state_ch82.json
    ...

data/
  knowledge_base/
    prophecies/
      canonical.json        # 十二钗判词的结构化数据（关键词、人物、阶段）

tests/
  story/
    test_story_state.py
    test_prophecy_analyst.py
```

---

## 七、自审 (Self-Review)

### Spec 覆盖检查
- ✅ 判词意象层（动态检测 + 导演干预）
- ✅ 剧情旗帜层（关键事件追踪）
- ✅ 人物概况层（定性，不用数字）
- ✅ 叙事节奏层（扩展 A）
- ✅ 伏笔债务层（扩展 C）
- ✅ Pre/Post-Chapter 完整流程
- ✅ 持久化策略

### Placeholder 扫描
- 无 TBD / TODO / 模糊描述

### 内部一致性
- `StoryState.to_scene_hints()` 输出的字段均与 `SceneSpec` 的现有字段对齐
- `foreshadowing_should_plant` 在 `ContextAssembler` 中已有处理逻辑，无需额外修改接口
