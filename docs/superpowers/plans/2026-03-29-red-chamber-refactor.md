# AI续写红楼梦 · 架构重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构AI续写红楼梦系统，通过三层知识库（风格/人物/伏笔）+ RAG驱动生成，使续写内容脱离"网文感"，真正贴近曹雪芹风格，并支持用户一句话实时引导情节走向。

**Architecture:** StyleKnowledgeBase 将前80回原著按段落类型向量化，CharacterKnowledgeBase 保存每位主角的语言特征卡片，ContextAssembler 在生成前将原著范例直接注入 prompt，LiteraryJudge 用向量相似度和禁用词检测替代现有的关键词打分，完整流程通过 `run_ch81.py` 串联。

**Tech Stack:** Python 3.11, gpt-5.4 (OpenAI-compatible API), ChromaDB 1.5.5, BAAI/bge-m3 (sentence-transformers), MPS加速

---

## 文件地图

### 新建文件

| 文件 | 职责 |
|------|------|
| `src/knowledge/__init__.py` | 模块入口 |
| `src/knowledge/style_kb.py` | StyleKnowledgeBase：ChromaDB 向量检索 |
| `src/knowledge/character_kb.py` | CharacterKnowledgeBase：人物语言特征卡片 |
| `src/knowledge/foreshadowing_kb.py` | ForeshadowingKnowledgeBase：伏笔管理（Phase 2） |
| `src/knowledge/builder.py` | 一次性建库脚本 |
| `src/generation/__init__.py` | 模块入口 |
| `src/generation/context_assembler.py` | ContextAssembler：拼装最终 prompt |
| `src/generation/content_writer.py` | ContentWriter：调用 LLM |
| `src/generation/literary_judge.py` | LiteraryJudge：评分+自动重写 |
| `src/story/__init__.py` | 模块入口（Phase 2） |
| `src/story/state.py` | StoryState：故事进度持久化（Phase 2） |
| `src/story/director.py` | StoryDirector：用户意图→SceneSpec（Phase 2） |
| `tests/knowledge/test_style_kb.py` | StyleKB 测试 |
| `tests/knowledge/test_character_kb.py` | CharacterKB 测试 |
| `tests/generation/test_context_assembler.py` | ContextAssembler 测试 |
| `tests/generation/test_literary_judge.py` | LiteraryJudge 测试 |
| `run_ch81.py` | Phase 1 入口：生成第81回 |
| `data/knowledge_base/foreshadowing/canonical.json` | 原著伏笔静态索引 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `requirements.txt` | 添加 chromadb、sentence-transformers |

---

## Phase 1：核心质量提升（第81回）

---

### Task 1：添加依赖 + 创建目录结构

**Files:**
- Modify: `requirements.txt`
- Create: `src/knowledge/__init__.py`
- Create: `src/generation/__init__.py`
- Create: `tests/knowledge/__init__.py`
- Create: `tests/generation/__init__.py`

- [ ] **Step 1: 更新 requirements.txt**

```
# requirements.txt（追加以下两行）
chromadb>=1.5.0
sentence-transformers>=3.0.0
```

- [ ] **Step 2: 创建模块 __init__.py 文件**

```bash
mkdir -p src/knowledge src/generation src/story
mkdir -p tests/knowledge tests/generation
touch src/knowledge/__init__.py src/generation/__init__.py src/story/__init__.py
touch tests/knowledge/__init__.py tests/generation/__init__.py
touch tests/__init__.py
```

- [ ] **Step 3: 验证依赖可导入**

```bash
python3 -c "import chromadb; from sentence_transformers import SentenceTransformer; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt src/knowledge/ src/generation/ src/story/ tests/
git commit -m "chore: add chromadb/sentence-transformers deps, scaffold new modules"
```

---

### Task 2：StyleKnowledgeBase

**Files:**
- Create: `src/knowledge/style_kb.py`
- Create: `tests/knowledge/test_style_kb.py`

- [ ] **Step 1: 写失败测试**

`tests/knowledge/test_style_kb.py`:

```python
import pytest
import tempfile
from src.knowledge.style_kb import StyleKnowledgeBase, StyleChunk


def make_test_kb(tmp_dir):
    kb = StyleKnowledgeBase(persist_dir=tmp_dir)
    chunks = [
        StyleChunk(
            text="只见宝玉歪在榻上，手执一卷《庄子》，却并未翻动。",
            chapter_num=27,
            paragraph_type="narrative",
            characters_present=["贾宝玉"],
            location="怡红院",
            emotional_tone="闲散",
        ),
        StyleChunk(
            text="黛玉道：'你这话从何说起？'宝玉笑道：'好妹妹，你别恼。'",
            chapter_num=32,
            paragraph_type="dialogue",
            characters_present=["林黛玉", "贾宝玉"],
            location="潇湘馆",
            emotional_tone="哀愁",
        ),
    ]
    kb.add_chunks(chunks)
    return kb


def test_count(tmp_path):
    kb = make_test_kb(str(tmp_path))
    assert kb.count() == 2


def test_search_returns_results(tmp_path):
    kb = make_test_kb(str(tmp_path))
    results = kb.search("宝玉读书", top_k=2)
    assert len(results) >= 1
    assert isinstance(results[0], str)


def test_search_filter_by_paragraph_type(tmp_path):
    kb = make_test_kb(str(tmp_path))
    results = kb.search("宝玉对话", paragraph_type="dialogue", top_k=2)
    assert len(results) >= 1
    # All returned texts should come from dialogue chunks
    assert "道：" in results[0] or "笑道" in results[0]


def test_search_empty_kb(tmp_path):
    kb = StyleKnowledgeBase(persist_dir=str(tmp_path))
    results = kb.search("任意查询", top_k=3)
    assert results == []
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
python3 -m pytest tests/knowledge/test_style_kb.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError` 或 `ImportError`

- [ ] **Step 3: 实现 StyleKnowledgeBase**

`src/knowledge/style_kb.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import torch
import chromadb


@dataclass
class StyleChunk:
    text: str
    chapter_num: int
    paragraph_type: str  # narrative | dialogue | scenery | poetry | inner_thought
    characters_present: List[str]
    location: str = ""
    emotional_tone: str = "neutral"


class StyleKnowledgeBase:
    """原著风格段落的向量知识库。"""

    def __init__(self, persist_dir: str = "data/knowledge_base/style"):
        self._model = None
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="style_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            self._model = SentenceTransformer("BAAI/bge-m3", device=device)
        return self._model

    def add_chunks(self, chunks: List[StyleChunk]) -> None:
        if not chunks:
            return
        texts = [c.text for c in chunks]
        embeddings = self.model.encode(texts, normalize_embeddings=True).tolist()
        ids = [
            f"ch{c.chapter_num}_{abs(hash(c.text)) % 10_000_000}"
            for c in chunks
        ]
        metadatas = [
            {
                "chapter_num": c.chapter_num,
                "paragraph_type": c.paragraph_type,
                "characters_present": ",".join(c.characters_present),
                "location": c.location,
                "emotional_tone": c.emotional_tone,
            }
            for c in chunks
        ]
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

    def search(
        self,
        query: str,
        paragraph_type: Optional[str] = None,
        characters: Optional[List[str]] = None,
        top_k: int = 3,
    ) -> List[str]:
        """返回与 query 最相近的原著段落文本列表。"""
        if self.count() == 0:
            return []
        query_emb = self.model.encode([query], normalize_embeddings=True).tolist()
        where: Optional[dict] = None
        if paragraph_type:
            where = {"paragraph_type": {"$eq": paragraph_type}}
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=min(top_k, self.count()),
            where=where,
            include=["documents"],
        )
        return results["documents"][0] if results["documents"] else []

    def count(self) -> int:
        return self.collection.count()
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
python3 -m pytest tests/knowledge/test_style_kb.py -v
```

Expected: 4 passed（首次运行会下载 bge-m3，约500MB，耐心等待）

- [ ] **Step 5: Commit**

```bash
git add src/knowledge/style_kb.py tests/knowledge/test_style_kb.py
git commit -m "feat: add StyleKnowledgeBase with ChromaDB + bge-m3"
```

---

### Task 3：OriginalTextParser + 建库

**Files:**
- Create: `src/knowledge/builder.py`
- Create: `data/knowledge_base/foreshadowing/canonical.json`

- [ ] **Step 1: 实现原著解析器和建库脚本**

`src/knowledge/builder.py`:

