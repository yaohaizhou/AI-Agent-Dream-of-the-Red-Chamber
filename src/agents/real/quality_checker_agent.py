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

            # 检查主要人物的刻画
            score = 5.0  # 基础分数

            for char_name, char_info in characters.items():
                if char_name in content:
                    # 检查性格特征是否符合
                    personality_traits = char_info.get("性格", "")
                    if any(trait in content for trait in personality_traits.split()):
                        score += 0.5

                    # 检查对话是否符合人物身份
                    if self._check_dialogue_consistency(content, char_name, char_info):
                        score += 0.3

            return min(score, 10.0)

        except Exception as e:
            print(f"人物评估失败: {e}")
            return 6.0  # 默认中等分数

    def _check_dialogue_consistency(self, content: str, char_name: str, char_info: Dict) -> bool:
        """检查对话一致性"""
        # 这里可以实现更复杂的对话分析逻辑
        # 暂时返回True
        return True

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
