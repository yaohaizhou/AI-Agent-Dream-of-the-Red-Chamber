"""
一次性建库脚本。
运行: python3 -m src.knowledge.builder
构建完成后，data/knowledge_base/style/ 即可用于 RAG 检索。
"""
from __future__ import annotations
import gc
import re
import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple

from src.knowledge.style_kb import StyleKnowledgeBase, StyleChunk
from src.knowledge.character_kb import build_character_kb

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
DIALOGUE_PATTERN = re.compile(r"(?:[\u4e00-\u9fff]{1,4}[笑冷忙低嗔含微轻忽突]?道|问|答)[：:]?[“\"「『]")
INNER_THOUGHT = re.compile(r"(心中|心下|心里|想道|暗想|自思|不觉|不禁|只见|但见)")
SCENERY_KEYWORDS = ["日", "月", "风", "雨", "雪", "花", "树", "山", "水", "云", "天", "园", "院", "景"]
POETRY_MARKERS = re.compile(r"(判词|词曰|诗云|赋曰|歌云|曲子|题曰|其词|其判)")
BUILD_BATCH_SIZE = 8
BUILD_DEVICE = "cpu"
BUILD_ENCODE_BATCH_SIZE = 2


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

    persist_path = Path(persist_dir)
    build_path = Path(
        tempfile.mkdtemp(
            prefix=f"{persist_path.name}.building.",
            dir=str(persist_path.parent),
        )
    )

    kb = StyleKnowledgeBase(
        persist_dir=str(build_path),
        device=BUILD_DEVICE,
        encode_batch_size=BUILD_ENCODE_BATCH_SIZE,
    )
    total_chunks = sum(len(texts) for _, texts in chapters)
    print(f"   共 {total_chunks} 个段落块，按批次写入 ChromaDB...")

    processed = 0
    batch: List[StyleChunk] = []
    for chapter_num, texts in chapters:
        for text in texts:
            batch.append(
                StyleChunk(
                    text=text,
                    chapter_num=chapter_num,
                    paragraph_type=_classify(text),
                    characters_present=_extract_characters(text),
                )
            )
            if len(batch) >= BUILD_BATCH_SIZE:
                kb.add_chunks(batch)
                processed += len(batch)
                print(f"   进度: {processed}/{total_chunks}", end="\r")
                batch.clear()
                gc.collect()

    if batch:
        kb.add_chunks(batch)
        processed += len(batch)
        print(f"   进度: {processed}/{total_chunks}", end="\r")
        batch.clear()
        gc.collect()

    built_count = kb.count()
    kb.close()

    if persist_path.exists():
        shutil.rmtree(persist_path)
    build_path.replace(persist_path)

    print(f"\n✅ 风格层知识库构建完成，共 {built_count} 条。")
    build_character_kb(
        source=source,
        persist_path=str(persist_path.parent / "characters" / "canonical.json"),
    )
    return StyleKnowledgeBase(persist_dir=str(persist_path), device=BUILD_DEVICE)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    Path("data/knowledge_base/style").mkdir(parents=True, exist_ok=True)
    Path("data/knowledge_base/characters").mkdir(parents=True, exist_ok=True)
    Path("data/knowledge_base/foreshadowing").mkdir(parents=True, exist_ok=True)
    build_style_kb()