```python
"""
一次性建库脚本。
运行: python3 -m src.knowledge.builder
构建完成后，data/knowledge_base/style/ 即可用于 RAG 检索。
"""
from __future__ import annotations
import re
import json
from pathlib import Path
from typing import List, Tuple

from src.knowledge.style_kb import StyleKnowledgeBase, StyleChunk

MAIN_CHARACTERS = [
    "林黛玉", "贾宝玉", "薛宝钗", "王熙凤", "贾母",
    "贾探春", "史湘云", "袭人", "紫鹃", "贾政",
    "王夫人", "贾琏", "平儿", "鸳鸯", "贾迎春", "贾惜春",
]
SHORT_NAME_MAP = {
    "宝玉": "贾宝玉", "黛玉": "林黛玉", "宝钗": "薛宝钗",
    "凤姐": "王熙凤", "熙凤": "王熙凤",
}

CHAPTER_HEADER = re.compile(r"^###\s+第([一二三四五六七八九十百]+)回")
DIALOGUE_PATTERN = re.compile(r"[\u4e00-\u9fff]{1,4}[笑冷忙低嗔含微轻忽突]?道[：:]?[\"\"「『]")
INNER_THOUGHT = re.compile(r"(心中|心下|心里|想道|暗想|自思|不觉|不禁|只见|但见)")
SCENERY_KEYWORDS = ["日", "月", "风", "雨", "雪", "花", "树", "山", "水", "云", "天", "园", "院", "景"]
POETRY_MARKERS = re.compile(r"(判词|词曰|诗云|赋曰|歌云|曲子|题曰|其词|其判)")


def _classify(text: str) -> str:
    if POETRY_MARKERS.search(text) or (
        len(text) < 120 and text.count("，") >= 2 and text.count("。") >= 1
        and not DIALOGUE_PATTERN.search(text)
    ):
        return "poetry"
    if DIALOGUE_PATTERN.search(text):
        return "dialogue"
    if INNER_THOUGHT.search(text) and not DIALOGUE_PATTERN.search(text):
        return "inner_thought"
    scenery_count = sum(1 for kw in SCENERY_KEYWORDS if kw in text)
    if scenery_count >= 4 and len(text) < 250 and not DIALOGUE_PATTERN.search(text):
        return "scenery"
    return "narrative"


def _extract_characters(text: str) -> List[str]:
    found = [c for c in MAIN_CHARACTERS if c in text]
    for short, full in SHORT_NAME_MAP.items():
        if short in text and full not in found:
            found.append(full)
    return found


def _split_chapter(raw: str) -> List[str]:
    """将章节原文切分为 100-450 字的段落块。"""
    # 先按换行分段
    paras = [p.strip() for p in raw.split("\n") if len(p.strip()) > 30]
    chunks = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) < 450:
            buf += p
        else:
            if buf:
                chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return [c for c in chunks if len(c) >= 60]


def parse_original(filepath: str) -> List[Tuple[int, List[str]]]:
    """返回 [(chapter_num, [chunk_text, ...]), ...]"""
    text = Path(filepath).read_text(encoding="utf-8")
    chapters = []
    current_num = 0
    current_lines: List[str] = []

    for line in text.splitlines():
        m = CHAPTER_HEADER.match(line.strip())
        if m:
            if current_num > 0 and current_lines:
                chapters.append((current_num, _split_chapter("\n".join(current_lines))))
            current_lines = []
            # 将中文数字章节号转换为阿拉伯数字
            current_num = _cn_to_int(m.group(1))
        elif line.strip() == "----":
            continue
        else:
            current_lines.append(line)

    if current_num > 0 and current_lines:
        chapters.append((current_num, _split_chapter("\n".join(current_lines))))

    return chapters


_CN = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,
       "十一":11,"十二":12,"十三":13,"十四":14,"十五":15,"十六":16,"十七":17,
       "十八":18,"十九":19,"二十":20,"二十一":21,"二十二":22,"二十三":23,
       "二十四":24,"二十五":25,"二十六":26,"二十七":27,"二十八":28,"二十九":29,
       "三十":30,"三十一":31,"三十二":32,"三十三":33,"三十四":34,"三十五":35,
       "三十六":36,"三十七":37,"三十八":38,"三十九":39,"四十":40,"四十一":41,
       "四十二":42,"四十三":43,"四十四":44,"四十五":45,"四十六":46,"四十七":47,
       "四十八":48,"四十九":49,"五十":50,"五十一":51,"五十二":52,"五十三":53,
       "五十四":54,"五十五":55,"五十六":56,"五十七":57,"五十八":58,"五十九":59,
       "六十":60,"六十一":61,"六十二":62,"六十三":63,"六十四":64,"六十五":65,
       "六十六":66,"六十七":67,"六十八":68,"六十九":69,"七十":70,"七十一":71,
       "七十二":72,"七十三":73,"七十四":74,"七十五":75,"七十六":76,"七十七":77,
       "七十八":78,"七十九":79,"八十":80}

def _cn_to_int(s: str) -> int:
    return _CN.get(s, 0)


def build_style_kb(
    source: str = "data/raw/hongloumeng_80.md",
    persist_dir: str = "data/knowledge_base/style",
) -> StyleKnowledgeBase:
    print(f"📖 解析原著: {source}")
    chapters = parse_original(source)
    print(f"   共解析 {len(chapters)} 回，开始向量化...")

    kb = StyleKnowledgeBase(persist_dir=persist_dir)

    if kb.count() > 0:
        print(f"   知识库已存在 {kb.count()} 条记录，跳过重建。")
        print("   如需重建，请删除 data/knowledge_base/style/ 目录后重新运行。")
        return kb

    all_chunks: List[StyleChunk] = []
    for chapter_num, texts in chapters:
        for text in texts:
            chunk = StyleChunk(
                text=text,
                chapter_num=chapter_num,
                paragraph_type=_classify(text),
                characters_present=_extract_characters(text),
            )
            all_chunks.append(chunk)

    print(f"   共 {len(all_chunks)} 个段落块，按批次写入 ChromaDB...")
    BATCH = 64
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i : i + BATCH]
        kb.add_chunks(batch)
        print(f"   进度: {min(i + BATCH, len(all_chunks))}/{len(all_chunks)}", end="\r")

    print(f"\n✅ 风格层知识库构建完成，共 {kb.count()} 条。")
    return kb


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    Path("data/knowledge_base/style").mkdir(parents=True, exist_ok=True)
    Path("data/knowledge_base/characters").mkdir(parents=True, exist_ok=True)
    Path("data/knowledge_base/foreshadowing").mkdir(parents=True, exist_ok=True)
    build_style_kb()
```

- [ ] **Step 2: 创建原著伏笔静态索引**

`data/knowledge_base/foreshadowing/canonical.json`:

```json
[
  {
    "id": "f001",
    "source_chapter": 5,
    "hint_text": "玉带林中挂，金簪雪里埋",
    "character": "林黛玉",
    "expected_payoff_range": [95, 115],
    "payoff_keywords": ["黛玉", "生死", "离开", "假死", "病逝"],
    "status": "pending"
  },
  {
    "id": "f002",
    "source_chapter": 5,
    "hint_text": "二十年来辨是非，榴花开处照宫闱",
    "character": "元春",
    "expected_payoff_range": [83, 92],
    "payoff_keywords": ["元春", "宫中", "薨", "宫闱"],
    "status": "pending"
  },
  {
    "id": "f003",
    "source_chapter": 5,
    "hint_text": "才自精明志自高，生于末世运偏消",
    "character": "贾探春",
    "expected_payoff_range": [100, 112],
    "payoff_keywords": ["探春", "远嫁", "离去", "和亲"],
    "status": "pending"
  },
  {
    "id": "f004",
    "source_chapter": 5,
    "hint_text": "一从二令三人木，哭向金陵事更哀",
    "character": "王熙凤",
    "expected_payoff_range": [95, 108],
    "payoff_keywords": ["凤姐", "失势", "病重", "金陵"],
    "status": "pending"
  },
  {
    "id": "f005",
    "source_chapter": 13,
    "hint_text": "三春过后诸芳尽，各自须寻各自门",
    "character": "秦可卿",
    "expected_payoff_range": [81, 100],
    "payoff_keywords": ["贾府", "衰败", "诸芳", "离散"],
    "status": "pending"
  }
]
```

- [ ] **Step 3: 运行建库脚本**

```bash
python3 -m src.knowledge.builder
```

Expected 输出（首次运行耗时约3-5分钟）:
```
📖 解析原著: data/raw/hongloumeng_80.md
   共解析 80 回，开始向量化...
   共 XXXX 个段落块，按批次写入 ChromaDB...
   进度: XXXX/XXXX
✅ 风格层知识库构建完成，共 XXXX 条。
```

- [ ] **Step 4: 验证知识库可检索**

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from src.knowledge.style_kb import StyleKnowledgeBase
kb = StyleKnowledgeBase()
print('总条数:', kb.count())
results = kb.search('宝玉黛玉秋日在园中说话', paragraph_type='dialogue', top_k=2)
for i, r in enumerate(results):
    print(f'--- 结果{i+1} ---')
    print(r[:150])
"
```

Expected: 打印2条包含对话的原著段落

- [ ] **Step 5: Commit**

```bash
git add src/knowledge/builder.py data/knowledge_base/foreshadowing/canonical.json
git commit -m "feat: add OriginalTextParser and StyleKB builder script"
```

---

### Task 4：CharacterKnowledgeBase

**Files:**
- Create: `src/knowledge/character_kb.py`
- Create: `tests/knowledge/test_character_kb.py`

- [ ] **Step 1: 写失败测试**

`tests/knowledge/test_character_kb.py`:

```python
from src.knowledge.character_kb import CharacterKnowledgeBase


def test_get_profile_returns_dict():
    kb = CharacterKnowledgeBase()
    profile = kb.get_profile("林黛玉")
    assert profile is not None
    assert "惯用句式" in profile
    assert "禁用词" in profile
    assert isinstance(profile["禁用词"], list)


def test_get_profile_unknown_character():
    kb = CharacterKnowledgeBase()
    profile = kb.get_profile("路人甲")
    assert profile is None


def test_format_constraint_contains_character_name():
    kb = CharacterKnowledgeBase()
    constraint = kb.format_constraint("贾宝玉", kb.get_profile("贾宝玉"))
    assert "贾宝玉" in constraint
    assert "禁用" in constraint or "惯用" in constraint


def test_all_main_characters_have_profiles():
    kb = CharacterKnowledgeBase()
    for name in ["林黛玉", "贾宝玉", "薛宝钗", "王熙凤", "贾母"]:
        assert kb.get_profile(name) is not None, f"缺少 {name} 的语言特征配置"
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
python3 -m pytest tests/knowledge/test_character_kb.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 CharacterKnowledgeBase**

`src/knowledge/character_kb.py`:

