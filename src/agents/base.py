#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础Agent类
定义所有Agent的共同接口和功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentMessage:
    """Agent间通信的消息格式"""
    message_id: str
    sender: str
    receiver: str
    message_type: str  # request, response, notification
    payload: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool
    data: Any
    message: str
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """基础Agent类"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.status = "initialized"
        self.last_active = datetime.now()

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """处理输入数据的主方法"""
        pass

    def update_status(self, status: str):
        """更新Agent状态"""
        self.status = status
        self.last_active = datetime.now()

    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "name": self.name,
            "status": self.status,
            "last_active": self.last_active.isoformat(),
            "config": self.config
        }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据的有效性"""
        return True

    def handle_error(self, error: Exception) -> AgentResult:
        """处理执行过程中的错误"""
        return AgentResult(
            success=False,
            data=None,
            message=f"Agent {self.name} 执行出错: {str(error)}"
        )


class MockAgent(BaseAgent):
    """模拟Agent，用于demo和测试"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.response_delay = config.get('response_delay', 1.0) if config else 1.0

    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """模拟处理过程"""
        import asyncio
        import time

        self.update_status("processing")

        # 模拟处理时间
        await asyncio.sleep(self.response_delay)

        # 生成模拟结果
        result_data = {
            "agent_name": self.name,
            "processed_at": datetime.now().isoformat(),
            "input_summary": str(input_data)[:100] + "..." if len(str(input_data)) > 100 else str(input_data),
            "mock_result": f"这是{self.name}的模拟处理结果"
        }

        self.update_status("completed")

        return AgentResult(
            success=True,
            data=result_data,
            message=f"{self.name} 处理完成"
        )
