#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评分器基类模块
提供统一的评分逻辑和配置管理
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Protocol
from dataclasses import dataclass
import re
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoreConfig:
    """评分配置常量"""
    # 基础分数
    SPEECH_BASE_SCORE: float = 0.5
    BEHAVIOR_BASE_SCORE: float = 0.45
    EMOTION_BASE_SCORE: float = 0.5
    RELATIONSHIP_BASE_SCORE: float = 0.5
    STRUCTURE_BASE_SCORE: float = 0.5
    STYLE_BASE_SCORE: float = 0.5
    
    # 权重配置
    SPEECH_WEIGHT_HIGH: float = 0.25
    SPEECH_WEIGHT_MEDIUM: float = 0.15
    SPEECH_WEIGHT_SIGNATURE: float = 0.10
    
    BEHAVIOR_WEIGHT_HIGH: float = 0.25
    BEHAVIOR_WEIGHT_CONTEXT: float = 0.15
    BEHAVIOR_WEIGHT_MEDIUM: float = 0.10
    
    EMOTION_WEIGHT_DEDUCT: float = 0.30
    EMOTION_WEIGHT_BONUS: float = 0.20
    
    RELATIONSHIP_WEIGHT_FOUND: float = 0.25
    RELATIONSHIP_WEIGHT_KEYWORDS_2: float = 0.15
    RELATIONSHIP_WEIGHT_KEYWORDS_4: float = 0.10
    
    # 阈值配置
    HIGH_MATCH_THRESHOLD: int = 3
    MEDIUM_MATCH_THRESHOLD: int = 3
    EMOTION_COUNT_THRESHOLD: int = 3
    RELATIONSHIP_KEYWORDS_THRESHOLD_1: int = 2
    RELATIONSHIP_KEYWORDS_THRESHOLD_2: int = 4
    
    # 维度权重（用于综合评分）
    DIMENSION_WEIGHT_SPEECH: float = 0.30
    DIMENSION_WEIGHT_BEHAVIOR: float = 0.25
    DIMENSION_WEIGHT_EMOTION: float = 0.25
    DIMENSION_WEIGHT_RELATIONSHIP: float = 0.20
    
    # 质量等级阈值
    QUALITY_THRESHOLD_EXCELLENT: float = 9.0
    QUALITY_THRESHOLD_GOOD: float = 8.0
    QUALITY_THRESHOLD_PASS: float = 7.0
    QUALITY_THRESHOLD_FAIR: float = 6.0
    QUALITY_THRESHOLD_POOR: float = 5.0


class KeywordCache:
    """关键词缓存，预编译正则表达式以提高性能"""
    
    def __init__(self):
        self._patterns: Dict[str, re.Pattern] = {}
        self._indicator_sets: Dict[str, List[str]] = {}
    
    def get_pattern(self, keyword: str) -> re.Pattern:
        """获取编译后的正则表达式"""
        if keyword not in self._patterns:
            self._patterns[keyword] = re.compile(re.escape(keyword))
        return self._patterns[keyword]
    
    def match_any(self, content: str, keywords: List[str]) -> List[str]:
        """匹配任意关键词，返回匹配列表"""
        matches = []
        content_lower = content.lower()
        for kw in keywords:
            if self.get_pattern(kw).search(content_lower):
                matches.append(kw)
        return matches
    
    def count_matches(self, content: str, keywords: List[str]) -> int:
        """计算关键词匹配数量"""
        return len(self.match_any(content, keywords))
    
    def register_indicator_set(self, name: str, indicators: List[str]):
        """注册一组指标词"""
        self._indicator_sets[name] = indicators
    
    def count_indicators(self, content: str, set_name: str) -> int:
        """计算特定指标集的出现次数"""
        if set_name not in self._indicator_sets:
            return 0
        return sum(1 for ind in self._indicator_sets[set_name] if ind in content)


# 全局缓存实例
_keyword_cache = KeywordCache()


def get_keyword_cache() -> KeywordCache:
    """获取全局关键词缓存实例"""
    return _keyword_cache


