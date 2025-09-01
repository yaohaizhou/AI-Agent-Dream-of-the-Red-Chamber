#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于Google ADK的红楼梦续写Agent系统
使用Google ADK框架重构现有的Agent架构
"""

import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.tools import google_search

from ..config.settings import Settings
from ..prompts.literary_prompts import get_literary_prompts


class ChapterAnalysisTool(HongLouMengTool):
    """章节分析工具"""
    
    def __init__(self):
        super().__init__(
            name="chapter_analysis",
            description="分析红楼梦章节内容，提取人物关系和情节要素"
        )
    
    async def execute(self, text: str) -> Dict[str, Any]:
        """执行章节分析"""
        try:
            # 使用jieba进行中文分词
            import jieba
            import jieba.posseg as pseg
            
            # 提取人物名称
            characters = self._extract_characters(text)
            
            # 提取关键事件
            events = self._extract_events(text)
            
            # 分析情感色彩
            sentiment = self._analyze_sentiment(text)
            
            return {
                "characters": characters,
                "events": events,
                "sentiment": sentiment,
                "word_count": len(text),
                "chapter_themes": self._extract_themes(text)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_characters(self, text: str) -> List[str]:
        """提取人物名称"""
        # 红楼梦主要人物名单
        main_characters = [
            "贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母",
            "贾政", "王夫人", "贾赦", "邢夫人", "贾琏",
            "史湘云", "妙玉", "贾迎春", "贾探春", "贾惜春",
            "李纨", "秦可卿", "贾蓉", "贾珍", "尤氏"
        ]
        
        found_characters = []
        for char in main_characters:
            if char in text:
                found_characters.append(char)
        
        return found_characters
    
    def _extract_events(self, text: str) -> List[str]:
        """提取关键事件"""
        # 简化的事件提取逻辑
        event_keywords = ["说道", "笑道", "哭了", "来了", "去了", "见了"]
        events = []
        
        sentences = text.split('。')
        for sentence in sentences:
            for keyword in event_keywords:
                if keyword in sentence and len(sentence) > 10:
                    events.append(sentence.strip())
                    break
        
        return events[:5]  # 返回前5个事件
    
    def _analyze_sentiment(self, text: str) -> str:
        """分析情感色彩"""
        positive_words = ["喜", "乐", "笑", "欢", "美", "好"]
        negative_words = ["悲", "哭", "愁", "恨", "苦", "痛"]
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            return "积极"
        elif neg_count > pos_count:
            return "消极"
        else:
            return "中性"
    
    def _extract_themes(self, text: str) -> List[str]:
        """提取主题"""
        themes = []
        theme_keywords = {
            "爱情": ["爱", "情", "心", "意"],
            "家族": ["家", "族", "府", "门"],
            "命运": ["命", "运", "缘", "分"],
            "社会": ["官", "仕", "朝", "廷"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text for keyword in keywords):
                themes.append(theme)
        
        return themes


class StrategyPlanningTool(HongLouMengTool):
    """策略规划工具"""
    
    def __init__(self):
        super().__init__(
            name="strategy_planning",
            description="制定红楼梦续写策略和情节大纲"
        )
    
    async def execute(self, user_ending: str, knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """执行策略规划"""
        try:
            # 兼容性检查
            compatibility = await self._check_compatibility(user_ending)
            
            if not compatibility["compatible"]:
                return {
                    "success": False,
                    "error": f"用户结局与原著冲突: {compatibility['reason']}"
                }
            
            # 生成40回大纲
            plot_outline = await self._generate_plot_outline(user_ending, knowledge_base)
            
            return {
                "success": True,
                "compatibility_check": compatibility,
                "plot_outline": plot_outline,
                "strategy_summary": self._generate_strategy_summary(user_ending)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_compatibility(self, user_ending: str) -> Dict[str, Any]:
        """检查兼容性"""
        # 简化的兼容性检查
        conflicts = []
        
        # 检查是否与原著人物设定冲突
        if "贾宝玉" in user_ending and "出家" in user_ending:
            # 这与原著暗示的结局一致
            pass
        elif "林黛玉" in user_ending and ("死" in user_ending or "亡" in user_ending):
            # 检查是否与用户期望的结局冲突
            if "结婚" in user_ending or "成亲" in user_ending:
                conflicts.append("林黛玉死亡与结婚结局冲突")
        
        return {
            "compatible": len(conflicts) == 0,
            "conflicts": conflicts,
            "reason": conflicts[0] if conflicts else None
        }
    
    async def _generate_plot_outline(self, user_ending: str, knowledge_base: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成情节大纲"""
        # 生成40回的基本框架
        outline = []
        
        for i in range(40):
            chapter_num = 81 + i
            
            if i < 10:
                phase = "开端"
                theme = "家族变故初现"
            elif i < 20:
                phase = "发展"
                theme = "情感纠葛加深"
            elif i < 30:
                phase = "高潮"
                theme = "命运转折关键"
            else:
                phase = "结局"
                theme = "尘埃落定收尾"
            
            outline.append({
                "chapter": chapter_num,
                "title": f"第{chapter_num}回",
                "phase": phase,
                "theme": theme,
                "main_characters": self._get_chapter_characters(i),
                "plot_points": self._get_chapter_plot_points(i, user_ending),
                "estimated_words": 2500
            })
        
        return outline
    
    def _get_chapter_characters(self, chapter_index: int) -> List[str]:
        """获取章节主要人物"""
        all_characters = ["贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母"]
        
        # 根据章节阶段返回不同人物组合
        if chapter_index < 10:
            return all_characters[:3]
        elif chapter_index < 20:
            return all_characters[:4]
        else:
            return all_characters
    
    def _get_chapter_plot_points(self, chapter_index: int, user_ending: str) -> List[str]:
        """获取章节情节要点"""
        if chapter_index < 10:
            return ["家族日常", "人物关系发展", "伏笔铺垫"]
        elif chapter_index < 20:
            return ["情感冲突", "社会变迁", "命运暗示"]
        elif chapter_index < 30:
            return ["关键转折", "高潮冲突", "情感爆发"]
        else:
            return ["结局铺垫", "人物归宿", "主题升华"]
    
    def _generate_strategy_summary(self, user_ending: str) -> str:
        """生成策略摘要"""
        return f"""
续写策略摘要：
- 用户期望结局：{user_ending}
- 创作风格：古典文学，雅致优美
- 人物塑造：保持原著性格特征
- 情节发展：循序渐进，合理过渡
- 主题表达：命运、爱情、家族兴衰
- 文学技法：诗词点缀，意境深远
"""