```python
"""人物语言特征知识库。基于原著研究预设，支持运行时扩展。"""
from __future__ import annotations
from typing import Dict, Any, Optional, List

_PROFILES: Dict[str, Dict[str, Any]] = {
    "林黛玉": {
        "惯用句式": ["……罢了", "偏……", "可不是……", "又何必……", "……也是有的"],
        "称谓": {"贾宝玉": "你/宝玉", "王熙凤": "凤姐姐", "贾母": "外祖母", "薛宝钗": "宝姐姐"},
        "禁用词": ["高兴", "开心", "没事", "搞定", "好的", "感觉", "其实", "然后"],
        "语气特征": "清冷敏感，善用反问，借景抒情，点到即止，鲜有直白表达",
        "典型句例": [
            "你且去罢，我这里不用你。",
            "这话从何说起？",
            "我有什么可说的，横竖都是你们的道理。",
        ],
    },
    "贾宝玉": {
        "惯用句式": ["我偏……", "好妹妹……", "……混账话", "……方好", "好姐姐……"],
        "称谓": {"林黛玉": "林妹妹", "薛宝钗": "宝姐姐", "王熙凤": "凤姐姐", "贾母": "老祖宗"},
        "禁用词": ["官场", "仕途经济", "高兴", "开心", "功名"],
        "语气特征": "急切直白，深情重义，厌恶仕途经济，对女儿家充满尊重",
        "典型句例": [
            "好妹妹，你别恼，我也是一时糊涂了。",
            "这些混账话，我最不爱听！",
            "我偏不依，你又能把我如何？",
        ],
    },
    "薛宝钗": {
        "惯用句式": ["……才是", "……罢了", "……方妥", "可不是这个道理", "……也就罢了"],
        "称谓": {"贾宝玉": "宝兄弟", "林黛玉": "林丫头/林妹妹", "贾母": "老太太"},
        "禁用词": ["高兴", "开心", "没事"],
        "语气特征": "端庄稳重，识大体，善劝人，藏锋露礼，不轻易表露真情",
        "典型句例": [
            "你这话虽有理，只是也要顾着些体面才是。",
            "横竖不过这样，也就罢了。",
            "姑娘家的，这话说出去不大好听。",
        ],
    },
    "王熙凤": {
        "惯用句式": ["……才罢", "……可了不得了", "哪里的话", "……我的儿", "……可不是"],
        "称谓": {"贾母": "老祖宗", "贾宝玉": "宝兄弟", "林黛玉": "林妹妹"},
        "禁用词": ["高兴", "开心"],
        "语气特征": "伶牙俐齿，快人快语，善奉承，精于算计，豪爽中藏精明",
        "典型句例": [
            "哟，这不是说笑话嘛，天下哪有这样的道理！",
            "我的儿，你可来了，老祖宗念叨你半日了。",
            "这话说的，我还不知道？",
        ],
    },
    "贾母": {
        "惯用句式": ["……才好", "……罢了", "我的……", "可不是", "……孩子们"],
        "称谓": {"贾宝玉": "宝玉/我的心肝", "林黛玉": "我的玉儿", "王熙凤": "凤丫头"},
        "禁用词": ["高兴", "开心", "搞定"],
        "语气特征": "慈祥主导，威严犹存，见多识广，善用经验劝说晚辈",
        "典型句例": [
            "我的玉儿，你又哭什么？",
            "这孩子，也太实心眼儿了。",
            "什么要紧，不过是小孩子们淘气。",
        ],
    },
    "袭人": {
        "惯用句式": ["……才是正理", "……方好", "……罢", "二爷……"],
        "称谓": {"贾宝玉": "二爷", "林黛玉": "林姑娘", "薛宝钗": "宝姑娘"},
        "禁用词": ["高兴", "开心"],
        "语气特征": "温柔体贴，劝人向好，隐忍内敛，偶见私心",
        "典型句例": [
            "二爷，这话说得不妥，仔细让太太听见了。",
            "姑娘说的是，只是也要保重自己才是。",
        ],
    },
    "紫鹃": {
        "惯用句式": ["……姑娘", "……罢", "……才好"],
        "称谓": {"林黛玉": "姑娘", "贾宝玉": "宝二爷", "袭人": "袭人姐姐"},
        "禁用词": ["高兴", "开心"],
        "语气特征": "忠心护主，直率敢言，偶有机智，对宝玉略有警惕",
        "典型句例": [
            "姑娘，外头风大，仔细着凉。",
            "宝二爷，姑娘身子不好，今儿就不留了。",
        ],
    },
    "贾探春": {
        "惯用句式": ["……才是", "……方好", "……罢了", "这话……"],
        "称谓": {"贾宝玉": "宝哥哥", "王熙凤": "凤姐姐", "贾母": "老太太"},
        "禁用词": ["高兴", "开心"],
        "语气特征": "精明果断，志向高远，洒脱大方，偶有悲凉，不甘于庶出身份",
        "典型句例": [
            "这事原也该早办了，偏偏的拖拖拉拉，成什么体统。",
            "我是庶出，也没什么好说的，只是这理终究不对。",
        ],
    },
    "史湘云": {
        "惯用句式": ["……呢", "……罢", "爱哥哥……", "可不是……"],
        "称谓": {"贾宝玉": "爱哥哥", "林黛玉": "林姐姐", "薛宝钗": "宝姐姐"},
        "禁用词": ["高兴", "开心"],
        "语气特征": "豪爽率真，乐天派，说话有些咬舌，偶用'爱哥哥'",
        "典型句例": [
            "爱哥哥，你们怎么不等我？",
            "这有什么，我们就这么办了罢。",
        ],
    },
}


class CharacterKnowledgeBase:
    """人物语言特征卡片库。"""

    def get_profile(self, character: str) -> Optional[Dict[str, Any]]:
        return _PROFILES.get(character)

    def format_constraint(self, character: str, profile: Dict[str, Any]) -> str:
        forbidden = "、".join(profile.get("禁用词", []))
        examples = "　".join(profile.get("典型句例", [])[:2])
        return (
            f"{character}：{profile.get('语气特征', '')}\n"
            f"  惯用句式：{'　'.join(profile.get('惯用句式', [])[:3])}\n"
            f"  禁用词：{forbidden}\n"
            f"  典型句例：{examples}"
        )

    def get_all_names(self) -> List[str]:
        return list(_PROFILES.keys())
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
python3 -m pytest tests/knowledge/test_character_kb.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/knowledge/character_kb.py tests/knowledge/test_character_kb.py
git commit -m "feat: add CharacterKnowledgeBase with 9 main character voice profiles"
```

---

### Task 5：ContextAssembler

**Files:**
- Create: `src/generation/context_assembler.py`
- Create: `tests/generation/test_context_assembler.py`

- [ ] **Step 1: 写失败测试**

`tests/generation/test_context_assembler.py`:

```python
import tempfile
import pytest
from src.knowledge.style_kb import StyleKnowledgeBase, StyleChunk
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.generation.context_assembler import ContextAssembler, SceneSpec


def make_kb(tmp_path):
    kb = StyleKnowledgeBase(persist_dir=str(tmp_path / "style"))
    kb.add_chunks([
        StyleChunk(
            text="宝玉道：'林妹妹，你别恼，我只是随口一说。'黛玉转过身去，并不理他。",
            chapter_num=30,
            paragraph_type="dialogue",
            characters_present=["贾宝玉", "林黛玉"],
            emotional_tone="哀愁",
        ),
        StyleChunk(
            text="只见那日天色阴沉，园中落叶纷纷，满地碎金，别有一番萧瑟意境。",
            chapter_num=27,
            paragraph_type="scenery",
            characters_present=[],
            emotional_tone="哀愁",
        ),
    ])
    return kb


def test_assemble_returns_two_strings(tmp_path):
    style_kb = make_kb(tmp_path)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉"],
        scene_description="秋日宝黛在园中对话，感时伤怀",
        emotional_tone="哀愁",
    )
    system_msg, user_prompt = assembler.assemble(spec)
    assert isinstance(system_msg, str) and len(system_msg) > 50
    assert isinstance(user_prompt, str) and len(user_prompt) > 50


def test_system_contains_original_text_example(tmp_path):
    style_kb = make_kb(tmp_path)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉"],
        scene_description="宝黛对话",
        emotional_tone="哀愁",
    )
    system_msg, _ = assembler.assemble(spec)
    # system 应含有原著片段
    assert "黛玉" in system_msg or "宝玉" in system_msg


def test_user_prompt_contains_forbidden_words_reminder(tmp_path):
    style_kb = make_kb(tmp_path)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["林黛玉"],
        scene_description="黛玉独自伤怀",
        emotional_tone="哀愁",
    )
    _, user_prompt = assembler.assemble(spec)
    assert "禁用" in user_prompt or "高兴" in user_prompt


def test_user_hint_appears_in_prompt(tmp_path):
    style_kb = make_kb(tmp_path)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉"],
        scene_description="宝玉读书",
        emotional_tone="闲散",
        user_hint="让宝玉收到一封神秘信件",
    )
    _, user_prompt = assembler.assemble(spec)
    assert "神秘信件" in user_prompt
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
python3 -m pytest tests/generation/test_context_assembler.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 ContextAssembler**

`src/generation/context_assembler.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.knowledge.style_kb import StyleKnowledgeBase
from src.knowledge.character_kb import CharacterKnowledgeBase

FORBIDDEN_WORDS = "高兴、开心、没事、感觉、其实、然后、但是（改用"却"）、好的、搞定、不错"


@dataclass
class SceneSpec:
    chapter_num: int
    characters: List[str]
    scene_description: str        # 例："秋日宝黛在大观园中对话，感时伤怀"
    emotional_tone: str           # 例："哀而不伤"
    user_hint: Optional[str] = None
    previous_summary: str = ""
    foreshadowing_must_payoff: List[str] = field(default_factory=list)
    foreshadowing_should_plant: List[str] = field(default_factory=list)


class ContextAssembler:
    """将三层知识库检索结果组装为最终 prompt。"""

    def __init__(self, style_kb: StyleKnowledgeBase, character_kb: CharacterKnowledgeBase):
        self.style_kb = style_kb
        self.character_kb = character_kb

    def assemble(self, spec: SceneSpec) -> Tuple[str, str]:
        """返回 (system_message, user_prompt) 元组。"""
        narrative_examples = self.style_kb.search(
            spec.scene_description, paragraph_type="narrative", top_k=2
        )
        dialogue_examples = self.style_kb.search(
            spec.scene_description, paragraph_type="dialogue", top_k=2
        )

        system_msg = self._build_system(narrative_examples, dialogue_examples)
        user_prompt = self._build_user(spec)
        return system_msg, user_prompt

    def _build_system(self, narrative_examples: List[str], dialogue_examples: List[str]) -> str:
        parts = [
            "你是续写《红楼梦》的笔者，笔力须与曹雪芹原著一脉相承。",
            f"绝对禁止出现以下现代词汇：{FORBIDDEN_WORDS}。",
            "叙事须用第三人称全知视角，语感古朴克制，情感含而不露。",
            "",
        ]
        if narrative_examples:
            parts.append("【原著叙事风格范例——请严格仿照以下行文节奏】")
            for i, ex in enumerate(narrative_examples, 1):
                parts.append(f"范例{i}：\n{ex[:500]}")
            parts.append("")

        if dialogue_examples:
            parts.append("【原著对话风格范例——人物说话须仿照以下语气和措辞】")
            for i, ex in enumerate(dialogue_examples, 1):
                parts.append(f"范例{i}：\n{ex[:500]}")

        return "\n".join(parts)

    def _build_user(self, spec: SceneSpec) -> str:
        parts = []

        if spec.previous_summary:
            parts += ["【前情提要】", spec.previous_summary, ""]

        # 人物语言约束
        constraints = []
        for char in spec.characters:
            profile = self.character_kb.get_profile(char)
            if profile:
                constraints.append(self.character_kb.format_constraint(char, profile))
        if constraints:
            parts += ["【本章人物语言约束】"] + constraints + [""]

        # 伏笔指令
        if spec.foreshadowing_must_payoff:
            parts.append("【本章伏笔指令】")
            parts.append("必须兑现（本章正文中必须出现）：")
            for f in spec.foreshadowing_must_payoff:
                parts.append(f"  · {f}")
            parts.append("")
        if spec.foreshadowing_should_plant:
            parts.append("建议本章埋设：")
            for f in spec.foreshadowing_should_plant:
                parts.append(f"  · {f}")
            parts.append("")

        if spec.user_hint:
            parts += [f"【读者方向（本章须体现）】", spec.user_hint, ""]

        parts += [
            "【续写任务】",
            f"请续写《红楼梦》第{spec.chapter_num}回，约2500字。",
            f"场景：{spec.scene_description}",
            f"情感基调：{spec.emotional_tone}",
            "要求：",
            "  1. 开头须自然衔接前情，不可突兀",
            "  2. 结尾须留下悬念引出下回",
            "  3. 严格模仿上方叙事和对话范例的语言节奏",
            "  4. 不得出现现代口语和白话词汇",
        ]
        return "\n".join(parts)
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
python3 -m pytest tests/generation/test_context_assembler.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/generation/context_assembler.py tests/generation/test_context_assembler.py
git commit -m "feat: add ContextAssembler - RAG-driven prompt assembly"
```

---

### Task 6：ContentWriter

**Files:**
- Create: `src/generation/content_writer.py`

- [ ] **Step 1: 实现 ContentWriter**

`src/generation/content_writer.py`:

```python
"""ContentWriter：调用 LLM，返回原始生成文本。"""
from __future__ import annotations
import asyncio
from src.config.settings import Settings
from src.agents.gpt5_client import get_gpt5_client


