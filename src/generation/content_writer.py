"""ContentWriter：调用 LLM，返回原始生成文本。"""
from __future__ import annotations

from src.agents.gpt5_client import get_gpt5_client
from src.config.settings import Settings


class ContentWriter:
    def __init__(self, settings: Settings):
        self.client = get_gpt5_client(settings)

    async def write(
        self,
        system_msg: str,
        user_prompt: str,
        chapter_num: int,
        temperature: float = 0.85,
        max_tokens: int = 6000,
    ) -> str:
        """调用 LLM，返回生成的章节文本；失败时返回空字符串。"""
        result = await self.client.generate_content(
            prompt=user_prompt,
            system_message=system_msg,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if result.get("success"):
            return result.get("content", "")
        return ""
