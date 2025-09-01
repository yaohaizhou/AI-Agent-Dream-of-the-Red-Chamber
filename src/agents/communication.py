#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent通信总线
负责Agent间的消息传递、反馈机制和协调
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """消息类型"""
    FEEDBACK = "feedback"
    REVISION_REQUEST = "revision_request"
    QUALITY_ALERT = "quality_alert"
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"
    STATUS_UPDATE = "status_update"


@dataclass
class AgentMessage:
    """Agent消息"""
    id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1-5, 5为最高优先级


class AgentCommunicationBus:
    """Agent通信总线"""
    
    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.feedback_channels = {}
        self.message_history = []
        self.active_agents = set()
        
    def register_agent(self, agent_name: str):
        """注册Agent"""
        self.active_agents.add(agent_name)
        self.feedback_channels[agent_name] = asyncio.Queue()
        
    async def send_message(self, message: AgentMessage):
        """发送消息"""
        await self.message_queue.put(message)
        self.message_history.append(message)
        
        # 如果是发送给特定Agent的消息，也放入其专用通道
        if message.to_agent in self.feedback_channels:
            await self.feedback_channels[message.to_agent].put(message)
    
    async def send_feedback(self, from_agent: str, to_agent: str, feedback: Dict[str, Any]):
        """发送反馈消息"""
        message = AgentMessage(
            id=f"feedback_{datetime.now().timestamp()}",
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.FEEDBACK,
            content=feedback,
            timestamp=datetime.now(),
            priority=3
        )
        await self.send_message(message)
    
    async def request_revision(self, from_agent: str, to_agent: str, revision_request: Dict[str, Any]):
        """请求修订"""
        message = AgentMessage(
            id=f"revision_{datetime.now().timestamp()}",
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.REVISION_REQUEST,
            content=revision_request,
            timestamp=datetime.now(),
            priority=4
        )
        await self.send_message(message)
    
    async def send_quality_alert(self, from_agent: str, quality_issues: Dict[str, Any]):
        """发送质量警报"""
        message = AgentMessage(
            id=f"quality_alert_{datetime.now().timestamp()}",
            from_agent=from_agent,
            to_agent="orchestrator",
            message_type=MessageType.QUALITY_ALERT,
            content=quality_issues,
            timestamp=datetime.now(),
            priority=5
        )
        await self.send_message(message)
    
    async def get_messages_for_agent(self, agent_name: str) -> List[AgentMessage]:
        """获取特定Agent的消息"""
        messages = []
        if agent_name in self.feedback_channels:
            while not self.feedback_channels[agent_name].empty():
                try:
                    message = await asyncio.wait_for(
                        self.feedback_channels[agent_name].get(), 
                        timeout=0.1
                    )
                    messages.append(message)
                except asyncio.TimeoutError:
                    break
        return messages
    
    async def broadcast_status_update(self, from_agent: str, status: Dict[str, Any]):
        """广播状态更新"""
        message = AgentMessage(
            id=f"status_{datetime.now().timestamp()}",
            from_agent=from_agent,
            to_agent="all",
            message_type=MessageType.STATUS_UPDATE,
            content=status,
            timestamp=datetime.now(),
            priority=2
        )
        await self.send_message(message)
    
    def get_message_history(self, agent_name: Optional[str] = None) -> List[AgentMessage]:
        """获取消息历史"""
        if agent_name:
            return [msg for msg in self.message_history 
                   if msg.from_agent == agent_name or msg.to_agent == agent_name]
        return self.message_history.copy()


# 全局通信总线实例
_communication_bus = None

def get_communication_bus() -> AgentCommunicationBus:
    """获取全局通信总线实例"""
    global _communication_bus
    if _communication_bus is None:
        _communication_bus = AgentCommunicationBus()
    return _communication_bus
