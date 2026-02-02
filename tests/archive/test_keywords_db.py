#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

print("关键词库键:", list(agent.character_keywords.keys()))
print()

for char_name in ["贾宝玉", "林黛玉"]:
    score = agent._check_with_keywords_db(test_content, char_name)
    print(f"{char_name}: 关键词库评分 = {score:.2f}")
