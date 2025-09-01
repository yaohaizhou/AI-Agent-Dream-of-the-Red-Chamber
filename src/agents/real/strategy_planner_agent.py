#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
续写策略Agent
负责制定红楼梦续写的详细策略和情节规划
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..base import BaseAgent, AgentResult
from ..gpt5_client import get_gpt5_client
from ...config.settings import Settings
from ...prompts.literary_prompts import get_literary_prompts


class StrategyPlannerAgent(BaseAgent):
    """续写策略规划Agent"""

    def __init__(self, settings: Settings):
        super().__init__("续写策略Agent", {"task": "情节策略规划"})
        self.settings = settings
        self.gpt5_client = get_gpt5_client(settings)
        self.prompts = get_literary_prompts()

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """处理续写策略规划"""
        self.update_status("planning")

        try:
            user_ending = input_data.get("ending", "")
            knowledge_base = input_data.get("knowledge_base", {})

            # 验证用户结局与原著的兼容性
            compatibility_check = await self._check_compatibility(user_ending)

            if not compatibility_check["compatible"]:
                return AgentResult(
                    success=False,
                    data={"compatibility_issue": compatibility_check},
                    message=f"用户结局与原著存在冲突: {compatibility_check['reason']}"
                )

            # 生成续写策略
            strategy = await self._generate_strategy(user_ending, knowledge_base)

            # 设计40回情节大纲
            plot_outline = await self._design_plot_outline(strategy, user_ending)

            # 整合策略结果
            strategy_result = {
                "user_ending": user_ending,
                "compatibility_check": compatibility_check,
                "overall_strategy": strategy,
                "plot_outline": plot_outline,
                "character_arcs": self._design_character_arcs(strategy),
                "theme_development": self._design_theme_development(strategy),
                "literary_devices": self._design_literary_devices(strategy)
            }

            self.update_status("completed")

            return AgentResult(
                success=True,
                data=strategy_result,
                message="续写策略规划完成"
            )

        except Exception as e:
            self.update_status("error")
            return self.handle_error(e)

    async def _check_compatibility(self, user_ending: str) -> Dict[str, Any]:
        """检查用户结局与原著的兼容性"""
        try:
            # 分析用户结局的关键元素
            ending_analysis = self._analyze_user_ending(user_ending)

            # 检查与原著人物性格的冲突
            character_conflicts = self._check_character_conflicts(ending_analysis)

            # 检查与原著主题的冲突
            theme_conflicts = self._check_theme_conflicts(ending_analysis)

            # 评估整体兼容性
            compatibility_score = self._calculate_compatibility_score(
                character_conflicts, theme_conflicts
            )

            return {
                "compatible": compatibility_score >= 0.7,
                "compatibility_score": compatibility_score,
                "character_conflicts": character_conflicts,
                "theme_conflicts": theme_conflicts,
                "reason": self._generate_compatibility_reason(
                    compatibility_score, character_conflicts, theme_conflicts
                )
            }

        except Exception as e:
            return {
                "compatible": True,  # 默认兼容，避免阻断流程
                "compatibility_score": 0.8,
                "error": str(e)
            }

    def _analyze_user_ending(self, user_ending: str) -> Dict[str, Any]:
        """分析用户结局的关键元素"""
        analysis = {
            "main_characters": [],
            "key_events": [],
            "emotional_tone": "neutral",
            "social_outcome": "unchanged",
            "philosophical_theme": "none"
        }

        # 提取主要人物
        characters = ["宝玉", "黛玉", "宝钗", "贾母", "王夫人"]
        for char in characters:
            if char in user_ending:
                analysis["main_characters"].append(char)

        # 分析情感基调
        if any(word in user_ending for word in ["团圆", "幸福", "美满"]):
            analysis["emotional_tone"] = "positive"
        elif any(word in user_ending for word in ["悲剧", "分离", "痛苦"]):
            analysis["emotional_tone"] = "negative"

        # 分析社会结局
        if any(word in user_ending for word in ["复兴", "兴旺", "繁荣"]):
            analysis["social_outcome"] = "positive"
        elif any(word in user_ending for word in ["败落", "衰败", "没落"]):
            analysis["social_outcome"] = "negative"

        return analysis

    def _check_character_conflicts(self, ending_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查人物性格冲突"""
        conflicts = []

        # 宝玉性格冲突检查
        if "宝玉" in ending_analysis["main_characters"]:
            if any(word in ending_analysis.get("user_ending", "") for word in ["皇帝", "权臣", "富商"]):
                conflicts.append({
                    "character": "贾宝玉",
                    "conflict_type": "personality",
                    "description": "宝玉'白玉为堂金作马'的性格与追求权力财富相冲突",
                    "severity": "high"
                })

        # 黛玉性格冲突检查
        if "黛玉" in ending_analysis["main_characters"]:
            if any(word in ending_analysis.get("user_ending", "") for word in ["世故", "圆滑", "适应"]):
                conflicts.append({
                    "character": "林黛玉",
                    "conflict_type": "personality",
                    "description": "黛玉清高孤傲的性格与世故圆滑相冲突",
                    "severity": "medium"
                })

        return conflicts

    def _check_theme_conflicts(self, ending_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查主题冲突"""
        conflicts = []

        user_ending = ending_analysis.get("user_ending", "")

        # 检查与"落了片白茫茫大地真干净"主题的冲突
        if "皆大欢喜" in user_ending and "白茫茫大地" in user_ending:
            conflicts.append({
                "theme": "人生无常",
                "conflict_type": "philosophical",
                "description": "红楼梦的核心哲理与过于圆满的结局相冲突",
                "severity": "medium"
            })

        return conflicts

    def _calculate_compatibility_score(self, character_conflicts: List, theme_conflicts: List) -> float:
        """计算兼容性分数"""
        base_score = 1.0

        # 人物冲突扣分
        for conflict in character_conflicts:
            if conflict["severity"] == "high":
                base_score -= 0.3
            elif conflict["severity"] == "medium":
                base_score -= 0.15

        # 主题冲突扣分
        for conflict in theme_conflicts:
            if conflict["severity"] == "high":
                base_score -= 0.25
            elif conflict["severity"] == "medium":
                base_score -= 0.1

        return max(0.0, min(1.0, base_score))

    def _generate_compatibility_reason(self, score: float, char_conflicts: List, theme_conflicts: List) -> str:
        """生成兼容性原因说明"""
        if score >= 0.8:
            return "结局与原著高度兼容，可以放心续写"
        elif score >= 0.6:
            return "结局基本兼容，但存在一些性格或主题冲突，建议适当调整"
        else:
            reasons = []
            for conflict in char_conflicts + theme_conflicts:
                reasons.append(conflict["description"])
            return f"结局与原著存在明显冲突: {'; '.join(reasons)}"

    async def _generate_strategy(self, user_ending: str, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """生成续写策略"""
        try:
            # 使用GPT-5生成策略
            system_msg, user_prompt = self.prompts.create_custom_prompt(
                "strategy_planner",
                {"ending": user_ending}
            )

            response = await self.gpt5_client.generate_with_retry(
                prompt=user_prompt,
                system_message=system_msg,
                temperature=0.7,
                max_tokens=4000
            )

            if response["success"]:
                return self._parse_strategy_response(response["content"])
            else:
                return self._fallback_strategy(user_ending)

        except Exception as e:
            print(f"生成策略失败: {e}")
            return self._fallback_strategy(user_ending)

    def _parse_strategy_response(self, response_content: str) -> Dict[str, Any]:
        """解析策略响应"""
        # 这里应该解析GPT-5返回的结构化策略
        # 暂时返回模拟结果
        return {
            "overall_approach": "渐进式发展，突出人物内心冲突",
            "key_themes": ["爱情的考验", "家族的命运", "个人的觉醒"],
            "narrative_style": "第三人称全知视角，详略得当",
            "emotional_arc": ["期待", "冲突", "高潮", "化解"]
        }

    def _fallback_strategy(self, user_ending: str) -> Dict[str, Any]:
        """备用策略生成"""
        return {
            "overall_approach": "尊重原著精神，适度发展用户结局",
            "key_themes": ["爱情", "命运", "家族", "觉醒"],
            "narrative_style": "古典小说风格",
            "emotional_arc": ["铺垫", "发展", "高潮", "结局"]
        }

    async def _design_plot_outline(self, strategy: Dict[str, Any], user_ending: str) -> List[Dict[str, Any]]:
        """设计40回情节大纲"""
        plot_outline = []

        # 按照阶段划分情节
        phases = [
            {"name": "前期铺垫", "chapters": range(81, 91), "focus": "爱情发展"},
            {"name": "中期冲突", "chapters": range(91, 101), "focus": "考验与磨难"},
            {"name": "后期高潮", "chapters": range(101, 111), "focus": "爱情圆满"},
            {"name": "大结局", "chapters": range(111, 121), "focus": "幸福美满"}
        ]

        chapter_num = 81
        for phase in phases:
            for chapter in phase["chapters"]:
                plot_outline.append({
                    "chapter_num": chapter,
                    "title": f"第{chapter}回 (模拟标题)",
                    "phase": phase["name"],
                    "focus": phase["focus"],
                    "key_events": self._generate_chapter_events(chapter, phase["focus"], user_ending),
                    "character_development": self._generate_character_development(chapter, phase["focus"]),
                    "themes": self._generate_chapter_themes(chapter, phase["focus"]),
                    "word_count_estimate": 2500
                })

        return plot_outline

    def _generate_chapter_events(self, chapter_num: int, focus: str, user_ending: str) -> List[str]:
        """生成章节关键事件"""
        # 根据章节和焦点生成相应的事件
        if focus == "爱情发展":
            return ["宝黛爱情加深", "家庭琐事", "诗词唱和"]
        elif focus == "考验与磨难":
            return ["外部压力", "内心冲突", "误会产生"]
        elif focus == "爱情圆满":
            return ["困难克服", "真相大白", "感情升华"]
        else:  # 大结局
            return ["最终团圆", "家族复兴", "人生感悟"]

    def _generate_character_development(self, chapter_num: int, focus: str) -> Dict[str, str]:
        """生成人物发展"""
        developments = {
            "宝玉": "性格发展描述",
            "黛玉": "情感变化描述",
            "宝钗": "处境变化描述"
        }
        return developments

    def _generate_chapter_themes(self, chapter_num: int, focus: str) -> List[str]:
        """生成章节主题"""
        return ["爱情", "命运", "觉醒"]

    def _design_character_arcs(self, strategy: Dict[str, Any]) -> Dict[str, List[str]]:
        """设计人物成长弧线"""
        return {
            "贾宝玉": ["纯真少年", "叛逆青年", "觉醒者", "精神解脱"],
            "林黛玉": ["聪慧少女", "多愁佳人", "坚守理想", "灵魂升华"],
            "薛宝钗": ["贤惠小姐", "世故妇人", "适应社会", "智慧人生"]
        }

    def _design_theme_development(self, strategy: Dict[str, Any]) -> Dict[str, List[str]]:
        """设计主题发展"""
        return {
            "爱情": ["纯真", "考验", "升华", "永恒"],
            "家族": ["繁荣", "危机", "转折", "复兴"],
            "个人": ["迷茫", "觉醒", "挣扎", "解脱"]
        }

    def _design_literary_devices(self, strategy: Dict[str, Any]) -> Dict[str, List[str]]:
        """设计文学手法"""
        return {
            "诗词": ["五言绝句", "七言律诗", "词牌名"],
            "对联": ["楹联", "集句", "即景联"],
            "象征": ["白玉", "绛珠草", "金玉良缘"],
            "意象": ["芭蕉", "桃花", "白雪"]
        }
