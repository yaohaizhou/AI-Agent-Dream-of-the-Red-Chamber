#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础Agent类
定义所有Agent的共同接口和功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


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
        self.communication_bus = None
        self.feedback_history = []

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResult:
        """处理输入数据的主方法"""
        pass

    def set_communication_bus(self, communication_bus):
        """设置通信总线"""
        self.communication_bus = communication_bus
        if communication_bus:
            communication_bus.register_agent(self.name)

    async def send_feedback(self, to_agent: str, feedback: Dict[str, Any]):
        """发送反馈给其他Agent"""
        if self.communication_bus:
            await self.communication_bus.send_feedback(self.name, to_agent, feedback)

    async def request_revision(self, to_agent: str, revision_request: Dict[str, Any]):
        """请求其他Agent修订"""
        if self.communication_bus:
            await self.communication_bus.request_revision(self.name, to_agent, revision_request)

    async def send_quality_alert(self, quality_issues: Dict[str, Any]):
        """发送质量警报"""
        if self.communication_bus:
            await self.communication_bus.send_quality_alert(self.name, quality_issues)

    async def get_feedback_messages(self):
        """获取反馈消息"""
        if self.communication_bus:
            messages = await self.communication_bus.get_messages_for_agent(self.name)
            self.feedback_history.extend(messages)
            return messages
        return []

    def update_status(self, status: str):
        """更新Agent状态"""
        self.status = status
        self.last_active = datetime.now()
        
        # 广播状态更新
        if self.communication_bus:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.communication_bus.broadcast_status_update(
                        self.name, {"status": status, "timestamp": self.last_active.isoformat()}
                    ))
            except:
                pass  # 如果无法获取事件循环，忽略状态广播

    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "name": self.name,
            "status": self.status,
            "last_active": self.last_active.isoformat(),
            "config": self.config,
            "feedback_count": len(self.feedback_history)
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

        # 对于用户交互Agent，需要保留原始数据
        if "用户交互" in self.name:
            # 保留输入数据，只添加处理信息
            result_data = input_data.copy()
            result_data.update({
                "agent_name": self.name,
                "processed_at": datetime.now().isoformat(),
                "processing_info": f"{self.name}格式化完成"
            })
        else:
            # 其他MockAgent生成模拟结果
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
