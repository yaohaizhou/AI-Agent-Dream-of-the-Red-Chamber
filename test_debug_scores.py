#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试测试 - 查看各项分数
"""

import sys
sys.path.append('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber')

from src.agents.real.quality_checker_agent import QualityCheckerAgent
from src.config.settings import Settings

test_content = """
话说宝玉自那日见了黛玉，心中便放不下。这日早起，便往潇湘馆来。
黛玉正在窗下抚琴，见宝玉进来，便停下手中活儿。
宝玉笑道："好妹妹，你今日气色比昨日好些了。"
黛玉摇头叹道："不过是一时罢了，我这身子你是知道的。"
宝玉听了，心中甚是难过，赔笑道："妹妹何必如此说，我这几日正想着
要去求老太太，请个高明大夫来给你瞧瞧。"
黛玉垂泪道："你又说这些，我怎当得起。"
二人相对无言，只是叹气。
"""

settings = Settings()
agent = QualityCheckerAgent(settings)

characters = {
    "贾宝玉": {
        "性格": "纯真善良 叛逆封建 礼教反对者 情感细腻 尊重女性",
        "典型行为": "关心女性 逃避仕途经济 喜欢诗词",
        "语言特点": "温和体贴 对女性尊重 有时叛逆"
    },
    "林黛玉": {
        "性格": "聪慧敏感 多愁善感 才华横溢 个性率真",
        "典型行为": "写诗作词 体弱多病 多疑敏感",
        "语言特点": "机智尖锐 带有诗意 有时尖刻"
    }
}

# 直接调用各个检查方法
content_lower = test_content.lower()

print("=" * 60)
print("🔍 各项评分详细分析")
print("=" * 60)

total_score = 5.0  # 基础分
print(f"\n基础分: {total_score}")

for char_name, char_info in characters.items():
    print(f"\n{'='*40}")
    print(f"👤 {char_name}")
    print(f"{'='*40}")
    
    # 性格匹配
    personality_traits = char_info.get("性格", "")
    trait_match = agent._check_personality_match(test_content, char_name, personality_traits)
    print(f"  性格匹配度: {trait_match:.2f} (权重0.8) -> +{trait_match * 0.8:.2f}")
    total_score += trait_match * 0.8
    
    # 行为匹配
    behavior_match = agent._check_behavior_consistency(test_content, char_name, char_info)
    print(f"  行为匹配度: {behavior_match:.2f} (权重0.6) -> +{behavior_match * 0.6:.2f}")
    total_score += behavior_match * 0.6
    
    # 对话匹配
    dialogue_match = agent._check_dialogue_consistency(test_content, char_name, char_info)
    print(f"  对话匹配度: {dialogue_match:.2f} (权重0.7) -> +{dialogue_match * 0.7:.2f}")
    total_score += dialogue_match * 0.7
    
    # 关系匹配
    relationship_match = agent._check_relationship_consistency(test_content, char_name, characters)
    print(f"  关系匹配度: {relationship_match:.2f} (权重0.5) -> +{relationship_match * 0.5:.2f}")
    total_score += relationship_match * 0.5

print(f"\n{'='*60}")
print(f"📊 总评分: {total_score:.1f}/10.0")
print(f"{'='*60}")
