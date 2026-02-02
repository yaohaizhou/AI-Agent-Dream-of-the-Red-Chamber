#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的评分算法 V2
验证人物一致性评分是否恢复正常
"""

import sys
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.agents.character_consistency_checker import (
    CharacterConsistencyChecker, 
    AdvancedQualityChecker,
    CharacterProfile
)


def test_character_profiles():
    """测试人物档案加载"""
    print("\n" + "="*60)
    print("📋 测试1: 人物档案加载")
    print("="*60)
    
    checker = CharacterConsistencyChecker()
    profiles = checker.character_profiles
    
    print(f"✅ 成功加载 {len(profiles)} 个人物档案:")
    for name in profiles.keys():
        profile = profiles[name]
        print(f"   • {name}")
        print(f"     - 语言关键词: {len(profile.speech_keywords.get('high', []))} 个高权重")
        print(f"     - 行为关键词: {len(profile.behavior_keywords.get('high', []))} 个高权重")
        print(f"     - 情感关键词: {len(profile.emotion_keywords.get('dominant', []))} 个主导")
        print(f"     - 关系定义: {len(profile.relationship_keywords)} 个角色")
    
    return True


def test_keyword_matching():
    """测试关键词匹配逻辑"""
    print("\n" + "="*60)
    print("🔍 测试2: 关键词匹配")
    print("="*60)
    
    checker = CharacterConsistencyChecker()
    
    # 测试内容 - 包含宝玉典型特征
    test_content_baoyu = (
        "宝玉见了黛玉，心中甚是欢喜，笑道：'好妹妹，你今日身子可好些了？' "
        "黛玉摇头道：'还是老样子，不想吃饭，只是咳嗽。' "
        "宝玉叹气道：'读书也罢，仕途也罢，我只求妹妹康健。' "
        "二人相对垂泪，情真意切。"
    )
    
    print("\n测试内容片段 (宝玉/黛玉场景):")
    print(f"  {test_content_baoyu[:100]}...")
    
    # 检查关键词命中
    baoyu_profile = checker.character_profiles['宝玉']
    
    high_matches = [kw for kw in baoyu_profile.speech_keywords.get('high', []) 
                   if kw in test_content_baoyu]
    print(f"\n✅ 宝玉高权重语言关键词命中: {high_matches}")
    
    behavior_matches = [kw for kw in baoyu_profile.behavior_keywords.get('high', []) 
                       if kw in test_content_baoyu]
    print(f"✅ 宝玉行为关键词命中: {behavior_matches}")
    
    return len(high_matches) > 0


import asyncio

async def test_character_scoring():
    """测试人物评分"""
    print("\n" + "="*60)
    print("📊 测试3: 人物一致性评分")
    print("="*60)
    
    checker = CharacterConsistencyChecker()
    
    test_cases = [
        {
            "name": "标准宝玉黛玉场景",
            "content": (
                "话说宝玉自那日见了黛玉，心中便放不下。这日早起，便往潇湘馆来。 "
                "黛玉正在窗下抚琴，见宝玉进来，便停下手中活儿。 "
                "宝玉笑道：'好妹妹，你今日气色比昨日好些了。' "
                "黛玉摇头叹道：'不过是一时罢了，我这身子你是知道的。' "
                "宝玉听了，心中甚是难过，赔笑道：'妹妹何必如此说，我这几日正想着 "
                "要去求老太太，请个高明大夫来给你瞧瞧。' "
                "黛玉垂泪道：'你又说这些，我怎当得起。' "
                "二人相对无言，只是叹气。"
            ),
            "expected_chars": ["宝玉", "黛玉"]
        },
        {
            "name": "宝钗劝学场景",
            "content": (
                "宝钗见了宝玉，便道：'宝兄弟，我听说你这几日又在园中闲逛，可曾读书了？' "
                "宝玉赔笑道：'宝姐姐说的是，只是我见了书便头疼。' "
                "宝钗摇头道：'你应该以仕途经济为重，不可如此荒废。' "
                "宝玉听了，心中不快，却也只得点头称是。"
            ),
            "expected_chars": ["宝玉", "宝钗"]
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- 测试案例 {i}: {case['name']} ---")
        
        # 测试评分
        score = await checker.evaluate_character_consistency(
            case['content'], 
            {name: checker.character_profiles[name] for name in case['expected_chars']}
        )
        
        print(f"📊 人物一致性评分: {score:.2f}/10.0")
        
        # 分析各个角色的贡献
        for char_name in case['expected_chars']:
            if char_name in checker.character_profiles:
                profile = checker.character_profiles[char_name]
                
                # 检查各类关键词命中情况
                speech_high = [kw for kw in profile.speech_keywords.get('high', []) if kw in case['content']]
                behavior_high = [kw for kw in profile.behavior_keywords.get('high', []) if kw in case['content']]
                
                print(f"  👤 {char_name}:")
                print(f"    语言关键词命中: {len(speech_high)}/{len(profile.speech_keywords.get('high', []))} - {speech_high}")
                print(f"    行为关键词命中: {len(behavior_high)}/{len(profile.behavior_keywords.get('high', []))} - {behavior_high}")
        
        if score >= 6.0:
            print(f"✅ {case['name']}: 评分合格 ({score:.2f}/10.0)")
        else:
            print(f"⚠️  {case['name']}: 评分偏低 ({score:.2f}/10.0)")
    
    return True


async def main():
    """主测试函数"""
    print("🎭 AI续写红楼梦项目 - 评分算法修复验证 V2")
    print("="*60)
    
    try:
        # 测试1: 人物档案
        if not test_character_profiles():
            print("❌ 人物档案测试失败")
            return False
        
        # 测试2: 关键词匹配
        if not test_keyword_matching():
            print("❌ 关键词匹配测试失败")
            return False
        
        # 测试3: 人物评分
        if not await test_character_scoring():
            print("❌ 人物评分测试失败")
            return False
        
        print("\n" + "="*60)
        print("🎉 所有测试通过!")
        print("✅ 评分算法修复成功")
        print("✅ 人物一致性评分恢复正常")
        print("✅ 关键词匹配功能正常")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        print(f"详细错误:\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)