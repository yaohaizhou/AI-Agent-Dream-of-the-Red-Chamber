# ChapterPlannerAgent Mock模式使用说明

> **日期**: 2025-09-30  
> **作者**: heai

---

## 🎭 Mock模式介绍

Mock模式允许您在**不调用GPT-5 API**的情况下快速测试ChapterPlannerAgent的逻辑和数据流程。

### 优势

- ⚡ **极快速度**: 10回规划仅需0.00秒
- 💰 **零成本**: 不消耗API调用额度
- 🔧 **快速开发**: 适合调试和开发新功能
- ✅ **完整数据**: 生成结构完整的模拟数据

---

## 🚀 使用方法

### 方法1: 命令行参数

```bash
# 运行Mock模式测试
python tests/test_chapter_planner.py --mock

# 或使用短参数
python tests/test_chapter_planner.py -m
```

### 方法2: 代码中启用

```python
from src.config.settings import Settings
from src.agents.real.chapter_planner_agent import ChapterPlannerAgent

# 创建设置并启用Mock模式
settings = Settings()
settings.use_mock_chapter_planner = True  # 启用Mock模式

# 创建Agent
agent = ChapterPlannerAgent(settings)

# 正常使用，但不会调用真实API
result = await agent.process(input_data)
```

---

## 📊 Mock数据特点

### 生成的数据包含

1. **元数据**
   - 版本、创建时间
   - 用户结局
   - 章节范围

2. **全局结构**
   - 四阶段叙事划分
   - 主要剧情线
   - 时间线规划

3. **章节详情** (每回)
   - 对仗工整的回目标题
   - 3个主要角色
   - 2个主要情节点
   - 文学元素（诗词、象征、伏笔）

### Mock标题示例

```
第81回: 暗香疏影探春事 / 落絮纷纷忆旧情
第82回: 病榻诗成伤往日 / 园中絮语话新愁
第83回: 宝玉探病怀真意 / 黛玉题诗寄深情
第84回: 荣府渐衰人心散 / 怡红未改旧时颜
第85回: 贾母垂泪话家运 / 宝钗持重理中馈
```

### Mock角色分配

根据章节号自动轮换角色组合：
- 第81回: 贾宝玉、林黛玉、薛宝钗
- 第82回: 林黛玉、薛宝钗、贾母
- 第83回: 薛宝钗、贾母、王夫人
- ...

---

## 🔄 开发模式切换

### 开发流程建议

1. **初期开发**: 使用Mock模式
   - 快速验证逻辑
   - 调试数据流程
   - 完善功能

2. **中期测试**: 小规模真实测试
   - 测试1-2回
   - 验证API调用
   - 检查JSON解析

3. **最终验证**: 完整真实测试
   - 测试40回完整流程
   - 验证质量
   - 性能测试

### 切换方式

```bash
# Mock模式（开发）
python tests/test_chapter_planner.py --mock

# 真实模式（测试）
python tests/test_chapter_planner.py --full
```

---

## 📝 测试输出对比

### Mock模式

```
耗时: 0.00秒
API调用: 0次
成本: $0
数据: 完整模拟数据
```

### 真实模式

```
耗时: ~30秒 (10回)
API调用: 11次 (1次全局 + 10次单章)
成本: ~$0.50 (取决于定价)
数据: GPT-5生成的真实数据
```

---

## 🎯 适用场景

### ✅ 适合Mock模式

- 调试Agent逻辑
- 测试数据流程
- 验证一致性检查
- 开发新功能
- 快速迭代

### ⚠️ 需要真实模式

- 验证Prompt质量
- 测试JSON解析
- 评估生成质量
- 最终验收测试
- 生产环境使用

---

## 🛠️ 技术实现

### Mock数据生成器

```python
def _create_enhanced_mock_chapter_detail(self, chapter_num, narrative_phase, previous_chapter):
    """创建增强版的模拟章节规划"""
    
    # 使用预定义的标题库
    mock_titles = [
        ("暗香疏影探春事", "落絮纷纷忆旧情"),
        ("病榻诗成伤往日", "园中絮语话新愁"),
        ...
    ]
    
    # 根据章节号选择标题和角色
    title_idx = (chapter_num - 81) % len(mock_titles)
    title = mock_titles[title_idx]
    
    # 生成完整的章节数据
    return {
        "chapter_number": chapter_num,
        "chapter_title": {...},
        "main_characters": [...],
        ...
    }
```

### 特点

- 🎲 **确定性**: 相同输入生成相同输出
- 📦 **完整性**: 包含所有必要字段
- 🔄 **多样性**: 基于章节号变化

---

## 📚 相关文档

- **Day 2总结**: `docs/CHAPTER_PLANNER_DAY2_SUMMARY.md`
- **技术方案**: `docs/TECHNICAL_DESIGN_V2.md`
- **测试脚本**: `tests/test_chapter_planner.py`
- **源代码**: `src/agents/real/chapter_planner_agent.py`

---

## 💡 提示

1. **开发时优先使用Mock模式**，节省时间和成本
2. **定期进行真实测试**，确保Prompt和解析正常
3. **Mock数据仅用于测试**，不要用于生产环境
4. **真实模式建议先测试少量回数**（1-5回），再扩展到40回

---

**Happy Mocking! 🎭**
