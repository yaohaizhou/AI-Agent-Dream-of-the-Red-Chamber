#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人物一致性检查模块
确保续写内容中人物行为、语言、思想符合原著设定
"""

import asyncio
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CharacterProfile:
    """人物档案"""
    name: str
    personality: str  # 性格特征
    speech_pattern: str  # 语言习惯
    behavioral_traits: List[str]  # 行为特征
    relationships: Dict[str, str]  # 与其他角色的关系
    core_values: List[str]  # 核心价值观
    emotional_tendencies: List[str]  # 情感倾向


class CharacterConsistencyChecker:
    """人物一致性检查器"""
    
    def __init__(self, gpt5_client, prompts):
        self.gpt5_client = gpt5_client
        self.prompts = prompts
        self.character_profiles = self._load_character_profiles()
    
    def _load_character_profiles(self) -> Dict[str, CharacterProfile]:
        """加载人物档案"""
        profiles = {}
        
        # 宝玉档案
        profiles['宝玉'] = CharacterProfile(
            name='宝玉',
            personality='敏感多情，厌恶仕途经济，尊重女性，富有同情心',
            speech_pattern='语气温和，常用"好妹妹"等亲昵称呼，反对功名利禄',
            behavioral_traits=[
                '喜欢亲近女性，厌恶男性应酬',
                '关注他人感受，体贴入微',
                '对诗词歌赋有兴趣',
                '逃避严父管教'
            ],
            relationships={
                '黛玉': '深爱，心灵相通',
                '宝钗': '敬重但保持距离',
                '贾母': '深受宠爱',
                '贾政': '畏惧但内心反抗'
            },
            core_values=['真情至上', '反对功名', '尊重个性'],
            emotional_tendencies=['多愁善感', '喜怒形于色']
        )
        
        # 黛玉档案
        profiles['黛玉'] = CharacterProfile(
            name='黛玉',
            personality='才华横溢，多愁善感，敏感细腻，孤高自许',
            speech_pattern='说话尖刻但有理，常用反讽，心思细密',
            behavioral_traits=[
                '经常独自垂泪',
                '喜欢诗词创作',
                '身体虚弱，易生病',
                '心思敏感，容易多疑'
            ],
            relationships={
                '宝玉': '深爱，心灵相通，多疑多虑',
                '宝钗': '暗中比较，略有嫉妒',
                '贾母': '受宠但自卑',
                '紫鹃': '主仆情深'
            },
            core_values=['真情至上', '才情并重', '独立自尊'],
            emotional_tendencies=['多愁善感', '情绪波动大']
        )
        
        # 宝钗档案
        profiles['宝钗'] = CharacterProfile(
            name='宝钗',
            personality='端庄贤惠，世故圆通，识大体，稳重内敛',
            speech_pattern='说话委婉得体，善于劝导，少有激烈言辞',
            behavioral_traits=[
                '善于处理人际关系',
                '注重实用，不尚虚华',
                '关心家族利益',
                '善于自我调节'
            ],
            relationships={
                '宝玉': '敬重，有意无意引导',
                '黛玉': '表面和善，内心竞争',
                '贾母': '得体周到',
                '湘云': '照顾体贴'
            },
            core_values=['实用理性', '家族和谐', '个人修养'],
            emotional_tendencies=['内敛克制', '理性调节']
        )
        
        # 贾母档案
        profiles['贾母'] = CharacterProfile(
            name='贾母',
            personality='慈祥和蔼，家族权威，疼爱孙辈，精明老练',
            speech_pattern='慈爱中带威严，常忆往昔，关爱后辈',
            behavioral_traits=[
                '疼爱宝玉黛玉',
                '维护家族体面',
                '享受生活乐趣',
                '处事经验丰富'
            ],
            relationships={
                '宝玉': '最疼爱的孙子',
                '黛玉': '外孙女，怜其身世',
                '贾政': '儿子，权威地位',
                '王夫人': '儿媳，信任有加'
            },
            core_values=['家族和睦', '孙辈幸福', '传统秩序'],
            emotional_tendencies=['慈爱宽容', '怀旧念旧']
        )
        
        # 王熙凤档案
        profiles['王熙凤'] = CharacterProfile(
            name='王熙凤',
            personality='精明能干，权势欲强，口才出众，心机深沉',
            speech_pattern='说话爽快，善于算计，常用威胁暗示',
            behavioral_traits=[
                '善于理财',
                '手段强硬',
                '追求权力',
                '表面热情实则算计'
            ],
            relationships={
                '贾琏': '夫妻但貌合神离',
                '贾母': '讨好以巩固地位',
                '平儿': '既依赖又防备',
                '下人': '严厉管理'
            },
            core_values=['权力地位', '财富积累', '个人利益'],
            emotional_tendencies=['强势主导', '利益至上']
        )
        
        return profiles
    
    async def check_consistency(
        self,
        content: str,
        target_characters: List[str],
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        检查内容中人物一致性
        
        Args:
            content: 待检查的内容
            target_characters: 关注的角色列表
            threshold: 一致性阈值
            
        Returns:
            检查结果字典
        """
        results = {}
        
        for char_name in target_characters:
            if char_name in self.character_profiles:
                profile = self.character_profiles[char_name]
                score, issues = await self._check_single_character(
                    content, char_name, profile
                )
                results[char_name] = {
                    "score": score,
                    "issues": issues,
                    "consistent": score >= threshold
                }
        
        overall_score = sum(r["score"] for r in results.values()) / len(results) if results else 0.0
        
        return {
            "overall_score": overall_score,
            "individual_results": results,
            "is_consistent": overall_score >= threshold,
            "suggestions": self._generate_suggestions(results)
        }
    
    async def _check_single_character(
        self,
        content: str,
        char_name: str,
        profile: CharacterProfile
    ) -> tuple[float, List[str]]:
        """检查单个角色的一致性"""
        issues = []
        
        # 1. 检查语言风格匹配度
        speech_score, speech_issues = self._check_speech_pattern(content, char_name, profile)
        issues.extend(speech_issues)
        
        # 2. 检查行为特征匹配度
        behavior_score, behavior_issues = self._check_behavioral_traits(content, char_name, profile)
        issues.extend(behavior_issues)
        
        # 3. 检查情感倾向匹配度
        emotion_score, emotion_issues = self._check_emotional_tendencies(content, char_name, profile)
        issues.extend(emotion_issues)
        
        # 4. 检查关系表现
        relation_score, relation_issues = self._check_relationships(content, char_name, profile)
        issues.extend(relation_issues)
        
        # 计算平均分数
        avg_score = (speech_score + behavior_score + emotion_score + relation_score) / 4.0
        
        return avg_score, issues
    
    def _check_speech_pattern(self, content: str, char_name: str, profile: CharacterProfile) -> tuple[float, List[str]]:
        """检查语言风格"""
        issues = []
        
        # 检查是否符合说话习惯
        pattern_match = 0
        total_patterns = len(profile.speech_pattern.split(','))
        
        for pattern in profile.speech_pattern.split(','):
            pattern = pattern.strip()
            if pattern.lower() in content.lower():
                pattern_match += 1
        
        score = pattern_match / total_patterns if total_patterns > 0 else 1.0
        
        if score < 0.5:
            issues.append(f"{char_name}的语言风格与原著不符")
        
        return score, issues
    
    def _check_behavioral_traits(self, content: str, char_name: str, profile: CharacterProfile) -> tuple[float, List[str]]:
        """检查行为特征"""
        issues = []
        
        trait_match = 0
        for trait in profile.behavioral_traits:
            if trait in content:
                trait_match += 1
        
        score = trait_match / len(profile.behavioral_traits) if profile.behavioral_traits else 1.0
        
        if score < 0.3:
            issues.append(f"{char_name}的行为特征表现不足")
        
        return score, issues
    
    def _check_emotional_tendencies(self, content: str, char_name: str, profile: CharacterProfile) -> tuple[float, List[str]]:
        """检查情感倾向"""
        issues = []
        
        emotion_match = 0
        for tendency in profile.emotional_tendencies:
            # 检查相关情感表达
            emotion_keywords = self._get_emotion_keywords(tendency)
            for keyword in emotion_keywords:
                if keyword in content:
                    emotion_match += 1
                    break
        
        score = emotion_match / len(profile.emotional_tendencies) if profile.emotional_tendencies else 1.0
        
        if score < 0.3:
            issues.append(f"{char_name}的情感倾向表现不足")
        
        return score, issues
    
    def _get_emotion_keywords(self, tendency: str) -> List[str]:
        """获取情感关键词"""
        keywords_map = {
            '多愁善感': ['愁', '悲', '哀', '叹', '泪', '忧'],
            '情绪波动大': ['喜', '怒', '悲', '欢', '变', '忽'],
            '内敛克制': ['默', '静', '忍', '藏', '不语', '淡然'],
            '理性调节': ['理', '智', '冷静', '分析', '思考'],
            '慈爱宽容': ['慈', '爱', '怜', '护', '疼', '温和'],
            '怀旧念旧': ['忆', '昔', '往', '从前', '当年'],
            '强势主导': ['令', '命', '决', '主', '掌', '控'],
            '利益至上': ['利', '益', '钱', '财', '得失', '算计'],
            '喜怒形于色': ['笑', '哭', '怒', '恼', '愤', '悦']
        }
        return keywords_map.get(tendency, [])
    
    def _check_relationships(self, content: str, char_name: str, profile: CharacterProfile) -> tuple[float, List[str]]:
        """检查人物关系"""
        issues = []
        
        relation_match = 0
        for related_char, relation_desc in profile.relationships.items():
            # 检查两角色是否同时出现在文本中
            if related_char in content and char_name in content:
                # 检查是否体现了特定关系
                relation_keywords = relation_desc.split(',')
                for keyword in relation_keywords:
                    if keyword.strip() in content:
                        relation_match += 1
                        break
        
        score = relation_match / len(profile.relationships) if profile.relationships else 1.0
        
        if score < 0.2:
            issues.append(f"{char_name}与其他角色的关系表现不足")
        
        return score, issues
    
    def _generate_suggestions(self, results: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        for char_name, result in results.items():
            if not result["consistent"]:
                suggestions.append(f"需要加强{char_name}的人物特征表现")
        
        return suggestions
    
    async def enhance_characterization(
        self,
        content: str,
        target_characters: List[str]
    ) -> str:
        """
        增强人物刻画
        
        Args:
            content: 原始内容
            target_characters: 目标角色列表
            
        Returns:
            增强后的内容
        """
        enhanced_content = content
        
        for char_name in target_characters:
            if char_name in self.character_profiles:
                profile = self.character_profiles[char_name]
                
                # 添加语言特征
                enhanced_content = self._enhance_speech_patterns(enhanced_content, char_name, profile)
                
                # 添加行为特征
                enhanced_content = self._enhance_behavioral_traits(enhanced_content, char_name, profile)
        
        return enhanced_content
    
    def _enhance_speech_patterns(self, content: str, char_name: str, profile: CharacterProfile) -> str:
        """增强语言特征"""
        # 如果内容中有人物对话，增强其语言特点
        if char_name in content:
            # 添加语言习惯相关的描述
            speech_elements = profile.speech_pattern.split(',')
            for element in speech_elements[:2]:  # 只取前两个元素避免过度
                element = element.strip()
                if element and element not in content:
                    # 在合适的位置添加体现语言特点的内容
                    content += f"\n（{char_name}此时{element}，众人皆知其性情如此。）"
        
        return content
    
    def _enhance_behavioral_traits(self, content: str, char_name: str, profile: CharacterProfile) -> str:
        """增强行为特征"""
        for trait in profile.behavioral_traits[:2]:  # 只取前两个特征
            if trait not in content:
                # 在内容中适当位置添加行为描述
                content += f"\n（{char_name}素来{trait}，此事亦不例外。）"
        
        return content


class AdvancedQualityChecker:
    """高级质量检查器（整合渐进式生成和人物一致性）"""
    
    def __init__(self, gpt5_client, prompts):
        self.progressive_gen = ProgressiveGenerator(gpt5_client, prompts)
        self.char_checker = CharacterConsistencyChecker(gpt5_client, prompts)
    
    async def comprehensive_check(
        self,
        content: str,
        chapter_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """综合质量检查"""
        # 1. 人物一致性检查
        target_chars = context.get('target_characters', ['宝玉', '黛玉', '宝钗'])
        char_check_result = await self.char_checker.check_consistency(
            content, target_chars
        )
        
        # 2. 结构完整性检查
        structure_score = self._check_structure(content, chapter_info)
        
        # 3. 风格一致性检查
        style_score = await self._check_style_consistency(content, context)
        
        # 4. 计算综合评分
        overall_score = (
            char_check_result['overall_score'] * 0.4 +
            structure_score * 0.3 +
            style_score * 0.3
        )
        
        return {
            "overall_score": overall_score,
            "character_consistency": char_check_result,
            "structure_score": structure_score,
            "style_score": style_score,
            "is_acceptable": overall_score >= 8.0,
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
    
    async def _check_style_consistency(self, content: str, context: Dict[str, Any]) -> float:
        """检查风格一致性"""
        prompt = f"""
请评估以下《红楼梦》续写片段的风格一致性：

内容：
{content[:2000]}

评估标准：
1. 语言风格是否符合古典白话小说
2. 人物对话是否符合身份
3. 叙述方式是否符合原著特点
4. 用词是否典雅，符合时代背景

请给出1-10分的评分，并简要说明理由。
"""
        
        response = await self.progressive_gen.gpt5_client.generate_with_retry(
            prompt=prompt,
            system_message="你是《红楼梦》文学风格评估专家。",
            temperature=0.3,
            max_tokens=500
        )
        
        if response["success"]:
            try:
                # 从响应中提取分数
                text = response["content"]
                # 寻找数字评分
                import re
                numbers = re.findall(r'\d+\.?\d*', text)
                if numbers:
                    score = float(numbers[0])
                    return min(score / 10.0, 1.0)  # 转换为0-1范围
            except:
                pass
        
        return 0.7  # 默认分数
    
    def _generate_comprehensive_recommendations(
        self,
        char_result: Dict,
        structure_score: float,
        style_score: float
    ) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        if char_result['overall_score'] < 0.8:
            recommendations.append("人物性格一致性有待提高")
        
        if structure_score < 0.8:
            recommendations.append("章节结构需要完善")
        
        if style_score < 0.8:
            recommendations.append("文风需要更贴近原著")
        
        return recommendations
