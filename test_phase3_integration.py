#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 系统集成测试
验证所有评分组件协同工作
"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.agents.character_consistency_checker import CharacterConsistencyChecker, AdvancedQualityChecker
from src.utils.enhanced_scorer import score_content, generate_score_report


def test_all_scorers():
    """测试所有评分器的一致性"""
    print("="*70)
    print("🧪 Phase 3: 系统集成测试 - 所有评分器一致性验证")
    print("="*70)
    
    # 测试内容
    test_content = """
    话说宝玉自那日见了黛玉，心中便放不下。这日早起，便往潇湘馆来。 
    黛玉正在窗下抚琴，见宝玉进来，便停下手中活儿。 
    宝玉笑道：'好妹妹，你今日气色比昨日好些了。' 
    黛玉摇头叹道：'不过是一时罢了，我这身子你是知道的。' 
    宝玉听了，心中甚是难过，赔笑道：'妹妹何必如此说，我这几日正想着 
    要去求老太太，请个高明大夫来给你瞧瞧。' 
    黛玉垂泪道：'你又说这些，我怎当得起。' 
    二人相对无言，只是叹气。
    """
    
    characters = ["宝玉", "黛玉"]
    
    # 测试1: CharacterConsistencyChecker
    print("\n" + "-"*70)
    print("📊 测试1: CharacterConsistencyChecker")
    print("-"*70)
    
    async def check_consistency():
        checker = CharacterConsistencyChecker()
        result = await checker.check_consistency(test_content, characters)
        return result
    
    result1 = asyncio.run(check_consistency())
    print(f"✅ 综合评分: {result1['overall_score']:.2f}/10.0")
    for char, data in result1['individual_results'].items():
        print(f"   {char}: {data['score']:.2f}")
    
    # 测试2: EnhancedScorer
    print("\n" + "-"*70)
    print("📊 测试2: EnhancedScorer")
    print("-"*70)
    
    result2 = score_content(test_content, characters)
    print(f"✅ 综合评分: {result2['overall_score']:.2f}/10.0")
    for char, data in result2['individual_scores'].items():
        print(f"   {char}: {data['total_score']:.2f}")
    
    # 测试3: AdvancedQualityChecker
    print("\n" + "-"*70)
    print("📊 测试3: AdvancedQualityChecker")
    print("-"*70)
    
    async def check_quality():
        checker = AdvancedQualityChecker()
        result = await checker.comprehensive_check(
            test_content,
            {"title": "测试章节"},
            {"target_characters": characters}
        )
        return result
    
    result3 = asyncio.run(check_quality())
    print(f"✅ 综合评分: {result3['overall_score']:.2f}/10.0")
    print(f"   人物一致性: {result3['character_consistency']['overall_score']:.2f}")
    print(f"   结构完整性: {result3['structure_score']:.2f}")
    print(f"   风格一致性: {result3['style_score']:.2f}")
    
    # 对比结果
    print("\n" + "="*70)
    print("📈 评分对比")
    print("="*70)
    
    scores = {
        "CharacterConsistencyChecker": result1['overall_score'],
        "EnhancedScorer": result2['overall_score'],
        "AdvancedQualityChecker": result3['overall_score']
    }
    
    for name, score in scores.items():
        status = "✅" if score >= 7.0 else "⚠️"
        print(f"{status} {name}: {score:.2f}")
    
    # 检查一致性
    avg_score = sum(scores.values()) / len(scores)
    variance = max(scores.values()) - min(scores.values())
    
    print(f"\n平均分: {avg_score:.2f}")
    print(f"分差: {variance:.2f}")
    
    if variance <= 3.0:
        print("✅ 评分器一致性良好")
    else:
        print("⚠️ 评分器差异较大，需要进一步调优")
    
    # 最终判断
    print("\n" + "="*70)
    print("🎯 最终评估")
    print("="*70)
    
    all_passed = all(s >= 7.0 for s in scores.values())
    if all_passed:
        print("✅ 所有评分器评分均达到7.0+目标！")
        print("🎉 Phase 3 系统集成测试通过！")
    else:
        print("⚠️ 部分评分器未达到7.0目标")
        print("需要进一步优化")
    
    return all_passed


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*70)
    print("🔍 边界情况测试")
    print("="*70)
    
    # 空内容
    empty_content = ""
    result = score_content(empty_content, ["宝玉"])
    print(f"✅ 空内容测试: {result['overall_score']:.2f}")
    
    # 无人物内容
    no_char_content = "话说这园中景色宜人，花鸟鱼虫各得其乐。"
    result = score_content(no_char_content, ["宝玉"])
    print(f"✅ 无人物内容测试: {result['overall_score']:.2f}")
    
    # 短内容
    short_content = "宝玉笑道：'好妹妹，你好些了。'"
    result = score_content(short_content, ["宝玉", "黛玉"])
    print(f"✅ 短内容测试: {result['overall_score']:.2f}")
    
    print("✅ 边界情况测试完成")


if __name__ == "__main__":
    print("🚀 启动Phase 3系统集成测试...\n")
    
    success = test_all_scorers()
    test_edge_cases()
    
    print("\n" + "="*70)
    if success:
        print("🎉 所有测试通过！系统可以投入使用！")
        sys.exit(0)
    else:
        print("⚠️ 测试未完全通过，请检查日志")
        sys.exit(1)
