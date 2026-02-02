#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版人物一致性评分器 V3
与 character_consistency_checker.py 使用相同的评分逻辑
"""

import json
from typing import Dict, Any, List
from pathlib import Path


class EnhancedCharacterScorer:
    """增强版人物评分器 V3"""
    
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
        
        # 使用与 character_consistency_checker 相同的评分逻辑
        speech_score, speech_details = self._check_speech(content_lower, char_data)
        behavior_score, behavior_details = self._check_behavior(content_lower, char_data)
        emotion_score, emotion_details = self._check_emotion(content_lower, char_data)
        relation_score, relation_details = self._check_relationships(content_lower, char_data)
        
        # 计算加权分数 (与 character_consistency_checker 相同权重)
        total_normalized = (
            speech_score * 0.30 +
            behavior_score * 0.25 +
            emotion_score * 0.25 +
            relation_score * 0.20
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
    
    def _check_speech(self, content: str, char_data: Dict) -> tuple[float, Dict]:
        """检查语言风格 - 与 character_consistency_checker 相同逻辑"""
        speech = char_data.get("speech", {})
        
        base_score = 0.5
        
        # 高权重关键词
        high_keywords = speech.get("high_weight", [])
        high_matches = [kw for kw in high_keywords if kw in content]
        high_score = 0.25 if len(high_matches) >= 1 else 0.0
        if len(high_matches) >= 3:
            high_score = 0.35
        
        # 中权重关键词
        medium_keywords = speech.get("medium_weight", [])
        medium_matches = [kw for kw in medium_keywords if kw in content]
        medium_score = 0.15 if len(medium_matches) >= 1 else 0.0
        if len(medium_matches) >= 3:
            medium_score = 0.25
        
        # 标志性词汇
        signature_keywords = speech.get("signature", [])
        sig_matches = [kw for kw in signature_keywords if kw in content]
        sig_score = 0.1 if len(sig_matches) >= 1 else 0.0
        
        score = base_score + high_score + medium_score + sig_score
        score = min(score, 1.0)
        
        return score, {
            "high_matches": high_matches,
            "medium_matches": medium_matches,
            "signature_matches": sig_matches,
            "score_breakdown": {"base": base_score, "high": high_score, "medium": medium_score, "sig": sig_score}
        }
    
    def _check_behavior(self, content: str, char_data: Dict) -> tuple[float, Dict]:
        """检查行为特征"""
        behavior = char_data.get("behavior", {})
        
        base_score = 0.45
        
        # 高权重行为
        actions = behavior.get("actions", [])
        action_matches = [kw for kw in actions if kw in content]
        action_score = 0.25 if len(action_matches) >= 1 else 0.0
        if len(action_matches) >= 3:
            action_score = 0.35
        
        # 上下文行为
        context = behavior.get("context", [])
        context_matches = [kw for kw in context if kw in content]
        context_score = 0.15 if len(context_matches) >= 1 else 0.0
        
        # medium行为
        medium_actions = behavior.get("medium", [])
        medium_matches = [kw for kw in medium_actions if kw in content]
        medium_score = 0.1 if len(medium_matches) >= 1 else 0.0
        
        score = base_score + action_score + context_score + medium_score
        score = min(score, 1.0)
        
        return score, {
            "action_matches": action_matches,
            "context_matches": context_matches,
            "medium_matches": medium_matches
        }
    
    def _check_emotion(self, content: str, char_data: Dict) -> tuple[float, Dict]:
        """检查情感倾向"""
        emotions = char_data.get("behavior", {}).get("emotions", [])
        
        base_score = 0.5
        
        emotion_count = sum(content.count(kw) for kw in emotions)
        
        emotion_score = 0.0
        if emotion_count > 0:
            emotion_score = 0.3
            if emotion_count >= 3:
                emotion_score += 0.2
        
        score = base_score + emotion_score
        score = min(score, 1.0)
        
        return score, {"emotion_count": emotion_count}
    
    def _check_relationships(self, content: str, char_data: Dict) -> tuple[float, Dict]:
        """检查人物关系"""
        relationships = char_data.get("relationships", {})
        
        base_score = 0.5
        relation_found = False
        keyword_hits = 0
        match_details = {}
        
        for related_char, keywords in relationships.items():
            if related_char in content:
                relation_found = True
                hits = [kw for kw in keywords if kw in content]
                if hits:
                    keyword_hits += len(hits)
                match_details[related_char] = {"hits": hits}
        
        dynamic_score = 0.0
        if relation_found:
            dynamic_score = 0.25
        if keyword_hits >= 2:
            dynamic_score += 0.15
        if keyword_hits >= 4:
            dynamic_score += 0.1
        
        score = base_score + dynamic_score
        score = min(score, 1.0)
        
        return score, {"hits": match_details, "keyword_hits": keyword_hits}


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
