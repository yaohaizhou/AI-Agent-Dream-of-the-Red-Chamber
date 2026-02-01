#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编排Agent
负责协调各个Agent的工作流程
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .base import BaseAgent, AgentResult, MockAgent
from .real.data_processor_agent import DataProcessorAgent
from .real.strategy_planner_agent import StrategyPlannerAgent
from .real.chapter_planner_agent import ChapterPlannerAgent
from .real.content_generator_agent import ContentGeneratorAgent
from .real.quality_checker_agent import QualityCheckerAgent
from .progressive_generator import ProgressiveGenerator
from .character_consistency_checker import AdvancedQualityChecker
from .communication import get_communication_bus, MessageType
from ..config.settings import Settings


class OrchestratorAgent(BaseAgent):
    """编排Agent，协调多Agent协作"""

    def __init__(self, settings: Settings):
        super().__init__("编排Agent", {"coordinator": True})
        self.settings = settings
        self.communication_bus = get_communication_bus()
        self.set_communication_bus(self.communication_bus)
        self.agents = self._initialize_agents()

    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """初始化所有Agent"""
        agents = {}

        try:
            # 数据预处理Agent
            agents['data_processor'] = DataProcessorAgent(self.settings)
            agents['data_processor'].set_communication_bus(self.communication_bus)

            # 续写策略Agent
            agents['strategy_planner'] = StrategyPlannerAgent(self.settings)
            agents['strategy_planner'].set_communication_bus(self.communication_bus)

            # 章节规划Agent（V2新增）
            agents['chapter_planner'] = ChapterPlannerAgent(self.settings)
            agents['chapter_planner'].set_communication_bus(self.communication_bus)

            # 内容生成Agent
            agents['content_generator'] = ContentGeneratorAgent(self.settings)
            agents['content_generator'].set_communication_bus(self.communication_bus)

            # 质量校验Agent
            agents['quality_checker'] = QualityCheckerAgent(self.settings)
            agents['quality_checker'].set_communication_bus(self.communication_bus)

            # 用户交互Agent (暂时使用MockAgent)
            agents['user_interface'] = MockAgent(
                "用户交互Agent",
                {
                    "response_delay": 0.5,
                    "task": "处理用户输入和输出格式化"
                }
            )
            agents['user_interface'].set_communication_bus(self.communication_bus)

        except Exception as e:
            print(f"Agent初始化失败，使用MockAgent: {e}")
            # 如果真实Agent初始化失败，回退到MockAgent
            agents = self._initialize_mock_agents()

        return agents

    def _initialize_mock_agents(self) -> Dict[str, BaseAgent]:
        """初始化MockAgent作为备用"""
        agents = {}

        # 数据预处理Agent
        agents['data_processor'] = MockAgent(
            "数据预处理Agent",
            {
                "response_delay": 2.0,
                "task": "分析红楼梦文本，提取人物关系和情节脉络"
            }
        )

        # 续写策略Agent
        agents['strategy_planner'] = MockAgent(
            "续写策略Agent",
            {
                "response_delay": 1.5,
                "task": "根据用户结局制定续写策略和大纲"
            }
        )

        # 章节规划Agent（V2新增）
        agents['chapter_planner'] = MockAgent(
            "章节规划Agent",
            {
                "response_delay": 1.0,
                "task": "设计每一回的详细内容规划"
            }
        )

        # 内容生成Agent
        agents['content_generator'] = MockAgent(
            "内容生成Agent",
            {
                "response_delay": 3.0,
                "task": "生成古典文学风格的续写内容"
            }
        )

        # 质量校验Agent
        agents['quality_checker'] = MockAgent(
            "质量校验Agent",
            {
                "response_delay": 1.0,
                "task": "评估内容质量和一致性"
            }
        )

        # 用户交互Agent
        agents['user_interface'] = MockAgent(
            "用户交互Agent",
            {
                "response_delay": 0.5,
                "task": "处理用户输入和输出格式化"
            }
        )

        return agents

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """执行完整的续写流程"""
        self.update_status("orchestrating")

        try:
            print("🔍 [DEBUG] 开始执行续写流程")
            print(f"🔍 [DEBUG] 输入数据: {input_data}")

            # 1. 验证输入
            print("🔍 [DEBUG] 步骤1: 验证输入")
            if not self._validate_continuation_request(input_data):
                print("❌ [DEBUG] 输入验证失败")
                return AgentResult(
                    success=False,
                    data=None,
                    message="输入验证失败"
                )
            print("✅ [DEBUG] 输入验证通过")

            # 2. 并行执行数据预处理和策略规划
            print("🔍 [DEBUG] 步骤2: 并行执行数据预处理和策略规划")
            preprocessing_result, strategy_result = await self._parallel_preprocessing(input_data)

            print(f"🔍 [DEBUG] 数据预处理结果: success={preprocessing_result.success}, message={preprocessing_result.message}")
            print(f"🔍 [DEBUG] 策略规划结果: success={strategy_result.success}, message={strategy_result.message}")

            if not preprocessing_result.success or not strategy_result.success:
                print("❌ [DEBUG] 预处理阶段失败")
                return AgentResult(
                    success=False,
                    data={
                        "preprocessing_error": preprocessing_result.message if not preprocessing_result.success else None,
                        "strategy_error": strategy_result.message if not strategy_result.success else None
                    },
                    message="预处理阶段失败"
                )

            print("✅ [DEBUG] 预处理阶段完成")

            # 3. 章节规划（V2新增）
            print("🔍 [DEBUG] 步骤3: 章节规划")
            chapter_planning_context = {
                "user_ending": input_data.get("ending", ""),
                "overall_strategy": strategy_result.data,
                "knowledge_base": preprocessing_result.data,
                "chapters_count": input_data.get("chapters", 1),  # 默认规划1回用于测试
                "start_chapter": 81
            }
            print(f"🔍 [DEBUG] 章节规划上下文: {chapter_planning_context}")

            chapter_plan_result = await self._plan_chapters(chapter_planning_context)

            print(f"🔍 [DEBUG] 章节规划结果: success={chapter_plan_result.success}, message={chapter_plan_result.message}")

            if not chapter_plan_result.success:
                print("❌ [DEBUG] 章节规划失败")
                return AgentResult(
                    success=False,
                    data=chapter_plan_result.data,
                    message="章节规划失败"
                )

            print("✅ [DEBUG] 章节规划完成")

            # 4. 使用渐进式生成器生成续写内容
            print("🔍 [DEBUG] 步骤4: 使用渐进式生成器生成续写内容")
            generation_context = {
                "knowledge_base": preprocessing_result.data,
                "strategy": strategy_result.data,
                "chapter_plan": chapter_plan_result.data,
                "user_ending": input_data.get("ending", ""),
                "story_context": self._extract_story_context(preprocessing_result.data, strategy_result.data)
            }
            print(f"🔍 [DEBUG] 生成上下文: {generation_context}")

            # 初始化渐进式生成器和高级质量检查器
            content_generator = self.agents['content_generator']
            progressive_gen = ProgressiveGenerator(content_generator.gpt5_client, content_generator.prompts)
            advanced_checker = AdvancedQualityChecker(content_generator.gpt5_client, content_generator.prompts)

            # 生成章节
            chapter_number = 81  # 从第81回开始
            generation_result = await progressive_gen.generate_chapter(
                chapter_number=chapter_number,
                context=generation_context,
                quality_threshold=8.0
            )

            print(f"🔍 [DEBUG] 渐进式生成完成，章节: {chapter_number}")

            # 5. 使用高级质量检查器进行评估
            print("🔍 [DEBUG] 步骤5: 使用高级质量检查器进行评估")
            content_to_check = generation_result.get("final_content", "")
            chapter_info = {
                "chapter_number": chapter_number,
                "title": generation_result.get("title", f"第{chapter_number}回"),
                "scenes": generation_result.get("scenes_content", [])
            }

            quality_result = await advanced_checker.comprehensive_check(
                content=content_to_check,
                chapter_info=chapter_info,
                context=generation_context
            )

            print(f"🔍 [DEBUG] 高级质量检查完成，总体评分: {quality_result['overall_score']}")

            # 6. 格式化输出
            print("🔍 [DEBUG] 步骤6: 格式化输出")
            final_result = await self._format_output({
                "content": generation_result,
                "quality": quality_result,
                "metadata": input_data
            })

            print(f"🔍 [DEBUG] 格式化输出结果: success={final_result.success}, message={final_result.message}")

            self.update_status("completed")

            # 整合所有阶段的数据
            integrated_data = {
                "knowledge_base": preprocessing_result.data if preprocessing_result.success else {},
                "strategy": strategy_result.data if strategy_result.success else {},
                "chapter_plan": chapter_plan_result.data if chapter_plan_result.success else {},
                "content": generation_result,
                "quality": quality_result,
                "user_interface": final_result.data if final_result.success else {}
            }

            print("✅ [DEBUG] 续写流程全部完成")
            return AgentResult(
                success=True,
                data=integrated_data,
                message="续写流程完成"
            )

        except Exception as e:
            print(f"❌ [DEBUG] 续写流程异常: {str(e)}")
            import traceback
            print(f"❌ [DEBUG] 异常详情:\n{traceback.format_exc()}")
            self.update_status("error")
            return self.handle_error(e)

    def _validate_continuation_request(self, input_data: Dict[str, Any]) -> bool:
        """验证续写请求"""
        required_fields = ["ending", "chapters"]
        for field in required_fields:
            if field not in input_data:
                return False
        return True

    async def _parallel_preprocessing(self, input_data: Dict[str, Any]) -> tuple[AgentResult, AgentResult]:
        """并行执行数据预处理和策略规划，带错误恢复"""
        try:
            # 并行处理，但设置超时和错误处理
            preprocessing_task = asyncio.wait_for(
                self.agents['data_processor'].process(input_data), 
                timeout=60.0  # 设置60秒超时
            )
            strategy_task = asyncio.wait_for(
                self.agents['strategy_planner'].process(input_data), 
                timeout=60.0
            )

            preprocessing_result, strategy_result = await asyncio.gather(
                preprocessing_task, 
                strategy_task,
                return_exceptions=True  # 允许单个任务失败
            )

            # 检查是否返回的是异常
            if isinstance(preprocessing_result, Exception):
                print(f"⚠️ 数据预处理任务异常: {preprocessing_result}")
                preprocessing_result = self._create_fallback_result("data_processor", preprocessing_result)
            
            if isinstance(strategy_result, Exception):
                print(f"⚠️ 策略规划任务异常: {strategy_result}")
                strategy_result = self._create_fallback_result("strategy_planner", strategy_result)

        except asyncio.TimeoutError:
            print("⏰ 并行预处理超时，使用降级方案")
            preprocessing_result = self._create_fallback_result("data_processor", "Timeout")
            strategy_result = self._create_fallback_result("strategy_planner", "Timeout")
        except Exception as e:
            print(f"🚨 并行预处理严重错误: {e}")
            preprocessing_result = self._create_fallback_result("data_processor", e)
            strategy_result = self._create_fallback_result("strategy_planner", e)

        return preprocessing_result, strategy_result

    def _create_fallback_result(self, agent_name: str, error: Exception) -> AgentResult:
        """创建降级结果"""
        print(f"🔄 [{agent_name}] 创建降级结果...")
        
        # 根据不同代理类型创建相应的降级数据
        fallback_data = {}
        
        if agent_name == "data_processor":
            # 数据预处理的降级数据
            fallback_data = {
                "characters": {
                    "贾宝玉": {"性格": "纯真善良，反叛封建礼教", "现状": "经历诸多变故", "发展方向": "寻求精神解脱"},
                    "林黛玉": {"性格": "聪慧敏感，多愁善感", "现状": "体弱多病", "发展方向": "坚持纯真爱情理想"},
                    "薛宝钗": {"性格": "端庄贤惠，世故圆通", "现状": "深得贾府喜爱", "发展方向": "适应社会规范"}
                },
                "plot_structure": {
                    "total_chapters": 80,
                    "key_events": [{"chapter": 1, "event": "甄士隐梦幻识通灵", "importance": "high"}]
                },
                "themes": ["爱情与婚姻", "家族兴衰", "封建礼教"],
                "text_statistics": {"chapter_count": 80, "character_count": 500000}
            }
        elif agent_name == "strategy_planner":
            # 策略规划的降级数据
            fallback_data = {
                "user_ending": "未知结局",
                "overall_strategy": {
                    "overall_approach": "渐进式发展",
                    "key_themes": ["爱情", "家族", "个人"],
                    "narrative_style": "第三人称全知视角"
                },
                "plot_outline": [{
                    "chapter_num": 81,
                    "title": "第81回 占旺相四美钓游鱼 奉严词两番入家塾",
                    "phase": "续写开篇",
                    "focus": "承接前文，开启新发展"
                }]
            }
        
        return AgentResult(
            success=False,
            data=fallback_data,
            message=f"[降级方案] {agent_name} 代理出现错误: {str(error) if hasattr(error, '__str__') else 'Unknown error'}"
        )

    def _extract_story_context(self, knowledge_base: Dict[str, Any], strategy: Dict[str, Any]) -> str:
        """从知识库和策略中提取故事上下文"""
        context_parts = []
        
        # 从知识库中提取人物信息
        characters = knowledge_base.get("characters", {})
        if characters:
            context_parts.append("人物状态：")
            for name, info in characters.items():
                personality = info.get("性格", "未知")
                current_state = info.get("现状", "未知")
                context_parts.append(f"- {name}：{personality}，{current_state}")
        
        # 从策略中提取用户期望
        user_ending = strategy.get("user_ending", "未知结局")
        context_parts.append(f"理想结局方向：{user_ending}")
        
        # 从策略中提取主题
        overall_strategy = strategy.get("overall_strategy", {})
        themes = overall_strategy.get("key_themes", [])
        if themes:
            context_parts.append(f"核心主题：{', '.join(themes)}")
        
        return "\n".join(context_parts)

    async def _plan_chapters(self, context: Dict[str, Any]) -> AgentResult:
        """章节规划（V2新增）"""
        print("📋 [DEBUG] 调用ChapterPlannerAgent进行章节规划")
        return await self.agents['chapter_planner'].process(context)

    async def _generate_content(self, context: Dict[str, Any]) -> AgentResult:
        """生成续写内容"""
        return await self.agents['content_generator'].process(context)

    async def _assess_quality(self, content: Any) -> AgentResult:
        """质量评估"""
        # 处理content数据格式
        if isinstance(content, dict):
            # 如果是字典格式，提取chapters字段
            chapters = content.get("chapters", [])
            if chapters:
                # 将所有章节内容合并为一个字符串进行评估
                content_text = "\n\n".join(chapters)
            else:
                content_text = ""
        else:
            content_text = str(content) if content else ""
        
        return await self.agents['quality_checker'].process({"content": content_text})

    async def _format_output(self, results: Dict[str, Any]) -> AgentResult:
        """格式化输出结果"""
        return await self.agents['user_interface'].process(results)

    def get_agents_status(self) -> Dict[str, Any]:
        """获取所有Agent的状态"""
        return {
            agent_name: agent.get_status()
            for agent_name, agent in self.agents.items()
        }

    async def continue_dream_of_red_chamber(
        self,
        ending: str,
        chapters: int = 40,
        quality_threshold: float = 7.0
    ) -> AgentResult:
        """续写红楼梦的主方法"""
        input_data = {
            "ending": ending,
            "chapters": chapters,
            "quality_threshold": quality_threshold,
            "timestamp": datetime.now().isoformat()
        }

        return await self.process(input_data)

    def save_results(self, results: AgentResult, output_dir: Optional[str] = None):
        """保存结果到文件"""
        if output_dir is None:
            output_dir = f"output/red_chamber_continuation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        import json

        # 保存结果摘要
        summary_file = output_path / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "success": results.success,
                "message": results.message,
                "timestamp": datetime.now().isoformat(),
                "output_dir": str(output_path)
            }, f, ensure_ascii=False, indent=2)

        # 保存详细结果
        if results.success and results.data:
            details_file = output_path / "details.json"
            with open(details_file, 'w', encoding='utf-8') as f:
                json.dump(results.data, f, ensure_ascii=False, indent=2)

        # 生成markdown格式的续写内容
        self._generate_markdown_content(results, output_path)

        return str(output_path)

    def _generate_markdown_content(self, results: AgentResult, output_path: Path):
        """生成markdown格式的续写内容"""
        if not results.success or not results.data:
            return

        # 创建章节目录
        chapters_dir = output_path / "chapters"
        chapters_dir.mkdir(exist_ok=True)

        # 获取实际生成的章节内容（现在使用新的渐进式生成器数据结构）
        content_data = results.data.get("content", {})
        final_content = content_data.get("final_content", "")
        title = content_data.get("title", f"第81回")
        
        # 提取章节号
        import re
        chapter_num_match = re.search(r'第(\d+)回', title)
        if chapter_num_match:
            chapter_num = int(chapter_num_match.group(1))
        else:
            chapter_num = 81  # 默认从第81回开始
        
        print(f"💾 [DEBUG] 保存第{chapter_num}回续写内容")
        
        # 保存生成的章节内容
        if final_content:
            chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.md"
            
            # 格式化章节内容
            formatted_content = f"""# {title}

{final_content}

---

*本回由AI续写系统生成，保持古典文学风格*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            print(f"💾 [DEBUG] 已保存第{chapter_num}回，长度: {len(final_content)}")
        else:
            print("⚠️ [DEBUG] 没有找到生成的章节内容，创建占位符文件")
            # 如果没有实际内容，创建一个占位符
            placeholder_content = f"""# {title}

