from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.knowledge.character_kb import CharacterKnowledgeBase
from src.knowledge.style_kb import StyleKnowledgeBase

FORBIDDEN_WORDS = "高兴、开心、没事、感觉、其实、然后、所以、但是（改用‘却’）、好的、搞定、不错"
DEFAULT_CHAPTER_THEMES = [
    "家运将衰",
    "宝黛情深而前景未明",
]
DEFAULT_CHAPTER_ORGANIZATION = [
    "先写秋意与家势",
    "再入人物情事",
    "末段须以外部消息或动静收束",
]
DIALOGUE_DENSITY_GUIDANCE = [
    "叙述须多于对话",
    "不得连缀成长段轮番答话",
    "每段对话都须承担人物推进、情绪转折或情节递进之用",
]


@dataclass
class SceneSpec:
    chapter_num: int
    characters: List[str]
    scene_description: str
    emotional_tone: str
    user_hint: Optional[str] = None
    previous_summary: str = ""
    foreshadowing_must_payoff: List[str] = field(default_factory=list)
    foreshadowing_should_plant: List[str] = field(default_factory=list)


class ContextAssembler:
    """将知识库结果组装为生成提示词。"""

    def __init__(self, style_kb: StyleKnowledgeBase, character_kb: CharacterKnowledgeBase):
        self.style_kb = style_kb
        self.character_kb = character_kb

    def assemble(self, spec: SceneSpec) -> Tuple[str, str]:
        query = self._build_query(spec)
        narrative_examples = self.style_kb.search(query, paragraph_type="narrative", top_k=2)
        if not narrative_examples and spec.emotional_tone:
            narrative_examples = self.style_kb.search(spec.emotional_tone, paragraph_type="narrative", top_k=2)

        dialogue_examples = self.style_kb.search(query, paragraph_type="dialogue", characters=spec.characters, top_k=2)
        if not dialogue_examples:
            dialogue_examples = self.style_kb.search(query, paragraph_type="dialogue", top_k=2)

        scenery_examples = self.style_kb.search(query, paragraph_type="scenery", top_k=1)

        system_msg = self._build_system(narrative_examples, dialogue_examples, scenery_examples)
        user_prompt = self._build_user(spec)
        return system_msg, user_prompt

    def _build_query(self, spec: SceneSpec) -> str:
        parts = [spec.scene_description, spec.emotional_tone]
        if spec.characters:
            parts.append(" ".join(spec.characters))
        return " ".join(part for part in parts if part).strip()

    def _build_system(
        self,
        narrative_examples: List[str],
        dialogue_examples: List[str],
        scenery_examples: List[str],
    ) -> str:
        parts = [
            "你是续写《红楼梦》的笔者，笔力须与曹雪芹原著一脉相承。",
            f"绝对禁止出现以下现代词汇：{FORBIDDEN_WORDS}。",
            "叙事须用第三人称全知视角，语感古朴克制，情感含而不露。",
            "只可顺着原著语势铺写，不可写成现代网文口吻。",
            "",
        ]
        if narrative_examples:
            parts.append("【原著叙事风格范例】")
            for i, ex in enumerate(narrative_examples, 1):
                parts.append(f"范例{i}：\n{ex[:500]}")
            parts.append("")

        if dialogue_examples:
            parts.append("【原著对话风格范例】")
            for i, ex in enumerate(dialogue_examples, 1):
                parts.append(f"范例{i}：\n{ex[:500]}")
            parts.append("")

        if scenery_examples:
            parts.append("【原著景物风格范例】")
            for i, ex in enumerate(scenery_examples, 1):
                parts.append(f"范例{i}：\n{ex[:500]}")

        return "\n".join(parts)

    def _build_user(self, spec: SceneSpec) -> str:
        parts: List[str] = []

        if spec.previous_summary:
            parts += ["【前情提要】", spec.previous_summary, ""]

        character_lines = self._build_character_constraints(spec.characters)
        if character_lines:
            parts += ["【本章人物状态】"] + character_lines + [""]

        parts += ["【本章主题】", *self._build_theme_lines(spec), ""]
        parts += ["【本章章法】", *self._build_structure_lines(spec), ""]
        parts += ["【叙述约束】", *self._build_narration_constraints(), ""]

        if spec.foreshadowing_must_payoff:
            parts.append("【本章伏笔指令】")
            parts.append("必须兑现：")
            for item in spec.foreshadowing_must_payoff:
                parts.append(f"- {item}")
            parts.append("")

        if spec.foreshadowing_should_plant:
            if "【本章伏笔指令】" not in parts:
                parts.append("【本章伏笔指令】")
            parts.append("建议埋设：")
            for item in spec.foreshadowing_should_plant:
                parts.append(f"- {item}")
            parts.append("")

        if spec.user_hint:
            parts += ["【读者方向（本章须体现）】", spec.user_hint, ""]

        parts += [
            "【续写任务】",
            f"请续写《红楼梦》第{spec.chapter_num}回，约2500字。",
            f"场景：{spec.scene_description}",
            f"情感基调：{spec.emotional_tone}",
            f"禁用现代词汇：{FORBIDDEN_WORDS}",
            "要求：",
            "1. 开头须自然承接前情。",
            "2. 对话须贴合人物身份与性情。",
            "3. 结尾须留下可引下回的余意或悬念。",
            "4. 严格模仿 system 中提供的原著范例语感。",
            "5. 不得出现现代口语、解释腔和网文化抒情。",
        ]
        return "\n".join(parts)

    def _build_theme_lines(self, spec: SceneSpec) -> List[str]:
        lines = [
            "- 家运将衰：须写出贾府表面如常、内里吃紧的气象。",
            "- 宝黛情深而前景未明：须写出二人相知愈深，却更觉世事难凭。",
        ]
        if spec.foreshadowing_should_plant:
            lines.extend(f"- 伏脉关联：{item}" for item in spec.foreshadowing_should_plant)
        return lines

    def _build_structure_lines(self, spec: SceneSpec) -> List[str]:
        del spec
        return [
            "- 先写秋意与家势，以景与人心相映，点出衰飒之感。",
            "- 再入人物情事，以叙述、动作、神色、停顿承托情绪，不可径以长对答铺写。",
            "- 若写多人同席或同场，不得连缀成长段轮番答话，须使场面服务于家势与情势。",
            "- 末段须以外部消息或动静收束，使下回有可接之变。",
        ]

    def _build_narration_constraints(self) -> List[str]:
        return [
            "- 叙述须多于对话，景物、动作、神情、心事要成为主要承载。",
            "- 对话不可接连数段铺陈，尤不可只图热闹。",
            "- 每段对话都须承担推进情意、显出家势、或引出后变三者之一。",
            "- 章中须反复回扣秋意、衰象、隐忧，不可写散。",
        ]

    def _build_character_constraints(self, characters: List[str]) -> List[str]:
        lines: List[str] = []
        for name in characters:
            profile = self.character_kb.get(name)
            if not profile:
                continue
            personality = str(profile.get("性格", "")).strip()
            current_state = str(profile.get("现状", "")).strip()
            direction = str(profile.get("发展方向", "")).strip()
            description = str(profile.get("description", "")).strip()
            summary = "；".join(part for part in [description, personality, current_state, direction] if part)
            if summary:
                lines.append(f"- {self.character_kb.resolve_name(name) or name}：{summary}")
        return lines
