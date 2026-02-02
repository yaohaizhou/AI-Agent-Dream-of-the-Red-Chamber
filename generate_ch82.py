#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第82回测试脚本
验证系统稳定性和生成质量
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.agents.orchestrator import OrchestratorAgent


async def generate_chapter_82():
    """生成第82回"""
    print("=" * 60)
    print("📚 AI红楼梦 - 生成第82回")
    print("=" * 60)
    
    # 初始化设置
    settings = Settings()
    
    # 创建编排器
    orchestrator = OrchestratorAgent(settings)
    
    # 定义续写参数 - 第82回
    continuation_params = {
        "ending": "宝玉和黛玉终成眷属，贾府中兴",
        "chapters": 1,
        "quality_threshold": 8.0,
        "start_chapter": 82  # 从第82回开始
    }
    
    print(f"🚀 开始生成第82回")
    print(f"📝 质量阈值: {continuation_params['quality_threshold']}")
    
    # 执行续写
    result = await orchestrator.continue_dream_of_red_chamber(
        ending=continuation_params["ending"],
        chapters=continuation_params["chapters"],
        quality_threshold=continuation_params["quality_threshold"]
    )
    
    print("\n" + "=" * 60)
    print("📊 生成结果")
    print("=" * 60)
    
    if result.success:
        # 保存结果
        output_dir = orchestrator.save_results(result)
        
        # 显示质量评分
        quality_data = result.data.get("quality", {}) if result.data else {}
        overall_score = quality_data.get("overall_score", 0) if quality_data else 0
        
        # 显示人物一致性评分
        char_consistency = quality_data.get("character_consistency", {})
        char_score = char_consistency.get("overall_score", 0) if char_consistency else 0
        individual_results = char_consistency.get("individual_results", {})
        
        print(f"✅ 生成成功!")
        print(f"📁 输出目录: {output_dir}")
        print(f"📊 综合评分: {overall_score:.2f}/10.0")
        print(f"👥 人物一致性: {char_score:.2f}/10.0")
        
        if individual_results:
            print("\n🎭 各人物评分:")
            for char_name, char_data in individual_results.items():
                score = char_data.get("score", 0)
                print(f"  - {char_name}: {score:.1f}/10.0")
        
        # 检查是否达标
        if overall_score >= 7.5:
            print(f"\n🎉 质量达标! 评分 {overall_score:.1f} >= 7.5")
        else:
            print(f"\n⚠️ 质量未达标: {overall_score:.1f} < 7.5")
        
        return True, overall_score
    else:
        print(f"❌ 生成失败: {result.message}")
        return False, 0


if __name__ == "__main__":
    try:
        success, score = asyncio.run(generate_chapter_82())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
