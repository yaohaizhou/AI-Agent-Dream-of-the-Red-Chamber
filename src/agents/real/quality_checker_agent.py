#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量校验Agent
负责评估续写内容的质量和文学价值
"""

import asyncio
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import Counter

from ..base import BaseAgent, AgentResult
from ..gpt5_client import get_gpt5_client
from ...config.settings import Settings
from ...prompts.literary_prompts import get_literary_prompts


class QualityCheckerAgent(BaseAgent):
    """质量校验Agent"""

    def __init__(self, settings: Settings):
        super().__init__("质量校验Agent", {"task": "内容质量评估"})
        self.settings = settings
        self.gpt5_client = get_gpt5_client(settings)
        self.prompts = get_literary_prompts()

        # 质量评估标准
        self.quality_criteria = self._load_quality_criteria()

    def _load_quality_criteria(self) -> Dict[str, Any]:
        """加载质量评估标准"""
        return {
            "style_consistency": {
                "weight": 0.3,
                "indicators": [
                    "古典小说语言特征",
                    "文辞雅致程度",
                    "修辞手法运用",
                    "叙事视角一致性"
                ]
            },
            "character_accuracy": {
                "weight": 0.3,
                "indicators": [
                    "人物性格把握",
                    "行为逻辑合理性",
                    "对话个性化程度",
                    "人物发展连贯性"
                ]
            },
            "plot_reasonability": {
                "weight": 0.25,
                "indicators": [
                    "情节发展逻辑",
                    "与原著衔接自然度",
                    "故事张力把握",
                    "结局合理性"
                ]
            },
            "literary_quality": {
                "weight": 0.15,
                "indicators": [
                    "意象运用丰富度",
                    "情感表达深度",
                    "艺术手法多样性",
                    "审美价值"
                ]
            }
        }

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """评估内容质量"""
        self.update_status("evaluating")

        try:
            content_to_evaluate = input_data.get("content", "")
            chapter_info = input_data.get("chapter_info", {})
            context = input_data.get("context", {})

            if not content_to_evaluate:
                return AgentResult(
                    success=False,
                    data=None,
                    message="没有找到需要评估的内容"
                )

            # 执行多维度质量评估
            evaluation_results = await self._perform_comprehensive_evaluation(
                content_to_evaluate, chapter_info, context
            )

            # 计算综合评分
            overall_score = self._calculate_overall_score(evaluation_results)

            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(
                evaluation_results, overall_score
            )

            # 构建评估报告
            evaluation_report = {
                "overall_score": overall_score,
                "dimension_scores": evaluation_results,
                "evaluation_details": self._generate_evaluation_details(evaluation_results),
                "improvement_suggestions": improvement_suggestions,
                "quality_level": self._determine_quality_level(overall_score),
                "timestamp": datetime.now().isoformat(),
                "evaluator": self.name
            }

            # 决定是否通过质量检查
            quality_passed = overall_score >= self.settings.quality.min_score_threshold

            self.update_status("completed")

            return AgentResult(
                success=quality_passed,
                data=evaluation_report,
                message=f"质量评估完成，得分: {overall_score:.1f}/10 ({'通过' if quality_passed else '需要改进'})"
            )

        except Exception as e:
            self.update_status("error")
            return self.handle_error(e)

    async def _perform_comprehensive_evaluation(
        self,
        content: str,
        chapter_info: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """执行综合质量评估"""
        evaluation_tasks = [
            self._evaluate_style_consistency(content, context),
            self._evaluate_character_accuracy(content, context),
            self._evaluate_plot_reasonability(content, chapter_info, context),
            self._evaluate_literary_quality(content, chapter_info)
        ]

        # 并行执行各项评估
        results = await asyncio.gather(*evaluation_tasks)

        return {
            "style_consistency": results[0],
            "character_accuracy": results[1],
            "plot_reasonability": results[2],
            "literary_quality": results[3]
        }

    async def _evaluate_style_consistency(self, content: str, context: Dict[str, Any]) -> float:
        """评估风格一致性"""
        try:
            # 使用GPT-5进行风格评估
            system_msg, user_prompt = self.prompts.create_custom_prompt(
                "quality_checker",
                {
                    "chapter_num": 81,  # 示例章节号
                    "chapter_title": "风格评估章节",
                    "chapter_content": content[:2000]  # 限制内容长度
                }
            )

            response = await self.gpt5_client.generate_with_retry(
                prompt=user_prompt + "\n\n请重点评估语言风格的古典小说特征。",
                system_message=system_msg,
                temperature=0.4,
                max_tokens=1500
            )

            if response["success"]:
                return self._parse_evaluation_score(response["content"], "style_consistency")
            else:
                return self._fallback_style_evaluation(content)

        except Exception as e:
            print(f"风格评估失败: {e}")
            return self._fallback_style_evaluation(content)

    def _fallback_style_evaluation(self, content: str) -> float:
        """备用风格评估方法"""
        score = 5.0  # 基础分数

        # 检查古典文学特征
        classical_indicators = [
            "话说", "原来", "却说", "且听下回分解",
            "诗曰", "词曰", "话说", "只见"
        ]

        indicator_count = sum(1 for indicator in classical_indicators if indicator in content)
        score += min(indicator_count * 0.5, 3.0)

        # 检查文言文成分
        wenyan_indicators = ["之", "乎", "者", "也", "矣", "焉", "哉"]
        wenyan_count = sum(1 for indicator in wenyan_indicators if indicator in content)
        score += min(wenyan_count * 0.2, 1.5)

        return min(score, 10.0)

    async def _evaluate_character_accuracy(self, content: str, context: Dict[str, Any]) -> float:
        """评估人物塑造准确性"""
        try:
            # 获取人物信息
            characters = context.get("characters", {})
            if not characters:
                # 如果没有上下文人物信息，尝试从内容中推断
                characters = self._infer_characters_from_content(content)

            # 检查主要人物的刻画
            score = 5.0  # 基础分数
            evaluated_characters = 0

            for char_name, char_info in characters.items():
                if char_name in content:
                    evaluated_characters += 1
                    
                    # 检查性格特征是否符合
                    personality_traits = char_info.get("性格", "")
                    if personality_traits:
                        trait_matches = self._check_personality_match(content, char_name, personality_traits)
                        score += trait_matches * 0.8  # 性格匹配权重较高

                    # 检查行为逻辑是否符合人物设定
                    behavior_matches = self._check_behavior_consistency(content, char_name, char_info)
                    score += behavior_matches * 0.6

                    # 检查对话风格是否符合人物身份
                    dialogue_matches = self._check_dialogue_consistency(content, char_name, char_info)
                    score += dialogue_matches * 0.7

                    # 检查人物与其他角色的互动是否符合设定
                    relationship_matches = self._check_relationship_consistency(content, char_name, characters)
                    score += relationship_matches * 0.5

            # 如果没有找到任何主要人物，扣分
            if evaluated_characters == 0 and characters:
                score -= 2.0

            return min(max(score, 0.0), 10.0)  # 确保分数在0-10之间

        except Exception as e:
            print(f"人物评估失败: {e}")
            import traceback
            print(f"错误详情:\n{traceback.format_exc()}")
            return 6.0  # 默认中等分数

    def _infer_characters_from_content(self, content: str) -> Dict[str, Dict[str, str]]:
        """
        从内容中推断人物信息
        """
        # 红楼梦主要人物及其典型特征
        known_characters = {
            "贾宝玉": {
                "性格": "纯真善良 叛逆封建 礼教反对者 情感细腻 尊重女性",
                "典型行为": "关心女性 逃避仕途经济 喜欢诗词",
                "语言特点": "温和体贴 对女性尊重 有时叛逆"
            },
            "林黛玉": {
                "性格": "聪慧敏感 多愁善感 才华横溢 个性率真",
                "典型行为": "写诗作词 体弱多病 多疑敏感",
                "语言特点": "机智尖锐 带有诗意 有时尖刻"
            },
            "薛宝钗": {
                "性格": "端庄贤惠 世故圆通 大方得体 识大体",
                "典型行为": "劝导他人 注重礼仪 处事稳重",
                "语言特点": "温和理性 劝导性强 符合礼教"
            },
            "王熙凤": {
                "性格": "精明能干 权势欲强 口才出众 心机深沉",
                "典型行为": "管理家务 施展权术 言语犀利",
                "语言特点": "爽朗直率 带有权威性 机智幽默"
            },
            "贾母": {
                "性格": "慈祥和蔼 家族权威 尊贵威严",
                "典型行为": "疼爱孙辈 决定家族大事",
                "语言特点": "慈祥关爱 威严中有温情"
            }
        }

        # 从内容中检测出现的人物
        detected_characters = {}
        for name, traits in known_characters.items():
            if name in content:
                detected_characters[name] = traits

        return detected_characters

    def _check_personality_match(self, content: str, char_name: str, personality_traits: str) -> float:
        """
        检查人物性格是否与设定匹配 - V2修复版
        返回0-1之间的匹配度
        """
        # 定义核心关键词映射 (从长描述提取关键词)
        keyword_mapping = {
            # 宝玉
            "纯真": ["真", "纯", "痴"],
            "善良": ["善", "怜", "疼", "爱"],
            "叛逆": ["叛逆", "不听", "不愿", "不想"],
            "封建": ["礼教", "规矩", "功名", "仕途"],
            "细腻": ["细", "心", "想", "思"],
            "尊重": ["尊重", "疼", "爱", "怜"],
            # 黛玉
            "聪慧": ["诗", "词", "才"],
            "敏感": ["敏感", "多心", "疑"],
            "多愁": ["愁", "悲", "泪", "叹"],
            "率真": ["真", "直", "说"],
            # 宝钗
            "端庄": ["端庄", "得体", "礼"],
            "贤惠": ["贤", "惠", "劝"],
            "圆通": ["圆", "通", "妥"],
            "大体": ["大体", "全", "周"],
            # 王熙凤
            "精明": ["精", "明", "算"],
            "能干": ["能干", "管", "办"],
            "权术": ["权", "术", "计"],
            # 贾母
            "慈祥": ["慈", "祥", "疼", "爱"],
            "威严": ["威", "严", "命", "令"],
        }
        
        content_lower = content.lower()
        matches = 0
        total_checks = 0
        
        # 检查每个性格词的关键词
        for trait in personality_traits.split():
            keywords = keyword_mapping.get(trait, [trait])
            total_checks += 1
            
            for kw in keywords:
                if kw in content_lower:
                    matches += 1
                    break
        
        return matches / total_checks if total_checks > 0 else 0.5

    def _check_behavior_consistency(self, content: str, char_name: str, char_info: Dict[str, str]) -> float:
        """
        检查人物行为是否与设定一致 - V2修复版
        返回0-1之间的匹配度
        """
        # 定义核心行为关键词映射
        behavior_keywords = {
            # 宝玉
            "关心": ["关心", "疼", "爱", "问", "瞧"],
            "女性": ["妹妹", "姐姐", "女儿", "丫鬟"],
            "逃避": ["逃", "躲", "避", "怕", "烦"],
            "仕途": ["仕途", "功名", "读书", "做官", "老爷"],
            "诗词": ["诗", "词", "曲", "赋", "联"],
            # 黛玉
            "写诗": ["诗", "词", "写", "作", "吟"],
            "体弱": ["病", "弱", "咳", "喘", "药"],
            "多疑": ["疑", "猜", "想", "心"],
            # 宝钗
            "劝导": ["劝", "说", "教", "导"],
            "礼仪": ["礼", "仪", "规", "矩"],
            "稳重": ["稳", "重", "妥", "当"],
            # 王熙凤
            "管理": ["管", "理", "办", "查"],
            "权术": ["权", "术", "计", "谋"],
            "言语": ["说", "话", "言", "语"],
            # 贾母
            "疼爱": ["疼", "爱", "宠", "护", "心肝"],
            "决定": ["定", "决", "命", "令"],
        }
        
        typical_behaviors = char_info.get("典型行为", "")
        if not typical_behaviors:
            return 0.5
        
        content_lower = content.lower()
        matches = 0
        total_checks = 0
        
        # 对每个行为描述提取核心词
        for behavior_desc in typical_behaviors.split():
            total_checks += 1
            found = False
            
            # 查找匹配的关键词
            for key, keywords in behavior_keywords.items():
                if key in behavior_desc:
                    for kw in keywords:
                        if kw in content_lower:
                            matches += 1
                            found = True
                            break
                if found:
                    break
            
            # 如果没找到映射，直接用描述词匹配
            if not found and behavior_desc in content_lower:
                matches += 1
        
        return matches / total_checks if total_checks > 0 else 0.5

    def _check_dialogue_consistency(self, content: str, char_name: str, char_info: Dict[str, str]) -> float:
        """
        检查对话是否符合人物身份 - V2修复版
        返回0-1之间的匹配度
        """
        # 定义语言特点关键词映射
        dialogue_keywords = {
            # 宝玉
            "温和": ["温", "柔", "轻", "慢"],
            "体贴": ["体贴", "心疼", "问", "瞧"],
            "尊重": ["尊重", "不敢", "请"],
            "叛逆": ["叛逆", "不愿", "不想", "偏"],
            # 黛玉
            "机智": ["机智", "尖", "刻", "讽"],
            "诗意": ["诗", "词", "花", "月"],
            "尖刻": ["尖", "刻", "讽", "刺"],
            # 宝钗
            "温和": ["温", "柔", "和"],
            "理性": ["理", "智", "思", "想"],
            "劝导": ["劝", "说", "教"],
            "礼教": ["礼", "教", "规", "矩"],
            # 王熙凤
            "爽朗": ["爽", "快", "直"],
            "权威": ["权", "威", "命", "令"],
            "机智": ["机智", "巧", "妙"],
            # 贾母
            "慈祥": ["慈", "祥", "爱", "疼"],
            "关爱": ["关", "爱", "护", "宠"],
            "温情": ["温", "情", "柔", "暖"],
        }
        
        content_lower = content.lower()
        dialogue_matches = 0
        total_checks = 0

        # 检查语言特点
        language_traits = char_info.get("语言特点", "")
        if language_traits:
            for trait_desc in language_traits.split():
                total_checks += 1
                found = False
                
                # 查找关键词映射
                for key, keywords in dialogue_keywords.items():
                    if key in trait_desc:
                        for kw in keywords:
                            if kw in content_lower:
                                dialogue_matches += 1
                                found = True
                                break
                    if found:
                        break
                
                # 如果没找到映射，直接用描述词
                if not found and trait_desc in content_lower:
                    dialogue_matches += 1

        return dialogue_matches / total_checks if total_checks > 0 else 0.5

    def _check_relationship_consistency(self, content: str, char_name: str, all_characters: Dict[str, Dict[str, str]]) -> float:
        """
        检查人物关系是否符合设定
        返回0-1之间的匹配度
        """
        if char_name not in all_characters:
            return 0.0

        char_info = all_characters[char_name]
        relationship_matches = 0
        total_checks = 0

        # 检查与其他角色的互动是否符合设定
        for other_char, other_info in all_characters.items():
            if char_name != other_char and other_char in content:
                # 检查互动方式是否符合人物设定
                # 这里可以添加更复杂的交互分析逻辑
                relationship_matches += 0.5  # 简单给予一半的匹配度
                total_checks += 1

        return relationship_matches / total_checks if total_checks > 0 else 0.0

    async def _evaluate_plot_reasonability(self, content: str, chapter_info: Dict[str, Any], context: Dict[str, Any]) -> float:
        """评估情节合理性"""
        try:
            score = 5.0  # 基础分数

            # 检查情节发展逻辑
            if self._check_plot_logic(content, chapter_info):
                score += 1.5

            # 检查与前文的衔接
            if self._check_continuity(content, context):
                score += 1.5

            # 检查故事张力
            if self._check_narrative_tension(content):
                score += 1.0

            # 检查结局合理性
            if self._check_ending_reasonability(content, chapter_info):
                score += 1.0

            return min(score, 10.0)

        except Exception as e:
            return 6.0

    def _check_plot_logic(self, content: str, chapter_info: Dict[str, Any]) -> bool:
        """检查情节逻辑"""
        # 检查是否有明显的逻辑矛盾
        contradictions = ["却又", "但是却", "然而却"]
        contradiction_count = sum(1 for contra in contradictions if contra in content)

        return contradiction_count <= 2  # 允许少量转折

    def _check_continuity(self, content: str, context: Dict[str, Any]) -> bool:
        """检查连续性"""
        # 检查是否提到前文的重要元素
        # 这里可以实现更复杂的连续性检查
        return True

    def _check_narrative_tension(self, content: str) -> bool:
        """检查叙事张力"""
        # 检查是否有冲突和转折
        tension_indicators = ["却", "原来", "突然", "不想", "谁知"]
        tension_count = sum(1 for indicator in tension_indicators if indicator in content)

        return tension_count >= 3

    def _check_ending_reasonability(self, content: str, chapter_info: Dict[str, Any]) -> bool:
        """检查结局合理性"""
        # 检查是否有适当的章节结尾
        ending_indicators = ["且听下回分解", "正是", "后事如何", "下回书交代"]
        has_proper_ending = any(indicator in content for indicator in ending_indicators)

        return has_proper_ending

    async def _evaluate_literary_quality(self, content: str, chapter_info: Dict[str, Any]) -> float:
        """评估文学质量"""
        try:
            score = 5.0  # 基础分数

            # 检查修辞手法
            if self._check_rhetorical_devices(content):
                score += 1.0

            # 检查意象运用
            if self._check_imagery_usage(content):
                score += 1.0

            # 检查情感深度
            if self._check_emotional_depth(content):
                score += 1.0

            # 检查艺术表现力
            if self._check_artistic_expression(content):
                score += 1.0

            # 检查语言美感
            if self._check_linguistic_beauty(content):
                score += 0.5

            return min(score, 10.0)

        except Exception as e:
            return 6.0

    def _check_rhetorical_devices(self, content: str) -> bool:
        """检查修辞手法"""
        rhetorical_devices = ["比喻", "拟人", "对仗", "排比", "反问"]
        # 这里可以实现更精确的修辞手法识别
        return len(content) > 1000  # 简单检查：内容足够长就有一定修辞

    def _check_imagery_usage(self, content: str) -> bool:
        """检查意象运用"""
        imagery_indicators = ["月下", "花开", "风吹", "雨打", "雪飘"]
        imagery_count = sum(1 for indicator in imagery_indicators if indicator in content)
        return imagery_count >= 2

    def _check_emotional_depth(self, content: str) -> bool:
        """检查情感深度"""
        emotion_indicators = ["伤感", "喜悦", "悲伤", "思念", "无奈"]
        emotion_count = sum(1 for indicator in emotion_indicators if indicator in content)
        return emotion_count >= 1

    def _check_artistic_expression(self, content: str) -> bool:
        """检查艺术表现力"""
        artistic_indicators = ["诗曰", "词曰", "有诗为证", "正是"]
        artistic_count = sum(1 for indicator in artistic_indicators if indicator in content)
        return artistic_count >= 1

    def _check_linguistic_beauty(self, content: str) -> bool:
        """检查语言美感"""
        # 检查文言文成分比例
        wenyan_chars = ["之", "乎", "者", "也", "矣", "焉", "哉"]
        wenyan_count = sum(1 for char in wenyan_chars if char in content)
        wenyan_ratio = wenyan_count / len(content) if content else 0

        return wenyan_ratio >= 0.002  # 文言文成分比例不低于0.2%

    def _parse_evaluation_score(self, evaluation_text: str, dimension: str) -> float:
        """解析评估分数"""
        try:
            # 从评估文本中提取分数
            # 这里应该解析GPT-5返回的评分
            # 暂时返回模拟分数
            base_score = 7.0

            # 根据文本内容调整分数
            if "优秀" in evaluation_text or "很好" in evaluation_text:
                base_score += 1.5
            elif "良好" in evaluation_text or "不错" in evaluation_text:
                base_score += 0.5
            elif "一般" in evaluation_text:
                base_score -= 0.5
            elif "不足" in evaluation_text or "需要改进" in evaluation_text:
                base_score -= 1.5

            return max(0.0, min(10.0, base_score))

        except Exception:
            return 6.0  # 默认中等分数

    def _calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """计算综合评分"""
        overall_score = 0.0

        for dimension, score in dimension_scores.items():
            weight = self.quality_criteria[dimension]["weight"]
            overall_score += score * weight

        return round(overall_score, 1)

    def _generate_evaluation_details(self, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """生成评估详情"""
        details = {}

        for dimension, score in dimension_scores.items():
            criteria = self.quality_criteria[dimension]
            indicators = criteria["indicators"]

            details[dimension] = {
                "score": score,
                "weight": criteria["weight"],
                "indicators": indicators,
                "level": self._score_to_level(score)
            }

        return details

    def _score_to_level(self, score: float) -> str:
        """分数转换为等级"""
        if score >= 9.0:
            return "优秀"
        elif score >= 8.0:
            return "良好"
        elif score >= 7.0:
            return "合格"
        elif score >= 5.0:
            return "待改进"
        else:
            return "需要重写"

    def _generate_improvement_suggestions(self, dimension_scores: Dict[str, float], overall_score: float) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 根据各维度分数生成针对性建议
        for dimension, score in dimension_scores.items():
            if score < 7.0:
                suggestions.extend(self._get_dimension_suggestions(dimension, score))

        # 整体建议
        if overall_score < 7.0:
            suggestions.append("建议重新构思章节结构，提升故事的艺术张力")
        elif overall_score < 8.0:
            suggestions.append("建议加强人物心理描写，深化情感表达")
        else:
            suggestions.append("整体质量良好，可以进一步打磨语言细节")

        return suggestions

    def _get_dimension_suggestions(self, dimension: str, score: float) -> List[str]:
        """获取维度特定建议"""
        suggestions_map = {
            "style_consistency": [
                "建议多使用古典小说惯用语，如'话说'、'原来'等",
                "注意文言文与白话文的比例平衡",
                "加强修辞手法的运用，如比喻、拟人等"
            ],
            "character_accuracy": [
                "深入分析人物性格特征，避免行为逻辑矛盾",
                "注意人物对话的个性化，避免千人一面",
                "关注人物成长弧线的发展合理性"
            ],
            "plot_reasonability": [
                "检查情节发展逻辑，避免突兀转折",
                "加强与前文的衔接和照应",
                "注意故事节奏的把握"
            ],
            "literary_quality": [
                "增加意象描写，提升艺术表现力",
                "深化情感表达，避免表面化",
                "尝试融入诗词等古典文学元素"
            ]
        }

        return suggestions_map.get(dimension, ["建议加强该维度表现"])

    def _determine_quality_level(self, overall_score: float) -> str:
        """确定质量等级"""
        if overall_score >= 9.0:
            return "大师级"
        elif overall_score >= 8.0:
            return "优秀"
        elif overall_score >= 7.0:
            return "良好"
        elif overall_score >= 6.0:
            return "合格"
        elif overall_score >= 5.0:
            return "待改进"
        else:
            return "需要重写"