class ContentWriter:
    def __init__(self, settings: Settings):
        self.client = get_gpt5_client(settings)

    async def write(
        self,
        system_msg: str,
        user_prompt: str,
        chapter_num: int,
        temperature: float = 0.85,
        max_tokens: int = 6000,
    ) -> str:
        """调用 LLM，返回生成的章节文本；失败时返回空字符串。"""
        result = await self.client.generate_content(
            prompt=user_prompt,
            system_message=system_msg,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if result.get("success"):
            return result.get("content", "")
        return ""
```

- [ ] **Step 2: 快速集成验证（不写 mock 测试，直接跑真实 API）**

```bash
python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from src.config.settings import Settings
from src.generation.content_writer import ContentWriter

async def test():
    writer = ContentWriter(Settings())
    text = await writer.write(
        system_msg='你是一位古典文学作家。',
        user_prompt='请用古典文学风格写一段50字的宝玉读书的场景描写。',
        chapter_num=81,
        max_tokens=200,
    )
    print('生成结果（前100字）:', text[:100])

asyncio.run(test())
" 2>&1 | grep -v DEBUG | grep -v 已加载 | grep -v 已读取
```

Expected: 打印一段古文风格的文字

- [ ] **Step 3: Commit**

```bash
git add src/generation/content_writer.py
git commit -m "feat: add ContentWriter wrapping gpt5_client"
```

---

### Task 7：LiteraryJudge

**Files:**
- Create: `src/generation/literary_judge.py`
- Create: `tests/generation/test_literary_judge.py`

- [ ] **Step 1: 写失败测试**

`tests/generation/test_literary_judge.py`:

```python
import tempfile
from src.knowledge.style_kb import StyleKnowledgeBase, StyleChunk
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.generation.context_assembler import SceneSpec
from src.generation.literary_judge import LiteraryJudge


def make_judge(tmp_path):
    style_kb = StyleKnowledgeBase(persist_dir=str(tmp_path / "style"))
    style_kb.add_chunks([
        StyleChunk(
            text="宝玉叹道：'这花开了又谢，谢了又开，到底是为谁？'黛玉不语，只望着那池中残荷出神。",
            chapter_num=40,
            paragraph_type="dialogue",
            characters_present=["贾宝玉", "林黛玉"],
            emotional_tone="哀愁",
        )
    ])
    char_kb = CharacterKnowledgeBase()
    return LiteraryJudge(style_kb, char_kb)


GOOD_TEXT = """
    且说那日天色阴沉，宝玉漫步至潇湘馆前，只见黛玉倚窗而坐，手中一卷书，
    却并未翻动。宝玉轻叩竹帘，道："林妹妹，你在做什么呢？"
    黛玉抬起头来，眼中隐有泪光，淡淡道："不过坐着罢了，你来做什么？"
"""

BAD_TEXT = "宝玉很高兴地跑去找黛玉，开心地说：你好啊，我们今天去玩吧，感觉天气不错。"


def make_spec():
    return SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉"],
        scene_description="宝黛秋日相遇",
        emotional_tone="哀愁",
    )


def test_good_text_scores_higher_than_bad(tmp_path):
    judge = make_judge(tmp_path)
    good_result = judge.judge(GOOD_TEXT, make_spec())
    bad_result = judge.judge(BAD_TEXT, make_spec())
    assert good_result.score > bad_result.score


def test_bad_text_fails(tmp_path):
    judge = make_judge(tmp_path)
    result = judge.judge(BAD_TEXT, make_spec())
    assert not result.passed


def test_good_text_passes(tmp_path):
    judge = make_judge(tmp_path)
    result = judge.judge(GOOD_TEXT, make_spec())
    assert result.passed


def test_feedback_mentions_forbidden_word(tmp_path):
    judge = make_judge(tmp_path)
    result = judge.judge(BAD_TEXT, make_spec())
    assert "高兴" in result.feedback or "开心" in result.feedback


def test_foreshadowing_score_full_when_no_requirement(tmp_path):
    judge = make_judge(tmp_path)
    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉"],
        scene_description="宝玉读书",
        emotional_tone="闲散",
        foreshadowing_must_payoff=[],
    )
    result = judge.judge(GOOD_TEXT, spec)
    assert result.foreshadowing_score == 9.0
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
python3 -m pytest tests/generation/test_literary_judge.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现 LiteraryJudge**

`src/generation/literary_judge.py`:

```python
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import List, TYPE_CHECKING
import numpy as np

from src.knowledge.style_kb import StyleKnowledgeBase
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.generation.context_assembler import SceneSpec, ContextAssembler

if TYPE_CHECKING:
    from src.generation.content_writer import ContentWriter


@dataclass
class JudgementResult:
    score: float            # 综合分 0–10
    style_score: float      # 风格相似度得分
    voice_score: float      # 人物声音准确度得分
    foreshadowing_score: float  # 伏笔完成度得分
    feedback: str
    passed: bool


class LiteraryJudge:
    THRESHOLD = 7.0
    MAX_RETRIES = 3

    def __init__(self, style_kb: StyleKnowledgeBase, character_kb: CharacterKnowledgeBase):
        self.style_kb = style_kb
        self.character_kb = character_kb

    def judge(self, text: str, spec: SceneSpec) -> JudgementResult:
        style_score = self._score_style(text, spec)
        voice_score = self._score_voice(text, spec.characters)
        foreshadowing_score = self._score_foreshadowing(text, spec.foreshadowing_must_payoff)

        overall = style_score * 0.40 + voice_score * 0.35 + foreshadowing_score * 0.25
        feedback = self._build_feedback(style_score, voice_score, text, spec)

        return JudgementResult(
            score=round(overall, 2),
            style_score=round(style_score, 2),
            voice_score=round(voice_score, 2),
            foreshadowing_score=round(foreshadowing_score, 2),
            feedback=feedback,
            passed=overall >= self.THRESHOLD,
        )

    def _score_style(self, text: str, spec: SceneSpec) -> float:
        examples = self.style_kb.search(spec.scene_description, top_k=3)
        if not examples:
            return 6.0
        model = self.style_kb.model
        sample = text[:800]
        text_emb = model.encode([sample], normalize_embeddings=True)
        example_embs = model.encode(examples, normalize_embeddings=True)
        sims = np.dot(text_emb, example_embs.T)[0]
        avg = float(np.mean(sims))
        # cosine sim [0.25, 0.75] → score [3, 10]
        return float(np.clip((avg - 0.25) / 0.50 * 7 + 3, 3.0, 10.0))

    def _score_voice(self, text: str, characters: List[str]) -> float:
        total, violations = 0, 0
        for char in characters:
            profile = self.character_kb.get_profile(char)
            if not profile:
                continue
            for word in profile.get("禁用词", []):
                total += 1
                if word in text:
                    violations += 1
        if total == 0:
            return 8.0
        rate = violations / total
        return float(np.clip(10.0 - rate * 25, 3.0, 10.0))

    def _score_foreshadowing(self, text: str, must_payoff: List[str]) -> float:
        if not must_payoff:
            return 9.0
        fulfilled = sum(
            1 for f in must_payoff
            if any(kw.strip() in text for kw in f.split("/"))
        )
        return 10.0 * fulfilled / len(must_payoff)

    def _build_feedback(
        self, style_score: float, voice_score: float, text: str, spec: SceneSpec
    ) -> str:
        issues = []
        if style_score < 6.5:
            issues.append(
                f"叙事风格与原著相似度不足（得分{style_score:.1f}）——"
                "需更贴近原著叙事节奏，减少白话句式"
            )
        if voice_score < 7.0:
            for char in spec.characters:
                profile = self.character_kb.get_profile(char)
                if not profile:
                    continue
                found = [w for w in profile.get("禁用词", []) if w in text]
                if found:
                    issues.append(f'"{char}"出现现代口语：{"、".join(found)}')
        if not issues:
            return "内容质量良好，无明显问题。"
        return "需要改进：" + "；".join(issues)

    async def judge_and_rewrite(
        self,
        text: str,
        spec: SceneSpec,
        writer: "ContentWriter",
        assembler: ContextAssembler,
    ) -> tuple[str, JudgementResult]:
        """评分不通过时自动带反馈重写，最多 MAX_RETRIES 次，返回最高分版本。"""
        best_text, best_result = text, self.judge(text, spec)

        for attempt in range(self.MAX_RETRIES):
            if best_result.passed:
                break
            print(
                f"   ⚠️  第{attempt + 1}次重写（得分{best_result.score:.1f}）"
                f"：{best_result.feedback[:60]}…"
            )
            system_msg, user_prompt = assembler.assemble(spec)
            user_prompt += (
                f"\n\n【上次评审反馈，本次须针对以下问题改写】\n{best_result.feedback}"
            )
            new_text = await writer.write(system_msg, user_prompt, spec.chapter_num)
            if not new_text:
                break
            new_result = self.judge(new_text, spec)
            if new_result.score > best_result.score:
                best_text, best_result = new_text, new_result

        if not best_result.passed:
            print(f"   ⚠️  {self.MAX_RETRIES}次重写后仍未达标（{best_result.score:.1f}），保留最高分版本。")

        return best_text, best_result
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
python3 -m pytest tests/generation/test_literary_judge.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/generation/literary_judge.py tests/generation/test_literary_judge.py
git commit -m "feat: add LiteraryJudge with vector-based style scoring and auto-rewrite"
```

---

### Task 8：run_ch81.py — 端到端生成第81回

**Files:**
- Create: `run_ch81.py`

- [ ] **Step 1: 实现入口脚本**