class ContentGenerationTool(HongLouMengTool):
    """内容生成工具"""
    
    def __init__(self):
        super().__init__(
            name="content_generation",
            description="生成高质量的古典文学续写内容"
        )
    
    async def execute(self, chapter_info: Dict[str, Any], strategy: Dict[str, Any], 
                     knowledge_base: Dict[str, Any]) -> Dict[str, Any]:
        """执行内容生成"""
        try:
            # 生成章节内容
            content = await self._generate_chapter_content(chapter_info, strategy, knowledge_base)
            
            return {
                "success": True,
                "content": content,
                "word_count": len(content),
                "chapter_info": chapter_info
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _generate_chapter_content(self, chapter_info: Dict[str, Any], 
                                       strategy: Dict[str, Any], knowledge_base: Dict[str, Any]) -> str:
        """生成章节内容"""
        # 这里应该调用LLM生成内容，暂时返回模板内容
        chapter_num = chapter_info.get("chapter", 81)
        title = chapter_info.get("title", f"第{chapter_num}回")
        theme = chapter_info.get("theme", "续写内容")
        
        content = f"""### {title}

{theme}
----

话说{chapter_info.get('main_characters', ['贾宝玉'])[0]}当日...

（此处为生成的古典文学内容，约2500字）

这一回中，{theme}得到了充分的展现，人物性格也有了进一步的发展。正是：

    {self._generate_poem()}

欲知后事如何，且听下回分解。
"""
        
        return content
    
    def _generate_poem(self) -> str:
        """生成诗词"""
        poems = [
            "花开花落总无情，\n    人生如梦亦如风。",
            "红楼一梦醒来时，\n    方知世事皆虚无。",
            "情深不寿慧极伤，\n    月满则亏水满溢。"
        ]
        
        import random
        return random.choice(poems)


class QualityAssessmentTool(HongLouMengTool):
    """质量评估工具"""
    
    def __init__(self):
        super().__init__(
            name="quality_assessment",
            description="评估续写内容的质量和文学价值"
        )
    
    async def execute(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量评估"""
        try:
            chapters = content.get("chapters", [])
            
            # 评估各个维度
            style_score = self._assess_style_consistency(chapters)
            character_score = self._assess_character_accuracy(chapters)
            plot_score = self._assess_plot_coherence(chapters)
            literary_score = self._assess_literary_quality(chapters)
            
            # 计算综合分数
            overall_score = (
                style_score * 0.3 +
                character_score * 0.3 +
                plot_score * 0.25 +
                literary_score * 0.15
            )
            
            return {
                "success": True,
                "overall_score": round(overall_score, 1),
                "detailed_scores": {
                    "style_consistency": style_score,
                    "character_accuracy": character_score,
                    "plot_coherence": plot_score,
                    "literary_quality": literary_score
                },
                "suggestions": self._generate_suggestions(overall_score, {
                    "style_consistency": style_score,
                    "character_accuracy": character_score,
                    "plot_coherence": plot_score,
                    "literary_quality": literary_score
                })
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _assess_style_consistency(self, chapters: List[str]) -> float:
        """评估风格一致性"""
        # 简化的风格评估
        classical_indicators = ["道", "曰", "乃", "之", "其", "也", "矣"]
        
        total_score = 0
        for chapter in chapters:
            score = sum(1 for indicator in classical_indicators if indicator in chapter)
            total_score += min(score / 10, 1.0) * 10  # 标准化到10分制
        
        return round(total_score / len(chapters) if chapters else 0, 1)
    
    def _assess_character_accuracy(self, chapters: List[str]) -> float:
        """评估人物准确性"""
        # 检查人物出现频率和描写
        main_characters = ["贾宝玉", "林黛玉", "薛宝钗", "王熙凤"]
        
        character_presence = 0
        for chapter in chapters:
            for char in main_characters:
                if char in chapter:
                    character_presence += 1
        
        # 基于人物出现频率评分
        score = min(character_presence / (len(chapters) * 2), 1.0) * 10
        return round(score, 1)
    
    def _assess_plot_coherence(self, chapters: List[str]) -> float:
        """评估情节连贯性"""
        # 简化的连贯性评估
        coherence_indicators = ["话说", "却说", "原来", "后来", "从此"]
        
        coherence_score = 0
        for chapter in chapters:
            score = sum(1 for indicator in coherence_indicators if indicator in chapter)
            coherence_score += min(score / 5, 1.0) * 10
        
        return round(coherence_score / len(chapters) if chapters else 0, 1)
    
    def _assess_literary_quality(self, chapters: List[str]) -> float:
        """评估文学质量"""
        # 检查修辞手法和诗词
        literary_elements = ["诗曰", "词云", "正是", "恰似", "如同"]
        
        literary_score = 0
        for chapter in chapters:
            score = sum(1 for element in literary_elements if element in chapter)
            literary_score += min(score / 3, 1.0) * 10
        
        return round(literary_score / len(chapters) if chapters else 0, 1)
    
    def _generate_suggestions(self, overall_score: float, detailed_scores: Dict[str, float]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if overall_score < 7.0:
            suggestions.append("整体质量需要提升，建议加强古典文学风格")
        
        if detailed_scores["style_consistency"] < 7.0:
            suggestions.append("建议增加更多古典文学语言特征，如'道'、'曰'等")
        
        if detailed_scores["character_accuracy"] < 7.0:
            suggestions.append("建议加强主要人物的出场和性格刻画")
        
        if detailed_scores["plot_coherence"] < 7.0:
            suggestions.append("建议增强章节间的情节连贯性")
        
        if detailed_scores["literary_quality"] < 7.0:
            suggestions.append("建议添加更多诗词和修辞手法")
        
        return suggestions


class HongLouMengDataProcessor(LlmAgent):
    """红楼梦数据处理Agent"""
    
    def __init__(self, settings: Settings):
        super().__init__(
            name="红楼梦数据处理Agent",
            model="gemini-2.0-flash",  # 使用Gemini模型
            instruction="""你是红楼梦文本分析专家，负责：
1. 分析红楼梦前80回内容
2. 提取人物关系和性格特征
3. 构建知识图谱
4. 识别文学风格特征
请保持专业和准确。""",
            description="分析红楼梦文本，提取知识图谱和文学特征",
            tools=[ChapterAnalysisTool()]
        )
        self.settings = settings


class HongLouMengStrategyPlanner(LlmAgent):
    """红楼梦策略规划Agent"""
    
    def __init__(self, settings: Settings):
        super().__init__(
            name="红楼梦策略规划Agent",
            model="gemini-2.0-flash",
            instruction="""你是红楼梦续写策略专家，负责：
1. 分析用户期望的结局
2. 检查与原著的兼容性
3. 制定40回续写大纲
4. 设计情节发展策略
请确保策略符合古典文学传统。""",
            description="制定红楼梦续写策略和情节规划",
            tools=[StrategyPlanningTool()]
        )
        self.settings = settings


class HongLouMengContentGenerator(LlmAgent):
    """红楼梦内容生成Agent"""
    
    def __init__(self, settings: Settings):
        super().__init__(
            name="红楼梦内容生成Agent",
            model="gemini-2.0-flash",
            instruction="""你是古典文学创作大师，专门续写红楼梦，要求：
1. 严格遵循古典文学风格
2. 保持人物性格一致性
3. 使用雅致优美的文辞
4. 融入诗词和修辞手法
5. 体现深刻的文学内涵
请创作出媲美原著的高质量内容。""",
            description="生成高质量的红楼梦续写内容",
            tools=[ContentGenerationTool()]
        )
        self.settings = settings


class HongLouMengQualityChecker(LlmAgent):
    """红楼梦质量校验Agent"""
    
    def __init__(self, settings: Settings):
        super().__init__(
            name="红楼梦质量校验Agent",
            model="gemini-2.0-flash",
            instruction="""你是文学评论专家，专门评估红楼梦续写质量：
1. 风格一致性评估
2. 人物性格准确性
3. 情节合理性分析
4. 文学素养评价
请提供客观专业的评估和改进建议。""",
            description="评估续写内容的质量和文学价值",
            tools=[QualityAssessmentTool()]
        )
        self.settings = settings


class HongLouMengCoordinator(LlmAgent):
    """红楼梦续写协调Agent"""
    
    def __init__(self, settings: Settings):
        # 创建子Agent
        data_processor = HongLouMengDataProcessor(settings)
        strategy_planner = HongLouMengStrategyPlanner(settings)
        content_generator = HongLouMengContentGenerator(settings)
        quality_checker = HongLouMengQualityChecker(settings)
        
        super().__init__(
            name="红楼梦续写协调Agent",
            model="gemini-2.0-flash",
            instruction="""你是红楼梦续写项目的总协调者，负责：
1. 协调各个专业Agent的工作
2. 确保续写流程的顺利进行
3. 处理Agent间的通信和反馈
4. 保证最终输出的质量
请统筹全局，确保项目成功。""",
            description="协调红楼梦续写的整个流程",
            sub_agents=[
                data_processor,
                strategy_planner,
                content_generator,
                quality_checker
            ]
        )
        self.settings = settings
        
        # 保存子Agent引用
        self.data_processor = data_processor
        self.strategy_planner = strategy_planner
        self.content_generator = content_generator
        self.quality_checker = quality_checker
    
    async def process_continuation_request(self, user_ending: str, chapters: int = 1) -> Dict[str, Any]:
        """处理续写请求"""
        try:
            print("🎭 [ADK] 开始红楼梦续写流程")
            
            # 1. 数据预处理
            print("📊 [ADK] 执行数据预处理...")
            data_result = await self.data_processor.run({"action": "analyze_text"})
            
            # 2. 策略规划
            print("📝 [ADK] 制定续写策略...")
            strategy_result = await self.strategy_planner.run({
                "user_ending": user_ending,
                "knowledge_base": data_result.get("data", {})
            })
            
            # 3. 内容生成
            print("🎨 [ADK] 生成续写内容...")
            content_result = await self.content_generator.run({
                "strategy": strategy_result.get("data", {}),
                "chapters": chapters,
                "knowledge_base": data_result.get("data", {})
            })
            
            # 4. 质量评估
            print("🔍 [ADK] 评估内容质量...")
            quality_result = await self.quality_checker.run({
                "content": content_result.get("data", {})
            })
            
            # 5. 整合结果
            final_result = {
                "success": True,
                "data": {
                    "content": content_result.get("data", {}),
                    "quality": quality_result.get("data", {}),
                    "strategy": strategy_result.get("data", {}),
                    "metadata": {
                        "user_ending": user_ending,
                        "chapters_requested": chapters,
                        "processing_time": "completed"
                    }
                },
                "message": "红楼梦续写完成"
            }
            
            print("✅ [ADK] 红楼梦续写流程完成")
            return final_result
            
        except Exception as e:
            print(f"❌ [ADK] 续写流程失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "续写流程执行失败"
            }


def create_hongloumeng_agent_system(settings: Settings) -> HongLouMengCoordinator:
    """创建红楼梦Agent系统"""
    return HongLouMengCoordinator(settings)
