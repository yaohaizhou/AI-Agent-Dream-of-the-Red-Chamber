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
且说秋气一日紧似一日，贾府中虽仍循旧例，里头却渐觉不似从前热闹。宝玉自外头回来，见潇湘馆前竹影沉沉，心下先有几分怅惘。
黛玉倚窗而坐，颜色清减，见他来了，只淡淡问了一句来意。宝玉见她眉间隐忧，也不敢多说，只陪着立了半晌。
二人虽无多话，那一点相知之意却都含在神色之间。正说着，远处忽有人来传话，园中静气顿时一变。
"""

BAD_TEXT = "宝玉很高兴地跑去找黛玉，开心地说：你好啊，我们今天去玩吧，感觉天气不错。"

DIALOGUE_HEAVY_TEXT = """
宝玉道：\"林妹妹，你今日可好？\"
黛玉道：\"也不过如此。\"
宝玉道：\"我心里惦着你。\"
黛玉道：\"你又来哄我。\"
宝玉道：\"我几时哄你了？\"
黛玉道：\"谁知道呢。\"
"""

THEME_FOCUSED_TEXT = """
如今贾府表面仍照旧例行事，内里却渐见支绌之象。秋气一天紧似一天，园中草木也带出衰声。
宝玉自外头回来，见潇湘馆竹影沉沉，心下先有三分怅惘。黛玉虽只淡淡说了两句，眉间眼底却都是欲说还休之意。
二人并不多话，只因彼此都知眼前光景一年不似一年，便连这一点相见之情，也像隔着风露与世事。
说话间，外头忽有人来传急信，满园静气顿时一变，越发显出繁华将尽而事变将来的意思。
"""


def make_spec():
    return SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉"],
        scene_description="宝黛秋日相遇",
        emotional_tone="哀愁",
        foreshadowing_should_plant=["家运将衰", "宝黛情深而终难两全"],
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


def test_dialogue_heavy_text_gets_lower_dialogue_balance_score(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(DIALOGUE_HEAVY_TEXT, make_spec())
    assert result.dialogue_balance_score < 7.0


def test_theme_focused_text_gets_higher_theme_focus_score(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(THEME_FOCUSED_TEXT, make_spec())
    assert result.theme_focus_score >= 8.0


def test_dialogue_heavy_text_feedback_mentions_dialogue_density(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(DIALOGUE_HEAVY_TEXT, make_spec())
    assert "对话" in result.feedback


def test_judgement_result_exposes_new_subscores(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(THEME_FOCUSED_TEXT, make_spec())
    assert isinstance(result.dialogue_balance_score, float)
    assert isinstance(result.theme_focus_score, float)


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
