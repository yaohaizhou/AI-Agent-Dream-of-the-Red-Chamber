import numpy as np

from src.generation.context_assembler import SceneSpec
from src.generation.literary_judge import LiteraryJudge
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


def make_judge(tmp_path, monkeypatch):
    monkeypatch.setattr(StyleKnowledgeBase, "model", property(lambda self: DummyEmbeddings()))
    style_kb = StyleKnowledgeBase(persist_dir=str(tmp_path / "style"))
    style_kb.add_chunks([
        StyleChunk(
            text="宝玉叹道：'这花开了又谢，谢了又开，到底是为谁？'黛玉不语，只望着那池中残荷出神。",
            chapter_num=40,
            paragraph_type="dialogue",
            characters_present=["贾宝玉", "林黛玉"],
            emotional_tone="哀愁",
        ),
        StyleChunk(
            text="且说秋光渐老，竹影筛窗，宝玉缓步行来，只见黛玉临风独坐，神思恍惚。",
            chapter_num=41,
            paragraph_type="narrative",
            characters_present=["贾宝玉", "林黛玉"],
            emotional_tone="哀愁",
        ),
    ])
    char_kb = CharacterKnowledgeBase()
    char_kb._profiles = {
        "贾宝玉": {
            "aliases": ["宝玉"],
            "性格": "纯真敏感",
            "现状": "在贾府中",
            "发展方向": "由情入悟",
            "description": "贾府公子",
        },
        "林黛玉": {
            "aliases": ["黛玉"],
            "性格": "聪慧敏感",
            "现状": "寄居贾府",
            "发展方向": "命运愈发凄婉",
            "description": "林家小姐",
        },
    }
    char_kb._rebuild_alias_index()
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


def test_good_text_scores_higher_than_bad(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    good_result = judge.judge(GOOD_TEXT, make_spec())
    bad_result = judge.judge(BAD_TEXT, make_spec())
    assert good_result.score > bad_result.score


def test_bad_text_fails(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(BAD_TEXT, make_spec())
    assert not result.passed


def test_good_text_passes(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(GOOD_TEXT, make_spec())
    assert result.passed


def test_feedback_mentions_forbidden_word(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(BAD_TEXT, make_spec())
    assert "高兴" in result.feedback or "开心" in result.feedback


def test_foreshadowing_score_full_when_no_requirement(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉"],
        scene_description="宝玉读书",
        emotional_tone="闲散",
        foreshadowing_must_payoff=[],
    )
    result = judge.judge(GOOD_TEXT, spec)
    assert result.foreshadowing_score == 9.0
