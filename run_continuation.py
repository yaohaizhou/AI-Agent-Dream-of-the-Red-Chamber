#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI续写红楼梦 - 主程序
使用渐进式生成和高级质量检查
"""

import asyncio
import sys
from pathlib import Path
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.agents.orchestrator import OrchestratorAgent


async def main():
    """主函数"""
    print("📚 AI续写红楼梦项目启动中...")
    
    # 初始化设置
    settings = Settings()
    
    # 创建编排器
    orchestrator = OrchestratorAgent(settings)
    
    # 定义续写参数
    continuation_params = {
        "ending": "宝玉和黛玉终成眷属，贾府中兴",
        "chapters": 1,  # 先生成1回作为测试
        "quality_threshold": 8.0
    }
    
    print(f"🚀 开始续写红楼梦，参数: {continuation_params}")
    
    # 执行续写
    result = await orchestrator.continue_dream_of_red_chamber(
        ending=continuation_params["ending"],
        chapters=continuation_params["chapters"],
        quality_threshold=continuation_params["quality_threshold"]
    )
    
    print(f"✅ 续写完成! 成功: {result.success}")
    print(f"📝 消息: {result.message}")
    
    if result.success:
        # 保存结果
        output_dir = orchestrator.save_results(result)
        print(f"💾 结果已保存到: {output_dir}")
        
        # 显示质量评分
        quality_data = result.data.get("quality", {}) if result.data else {}
        overall_score = quality_data.get("overall_score", 0) if quality_data else 0
        print(f"📊 质量评分: {overall_score:.2f}/10.0")
        
        # 显示人物一致性评分
        char_consistency = quality_data.get("character_consistency", {})
        char_score = char_consistency.get("overall_score", 0) if char_consistency else 0
        print(f"👥 人物一致性: {char_score:.2f}/1.0")
    
    return result


if __name__ == "__main__":
    if sys.version_info < (3, 7):
        print("❌ 错误: 需要 Python 3.7 或更高版本")
        sys.exit(1)
    
    print("🌟 欢迎使用AI续写红楼梦系统!")
    print("=" * 50)
    
    try:
        # 运行主函数
        result = asyncio.run(main())
        
        if result.success:
            print("\n🎉 续写任务顺利完成!")
            print("📖 请查看输出目录获取生成的章节内容")
        else:
            print(f"\n❌ 续写任务失败: {result.message}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断了程序")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 程序执行出错: {str(e)}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")
        sys.exit(1)