`run_ch81.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 入口：生成《红楼梦》第81回。

用法：
  python3 run_ch81.py
  python3 run_ch81.py --hint "让宝玉在园中偶然发现一封旧信"
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings
from src.knowledge.style_kb import StyleKnowledgeBase
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.knowledge.builder import build_style_kb
from src.generation.context_assembler import ContextAssembler, SceneSpec
from src.generation.content_writer import ContentWriter
from src.generation.literary_judge import LiteraryJudge


PREVIOUS_SUMMARY = (
    "第八十回：宝玉因扇坠落水之事，惹得袭人等人忧虑。"
    "黛玉身体依旧虚弱，日夜咳嗽。贾府上下忙于迎接贵客，"
    "王夫人私下与薛姨妈议论宝玉婚事，气氛渐趋紧张。"
    "宝黛于暮色中于园内短暂相遇，各怀心事，欲言又止。"
)

CH81_SCENE = SceneSpec(
    chapter_num=81,
    characters=["贾宝玉", "林黛玉", "袭人", "紫鹃"],
    scene_description=(
        "秋日午后，宝玉在怡红院中百无聊赖，前往潇湘馆探望黛玉。"
        "二人在竹林小径间漫步，话及诗词，感叹时世，各怀愁绪。"
        "傍晚时分忽有消息传来，令二人各自心惊。"
    ),
    emotional_tone="哀而不伤，含蓄蕴藉",
    previous_summary=PREVIOUS_SUMMARY,
    foreshadowing_should_plant=[
        "黛玉身体每况愈下，暗示凶兆",
        "宝玉对仕途经济愈加厌倦，只恨不能长守园中",
    ],
)


async def main(user_hint: str = None):
    print("=" * 60)
    print("📚 AI续写红楼梦 · Phase 1 · 第81回")
    print("=" * 60)

    settings = Settings()

    # 1. 确保知识库已构建
    print("\n[1/4] 加载/构建风格层知识库...")
    style_kb = build_style_kb()
    char_kb = CharacterKnowledgeBase()

    # 2. 组装 prompt
    print("[2/4] 组装上下文 prompt...")
    assembler = ContextAssembler(style_kb, char_kb)
    spec = CH81_SCENE
    if user_hint:
        spec.user_hint = user_hint
        print(f"      读者方向：{user_hint}")

    system_msg, user_prompt = assembler.assemble(spec)
    print(f"      system_msg: {len(system_msg)} 字符")
    print(f"      user_prompt: {len(user_prompt)} 字符")

    # 3. 生成内容
    print("[3/4] 调用 gpt-5.4 生成第81回...")
    writer = ContentWriter(settings)
    raw_text = await writer.write(system_msg, user_prompt, chapter_num=81)

    if not raw_text:
        print("❌ 生成失败，请检查 API 配置。")
        sys.exit(1)

    # 4. 评判 + 自动重写
    print("[4/4] LiteraryJudge 评分...")
    judge = LiteraryJudge(style_kb, char_kb)
    final_text, result = await judge.judge_and_rewrite(raw_text, spec, writer, assembler)

    print(f"\n✅ 生成完成")
    print(f"   综合得分：{result.score:.2f}/10.0")
    print(f"   风格相似度：{result.style_score:.2f}")
    print(f"   人物声音：{result.voice_score:.2f}")
    print(f"   伏笔完成度：{result.foreshadowing_score:.2f}")
    print(f"   评语：{result.feedback}")

    # 保存结果
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(f"output/ch81_{ts}")
    out_dir.mkdir(parents=True, exist_ok=True)

    chapter_file = out_dir / "chapter_081.md"
    chapter_file.write_text(
        f"# 第八十一回\n\n{final_text}\n\n"
        f"---\n*综合得分：{result.score:.2f}/10.0 · 生成时间：{ts}*\n",
        encoding="utf-8",
    )
    report_file = out_dir / "quality_report.md"
    report_file.write_text(
        f"# 质量报告 · 第81回\n\n"
        f"- 综合得分：{result.score:.2f}/10.0\n"
        f"- 风格相似度：{result.style_score:.2f}\n"
        f"- 人物声音准确度：{result.voice_score:.2f}\n"
        f"- 伏笔完成度：{result.foreshadowing_score:.2f}\n"
        f"- 评语：{result.feedback}\n",
        encoding="utf-8",
    )

    print(f"\n💾 输出目录：{out_dir}")
    print(f"📖 章节文件：{chapter_file}")
    print("\n" + "=" * 60)
    print("第81回前300字预览：")
    print("=" * 60)
    print(final_text[:300])
    print("…")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成红楼梦第81回")
    parser.add_argument("--hint", type=str, default=None, help="读者方向，一句话引导情节")
    args = parser.parse_args()
    asyncio.run(main(user_hint=args.hint))
```

- [ ] **Step 2: 运行 Phase 1 端到端测试**

```bash
python3 run_ch81.py
```

Expected 输出：
```
============================================================
📚 AI续写红楼梦 · Phase 1 · 第81回
============================================================

[1/4] 加载/构建风格层知识库...
   知识库已存在 XXXX 条记录，跳过重建。
[2/4] 组装上下文 prompt...
[3/4] 调用 gpt-5.4 生成第81回...
[4/4] LiteraryJudge 评分...

✅ 生成完成
   综合得分：X.XX/10.0
   ...
💾 输出目录：output/ch81_XXXXXXXX_XXXXXX
```

- [ ] **Step 3: 带用户引导测试**

```bash
python3 run_ch81.py --hint "让宝玉在园中偶然捡到黛玉的一首未完成的诗稿"
```

Expected：输出中包含"诗稿"相关情节

- [ ] **Step 4: Commit**

```bash
git add run_ch81.py
git commit -m "feat: Phase 1 complete - run_ch81.py end-to-end generation with RAG+LiteraryJudge"
```

---

## Phase 2：故事连贯性（连续3回）

---

### Task 9a：state_schema.py — 五层数据结构

**Files:**
- Create: `src/story/state_schema.py`

- [x] **Step 1: 写失败测试**

`tests/story/__init__.py`（空文件，先创建目录）:

```bash
mkdir -p tests/story
touch tests/story/__init__.py
```

`tests/story/test_story_state.py`（先写测试，后面 Task 9b 实现代码时运行）:

```python
import json
import pytest
from pathlib import Path

from src.story.state_schema import (
    ProphecyAnchor,
    CharacterStateEntry,
    ToneRecord,
    NarrativePacing,
    ForeshadowingDebt,
)
from src.story.story_state import StoryState, SceneHints


# ── Fixtures ──────────────────────────────────────────────────────────────

def make_state_with_debt(urgency_weight: float, chapters_since_hint: int) -> StoryState:
    state = StoryState()
    state.foreshadowing_debts = [
        ForeshadowingDebt(
            id="fd_001",
            description="黛玉泪尽而逝",
            source="原著第5回",
            keywords=["泪尽", "香消"],
            planted_at_chapter=5,
            last_hinted_chapter=75,
            chapters_since_hint=chapters_since_hint,
            urgency_weight=urgency_weight,
            status="pending",
        )
    ]
    return state


# ── StoryState 基础 ────────────────────────────────────────────────────────

def test_initial_state_has_chapter_80():
    state = StoryState()
    assert state.current_chapter == 80


def test_to_scene_hints_returns_scene_hints_type():
    state = StoryState()
    hints = state.to_scene_hints(characters=["贾宝玉"])
    assert isinstance(hints, SceneHints)


def test_to_scene_hints_uses_chapter_summary_as_previous_summary():
    state = StoryState()
    state.chapter_summary = "第81回：宝黛秋日相遇，各怀心事。"
    hints = state.to_scene_hints(characters=[])
    assert hints.previous_summary == "第81回：宝黛秋日相遇，各怀心事。"


def test_to_scene_hints_high_urgency_debt_in_must_payoff():
    state = make_state_with_debt(urgency_weight=0.8, chapters_since_hint=0)
    hints = state.to_scene_hints(characters=[])
    assert any("黛玉泪尽而逝" in item for item in hints.foreshadowing_must_payoff)


def test_to_scene_hints_overdue_debt_in_must_payoff():
    """chapters_since_hint >= 8 应强制进入 must_payoff"""
    state = make_state_with_debt(urgency_weight=0.2, chapters_since_hint=9)
    hints = state.to_scene_hints(characters=[])
    assert any("黛玉泪尽而逝" in item for item in hints.foreshadowing_must_payoff)


def test_to_scene_hints_thematic_keywords_in_should_plant():
    state = StoryState()
    state.current_thematic_keywords = ["秋", "竹影", "药香"]
    hints = state.to_scene_hints(characters=[])
    for kw in ["秋", "竹影", "药香"]:
        assert kw in hints.foreshadowing_should_plant


def test_to_scene_hints_suggests_emotional_tone_from_character():
    state = StoryState()
    state.character_states["林黛玉"] = CharacterStateEntry(
        health_trend="衰退",
        emotional_center="凄婉",
        last_scene_chapter=81,
        notes="",
    )
    hints = state.to_scene_hints(characters=["林黛玉"])
    assert "凄婉" in hints.suggested_emotional_tone


# ── 持久化 ─────────────────────────────────────────────────────────────────

def test_save_creates_chapter_file(tmp_path):
    state = StoryState(_state_dir=str(tmp_path))
    state.chapter_summary = "宝黛相遇。"
    saved_path = state.save(chapter_num=81)
    assert saved_path.exists()
    assert "state_ch081" in saved_path.name


def test_load_roundtrip_preserves_fields(tmp_path):
    state = StoryState(_state_dir=str(tmp_path))
    state.current_chapter = 81
    state.chapter_summary = "第81回摘要。"
    state.current_thematic_keywords = ["秋", "残荷"]
    state.character_states["贾宝玉"] = CharacterStateEntry(
        health_trend="平稳",
        emotional_center="怅惘",
        last_scene_chapter=81,
        notes="丢玉征兆",
    )
    saved_path = state.save(chapter_num=81)

    loaded = StoryState.load(str(saved_path))
    assert loaded.current_chapter == 81
    assert loaded.chapter_summary == "第81回摘要。"
    assert loaded.current_thematic_keywords == ["秋", "残荷"]
    assert loaded.character_states["贾宝玉"].emotional_center == "怅惘"


def test_load_latest_returns_newest_snapshot(tmp_path):
    for ch in [81, 82, 83]:
        s = StoryState(_state_dir=str(tmp_path))
        s.current_chapter = ch
        s.save(chapter_num=ch)

    latest = StoryState.load_latest(str(tmp_path))
    assert latest.current_chapter == 83


def test_load_latest_returns_default_when_dir_empty(tmp_path):
    state = StoryState.load_latest(str(tmp_path))
    assert state.current_chapter == 80


# ── update_from_analysis ───────────────────────────────────────────────────

def test_update_increments_chapters_since_hint():
    from src.story.prophecy_analyst import AnalysisResult
    state = make_state_with_debt(urgency_weight=0.3, chapters_since_hint=3)
    result = AnalysisResult(
        chapter_num=82,
        chapter_summary="贾府近况。",
        detected_prophecy_ids=[],
        resolved_debt_ids=[],
        new_thematic_keywords=["秋"],
        tone="衰寂",
        ending_type="悬念",
    )
    state.update_from_analysis(result)
    assert state.foreshadowing_debts[0].chapters_since_hint == 4


def test_update_marks_resolved_debt():
    from src.story.prophecy_analyst import AnalysisResult
    state = make_state_with_debt(urgency_weight=0.5, chapters_since_hint=2)
    result = AnalysisResult(
        chapter_num=82,
        chapter_summary="黛玉泪尽。",
        detected_prophecy_ids=[],
        resolved_debt_ids=["fd_001"],
        new_thematic_keywords=[],
        tone="悲恸",
        ending_type="收束",
    )
    state.update_from_analysis(result)
    assert state.foreshadowing_debts[0].status == "resolved"


def test_update_keeps_recent_tone_streak_max_3():
    from src.story.prophecy_analyst import AnalysisResult
    state = StoryState()
    for ch, tone in [(79, "热闹"), (80, "衰寂"), (81, "衰寂"), (82, "过渡")]:
        state.update_from_analysis(AnalysisResult(
            chapter_num=ch,
            chapter_summary="",
            detected_prophecy_ids=[],
            resolved_debt_ids=[],
            new_thematic_keywords=[],
            tone=tone,
            ending_type="悬念",
        ))
    assert len(state.narrative_pacing.recent_tone_streak) == 3
    assert state.narrative_pacing.recent_tone_streak[-1].tone == "过渡"
```

