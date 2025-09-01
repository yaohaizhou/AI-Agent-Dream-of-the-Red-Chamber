#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT-5 API客户端
负责与GPT-5模型进行通信，实现高质量的续写内容生成
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai
from openai import AsyncOpenAI

from ..config.settings import Settings


class GPT5Client:
    """GPT-5 API客户端"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """初始化OpenAI客户端"""
        try:
            # 从配置中获取API设置
            base_url = self.settings.base_url
            api_key = self.settings.api_key

            if not base_url or not api_key:
                print("GPT-5 API配置不完整，使用模拟客户端")
                self.client = MockGPT5Client()
                return

            self.client = AsyncOpenAI(
                base_url=base_url,
                api_key=api_key,
                default_headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )

        except Exception as e:
            print(f"初始化GPT-5客户端失败: {e}")
            # 创建模拟客户端用于测试
            self.client = MockGPT5Client()

    async def generate_content(
        self,
        prompt: str,
        system_message: str = "",
        temperature: float = 0.8,
        max_tokens: int = 8000,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成内容

        Args:
            prompt: 用户提示
            system_message: 系统消息
            temperature: 温度参数
            max_tokens: 最大token数
            context: 上下文信息

        Returns:
            生成结果字典
        """
        try:
            print(f"🤖 [DEBUG] 准备API调用 - 模型: {self.settings.model_name}, 温度: {temperature}")
            print(f"🤖 [DEBUG] 最大token数: {max_tokens}")

            messages = []

            # 添加系统消息
            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })
                print("🤖 [DEBUG] 添加了系统消息")

            # 添加上下文（如果有）
            if context:
                messages.append({
                    "role": "user",
                    "content": f"参考上下文：\n{context}"
                })
                print("🤖 [DEBUG] 添加了上下文消息")

            # 添加用户提示
            messages.append({
                "role": "user",
                "content": prompt
                })
            print(f"🤖 [DEBUG] 添加了用户提示，总消息数: {len(messages)}")

            # 调用API
            print("🤖 [DEBUG] 发送API请求...")
            response = await self.client.chat.completions.create(
                model=self.settings.model_name,  # 使用配置中的模型名称
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )

            print("🤖 [DEBUG] API响应成功")
            print(f"🤖 [DEBUG] 响应模型: {response.model}")
            print(f"🤖 [DEBUG] 完成原因: {response.choices[0].finish_reason}")
            print(f"🤖 [DEBUG] 生成内容长度: {len(response.choices[0].message.content)}")

            # 解析响应
            result = {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "timestamp": datetime.now().isoformat(),
                "finish_reason": response.choices[0].finish_reason
            }

            return result

        except Exception as e:
            print(f"🤖 [DEBUG] API调用异常: {str(e)}")
            import traceback
            print(f"🤖 [DEBUG] 异常详情:\n{traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def generate_with_retry(
        self,
        prompt: str,
        system_message: str = "",
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """带重试机制的内容生成"""
        print(f"🤖 [DEBUG] 开始API调用，重试次数: {max_retries}")
        print(f"🤖 [DEBUG] Prompt长度: {len(prompt)}")
        print(f"🤖 [DEBUG] System message长度: {len(system_message)}")

        for attempt in range(max_retries):
            print(f"🤖 [DEBUG] 第 {attempt + 1} 次尝试...")
            result = await self.generate_content(prompt, system_message, **kwargs)

            if result["success"]:
                print(f"🤖 [DEBUG] 第 {attempt + 1} 次尝试成功")
                return result

            print(f"🤖 [DEBUG] 第 {attempt + 1} 次尝试失败: {result.get('error', 'unknown error')}")

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                print(f"🤖 [DEBUG] 生成失败 (尝试 {attempt + 1}/{max_retries})，{wait_time}秒后重试...")
                await asyncio.sleep(wait_time)
            else:
                print(f"🤖 [DEBUG] 所有重试都失败了")

        return result


class MockGPT5Client:
    """模拟GPT-5客户端，用于测试"""

    async def chat(self, **kwargs):
        """模拟聊天接口"""
        await asyncio.sleep(1)  # 模拟API延迟

        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice()]
                self.usage = MockUsage()
                self.model = f"{self.settings.model_name}-mock"

        class MockChoice:
            def __init__(self):
                self.message = MockMessage()
                self.finish_reason = "stop"

        class MockMessage:
            def __init__(self):
                self.content = "这是模拟生成的古典文学内容。古风雅致，韵味悠长..."

        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 1000
                self.completion_tokens = 500
                self.total_tokens = 1500

        return MockResponse()

    async def completions(self):
        """兼容OpenAI API接口"""
        return self

    async def create(self, **kwargs):
        """创建完成的模拟方法"""
        return await self.chat(**kwargs)


# 全局客户端实例
_gpt5_client = None

def get_gpt5_client(settings: Settings = None) -> GPT5Client:
    """获取GPT-5客户端实例"""
    global _gpt5_client
    if _gpt5_client is None:
        if settings is None:
            from ..config.settings import Settings
            settings = Settings()
        _gpt5_client = GPT5Client(settings)
    return _gpt5_client