*续写内容生成中...*

---

*本回由AI续写系统生成*
"""
            chapter_file = chapters_dir / f"chapter_{chapter_num:03d}.md"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(placeholder_content)

        # 生成策略大纲（使用实际的策略数据）
        strategy_file = output_path / "strategy_outline.md"
        strategy_content = self._generate_strategy_markdown(results.data.get("strategy", {}))
        with open(strategy_file, 'w', encoding='utf-8') as f:
            f.write(strategy_content)

        # 生成质量报告（使用新的高级质量检查器数据）
        quality_file = output_path / "quality_report.md"
        quality_data = results.data.get("quality", {})
        quality_content = self._generate_advanced_quality_markdown(quality_data)
        with open(quality_file, 'w', encoding='utf-8') as f:
            f.write(quality_content)

    def _generate_strategy_markdown(self, strategy_data: Dict[str, Any]) -> str:
        """生成策略大纲的markdown内容"""
        if not strategy_data:
            return "# 续写策略大纲\n\n*策略数据生成中...*\n"
        
        user_ending = strategy_data.get("user_ending", "未指定结局")
        compatibility = strategy_data.get("compatibility_check", {})
        overall_strategy = strategy_data.get("overall_strategy", {})
        plot_outline = strategy_data.get("plot_outline", [])
        character_arcs = strategy_data.get("character_arcs", {})
        theme_development = strategy_data.get("theme_development", {})
        
        content = f"""# 续写策略大纲

