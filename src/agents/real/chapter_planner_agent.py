#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
章节规划Agent
负责81-120回的详细编排规划
@author: heai
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..base import BaseAgent, AgentResult
from ..gpt5_client import get_gpt5_client
from ...config.settings import Settings
from ...prompts.literary_prompts import get_literary_prompts


class ChapterPlannerAgent(BaseAgent):
    """章节规划Agent - 负责81-120回的详细编排"""

    def __init__(self, settings: Settings):
        super().__init__("章节规划Agent", {"task": "章节编排"})
        self.settings = settings
        self.gpt5_client = get_gpt5_client(settings)
        self.prompts = get_literary_prompts()
        
        # 添加mock模式开关（用于开发测试）
        self.use_mock = getattr(settings, 'use_mock_chapter_planner', False)
        
        # 添加Prompt版本选择（v1=复杂版, v2=简化版）
        self.prompt_version = getattr(settings, 'chapter_planner_prompt_version', 'v2')

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        主处理流程

        输入:
            - overall_strategy: 总体策略
            - knowledge_base: 前80回分析数据
            - user_ending: 用户理想结局
            - chapters_count: 要规划的章节数 (默认40)
            - start_chapter: 起始章节号 (默认81)

        输出:
            - chapters_plan: 完整的章节编排方案
        """
        self.update_status("planning")

        try:
            # 提取输入数据
            overall_strategy = input_data.get("overall_strategy", {})
            knowledge_base = input_data.get("knowledge_base", {})
            user_ending = input_data.get("user_ending", "")
            chapters_count = input_data.get("chapters_count", 40)
            start_chapter = input_data.get("start_chapter", 81)

            # 步骤1: 规划全局结构
            self.update_status("planning_global_structure")
            global_structure = await self._plan_global_structure(
                overall_strategy, knowledge_base, user_ending, chapters_count, start_chapter
            )

            # 步骤2: 规划每个章节的详细内容
            self.update_status("planning_chapter_details")
            chapters_details = await self._plan_all_chapters(
                global_structure, knowledge_base, start_chapter, chapters_count
            )

            # 步骤3: 分配角色，确保合理分布
            self.update_status("distributing_characters")
            character_distribution = self._distribute_characters(chapters_details)

            # 步骤4: 验证章节间的连贯性
            self.update_status("validating_consistency")
            validation_result = self._validate_consistency(chapters_details)

            # 整合最终结果
            chapters_plan = {
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "user_ending": user_ending,
                    "total_chapters": chapters_count,
                    "start_chapter": start_chapter,
                    "end_chapter": start_chapter + chapters_count - 1
                },
                "global_structure": global_structure,
                "chapters": chapters_details,
                "character_distribution": character_distribution,
                "validation": validation_result
            }

            self.update_status("completed")

            return AgentResult(
                success=True,
                data=chapters_plan,
                message=f"成功规划{chapters_count}回章节内容"
            )

        except Exception as e:
            self.update_status("error")
            return self.handle_error(e)

    async def _plan_global_structure(
        self,
        overall_strategy: Dict[str, Any],
        knowledge_base: Dict[str, Any],
        user_ending: str,
        chapters_count: int,
        start_chapter: int
    ) -> Dict[str, Any]:
        """
        规划全局结构（四阶段划分、主要剧情线）

        Returns:
            {
                "narrative_phases": {...},  # 叙事阶段划分
                "major_plotlines": [...],   # 主要剧情线
                "timeline": {...}            # 时间线规划
            }
        """
        # 如果启用mock模式，直接返回默认结构
        if self.use_mock:
            print("🎭 [MOCK模式] 使用模拟全局结构")
            return self._create_default_global_structure(
                start_chapter, chapters_count, user_ending
            )
        
        # 初始化缓存管理器
        from ...utils.cache import CacheManager
        cache_manager = CacheManager(default_ttl=7200)  # 缓存2小时
        
        # 生成缓存键
        cache_key = self._generate_cache_key(
            "global_structure",
            overall_strategy, 
            knowledge_base, 
            user_ending, 
            chapters_count, 
            start_chapter
        )
        
        # 尝试从缓存获取结果
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            print("🎯 [CACHE] 命中全局结构缓存")
            return cached_result

        # 构建prompt
        system_prompt, user_prompt = self.prompts.create_custom_prompt(
            "chapter_planner_global",
            {
                "overall_strategy": json.dumps(overall_strategy, ensure_ascii=False, indent=2),
                "user_ending": user_ending,
                "chapters_count": chapters_count,
                "start_chapter": start_chapter,
                "end_chapter": start_chapter + chapters_count - 1,
                "knowledge_summary": self._extract_knowledge_summary(knowledge_base)
            }
        )

        # 调用GPT-5生成全局结构
        result = await self.gpt5_client.generate_with_retry(
            prompt=user_prompt,
            system_message=system_prompt,
            temperature=0.7,
            max_tokens=4000
        )

        # 检查是否成功
        if not result.get("success", False):
            print(f"⚠️  GPT-5调用失败，使用默认全局结构: {result.get('error', 'Unknown error')}")
            default_result = self._create_default_global_structure(
                start_chapter, chapters_count, user_ending
            )
            # 也缓存默认结果
            cache_manager.set(cache_key, default_result)
            return default_result

        # 解析并验证结果
        response_content = result.get("content", "")
        global_structure = self._parse_json_from_response(
            response_content, 
            context="global_structure"
        )
        
        if global_structure:
            # 缓存成功的结果
            cache_manager.set(cache_key, global_structure)
            return global_structure
        else:
            print(f"⚠️  JSON解析失败，使用默认全局结构")
            print(f"📄 原始响应: {response_content[:200]}...")
            default_result = self._create_default_global_structure(
                start_chapter, chapters_count, user_ending
            )
            # 缓存默认结果
            cache_manager.set(cache_key, default_result)
            return default_result

    def _generate_cache_key(self, operation: str, *args) -> str:
        """生成缓存键"""
        import hashlib
        import json
        
        cache_input = {
            'operation': operation,
            'args': [json.dumps(arg, sort_keys=True, default=str) for arg in args]
        }
        serialized = json.dumps(cache_input, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()

    async def _plan_all_chapters(
        self,
        global_structure: Dict[str, Any],
        knowledge_base: Dict[str, Any],
        start_chapter: int,
        chapters_count: int
    ) -> List[Dict[str, Any]]:
        """
        规划所有章节的详细内容

        Returns:
            List of chapter details
        """
        chapters_details = []

        # 逐个规划每一回（可以考虑并发优化）
        for i in range(chapters_count):
            chapter_num = start_chapter + i

            # 规划单个章节
            chapter_detail = await self._plan_single_chapter(
                chapter_num=chapter_num,
                global_structure=global_structure,
                knowledge_base=knowledge_base,
                previous_chapter=chapters_details[-1] if chapters_details else None
            )

            chapters_details.append(chapter_detail)

            # 每规划5回打印一次进度
            if (i + 1) % 5 == 0:
                print(f"已规划 {i + 1}/{chapters_count} 回")

        return chapters_details

    async def _plan_single_chapter(
        self,
        chapter_num: int,
        global_structure: Dict[str, Any],
        knowledge_base: Dict[str, Any],
        previous_chapter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        规划单个章节的详细内容

        Returns:
            {
                "chapter_number": 81,
                "chapter_title": {...},
                "narrative_phase": "setup",
                "main_characters": [...],
                "main_plot_points": [...],
                "subplot_connections": [...],
                "literary_elements": {...},
                "chapter_metadata": {...}
            }
        """
        # 确定当前章节所处的叙事阶段
        narrative_phase = self._get_narrative_phase(chapter_num, global_structure)

        # 如果启用mock模式，直接返回默认结构
        if self.use_mock:
            print(f"🎭 [MOCK模式] 第{chapter_num}回使用模拟结构")
            return self._create_enhanced_mock_chapter_detail(chapter_num, narrative_phase, previous_chapter)

        # 找到相关的剧情线
        related_plotlines = self._get_related_plotlines(chapter_num, global_structure)

        # 根据prompt版本选择不同的模板
        prompt_name = f"chapter_planner_detail_{self.prompt_version}" if self.prompt_version == 'v2' else "chapter_planner_detail"
        
        # 构建prompt参数（V2版本使用简化参数）
        if self.prompt_version == 'v2':
            prompt_params = {
                "chapter_num": chapter_num,
                "narrative_phase": narrative_phase,
                "related_plotlines": self._format_plotlines_simple(related_plotlines),
                "previous_chapter_summary": self._get_chapter_summary(previous_chapter) if previous_chapter else "第80回的日常场景"
            }
        else:
            prompt_params = {
                "chapter_num": chapter_num,
                "narrative_phase": narrative_phase,
                "related_plotlines": json.dumps(related_plotlines, ensure_ascii=False, indent=2),
                "previous_chapter_summary": self._get_chapter_summary(previous_chapter) if previous_chapter else "第80回的日常场景",
                "global_context": json.dumps(global_structure.get("narrative_phases", {}), ensure_ascii=False),
                "knowledge_base": self._extract_relevant_knowledge(knowledge_base, chapter_num)
            }
        
        # 构建prompt
        system_prompt, user_prompt = self.prompts.create_custom_prompt(
            prompt_name,
            prompt_params
        )

        # 调用GPT-5生成章节详细规划
        result = await self.gpt5_client.generate_with_retry(
            prompt=user_prompt,
            system_message=system_prompt,
            temperature=0.7,
            max_tokens=4000
        )

        # 检查是否成功
        if not result.get("success", False):
            print(f"⚠️  第{chapter_num}回规划失败，使用默认结构: {result.get('error', 'Unknown error')}")
            return self._create_default_chapter_detail(chapter_num, narrative_phase)

        # 解析结果
        response_content = result.get("content", "")
        chapter_detail = self._parse_json_from_response(
            response_content,
            context=f"chapter_{chapter_num}"
        )
        
        if chapter_detail:
            chapter_detail["chapter_number"] = chapter_num
            return chapter_detail
        else:
            print(f"⚠️  第{chapter_num}回JSON解析失败，使用默认结构")
            return self._create_default_chapter_detail(chapter_num, narrative_phase)

    def _distribute_characters(self, chapters_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分配角色，确保主要角色在40回中合理分布

        Returns:
            {
                "character_distribution": {
                    "贾宝玉": {
                        "total_appearances": 40,
                        "primary_role_chapters": [...],
                        "secondary_role_chapters": [...],
                        "absent_chapters": []
                    },
                    ...
                }
            }
        """
        character_stats = {}

        # 统计每个角色的出场情况
        for chapter in chapters_details:
            chapter_num = chapter.get("chapter_number")
            main_characters = chapter.get("main_characters", [])

            for char_info in main_characters:
                char_name = char_info.get("name", "")
                importance = char_info.get("importance", "minor")

                if char_name not in character_stats:
                    character_stats[char_name] = {
                        "total_appearances": 0,
                        "primary_role_chapters": [],
                        "secondary_role_chapters": [],
                        "minor_role_chapters": []
                    }

                character_stats[char_name]["total_appearances"] += 1

                if importance == "primary":
                    character_stats[char_name]["primary_role_chapters"].append(chapter_num)
                elif importance == "secondary":
                    character_stats[char_name]["secondary_role_chapters"].append(chapter_num)
                else:
                    character_stats[char_name]["minor_role_chapters"].append(chapter_num)

        # 计算缺席章节
        all_chapters = [ch.get("chapter_number") for ch in chapters_details]
        for char_name, stats in character_stats.items():
            appeared_chapters = (
                stats["primary_role_chapters"] +
                stats["secondary_role_chapters"] +
                stats["minor_role_chapters"]
            )
            stats["absent_chapters"] = [ch for ch in all_chapters if ch not in appeared_chapters]

        return {
            "character_distribution": character_stats,
            "total_characters": len(character_stats),
            "distribution_balance": self._calculate_distribution_balance(character_stats)
        }

    def _validate_consistency(self, chapters_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证章节间的连贯性

        Returns:
            {
                "is_consistent": True/False,
                "issues": [...],
                "suggestions": [...]
            }
        """
        issues = []
        suggestions = []

        # 检查1: 章节号连续性
        chapter_numbers = [ch.get("chapter_number") for ch in chapters_details]
        if chapter_numbers != sorted(chapter_numbers):
            issues.append("章节号不连续")

        # 检查2: 每回都有标题
        for chapter in chapters_details:
            if not chapter.get("chapter_title"):
                issues.append(f"第{chapter.get('chapter_number')}回缺少标题")

        # 检查3: 每回都有主要角色
        for chapter in chapters_details:
            if not chapter.get("main_characters"):
                issues.append(f"第{chapter.get('chapter_number')}回缺少主要角色")

        # 检查4: 每回都有主要情节点
        for chapter in chapters_details:
            if not chapter.get("main_plot_points"):
                issues.append(f"第{chapter.get('chapter_number')}回缺少主要情节点")

        # 检查5: 前后章节的衔接
        for i in range(1, len(chapters_details)):
            prev_chapter = chapters_details[i - 1]
            curr_chapter = chapters_details[i]

            prev_setup = prev_chapter.get("chapter_metadata", {}).get("next_chapter_setup", "")
            curr_link = curr_chapter.get("chapter_metadata", {}).get("previous_chapter_link", "")

            if not prev_setup or not curr_link:
                suggestions.append(f"第{prev_chapter.get('chapter_number')}回与第{curr_chapter.get('chapter_number')}回的衔接可以更明确")

        return {
            "is_consistent": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "total_checks": 5,
            "passed_checks": 5 - len(issues)
        }

    # ========== 辅助方法 ==========

    def _parse_json_from_response(self, response_content: str, context: str = "") -> Optional[Dict[str, Any]]:
        """
        从GPT响应中智能解析JSON
        
        Args:
            response_content: GPT返回的原始内容
            context: 上下文信息（用于调试）
            
        Returns:
            解析后的JSON字典，如果失败则返回None
        """
        # 保存原始响应以供调试
        if hasattr(self, '_debug_responses'):
            self._debug_responses.append({
                "context": context,
                "content": response_content,
                "timestamp": datetime.now().isoformat()
            })
        
        # 策略1: 直接解析
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            pass
        
        # 策略2: 提取markdown代码块（支持多种格式）
        patterns = [
            r'```json\s*(.*?)\s*```',  # ```json ... ```
            r'```\s*(\{.*?\})\s*```',  # ``` {...} ``` （无语言标识）
            r'```\s*(\[.*?\])\s*```'   # ``` [...] ``` （数组格式）
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_content, re.DOTALL)
            if matches:
                for match in matches:
                    try:
                        return json.loads(match.strip())
                    except json.JSONDecodeError:
                        continue
        
        # 策略3: 查找第一个 { 和最后一个 } 或 [ 和 ]
        # 优先查找对象结构
        obj_start = response_content.find('{')
        obj_end = response_content.rfind('}')
        if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
            json_str = response_content[obj_start:obj_end+1]
            parsed = self._try_parse_json_with_fixes(json_str, context)
            if parsed is not None:
                return parsed
        
        # 查找数组结构
        arr_start = response_content.find('[')
        arr_end = response_content.rfind(']')
        if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
            json_str = response_content[arr_start:arr_end+1]
            parsed = self._try_parse_json_with_fixes(json_str, context)
            if parsed is not None:
                return parsed
        
        # 策略4: 查找嵌套结构（可能有多对{}）
        brace_pairs = self._find_matching_braces(response_content)
        for start, end in brace_pairs:
            json_str = response_content[start:end+1]
            parsed = self._try_parse_json_with_fixes(json_str, context)
            if parsed is not None:
                return parsed
        
        # 如果所有策略都失败，保存失败的响应以供调试
        debug_file = Path("output/debug_json_parse_failure.txt")
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n=== {context} - {datetime.now()} ===\n")
            f.write(f"Content:\n{response_content}\n")
        
        print(f"⚠️  JSON解析失败已保存到: {debug_file}")
        return None

    def _try_parse_json_with_fixes(self, json_str: str, context: str) -> Optional[Dict[str, Any]]:
        """
        尝试修复并解析JSON字符串
        """
        # 原始尝试
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # 尝试修复常见问题
        fixes = [
            # 1. 移除注释
            lambda s: re.sub(r'//.*?\n', '\n', s),
            # 2. 修复尾随逗号
            lambda s: re.sub(r',(\s*[}\]])', r'\1', s),
            # 3. 修复单引号（更谨慎的替换）
            lambda s: re.sub(r"'([^']*)':", r'"\1":', s),  # 修复键名
            lambda s: re.sub(r":\s*'([^']*)'", r': "\1"', s),  # 修复字符串值
            # 4. 修复未转义的引号（在字符串值中）
            lambda s: re.sub(r':\s*"([^"]*)"([^},\]])', lambda m: f': "{m.group(1).replace(chr(0), "")}"{m.group(2)}', s.replace('"', chr(0)).replace("'", '"').replace(chr(0), '"')),
        ]
        
        fixed_str = json_str
        for fix in fixes:
            try:
                fixed_str = fix(fixed_str)
                result = json.loads(fixed_str)
                return result
            except json.JSONDecodeError:
                continue
        
        # 如果仍然失败，尝试更高级的修复
        return self._advanced_json_fix(fixed_str, context)

    def _advanced_json_fix(self, json_str: str, context: str) -> Optional[Dict[str, Any]]:
        """
        高级JSON修复方法
        """
        try:
            # 尝试使用更宽松的JSON解析器
            import json5  # 如果有json5模块
            return json5.loads(json_str)
        except ImportError:
            pass
        except Exception:
            pass
        
        # 手动修复一些复杂情况
        try:
            # 修复包含未转义引号的字符串值
            fixed_str = self._fix_unescaped_quotes(json_str)
            return json.loads(fixed_str)
        except json.JSONDecodeError:
            pass
        
        return None

    def _fix_unescaped_quotes(self, json_str: str) -> str:
        """
        修复JSON字符串中未转义的引号
        """
        # 这是一个简化的修复方法
        # 在实际应用中，可能需要更复杂的解析
        try:
            # 尝试逐字符解析，修复未转义的引号
            result = []
            in_string = False
            escape_next = False
            
            for i, char in enumerate(json_str):
                if escape_next:
                    result.append(char)
                    escape_next = False
                    continue
                    
                if char == '\\':
                    result.append(char)
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    
                if char == '"' and in_string and i > 0 and json_str[i-1] != '\\' and i < len(json_str) - 1:
                    # 检查是否是在字符串中间的引号，可能需要转义
                    # 这里简化处理，实际上需要更复杂的逻辑
                    pass
                    
                result.append(char)
            
            return ''.join(result)
        except:
            # 如果修复失败，返回原始字符串
            return json_str

    def _find_matching_braces(self, text: str) -> List[tuple]:
        """
        查找文本中匹配的大括号对
        返回 [(start, end), ...] 的列表
        """
        results = []
        stack = []
        
        for i, char in enumerate(text):
            if char == '{':
                stack.append(i)
            elif char == '}' and stack:
                start = stack.pop()
                if not stack:  # 只记录最外层的匹配对
                    results.append((start, i))
        
        # 按大小排序，优先返回较大的匹配对（更可能是完整的JSON对象）
        results.sort(key=lambda x: x[1] - x[0], reverse=True)
        return results

    def _extract_knowledge_summary(self, knowledge_base: Dict[str, Any]) -> str:
        """提取知识库摘要"""
        summary_parts = []

        if "characters" in knowledge_base:
            char_count = len(knowledge_base["characters"])
            summary_parts.append(f"主要人物: {char_count}位")

        if "relationships" in knowledge_base:
            rel_count = len(knowledge_base["relationships"])
            summary_parts.append(f"人物关系: {rel_count}条")

        if "plotlines" in knowledge_base:
            plot_count = len(knowledge_base["plotlines"])
            summary_parts.append(f"情节线索: {plot_count}条")

        return ", ".join(summary_parts) if summary_parts else "前80回基本信息"

    def _extract_relevant_knowledge(self, knowledge_base: Dict[str, Any], chapter_num: int) -> str:
        """提取与当前章节相关的知识"""
        # 简化版本，返回主要人物列表
        characters = knowledge_base.get("characters", {})
        main_chars = ["贾宝玉", "林黛玉", "薛宝钗", "贾母", "王夫人", "贾政"]

        char_info = []
        for char_name in main_chars:
            if char_name in characters:
                char_info.append(f"{char_name}: {characters[char_name].get('description', '重要人物')}")

        return "\n".join(char_info) if char_info else "主要人物信息"

    def _get_narrative_phase(self, chapter_num: int, global_structure: Dict[str, Any]) -> str:
        """获取章节所处的叙事阶段"""
        phases = global_structure.get("narrative_phases", {})

        for phase_name, phase_info in phases.items():
            chapters = phase_info.get("chapters", [])
            if chapter_num in chapters:
                return phase_name

        # 默认分配
        if chapter_num <= 85:
            return "setup"
        elif chapter_num <= 100:
            return "development"
        elif chapter_num <= 115:
            return "climax"
        else:
            return "resolution"

    def _get_related_plotlines(self, chapter_num: int, global_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取与当前章节相关的剧情线"""
        plotlines = global_structure.get("major_plotlines", [])
        related = []

        for plotline in plotlines:
            involved_chapters = plotline.get("chapters_involved", [])
            if chapter_num in involved_chapters:
                related.append(plotline)

        return related

    def _get_chapter_summary(self, chapter: Dict[str, Any]) -> str:
        """获取章节摘要（兼容V1和V2格式）"""
        if not chapter:
            return "无"

        chapter_num = chapter.get("chapter_number", "")
        title = chapter.get("chapter_title", {})
        title_str = f"{title.get('first_part', '')} {title.get('second_part', '')}"

        # 兼容V1和V2格式
        plot_points = chapter.get("main_plot_points", []) or chapter.get("plot_points", [])
        plot_summary = ", ".join([p.get("event", "")[:20] for p in plot_points[:2]])

        return f"第{chapter_num}回 {title_str} - {plot_summary}"
    
    def _format_plotlines_simple(self, plotlines: list) -> str:
        """将剧情线列表格式化为简单的文本描述（V2版本用）"""
        if not plotlines:
            return "无特定剧情线"
        
        lines = []
        for pl in plotlines[:3]:  # 最多3条
            name = pl.get("name", "未命名")
            arc = pl.get("narrative_arc", "")
            lines.append(f"- {name}: {arc}")
        
        return "\n".join(lines)

    def _create_default_global_structure(
        self,
        start_chapter: int,
        chapters_count: int,
        user_ending: str
    ) -> Dict[str, Any]:
        """创建默认的全局结构（当GPT-5调用失败时使用）"""
        end_chapter = start_chapter + chapters_count - 1

        # 简单的四阶段划分
        setup_end = start_chapter + int(chapters_count * 0.125) - 1  # 12.5%
        development_end = start_chapter + int(chapters_count * 0.5) - 1  # 50%
        climax_end = start_chapter + int(chapters_count * 0.875) - 1  # 87.5%

        return {
            "narrative_phases": {
                "setup": {
                    "chapters": list(range(start_chapter, setup_end + 1)),
                    "description": "铺垫阶段：暗流涌动，危机初显"
                },
                "development": {
                    "chapters": list(range(setup_end + 1, development_end + 1)),
                    "description": "发展阶段：矛盾激化，命运转折"
                },
                "climax": {
                    "chapters": list(range(development_end + 1, climax_end + 1)),
                    "description": "高潮阶段：家族崩塌，人物抉择"
                },
                "resolution": {
                    "chapters": list(range(climax_end + 1, end_chapter + 1)),
                    "description": "结局阶段：尘埃落定，各有归宿"
                }
            },
            "major_plotlines": [
                {
                    "id": "plotline_001",
                    "name": "宝黛爱情线",
                    "priority": "primary",
                    "chapters_involved": list(range(start_chapter, end_chapter + 1, 3)),
                    "narrative_arc": "相思→误会→和解→考验→结局"
                },
                {
                    "id": "plotline_002",
                    "name": "贾府衰败线",
                    "priority": "primary",
                    "chapters_involved": list(range(start_chapter + 1, end_chapter + 1, 4)),
                    "narrative_arc": "预兆→危机→崩溃→覆灭"
                }
            ]
        }

    def _create_default_chapter_detail(self, chapter_num: int, narrative_phase: str) -> Dict[str, Any]:
        """创建默认的章节详细规划（当GPT-5调用失败时使用）"""
        return {
            "chapter_number": chapter_num,
            "chapter_title": {
                "first_part": f"第{chapter_num}回上",
                "second_part": f"第{chapter_num}回下"
            },
            "narrative_phase": narrative_phase,
            "main_characters": [
                {
                    "name": "贾宝玉",
                    "role": "protagonist",
                    "importance": "primary",
                    "key_scenes": ["待规划"],
                    "emotional_arc": "待规划"
                }
            ],
            "main_plot_points": [
                {
                    "sequence": 1,
                    "event": "待规划的情节点",
                    "type": "待定",
                    "location": "待定",
                    "participants": ["待定"]
                }
            ],
            "subplot_connections": [],
            "literary_elements": {
                "poetry_count": 1,
                "symbolism": [],
                "foreshadowing": []
            },
            "chapter_metadata": {
                "estimated_length": 2500,
                "previous_chapter_link": "待规划",
                "next_chapter_setup": "待规划"
            }
        }
    
    def _create_enhanced_mock_chapter_detail(self, chapter_num: int, narrative_phase: str, previous_chapter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建增强版的模拟章节规划（用于mock模式测试）"""
        
        # 模拟的回目标题库
        mock_titles = [
            ("暗香疏影探春事", "落絮纷纷忆旧情"),
            ("病榻诗成伤往日", "园中絮语话新愁"),
            ("宝玉探病怀真意", "黛玉题诗寄深情"),
            ("荣府渐衰人心散", "怡红未改旧时颜"),
            ("贾母垂泪话家运", "宝钗持重理中馈")
        ]
        
        # 选择一个标题（基于章节号）
        title_idx = (chapter_num - 81) % len(mock_titles)
        title = mock_titles[title_idx]
        
        # 模拟主要角色
        all_characters = ["贾宝玉", "林黛玉", "薛宝钗", "贾母", "王夫人", "贾政", "史湘云", "探春"]
        # 根据章节号选择不同的角色组合
        char_offset = (chapter_num - 81) % 3
        main_chars = all_characters[char_offset:char_offset+3]
        
        return {
            "chapter_number": chapter_num,
            "chapter_title": {
                "first_part": title[0],
                "second_part": title[1]
            },
            "narrative_phase": narrative_phase,
            "main_characters": [
                {
                    "name": char_name,
                    "role": "protagonist" if char_name in ["贾宝玉", "林黛玉"] else "supporting",
                    "importance": "primary" if i == 0 else "secondary",
                    "emotional_arc": f"{char_name}在本回中经历情感变化"
                } for i, char_name in enumerate(main_chars)
            ],
            "main_plot_points": [
                {
                    "sequence": 1,
                    "event": f"第{chapter_num}回主要情节点一",
                    "type": "daily_life",
                    "location": "大观园",
                    "participants": main_chars[:2]
                },
                {
                    "sequence": 2,
                    "event": f"第{chapter_num}回主要情节点二",
                    "type": "conflict",
                    "location": "荣禧堂",
                    "participants": main_chars[1:]
                }
            ],
            "subplot_connections": [
                {
                    "plotline_name": "宝黛爱情线",
                    "progress_description": "本回推进宝黛感情发展"
                }
            ],
            "literary_elements": {
                "poetry_count": 1,
                "symbolism": ["花落象征命运"],
                "foreshadowing": ["暗示后续变故"]
            },
            "chapter_metadata": {
                "estimated_length": 2500,
                "previous_chapter_link": f"承接第{chapter_num-1}回" if chapter_num > 81 else "承接第80回",
                "next_chapter_setup": f"为第{chapter_num+1}回铺垫"
            }
        }

    def _calculate_distribution_balance(self, character_stats: Dict[str, Any]) -> float:
        """计算角色分布的平衡度（0-1，越接近1越平衡）"""
        if not character_stats:
            return 0.0

        # 简单计算：主要角色的出场频率方差
        main_characters = ["贾宝玉", "林黛玉", "薛宝钗"]
        appearances = []

        for char_name in main_characters:
            if char_name in character_stats:
                appearances.append(character_stats[char_name]["total_appearances"])

        if not appearances:
            return 0.0

        # 计算平均值和方差
        avg = sum(appearances) / len(appearances)
        variance = sum((x - avg) ** 2 for x in appearances) / len(appearances)

        # 归一化到0-1（方差越小，平衡度越高）
        balance_score = 1.0 / (1.0 + variance / 100)

        return round(balance_score, 2)