- [x] **Step 2: 运行测试，确认报 ImportError（预期失败）**

```bash
cd /path/to/worktree  # 在 worktree 目录下运行
python3 -m pytest tests/story/test_story_state.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'src.story.state_schema'`

- [x] **Step 3: 创建 `src/story/state_schema.py`**

```python
"""五层故事状态机的数据结构定义。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class ProphecyAnchor:
    """L1：判词意象层 — 跟踪十二钗判词的激活与兑现。"""
    id: str
    character: str
    prophecy_fragment: str
    keywords: List[str]
    activated_at_chapter: int
    urgency: str  # dormant | building | peak | resolved


@dataclass
class ToneRecord:
    """L4 辅助：单章叙事基调记录。"""
    chapter: int
    tone: str  # 热闹 | 衰寂 | 忧虑 | 悲恸 | 过渡


@dataclass
class NarrativePacing:
    """L4：叙事节奏层 — 防止连续多章基调相同。"""
    recent_tone_streak: List[ToneRecord] = field(default_factory=list)
    last_chapter_ending: str = "收束"   # 悬念 | 收束 | 过渡
    suggested_next_tone: str = "平稳"
    notes: str = ""


@dataclass
class CharacterStateEntry:
    """L3：人物概况层 — 定性描述，不用数字。"""
    health_trend: str = "平稳"    # 平稳 | 衰退 | 危急 | 已逝
    emotional_center: str = "平静"
    last_scene_chapter: int = 80
    notes: str = ""


@dataclass
class ForeshadowingDebt:
    """L5：伏笔债务层 — 追踪每条伏笔的压力与兑现进度。"""
    id: str
    description: str
    source: str
    keywords: List[str]
    planted_at_chapter: int
    last_hinted_chapter: int
    chapters_since_hint: int
    urgency_weight: float   # 0.0–1.0
    status: str             # pending | hinting | resolved
```

- [x] **Step 4: Commit schema**

```bash
git add src/story/state_schema.py tests/story/__init__.py tests/story/test_story_state.py
git commit -m "feat: add state_schema.py with 5-layer dataclasses + failing tests"
```

---

### Task 9b：story_state.py — StoryState 主类

**Files:**
- Create: `src/story/story_state.py`

- [x] **Step 1: 实现 `src/story/story_state.py`**

```python
"""StoryState：五层故事状态机，跨章节共享语境。"""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

from src.story.state_schema import (
    ProphecyAnchor,
    CharacterStateEntry,
    ToneRecord,
    NarrativePacing,
    ForeshadowingDebt,
)

if TYPE_CHECKING:
    from src.story.prophecy_analyst import AnalysisResult

HINT_THRESHOLD = 8        # 超过此章数强制兑现
HIGH_URGENCY_THRESHOLD = 0.7  # 权重高于此值强制兑现


@dataclass
class SceneHints:
    """StoryState 给 StoryDirector 的语境摘要，直接映射到 SceneSpec 字段。"""
    previous_summary: str
    foreshadowing_must_payoff: List[str]
    foreshadowing_should_plant: List[str]
    suggested_emotional_tone: str
    suggested_next_tone: str


@dataclass
class StoryState:
    # ── 基础 ──
    current_chapter: int = 80

    # ── L1：判词意象层 ──
    active_prophecies: List[ProphecyAnchor] = field(default_factory=list)
    current_thematic_keywords: List[str] = field(default_factory=list)

    # ── L2：剧情旗帜层 ──
    milestones: Dict[str, bool] = field(default_factory=lambda: {
        "宝玉丢玉": False,
        "大观园抄检": False,
        "黛玉焚稿": False,
        "金玉良缘订立": False,
        "贾府获罪抄家": False,
        "宝玉出家": False,
    })
    chapter_summary: str = ""

    # ── L3：人物概况层 ──
    character_states: Dict[str, CharacterStateEntry] = field(default_factory=dict)

    # ── L4：叙事节奏层 ──
    narrative_pacing: NarrativePacing = field(default_factory=NarrativePacing)

    # ── L5：伏笔债务层 ──
    foreshadowing_debts: List[ForeshadowingDebt] = field(default_factory=list)

    # ── 内部 ──
    _state_dir: str = field(default="outputs/state", repr=False)

    # ─────────────────────────────────────────────
    # Pre-chapter：给 StoryDirector 提供语境
    # ─────────────────────────────────────────────

    def to_scene_hints(self, characters: List[str]) -> SceneHints:
        """将当前状态转换为下一章 SceneSpec 所需的附加参数。"""
        must_payoff = [
            d.description
            for d in self.foreshadowing_debts
            if d.status == "pending" and (
                d.urgency_weight >= HIGH_URGENCY_THRESHOLD
                or d.chapters_since_hint >= HINT_THRESHOLD
            )
        ]
        should_plant = list(self.current_thematic_keywords) + [
            d.description
            for d in self.foreshadowing_debts
            if d.status == "pending"
            and d.urgency_weight < HIGH_URGENCY_THRESHOLD
            and d.chapters_since_hint < HINT_THRESHOLD
        ]

        emotional_tone = self._dominant_emotional_tone(characters)

        return SceneHints(
            previous_summary=self.chapter_summary,
            foreshadowing_must_payoff=must_payoff,
            foreshadowing_should_plant=should_plant,
            suggested_emotional_tone=emotional_tone,
            suggested_next_tone=self.narrative_pacing.suggested_next_tone,
        )

    def _dominant_emotional_tone(self, characters: List[str]) -> str:
        centers = [
            self.character_states[c].emotional_center
            for c in characters
            if c in self.character_states
        ]
        if not centers:
            return "哀而不伤"
        return "、".join(dict.fromkeys(centers))  # 去重保序

    # ─────────────────────────────────────────────
    # Post-chapter：接收 ProphecyAnalyst 结果并更新
    # ─────────────────────────────────────────────

    def update_from_analysis(self, result: "AnalysisResult") -> None:
        """用 ProphecyAnalyst 的分析结果更新全部五层状态。"""
        self.current_chapter = result.chapter_num
        self.chapter_summary = f"第{result.chapter_num}回：{result.chapter_summary}"
        self.current_thematic_keywords = result.new_thematic_keywords

        # L1：升级命中的判词意象
        for anchor in self.active_prophecies:
            if anchor.id in result.detected_prophecy_ids:
                _upgrade_urgency(anchor)

        # L5：标记已兑现的债务，递增其余
        for debt in self.foreshadowing_debts:
            if debt.id in result.resolved_debt_ids:
                debt.status = "resolved"
            elif debt.status == "pending":
                debt.chapters_since_hint += 1

        # L4：更新节奏记录（保留最近3章）
        pacing = self.narrative_pacing
        pacing.recent_tone_streak.append(
            ToneRecord(chapter=result.chapter_num, tone=result.tone)
        )
        if len(pacing.recent_tone_streak) > 3:
            pacing.recent_tone_streak = pacing.recent_tone_streak[-3:]
        pacing.last_chapter_ending = result.ending_type
        pacing.suggested_next_tone = _compute_next_tone(pacing)

    # ─────────────────────────────────────────────
    # 持久化
    # ─────────────────────────────────────────────

    def save(self, chapter_num: int) -> Path:
        """保存快照到 {_state_dir}/state_ch{chapter_num:03d}.json。"""
        out_dir = Path(self._state_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"state_ch{chapter_num:03d}.json"
        path.write_text(
            json.dumps(_to_dict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, path: str) -> "StoryState":
        """从指定路径加载快照。"""
        p = Path(path)
        if not p.exists():
            return cls()
        return _from_dict(json.loads(p.read_text(encoding="utf-8")))

    @classmethod
    def load_latest(cls, state_dir: str = "outputs/state") -> "StoryState":
        """加载 state_dir 中章节编号最大的快照；目录为空时返回默认初始状态。"""
        snapshots = sorted(Path(state_dir).glob("state_ch*.json"))
        if not snapshots:
            return cls(_state_dir=state_dir)
        latest = cls.load(str(snapshots[-1]))
        latest._state_dir = state_dir
        return latest


# ──────────────────────────────────────────────────────
# 内部辅助函数（模块私有）
# ──────────────────────────────────────────────────────

_URGENCY_ORDER = ["dormant", "building", "peak", "resolved"]


def _upgrade_urgency(anchor: ProphecyAnchor) -> None:
    try:
        idx = _URGENCY_ORDER.index(anchor.urgency)
        if idx < len(_URGENCY_ORDER) - 1:
            anchor.urgency = _URGENCY_ORDER[idx + 1]
    except ValueError:
        pass


def _compute_next_tone(pacing: NarrativePacing) -> str:
    tones = [r.tone for r in pacing.recent_tone_streak]
    if tones.count("衰寂") >= 2:
        return "过渡"
    if pacing.last_chapter_ending == "悬念":
        return "收束"
    return "平稳"


def _to_dict(state: StoryState) -> dict:
    return {
        "current_chapter": state.current_chapter,
        "active_prophecies": [asdict(p) for p in state.active_prophecies],
        "current_thematic_keywords": state.current_thematic_keywords,
        "milestones": state.milestones,
        "chapter_summary": state.chapter_summary,
        "character_states": {
            name: asdict(cs) for name, cs in state.character_states.items()
        },
        "narrative_pacing": asdict(state.narrative_pacing),
        "foreshadowing_debts": [asdict(d) for d in state.foreshadowing_debts],
    }


def _from_dict(data: dict) -> StoryState:
    state = StoryState()
    state.current_chapter = data.get("current_chapter", 80)
    state.chapter_summary = data.get("chapter_summary", "")
    state.current_thematic_keywords = data.get("current_thematic_keywords", [])
    state.milestones = data.get("milestones", state.milestones)

    state.active_prophecies = [
        ProphecyAnchor(**p) for p in data.get("active_prophecies", [])
    ]
    state.character_states = {
        name: CharacterStateEntry(**cs)
        for name, cs in data.get("character_states", {}).items()
    }
    pacing_data = data.get("narrative_pacing", {})
    streak = [ToneRecord(**r) for r in pacing_data.get("recent_tone_streak", [])]
    state.narrative_pacing = NarrativePacing(
        recent_tone_streak=streak,
        last_chapter_ending=pacing_data.get("last_chapter_ending", "收束"),
        suggested_next_tone=pacing_data.get("suggested_next_tone", "平稳"),
        notes=pacing_data.get("notes", ""),
    )
    state.foreshadowing_debts = [
        ForeshadowingDebt(**d) for d in data.get("foreshadowing_debts", [])
    ]
    return state
```

- [x] **Step 2: 运行测试，确认全部通过**

```bash
python3 -m pytest tests/story/test_story_state.py -v
```

