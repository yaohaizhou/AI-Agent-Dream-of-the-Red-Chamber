#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版人物一致性评分器 V4
使用 base_scorer 基类模块
"""

import json
from typing import Dict, Any, List
from pathlib import Path

from src.utils.base_scorer import BaseScorer, CharacterScorerMixin, ScoreConfig, get_keyword_cache


class EnhancedCharacterScorer(BaseScorer, CharacterScorerMixin):
    """增强版人物评分器 V4 - 使用基类"""
    
    def __init__(self, config: ScoreConfig = None):
        super().__init__(config)
        self.cache = get_keyword_cache()
        self.keywords_db = self._load_keywords_db()
    
    def _load_keywords_db(self) -> Dict:
        """加载关键词库"""
        keywords_path = Path(__file__).parent / "character_keywords.json"
        with open(keywords_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def score_character(self, content: str, character_name: str) -> Dict[str, Any]:
        """
        评分单个人物的一致性 - 使用基类方法
        
        Returns:
            {
                "total_score": float,  # 0-10
                "speech_score": float,
                "behavior_score": float,
                "relationship_score": float,
                "details": Dict
            }
        """
        char_data = self.keywords_db["characters"].get(character_name)
        if not char_data:
            return {"total_score": 5.0, "error": f"未找到人物: {character_name}"}
        
        # 使用基类 CharacterScorerMixin 的方法
        speech_score, speech_details = self.score_speech_pattern(
            content, char_data.get("speech", {})
        )
        behavior_score, behavior_details = self.score_behavior(
            content, char_data.get("behavior", {})
        )
        emotion_score, emotion_details = self.score_emotion(
            content, char_data.get("behavior", {})
        )
        relation_score, relation_details = self.score_relationships(
            content, char_data.get("relationships", {})
        )
        
        # 使用基类方法计算加权分数
        total_normalized = self.calculate_weighted_score(
            speech_score, behavior_score, emotion_score, relation_score
        )
        
        return {
            "total_score": total_normalized * 10,  # 转换为0-10范围
            "speech_score": speech_score * 10,
            "behavior_score": behavior_score * 10,
            "emotion_score": emotion_score * 10,
            "relationship_score": relation_score * 10,
            "details": {
                "speech": speech_details,
                "behavior": behavior_details,
                "emotion": emotion_details,
                "relationships": relation_details
            }
        }
    
    # 注意：_check_speech, _check_behavior, _check_emotion, _check_relationships
    # 方法已被移除，现在使用从 CharacterScorerMixin 继承的方法：
    # - score_speech_pattern()
    # - score_behavior()
    # - score_emotion()
    # - score_relationships()
    # - calculate_weighted_score()
    
    def score(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        实现基类的抽象方法
        
        Args:
            content: 待评分内容
            **kwargs: 额外参数，应包含 'characters' 列表
            
        Returns:
            评分结果字典
        """
        characters = kwargs.get('characters', ['宝玉', '黛玉'])
        return score_content(content, characters)


# 便捷函数
def score_content(content: str, characters: List[str]) -> Dict[str, Any]:
    """
    快速评分接口
    
    Args:
        content: 待评分内容
        characters: 需要评分的人物列表
    
    Returns:
        评分结果字典
    """
    scorer = EnhancedCharacterScorer()
    results = {}
    
    for char in characters:
        results[char] = scorer.score_character(content, char)
    
    avg_score = sum(r["total_score"] for r in results.values()) / len(results) if results else 0
    
    return {
        "overall_score": avg_score,
        "individual_scores": results
    }


def generate_score_report(content: str, characters: List[str]) -> str:
    """
    生成详细评分报告
    
    Args:
        content: 待评分内容
        characters: 需要评分的人物列表
    
    Returns:
        格式化的评分报告字符串
    """
    result = score_content(content, characters)
    
    report_lines = [
        "=" * 60,
        "📝 人物一致性评分报告",
        "=" * 60,
        f"\n📊 综合评分: {result['overall_score']:.2f}/10.0",
        f"\n质量等级: {_get_quality_level(result['overall_score'])}",
    ]
    
    for char, score_data in result['individual_scores'].items():
        report_lines.append(f"\n{'='*60}")
        report_lines.append(f"👤 {char}")
        report_lines.append(f"{'='*60}")
        report_lines.append(f"  总分: {score_data['total_score']:.2f}")
        report_lines.append(f"  ├─ 语言风格: {score_data['speech_score']:.2f}")
        report_lines.append(f"  ├─ 行为特征: {score_data['behavior_score']:.2f}")
        report_lines.append(f"  ├─ 情感表达: {score_data['emotion_score']:.2f}")
        report_lines.append(f"  └─ 人物关系: {score_data['relationship_score']:.2f}")
        
        # 添加详细匹配信息
        details = score_data.get('details', {})
        if 'speech' in details:
            speech = details['speech']
            if speech.get('high_matches'):
                report_lines.append(f"\n  语言关键词命中: {speech['high_matches'][:5]}")
    
    report_lines.append("\n" + "=" * 60)
    return "\n".join(report_lines)


def _get_quality_level(score: float) -> str:
    """获取质量等级"""
    if score >= 9.0:
        return "🏆 大师级"
    elif score >= 8.0:
        return "✨ 优秀"
    elif score >= 7.0:
        return "✅ 良好"
    elif score >= 6.0:
        return "📝 合格"
    elif score >= 5.0:
        return "⚠️ 待改进"
    else:
        return "❌ 需要重写"


if __name__ == "__main__":
    # 测试
    test_content = """
    话说宝玉自那日见了黛玉，心中便放不下。这日早起，便往潇湘馆来。 
    黛玉正在窗下抚琴，见宝玉进来，便停下手中活儿。 
    宝玉笑道：'好妹妹，你今日气色比昨日好些了。' 
    黛玉摇头叹道：'不过是一时罢了，我这身子你是知道的。' 
    宝玉听了，心中甚是难过，赔笑道：'妹妹何必如此说，我这几日正想着 
    要去求老太太，请个高明大夫来给你瞧瞧。' 
    黛玉垂泪道：'你又说这些，我怎当得起。' 
    二人相对无言，只是叹气。
    """
    
    print(generate_score_report(test_content, ["宝玉", "黛玉"]))
