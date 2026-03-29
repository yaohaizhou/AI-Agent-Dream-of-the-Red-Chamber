from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase, ForeshadowingTask
from src.story.director import StoryDirector
from src.story.story_state import StoryState


class StubForeshadowingKB(ForeshadowingKnowledgeBase):
    def __init__(self):
        self.canonical = []

    def get_chapter_tasks(self, chapter_num, active_dynamic=None):
        return ForeshadowingTask(
            must_payoff=[],
            should_plant=[],
            active_threads=list(active_dynamic or []),
        )


def test_make_spec_records_strong_event_hint_into_state():
    state = StoryState()
    director = StoryDirector(state, StubForeshadowingKB())

    spec = director.make_spec(81, user_hint="让宝玉在第81回收到一封匿名信")

    assert spec.user_hint == "宝玉收到匿名信"
    assert state.active_user_guidance[-1].strength == "strong"
    assert state.active_user_guidance[-1].guidance_type == "event"


def test_make_spec_records_medium_direction_hint_for_future_chapters():
    state = StoryState()
    director = StoryDirector(state, StubForeshadowingKB())

    director.make_spec(81, user_hint="让宝玉最终出家")
    next_spec = director.make_spec(82)

    assert any("宝玉最终出家" in item for item in next_spec.foreshadowing_should_plant)


def test_make_spec_softens_conflicting_hint_instead_of_dropping_it():
    state = StoryState()
    state.chapter_summary = "第80回：元春病势沉重，宫中已有不祥消息。"
    director = StoryDirector(state, StubForeshadowingKB())

    spec = director.make_spec(81, user_hint="让元春大喜回府省亲")

    assert spec.user_hint == "谨守现有情势，元春喜讯不可骤然落实"
    assert state.active_user_guidance[-1].conflict_status == "softened"


def test_make_spec_turns_emotion_hint_into_tone_guidance():
    state = StoryState()
    director = StoryDirector(state, StubForeshadowingKB())

    spec = director.make_spec(81, user_hint="这一回气氛更凄冷些")

    assert "凄冷" in spec.emotional_tone
    assert state.active_user_guidance[-1].guidance_type == "emotion"
