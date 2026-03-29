"""StoryDirector：将用户一句话转换为本章的 SceneSpec。"""
from __future__ import annotations

from typing import Optional

from src.generation.context_assembler import SceneSpec
from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase
from src.story.story_state import StoryState

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
        defaults = _DEFAULT_SCENES.get(
            chapter_num,
            {
                "characters": ["贾宝玉", "林黛玉"],
                "scene_description": f"第{chapter_num}回故事继续发展，人物命运推进",
                "emotional_tone": "哀愁",
            },
        )

        scene_hints = self.state.to_scene_hints(defaults["characters"])
        tasks = self.foreshadowing_kb.get_chapter_tasks(
            chapter_num,
            active_dynamic=scene_hints.foreshadowing_should_plant,
        )

        emotional_tone = defaults["emotional_tone"]
        if scene_hints.suggested_emotional_tone and scene_hints.suggested_emotional_tone != "哀而不伤":
            emotional_tone = scene_hints.suggested_emotional_tone
        if scene_hints.suggested_next_tone and scene_hints.suggested_next_tone not in emotional_tone:
            emotional_tone = f"{emotional_tone}，{scene_hints.suggested_next_tone}"

        foreshadowing_must_payoff = list(dict.fromkeys(
            list(scene_hints.foreshadowing_must_payoff) + list(tasks.must_payoff)
        ))
        foreshadowing_should_plant = list(dict.fromkeys(
            list(tasks.active_threads) + list(tasks.should_plant)
        ))

        return SceneSpec(
            chapter_num=chapter_num,
            characters=list(defaults["characters"]),
            scene_description=defaults["scene_description"],
            emotional_tone=emotional_tone,
            user_hint=user_hint,
            previous_summary=scene_hints.previous_summary,
            foreshadowing_must_payoff=foreshadowing_must_payoff,
            foreshadowing_should_plant=foreshadowing_should_plant,
        )
