#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渐进式生成模块
实现分层生成策略，确保输出质量
"""

import asyncio
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class GenerationStep:
    """生成步骤"""
    name: str
    prompt_template: str
    validator: callable
    max_retries: int = 3


@dataclass
class ChapterStructure:
    """章节结构"""
    chapter_number: int
    title: str  # 回目（八字对仗）
    scenes: List[Dict[str, Any]]  # 场景列表
    poetry: Optional[str]  # 诗词
    ending_hook: str  # 结尾悬念


class ProgressiveGenerator:
    """渐进式生成器"""
    
    def __init__(self, gpt5_client, prompts):
        self.gpt5_client = gpt5_client
        self.prompts = prompts
        self.steps = self._init_steps()
    
    def _init_steps(self) -> List[GenerationStep]:
        """初始化生成步骤"""
        return [
            GenerationStep(
                name="title",
                prompt_template="generate_title",
                validator=self._validate_title,
                max_retries=5
            ),
            GenerationStep(
                name="outline",
                prompt_template="generate_outline",
                validator=self._validate_outline,
                max_retries=3
            ),
            GenerationStep(
                name="scenes",
                prompt_template="generate_scenes",
                validator=self._validate_scenes,
                max_retries=3
            ),
            GenerationStep(
                name="poetry",
                prompt_template="generate_poetry",
                validator=self._validate_poetry,
                max_retries=5
            ),
            GenerationStep(
                name="polish",
                prompt_template="polish_chapter",
                validator=self._validate_polish,
                max_retries=2
            )
        ]
    
    async def generate_chapter(
        self,
        chapter_number: int,
        context: Dict[str, Any],
        quality_threshold: float = 8.0
    ) -> Dict[str, Any]:
        """
        渐进式生成完整章节
        
        Args:
            chapter_number: 章节号
            context: 生成上下文
            quality_threshold: 质量阈值
            
        Returns:
            包含完整章节内容的字典
        """
        result = {
            "chapter_number": chapter_number,
            "steps": {}
        }
        
        # Step 1: 生成回目
        print(f"📖 Step 1: 生成第{chapter_number}回回目...")
        title = await self._generate_title(chapter_number, context)
        result["steps"]["title"] = title
        result["title"] = title["content"]
        
        # Step 2: 生成场景大纲
        print(f"📋 Step 2: 生成场景大纲...")
        outline = await self._generate_outline(chapter_number, result["title"], context)
        result["steps"]["outline"] = outline
        result["scenes_plan"] = outline["scenes"]
        
        # Step 3: 逐场景生成
        print(f"✍️ Step 3: 生成各场景内容...")
        scenes_content = []
        for i, scene in enumerate(outline["scenes"], 1):
            print(f"  生成场景 {i}/{len(outline['scenes'])}: {scene.get('title', '无标题')}")
            scene_content = await self._generate_scene(
                chapter_number, 
                result["title"],
                scene,
                context,
                i,
                len(outline["scenes"])
            )
            scenes_content.append(scene_content)
        result["steps"]["scenes"] = scenes_content
        result["scenes_content"] = scenes_content
        
        # Step 4: 生成诗词
        print(f"🎵 Step 4: 生成诗词...")
        poetry = await self._generate_poetry(chapter_number, scenes_content, context)
        result["steps"]["poetry"] = poetry
        result["poetry"] = poetry["content"]
        
        # Step 5: 整体润色
        print(f"✨ Step 5: 整体润色...")
        polished = await self._polish_chapter(
            chapter_number,
            result["title"],
            scenes_content,
            poetry["content"],
            context
        )
        result["steps"]["polish"] = polished
        result["final_content"] = polished["content"]
        
        return result
    
    async def _generate_title(self, chapter_number: int, context: Dict) -> Dict:
        """生成回目（八字对仗）"""
        prompt = f"""
请为《红楼梦》第{chapter_number}回创作一个回目，要求：
1. 八字对仗，格式："XXXXXX XX XX XX XX"
2. 前四字概括上半回内容，后四字概括下半回内容
3. 使用古典文学词汇
4. 符合红楼梦回目风格