## 用户期望结局
{user_ending}

## 兼容性分析
- **兼容性评分**: {compatibility.get('compatibility_score', 0):.1f}/1.0
- **兼容性状态**: {'✅ 兼容' if compatibility.get('compatible', False) else '❌ 不兼容'}
- **分析说明**: {compatibility.get('reason', '未提供分析')}

## 总体策略
- **创作方法**: {overall_strategy.get('overall_approach', '未指定')}
- **叙事风格**: {overall_strategy.get('narrative_style', '未指定')}
- **核心主题**: {', '.join(overall_strategy.get('key_themes', []))}
- **情感弧线**: {' → '.join(overall_strategy.get('emotional_arc', []))}

## 情节大纲
"""
        
        # 添加章节大纲
        if plot_outline:
            for chapter in plot_outline:
                chapter_num = chapter.get('chapter_num', '?')
                title = chapter.get('title', '未定标题')
                phase = chapter.get('phase', '未定阶段')
                focus = chapter.get('focus', '未定重点')
                key_events = chapter.get('key_events', [])
                themes = chapter.get('themes', [])
                
                content += f"""
### {title}
- **阶段**: {phase}
- **重点**: {focus}
- **关键事件**: {', '.join(key_events) if key_events else '待规划'}
- **主题**: {', '.join(themes) if themes else '待确定'}
"""
        else:
            content += "\n*情节大纲生成中...*\n"
        
        # 添加人物发展弧线
        if character_arcs:
            content += "\n## 人物发展弧线\n"
            for character, arc in character_arcs.items():
                if isinstance(arc, list):
                    content += f"- **{character}**: {' → '.join(arc)}\n"
                else:
                    content += f"- **{character}**: {arc}\n"
        
        # 添加主题发展
        if theme_development:
            content += "\n## 主题发展\n"
            for theme, development in theme_development.items():
                if isinstance(development, list):
                    content += f"- **{theme}**: {' → '.join(development)}\n"
                else:
                    content += f"- **{theme}**: {development}\n"
        
        content += f"\n---\n\n*策略生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return content

    def _generate_quality_markdown(self, quality_data: Dict[str, Any]) -> str:
        """生成质量报告的markdown内容（旧版，保持向后兼容）"""
        if not quality_data:
            return "# 质量评估报告\n\n*质量评估数据生成中...*\n"
        
        overall_score = quality_data.get("overall_score", 0)
        dimensions = quality_data.get("dimensions", {})
        suggestions = quality_data.get("suggestions", [])
        
        # 生成星级评分
        stars = "⭐" * min(5, int(overall_score / 2))
        
        content = f"""# 质量评估报告

