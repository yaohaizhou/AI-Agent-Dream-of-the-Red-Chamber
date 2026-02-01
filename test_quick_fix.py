#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试修复后的评分算法
验证评分是否从0.2提升到合理水平
"""

import sys
sys.path.append('/home/azureuser/code/AI-Agent-Dream-of-the-Red-Chamber')

from src.agents.real.quality_checker_agent import QualityCheckerAgent
from src.config.settings import Settings

# 测试内容 - 宝玉黛玉场景
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

# 创建质量检查器
settings = Settings()
agent = QualityCheckerAgent(settings)

# 测试人物准确性评估
import asyncio

async def test():
    print("=" * 60)
    print("🧪 测试修复后的评分算法")
    print("=" * 60)
    
    # 测试人物评估
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
    
    score = await agent._evaluate_character_accuracy(test_content, context)
    print(f"\n📊 人物准确性评分: {score:.1f}/10.0")
    
    if score >= 4.0:
        print("✅ 修复成功！评分已达到合理水平 (≥4.0)")
    elif score >= 2.0:
        print("⚠️  有所改善，但仍有提升空间 (2.0-4.0)")
    else:
        print("❌ 评分仍然偏低，需要进一步优化 (<2.0)")
    
    # 与修复前对比
    print(f"\n📈 对比:")
    print(f"   修复前: 0.2/10.0")
    print(f"   修复后: {score:.1f}/10.0")
    print(f"   提升: {(score - 0.2):.1f}分 ({(score / 0.2):.1f}x)")
    
    return score

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result >= 4.0 else 1)
