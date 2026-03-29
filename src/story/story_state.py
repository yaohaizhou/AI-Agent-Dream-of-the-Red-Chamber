"""StoryState：五层故事状态机，跨章节共享语境。"""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, TYPE_CHECKING

from src.story.state_schema import (
    ProphecyAnchor,
    CharacterStateEntry,
    ToneRecord,
    NarrativePacing,
    ForeshadowingDebt,
)

if TYPE_CHECKING:
    from src.story.prophecy_analyst import AnalysisResult

HINT_THRESHOLD = 8        # 超过此章数强制兑现
HIGH_URGENCY_THRESHOLD = 0.7  # 权重高于此值强制兑现


@dataclass
class SceneHints:
    """StoryState 给 StoryDirector 的语境摘要，直接映射到 SceneSpec 字段。"""
    previous_summary: str
    foreshadowing_must_payoff: List[str]
    foreshadowing_should_plant: List[str]
    suggested_emotional_tone: str
    suggested_next_tone: str


@dataclass
class StoryState:
    # ── 基础 ──
    current_chapter: int = 80

    # ── L1：判词意象层 ──
    active_prophecies: List[ProphecyAnchor] = field(default_factory=list)
    current_thematic_keywords: List[str] = field(default_factory=list)

    # ── L2：剧情旗帜层 ──
    milestones: Dict[str, bool] = field(default_factory=lambda: {
        "宝玉丢玉": False,
        "大观园抄检": False,
        "黛玉焚稿": False,
        "金玉良缘订立": False,
        "贾府获罪抄家": False,
        "宝玉出家": False,
    })
    chapter_summary: str = ""

    # ── L3：人物概况层 ──
    character_states: Dict[str, CharacterStateEntry] = field(default_factory=dict)

    # ── L4：叙事节奏层 ──
    narrative_pacing: NarrativePacing = field(default_factory=NarrativePacing)

    # ── L5：伏笔债务层 ──
    foreshadowing_debts: List[ForeshadowingDebt] = field(default_factory=list)

    # ── 内部 ──
    _state_dir: str = field(default="outputs/state", repr=False)

    # ─────────────────────────────────────────────
    # Pre-chapter：给 StoryDirector 提供语境
    # ─────────────────────────────────────────────

    def to_scene_hints(self, characters: List[str]) -> SceneHints:
        """将当前状态转换为下一章 SceneSpec 所需的附加参数。"""
        must_payoff = [
            d.description
            for d in self.foreshadowing_debts
            if d.status == "pending" and (
                d.urgency_weight >= HIGH_URGENCY_THRESHOLD
                or d.chapters_since_hint >= HINT_THRESHOLD
            )
        ]
        should_plant = list(self.current_thematic_keywords) + [
            d.description
            for d in self.foreshadowing_debts
            if d.status == "pending"
            and d.urgency_weight < HIGH_URGENCY_THRESHOLD
            and d.chapters_since_hint < HINT_THRESHOLD
        ]

        emotional_tone = self._dominant_emotional_tone(characters)

        return SceneHints(
            previous_summary=self.chapter_summary,
            foreshadowing_must_payoff=must_payoff,
            foreshadowing_should_plant=should_plant,
            suggested_emotional_tone=emotional_tone,
            suggested_next_tone=self.narrative_pacing.suggested_next_tone,
        )

    def _dominant_emotional_tone(self, characters: List[str]) -> str:
        centers = [
            self.character_states[c].emotional_center
            for c in characters
            if c in self.character_states
        ]
        if not centers:
            return "哀而不伤"
        return "、".join(dict.fromkeys(centers))  # 去重保序

    # ─────────────────────────────────────────────
    # Post-chapter：接收 ProphecyAnalyst 结果并更新
    # ─────────────────────────────────────────────

    def update_from_analysis(self, result: "AnalysisResult") -> None:
        """用 ProphecyAnalyst 的分析结果更新全部五层状态。"""
        self.current_chapter = result.chapter_num
        self.chapter_summary = f"第{result.chapter_num}回：{result.chapter_summary}"
        self.current_thematic_keywords = result.new_thematic_keywords

        # L1：升级命中的判词意象
        for anchor in self.active_prophecies:
            if anchor.id in result.detected_prophecy_ids:
                _upgrade_urgency(anchor)

        # L5：标记已兑现的债务，递增其余
        for debt in self.foreshadowing_debts:
            if debt.id in result.resolved_debt_ids:
                debt.status = "resolved"
            elif debt.status == "pending":
                debt.chapters_since_hint += 1

        # L4：更新节奏记录（保留最近3章）
        pacing = self.narrative_pacing
        pacing.recent_tone_streak.append(
            ToneRecord(chapter=result.chapter_num, tone=result.tone)
        )
        if len(pacing.recent_tone_streak) > 3:
            pacing.recent_tone_streak = pacing.recent_tone_streak[-3:]
        pacing.last_chapter_ending = result.ending_type
        pacing.suggested_next_tone = _compute_next_tone(pacing)

    # ─────────────────────────────────────────────
    # 持久化
    # ─────────────────────────────────────────────

    def save(self, chapter_num: int) -> Path:
        """保存快照到 {_state_dir}/state_ch{chapter_num:03d}.json。"""
        out_dir = Path(self._state_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"state_ch{chapter_num:03d}.json"
        path.write_text(
            json.dumps(_to_dict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, path: str) -> "StoryState":
        """从指定路径加载快照。"""
        p = Path(path)
        if not p.exists():
            return cls()
        return _from_dict(json.loads(p.read_text(encoding="utf-8")))

    @classmethod
    def load_latest(cls, state_dir: str = "outputs/state") -> "StoryState":
        """加载 state_dir 中章节编号最大的快照；目录为空时返回默认初始状态。"""
        snapshots = sorted(Path(state_dir).glob("state_ch*.json"))
        if not snapshots:
            return cls(_state_dir=state_dir)
        latest = cls.load(str(snapshots[-1]))
        latest._state_dir = state_dir
        return latest


# ──────────────────────────────────────────────────────
# 内部辅助函数（模块私有）
# ──────────────────────────────────────────────────────

_URGENCY_ORDER = ["dormant", "building", "peak", "resolved"]


def _upgrade_urgency(anchor: ProphecyAnchor) -> None:
    try:
        idx = _URGENCY_ORDER.index(anchor.urgency)
        if idx < len(_URGENCY_ORDER) - 1:
            anchor.urgency = _URGENCY_ORDER[idx + 1]
    except ValueError:
        pass


def _compute_next_tone(pacing: NarrativePacing) -> str:
    tones = [r.tone for r in pacing.recent_tone_streak]
    if tones.count("衰寂") >= 2:
        return "过渡"
    if pacing.last_chapter_ending == "悬念":
        return "收束"
    return "平稳"


def _to_dict(state: StoryState) -> dict:
    return {
        "current_chapter": state.current_chapter,
        "active_prophecies": [asdict(p) for p in state.active_prophecies],
        "current_thematic_keywords": state.current_thematic_keywords,
        "milestones": state.milestones,
        "chapter_summary": state.chapter_summary,
        "character_states": {
            name: asdict(cs) for name, cs in state.character_states.items()
        },
        "narrative_pacing": asdict(state.narrative_pacing),
        "foreshadowing_debts": [asdict(d) for d in state.foreshadowing_debts],
    }


def _from_dict(data: dict) -> StoryState:
    state = StoryState()
    state.current_chapter = data.get("current_chapter", 80)
    state.chapter_summary = data.get("chapter_summary", "")
    state.current_thematic_keywords = data.get("current_thematic_keywords", [])
    state.milestones = data.get("milestones", state.milestones)

    state.active_prophecies = [
        ProphecyAnchor(**p) for p in data.get("active_prophecies", [])
    ]
    state.character_states = {
        name: CharacterStateEntry(**cs)
        for name, cs in data.get("character_states", {}).items()
    }
    pacing_data = data.get("narrative_pacing", {})
    streak = [ToneRecord(**r) for r in pacing_data.get("recent_tone_streak", [])]
    state.narrative_pacing = NarrativePacing(
        recent_tone_streak=streak,
        last_chapter_ending=pacing_data.get("last_chapter_ending", "收束"),
        suggested_next_tone=pacing_data.get("suggested_next_tone", "平稳"),
        notes=pacing_data.get("notes", ""),
    )
    state.foreshadowing_debts = [
        ForeshadowingDebt(**d) for d in data.get("foreshadowing_debts", [])
    ]
    return state