## 综合评分: {overall_score:.1f}/10 {stars}

### 维度详情
"""
        
        # 添加各维度评分
        dimension_names = {
            "style_consistency": "风格一致性",
            "character_accuracy": "人物准确性", 
            "plot_reasonability": "情节合理性",
            "literary_quality": "文学质量"
        }
        
        for dim_key, score in dimensions.items():
            dim_name = dimension_names.get(dim_key, dim_key)
            if isinstance(score, (int, float)):
                grade = self._get_quality_grade(score)
                content += f"- **{dim_name}**: {score:.1f}/10 ({grade})\n"
        
        # 添加改进建议
        if suggestions:
            content += "\n### 改进建议\n"
            for i, suggestion in enumerate(suggestions, 1):
                content += f"{i}. {suggestion}\n"
        else:
            content += "\n### 改进建议\n*暂无具体建议*\n"
        
        content += f"\n### 评估时间\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return content

    def _generate_advanced_quality_markdown(self, quality_data: Dict[str, Any]) -> str:
        """生成高级质量报告的markdown内容"""
        if not quality_data:
            return "# 高级质量评估报告\n\n*质量评估数据生成中...*\n"
        
        overall_score = quality_data.get("overall_score", 0)
        char_consistency = quality_data.get("character_consistency", {})
        structure_score = quality_data.get("structure_score", 0)
        style_score = quality_data.get("style_score", 0)
        recommendations = quality_data.get("recommendations", [])
        
        # 生成星级评分
        stars = "⭐" * min(5, int(overall_score / 2))
        
        content = f"""# 高级质量评估报告

