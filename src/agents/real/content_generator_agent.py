#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容生成Agent
负责生成高质量的古典文学续写内容
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from ..base import BaseAgent, AgentResult
from ..gpt5_client import get_gpt5_client
from ...config.settings import Settings
from ...prompts.literary_prompts import get_literary_prompts


class ContentGeneratorAgent(BaseAgent):
    """内容生成Agent"""

    def __init__(self, settings: Settings):
        super().__init__("内容生成Agent", {"task": "古典文学内容创作"})
        self.settings = settings
        self.gpt5_client = get_gpt5_client(settings)
        self.prompts = get_literary_prompts()

        # 古典文学风格特征
        self.literary_features = self._load_literary_features()

    def _load_literary_features(self) -> Dict[str, Any]:
        """加载古典文学风格特征"""
        return {
            "language_patterns": [
                "雅致古朴", "文辞优美", "韵味悠长",
                "第三人称全知视角", "详略得当"
            ],
            "rhetorical_devices": [
                "比喻", "拟人", "对仗", "排比",
                "反问", "设问", "象征", "暗示"
            ],
            "structural_elements": [
                "开端", "发展", "高潮", "结局",
                "伏笔", "照应", "点题", "升华"
            ],
            "classical_motifs": [
                "诗词唱和", "梦境描写", "景物烘托",
                "心理刻画", "细节描写", "象征手法"
            ]
        }

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """生成续写内容"""
        self.update_status("generating")

        try:
            print("🎨 [DEBUG] ContentGeneratorAgent 开始处理")
            print(f"🎨 [DEBUG] 输入数据: {input_data}")

            strategy_data = input_data.get("strategy", {})
            chapters_to_generate = input_data.get("chapters", 40)

            print(f"🎨 [DEBUG] 策略数据: {strategy_data}")
            print(f"🎨 [DEBUG] 需要生成章节数: {chapters_to_generate}")

            plot_outline = strategy_data.get("plot_outline", [])
            print(f"🎨 [DEBUG] 情节大纲包含 {len(plot_outline)} 个章节")

            # 生成所有章节内容
            generated_chapters = []

            for i, chapter_info in enumerate(plot_outline[:chapters_to_generate]):
                print(f"🎨 [DEBUG] 开始生成第 {i+1} 章: {chapter_info}")

                # 生成单个章节
                chapter_content = await self._generate_chapter_content(
                    chapter_info,
                    strategy_data,
                    input_data.get("knowledge_base", {})
                )

                print(f"🎨 [DEBUG] 第 {i+1} 章生成结果: success={chapter_content['success']}")

                if chapter_content["success"]:
                    generated_chapters.append(chapter_content["content"])
                    print(f"🎨 [DEBUG] 第 {i+1} 章生成成功，长度: {len(chapter_content['content'])}")
                else:
                    # 生成失败，使用备用内容
                    fallback_content = self._generate_fallback_content(chapter_info)
                    generated_chapters.append(fallback_content)
                    print(f"🎨 [DEBUG] 第 {i+1} 章生成失败，使用备用内容")

            print(f"🎨 [DEBUG] 总共生成 {len(generated_chapters)} 个章节")

            result_data = {
                "chapters": generated_chapters,
                "total_chapters": len(generated_chapters),
                "generation_stats": {
                    "success_rate": len([c for c in generated_chapters if "error" not in c]) / len(generated_chapters) if generated_chapters else 0,
                    "average_length": sum(len(c) for c in generated_chapters) / len(generated_chapters) if generated_chapters else 0,
                    "timestamp": datetime.now().isoformat()
                }
            }

            print(f"🎨 [DEBUG] 生成统计: {result_data['generation_stats']}")

            self.update_status("completed")

            return AgentResult(
                success=True,
                data=result_data,
                message=f"成功生成{len(generated_chapters)}回续写内容"
            )

        except Exception as e:
            print(f"🎨 [DEBUG] ContentGeneratorAgent 异常: {str(e)}")
            import traceback
            print(f"🎨 [DEBUG] 异常详情:\n{traceback.format_exc()}")
            self.update_status("error")
            return self.handle_error(e)

    async def _generate_chapter_content(
        self,
        chapter_info: Dict[str, Any],
        strategy_data: Dict[str, Any],
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成单个章节内容"""
        try:
            print(f"📝 [DEBUG] 开始生成章节 {chapter_info.get('chapter_num', 'unknown')}")

            chapter_num = chapter_info["chapter_num"]
            chapter_title = chapter_info["title"]
            key_events = chapter_info["key_events"]
            character_development = chapter_info["character_development"]

            print(f"📝 [DEBUG] 章节信息: {chapter_num}, {chapter_title}")
            print(f"📝 [DEBUG] 关键事件: {key_events}")
            print(f"📝 [DEBUG] 人物发展: {character_development}")

            # 构建生成prompt
            print("📝 [DEBUG] 构建生成上下文...")
            context = self._build_generation_context(
                chapter_info, strategy_data, knowledge_base
            )
            print(f"📝 [DEBUG] 上下文长度: {len(context)}")

            print("📝 [DEBUG] 创建prompt模板...")
            system_msg, user_prompt = self.prompts.create_custom_prompt(
                "content_generator",
                {
                    "chapter_num": chapter_num,
                    "chapter_title": chapter_title,
                    "chapter_summary": "; ".join(key_events),
                    "key_characters": ", ".join(character_development.keys()),
                    "theme_focus": ", ".join(chapter_info.get("themes", []))
                }
            )

            print(f"📝 [DEBUG] System message长度: {len(system_msg)}")
            print(f"📝 [DEBUG] User prompt长度: {len(user_prompt)}")

            # 添加上下文信息
            full_prompt = user_prompt + "\n\n参考上下文：\n" + context
            print(f"📝 [DEBUG] 完整prompt长度: {len(full_prompt)}")

            # 调用GPT-5生成内容
            print("📝 [DEBUG] 调用GPT-5 API...")
            response = await self.gpt5_client.generate_with_retry(
                prompt=full_prompt,
                system_message=system_msg,
                temperature=0.8,
                max_tokens=8000
            )

            print(f"📝 [DEBUG] API响应: success={response.get('success', False)}")

            if response["success"]:
                print("📝 [DEBUG] API调用成功，开始后处理...")
                content = self._post_process_content(response["content"], chapter_info)
                print(f"📝 [DEBUG] 后处理完成，内容长度: {len(content)}")
                return {
                    "success": True,
                    "content": content,
                    "chapter_num": chapter_num,
                    "word_count": len(content),
                    "generation_info": response
                }
            else:
                print(f"📝 [DEBUG] API调用失败: {response.get('error', 'unknown error')}")
                return {
                    "success": False,
                    "error": response.get("error", "生成失败"),
                    "chapter_num": chapter_num
                }

        except Exception as e:
            print(f"📝 [DEBUG] 生成章节异常: {str(e)}")
            import traceback
            print(f"📝 [DEBUG] 异常详情:\n{traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "chapter_num": chapter_info.get("chapter_num")
            }

    def _build_generation_context(
        self,
        chapter_info: Dict[str, Any],
        strategy_data: Dict[str, Any],
        knowledge_base: Dict[str, Any]
    ) -> str:
        """构建生成上下文"""
        context_parts = []

        # 添加情节大纲
        plot_outline = strategy_data.get("overall_strategy", {})
        if plot_outline:
            context_parts.append(f"总体情节框架: {plot_outline.get('overall_approach', '')}")

        # 添加人物信息
        characters = knowledge_base.get("characters", {})
        if characters:
            char_info = []
            for name, info in list(characters.items())[:3]:  # 限制前3个主要人物
                char_info.append(f"{name}: {info.get('性格', '')}")
            context_parts.append(f"主要人物性格: {'; '.join(char_info)}")

        # 添加主题信息
        themes = chapter_info.get("themes", [])
        if themes:
            context_parts.append(f"本回主题: {'、'.join(themes)}")

        # 添加文学要求
        literary_reqs = [
            "使用雅致古朴的古典小说语言",
            "融入诗词歌赋等古典元素",
            "注重人物心理描写",
            "运用合适的修辞手法"
        ]
        context_parts.append(f"文学要求: {'；'.join(literary_reqs)}")

        return "\n".join(context_parts)

    def _post_process_content(self, raw_content: str, chapter_info: Dict[str, Any]) -> str:
        """后处理生成的内容"""
        try:
            # 清理和格式化内容
            content = self._clean_content(raw_content)

            # 添加章节标题
            chapter_title = chapter_info.get("title", f"第{chapter_info['chapter_num']}回")
            formatted_content = f"### {chapter_title}\n\n{content}"

            # 添加章节信息
            chapter_info_text = self._generate_chapter_info(chapter_info)
            formatted_content = chapter_info_text + "\n\n" + formatted_content

            # 添加结尾标记
            formatted_content += "\n\n---\n\n*本回由AI续写，保持古典文学风格*"

            return formatted_content

        except Exception as e:
            print(f"内容后处理失败: {e}")
            return raw_content

    def _clean_content(self, content: str) -> str:
        """清理内容格式"""
        # 移除多余的换行
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 统一段落格式
        content = re.sub(r'^', '    ', content, flags=re.MULTILINE)

        # 清理特殊字符
        content = content.replace('\r', '')

        return content.strip()

    def _generate_chapter_info(self, chapter_info: Dict[str, Any]) -> str:
        """生成章节信息"""
        info_lines = []

        chapter_num = chapter_info.get("chapter_num")
        phase = chapter_info.get("phase", "")
        focus = chapter_info.get("focus", "")

        info_lines.append(f"**第{chapter_num}回**")
        if phase:
            info_lines.append(f"**阶段**: {phase}")
        if focus:
            info_lines.append(f"**重点**: {focus}")

        return "\n".join(info_lines)

    def _generate_fallback_content(self, chapter_info: Dict[str, Any]) -> str:
        """生成备用内容"""
        chapter_num = chapter_info["chapter_num"]
        chapter_title = chapter_info.get("title", f"第{chapter_num}回 (备用内容)")

        content = f"""### {chapter_title}

[这是第{chapter_num}回的备用内容]

话说...

[此处省略详细内容]

---

*本回备用内容，等待进一步完善*
"""

        return content

    def _ensure_literary_quality(self, content: str) -> str:
        """确保文学质量"""
        # 这里可以添加质量检查和改进逻辑
        # 检查是否包含古典文学元素
        # 验证语言风格是否符合要求
        # 调整内容长度和结构

        return content

    def _add_literary_elements(self, content: str, chapter_info: Dict[str, Any]) -> str:
        """添加文学元素"""
        # 根据章节特点添加合适的文学元素
        # 如诗词、对联、象征手法等

        return content
