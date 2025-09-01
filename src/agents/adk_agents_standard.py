#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准Google ADK红楼梦续写Agent系统
按照ADK官方文档的标准方式实现
"""

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.genai import types
from typing import Dict, Any, Optional
import json
from pathlib import Path

from ..config.settings import Settings


class HongLouMengADKSystem:
    """红楼梦续写ADK系统 - 标准实现"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # 创建ADK服务
        self.session_service = InMemorySessionService()
        self.artifact_service = InMemoryArtifactService()
        
        # 创建红楼梦续写Agent
        self.hongloumeng_agent = Agent(
            model="gemini-2.0-flash-001",  # 使用ADK推荐的模型
            name="hongloumeng_continuation_agent",
            description="专业的红楼梦续写智能体，能够分析原著风格并创作高质量的古典文学续写内容。",
            instruction="""你是红楼梦续写专家，具备以下能力：

1. 【文学分析能力】
   - 深入理解红楼梦前80回的文学风格、语言特色
   - 准确把握主要人物的性格特征和关系网络
   - 熟悉红楼梦的叙事结构和章回体特点

2. 【续写创作能力】
   - 根据用户期望结局制定合理的情节发展策略
   - 创作符合古典文学风格的高质量续写内容
   - 保持人物性格的一致性和情节的合理性

3. 【质量评估能力】
   - 评估续写内容的文学质量和风格一致性
   - 检查情节发展的合理性和人物刻画的准确性
   - 提供改进建议和质量评分

请始终用中文回应，保持古典文学的优雅文风。""",
            generate_content_config=types.GenerateContentConfig(
                temperature=0.7,  # 适中的创造性
                top_p=0.9,
                max_output_tokens=4000  # 足够长的输出
            )
        )
        
        # 会话和运行器将在需要时异步创建
        self.session = None
        self.runner = None
    
    async def _ensure_initialized(self):
        """确保会话和运行器已初始化"""
        if self.session is None:
            # 异步创建会话
            self.session = await self.session_service.create_session(
                app_name="hongloumeng_continuation", 
                user_id="user"
            )
            
            # 创建运行器
            self.runner = Runner(
                app_name="hongloumeng_continuation",
                agent=self.hongloumeng_agent,
                artifact_service=self.artifact_service,
                session_service=self.session_service
            )
    
    async def process_continuation_request(self, user_ending: str, chapters: int = 1) -> Dict[str, Any]:
        """处理续写请求"""
        try:
            # 确保初始化完成
            await self._ensure_initialized()
            
            print("🎭 [ADK] 开始红楼梦续写流程")
            
            # 构建续写请求消息
            continuation_message = f"""
请为红楼梦续写第81回，要求如下：

【用户期望结局】：{user_ending}
【续写章节数】：{chapters}回

【任务要求】：
1. 首先分析红楼梦前80回的主要情节线索和人物关系
2. 根据用户期望结局，制定合理的续写策略
3. 创作符合古典文学风格的第81回内容
4. 对创作内容进行质量评估

【输出格式】：
请按以下JSON格式输出结果：

```json
{{
    "analysis": {{
        "main_characters": ["主要人物列表"],
        "plot_threads": ["主要情节线索"],
        "literary_style": "文学风格分析"
    }},
    "strategy": {{
        "plot_direction": "情节发展方向",
        "character_development": "人物发展规划",
        "key_events": ["关键事件列表"]
    }},
    "content": {{
        "chapter_title": "第八十一回 章回标题",
        "chapter_content": "章回正文内容（完整的古典文学风格文本）"
    }},
    "quality_assessment": {{
        "style_consistency": 9,
        "character_accuracy": 8,
        "plot_reasonability": 9,
        "literary_quality": 8,
        "overall_score": 8.5,
        "comments": "质量评估说明"
    }}
}}
```

请开始续写：
"""
            
            print("🎨 [ADK] 正在生成续写内容...")
            
            # 使用ADK Runner运行Agent
            events = self.runner.run(
                user_id='user',
                session_id=self.session.id,
                new_message=continuation_message
            )
            
            # 收集响应内容
            response_content = ""
            for event in events:
                if hasattr(event, 'content') and event.content:
                    response_content += str(event.content)
                elif hasattr(event, 'text') and event.text:
                    response_content += str(event.text)
            
            print(f"🎨 [ADK] 收到响应内容长度: {len(response_content)}")
            
            # 尝试解析JSON响应
            try:
                # 查找JSON内容
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = response_content[json_start:json_end]
                    result = json.loads(json_content)
                    print("✅ [ADK] 成功解析JSON响应")
                    return result
                else:
                    print("⚠️ [ADK] 未找到JSON格式，使用原始响应")
                    return {
                        "analysis": {"literary_style": "分析中"},
                        "strategy": {"plot_direction": "策略制定中"},
                        "content": {
                            "chapter_title": "第八十一回 续写章节",
                            "chapter_content": response_content
                        },
                        "quality_assessment": {
                            "overall_score": 7.0,
                            "comments": "ADK生成的续写内容"
                        }
                    }
            
            except json.JSONDecodeError as e:
                print(f"⚠️ [ADK] JSON解析失败: {e}")
                return {
                    "analysis": {"literary_style": "分析中"},
                    "strategy": {"plot_direction": "策略制定中"},
                    "content": {
                        "chapter_title": "第八十一回 续写章节",
                        "chapter_content": response_content
                    },
                    "quality_assessment": {
                        "overall_score": 7.0,
                        "comments": "ADK生成的续写内容（JSON解析失败）"
                    }
                }
        
        except Exception as e:
            print(f"❌ [ADK] 续写流程失败: {e}")
            import traceback
            print(f"❌ [ADK] 错误详情:\n{traceback.format_exc()}")
            
            return {
                "analysis": {"literary_style": "分析失败"},
                "strategy": {"plot_direction": "策略制定失败"},
                "content": {
                    "chapter_title": "第八十一回 续写失败",
                    "chapter_content": f"续写过程中发生错误：{str(e)}"
                },
                "quality_assessment": {
                    "overall_score": 0.0,
                    "comments": f"续写失败：{str(e)}"
                }
            }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        await self._ensure_initialized()
        
        return {
            "agent_name": self.hongloumeng_agent.name,
            "model": self.hongloumeng_agent.model,
            "session_id": self.session.id,
            "status": "ready"
        }


def create_hongloumeng_adk_system(settings: Settings) -> HongLouMengADKSystem:
    """创建红楼梦ADK系统"""
    return HongLouMengADKSystem(settings)
