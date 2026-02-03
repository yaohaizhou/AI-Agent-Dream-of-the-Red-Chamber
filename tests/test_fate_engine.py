#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FateEngine 测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.fate_engine import FateEngine, create_fate_engine


def test_fate_engine():
    """测试 FateEngine"""
    print("=" * 60)
    print("🧪 FateEngine 测试")
    print("=" * 60)
    
    # 创建引擎
    engine = create_fate_engine()
    print("✅ 引擎创建成功")
    
    # 测试获取人物列表
    characters = engine.get_all_characters()
    print(f"✅ 加载了 {len(characters)} 个人物: {', '.join(characters)}")
    
    # 测试获取黛玉的命运弧线（第85回 - 关键转折期）
    arc = engine.get_character_arc("林黛玉", 85)
    assert arc is not None, "获取弧线失败"
    assert arc.character == "林黛玉"
    print(f"✅ 林黛玉@第85回: {arc.current_stage}")
    print(f"   情感基调: {arc.emotional_tone}")
    
    if arc.upcoming_turning_point:
        print(f"   即将到来: 第{arc.upcoming_turning_point['章节']}回 - {arc.upcoming_turning_point['事件']}")
    
    # 测试判词
    poem = engine.get_fate_summary("林黛玉")
    assert poem is not None
    print(f"✅ 黛玉判词: {poem[:20]}...")
    
    # 测试验证功能
    test_content = "林黛玉在园中散步，宝玉陪伴在旁，二人谈论诗词。"
    result = engine.validate_plot_consistency(test_content, 85, ["林黛玉", "贾宝玉"])
    print(f"✅ 验证结果: 分数={result.score:.2f}, 有效={result.is_valid}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_fate_engine()
