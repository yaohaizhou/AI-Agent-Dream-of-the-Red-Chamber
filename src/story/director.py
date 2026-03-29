"""StoryDirector：将用户一句话转换为本章的 SceneSpec。"""
from __future__ import annotations

from typing import Optional

from src.generation.context_assembler import SceneSpec
from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase
from src.story.story_state import StoryState

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
        characters = list(defaults["characters"])
        scene_hints = self.state.to_scene_hints(characters)
        tasks = self.foreshadowing_kb.get_chapter_tasks(chapter_num)

        emotional_tone = scene_hints.suggested_emotional_tone or defaults["emotional_tone"]

        should_plant = _merge_unique(
            scene_hints.foreshadowing_should_plant,
            tasks.should_plant,
            tasks.active_threads,
        )
        must_payoff = _merge_unique(
            scene_hints.foreshadowing_must_payoff,
            tasks.must_payoff,
        )

        return SceneSpec(
            chapter_num=chapter_num,
            characters=characters,
            scene_description=defaults["scene_description"],
            emotional_tone=emotional_tone,
            user_hint=user_hint,
            previous_summary=scene_hints.previous_summary,
            foreshadowing_must_payoff=must_payoff,
            foreshadowing_should_plant=should_plant,
        )


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            if item and item not in merged:
                merged.append(item)
    return merged
