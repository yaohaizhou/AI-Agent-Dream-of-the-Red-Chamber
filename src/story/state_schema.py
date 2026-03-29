"""五层故事状态机的数据结构定义。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class ProphecyAnchor:
    """L1：判词意象层 — 跟踪十二钗判词的激活与兑现。"""
    id: str
    character: str
    prophecy_fragment: str
    keywords: List[str]
    activated_at_chapter: int
    urgency: str  # dormant | building | peak | resolved


@dataclass
class ToneRecord:
    """L4 辅助：单章叙事基调记录。"""
    chapter: int
    tone: str  # 热闹 | 衰寂 | 忧虑 | 悲恸 | 过渡


@dataclass
class NarrativePacing:
    """L4：叙事节奏层 — 防止连续多章基调相同。"""
    recent_tone_streak: List[ToneRecord] = field(default_factory=list)
    last_chapter_ending: str = "收束"   # 悬念 | 收束 | 过渡
    suggested_next_tone: str = "平稳"
    notes: str = ""


@dataclass
class CharacterStateEntry:
    """L3：人物概况层 — 定性描述，不用数字。"""
    health_trend: str = "平稳"    # 平稳 | 衰退 | 危急 | 已逝
    emotional_center: str = "平静"
    last_scene_chapter: int = 80
    notes: str = ""


@dataclass
class ForeshadowingDebt:
    """L5：伏笔债务层 — 追踪每条伏笔的压力与兑现进度。"""
    id: str
    description: str
    source: str
    keywords: List[str]
    planted_at_chapter: int
    last_hinted_chapter: int
    chapters_since_hint: int
    urgency_weight: float   # 0.0–1.0
    status: str             # pending | hinting | resolved