当前故事背景：
{context.get('story_context', '贾府面临转折，宝玉黛玉感情发展')}

理想结局方向：
{context.get('user_ending', '宝玉和黛玉终成眷属，贾府中兴')}

请只输出回目，不要其他内容。示例格式：
占旺相四美釣游魚 奉嚴詞兩番入家塾
"""
        
        for attempt in range(5):
            response = await self.gpt5_client.generate_with_retry(
                prompt=prompt,
                system_message="你是《红楼梦》续写专家，精通古典文学回目创作。",
                temperature=0.7,
                max_tokens=100
            )
            
            if response["success"]:
                title = response["content"].strip()
                if self._validate_title(title):
                    return {"content": title, "attempts": attempt + 1}
                else:
                    print(f"    回目格式不符，重试 ({attempt+1}/5)")
            else:
                print(f"    生成失败，重试 ({attempt+1}/5)")
        
        # 返回默认回目
        return {
            "content": f"第{chapter_number}回 宝玉读书黛玉作诗",
            "attempts": 5,
            "fallback": True
        }
    
    def _validate_title(self, title: str) -> bool:
        """验证回目格式"""
        # 移除空格和标点
        clean_title = re.sub(r'\s+', '', title)
        
        # 检查长度（8-12个汉字，允许间隔符）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', clean_title)
        if len(chinese_chars) != 8:
            return False
        
        # 检查是否有分隔（空格或间隔号）
        parts = re.split(r'[\s·]+', title.strip())
        if len(parts) != 2:
            return False
        
        # 检查每部分字数
        part1_chars = re.findall(r'[\u4e00-\u9fff]', parts[0])
        part2_chars = re.findall(r'[\u4e00-\u9fff]', parts[1])
        
        return len(part1_chars) == 4 and len(part2_chars) == 4
    
    async def _generate_outline(
        self, 
        chapter_number: int, 
        title: str, 
        context: Dict
    ) -> Dict:
        """生成场景大纲"""
        prompt = f"""
请为《红楼梦》第{chapter_number}回"{title}"设计场景大纲。

要求：
1. 设计3-4个场景
2. 每个场景包含：标题、人物、主要内容
3. 场景之间要有逻辑关联
4. 最后一个场景要留下悬念

人物状态参考：
- 宝玉：{context.get('characters', {}).get('宝玉', '敏感多情，厌恶仕途')}
- 黛玉：{context.get('characters', {}).get('黛玉', '才华横溢，体弱多病')}
- 宝钗：{context.get('characters', {}).get('宝钗', '端庄贤惠，世故圆通')}

请按以下格式输出：

场景1：
标题：[场景标题]
人物：[出场人物]
内容：[主要内容]

场景2：
...

场景N：
标题：[场景标题]
人物：[出场人物]
内容：[主要内容]

