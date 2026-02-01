#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试 - 查看评分计算过程
"""

import sys
sys.path.append('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber')

from src.agents.real.quality_checker_agent import QualityCheckerAgent
from src.config.settings import Settings

# 测试内容
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

# 人物信息
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

# 测试各个检查方法
content_lower = test_content.lower()

print("=" * 60)
print("🔍 详细评分分析")
print("=" * 60)

# 分析 personality match
print("\n📋 性格匹配分析:")
for char_name, char_info in characters.items():
    personality = char_info.get("性格", "")
    print(f"\n  {char_name}:")
    print(f"    性格描述: {personality}")
    traits = personality.split()
    print(f"    拆分成: {traits}")
    
    # 检查每个trait的匹配
    for trait in traits[:3]:  # 只检查前3个
        import re
        pattern = re.compile(r'[纯真善良叛逆封建细腻尊重聪慧敏感多愁率真]')
        found = pattern.findall(trait)
        print(f"      '{trait}' -> 可能匹配: {found}")

# 分析 behavior match
print("\n📋 行为匹配分析:")
for char_name, char_info in characters.items():
    behaviors = char_info.get("典型行为", "").split()
    print(f"\n  {char_name}:")
    print(f"    行为描述: {behaviors}")
    
    # 检查内容中是否有相关词
    keywords_in_content = []
    for kw in ["妹妹", "关心", "疼", "爱", "问", "诗", "病", "泪", "叹"]:
        if kw in content_lower:
            keywords_in_content.append(kw)
    print(f"    内容中发现的匹配词: {keywords_in_content}")

print("\n" + "=" * 60)
print("💡 建议:")
print("  1. 增加更多常见关键词到映射表")
print("  2. 调整基础分和权重")
print("  3. 考虑使用更简单的匹配逻辑")
print("=" * 60)
