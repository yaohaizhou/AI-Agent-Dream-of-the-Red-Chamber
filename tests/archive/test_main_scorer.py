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

context = {
    "characters": {
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
}

async def test():
    print("=" * 60)
    print("🔍 主评分逻辑测试")
    print("=" * 60)
    
    score = await agent._evaluate_character_accuracy(test_content, context)
    print(f"\n人物准确性评分: {score:.1f}/10.0")
    
    # 检查关键词库是否加载成功
    print(f"\n关键词库键: {list(agent.character_keywords.keys())}")
    
    # 手动测试关键词库评分
    for char_name in ["贾宝玉", "林黛玉"]:
        kw_score = agent._check_with_keywords_db(test_content, char_name)
        print(f"{char_name} 关键词库评分: {kw_score:.2f}")

asyncio.run(test())