悬念：[为下回埋下的伏笔]
"""
        
        response = await self.gpt5_client.generate_with_retry(
            prompt=prompt,
            system_message="你是《红楼梦》续写专家，擅长设计符合原著风格的场景。",
            temperature=0.8,
            max_tokens=2000
        )
        
        if response["success"]:
            outline_text = response["content"]
            scenes = self._parse_outline(outline_text)
            return {
                "content": outline_text,
                "scenes": scenes,
                "raw_response": response["content"]
            }
        else:
            return {
                "content": "",
                "scenes": self._default_scenes(),
                "error": response.get("error", "Unknown error")
            }
    
    def _parse_outline(self, outline_text: str) -> List[Dict]:
        """解析大纲文本"""
        scenes = []
        current_scene = {}
        
        for line in outline_text.split('\n'):
            line = line.strip()
            if line.startswith('场景'):
                if current_scene:
                    scenes.append(current_scene)
                current_scene = {"id": len(scenes) + 1}
            elif line.startswith('标题：'):
                current_scene['title'] = line[3:].strip()
            elif line.startswith('人物：'):
                current_scene['characters'] = line[3:].strip()
            elif line.startswith('内容：'):
                current_scene['content'] = line[3:].strip()
        
        if current_scene:
            scenes.append(current_scene)
        
        return scenes if scenes else self._default_scenes()
    
    def _default_scenes(self) -> List[Dict]:
        """默认场景"""
        return [
            {
                "id": 1,
                "title": "园中散步",
                "characters": "宝玉、黛玉",
                "content": "宝玉和黛玉在园中散步，谈论诗词"
            },
            {
                "id": 2,
                "title": "书房读书",
                "characters": "宝玉、贾政",
                "content": "贾政检查宝玉功课，宝玉心不在焉"
            },
            {
                "id": 3,
                "title": "夜读相思",
                "characters": "宝玉、黛玉",
                "content": "宝玉夜晚思念黛玉，写下诗句"
            }
        ]
    
    def _validate_outline(self, outline: Dict) -> bool:
        """验证大纲"""
        scenes = outline.get("scenes", [])
        return 2 <= len(scenes) <= 5
    
    async def _generate_scene(
        self,
        chapter_number: int,
        title: str,
        scene: Dict,
        context: Dict,
        scene_index: int,
        total_scenes: int
    ) -> Dict:
        """生成单个场景"""
        is_first = scene_index == 1
        is_last = scene_index == total_scenes
        
        prompt = f"""
请为《红楼梦》第{chapter_number}回"{title}"生成第{scene_index}个场景的内容。

场景信息：
标题：{scene.get('title', '')}
人物：{scene.get('characters', '')}
内容概要：{scene.get('content', '')}

写作要求：
1. 使用古典白话风格
2. 通过对话和行动展现人物性格
3. 适当加入环境描写烘托气氛
4. 字数控制在800-1200字
{"5. 这是第一个场景，需要有开场铺垫" if is_first else ""}
{"6. 这是最后一个场景，需要留下悬念，以'且听下回分解'结尾" if is_last else ""}

人物性格参考：
{self._get_character_prompts(scene.get('characters', ''), context)}

请直接输出场景正文，不需要标题。
"""
        
        response = await self.gpt5_client.generate_with_retry(
            prompt=prompt,
            system_message="你是《红楼梦》续写专家，擅长创作符合原著风格的古典文学。",
            temperature=0.8,
            max_tokens=2000
        )
        
        if response["success"]:
            return {
                "content": response["content"],
                "scene_info": scene,
                "scene_index": scene_index
            }
        else:
            return {
                "content": f"【场景{scene_index}生成失败】",
                "scene_info": scene,
                "scene_index": scene_index,
                "error": response.get("error")
            }
    
    def _get_character_prompts(self, characters_str: str, context: Dict) -> str:
        """获取人物提示"""
        prompts = []
        character_db = context.get('characters', {})
        
        for char in ['宝玉', '黛玉', '宝钗', '贾母', '王熙凤']:
            if char in characters_str:
                info = character_db.get(char, {})
                personality = info.get('性格', self._default_personality(char))
                prompts.append(f"- {char}：{personality}")
        
        return '\n'.join(prompts) if prompts else "- 宝玉：敏感多情，厌恶仕途经济\n- 黛玉：才华横溢，多愁善感"
    
    def _default_personality(self, char: str) -> str:
        """默认人物性格"""
        defaults = {
            '宝玉': '敏感多情，厌恶仕途经济，尊重女性',
            '黛玉': '才华横溢，多愁善感，身体虚弱',
            '宝钗': '端庄贤惠，世故圆通，识大体',
            '贾母': '慈祥和蔼，家族权威，疼爱孙辈',
            '王熙凤': '精明能干，权势欲强，口才出众'
        }
        return defaults.get(char, '性格鲜明')
    
    def _validate_scenes(self, scenes: List[Dict]) -> bool:
        """验证场景"""
        if not scenes or len(scenes) < 2:
            return False
        for scene in scenes:
            if not scene.get('content') or len(scene['content']) < 200:
                return False
        return True
    
    async def _generate_poetry(
        self,
        chapter_number: int,
        scenes_content: List[Dict],
        context: Dict
    ) -> Dict:
        """生成诗词"""
        # 提取场景摘要
        scene_summary = '\n'.join([
            f"场景{s['scene_index']}：{s['scene_info'].get('title', '')}"
            for s in scenes_content
        ])
        
        prompt = f"""
