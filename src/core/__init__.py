"""
Core 模块 - 新系统核心组件
"""

from .fate_engine import FateEngine, CharacterArc, ValidationResult
from .intent_loader import IntentLoader, load_default_intent
from .intent_parser import IntentParser, UserIntent, parse_user_intent
from .plot_planner import PlotPlanner, MasterPlan, ChapterPlan, Phase
from .foreshadowing import ForeshadowingManager, Foreshadowing

__all__ = [
    'FateEngine', 'CharacterArc', 'ValidationResult',
    'IntentLoader', 'load_default_intent',
    'IntentParser', 'UserIntent', 'parse_user_intent',
    'PlotPlanner', 'MasterPlan', 'ChapterPlan', 'Phase',
    'ForeshadowingManager', 'Foreshadowing'
]
