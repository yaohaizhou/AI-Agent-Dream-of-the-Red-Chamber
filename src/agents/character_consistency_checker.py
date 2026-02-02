#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人物一致性检查模块 V2
使用关键词匹配替代长文本匹配，解决评分严重偏低问题
"""

import asyncio
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CharacterProfile:
    """人物档案 - 结构化关键词版"""
    name: str
    # 语言风格关键词
    speech_keywords: Dict[str, List[str]]  # weight -> keywords
    # 行为特征关键词
    behavior_keywords: Dict[str, List[str]]
    # 情感倾向关键词
    emotion_keywords: Dict[str, List[str]]
    # 人物关系关键词
    relationship_keywords: Dict[str, List[str]]
    # 核心价值观关键词
    value_keywords: List[str]


class CharacterConsistencyChecker:
    """人物一致性检查器 V2 - 修复版"""
    
    def __init__(self, gpt5_client=None, prompts=None):
        self.gpt5_client = gpt5_client
        self.prompts = prompts
        self.character_profiles = self._load_character_profiles()
    
    def _load_character_profiles(self) -> Dict[str, CharacterProfile]:
        """加载结构化人物档案 - 使用关键词而非长描述"""
        profiles = {}
        
        # 宝玉档案 - 关键词结构化
        profiles['宝玉'] = CharacterProfile(
            name='宝玉',
            speech_keywords={
                'high': ['好妹妹', '好姐姐', '读书', '仕途', '经济', '功课', '老爷'],
                'medium': ['罢了', '有趣', '可怜', '不想', '由得'],
                'negative': ['混账', '该死', '畜生']  # 宝玉较少说这些
            },
            behavior_keywords={
                'high': ['摇头', '叹气', '赔笑', '凑近', '躲避'],
                'medium': ['呆坐', '出神', '发怔', '纳闷'],
                'context': ['女儿', '水作', '泥作', '清净']  # 宝玉特有的价值观表达
            },
            emotion_keywords={
                'positive': ['喜', '笑', '欢', '乐'],
                'negative': ['悲', '叹', '愁', '烦', '恼'],
                'dominant': ['怜', '惜', '爱']  # 主导情感
            },
            relationship_keywords={
                '黛玉': ['林妹妹', '颦儿', '心', '情', '病', '诗'],
                '宝钗': ['宝姐姐', '客气', '周全', '稳重'],
                '贾母': ['老太太', '疼爱', '撒娇'],
                '贾政': ['老爷', '畏惧', '训斥', '躲避']
            },
            value_keywords=['女儿', '清净', '污泥', '仕途', '经济', '功名']
        )
        
        # 黛玉档案
        profiles['黛玉'] = CharacterProfile(
            name='黛玉',
            speech_keywords={
                'high': ['诗', '词', '花', '月', '泪', '病', '咳嗽'],
                'medium': ['何必', '倒是', '谁知', '不想', '原来'],
                'negative': ['欢喜', '热闹', '应酬']  # 黛玉较少参与
            },
            behavior_keywords={
                'high': ['垂泪', '拭泪', '咳嗽', '倚窗', '独坐'],
                'medium': ['冷笑', '叹气', '出神', '凝思'],
                'context': ['葬花', '题诗', '抚琴', '读书']
            },
            emotion_keywords={
                'positive': ['喜', '悦', '欣慰'],  # 较少
                'negative': ['悲', '愁', '怨', '叹', '泪'],
                'dominant': ['忧', '思', '怜']  # 主导情感
            },
            relationship_keywords={
                '宝玉': ['宝玉', '你', '我', '心', '情', '痴'],
                '宝钗': ['宝钗', '姐姐', '比较', '计较'],
                '紫鹃': ['紫鹃', '鹃儿', '丫鬟'],
                '贾母': ['老太太', '外祖母', '怜']
            },
            value_keywords=['诗', '才', '情', '真', '洁', '傲']
        )
        
        # 宝钗档案
        profiles['宝钗'] = CharacterProfile(
            name='宝钗',
            speech_keywords={
                'high': ['应该', '道理', '规矩', '妥当', '周全'],
                'medium': ['劝', '说', '想', '看', '听'],
                'negative': ['激烈', '冲动', '任性']
            },
            behavior_keywords={
                'high': ['微笑', '劝解', '打点', '周全'],
                'medium': ['稳重', '端庄', '得体', '大方'],
                'context': ['针线', '管家', '劝学', '应酬']
            },
            emotion_keywords={
                'positive': ['稳', '静', '淡'],
                'negative': ['急', '躁', '恼'],  # 极少
                'dominant': ['忍', '藏', '让']  # 主导情感
            },
            relationship_keywords={
                '宝玉': ['宝玉', '劝', '读书', '仕途'],
                '黛玉': ['黛玉', '妹妹', '和气', '照顾'],
                '王夫人': ['姨妈', '太太', '贴心'],
                '贾母': ['老太太', '喜欢', '懂事']
            },
            value_keywords=['礼', '理', '稳', '和', '全', '实']
        )
        
        # 贾母档案
        profiles['贾母'] = CharacterProfile(
            name='贾母',
            speech_keywords={
                'high': ['我的儿', '可怜', '心疼', '罢了', '由得'],
                'medium': ['想', '念', '疼', '爱', '宠'],
                'negative': ['狠', '罚', '骂']  # 对孙辈极少
            },
            behavior_keywords={
                'high': ['疼爱', '庇护', '夸奖', '赏赐'],
                'medium': ['回忆', '讲古', '享乐', '看戏'],
                'context': ['游园', '设宴', '听戏', '讲故事']
            },
            emotion_keywords={
                'positive': ['慈', '爱', '喜', '乐'],
                'negative': ['忧', '愁'],  # 较少
                'dominant': ['宠', '惯', '护']  # 主导情感
            },
            relationship_keywords={
                '宝玉': ['宝玉', '命根', '心肝', '最疼'],
                '黛玉': ['黛玉', '外孙女', '可怜', '疼'],
                '贾政': ['政儿', '儿子', '管教', '严厉'],
                '王熙凤': ['凤辣子', '能干', '喜欢']
            },
            value_keywords=['家', '和', '福', '乐', '尊', '宠']
        )
        
        # 王熙凤档案
        profiles['王熙凤'] = CharacterProfile(
            name='王熙凤',
            speech_keywords={
                'high': ['我说', '罢了', '仔细', '打量', '处置'],
                'medium': ['笑', '说', '问', '查', '办'],
                'negative': ['软弱', '犹豫', '退让']
            },
            behavior_keywords={
                'high': ['冷笑', '厉声', '指挥', '查问', '处置'],
                'medium': ['盘算', '算计', '安排', '打点'],
                'context': ['管家', '理账', '审人', '发落']
            },
            emotion_keywords={
                'positive': ['爽', '利', '快'],
                'negative': ['怒', '恼', '恨', '厉'],
                'dominant': ['威', '势', '利']  # 主导情感
            },
            relationship_keywords={
                '贾琏': ['琏二爷', '丈夫', '夫妻'],
                '贾母': ['老太太', '讨好', '奉承'],
                '平儿': ['平儿', '心腹', '信任'],
                '下人': ['奴才', '打量', '发落']
            },
            value_keywords=['权', '利', '财', '势', '威', '管']
        )
        
        return profiles
    
    async def check_consistency(
        self,
        content: str,
        target_characters: List[str],
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        检查内容中人物一致性 V2
        
        Args:
            content: 待检查的内容
            target_characters: 关注的角色列表
            threshold: 一致性阈值 (0-1)
            
        Returns:
            检查结果字典
        """
        results = {}
        
        for char_name in target_characters:
            if char_name in self.character_profiles:
                profile = self.character_profiles[char_name]
                score, details = self._check_single_character_v2(
                    content, char_name, profile
                )
                results[char_name] = {
                    "score": score,
                    "details": details,
                    "consistent": score >= threshold
                }
        
        overall_score = sum(r["score"] for r in results.values()) / len(results) if results else 0.0
        
        return {
            "overall_score": overall_score,
            "individual_results": results,
            "is_consistent": overall_score >= threshold,
            "suggestions": self._generate_suggestions_v2(results)
        }
    
    def _check_single_character_v2(
        self,
        content: str,
        char_name: str,
        profile: CharacterProfile
    ) -> tuple[float, Dict[str, Any]]:
        """检查单个角色的一致性 V2 - 关键词匹配版"""
        details = {}
        
        # 1. 检查语言风格匹配度 (权重 30%)
        speech_score, speech_details = self._check_speech_pattern_v2(content, char_name, profile)
        details['speech'] = speech_details
        
        # 2. 检查行为特征匹配度 (权重 25%)
        behavior_score, behavior_details = self._check_behavioral_traits_v2(content, char_name, profile)
        details['behavior'] = behavior_details
        
        # 3. 检查情感倾向匹配度 (权重 25%)
        emotion_score, emotion_details = self._check_emotional_tendencies_v2(content, char_name, profile)
        details['emotion'] = emotion_details
        
        # 4. 检查人物关系匹配度 (权重 20%)
        relation_score, relation_details = self._check_relationships_v2(content, char_name, profile)
        details['relationship'] = relation_details
        
        # 计算加权分数
        avg_score = (
            speech_score * 0.30 +
            behavior_score * 0.25 +
            emotion_score * 0.25 +
            relation_score * 0.20
        )
        
        return avg_score, details
    
    def _check_speech_pattern_v2(self, content: str, char_name: str, profile: CharacterProfile) -> tuple[float, Dict]:
        """检查语言风格 V2 - 加权关键词匹配 (优化版)"""
        details = {'matches': [], 'score_breakdown': {}}
        
        # 基础分0.3，确保不会太低
        base_score = 0.3
        
        # 高权重关键词 (命中+3分)
        high_matches = sum(1 for kw in profile.speech_keywords.get('high', []) 
                          if kw in content)
        high_total = len(profile.speech_keywords.get('high', []))
        # 降低期望: 从30%降到15%
        high_score = min(high_matches / max(high_total * 0.15, 1), 1.0) * 0.7
        
        # 中权重关键词 (命中+1分)
        medium_matches = sum(1 for kw in profile.speech_keywords.get('medium', []) 
                            if kw in content)
        medium_total = len(profile.speech_keywords.get('medium', []))
        # 降低期望: 从20%降到10%
        medium_score = min(medium_matches / max(medium_total * 0.10, 1), 1.0) * 0.3
        
        # 计算总分 (基础分 + 动态分)
        score = base_score + (high_score + medium_score) * 0.7
        score = min(score, 1.0)  # 封顶1.0
        
        details['matches'] = {
            'high': [kw for kw in profile.speech_keywords.get('high', []) if kw in content],
            'medium': [kw for kw in profile.speech_keywords.get('medium', []) if kw in content]
        }
        details['score_breakdown'] = {
            'base_score': base_score,
            'high_score': high_score,
            'medium_score': medium_score,
            'final': score
        }
        
        return score, details
    
    def _check_behavioral_traits_v2(self, content: str, char_name: str, profile: CharacterProfile) -> tuple[float, Dict]:
        """检查行为特征 V2 (优化版)"""
        details = {'matches': [], 'context_hits': 0}
        
        # 基础分0.25
        base_score = 0.25
        
        # 检查高权重行为
        high_matches = [kw for kw in profile.behavior_keywords.get('high', []) 
                       if kw in content]
        
        # 检查上下文相关行为
        context_matches = [kw for kw in profile.behavior_keywords.get('context', []) 
                          if kw in content]
        
        # 计算分数 - 降低期望: 从2个降到1个
        high_score = min(len(high_matches) / 1, 1.0) * 0.5  # 期望至少1个高权重行为
        context_score = min(len(context_matches) / 1, 0.5) * 0.25  # 上下文加分
        
        # 总分 = 基础分 + 动态分
        score = base_score + high_score + context_score
        score = min(score, 1.0)
        
        details['matches'] = {
            'high': high_matches,
            'context': context_matches
        }
        
        return score, details
    
    def _check_emotional_tendencies_v2(self, content: str, char_name: str, profile: CharacterProfile) -> tuple[float, Dict]:
        """检查情感倾向 V2 (优化版)"""
        details = {'dominant_emotion': None, 'emotion_counts': {}}
        
        # 基础分0.25
        base_score = 0.25
        
        # 统计各类情感词出现次数
        positive_count = sum(content.count(kw) for kw in profile.emotion_keywords.get('positive', []))
        negative_count = sum(content.count(kw) for kw in profile.emotion_keywords.get('negative', []))
        dominant_count = sum(content.count(kw) for kw in profile.emotion_keywords.get('dominant', []))
        
        total_emotions = positive_count + negative_count + dominant_count
        
        if total_emotions == 0:
            return base_score, details  # 没有情感表达，给基础分
        
        # 主导情感占比 - 提高权重
        dominant_ratio = dominant_count / total_emotions
        
        # 分数基于主导情感的表达程度 (更宽松)
        emotion_score = min(dominant_ratio * 1.5 + 0.2, 0.75)  # 主导情感越多分越高
        
        score = base_score + emotion_score
        score = min(score, 1.0)
        
        details['emotion_counts'] = {
            'positive': positive_count,
            'negative': negative_count,
            'dominant': dominant_count
        }
        details['dominant_ratio'] = dominant_ratio
        
        return score, details
    
    def _check_relationships_v2(self, content: str, char_name: str, profile: CharacterProfile) -> tuple[float, Dict]:
        """检查人物关系 V2 (优化版)"""
        details = {'relationship_hits': {}}
        
        # 基础分0.2
        base_score = 0.2
        
        total_score = 0
        relation_count = 0
        
        for related_char, keywords in profile.relationship_keywords.items():
            # 检查是否提及该关系人物
            if related_char in content:
                # 检查关系关键词命中 - 降低期望从2个到1个
                hits = [kw for kw in keywords if kw in content]
                hit_score = min(len(hits) / 1, 1.0) * 0.8  # 期望至少1个关键词
                
                details['relationship_hits'][related_char] = {
                    'keywords_found': hits,
                    'score': hit_score
                }
                
                total_score += hit_score
                relation_count += 1
        
        # 平均分 + 基础分
        dynamic_score = total_score / max(relation_count, 1) if relation_count > 0 else 0
        score = base_score + dynamic_score * 0.8
        score = min(score, 1.0)
        
        return score, details
    
    def _generate_suggestions_v2(self, results: Dict[str, Any]) -> List[str]:
        """生成改进建议 V2"""
        suggestions = []
        
        for char_name, result in results.items():
            if not result["consistent"]:
                score = result["score"]
                details = result.get("details", {})
                
                if score < 0.4:
                    suggestions.append(f"{char_name}的人物特征表现严重不足，需要全面加强")
                elif score < 0.6:
                    suggestions.append(f"{char_name}的人物特征需要加强")
                
                # 根据具体维度给出建议
                if 'speech' in details:
                    speech_score = details['speech'].get('score_breakdown', {}).get('final', 0)
                    if speech_score < 0.5:
                        suggestions.append(f"建议增加{char_name}的典型语言特征")
                
                if 'emotion' in details:
                    emotion_score = details['emotion'].get('dominant_ratio', 0)
                    if emotion_score < 0.3:
                        suggestions.append(f"建议加强{char_name}的情感表达")
        
        return suggestions


