#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据预处理Agent
负责分析红楼梦文本，提取人物关系和知识图谱
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict, Counter
import jieba
import jieba.posseg as pseg

from ..base import BaseAgent, AgentResult
from ..gpt5_client import get_gpt5_client
from ...config.settings import Settings
from ...prompts.literary_prompts import get_literary_prompts


class DataProcessorAgent(BaseAgent):
    """数据预处理Agent"""

    def __init__(self, settings: Settings):
        super().__init__("数据预处理Agent", {"task": "文本分析和知识提取"})
        self.settings = settings
        self.gpt5_client = get_gpt5_client(settings)
        self.prompts = get_literary_prompts()

        # 加载中文分词词典
        self._load_chinese_dictionary()

        # 缓存拆分后的章节，避免重复拆分
        self._chapters_cache = None
        self._chapters_dir = Path("data/processed/chapters")

        # 人物关系网络
        self.character_network = defaultdict(set)
        self.character_traits = {}
        self.plot_events = []
        self.themes = set()

    def _load_chinese_dictionary(self):
        """加载中文分词词典"""
        try:
            # 添加红楼梦专用词汇
            dream_words = [
                "贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母",
                "贾政", "王夫人", "贾琏", "贾珍", "贾蓉",
                "史湘云", "妙玉", "贾探春", "贾迎春", "贾惜春",
                "尤二姐", "尤三姐", "秦可卿", "李纨", "平儿",
                "鸳鸯", "袭人", "晴雯", "紫鹃", "小红",
                "茗烟", "焦大", "刘姥姥", "板儿", "贾雨村",
                "甄士隐", "英莲", "香菱", "金钏", "玉钏"
            ]

            for word in dream_words:
                jieba.add_word(word)

        except Exception as e:
            print(f"加载中文词典失败: {e}")

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """处理输入数据"""
        self.update_status("processing")

        try:
            # 读取红楼梦文本
            text_content = await self._load_dream_text()

            if not text_content:
                return AgentResult(
                    success=False,
                    data=None,
                    message="无法加载红楼梦文本"
                )

            # 并行处理多个分析任务
            analysis_results = await asyncio.gather(
                self._analyze_characters(text_content),
                self._analyze_plot_structure(text_content),
                self._extract_themes(text_content),
                self._build_knowledge_graph(text_content)
            )

            # 整合分析结果
            knowledge_base = {
                "characters": analysis_results[0],
                "plot_structure": analysis_results[1],
                "themes": analysis_results[2],
                "knowledge_graph": analysis_results[3],
                "text_statistics": self._calculate_text_statistics(text_content)
            }

            # 保存知识库
            await self._save_knowledge_base(knowledge_base)

            self.update_status("completed")

            return AgentResult(
                success=True,
                data=knowledge_base,
                message="数据预处理完成，知识库构建成功"
            )

        except Exception as e:
            self.update_status("error")
            return self.handle_error(e)

    async def _load_dream_text(self) -> Optional[str]:
        """加载红楼梦文本"""
        try:
            text_path = Path(self.settings.source_file)
            if not text_path.exists():
                print(f"红楼梦文本文件不存在: {text_path}")
                return None

            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return content

        except Exception as e:
            print(f"加载红楼梦文本失败: {e}")
            return None

    async def _analyze_characters(self, text: str) -> Dict[str, Any]:
        """分析人物特征"""
        try:
            # 使用GPT-5进行深度人物分析
            system_msg, user_prompt = self.prompts.create_custom_prompt(
                "data_processor",
                {
                    "character_list": self._extract_character_names(text),
                    "chapter_range": "81-120"
                }
            )

            response = await self.gpt5_client.generate_with_retry(
                prompt=user_prompt,
                system_message=system_msg,
                temperature=0.3,
                max_tokens=2000
            )

            if response["success"]:
                return self._parse_character_analysis(response["content"])
            else:
                return self._fallback_character_analysis(text)

        except Exception as e:
            print(f"人物分析失败: {e}")
            return self._fallback_character_analysis(text)

    def _extract_character_names(self, text: str) -> List[str]:
        """提取人物姓名"""
        # 红楼梦主要人物列表
        main_characters = [
            "贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母",
            "贾政", "王夫人", "贾琏", "贾珍", "贾蓉",
            "史湘云", "妙玉", "贾探春", "贾迎春", "贾惜春"
        ]

        found_characters = []
        for char in main_characters:
            if char in text:
                found_characters.append(char)

        return found_characters[:10]  # 限制数量

    def _parse_character_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """解析人物分析结果"""
        # 这里应该解析GPT-5返回的结构化分析结果
        # 暂时返回模拟结果
        return {
            "宝玉": {
                "性格": "纯真善良，反叛封建礼教",
                "现状": "经历诸多变故，对封建制度失望",
                "发展方向": "寻求精神解脱"
            },
            "黛玉": {
                "性格": "聪慧敏感，多愁善感",
                "现状": "体弱多病，爱情遭遇挫折",
                "发展方向": "坚持纯真爱情理想"
            },
            "宝钗": {
                "性格": "端庄贤惠，世故圆通",
                "现状": "深得贾府长辈喜爱",
                "发展方向": "适应封建社会规范"
            }
        }

    def _fallback_character_analysis(self, text: str) -> Dict[str, Any]:
        """备用人物分析方法"""
        return {
            "宝玉": {"性格": "叛逆纯真", "状态": "觉醒中"},
            "黛玉": {"性格": "聪慧敏感", "状态": "多病"},
            "宝钗": {"性格": "贤惠世故", "状态": "适应良好"}
        }

    async def _analyze_plot_structure(self, text: str) -> Dict[str, Any]:
        """分析情节结构"""
        try:
            # 提取关键情节节点
            chapters = self._split_into_chapters(text)
            plot_structure = {
                "total_chapters": len(chapters),
                "key_events": self._extract_key_events(text),
                "character_arcs": self._analyze_character_arcs(text),
                "themes_progression": self._analyze_theme_progression(text)
            }

            return plot_structure

        except Exception as e:
            print(f"情节分析失败: {e}")
            return {"error": str(e)}

    def _split_into_chapters(self, text: str) -> List[str]:
        """将文本分割为章节（带文件缓存机制）"""
        if self._chapters_cache is None:
            # 首先检查是否已经有拆分好的章节文件
            if self._chapters_dir.exists() and self._load_chapters_from_files():
                print("📚 [DEBUG] 从文件缓存中加载章节数据")
            else:
                print("📚 [DEBUG] 首次拆分章节，保存到文件...")
                self._split_and_save_chapters(text)

        return self._chapters_cache

    def _load_chapters_from_files(self) -> bool:
        """从文件加载章节数据"""
        try:
            chapter_files = sorted(self._chapters_dir.glob("chapter_*.md"))
            if not chapter_files:
                return False

            self._chapters_cache = []
            for chapter_file in chapter_files:
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():  # 只添加非空内容
                        self._chapters_cache.append(content)

            print(f"📚 [DEBUG] 从文件加载了 {len(self._chapters_cache)} 个章节")
            return len(self._chapters_cache) > 0

        except Exception as e:
            print(f"📚 [DEBUG] 从文件加载章节失败: {e}")
            return False

    def _split_and_save_chapters(self, text: str):
        """拆分章节并保存到文件"""
        try:
            # 确保目录存在
            self._chapters_dir.mkdir(parents=True, exist_ok=True)

            # 使用正则表达式查找所有章节标题和内容
            chapter_pattern = r'### 第[一二三四五六七八九十百\d]+回'
            title_matches = list(re.finditer(chapter_pattern, text))

            self._chapters_cache = []

            for i, match in enumerate(title_matches):
                chapter_start = match.start()
                chapter_title = match.group().strip()

                # 确定章节内容的结束位置
                if i < len(title_matches) - 1:
                    next_title_start = title_matches[i + 1].start()
                    chapter_content = text[chapter_start:next_title_start].strip()
                else:
                    # 最后一个章节
                    chapter_content = text[chapter_start:].strip()

                # 移除标题中的###标记，保留"第X回"部分
                clean_title = re.sub(r'^###\s*', '', chapter_title)

                # 构建文件内容
                file_content = f"### {clean_title}\n\n{chapter_content}"

                # 保存到文件
                chapter_num = i + 1  # 章节编号从1开始
                filename = f"chapter_{chapter_num:03d}.md"
                chapter_file = self._chapters_dir / filename

                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write(file_content)

                # 添加到缓存
                self._chapters_cache.append(chapter_content)

            print(f"📚 [DEBUG] 成功拆分并保存了 {len(self._chapters_cache)} 个章节到 {self._chapters_dir}")

        except Exception as e:
            print(f"📚 [DEBUG] 拆分并保存章节失败: {e}")
            import traceback
            print(f"📚 [DEBUG] 错误详情:\n{traceback.format_exc()}")

            # 如果保存失败，回退到简单的内存缓存
            chapter_pattern = r'### 第[一二三四五六七八九十百\d]+回'
            chapters = re.split(chapter_pattern, text)
            self._chapters_cache = [chap for chap in chapters if chap.strip()]

    def _extract_key_events(self, text: str) -> List[Dict[str, Any]]:
        """提取关键事件"""
        # 这里应该使用NLP技术提取关键事件
        # 暂时返回模拟结果
        return [
            {"chapter": 1, "event": "甄士隐梦幻识通灵", "importance": "high"},
            {"chapter": 3, "event": "贾雨村风尘怀闺秀", "importance": "medium"},
            {"chapter": 5, "event": "游幻境指迷十二钗", "importance": "high"}
        ]

    def _analyze_character_arcs(self, text: str) -> Dict[str, Any]:
        """分析人物成长轨迹"""
        return {
            "宝玉": ["纯真少年", "叛逆青年", "觉醒者"],
            "黛玉": ["聪慧少女", "多愁佳人", "坚守理想"],
            "宝钗": ["贤惠小姐", "世故妇人", "适应社会"]
        }

    def _analyze_theme_progression(self, text: str) -> List[str]:
        """分析主题发展"""
        return [
            "爱情与婚姻的冲突",
            "封建礼教的束缚",
            "家族兴衰的宿命",
            "个人觉醒的痛苦"
        ]

    async def _extract_themes(self, text: str) -> List[str]:
        """提取核心主题"""
        themes = [
            "爱情与婚姻",
            "家族兴衰",
            "封建礼教",
            "个人命运",
            "社会批判",
            "艺术与美",
            "人生哲理"
        ]

        # 这里可以添加更复杂的主题提取逻辑
        return themes

    async def _build_knowledge_graph(self, text: str) -> Dict[str, Any]:
        """构建知识图谱"""
        try:
            # 构建人物关系图
            relationships = self._extract_relationships(text)

            # 构建事件时间线
            timeline = self._build_timeline(text)

            # 构建主题网络
            theme_network = self._build_theme_network(text)

            return {
                "relationships": relationships,
                "timeline": timeline,
                "theme_network": theme_network
            }

        except Exception as e:
            print(f"构建知识图谱失败: {e}")
            return {"error": str(e)}

    def _extract_relationships(self, text: str) -> Dict[str, List[str]]:
        """提取人物关系"""
        # 简化的关系提取
        relationships = {
            "贾宝玉": ["林黛玉", "薛宝钗", "贾母", "王夫人", "贾政"],
            "林黛玉": ["贾宝玉", "贾母", "紫鹃", "贾敏"],
            "薛宝钗": ["贾宝玉", "王夫人", "薛姨妈", "香菱"]
        }
        return relationships

    def _build_timeline(self, text: str) -> List[Dict[str, Any]]:
        """构建事件时间线"""
        return [
            {"time": "第一回", "event": "甄士隐梦幻识通灵"},
            {"time": "第三回", "event": "贾雨村风尘怀闺秀"},
            {"time": "第五回", "event": "游幻境指迷十二钗"}
        ]

    def _build_theme_network(self, text: str) -> Dict[str, List[str]]:
        """构建主题网络"""
        return {
            "爱情": ["婚姻", "命运", "纯真"],
            "家族": ["兴衰", "礼教", "权力"],
            "个人": ["觉醒", "反抗", "解脱"]
        }

    def _calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """计算文本统计信息"""
        try:
            # 基本统计
            char_count = len(text)
            word_count = len(jieba.lcut(text))

            # 章节统计
            chapters = self._split_into_chapters(text)
            chapter_count = len(chapters)

            # 人物出现频率
            character_freq = Counter()
            for char in ["贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母"]:
                character_freq[char] = text.count(char)

            return {
                "character_count": char_count,
                "word_count": word_count,
                "chapter_count": chapter_count,
                "character_frequency": dict(character_freq),
                "avg_chapter_length": char_count // chapter_count if chapter_count > 0 else 0
            }

        except Exception as e:
            return {"error": str(e)}

    async def _save_knowledge_base(self, knowledge_base: Dict[str, Any]):
        """保存知识库"""
        try:
            output_path = Path(self.settings.knowledge_base)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存知识库失败: {e}")
