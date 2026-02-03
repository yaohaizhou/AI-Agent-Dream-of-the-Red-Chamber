#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ForeshadowingManager - 伏笔管理系统
管理伏笔的埋设、追踪和回收
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Foreshadowing:
    """伏笔数据结构"""
    id: str
    planted_chapter: int
    content: str
    target_chapter: int
    importance: str  # minor, major, crucial
    status: str = "active"  # active, resolved, abandoned
    planted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None


class ForeshadowingManager:
    """
    伏笔管理器
    
    功能：
    1. 埋设伏笔
    2. 追踪活跃伏笔
    3. 提醒回收时机
    4. 验证回收效果
    """
    
    def __init__(self):
        self.active_foreshadowings: Dict[str, Foreshadowing] = {}
        self.resolved_foreshadowings: Dict[str, Foreshadowing] = {}
        self._counter = 0
    
    def plant_seed(
        self,
        planted_chapter: int,
        content: str,
        target_chapter: int,
        importance: str = "major"
    ) -> Foreshadowing:
        """
        埋下伏笔
        
        Args:
            planted_chapter: 埋设章节
            content: 伏笔内容
            target_chapter: 目标回收章节
            importance: 重要性 (minor/major/crucial)
            
        Returns:
            Foreshadowing 对象
        """
        self._counter += 1
        seed_id = f"fs_{planted_chapter}_{self._counter}"
        
        seed = Foreshadowing(
            id=seed_id,
            planted_chapter=planted_chapter,
            content=content,
            target_chapter=target_chapter,
            importance=importance
        )
        
        self.active_foreshadowings[seed_id] = seed
        return seed
    
    def get_payoff_reminders(self, current_chapter: int) -> List[Dict[str, Any]]:
        """
        获取当前章节应该回收的伏笔提醒
        
        Args:
            current_chapter: 当前章节号
            
        Returns:
            需要回收的伏笔列表
        """
        reminders = []
        
        for seed in self.active_foreshadowings.values():
            if seed.target_chapter == current_chapter:
                reminders.append({
                    "type": "payoff_due",
                    "seed_id": seed.id,
                    "planted_chapter": seed.planted_chapter,
                    "content": seed.content,
                    "importance": seed.importance,
                    "message": f"[伏笔回收] 第{seed.planted_chapter}回埋下的'{seed.content}'需要在本次回收"
                })
            elif seed.target_chapter - current_chapter <= 3:
                reminders.append({
                    "type": "payoff_soon",
                    "seed_id": seed.id,
                    "planted_chapter": seed.planted_chapter,
                    "content": seed.content,
                    "target_chapter": seed.target_chapter,
                    "message": f"[伏笔预警] 第{seed.planted_chapter}回的伏笔将在第{seed.target_chapter}回收，注意铺垫"
                })
        
        return reminders
    
    def validate_payoff(
        self,
        content: str,
        chapter: int
    ) -> Dict[str, Any]:
        """
        验证生成的内容是否回收了应该回收的伏笔
        
        Args:
            content: 生成的内容
            chapter: 章节号
            
        Returns:
            验证结果
        """
        expected_payoffs = [
            seed for seed in self.active_foreshadowings.values()
            if seed.target_chapter == chapter
        ]
        
        resolved = []
        missed = []
        
        for seed in expected_payoffs:
            # 简单检查：伏笔内容是否在生成的内容中
            if self._is_payoff_present(content, seed):
                resolved.append(seed)
                # 标记为已解决
                seed.status = "resolved"
                seed.resolved_at = datetime.now().isoformat()
                self.resolved_foreshadowings[seed.id] = seed
                del self.active_foreshadowings[seed.id]
            else:
                missed.append(seed)
        
        return {
            "all_resolved": len(missed) == 0,
            "resolved_count": len(resolved),
            "missed_count": len(missed),
            "resolved": resolved,
            "missed": missed
        }
    
    def _is_payoff_present(self, content: str, seed: Foreshadowing) -> bool:
        """检查伏笔是否在内容中得到回收"""
        # 简化检查：关键词匹配
        keywords = seed.content.split()
        return any(kw in content for kw in keywords if len(kw) > 2)
    
    def get_active_seeds(self) -> List[Foreshadowing]:
        """获取所有活跃的伏笔"""
        return list(self.active_foreshadowings.values())
    
    def get_seed_by_id(self, seed_id: str) -> Optional[Foreshadowing]:
        """根据ID获取伏笔"""
        return self.active_foreshadowings.get(seed_id) or \
               self.resolved_foreshadowings.get(seed_id)
    
    def get_statistics(self) -> Dict[str, int]:
        """获取伏笔统计信息"""
        return {
            "active": len(self.active_foreshadowings),
            "resolved": len(self.resolved_foreshadowings),
            "total": len(self.active_foreshadowings) + len(self.resolved_foreshadowings)
        }
    
    def create_master_foreshadowing_plan(self) -> Dict[int, List[str]]:
        """
        创建81-120回的伏笔总体规划
        
        Returns:
            章节 -> 伏笔内容列表 的映射
        """
        plan = {
            85: ["通灵宝玉忽然失色"],
            88: ["道士预言假作真时真亦假"],
            92: ["凤姐冷笑有情人终成眷属"],
            95: ["紫鹃藏起黛玉亲笔信", "宝玉梦中惊叫林妹妹"],
            102: ["贾母感叹孩子们有主见"],
            112: ["回顾当初风波，感慨万千"]
        }
        
        # 自动埋设伏笔
        for chapter, contents in plan.items():
            for content in contents:
                # 计算回收章节（默认10章后回收）
                target = chapter + 10
                if target > 120:
                    target = 120
                self.plant_seed(chapter, content, target, "major")
        
        return plan


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("🔗 ForeshadowingManager 测试")
    print("=" * 60)
    
    manager = ForeshadowingManager()
    
    # 埋设伏笔
    seed1 = manager.plant_seed(85, "通灵宝玉失色", 95, "crucial")
    seed2 = manager.plant_seed(88, "道士预言", 98, "major")
    print(f"✅ 埋设伏笔: {seed1.id}, {seed2.id}")
    
    # 查看活跃伏笔
    stats = manager.get_statistics()
    print(f"📊 活跃伏笔: {stats['active']}")
    
    # 获取第95回的回收提醒
    reminders = manager.get_payoff_reminders(95)
    print(f"\n🔔 第95回提醒:")
    for r in reminders:
        print(f"   {r['message']}")
    
    # 模拟回收
    test_content = "宝玉看着通灵宝玉，想起黛玉，那块玉早已失色..."
    result = manager.validate_payoff(test_content, 95)
    print(f"\n✅ 回收验证: 已解决{result['resolved_count']}, 遗漏{result['missed_count']}")
    
    print("\n" + "=" * 60)
    print("✅ ForeshadowingManager 测试完成")
    print("=" * 60)
