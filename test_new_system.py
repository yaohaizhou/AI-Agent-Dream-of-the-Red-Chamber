#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新系统集成测试
测试所有新模块的集成功能
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.fate_engine import FateEngine, create_fate_engine
from src.core.intent_loader import IntentLoader, load_default_intent
from src.core.intent_parser import IntentParser, parse_user_intent
from src.core.plot_planner import PlotPlanner
from src.core.foreshadowing import ForeshadowingManager


def test_all_modules():
    """测试所有新模块"""
    print("=" * 70)
    print("🚀 新系统集成测试")
    print("=" * 70)
    
    # 测试1: FateEngine
    print("\n📍 测试1: FateEngine")
    engine = create_fate_engine()
    arc = engine.get_character_arc("林黛玉", 85)
    assert arc is not None
    print(f"   ✅ 黛玉@85回: {arc.current_stage}")
    
    # 测试2: IntentLoader
    print("\n📍 测试2: IntentLoader")
    intent = load_default_intent()
    assert '宏观结局' in intent
    print(f"   ✅ 默认意图加载: {intent['宏观结局']['type']}")
    
    # 测试3: IntentParser
    print("\n📍 测试3: IntentParser")
    user_input = "希望宝玉黛玉在一起，黛玉要坚强"
    parsed = parse_user_intent(user_input)
    assert parsed.macro_ending == "宝黛终成眷属"
    print(f"   ✅ 解析结果: {parsed.macro_ending}")
    
    # 测试4: PlotPlanner
    print("\n📍 测试4: PlotPlanner")
    planner = PlotPlanner(81, 40)
    plan = planner.create_master_plan("宝黛终成眷属", {})
    assert len(plan.phases) == 4
    print(f"   ✅ 总体规划: {len(plan.phases)}个阶段")
    
    # 测试5: ForeshadowingManager
    print("\n📍 测试5: ForeshadowingManager")
    fm = ForeshadowingManager()
    seed = fm.plant_seed(85, "宝玉失色", 95)
    reminders = fm.get_payoff_reminders(95)
    assert len(reminders) > 0
    print(f"   ✅ 伏笔管理: 已埋设{seed.id}")
    
    # 汇总
    print("\n" + "=" * 70)
    print("✅ 所有模块集成测试通过！")
    print("=" * 70)
    print("\n📊 新增模块:")
    print("   - FateEngine: 命运引擎 ✓")
    print("   - IntentLoader: 意图加载 ✓")
    print("   - IntentParser: 意图解析 ✓")
    print("   - PlotPlanner: 剧情规划 ✓")
    print("   - ForeshadowingManager: 伏笔管理 ✓")
    print("\n🎉 系统就绪，可以开始使用新功能！")


if __name__ == "__main__":
    test_all_modules()
