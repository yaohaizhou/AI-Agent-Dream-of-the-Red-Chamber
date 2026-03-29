import numpy as np

from src.generation.context_assembler import ContextAssembler, SceneSpec
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.knowledge.style_kb import StyleChunk, StyleKnowledgeBase


class DummyEmbeddings:
    def encode(self, texts, normalize_embeddings=True, batch_size=None, show_progress_bar=False):
        vectors = []
        for text in texts:
            seed = sum(ord(ch) for ch in text)
            vectors.append([
                float((seed % 97) + 1),
                float((len(text) % 89) + 1),
                float((text.count("道") + text.count("问") + text.count("答") + 1)),
            ])
        return np.array(vectors, dtype=float)


def make_kb(tmp_path, monkeypatch):
    monkeypatch.setattr(StyleKnowledgeBase, "model", property(lambda self: DummyEmbeddings()))
    kb = StyleKnowledgeBase(persist_dir=str(tmp_path / "style"))
    kb.add_chunks([
        StyleChunk(
            text="只见那日天色阴沉，园中落叶纷纷，满地碎金，别有一番萧瑟意境。",
            chapter_num=27,
            paragraph_type="narrative",
            characters_present=[],
            emotional_tone="哀愁",
        ),
        StyleChunk(
            text="宝玉道：'林妹妹，你别恼，我只是随口一说。'黛玉转过身去，并不理他。",
            chapter_num=30,
            paragraph_type="dialogue",
            characters_present=["贾宝玉", "林黛玉"],
            emotional_tone="哀愁",
        ),
        StyleChunk(
            text="只见秋风渐紧，竹影筛窗，阶前黄叶打旋，满院寂然，越发添了几分清冷。",
            chapter_num=27,
            paragraph_type="scenery",
            characters_present=[],
            emotional_tone="哀愁",
        ),
    ])
    return kb


def test_assemble_returns_two_strings(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
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


def test_system_contains_original_text_example(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉"],
        scene_description="宝黛对话",
        emotional_tone="哀愁",
    )
    system_msg, _ = assembler.assemble(spec)
    assert "黛玉" in system_msg or "宝玉" in system_msg


def test_user_prompt_contains_forbidden_words_reminder(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
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


def test_user_hint_appears_in_prompt(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
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


def test_user_prompt_contains_chapter_theme_block(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉"],
        scene_description="秋日宝黛在园中对话，感时伤怀",
        emotional_tone="哀愁",
    )
    _, user_prompt = assembler.assemble(spec)

    assert "【本章主题】" in user_prompt
    assert "家运将衰" in user_prompt
    assert "宝黛情深而前景未明" in user_prompt


def test_user_prompt_contains_chapter_organization_block(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉", "王熙凤"],
        scene_description="家宴之后宝黛再会，外头忽有急信",
        emotional_tone="哀愁",
    )
    _, user_prompt = assembler.assemble(spec)

    assert "【本章章法】" in user_prompt
    assert "先写秋意与家势" in user_prompt
    assert "再入人物情事" in user_prompt
    assert "末段须以外部消息或动静收束" in user_prompt


def test_user_prompt_limits_dialogue_density(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉", "薛宝钗"],
        scene_description="众人小宴后各怀心事",
        emotional_tone="哀愁",
    )
    _, user_prompt = assembler.assemble(spec)

    assert "叙述须多于对话" in user_prompt
    assert "不得连缀成长段轮番答话" in user_prompt
    assert "每段对话都须承担" in user_prompt
