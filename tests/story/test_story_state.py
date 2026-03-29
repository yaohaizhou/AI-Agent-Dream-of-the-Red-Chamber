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


def test_to_scene_hints_includes_active_user_guidance():
    state = StoryState()
    state.record_user_guidance(
        chapter_num=81,
        original_hint="让宝玉收到一封匿名信",
        normalized_hint="宝玉收到匿名信",
        guidance_type="event",
        strength="strong",
        conflict_status="compatible",
    )

    hints = state.to_scene_hints(characters=["贾宝玉"])

    assert "宝玉收到匿名信" in hints.foreshadowing_must_payoff


def test_to_scene_hints_uses_medium_guidance_as_should_plant():
    state = StoryState()
    state.record_user_guidance(
        chapter_num=81,
        original_hint="让宝玉渐渐起出家之念",
        normalized_hint="宝玉渐起出家之念",
        guidance_type="direction",
        strength="medium",
        conflict_status="compatible",
    )

    hints = state.to_scene_hints(characters=["贾宝玉"])

    assert "宝玉渐起出家之念" in hints.foreshadowing_should_plant


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


def test_story_state_save_and_load_preserve_user_guidance(tmp_path):
    state = StoryState(_state_dir=str(tmp_path))
    state.record_user_guidance(
        chapter_num=81,
        original_hint="让黛玉更加疑心",
        normalized_hint="黛玉疑心更深",
        guidance_type="emotion",
        strength="light",
        conflict_status="compatible",
    )

    saved = state.save(81)
    loaded = StoryState.load(str(saved))

    assert loaded.active_user_guidance[0].normalized_hint == "黛玉疑心更深"
    assert loaded.active_user_guidance[0].strength == "light"


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
