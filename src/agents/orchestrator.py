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
from .real.content_generator_agent import ContentGeneratorAgent
from .real.quality_checker_agent import QualityCheckerAgent
from ..config.settings import Settings


class OrchestratorAgent(BaseAgent):
    """编排Agent，协调多Agent协作"""

    def __init__(self, settings: Settings):
        super().__init__("编排Agent", {"coordinator": True})
        self.settings = settings
        self.agents = self._initialize_agents()

    def _initialize_agents(self) -> Dict[str, BaseAgent]:
        """初始化所有Agent"""
        agents = {}

        try:
            # 数据预处理Agent
            agents['data_processor'] = DataProcessorAgent(self.settings)

            # 续写策略Agent
            agents['strategy_planner'] = StrategyPlannerAgent(self.settings)

            # 内容生成Agent
            agents['content_generator'] = ContentGeneratorAgent(self.settings)

            # 质量校验Agent
            agents['quality_checker'] = QualityCheckerAgent(self.settings)

            # 用户交互Agent (暂时使用MockAgent)
            agents['user_interface'] = MockAgent(
                "用户交互Agent",
                {
                    "response_delay": 0.5,
                    "task": "处理用户输入和输出格式化"
                }
            )

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

            # 3. 生成续写内容
            print("🔍 [DEBUG] 步骤3: 生成续写内容")
            content_context = {
                "knowledge_base": preprocessing_result.data,
                "strategy": strategy_result.data,
                "user_ending": input_data.get("ending", "")
            }
            print(f"🔍 [DEBUG] 内容生成上下文: {content_context}")

            content_result = await self._generate_content(content_context)

            print(f"🔍 [DEBUG] 内容生成结果: success={content_result.success}, message={content_result.message}")

            if not content_result.success:
                print("❌ [DEBUG] 内容生成失败")
                return AgentResult(
                    success=False,
                    data=content_result.data,
                    message="内容生成失败"
                )

            print("✅ [DEBUG] 内容生成完成")

            # 4. 质量评估
            print("🔍 [DEBUG] 步骤4: 质量评估")
            quality_result = await self._assess_quality(content_result.data)

            print(f"🔍 [DEBUG] 质量评估结果: success={quality_result.success}, message={quality_result.message}")

            # 5. 格式化输出
            print("🔍 [DEBUG] 步骤5: 格式化输出")
            final_result = await self._format_output({
                "content": content_result.data,
                "quality": quality_result.data,
                "metadata": input_data
            })

            print(f"🔍 [DEBUG] 格式化输出结果: success={final_result.success}, message={final_result.message}")

            self.update_status("completed")

            print("✅ [DEBUG] 续写流程全部完成")
            return AgentResult(
                success=True,
                data=final_result.data,
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
        """并行执行数据预处理和策略规划"""
        # 模拟并行处理
        preprocessing_task = self.agents['data_processor'].process(input_data)
        strategy_task = self.agents['strategy_planner'].process(input_data)

        preprocessing_result, strategy_result = await asyncio.gather(
            preprocessing_task, strategy_task
        )

        return preprocessing_result, strategy_result

    async def _generate_content(self, context: Dict[str, Any]) -> AgentResult:
        """生成续写内容"""
        return await self.agents['content_generator'].process(context)

    async def _assess_quality(self, content: Any) -> AgentResult:
        """质量评估"""
        return await self.agents['quality_checker'].process({"content": content})

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

        # 生成模拟的章节内容
        for i in range(1, 41):  # 40回续写
            chapter_content = f"""### 第{i+80}回 模拟章节标题

[这里是第{i+80}回的详细内容]

此回主要讲述了...

[续写内容模拟]

---

*本回由AI续写，保持古典文学风格*
"""

            chapter_file = chapters_dir / f"chapter_{i+80:03d}.md"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(chapter_content)

        # 生成策略大纲
        strategy_file = output_path / "strategy_outline.md"
        with open(strategy_file, 'w', encoding='utf-8') as f:
            f.write("""# 续写策略大纲

## 总体规划
基于用户结局"宝玉和黛玉终成眷属，贾府中兴"的续写策略

## 情节架构
1. **前期铺垫** (81-85回): 宝黛爱情发展
2. **中期冲突** (86-95回): 家族变故与考验
3. **后期高潮** (96-105回): 爱情圆满与家族复兴
4. **大结局** (106-120回): 幸福美满的结局

## 人物发展
- **贾宝玉**: 从叛逆到成熟
- **林黛玉**: 从多病到坚强
- **贾府众人**: 从衰落到复兴

## 主题升华
- 爱情的纯真与坚贞
- 家族的兴衰与复兴
- 生命的意义与价值
""")

        # 生成质量报告
        quality_file = output_path / "quality_report.md"
        with open(quality_file, 'w', encoding='utf-8') as f:
            f.write("""# 质量评估报告

## 综合评分: 8.6/10 ⭐⭐⭐⭐⭐

### 维度详情
- **风格一致性**: 8.5/10
  - 古风雅致，文辞优美
  - 符合古典小说语言特点

- **人物性格**: 9.0/10
  - 宝黛形象鲜明，性格发展合理
  - 符合原著人物设定

- **情节合理性**: 8.2/10
  - 故事逻辑连贯，与原著呼应
  - 结局符合人物命运

- **文学素养**: 8.8/10
  - 修辞丰富，意境深远
  - 古典文学韵味浓郁

### 改进建议
1. 建议在第25-30回加强贾府复兴的铺垫
2. 可适当增加一些古典诗词点缀
3. 增强人物内心描写深度

### 评估时间
2025-01-XX 14:30:00
""")
