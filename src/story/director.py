"""StoryDirector：将用户一句话转换为本章的 SceneSpec。"""
from __future__ import annotations

from typing import Optional

from src.generation.context_assembler import SceneSpec
from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase
from src.story.story_state import StoryState

_CONFLICT_MARKERS = {
    "元春": ["病势沉重", "不祥消息", "宫中已有不祥消息"],
}

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

        characters = list(defaults["characters"])
        scene_hints = self.state.to_scene_hints(characters)
        analyzed_hint = _analyze_user_hint(user_hint, self.state.chapter_summary, chapter_num)
        if analyzed_hint is not None:
            self.state.record_user_guidance(
                chapter_num=chapter_num,
                original_hint=user_hint or "",
                normalized_hint=analyzed_hint["normalized_hint"],
                guidance_type=analyzed_hint["guidance_type"],
                strength=analyzed_hint["strength"],
                conflict_status=analyzed_hint["conflict_status"],
            )
            scene_hints = self.state.to_scene_hints(characters)
        tasks = self.foreshadowing_kb.get_chapter_tasks(
            chapter_num,
            active_dynamic=scene_hints.foreshadowing_should_plant,
        )

        emotional_tone = scene_hints.suggested_emotional_tone or defaults["emotional_tone"]
        if analyzed_hint and analyzed_hint["guidance_type"] == "emotion":
            emotional_tone = _merge_tone(emotional_tone, analyzed_hint["normalized_hint"])
        if scene_hints.suggested_next_tone and scene_hints.suggested_next_tone not in emotional_tone:
            emotional_tone = f"{emotional_tone}，{scene_hints.suggested_next_tone}"

        foreshadowing_must_payoff = _merge_unique(
            scene_hints.foreshadowing_must_payoff,
            tasks.must_payoff,
        )
        foreshadowing_should_plant = _merge_unique(
            tasks.active_threads,
            tasks.should_plant,
        )

        return SceneSpec(
            chapter_num=chapter_num,
            characters=characters,
            scene_description=defaults["scene_description"],
            emotional_tone=emotional_tone,
            user_hint=analyzed_hint["display_hint"] if analyzed_hint else user_hint,
            previous_summary=scene_hints.previous_summary,
            foreshadowing_must_payoff=foreshadowing_must_payoff,
            foreshadowing_should_plant=foreshadowing_should_plant,
        )


def _analyze_user_hint(user_hint: Optional[str], chapter_summary: str, chapter_num: int) -> Optional[dict[str, str]]:
    if not user_hint:
        return None

    normalized = user_hint.strip()
    guidance_type = _classify_guidance_type(normalized)
    strength = _classify_strength(normalized, guidance_type, chapter_num)
    conflict_status = "compatible"
    display_hint = _normalize_hint(normalized)
    guidance_text = display_hint

    if _conflicts_with_summary(normalized, chapter_summary):
        conflict_status = "softened"
        display_hint = "谨守现有情势，元春喜讯不可骤然落实"
        guidance_text = "元春喜讯暂不可骤然落实"
        strength = "light"

    return {
        "normalized_hint": guidance_text,
        "guidance_type": guidance_type,
        "strength": strength,
        "conflict_status": conflict_status,
        "display_hint": display_hint,
    }


def _classify_guidance_type(user_hint: str) -> str:
    if any(word in user_hint for word in ["气氛", "更凄", "更冷", "凄冷", "凄清", "悲凉", "清冷"]):
        return "emotion"
    if any(word in user_hint for word in ["最终", "渐渐", "渐起", "日后", "往后"]):
        return "direction"
    return "event"


def _classify_strength(user_hint: str, guidance_type: str, chapter_num: int) -> str:
    if guidance_type == "emotion":
        return "light"
    if guidance_type == "direction":
        return "medium"
    if f"第{chapter_num}回" in user_hint or "这一回" in user_hint or "本回" in user_hint:
        return "strong"
    return "medium"


def _normalize_hint(user_hint: str) -> str:
    hint = user_hint.strip()
    replacements = [
        "让",
        "在第81回",
        "在第82回",
        "在第83回",
        "这一回",
        "本回",
        "第81回",
        "第82回",
        "第83回",
        "些",
    ]
    for text in replacements:
        hint = hint.replace(text, "")
    hint = hint.replace("收到一封", "收到")
    hint = hint.replace("收到一则", "收到")
    hint = hint.replace("收到一张", "收到")
    hint = hint.replace("匿名信件", "匿名信")
    return hint.strip(" ，。")


def _conflicts_with_summary(user_hint: str, chapter_summary: str) -> bool:
    for character, markers in _CONFLICT_MARKERS.items():
        if character in user_hint and "大喜回府省亲" in user_hint:
            if any(marker in chapter_summary for marker in markers):
                return True
    return False


def _merge_tone(base_tone: str, hint_tone: str) -> str:
    if hint_tone in base_tone:
        return base_tone
    return f"{base_tone}，{hint_tone}"


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            if item and item not in merged:
                merged.append(item)
    return merged