class BaseScorer(ABC):
    """评分器抽象基类"""
    
    def __init__(self, config: Optional[ScoreConfig] = None):
        self.config = config or ScoreConfig()
        self.cache = get_keyword_cache()
    
    @abstractmethod
    def score(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        评分接口
        
        Args:
            content: 待评分内容
            **kwargs: 额外参数
            
        Returns:
            评分结果字典
        """
        pass
    
    def get_quality_level(self, score: float) -> str:
        """根据分数获取质量等级"""
        if score >= self.config.QUALITY_THRESHOLD_EXCELLENT:
            return "🏆 大师级"
        elif score >= self.config.QUALITY_THRESHOLD_GOOD:
            return "✨ 优秀"
        elif score >= self.config.QUALITY_THRESHOLD_PASS:
            return "✅ 良好"
        elif score >= self.config.QUALITY_THRESHOLD_FAIR:
            return "📝 合格"
        elif score >= self.config.QUALITY_THRESHOLD_POOR:
            return "⚠️ 待改进"
        else:
            return "❌ 需要重写"


class CharacterScorerMixin:
    """人物评分通用方法混入类"""
    
    config: ScoreConfig
    cache: KeywordCache
    
    def score_speech_pattern(
        self,
        content: str,
        speech_keywords: Dict[str, List[str]]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        评分语言风格
        
        Returns:
            (分数0-1, 详细信息)
        """
        cfg = self.config
        content_lower = content.lower()
        
        # 匹配各级关键词
        high_matches = self.cache.match_any(
            content, speech_keywords.get('high', [])
        )
        medium_matches = self.cache.match_any(
            content, speech_keywords.get('medium', [])
        )
        sig_matches = self.cache.match_any(
            content, speech_keywords.get('signature', [])
        )
        
        # 计算分数
        score = cfg.SPEECH_BASE_SCORE
        
        if len(high_matches) >= 1:
            score += cfg.SPEECH_WEIGHT_HIGH
        if len(high_matches) >= cfg.HIGH_MATCH_THRESHOLD:
            score += cfg.SPEECH_WEIGHT_HIGH * 0.4  # 额外奖励
            
        if len(medium_matches) >= 1:
            score += cfg.SPEECH_WEIGHT_MEDIUM
        if len(medium_matches) >= cfg.MEDIUM_MATCH_THRESHOLD:
            score += cfg.SPEECH_WEIGHT_MEDIUM * 0.67
            
        if len(sig_matches) >= 1:
            score += cfg.SPEECH_WEIGHT_SIGNATURE
        
        score = min(score, 1.0)
        
        details = {
            'matches': {
                'high': high_matches,
                'medium': medium_matches,
                'signature': sig_matches
            },
            'score_breakdown': {
                'base': cfg.SPEECH_BASE_SCORE,
                'high_matches': len(high_matches),
                'medium_matches': len(medium_matches),
                'signature_matches': len(sig_matches),
                'final': score
            }
        }
        
        return score, details
    
    def score_behavior(
        self,
        content: str,
        behavior_keywords: Dict[str, List[str]]
    ) -> Tuple[float, Dict[str, Any]]:
        """评分行为特征"""
        cfg = self.config
        
        high_matches = self.cache.match_any(
            content, behavior_keywords.get('high', [])
        )
        context_matches = self.cache.match_any(
            content, behavior_keywords.get('context', [])
        )
        medium_matches = self.cache.match_any(
            content, behavior_keywords.get('medium', [])
        )
        
        score = cfg.BEHAVIOR_BASE_SCORE
        
        if len(high_matches) >= 1:
            score += cfg.BEHAVIOR_WEIGHT_HIGH
        if len(high_matches) >= cfg.HIGH_MATCH_THRESHOLD:
            score += cfg.BEHAVIOR_WEIGHT_HIGH * 0.4
            
        if len(context_matches) >= 1:
            score += cfg.BEHAVIOR_WEIGHT_CONTEXT
            
        if len(medium_matches) >= 1:
            score += cfg.BEHAVIOR_WEIGHT_MEDIUM
        
        score = min(score, 1.0)
        
        details = {
            'action_matches': high_matches,
            'context_matches': context_matches,
            'medium_matches': medium_matches
        }
        
        return score, details
    
    def score_emotion(
        self,
        content: str,
        emotion_keywords: Dict[str, List[str]]
    ) -> Tuple[float, Dict[str, Any]]:
        """评分情感表达"""
        cfg = self.config
        content_lower = content.lower()
        
        # 统计情感词出现次数
        positive_count = sum(
            content_lower.count(kw) 
            for kw in emotion_keywords.get('positive', [])
        )
        negative_count = sum(
            content_lower.count(kw) 
            for kw in emotion_keywords.get('negative', [])
        )
        dominant_count = sum(
            content_lower.count(kw) 
            for kw in emotion_keywords.get('dominant', [])
        )
        
        total_emotions = positive_count + negative_count + dominant_count
        
        score = cfg.EMOTION_BASE_SCORE
        
        if total_emotions > 0:
            score += cfg.EMOTION_WEIGHT_DEDUCT
            if dominant_count >= cfg.EMOTION_COUNT_THRESHOLD:
                score += cfg.EMOTION_WEIGHT_BONUS
        
        score = min(score, 1.0)
        
        details = {
            'emotion_counts': {
                'positive': positive_count,
                'negative': negative_count,
                'dominant': dominant_count
            }
        }
        
        return score, details
    
    def score_relationships(
        self,
        content: str,
        relationship_keywords: Dict[str, List[str]]
    ) -> Tuple[float, Dict[str, Any]]:
        """评分人物关系"""
        cfg = self.config
        content_lower = content.lower()
        
        relation_found = False
        keyword_hits = 0
        match_details = {}
        
        for rel_char, keywords in relationship_keywords.items():
            if rel_char in content_lower:
                relation_found = True
                hits = self.cache.match_any(content, keywords)
                keyword_hits += len(hits)
                match_details[rel_char] = {
                    'hits': hits,
                    'count': len(hits)
                }
        
        score = cfg.RELATIONSHIP_BASE_SCORE
        
        if relation_found:
            score += cfg.RELATIONSHIP_WEIGHT_FOUND
        if keyword_hits >= cfg.RELATIONSHIP_KEYWORDS_THRESHOLD_1:
            score += cfg.RELATIONSHIP_WEIGHT_KEYWORDS_2
        if keyword_hits >= cfg.RELATIONSHIP_KEYWORDS_THRESHOLD_2:
            score += cfg.RELATIONSHIP_WEIGHT_KEYWORDS_4
        
        score = min(score, 1.0)
        
        details = {
            'hits': match_details,
            'total_keyword_hits': keyword_hits,
            'relation_found': relation_found
        }
        
        return score, details
    
    def calculate_weighted_score(
        self,
        speech_score: float,
        behavior_score: float,
        emotion_score: float,
        relationship_score: float
    ) -> float:
        """计算加权综合分数"""
        cfg = self.config
        return (
            speech_score * cfg.DIMENSION_WEIGHT_SPEECH +
            behavior_score * cfg.DIMENSION_WEIGHT_BEHAVIOR +
            emotion_score * cfg.DIMENSION_WEIGHT_EMOTION +
            relationship_score * cfg.DIMENSION_WEIGHT_RELATIONSHIP
        )


class StyleEvaluator:
    """风格评估器"""
    
    # 预定义的指标集
    CLASSICAL_INDICATORS = [
        "话说", "原来", "却说", "且听下回分解", "正是",
        "诗曰", "词曰", "只见", "但见", "忽见", "忽听",
        "次日", "当下", "且说", "不说", "再说"
    ]
    
    WENYAN_INDICATORS = ["之", "乎", "者", "也", "矣", "焉", "哉", "耳", "夫", "盖"]
    
    HONGLOUMENG_INDICATORS = [
        "丫鬟", "嬷嬷", "太太", "老太太", "老爷", "奶奶", "姑娘",
        "小姐", "公子", "爷", "奴才", "婢子", "小的"
    ]
    
    DIALOGUE_MARKERS = ["道：", "说道", "笑道", "叹道", "问道", "答道", "忙道"]
    
    def __init__(self):
        self.cache = get_keyword_cache()
        # 注册指标集
        self.cache.register_indicator_set('classical', self.CLASSICAL_INDICATORS)
        self.cache.register_indicator_set('wenyan', self.WENYAN_INDICATORS)
        self.cache.register_indicator_set('hongloumeng', self.HONGLOUMENG_INDICATORS)
        self.cache.register_indicator_set('dialogue', self.DIALOGUE_MARKERS)
    
    def evaluate(self, content: str) -> float:
        """
        评估风格一致性
        
        Returns:
            0-10分的风格评分
        """
        score = 6.0  # 基础分
        
        # 检查古典文学特征词
        indicator_count = self.cache.count_indicators(content, 'classical')
        score += min(indicator_count * 0.6, 3.5)
        
        # 检查文言文成分
        wenyan_count = sum(content.count(char) for char in self.WENYAN_INDICATORS)
        score += min(wenyan_count * 0.3, 2.0)
        
        # 检查《红楼梦》特色词汇
        hongloumeng_count = self.cache.count_indicators(content, 'hongloumeng')
        score += min(hongloumeng_count * 0.4, 2.0)
        
        # 检查对话标记
        dialogue_count = self.cache.count_indicators(content, 'dialogue')
        score += min(dialogue_count * 0.3, 1.5)
        
        return min(score, 10.0)


class StructureEvaluator:
    """结构完整性评估器"""
    
    ENDING_MARKERS = [
        '且听下回分解', '正是', '后事如何', 
        '下回书交代', '不知', '原来'
    ]
    
    def __init__(self):
        self.cache = get_keyword_cache()
    
    def evaluate(
        self,
        content: str,
        chapter_info: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        评估结构完整性
        
        Returns:
            0-1分的结构评分
        """
        score = 0.5  # 基础分
        
        # 检查是否有回目
        if chapter_info and chapter_info.get('title'):
            score += 0.15
        
        # 检查内容长度
        if 200 <= len(content) <= 10000:
            score += 0.15
        
        # 检查是否有诗词或对话标记
        if '诗' in content or '词' in content or '道：' in content:
            score += 0.1
        
        # 检查结尾标记
        if any(marker in content for marker in self.ENDING_MARKERS):
            score += 0.1
        
        return min(score, 1.0)


# 便捷函数
def create_default_scorer() -> Tuple[ScoreConfig, KeywordCache]:
    """创建默认评分配置和缓存"""
    return ScoreConfig(), get_keyword_cache()


def safe_score(default_value: float = 6.0):
    """
    评分函数错误处理装饰器
    
    Usage:
        @safe_score(default_value=6.0)
        def evaluate_something(self, content):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{func.__name__} 失败: {e}", exc_info=True)
                return default_value
        return wrapper
    return decorator
