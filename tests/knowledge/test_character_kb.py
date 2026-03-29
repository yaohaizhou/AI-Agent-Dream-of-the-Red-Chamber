from pathlib import Path

from src.knowledge.character_kb import CharacterKnowledgeBase, build_character_kb


def test_build_character_kb_extracts_canonical_profiles(tmp_path):
    source = tmp_path / "hongloumeng_sample.md"
    source.write_text(
        "### 第一回\n\n"
        "贾宝玉听见黛玉说话，心中一动。宝玉又见宝钗进来，忙起身相迎。\n\n"
        "凤姐笑道：\"你们只顾说话，倒把我撇在一边了。\"\n",
        encoding="utf-8",
    )
    persist_path = tmp_path / "characters" / "canonical.json"

    kb = build_character_kb(source=str(source), persist_path=str(persist_path))

    assert persist_path.exists()
    assert kb.count() == 4
    assert kb.get("贾宝玉")["性格"]
    assert kb.get("宝玉")["description"] == kb.get("贾宝玉")["description"]
    assert kb.get("凤姐")["mention_count"] >= 1



def test_character_kb_load_roundtrip(tmp_path):
    persist_path = tmp_path / "characters.json"
    persist_path.write_text(
        '{\n'
        '  "贾宝玉": {\n'
        '    "aliases": ["宝玉"],\n'
        '    "性格": "纯真",\n'
        '    "现状": "在贾府",\n'
        '    "发展方向": "觉醒",\n'
        '    "description": "主角",\n'
        '    "mention_count": 12\n'
        '  }\n'
        '}\n',
        encoding="utf-8",
    )

    kb = CharacterKnowledgeBase(persist_path=str(persist_path))
    assert kb.count() == 1
    assert kb.get("宝玉")["description"] == "主角"
