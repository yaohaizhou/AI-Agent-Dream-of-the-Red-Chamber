#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评分瓶颈分析
找出影响评分的关键因素
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

content_lower = test_content.lower()

print("=" * 70)
print("🔍 评分瓶颈分析")
print("=" * 70)

# 检查关键词库
print("\n📋 关键词库匹配分析:")
agent_keywords = agent.character_keywords

for char_name, char_info in characters.items():
    print(f"\n{'='*50}")
    print(f"👤 {char_name}")
    print(f"{'='*50}")
    
    # 查找对应的关键词数据
    char_key = None
    for key in agent_keywords.keys():
        if key in char_name or char_name in key:
            char_key = key
            break
    
    if char_key:
        char_data = agent_keywords[char_key]
        
        # 语言风格
        speech = char_data.get("speech", {})
        high_kw = speech.get("high_weight", [])
        medium_kw = speech.get("medium_weight", [])
        
        high_matches = [kw for kw in high_kw if kw in content_lower]
        medium_matches = [kw for kw in medium_kw if kw in content_lower]
        
        print(f"\n  语言风格关键词:")
        print(f"    高权重 ({len(high_kw)}个): 命中 {len(high_matches)}个 - {high_matches}")
        print(f"    中权重 ({len(medium_kw)}个): 命中 {len(medium_matches)}个 - {medium_matches}")
        
        # 行为
        behavior = char_data.get("behavior", {})
        actions = behavior.get("actions", [])
        emotions = behavior.get("emotions", [])
        
        action_matches = [kw for kw in actions if kw in content_lower]
        emotion_matches = [kw for kw in emotions if kw in content_lower]
        
        print(f"\n  行为关键词:")
        print(f"    动作 ({len(actions)}个): 命中 {len(action_matches)}个 - {action_matches}")
        print(f"    情感 ({len(emotions)}个): 命中 {len(emotion_matches)}个 - {emotion_matches}")
        
        # 内容中的实际关键词
        print(f"\n  内容中实际包含的关键词:")
        content_keywords = []
        for kw in ["妹妹", "身子", "难过", "泪", "叹气", "诗", "病"]:
            if kw in content_lower:
                content_keywords.append(kw)
        print(f"    {content_keywords}")

print("\n" + "=" * 70)
print("💡 优化建议:")
print("  1. 添加更多常见词到关键词库 (如: 身子, 难过)")
print("  2. 扩展同义词覆盖")
print("  3. 提高权重分配灵活性")
print("=" * 70)
