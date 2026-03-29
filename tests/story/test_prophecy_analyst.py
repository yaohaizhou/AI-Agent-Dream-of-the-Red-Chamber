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
