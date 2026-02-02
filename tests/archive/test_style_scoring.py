#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试风格一致性评分改进
"""

import sys
sys.path.append('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber')

from src.agents.real.quality_checker_agent import QualityCheckerAgent
from src.config.settings import Settings

# 测试内容 - 典型的红楼梦风格
test_content = """
话说宝玉自那日见了黛玉，心中便放不下。这日早起，便往潇湘馆来。
只见黛玉正在窗下抚琴，见宝玉进来，便停下手中活儿。
宝玉笑道："好妹妹，你今日气色比昨日好些了。"
黛玉摇头叹道："不过是一时罢了，我这身子你是知道的。"
宝玉听了，心中甚是难过，赔笑道："妹妹何必如此说，我这几日正想着
要去求老太太，请个高明大夫来给你瞧瞧。"
黛玉垂泪道："你又说这些，我怎当得起。"
二人相对无言，只是叹气。

原来黛玉身子素弱，又兼心事重重，这日又受了些风寒，更觉不适。
宝玉见此情景，心中如刀割一般，忙问道："妹妹可要吃些东西？
我打发丫鬟去取。"
黛玉摇头道："不用了，你且去罢，不要因为我误了功课。"
宝玉道："功课算什么，我只愿妹妹身子康健。"

正是：
一番关切千般意，两地相思一样愁。

且听下回分解。
"""

settings = Settings()
agent = QualityCheckerAgent(settings)

print("=" * 60)
print("🎨 风格一致性评分测试")
print("=" * 60)

# 测试备用风格评估方法
style_score = agent._fallback_style_evaluation(test_content)
print(f"\n风格一致性评分: {style_score:.1f}/10.0")

if style_score >= 7.0:
    print("✅ 风格评分优秀！")
elif style_score >= 5.0:
    print("⚠️ 风格评分尚可，有提升空间")
else:
    print("❌ 风格评分偏低，需要改进")

# 检查各项命中情况
print("\n详细分析:")

classical_indicators = [
    "话说", "原来", "却说", "且听下回分解", "正是",
    "诗曰", "词曰", "只见", "但见", "忽见", "忽听",
    "次日", "当下", "且说", "不说", "再说"
]
classical_hits = [i for i in classical_indicators if i in test_content]
print(f"  古典文学特征词: {len(classical_hits)}个命中 - {classical_hits}")

wenyan_indicators = ["之", "乎", "者", "也", "矣", "焉", "哉", "耳"]
wenyan_hits = [i for i in wenyan_indicators if i in test_content]
print(f"  文言文虚词: {len(wenyan_hits)}个命中 - {wenyan_hits}")

hongloumeng_indicators = [
    "丫鬟", "嬷嬷", "太太", "老太太", "老爷", "奶奶", "姑娘",
    "小姐", "公子", "爷", "奴才", "婢子", "小的"
]
hongloumeng_hits = [i for i in hongloumeng_indicators if i in test_content]
print(f"  红楼梦特色词: {len(hongloumeng_hits)}个命中 - {hongloumeng_hits}")

dialogue_markers = ["道", "说道", "笑道", "叹道", "问道", "答道", "忙道"]
dialogue_hits = [i for i in dialogue_markers if i in test_content]
print(f"  对话标记: {len(dialogue_hits)}个命中 - {dialogue_hits}")
