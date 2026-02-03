#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PlotPlanner - 多章剧情规划器
实现40回的整体连贯性规划
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class Phase:
    """剧情阶段"""
    name: str
    chapters: range
    theme: str
    emotional_arc: str
    key_tasks: List[str] = field(default_factory=list)


@dataclass
class ChapterPlan:
    """单章计划"""
    chapter_num: int
    phase: Phase
    title: str
    scenes: List[Dict[str, Any]]
    characters: List[str]
    cliffhanger: str
    foreshadowing: List[str] = field(default_factory=list)


@dataclass
class MasterPlan:
    """总体规划"""
    total_chapters: int
    start_chapter: int
    phases: List[Phase]
    chapter_plans: Dict[int, ChapterPlan] = field(default_factory=dict)


class PlotPlanner:
    """
    多章剧情规划器
    
    功能：
    1. 创建40回总体规划
    2. 分四阶段设计（铺垫/冲突/转折/结局）
    3. 确保章节间连贯性
    4. 管理伏笔埋设与回收
    """
    
    def __init__(
        self,
        start_chapter: int = 81,
        total_chapters: int = 40
    ):
        self.start_chapter = start_chapter
        self.total_chapters = total_chapters
        self.end_chapter = start_chapter + total_chapters - 1
    
    def create_master_plan(
        self,
        user_ending: str,
        character_fates: Dict[str, Any]
    ) -> MasterPlan:
        """
        创建总体规划
        
        Args:
            user_ending: 用户期望结局
            character_fates: 人物命运配置
            
        Returns:
            MasterPlan 总体规划
        """
        phases = self._create_phases()
        
        plan = MasterPlan(
            total_chapters=self.total_chapters,
            start_chapter=self.start_chapter,
            phases=phases
        )
        
        # 为每一章创建详细计划
        for chapter_num in range(self.start_chapter, self.end_chapter + 1):
            chapter_plan = self._plan_single_chapter(
                chapter_num,
                phases,
                user_ending,
                character_fates
            )
            plan.chapter_plans[chapter_num] = chapter_plan
        
        return plan
    
    def _create_phases(self) -> List[Phase]:
        """创建四阶段规划"""
        return [
            Phase(
                name="山雨欲来",
                chapters=range(81, 91),
                theme="表面平静，暗流涌动",
                emotional_arc="乐→疑",
                key_tasks=[
                    "埋下金玉良缘伏笔",
                    "展现宝黛感情深化",
                    "描写贾府内部矛盾",
                    "凤姐失势的开端"
                ]
            ),
            Phase(
                name="风云突变",
                chapters=range(91, 101),
                theme="矛盾爆发，命运转折",
                emotional_arc="疑→悲→惊",
                key_tasks=[
                    "金玉良缘逼迫成形",
                    "黛玉假死出府",
                    "宝玉逃婚寻找",
                    "贾府危机初现"
                ]
            ),
            Phase(
                name="绝处逢生",
                chapters=range(101, 111),
                theme="峰回路转，柳暗花明",
                emotional_arc="惊→喜→稳",
                key_tasks=[
                    "宝黛意外重逢",
                    "真相大白",
                    "贾府接纳黛玉",
                    "宝黛订婚"
                ]
            ),
            Phase(
                name="圆满收场",
                chapters=range(111, 121),
                theme="尘埃落定，各得其所",
                emotional_arc="稳→乐",
                key_tasks=[
                    "宝黛大婚",
                    "贾府中兴",
                    "人物归宿",
                    "圆满结局"
                ]
            )
        ]
    
    def _plan_single_chapter(
        self,
        chapter_num: int,
        phases: List[Phase],
        user_ending: str,
        character_fates: Dict[str, Any]
    ) -> ChapterPlan:
        """规划单章内容"""
        # 确定所属阶段
        phase = self._get_phase_for_chapter(chapter_num, phases)
        
        # 生成回目
        title = self._generate_chapter_title(chapter_num, phase)
        
        # 规划场景
        scenes = self._plan_scenes(chapter_num, phase)
        
        # 确定人物
        characters = self._select_characters(chapter_num, character_fates)
        
        # 设计悬念结尾
        cliffhanger = self._design_cliffhanger(chapter_num, phase)
        
        # 规划伏笔
        foreshadowing = self._plan_foreshadowing(chapter_num)
        
        return ChapterPlan(
            chapter_num=chapter_num,
            phase=phase,
            title=title,
            scenes=scenes,
            characters=characters,
            cliffhanger=cliffhanger,
            foreshadowing=foreshadowing
        )
    
    def _get_phase_for_chapter(
        self,
        chapter_num: int,
        phases: List[Phase]
    ) -> Phase:
        """获取章节所属阶段"""
        for phase in phases:
            if chapter_num in phase.chapters:
                return phase
        return phases[-1]
    
    def _generate_chapter_title(self, chapter_num: int, phase: Phase) -> str:
        """生成回目标题"""
        # 简化示例
        titles = {
            81: "秋窗风雨夕 宝黛诉衷情",
            85: "闻风声黛玉惊变 护真情宝玉立誓",
            92: "熙凤定计金玉缘 宝玉私会泪洒衫",
            95: "设计谋黛玉假死 闻噩耗宝玉疯癫",
            102: "水月庵宝黛重逢 荣国府真相大白",
            112: "结良缘宝黛大婚 庆团圆贾府重兴"
        }
        return titles.get(chapter_num, f"第{chapter_num}回")
    
    def _plan_scenes(self, chapter_num: int, phase: Phase) -> List[Dict[str, Any]]:
        """规划场景"""
        scenes = []
        
        # 根据阶段规划不同场景数
        if phase.name == "山雨欲来":
            scenes = [
                {"name": "日常场景", "location": "大观园", "mood": "平静"},
                {"name": "冲突场景", "location": "贾府", "mood": "紧张"}
            ]
        elif phase.name == "风云突变":
            scenes = [
                {"name": "危机场景", "location": "贾府", "mood": "悲痛"},
                {"name": "转折场景", "location": "外部", "mood": "惊险"}
            ]
        elif phase.name == "绝处逢生":
            scenes = [
                {"name": "重逢场景", "location": "庵堂", "mood": "悲喜交加"},
                {"name": "认亲场景", "location": "贾府", "mood": "温馨"}
            ]
        else:  # 圆满收场
            scenes = [
                {"name": "喜庆场景", "location": "贾府", "mood": "欢乐"},
                {"name": "回顾场景", "location": "大观园", "mood": "感慨"}
            ]
        
        return scenes
    
    def _select_characters(
        self,
        chapter_num: int,
        character_fates: Dict[str, Any]
    ) -> List[str]:
        """选择本章人物"""
        # 简化示例
        if chapter_num < 90:
            return ["贾宝玉", "林黛玉", "薛宝钗", "贾母"]
        elif chapter_num < 100:
            return ["贾宝玉", "林黛玉", "薛宝钗", "王熙凤", "贾母"]
        else:
            return ["贾宝玉", "林黛玉", "贾母", "王熙凤"]
    
    def _design_cliffhanger(self, chapter_num: int, phase: Phase) -> str:
        """设计悬念结尾"""
        cliffhangers = {
            85: "黛玉听闻金玉良缘，手中茶杯落地...",
            92: "宝玉转身离去，只留下一句'我偏不'...",
            95: "紫鹃看着空床，泪如雨下...",
            102: "帘后转出一人，正是黛玉...",
            112: "红烛高照，新人入洞房..."
        }
        return cliffhangers.get(chapter_num, "欲知后事如何，且听下回分解")
    
    def _plan_foreshadowing(self, chapter_num: int) -> List[str]:
        """规划伏笔"""
        # 伏笔设计：在第X回埋设，在X+10回收
        plantings = {
            85: ["通灵宝玉忽然失色 - 第95回收"],
            88: ["道士预言'假作真时真亦假' - 第98回收"],
            92: ["凤姐冷笑'有情人终成眷属' - 第102回收"],
            95: ["紫鹃藏起黛玉亲笔信 - 第102回收"]
        }
        return plantings.get(chapter_num, [])
    
    def get_chapter_plan(self, plan: MasterPlan, chapter_num: int) -> Optional[ChapterPlan]:
        """获取指定章节的计划"""
        return plan.chapter_plans.get(chapter_num)


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("📚 PlotPlanner 测试")
    print("=" * 60)
    
    planner = PlotPlanner(start_chapter=81, total_chapters=40)
    
    # 创建规划
    plan = planner.create_master_plan(
        user_ending="宝黛终成眷属",
        character_fates={}
    )
    
    print(f"\n✅ 总体规划创建成功")
    print(f"   总章节: {plan.total_chapters}")
    print(f"   阶段数: {len(plan.phases)}")
    
    # 查看第85回计划
    ch85 = planner.get_chapter_plan(plan, 85)
    if ch85:
        print(f"\n📖 第85回计划:")
        print(f"   阶段: {ch85.phase.name}")
        print(f"   标题: {ch85.title}")
        print(f"   场景: {len(ch85.scenes)}个")
        print(f"   悬念: {ch85.cliffhanger}")
        if ch85.foreshadowing:
            print(f"   伏笔: {ch85.foreshadowing}")
    
    print("\n" + "=" * 60)
    print("✅ PlotPlanner 测试完成")
    print("=" * 60)