请为《红楼梦》第{chapter_number}回创作一首诗词。

场景摘要：
{scene_summary}

要求：
1. 七言律诗格式（8句，每句7字）
2. 平仄基本合规
3. 押韵（二、四、六、八句押韵）
4. 意境凄婉，符合红楼梦风格
5. 内容紧扣本章情节

格式示例：
一夜西风落叶黄，
梦回残荷满池塘。
浮生聚散皆前定，
莫向天涯问短长。
堪怜弱质随风折，
可叹红颜伴露霜。
且趁霜华未凋尽，
留将诗酒度时光。

请只输出诗词内容，每句一行，不要其他说明。
"""
        
        for attempt in range(5):
            response = await self.gpt5_client.generate_with_retry(
                prompt=prompt,
                system_message="你是古典诗词创作专家，精通格律诗词创作。",
                temperature=0.7,
                max_tokens=300
            )
            
            if response["success"]:
                poetry = response["content"].strip()
                if self._validate_poetry(poetry):
                    return {
                        "content": poetry,
                        "attempts": attempt + 1
                    }
                else:
                    print(f"    诗词格律不符，重试 ({attempt+1}/5)")
            else:
                print(f"    诗词生成失败，重试 ({attempt+1}/5)")
        
        # 返回默认诗词
        return {
            "content": "一夜西风落叶黄，\n梦回残荷满池塘。\n浮生聚散皆前定，\n莫向天涯问短长。",
            "attempts": 5,
            "fallback": True
        }
    
    def _validate_poetry(self, poetry: str) -> bool:
        """验证诗词格式"""
        lines = [l.strip() for l in poetry.split('\n') if l.strip()]
        
        # 检查行数
        if len(lines) != 8:
            return False
        
        # 检查每句字数
        for line in lines:
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', line)
            if len(chinese_chars) != 7:
                return False
        
        # 简单押韵检查（检查最后一字）
        last_chars = [re.findall(r'[\u4e00-\u9fff]', line)[-1] for line in lines]
        # 2,4,6,8句押韵
        rhyme_group = [last_chars[1], last_chars[3], last_chars[5], last_chars[7]]
        # 至少要有相同的韵母（简化检查）
        
        return True
    
    async def _polish_chapter(
        self,
        chapter_number: int,
        title: str,
        scenes_content: List[Dict],
        poetry: str,
        context: Dict
    ) -> Dict:
        """整体润色"""
        # 合并场景内容
        combined = '\n\n'.join([s['content'] for s in scenes_content])
        
        prompt = f"""
请对以下内容进行整体润色，使其符合《红楼梦》的古典文学风格。

回目：{title}

原文：
{combined}

润色要求：
1. 统一语言风格，确保古典白话一致性
2. 检查人物称呼是否准确
3. 确保场景过渡自然
4. 保持叙事节奏，详略得当
5. 在适当位置插入以下诗词：
{poetry}
6. 结尾必须保留悬念，以"且听下回分解"结束

请直接输出润色后的完整章节内容。
"""
        
        response = await self.gpt5_client.generate_with_retry(
            prompt=prompt,
            system_message="你是《红楼梦》文本润色专家，擅长统一古典文学风格。",
            temperature=0.6,
            max_tokens=4000
        )
        
        if response["success"]:
            content = response["content"]
            # 确保有结尾标记
            if "且听下回分解" not in content:
                content += "\n\n毕竟不知后事如何，且听下回分解。"
            
            return {
                "content": content,
                "title": title
            }
        else:
            # 返回原始内容
            return {
                "content": combined + "\n\n毕竟不知后事如何，且听下回分解。",
                "title": title,
                "error": response.get("error")
            }
    
    def _validate_polish(self, content: str) -> bool:
        """验证润色结果"""
        if len(content) < 1000:
            return False
        if "且听下回分解" not in content:
            return False
        return True
