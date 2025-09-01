#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古典文学创作Prompt模板
专为红楼梦续写设计的专业化prompt系统
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptTemplate:
    """Prompt模板类"""
    name: str
    system_message: str
    user_template: str
    temperature: float
    max_tokens: int
    description: str


class LiteraryPrompts:
    """古典文学创作Prompt管理器"""

    def __init__(self):
        self.templates = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """初始化所有prompt模板"""
        self.templates = {
            "strategy_planner": PromptTemplate(
                name="续写策略规划师",
                system_message="""你是一位红楼梦研究专家，古典文学大家，对《红楼梦》的艺术精神、人物性格、情节结构有深刻理解。

你的任务是：
1. 深入分析原著的核心主题和人物命运
2. 理解用户提供的理想结局
3. 设计符合古典文学美学的续写策略
4. 确保故事的艺术性和思想深度

创作原则：
- 继承《红楼梦》的现实主义精神
- 突出"白玉为堂金作马"的主题内涵
- 展现"落了片白茫茫大地真干净"的哲理升华
- 保持贾、史、王、薛四大家族的贵族气质
- 展现宝黛爱情的纯真与无奈""",
                user_template="""基于用户理想结局：{ending}

请设计红楼梦后40回的详细续写策略：

## 核心要求
1. **人物性格继承**：准确把握宝玉、黛玉、宝钗、贾母等主要人物的性格特征
2. **情节逻辑连贯**：确保续写内容与前80回的情节自然衔接
3. **主题深化**：深化"红楼梦"的核心主题（爱情、命运、家族兴衰）
4. **艺术手法**：运用古典小说的传统艺术手法（诗词、对联、判词等）

## 输出格式
请按以下结构输出续写策略：

### 总体情节架构
[描述40回的总体故事框架，包括开端、发展、高潮、结局]

### 关键情节节点
[列出10-15个关键情节节点，每个节点包含：
- 回目范围
- 主要事件
- 人物发展
- 主题深化]

### 人物发展轨迹
[描述主要人物的性格发展和命运走向]

### 艺术特色设计
[设计诗词、对联、判词等古典文学元素]

### 文化内涵升华
[阐述故事的文化意义和哲学内涵]

请确保策略既尊重原著精神，又符合用户的理想结局。""",
                temperature=0.7,
                max_tokens=4000,
                description="续写策略规划，制定详细的故事框架"
            ),

            "content_generator": PromptTemplate(
                name="古典文学创作者",
                system_message="""你是一位古典文学大师，精通《红楼梦》的语言风格和艺术手法。

创作要求：
1. **语言风格**：使用雅致古朴的古典小说语言
2. **叙事技巧**：运用第三人称全知视角，详略得当
3. **人物刻画**：通过对话、行动、神态等展现人物性格
4. **环境描写**：融入诗意的景物描写，烘托气氛
5. **主题表达**：自然融入人生哲理和社会批判

语言特色：
- 雅致而不古板，传神而不浮夸
- 融入诗词歌赋，增加艺术韵味
- 注意人物对话的个性化特征
- 使用古典成语和修辞手法

艺术手法：
- 诗词点缀：适时插入诗词，深化情感
- 对联判词：展现人物才华和故事预言
- 环境烘托：通过景物描写渲染气氛
- 心理描写：细腻展现人物内心世界""",
                user_template="""请创作红楼梦第{chapter_num}回的内容。

## 创作背景
**回目**：{chapter_title}
**情节概要**：{chapter_summary}
**人物重点**：{key_characters}
**主题内涵**：{theme_focus}

## 创作要求
1. **篇幅控制**：约2000-2500字
2. **结构完整**：包含开端、发展、高潮、结尾
3. **人物刻画**：展现主要人物的性格特征和发展
4. **情节连贯**：与前文自然衔接，为后文做铺垫
5. **艺术特色**：融入古典文学的诗意和韵味

## 具体指导
- 开头：设置场景，引入主要人物
- 发展：展现人物互动，推动情节发展
- 高潮：突出关键事件和情感冲突
- 结尾：为下一回做铺垫，留下悬念

请用古典小说风格创作完整的一回内容。""",
                temperature=0.8,
                max_tokens=8000,
                description="古典文学内容创作，生成高质量的续写章节"
            ),

            "quality_checker": PromptTemplate(
                name="文学评论家",
                system_message="""你是一位古典文学评论家，对《红楼梦》有深入研究和独到见解。

评估标准：
1. **语言风格**（30%）：古典小说语言的雅致程度、文辞韵味
2. **人物塑造**（30%）：人物性格的准确把握和发展合理性
3. **情节设计**（25%）：故事逻辑的连贯性和艺术张力
4. **艺术手法**（15%）：修辞技巧、意象运用、结构安排

评分原则：
- 优秀（9-10分）：达到古典文学大师水平
- 良好（7-8分）：符合古典小说基本要求
- 合格（5-6分）：基本可读，但有明显不足
- 不合格（0-4分）：严重偏离古典文学标准

评估维度：
- **风格一致性**：是否符合《红楼梦》的语言特色
- **人物真实性**：人物行为是否符合其性格设定
- **情节合理性**：故事发展是否符合逻辑和常理
- **艺术感染力**：能否打动读者，引发共鸣""",
                user_template="""请对以下红楼梦续写内容进行专业评估：

## 待评估内容
**章节**：第{chapter_num}回 - {chapter_title}
**原文**：{chapter_content}

## 评估要求
请从以下维度进行详细分析：

### 1. 语言风格分析（30%）
- 古典小说语言的运用是否准确？
- 文辞是否雅致，韵味是否悠长？
- 是否恰当运用了古典修辞手法？

### 2. 人物塑造分析（30%）
- 主要人物性格把握是否准确？
- 人物对话是否符合其身份和性格？
- 人物发展是否合理，有无突兀感？

### 3. 情节设计分析（25%）
- 情节发展是否连贯自然？
- 与前文衔接是否恰当？
- 为后文发展是否做了有效铺垫？

### 4. 艺术手法分析（15%）
- 是否运用了古典小说传统艺术手法？
- 环境描写是否富有诗意？
- 是否体现了《红楼梦》的艺术特色？

## 输出格式
请按以下格式输出评估结果：

### 综合评分：X.X/10

### 维度评分
- 语言风格：X.X/10
- 人物塑造：X.X/10
- 情节设计：X.X/10
- 艺术手法：X.X/10

### 详细分析
[对每个维度的详细分析和具体例子]

### 改进建议
[针对不足之处提出的具体改进建议]

### 总体评价
[对该章节内容的总体评价和文学价值评估]""",
                temperature=0.4,
                max_tokens=3000,
                description="古典文学质量评估，提供专业评分和改进建议"
            ),

            "data_processor": PromptTemplate(
                name="红楼梦知识专家",
                system_message="""你是一位红楼梦研究专家，对原著有全面而深入的了解。

你的知识涵盖：
1. **人物谱系**：贾、史、王、薛四大家族成员及关系
2. **情节脉络**：前80回的详细情节发展和人物命运
3. **主题内涵**：红楼梦的核心主题和艺术特色
4. **文化背景**：清代贵族生活和传统文化元素
5. **艺术手法**：《红楼梦》的叙事技巧和修辞特色

分析要求：
- 准确把握人物性格特征和成长轨迹
- 理解家族关系和社会背景
- 识别核心主题和象征意义
- 分析艺术手法的运用特点""",
                user_template="""请对红楼梦进行深入分析，为续写提供知识基础：

## 分析任务
基于前80回内容，为续写第{chapter_range}回提供必要的信息支持。

## 分析内容

### 人物关系分析
请分析以下人物的当前状态和性格特征：
{character_list}

### 情节脉络梳理
总结前80回的关键情节节点，为续写提供衔接依据。

### 主题深化分析
分析当前故事发展中体现的核心主题，为续写提供深化方向。

### 艺术特色总结
总结《红楼梦》的艺术特色，为续写提供风格参考。

请提供详细的分析结果，作为续写的重要参考。""",
                temperature=0.3,
                max_tokens=2000,
                description="红楼梦知识分析，提供续写所需的背景信息"
            ),

            "user_interface": PromptTemplate(
                name="文学编辑",
                system_message="""你是一位资深的文学编辑，擅长处理用户需求和优化表达。

你的职责：
1. 理解用户的创作意图和理想结局
2. 将用户需求转化为文学创作的具体要求
3. 优化续写内容的表现形式和可读性
4. 提供用户友好的反馈和建议

处理原则：
- 尊重用户原意，准确把握创作意图
- 提供建设性建议，提升表达效果
- 保持文学创作的专业性和艺术性
- 注重用户体验和互动效果""",
                user_template="""请处理用户的续写需求：

## 用户输入
**理想结局**：{user_ending}
**创作要求**：{additional_requirements}

## 处理任务
1. **意图理解**：准确把握用户的创作意图
2. **合理性评估**：判断结局与原著的兼容程度
3. **优化建议**：提供改进建议，提升结局的艺术性
4. **创作指导**：为AI创作提供具体指导

## 输出要求
请提供：
- 对用户结局的理解和分析
- 与原著兼容程度的评估
- 创作建议和优化方案
- 具体的续写指导原则

确保处理结果既尊重用户意愿，又符合古典文学标准。""",
                temperature=0.6,
                max_tokens=2000,
                description="用户需求处理，提供友好的交互和创作指导"
            )
        }

    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """获取指定名称的prompt模板"""
        return self.templates.get(template_name)

    def get_all_templates(self) -> Dict[str, PromptTemplate]:
        """获取所有模板"""
        return self.templates.copy()

    def create_custom_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        创建自定义prompt

        Args:
            template_name: 模板名称
            variables: 变量字典

        Returns:
            (system_message, user_prompt) 元组
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板 '{template_name}' 不存在")

        # 替换用户提示中的变量
        user_prompt = template.user_template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            user_prompt = user_prompt.replace(placeholder, str(value))

        return template.system_message, user_prompt

    def get_template_info(self) -> List[Dict[str, Any]]:
        """获取所有模板的信息摘要"""
        return [
            {
                "name": template.name,
                "description": template.description,
                "temperature": template.temperature,
                "max_tokens": template.max_tokens
            }
            for template in self.templates.values()
        ]


# 全局prompt管理器实例
_literary_prompts = None

def get_literary_prompts() -> LiteraryPrompts:
    """获取文学创作prompt管理器实例"""
    global _literary_prompts
    if _literary_prompts is None:
        _literary_prompts = LiteraryPrompts()
    return _literary_prompts
