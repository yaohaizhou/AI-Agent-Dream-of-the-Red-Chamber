"""ProphecyAnalyst：章节生成后自动分析文本，更新 StoryState 的五层状态。"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List

from src.story.story_state import StoryState

# ── 基调关键词词表 ─────────────────────────────────────────────────────────

_TONE_PATTERNS = {
    "悲恸": ["泣", "哭", "痛哭", "悲恸", "号啕", "垂泪", "泪如雨"],
    "衰寂": ["凋零", "凄清", "寂寥", "残荷", "落叶", "秋风", "衰", "飘零", "萧瑟"],
    "忧虑": ["忧虑", "不安", "心惊", "愁", "忧", "惶", "惴"],
    "热闹": ["欢笑", "热闹", "笑语", "饮宴", "欢腾", "嬉笑", "喜"],
    "过渡": ["平静", "平常", "如常"],
}

_THEMATIC_SOURCES = ["秋", "冬", "哭", "笑", "泪", "雪", "残荷", "竹", "药", "风", "月", "花"]

_SUSPENSE_ENDINGS = re.compile(
    r"(且听下回分解|忽[有闻见]|急报|消息传来|不知后事如何|且慢|究竟如何|变故)"
)
_CLOSURE_ENDINGS = re.compile(r"(各自散去|方才罢了|一时无话|遂各安歇|此事方了|就此别过)")


@dataclass
class AnalysisResult:
    chapter_num: int
    chapter_summary: str
    detected_prophecy_ids: List[str]
    resolved_debt_ids: List[str]
    new_thematic_keywords: List[str]
    tone: str        # 热闹 | 衰寂 | 忧虑 | 悲恸 | 过渡
    ending_type: str  # 悬念 | 收束 | 过渡


class ProphecyAnalyst:
    """无状态的分析器，接收文本和当前 StoryState，输出 AnalysisResult。"""

    def analyze(
        self,
        text: str,
        state: StoryState,
        chapter_num: int,
        chapter_summary: str,
    ) -> AnalysisResult:
        return AnalysisResult(
            chapter_num=chapter_num,
            chapter_summary=chapter_summary,
            detected_prophecy_ids=self._detect_prophecy_hits(text, state),
            resolved_debt_ids=self._detect_resolved_debts(text, state),
            new_thematic_keywords=self._extract_thematic_keywords(text),
            tone=self._detect_tone(text),
            ending_type=self._detect_ending_type(text),
        )

    def _detect_prophecy_hits(self, text: str, state: StoryState) -> List[str]:
        return [
            anchor.id
            for anchor in state.active_prophecies
            if anchor.urgency != "resolved"
            and any(kw in text for kw in anchor.keywords)
        ]

    def _detect_resolved_debts(self, text: str, state: StoryState) -> List[str]:
        return [
            debt.id
            for debt in state.foreshadowing_debts
            if debt.status == "pending"
            and any(kw in text for kw in debt.keywords)
        ]

    def _extract_thematic_keywords(self, text: str) -> List[str]:
        return [kw for kw in _THEMATIC_SOURCES if kw in text]

    def _detect_tone(self, text: str) -> str:
        scores = {tone: 0 for tone in _TONE_PATTERNS}
        for tone, patterns in _TONE_PATTERNS.items():
            for pat in patterns:
                scores[tone] += text.count(pat)
        best = max(scores, key=lambda t: scores[t])
        return best if scores[best] > 0 else "过渡"

    def _detect_ending_type(self, text: str) -> str:
        # 取最后200字判断结尾类型
        tail = text[-200:]
        if _SUSPENSE_ENDINGS.search(tail):
            return "悬念"
        if _CLOSURE_ENDINGS.search(tail):
            return "收束"
        return "过渡"