Expected: 13 passed（含 `test_update_*` 3 个，此时 `AnalysisResult` 尚未实现，会报 ImportError — 先跳过那 3 个）

实际上 `update_from_analysis` 的测试依赖 `AnalysisResult`，在 Task 9c 之前先只跑不依赖它的测试：

```bash
python3 -m pytest tests/story/test_story_state.py -v -k "not update"
```

Expected: 10 passed

- [x] **Step 3: Commit**

```bash
git add src/story/story_state.py
git commit -m "feat: add StoryState with 5-layer schema, to_scene_hints, save/load/load_latest"
```

---

### Task 9c：prophecy_analyst.py — 自动分析引擎

**Files:**
- Create: `src/story/prophecy_analyst.py`
- Create: `tests/story/test_prophecy_analyst.py`
- Create: `data/knowledge_base/prophecies/canonical.json`

- [x] **Step 1: 创建十二钗判词数据**

`data/knowledge_base/prophecies/canonical.json`:

```json
[
  {
    "id": "pa_001",
    "character": "林黛玉",
    "prophecy_fragment": "玉带林中挂，金簪雪里埋（黛）",
    "keywords": ["泪尽", "还债", "香消", "玉殒", "归去", "飘零", "泪"],
    "initial_urgency": "dormant"
  },
  {
    "id": "pa_002",
    "character": "薛宝钗",
    "prophecy_fragment": "金簪雪里埋（钗）",
    "keywords": ["金玉", "良缘", "孤守", "独居", "孤寒"],
    "initial_urgency": "dormant"
  },
  {
    "id": "pa_003",
    "character": "贾元春",
    "prophecy_fragment": "二十年来辨是非，榴花开处照宫闱",
    "keywords": ["宫中", "薨", "宫闱", "噩耗", "驾崩"],
    "initial_urgency": "dormant"
  },
  {
    "id": "pa_004",
    "character": "贾探春",
    "prophecy_fragment": "才自精明志自高，生于末世运偏消",
    "keywords": ["远嫁", "和亲", "离去", "别离", "海外"],
    "initial_urgency": "dormant"
  },
  {
    "id": "pa_005",
    "character": "王熙凤",
    "prophecy_fragment": "一从二令三人木，哭向金陵事更哀",
    "keywords": ["金陵", "失势", "休弃", "哀哭", "衰败"],
    "initial_urgency": "dormant"
  }
]
```

- [x] **Step 2: 写失败测试**

`tests/story/test_prophecy_analyst.py`:

```python
import pytest
from src.story.state_schema import ProphecyAnchor, ForeshadowingDebt
from src.story.story_state import StoryState
from src.story.prophecy_analyst import ProphecyAnalyst, AnalysisResult


GOOD_TEXT = (
    "且说那日黛玉独坐窗前，泪痕犹湿，手中诗稿已被泪水洇透，"
    "自思此身飘零，不知归处。宝玉在外，怅惘难言，只觉世事难凭。"
    "园中落叶纷纷，秋意愈深，竹影摇曳，药香隐约。"
    "傍晚忽有急信传来，宝玉大惊，园中静气一变，且听下回分解。"
)

SAD_TEXT = "黛玉哭泣，泪尽而逝，香消玉殒，令人悲恸。"

HAPPY_TEXT = "众人在花厅中饮宴，热闹非凡，笑语盈盈，一派欢腾。"


def make_state_with_prophecy() -> StoryState:
    state = StoryState()
    state.active_prophecies = [
        ProphecyAnchor(
            id="pa_001",
            character="林黛玉",
            prophecy_fragment="玉带林中挂",
            keywords=["泪尽", "香消", "飘零"],
            activated_at_chapter=85,
            urgency="building",
        )
    ]
    state.foreshadowing_debts = [
        ForeshadowingDebt(
            id="fd_001",
            description="黛玉泪尽而逝",
            source="原著第5回",
            keywords=["泪尽", "香消"],
            planted_at_chapter=5,
            last_hinted_chapter=80,
            chapters_since_hint=2,
            urgency_weight=0.4,
            status="pending",
        )
    ]
    return state


def test_analyze_returns_analysis_result():
    analyst = ProphecyAnalyst()
    state = make_state_with_prophecy()
    result = analyst.analyze(GOOD_TEXT, state, chapter_num=86, chapter_summary="宝黛秋日。")
    assert isinstance(result, AnalysisResult)
    assert result.chapter_num == 86


def test_detect_prophecy_keywords_in_text():
    analyst = ProphecyAnalyst()
    state = make_state_with_prophecy()
    result = analyst.analyze(SAD_TEXT, state, chapter_num=86, chapter_summary="黛玉逝。")
    assert "pa_001" in result.detected_prophecy_ids


def test_no_prophecy_hit_when_keywords_absent():
    analyst = ProphecyAnalyst()
    state = make_state_with_prophecy()
    result = analyst.analyze(HAPPY_TEXT, state, chapter_num=86, chapter_summary="宴饮。")
    assert "pa_001" not in result.detected_prophecy_ids


def test_detect_resolved_debt_when_keywords_present():
    analyst = ProphecyAnalyst()
    state = make_state_with_prophecy()
    result = analyst.analyze(SAD_TEXT, state, chapter_num=86, chapter_summary="黛玉逝。")
    assert "fd_001" in result.resolved_debt_ids


def test_tone_detection_sad_text():
    analyst = ProphecyAnalyst()
    state = StoryState()
    result = analyst.analyze(SAD_TEXT, state, chapter_num=86, chapter_summary="")
    assert result.tone in ("衰寂", "悲恸")


def test_tone_detection_happy_text():
    analyst = ProphecyAnalyst()
    state = StoryState()
    result = analyst.analyze(HAPPY_TEXT, state, chapter_num=86, chapter_summary="")
    assert result.tone == "热闹"


def test_ending_type_suspense_detected():
    analyst = ProphecyAnalyst()
    state = StoryState()
    result = analyst.analyze(GOOD_TEXT, state, chapter_num=86, chapter_summary="")
    assert result.ending_type == "悬念"


def test_thematic_keywords_extracted():
    analyst = ProphecyAnalyst()
    state = StoryState()
    result = analyst.analyze(GOOD_TEXT, state, chapter_num=86, chapter_summary="")
    assert len(result.new_thematic_keywords) >= 1


def test_full_pipeline_update_from_analysis():
    """analyze 结果能正确更新 StoryState。"""
    analyst = ProphecyAnalyst()
    state = make_state_with_prophecy()
    result = analyst.analyze(SAD_TEXT, state, chapter_num=86, chapter_summary="黛玉逝。")
    state.update_from_analysis(result)
    # 判词意象应升级
    assert state.active_prophecies[0].urgency in ("peak", "resolved")
    # 债务应标记 resolved
    assert state.foreshadowing_debts[0].status == "resolved"
    # 章节应更新
    assert state.current_chapter == 86
```

- [x] **Step 3: 运行测试，确认失败**

```bash
python3 -m pytest tests/story/test_prophecy_analyst.py -v 2>&1 | head -10
```

Expected: `ModuleNotFoundError: No module named 'src.story.prophecy_analyst'`

- [x] **Step 4: 实现 `src/story/prophecy_analyst.py`**

```python
"""ProphecyAnalyst：章节生成后自动分析文本，更新 StoryState 的五层状态。"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List

from src.story.story_state import StoryState

# ── 基调关键词词表 ─────────────────────────────────────────────────────────

_TONE_PATTERNS = {
    "悲恸": ["泣", "哭", "痛哭", "悲恸", "号啕", "垂泪", "泪如雨"],
    "衰寂": ["凋零", "凄清", "寂寥", "残荷", "落叶", "秋风", "衰", "飘零", "萧瑟"],
    "忧虑": ["忧虑", "不安", "心惊", "愁", "忧", "惶", "惴"],
    "热闹": ["欢笑", "热闹", "笑语", "饮宴", "欢腾", "嬉笑", "喜"],
    "过渡": ["平静", "平常", "如常"],
}

_THEMATIC_SOURCES = ["秋", "冬", "哭", "笑", "泪", "雪", "残荷", "竹", "药", "风", "月", "花"]

_SUSPENSE_ENDINGS = re.compile(
    r"(且听下回分解|忽[有闻见]|急报|消息传来|不知后事如何|且慢|究竟如何|变故)"
)
_CLOSURE_ENDINGS = re.compile(r"(各自散去|方才罢了|一时无话|遂各安歇|此事方了|就此别过)")


@dataclass
class AnalysisResult:
    chapter_num: int
    chapter_summary: str
    detected_prophecy_ids: List[str]
    resolved_debt_ids: List[str]
    new_thematic_keywords: List[str]
    tone: str        # 热闹 | 衰寂 | 忧虑 | 悲恸 | 过渡
    ending_type: str  # 悬念 | 收束 | 过渡


class ProphecyAnalyst:
    """无状态的分析器，接收文本和当前 StoryState，输出 AnalysisResult。"""

    def analyze(
        self,
        text: str,
        state: StoryState,
        chapter_num: int,
        chapter_summary: str,
    ) -> AnalysisResult:
        return AnalysisResult(
            chapter_num=chapter_num,
            chapter_summary=chapter_summary,
            detected_prophecy_ids=self._detect_prophecy_hits(text, state),
            resolved_debt_ids=self._detect_resolved_debts(text, state),
            new_thematic_keywords=self._extract_thematic_keywords(text),
            tone=self._detect_tone(text),
            ending_type=self._detect_ending_type(text),
        )

    def _detect_prophecy_hits(self, text: str, state: StoryState) -> List[str]:
        return [
            anchor.id
            for anchor in state.active_prophecies
            if anchor.urgency != "resolved"
            and any(kw in text for kw in anchor.keywords)
        ]

    def _detect_resolved_debts(self, text: str, state: StoryState) -> List[str]:
        return [
            debt.id
            for debt in state.foreshadowing_debts
            if debt.status == "pending"
            and any(kw in text for kw in debt.keywords)
        ]

    def _extract_thematic_keywords(self, text: str) -> List[str]:
        return [kw for kw in _THEMATIC_SOURCES if kw in text]

    def _detect_tone(self, text: str) -> str:
        scores = {tone: 0 for tone in _TONE_PATTERNS}
        for tone, patterns in _TONE_PATTERNS.items():
            for pat in patterns:
                scores[tone] += text.count(pat)
        best = max(scores, key=lambda t: scores[t])
        return best if scores[best] > 0 else "过渡"

    def _detect_ending_type(self, text: str) -> str:
        # 取最后200字判断结尾类型
        tail = text[-200:]
        if _SUSPENSE_ENDINGS.search(tail):
            return "悬念"
        if _CLOSURE_ENDINGS.search(tail):
            return "收束"
        return "过渡"
```

- [x] **Step 5: 运行全部 story 测试，确认通过**

```bash
python3 -m pytest tests/story/ -v
```

Expected: 22 passed（含 `test_story_state.py` 13 个 + `test_prophecy_analyst.py` 9 个）

