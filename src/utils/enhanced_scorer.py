#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版人物一致性评分器 V2
使用结构化关键词库，提升评分精度
"""

import json
from typing import Dict, Any, List
from pathlib import Path


class EnhancedCharacterScorer:
    """增强版人物评分器"""
    
    def __init__(self):
        self.keywords_db = self._load_keywords_db()
    
    def _load_keywords_db(self) -> Dict:
        """加载关键词库"""
        keywords_path = Path(__file__).parent / "character_keywords.json"
        with open(keywords_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def score_character(self, content: str, character_name: str) -> Dict[str, Any]:
        """
        评分单个人物的一致性
        
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
        
        content_lower = content.lower()
        details = {}
        
        # 1. 语言风格评分 (40%)
        speech_score = self._score_speech(content_lower, char_data)
        details["speech"] = speech_score
        
        # 2. 行为特征评分 (40%)
        behavior_score = self._score_behavior(content_lower, char_data)
        details["behavior"] = behavior_score
        
        # 3. 人物关系评分 (20%)
        relationship_score = self._score_relationships(content_lower, char_data)
        details["relationships"] = relationship_score
        
        # 计算总分 (0-10)
        total = (
            speech_score["score"] * 0.4 +
            behavior_score["score"] * 0.4 +
            relationship_score["score"] * 0.2
        ) * 10
        
        return {
            "total_score": total,
            "speech_score": speech_score["score"] * 10,
            "behavior_score": behavior_score["score"] * 10,
            "relationship_score": relationship_score["score"] * 10,
            "details": details
        }
    
    def _score_speech(self, content: str, char_data: Dict) -> Dict:
        """评分语言风格"""
        speech = char_data.get("speech", {})
        weights = self.keywords_db.get("scoring_weights", {})
        
        # 高权重关键词
        high_keywords = speech.get("high_weight", [])
        high_matches = sum(1 for kw in high_keywords if kw in content)
        high_score = min(high_matches / max(len(high_keywords) * 0.3, 1), 1.0)
        
        # 中权重关键词
        medium_keywords = speech.get("medium_weight", [])
        medium_matches = sum(1 for kw in medium_keywords if kw in content)
        medium_score = min(medium_matches / max(len(medium_keywords) * 0.2, 1), 1.0)
        
        # 标志性词汇
        signature_keywords = speech.get("signature", [])
        sig_matches = sum(1 for kw in signature_keywords if kw in content)
        sig_score = min(sig_matches / max(len(signature_keywords) * 0.2, 1), 0.5)
        
        # 加权总分
        total = (
            high_score * weights.get("speech_high", 0.3) +
            medium_score * weights.get("speech_medium", 0.15) +
            sig_score
        )
        
        return {
            "score": min(total, 1.0),
            "high_matches": high_matches,
            "medium_matches": medium_matches,
            "signature_matches": sig_matches
        }
    
    def _score_behavior(self, content: str, char_data: Dict) -> Dict:
        """评分行为特征"""
        behavior = char_data.get("behavior", {})
        weights = self.keywords_db.get("scoring_weights", {})
        
        # 行为动作
        actions = behavior.get("actions", [])
        action_matches = sum(1 for kw in actions if kw in content)
        action_score = min(action_matches / max(len(actions) * 0.3, 1), 1.0)
        
        # 情感表达
        emotions = behavior.get("emotions", [])
        emotion_matches = sum(1 for kw in emotions if kw in content)
        emotion_score = min(emotion_matches / max(len(emotions) * 0.3, 1), 1.0)
        
        # 语境词
        context = behavior.get("context", [])
        context_matches = sum(1 for kw in context if kw in content)
        context_score = min(context_matches / max(len(context) * 0.2, 1), 0.5)
        
        # 加权总分
        total = (
            action_score * weights.get("behavior_actions", 0.25) +
            emotion_score * weights.get("behavior_emotions", 0.15) +
            context_score
        )
        
        return {
            "score": min(total, 1.0),
            "action_matches": action_matches,
            "emotion_matches": emotion_matches,
            "context_matches": context_matches
        }
    
    def _score_relationships(self, content: str, char_data: Dict) -> Dict:
        """评分人物关系"""
        relationships = char_data.get("relationships", {})
        
        if not relationships:
            return {"score": 0.5, "matches": {}}
        
        total_score = 0
        match_details = {}
        
        for related_char, keywords in relationships.items():
            if related_char in content:
                matches = [kw for kw in keywords if kw in content]
                if matches:
                    score = min(len(matches) / 2, 1.0)
                    total_score += score
                    match_details[related_char] = {
                        "score": score,
                        "matches": matches
                    }
        
        avg_score = total_score / len(relationships) if relationships else 0.5
        
        return {
            "score": avg_score,
            "matches": match_details
        }


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
    
    # 计算平均分
    avg_score = sum(r["total_score"] for r in results.values()) / len(results) if results else 0
    
    return {
        "overall_score": avg_score,
        "individual_scores": results
    }


if __name__ == "__main__":
    # 测试
    test_content = """
    宝玉笑道："好妹妹，你今日可好些了？"
    黛玉摇头叹道："还是那样，只是咳嗽得厉害。"
    宝玉垂泪道："妹妹若有个三长两短，我岂能独活？"
    黛玉听了，心中感动，亦自垂泪。
    """
    
    result = score_content(test_content, ["宝玉", "黛玉"])
    
    print("=" * 60)
    print("🧪 增强版评分器测试")
    print("=" * 60)
    print(f"\n综合评分: {result['overall_score']:.1f}/10.0")
    
    for char, score_data in result['individual_scores'].items():
        print(f"\n👤 {char}:")
        print(f"  总分: {score_data['total_score']:.1f}")
        print(f"  语言: {score_data['speech_score']:.1f}")
        print(f"  行为: {score_data['behavior_score']:.1f}")
        print(f"  关系: {score_data['relationship_score']:.1f}")