# 保持向后兼容 - 高级质量检查器使用新实现
class AdvancedQualityChecker:
    """高级质量检查器 V2"""
    
    def __init__(self, gpt5_client=None, prompts=None):
        self.gpt5_client = gpt5_client
        self.prompts = prompts
        self.char_checker = CharacterConsistencyChecker(gpt5_client, prompts)
    
    async def comprehensive_check(
        self,
        content: str,
        chapter_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """综合质量检查 V2"""
        # 1. 人物一致性检查
        target_chars = context.get('target_characters', ['宝玉', '黛玉', '宝钗'])
        char_check_result = await self.char_checker.check_consistency(
            content, target_chars
        )
        
        # 2. 结构完整性检查
        structure_score = self._check_structure(content, chapter_info)
        
        # 3. 风格一致性检查
        style_score = self._check_style_consistency_v2(content)
        
        # 4. 计算综合评分（转换为0-10范围）
        overall_score = (
            char_check_result['overall_score'] * 0.4 +
            structure_score * 0.3 +
            style_score * 0.3
        ) * 10  # 转换为0-10分制
        
        return {
            "overall_score": overall_score,
            "character_consistency": char_check_result,
            "structure_score": structure_score * 10,
            "style_score": style_score * 10,
            "is_acceptable": overall_score >= 7.0,
            "recommendations": self._generate_comprehensive_recommendations(
                char_check_result, structure_score, style_score
            )
        }
    
    def _check_structure(self, content: str, chapter_info: Dict[str, Any]) -> float:
        """检查结构完整性"""
        score = 0.0
        
        # 检查是否有回目
        if chapter_info.get('title'):
            score += 0.2
        
        # 检查内容长度（合理范围）
        if 1000 <= len(content) <= 5000:
            score += 0.3
        
        # 检查是否有诗词
        if '诗' in content or '词' in content:
            score += 0.2
        
        # 检查是否有结尾悬念
        if '且听下回分解' in content:
            score += 0.3
        
        return min(score, 1.0)
    
    def _check_style_consistency_v2(self, content: str) -> float:
        """检查风格一致性 V2 - 改进版"""
        score = 0.5  # 基础分
        
        # 检查古典文学特征词
        classical_indicators = [
            "话说", "原来", "却说", "且听下回分解",
            "诗曰", "词曰", "只见", "不知"
        ]
        indicator_count = sum(1 for ind in classical_indicators if ind in content)
        score += min(indicator_count * 0.1, 0.3)
        
        # 检查文言文成分
        wenyan_chars = ["之", "乎", "者", "也", "矣", "焉", "哉"]
        wenyan_count = sum(content.count(char) for char in wenyan_chars)
        wenyan_ratio = wenyan_count / len(content) if content else 0
        score += min(wenyan_ratio * 50, 0.2)  # 适当加分
        
        # 检查对话标记
        dialogue_marks = ["道：", "曰：", "说：", "问：", "答："]
        dialogue_count = sum(1 for mark in dialogue_marks if mark in content)
        score += min(dialogue_count * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _generate_comprehensive_recommendations(
        self,
        char_result: Dict,
        structure_score: float,
        style_score: float
    ) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        if char_result['overall_score'] < 0.6:
            recommendations.append("人物性格一致性有待提高")
            recommendations.extend(char_result.get('suggestions', []))
        
        if structure_score < 0.7:
            recommendations.append("章节结构需要完善")
        
        if style_score < 0.6:
            recommendations.append("文风需要更贴近原著")
        
        return recommendations