- [x] **Step 6: 运行 `test_story_state.py` 中之前跳过的 `update_*` 测试**

```bash
python3 -m pytest tests/story/test_story_state.py -v -k "update"
```

Expected: 3 passed

- [x] **Step 7: Commit**

```bash
git add src/story/prophecy_analyst.py \
        src/story/story_state.py \
        data/knowledge_base/prophecies/canonical.json \
        tests/story/test_prophecy_analyst.py
git commit -m "feat: add ProphecyAnalyst + canonical prophecy data, complete Task 9 story layer"
```

---

### Task 10：ForeshadowingKnowledgeBase

**Files:**
- Create: `src/knowledge/foreshadowing_kb.py`

- [ ] **Step 1: 实现 ForeshadowingKnowledgeBase**

`src/knowledge/foreshadowing_kb.py`:

```python
"""伏笔知识库：管理原著静态伏笔和动态新增伏笔。"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class ForeshadowingTask:
    must_payoff: List[str]   # 本章必须兑现的伏笔描述
    should_plant: List[str]  # 本章建议埋设的新伏笔
    active_threads: List[str]  # 进行中的伏笔线（背景信息）


class ForeshadowingKnowledgeBase:
    def __init__(
        self,
        canonical_path: str = "data/knowledge_base/foreshadowing/canonical.json",
    ):
        self.canonical: List[Dict[str, Any]] = []
        p = Path(canonical_path)
        if p.exists():
            self.canonical = json.loads(p.read_text(encoding="utf-8"))

    def get_chapter_tasks(
        self, chapter_num: int, active_dynamic: List[str] = None
    ) -> ForeshadowingTask:
        must_payoff = []
        active_threads = []

        for f in self.canonical:
            if f["status"] == "pending":
                lo, hi = f["expected_payoff_range"]
                hint = f["hint_text"]
                if lo <= chapter_num <= hi:
                    must_payoff.append(f'{f["character"]}的伏笔："{hint}"')
                elif chapter_num < lo:
                    active_threads.append(hint)

        return ForeshadowingTask(
            must_payoff=must_payoff,
            should_plant=[],
            active_threads=active_threads + (active_dynamic or []),
        )

    def mark_resolved(self, foreshadowing_id: str) -> None:
        for f in self.canonical:
            if f["id"] == foreshadowing_id:
                f["status"] = "resolved"
                break
```

- [ ] **Step 2: 快速验证**

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase
kb = ForeshadowingKnowledgeBase()
tasks = kb.get_chapter_tasks(83)
print('must_payoff:', tasks.must_payoff)
print('active_threads count:', len(tasks.active_threads))
"
```

Expected: 打印出 must_payoff 列表（第83回在元春伏笔的兑现范围内）

- [ ] **Step 3: Commit**

```bash
git add src/knowledge/foreshadowing_kb.py
git commit -m "feat: add ForeshadowingKnowledgeBase with canonical foreshadowing index"
```

---

### Task 11：StoryDirector + 连续3回入口

**Files:**
- Create: `src/story/director.py`
- Create: `run_continuation.py`（替换旧入口）

- [ ] **Step 1: 实现 StoryDirector**

`src/story/director.py`:

```python
"""StoryDirector：将用户一句话转换为本章的 SceneSpec。"""
from __future__ import annotations
from typing import Optional

from src.story.state import StoryState
from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase
from src.generation.context_assembler import SceneSpec

# 每回默认场景配置：可按需扩展
_DEFAULT_SCENES = {
    81: {
        "characters": ["贾宝玉", "林黛玉", "袭人", "紫鹃"],
        "scene_description": "秋日午后，宝玉前往潇湘馆探望黛玉，二人漫步竹径，感叹时世",
        "emotional_tone": "哀而不伤，含蓄蕴藉",
    },
    82: {
        "characters": ["贾宝玉", "林黛玉", "薛宝钗", "贾母"],
        "scene_description": "贾母召集众人赏秋，宝黛暗中相顾，宝钗若有所思",
        "emotional_tone": "表面热闹，暗流涌动",
    },
    83: {
        "characters": ["贾宝玉", "林黛玉", "王熙凤", "贾探春"],
        "scene_description": "贾府来了新消息，众人各自反应，暗示命运转折将至",
        "emotional_tone": "忧虑，不安",
    },
}


class StoryDirector:
    def __init__(self, state: StoryState, foreshadowing_kb: ForeshadowingKnowledgeBase):
        self.state = state
        self.foreshadowing_kb = foreshadowing_kb

    def make_spec(self, chapter_num: int, user_hint: Optional[str] = None) -> SceneSpec:
        defaults = _DEFAULT_SCENES.get(chapter_num, {
            "characters": ["贾宝玉", "林黛玉"],
            "scene_description": f"第{chapter_num}回故事继续发展，人物命运推进",
            "emotional_tone": "哀愁",
        })

        tasks = self.foreshadowing_kb.get_chapter_tasks(
            chapter_num,
            active_dynamic=self.state.active_foreshadowings,
        )

        return SceneSpec(
            chapter_num=chapter_num,
            characters=defaults["characters"],
            scene_description=defaults["scene_description"],
            emotional_tone=defaults["emotional_tone"],
            user_hint=user_hint,
            previous_summary=self.state.get_previous_summary(),
            foreshadowing_must_payoff=tasks.must_payoff,
            foreshadowing_should_plant=tasks.should_plant,
        )
```

- [ ] **Step 2: 实现连续多回入口**

`run_continuation.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 入口：连续续写多回，每回可指定用户引导。

用法：
  python3 run_continuation.py --chapters 3
  python3 run_continuation.py --chapters 3 --hints "让宝玉收到一封匿名信" "" "元春宫中传来噩耗"
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings
from src.knowledge.builder import build_style_kb
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase
from src.story.state import StoryState, ChapterSummary
from src.story.director import StoryDirector
from src.generation.context_assembler import ContextAssembler
from src.generation.content_writer import ContentWriter
from src.generation.literary_judge import LiteraryJudge


async def generate_one_chapter(
    chapter_num: int,
    user_hint,
    director: StoryDirector,
    assembler: ContextAssembler,
    writer: ContentWriter,
    judge: LiteraryJudge,
    out_dir: Path,
) -> ChapterSummary:
    print(f"\n{'=' * 50}")
    print(f"📖 生成第{chapter_num}回")
    if user_hint:
        print(f"   读者方向：{user_hint}")

    spec = director.make_spec(chapter_num, user_hint=user_hint or None)
    system_msg, user_prompt = assembler.assemble(spec)

    print("   调用 gpt-5.4...")
    raw_text = await writer.write(system_msg, user_prompt, chapter_num)

    if not raw_text:
        print(f"   ❌ 第{chapter_num}回生成失败")
        return ChapterSummary(chapter_num=chapter_num, summary="生成失败", key_events=[], new_foreshadowings=[])

    final_text, result = await judge.judge_and_rewrite(raw_text, spec, writer, assembler)
    print(f"   得分：{result.score:.2f}/10.0  {'✅' if result.passed else '⚠️'}")

    # 保存
    chapter_file = out_dir / f"chapter_{chapter_num:03d}.md"
    chapter_file.write_text(
        f"# 第{chapter_num}回\n\n{final_text}\n\n"
        f"---\n*得分：{result.score:.2f} · 风格：{result.style_score:.2f} · 人物：{result.voice_score:.2f}*\n",
        encoding="utf-8",
    )

    return ChapterSummary(
        chapter_num=chapter_num,
        summary=final_text[:200].replace("\n", ""),
        key_events=[],
        new_foreshadowings=spec.foreshadowing_should_plant,
    )


async def main(chapters: int, hints: list):
    settings = Settings()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(f"output/continuation_{ts}")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("📚 AI续写红楼梦 · Phase 2")
    print(f"   续写章数：{chapters}  输出：{out_dir}")

    style_kb = build_style_kb()
    char_kb = CharacterKnowledgeBase()
    foreshadowing_kb = ForeshadowingKnowledgeBase()
    state = StoryState.load("data/story_state.json")

    assembler = ContextAssembler(style_kb, char_kb)
    writer = ContentWriter(settings)
    judge = LiteraryJudge(style_kb, char_kb)
    director = StoryDirector(state, foreshadowing_kb)

    start = state.current_chapter + 1
    for i in range(chapters):
        chapter_num = start + i
        hint = hints[i] if i < len(hints) else None
        summary = await generate_one_chapter(
            chapter_num, hint, director, assembler, writer, judge, out_dir
        )
        state.advance(summary)

    print(f"\n🎉 完成！共生成 {chapters} 回，保存于 {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapters", type=int, default=3)
    parser.add_argument("--hints", nargs="*", default=[])
    args = parser.parse_args()
    asyncio.run(main(args.chapters, args.hints))
```

- [ ] **Step 3: 运行连续3回测试**

```bash
python3 run_continuation.py --chapters 3
```

Expected: 输出目录内有 chapter_081.md、chapter_082.md、chapter_083.md，每回得分均有打印

- [ ] **Step 4: Commit**

```bash
git add src/story/director.py run_continuation.py
git commit -m "feat: Phase 2 complete - StoryDirector + multi-chapter continuous generation"
```

---

## Phase 3：扩展到40回

### Task 12：批量生成81-120回

- [ ] **Step 1: 运行全40回批量生成**

```bash
python3 run_continuation.py --chapters 40
```

观察日志，确保每回都在生成。预计耗时约 40 × 2-3分钟 = 1.5-2小时。

- [ ] **Step 2: 检查前后文连贯性**

阅读 output 目录中 chapter_081.md～chapter_085.md，确认：
- 人物称谓前后一致（林黛玉/林妹妹/黛玉均指同一人）
- 第82回开头能自然接续第81回结尾
- 每回结尾有悬念

- [ ] **Step 3: Commit**

```bash
git add data/story_state.json
git commit -m "feat: Phase 3 - generated 40-chapter continuation, story_state persisted"
```

---

## 自检：Spec 覆盖确认

| Spec 要求 | 对应 Task |
|-----------|-----------|
| 三层知识库（风格/人物/伏笔）| Task 2-4、Task 10 |
| RAG 检索原著段落注入 prompt | Task 5（ContextAssembler）|
| 人物语言特征卡片约束 | Task 4（CharacterKB）|
| 向量相似度评分替代关键词打分 | Task 7（LiteraryJudge）|
| 自动重写机制（最多3次）| Task 7（judge_and_rewrite）|
| 用户一句话引导情节 | Task 8（run_ch81.py --hint），Task 11（StoryDirector）|
| 跨章节连贯性（前情提要）| Task 9（StoryState）|
| 伏笔有埋有收 | Task 10（ForeshadowingKB）|
| Phase 1 先做好第81回 | Task 8 |
| 批量40回 | Task 12 |
| MPS 加速 | Task 2（StyleKB model property）|
| API bug 修复 | 已修复（.env OPENAI_BASE_URL）|