## 综合评分: {overall_score:.1f}/10 {stars}

### 评估维度
- **人物一致性**: {char_consistency.get('overall_score', 0):.1f}/10
- **结构完整性**: {structure_score:.1f}/10
- **风格一致性**: {style_score:.1f}/10

"""
        
        # 添加人物一致性详情
        individual_results = char_consistency.get("individual_results", {})
        if individual_results:
            content += "### 人物一致性详情\n"
            for char_name, result in individual_results.items():
                score = result.get("score", 0)
                consistent = result.get("consistent", False)
                status = "✅" if consistent else "❌"
                content += f"- **{char_name}**: {score:.1f}/10 {status}\n"
            
            content += "\n"
        
        # 添加改进建议
        if recommendations:
            content += "### 改进建议\n"
            for i, recommendation in enumerate(recommendations, 1):
                content += f"{i}. {recommendation}\n"
        else:
            content += "### 改进建议\n*未发现问题*\n"
        
        content += f"\n### 评估时间\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return content

    def _get_quality_grade(self, score: float) -> str:
        """根据分数获取质量等级"""
        if score >= 9.0:
            return "优秀"
        elif score >= 8.0:
            return "良好"
        elif score >= 7.0:
            return "合格"
        elif score >= 6.0:
            return "待改进"
        else:
            return "需重写"

    async def _iterative_improvement(self, content_result: AgentResult, input_data: Dict[str, Any]) -> tuple[AgentResult, AgentResult]:
        """迭代改进机制"""
        max_iterations = 3
        current_iteration = 0
        min_score_threshold = self.settings.quality.min_score_threshold
        
        print(f"🔄 [DEBUG] 开始迭代优化，最大迭代次数: {max_iterations}, 最低分数要求: {min_score_threshold}")
        
        current_content = content_result
        
        while current_iteration < max_iterations:
            print(f"🔄 [DEBUG] 第 {current_iteration + 1} 次质量评估")
            
            # 质量评估
            quality_result = await self._assess_quality(current_content.data)
            
            if not quality_result.success:
                print("❌ [DEBUG] 质量评估失败，停止迭代")
                break
                
            overall_score = quality_result.data.get("overall_score", 0) if quality_result.data else 0
            print(f"🔍 [DEBUG] 当前质量分数: {overall_score}/{min_score_threshold}")
            
            # 如果质量达标，结束迭代
            if overall_score >= min_score_threshold:
                print(f"✅ [DEBUG] 质量达标 ({overall_score} >= {min_score_threshold})，结束迭代")
                return current_content, quality_result
            
            # 如果是最后一次迭代，不再重新生成
            if current_iteration >= max_iterations - 1:
                print(f"⚠️ [DEBUG] 达到最大迭代次数，当前分数: {overall_score}")
                break
            
            print(f"🔄 [DEBUG] 质量不达标 ({overall_score} < {min_score_threshold})，开始第 {current_iteration + 1} 次改进")
            
            # 发送质量警报
            await self.send_quality_alert({
                "iteration": current_iteration + 1,
                "current_score": overall_score,
                "threshold": min_score_threshold,
                "quality_issues": quality_result.data.get("detailed_scores", {})
            })
            
            # 基于质量反馈重新生成内容
            improvement_context = {
                "previous_content": current_content.data,
                "quality_feedback": quality_result.data,
                "improvement_suggestions": quality_result.data.get("suggestions", []),
                "target_score": min_score_threshold,
                "iteration": current_iteration + 1,
                "user_ending": input_data.get("ending", ""),
                "knowledge_base": input_data.get("knowledge_base", {}),
                "strategy": input_data.get("strategy", {})
            }
            
            print(f"🔄 [DEBUG] 发送改进请求给内容生成Agent")
            
            # 向内容生成Agent发送改进反馈
            await self.agents['content_generator'].send_feedback(
                "content_generator",
                {
                    "type": "improvement_request",
                    "quality_issues": quality_result.data.get("detailed_scores", {}),
                    "suggestions": quality_result.data.get("suggestions", []),
                    "target_score": min_score_threshold
                }
            )
            
            # 重新生成内容
            current_content = await self._generate_content(improvement_context)
            
            if not current_content.success:
                print(f"❌ [DEBUG] 第 {current_iteration + 1} 次内容重新生成失败")
                break
                
            print(f"✅ [DEBUG] 第 {current_iteration + 1} 次内容重新生成完成")
            current_iteration += 1
        
        # 最终质量评估
        final_quality_result = await self._assess_quality(current_content.data)
        final_score = final_quality_result.data.get("overall_score", 0) if final_quality_result.data else 0
        
        print(f"🏁 [DEBUG] 迭代优化完成，最终分数: {final_score}, 迭代次数: {current_iteration}")
        
        return current_content, final_quality_result

    async def _generate_content_with_feedback(self, context: Dict[str, Any]) -> AgentResult:
        """基于反馈生成改进内容"""
        print("🔄 [DEBUG] 基于反馈重新生成内容")
        
        # 检查是否有改进建议
        suggestions = context.get("improvement_suggestions", [])
        quality_issues = context.get("quality_feedback", {}).get("detailed_scores", {})
        
        # 构建改进提示
        improvement_prompt = self._build_improvement_prompt(suggestions, quality_issues)
        context["improvement_prompt"] = improvement_prompt
        
        # 调用内容生成Agent
        return await self.agents['content_generator'].process(context)
    
    def _build_improvement_prompt(self, suggestions: List[str], quality_issues: Dict[str, Any]) -> str:
        """构建改进提示"""
        prompt_parts = ["基于以下质量反馈进行改进：\n"]
        
        if suggestions:
            prompt_parts.append("### 改进建议：")
            for i, suggestion in enumerate(suggestions, 1):
                prompt_parts.append(f"{i}. {suggestion}")
            prompt_parts.append("")
        
        if quality_issues:
            prompt_parts.append("### 质量问题：")
            for dimension, score in quality_issues.items():
                if isinstance(score, (int, float)) and score < 7.0:
                    prompt_parts.append(f"- {dimension}: {score}/10 (需要改进)")
            prompt_parts.append("")
        
        prompt_parts.append("请重点关注以上问题，生成更高质量的内容。")
        
        return "\n".join(prompt_parts)
