#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import asyncio
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
    "宝玉": {
        "性格": "纯真善良 叛逆封建 礼教反对者 情感细腻 尊重女性",
        "典型行为": "关心女性 逃避仕途经济 喜欢诗词",
        "语言特点": "温和体贴 对女性尊重 有时叛逆"
    },
    "黛玉": {
        "性格": "聪慧敏感 多愁善感 才华横溢 个性率真",
        "典型行为": "写诗作词 体弱多病 多疑敏感",
        "语言特点": "机智尖锐 带有诗意 有时尖刻"
    }
}

print("=" * 60)
print("🔍 评分计算详情")
print("=" * 60)

total_score = 5.0  # 基础分
print(f"\n基础分: {total_score}")

for char_name, char_info in characters.items():
    if char_name in test_content:
        print(f"\n{'='*40}")
        print(f"👤 {char_name}")
        print(f"{'='*40}")
        
        # 关键词库评分
        enhanced = agent._check_with_keywords_db(test_content, char_name)
        enhanced_contrib = enhanced * 0.8
        print(f"  关键词库评分: {enhanced:.2f} × 0.8 = +{enhanced_contrib:.2f}")
        total_score += enhanced_contrib
        
        # 性格匹配
        personality = char_info.get("性格", "")
        trait = agent._check_personality_match(test_content, char_name, personality)
        trait_contrib = trait * 0.2
        print(f"  性格匹配: {trait:.2f} × 0.2 = +{trait_contrib:.2f}")
        total_score += trait_contrib
        
        # 行为匹配
        behavior = agent._check_behavior_consistency(test_content, char_name, char_info)
        behavior_contrib = behavior * 0.15
        print(f"  行为匹配: {behavior:.2f} × 0.15 = +{behavior_contrib:.2f}")
        total_score += behavior_contrib
        
        # 对话匹配
        dialogue = agent._check_dialogue_consistency(test_content, char_name, char_info)
        dialogue_contrib = dialogue * 0.15
        print(f"  对话匹配: {dialogue:.2f} × 0.15 = +{dialogue_contrib:.2f}")
        total_score += dialogue_contrib

print(f"\n{'='*60}")
print(f"📊 总分: {total_score:.1f}/10.0")
print(f"{'='*60}")
