#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FateEngine - 命运引擎
基于判词驱动剧情发展
"""

import yaml
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CharacterArc:
    """人物命运弧线"""
    character: str
    current_stage: str
    stage_config: Dict[str, Any]
    next_stage: Optional[str]
    upcoming_turning_point: Optional[Dict[str, Any]]
    emotional_tone: str


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    score: float
    issues: List[str]
    suggestions: List[str]


class FateEngine:
    """
    命运引擎 - 基于判词驱动剧情发展
    
    核心功能：
    1. 加载人物命运配置
    2. 根据当前章节获取人物命运阶段
    3. 验证生成的剧情是否符合命运轨迹
    4. 提供情感基调建议
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化命运引擎
        
        Args:
            config_path: 命运配置文件路径，默认使用 config/fates/character_fates.yml
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "fates" / "character_fates.yml"
        
        self.config_path = config_path
        self.fate_config = self._load_fate_config()
        self.characters = list(self.fate_config.keys())
    
    def _load_fate_config(self) -> Dict[str, Any]:
        """加载命运配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载命运配置失败: {e}")
            return {}
    
    def get_character_arc(self, character: str, current_chapter: int) -> Optional[CharacterArc]:
        """
        获取人物在当前章节的命运阶段
        
        Args:
            character: 人物名称（如"林黛玉"）
            current_chapter: 当前章节号（81-120）
            
        Returns:
            CharacterArc 对象，包含当前阶段、下一阶段、转折点等信息
        """
        if character not in self.fate_config:
            return None
        
        char_fate = self.fate_config[character]
        fate_trajectory = char_fate.get('命运轨迹', {})
        
        # 查找当前阶段
        current_stage_name = None
        current_stage_config = None
        
        for stage_name, stage_config in fate_trajectory.items():
            chapter_range = stage_config.get('章节范围', '')
            start, end = self._parse_chapter_range(chapter_range)
            
            if start <= current_chapter <= end:
                current_stage_name = stage_name
                current_stage_config = stage_config
                break
        
        if current_stage_name is None:
            return None
        
        # 查找下一阶段
        next_stage = self._get_next_stage(fate_trajectory, current_stage_name)
        
        # 查找即将到来的转折点
        turning_point = self._get_upcoming_turning_point(
            char_fate.get('关键转折点', []),
            current_chapter
        )
        
        # 获取情感基调
        emotional_tone = current_stage_config.get('情感基调', '中性')
        
        return CharacterArc(
            character=character,
            current_stage=current_stage_name,
            stage_config=current_stage_config,
            next_stage=next_stage,
            upcoming_turning_point=turning_point,
            emotional_tone=emotional_tone
        )
    
    def _parse_chapter_range(self, range_str: str) -> Tuple[int, int]:
        """解析章节范围字符串，如'81-90' -> (81, 90)"""
        try:
            parts = range_str.split('-')
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        except:
            pass
        return 81, 120
    
    def _get_next_stage(self, trajectory: Dict, current_stage: str) -> Optional[str]:
        """获取下一阶段名称"""
        stages = list(trajectory.keys())
        try:
            current_idx = stages.index(current_stage)
            if current_idx + 1 < len(stages):
                return stages[current_idx + 1]
        except ValueError:
            pass
        return None
    
    def _get_upcoming_turning_point(
        self,
        turning_points: List[Dict],
        current_chapter: int
    ) -> Optional[Dict]:
        """获取即将到来的转折点"""
        upcoming = None
        min_diff = float('inf')
        
        for tp in turning_points:
            tp_chapter = tp.get('章节', 0)
            if tp_chapter > current_chapter:
                diff = tp_chapter - current_chapter
                if diff < min_diff:
                    min_diff = diff
                    upcoming = tp
        
        return upcoming
    
    def validate_plot_consistency(
        self,
        content: str,
        chapter: int,
        characters: List[str]
    ) -> ValidationResult:
        """
        验证生成的剧情是否符合命运轨迹
        
        Args:
            content: 生成的内容
            chapter: 章节号
            characters: 涉及的人物列表
            
        Returns:
            ValidationResult 验证结果
        """
        issues = []
        suggestions = []
        total_score = 0.0
        valid_count = 0
        
        for char in characters:
            arc = self.get_character_arc(char, chapter)
            if arc is None:
                continue
            
            # 检查1: 人物行为是否符合当前阶段
            behavior_check = self._check_behavior_consistency(
                content, char, arc.stage_config
            )
            
            # 检查2: 情感基调是否符合
            tone_check = self._check_emotional_tone(
                content, arc.emotional_tone
            )
            
            # 检查3: 是否提前泄露未来命运
            spoiler_check = self._check_spoiler_leak(
                content, char, chapter
            )
            
            char_score = (behavior_check['score'] + tone_check['score'] + spoiler_check['score']) / 3
            total_score += char_score
            valid_count += 1
            
            issues.extend(behavior_check['issues'])
            issues.extend(tone_check['issues'])
            issues.extend(spoiler_check['issues'])
            
            suggestions.extend(behavior_check['suggestions'])
            suggestions.extend(tone_check['suggestions'])
            suggestions.extend(spoiler_check['suggestions'])
        
        avg_score = total_score / valid_count if valid_count > 0 else 0.0
        
        return ValidationResult(
            is_valid=avg_score >= 0.6,
            score=avg_score,
            issues=issues,
            suggestions=suggestions
        )
    
    def _check_behavior_consistency(
        self,
        content: str,
        character: str,
        stage_config: Dict
    ) -> Dict:
        """检查人物行为是否符合阶段配置"""
        key_events = stage_config.get('关键事件', [])
        issues = []
        suggestions = []
        score = 1.0
        
        # 简化检查：确保内容中有该人物
        if character not in content:
            issues.append(f"内容中缺少人物'{character}'")
            score -= 0.3
        
        return {
            'score': max(0, score),
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _check_emotional_tone(self, content: str, expected_tone: str) -> Dict:
        """检查情感基调是否符合"""
        issues = []
        suggestions = []
        score = 1.0
        
        # 情感基调关键词映射
        tone_keywords = {
            '哀而不伤': ['愁', '叹', '悲', '泪'],
            '大悲大痛转希望': ['哭', '痛', '死', '疯'],
            '悲喜交加': ['喜', '悲', '哭', '笑'],
            '温馨圆满': ['喜', '笑', '乐', '福'],
            '中性': []
        }
        
        keywords = tone_keywords.get(expected_tone, [])
        if keywords:
            found = any(kw in content for kw in keywords)
            if not found:
                suggestions.append(f"建议增加'{expected_tone}'相关的情感描写")
                score -= 0.2
        
        return {
            'score': max(0, score),
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _check_spoiler_leak(self, content: str, character: str, chapter: int) -> Dict:
        """检查是否提前泄露未来命运"""
        issues = []
        suggestions = []
        score = 1.0
        
        # 获取该人物的所有转折点
        if character in self.fate_config:
            turning_points = self.fate_config[character].get('关键转折点', [])
            for tp in turning_points:
                tp_chapter = tp.get('章节', 0)
                if tp_chapter > chapter:
                    # 检查是否提前提到了未来事件
                    tp_event = tp.get('事件', '')
                    if tp_event and tp_event in content:
                        issues.append(f"提前泄露了第{tp_chapter}回的事件：{tp_event}")
                        score -= 0.5
        
        return {
            'score': max(0, score),
            'issues': issues,
            'suggestions': suggestions
        }
    
    def get_all_characters(self) -> List[str]:
        """获取所有已配置的人物列表"""
        return self.characters
    
    def get_fate_summary(self, character: str) -> Optional[str]:
        """获取人物判词"""
        if character not in self.fate_config:
            return None
        return self.fate_config[character].get('判词', '')


# 便捷函数
def create_fate_engine() -> FateEngine:
    """创建默认的命运引擎实例"""
    return FateEngine()


if __name__ == "__main__":
    # 测试
    engine = create_fate_engine()
    
    print("=" * 60)
    print("🎭 FateEngine 测试")
    print("=" * 60)
    
    # 测试获取人物弧线
    arc = engine.get_character_arc("林黛玉", 85)
    if arc:
        print(f"\n👤 {arc.character} @ 第85回")
        print(f"  当前阶段: {arc.current_stage}")
        print(f"  情感基调: {arc.emotional_tone}")
        if arc.upcoming_turning_point:
            print(f"  即将到来: 第{arc.upcoming_turning_point['章节']}回 - {arc.upcoming_turning_point['事件']}")
    
    # 测试判词
    poem = engine.get_fate_summary("贾宝玉")
    print(f"\n📜 宝玉判词: {poem}")
    
    print("\n✅ FateEngine 测试完成")
