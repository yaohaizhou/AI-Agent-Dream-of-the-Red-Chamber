#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合质量评估测试
验证所有评分维度
"""

import sys
import asyncio
sys.path.append('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber')

from src.agents.real.quality_checker_agent import QualityCheckerAgent
from src.config.settings import Settings

# 测试内容
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

context = {
    "characters": {
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
}

chapter_info = {
    "chapter_num": 81,
    "title": "第八十一回 占旺相四美钓游鱼 奉严词两番入家塾"
}

settings = Settings()
agent = QualityCheckerAgent(settings)

async def test():
    print("=" * 70)
    print("🎭 综合质量评估测试")
    print("=" * 70)
    
    # 测试各维度评分
    print("\n📊 各维度评分:")
    
    style_score = await agent._evaluate_style_consistency(test_content, context)
    print(f"  风格一致性: {style_score:.1f}/10.0")
    
    char_score = await agent._evaluate_character_accuracy(test_content, context)
    print(f"  人物一致性: {char_score:.1f}/10.0")
    
    plot_score = await agent._evaluate_plot_reasonability(test_content, chapter_info, context)
    print(f"  情节合理性: {plot_score:.1f}/10.0")
    
    literary_score = await agent._evaluate_literary_quality(test_content, chapter_info)
    print(f"  文学质量: {literary_score:.1f}/10.0")
    
    # 计算综合评分
    weights = {
        "style_consistency": 0.3,
        "character_accuracy": 0.3,
        "plot_reasonability": 0.25,
        "literary_quality": 0.15
    }
    
    overall = (
        style_score * weights["style_consistency"] +
        char_score * weights["character_accuracy"] +
        plot_score * weights["plot_reasonability"] +
        literary_score * weights["literary_quality"]
    )
    
    print("\n" + "=" * 70)
    print(f"📈 综合评分: {overall:.1f}/10.0")
    print("=" * 70)
    
    if overall >= 8.0:
        print("\n✅ 优秀！系统质量达到高标准")
    elif overall >= 7.0:
        print("\n✅ 良好！系统质量达标")
    else:
        print("\n⚠️ 需要继续优化")
    
    return overall

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result >= 7.0 else 1)
