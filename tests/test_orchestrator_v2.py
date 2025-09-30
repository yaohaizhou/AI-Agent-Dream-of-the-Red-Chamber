#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试V2 Orchestrator集成
验证ChapterPlannerAgent在工作流中的集成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.agents.orchestrator import OrchestratorAgent


async def test_orchestrator_v2_mock():
    """测试V2 Orchestrator（Mock模式）"""
    
    print("=" * 60)
    print("V2 Orchestrator 集成测试 - MOCK模式")
    print("=" * 60)
    
    # 1. 初始化
    print("\n[1] 初始化Orchestrator...")
    settings = Settings()
    settings.use_mock_chapter_planner = True  # 启用Mock模式
    settings.chapter_planner_prompt_version = 'v2'  # 使用V2 Prompt
    
    orchestrator = OrchestratorAgent(settings)
    print(f"✓ Orchestrator已创建: {orchestrator.name}")
    
    # 显示所有Agent
    agents = orchestrator.agents
    print(f"\n  已加载的Agents ({len(agents)}个):")
    for agent_name, agent in agents.items():
        print(f"  - {agent_name}: {agent.name}")
    
    # 验证ChapterPlannerAgent已加载
    if 'chapter_planner' in agents:
        print("\n✅ ChapterPlannerAgent已成功集成！")
    else:
        print("\n❌ ChapterPlannerAgent未找到！")
        return
    
    # 2. 准备测试数据
    print("\n[2] 准备测试数据...")
    input_data = {
        "ending": "贾府衰败势如流 往昔繁华化虚无",
        "chapters": 1,  # Mock模式测试1回
        "quality_threshold": 7.0,
        "timestamp": "2025-09-30T16:00:00"
    }
    print("✓ 测试数据准备完成")
    print(f"  用户结局: {input_data['ending']}")
    print(f"  规划章节: {input_data['chapters']}回")
    
    # 3. 执行完整流程
    print("\n[3] 执行完整工作流程...")
    import time
    start_time = time.time()
    
    result = await orchestrator.process(input_data)
    
    elapsed = time.time() - start_time
    print(f"\n  总耗时: {elapsed:.2f}秒")
    
    # 4. 检查结果
    print("\n[4] 检查结果...")
    if result.success:
        print("✓ 流程执行成功!")
        
        # 检查各阶段数据
        data = result.data
        print(f"\n  数据完整性检查:")
        print(f"  - knowledge_base: {'✓' if data.get('knowledge_base') else '✗'}")
        print(f"  - strategy: {'✓' if data.get('strategy') else '✗'}")
        print(f"  - chapter_plan: {'✓' if data.get('chapter_plan') else '✗'} [V2新增]")
        print(f"  - content: {'✓' if data.get('content') else '✗'}")
        print(f"  - quality: {'✓' if data.get('quality') else '✗'}")
        
        # 显示章节规划摘要
        chapter_plan = data.get('chapter_plan', {})
        if chapter_plan:
            metadata = chapter_plan.get('metadata', {})
            chapters = chapter_plan.get('chapters', [])
            print(f"\n  章节规划摘要:")
            print(f"  - 规划版本: {metadata.get('version', 'N/A')}")
            print(f"  - 规划章节数: {metadata.get('total_chapters', 0)}")
            print(f"  - 起始章节: 第{metadata.get('start_chapter', '?')}回")
            
            if chapters:
                first_chapter = chapters[0]
                title = first_chapter.get('chapter_title', {})
                print(f"\n  第一回标题:")
                print(f"  {title.get('first_part', '?')} / {title.get('second_part', '?')}")
        
        print("\n✅ V2 Orchestrator集成测试通过！")
    else:
        print("✗ 流程执行失败!")
        print(f"  错误信息: {result.message}")
        print(f"  错误数据: {result.data}")


async def test_orchestrator_v2_real():
    """测试V2 Orchestrator（真实API模式）"""
    
    print("=" * 60)
    print("V2 Orchestrator 集成测试 - 真实API模式")
    print("=" * 60)
    
    # 1. 初始化
    print("\n[1] 初始化Orchestrator...")
    settings = Settings()
    settings.use_mock_chapter_planner = False  # 禁用Mock模式
    settings.chapter_planner_prompt_version = 'v2'  # 使用V2 Prompt
    
    orchestrator = OrchestratorAgent(settings)
    print(f"✓ Orchestrator已创建: {orchestrator.name}")
    print(f"  模式: 真实API")
    
    # 2. 准备测试数据（只测试1回）
    print("\n[2] 准备测试数据...")
    input_data = {
        "ending": "贾府衰败势如流 往昔繁华化虚无",
        "chapters": 1,  # 真实模式先测试1回
        "quality_threshold": 7.0,
        "timestamp": "2025-09-30T16:00:00"
    }
    print("✓ 测试数据准备完成")
    print(f"  规划范围: 仅第81回")
    
    # 3. 执行完整流程
    print("\n[3] 执行完整工作流程（调用真实API）...")
    import time
    start_time = time.time()
    
    result = await orchestrator.process(input_data)
    
    elapsed = time.time() - start_time
    print(f"\n  总耗时: {elapsed:.2f}秒")
    
    # 4. 检查结果
    print("\n[4] 检查结果...")
    if result.success:
        print("✓ 流程执行成功!")
        
        # 保存结果
        output_dir = orchestrator.save_results(result)
        print(f"\n✓ 结果已保存到: {output_dir}")
        
        print("\n✅ V2 Orchestrator真实测试通过！")
    else:
        print("✗ 流程执行失败!")
        print(f"  错误信息: {result.message}")


if __name__ == "__main__":
    import sys
    
    print("\n开始测试 V2 Orchestrator集成\n")
    
    # 检查命令行参数
    run_mode = "mock"  # 默认Mock模式
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--real', '-r', 'real']:
            run_mode = "real"
        elif sys.argv[1] in ['--mock', '-m', 'mock']:
            run_mode = "mock"
    else:
        # 询问运行模式
        print("=" * 60)
        try:
            user_input = input("\n选择测试模式:\n  1. Mock模式 (快速，不调用API) [默认]\n  2. 真实API模式 (调用GPT-5)\n请选择 [1/2]: ")
            if user_input == '2':
                run_mode = "real"
        except EOFError:
            print("\n检测到非交互式环境，使用Mock模式。")
    
    if run_mode == "mock":
        print("\n使用Mock模式测试...")
        asyncio.run(test_orchestrator_v2_mock())
    else:
        print("\n使用真实API模式测试...")
        asyncio.run(test_orchestrator_v2_real())
    
    print("\n" + "=" * 60)
    print("提示:")
    print("  - Mock模式: python tests/test_orchestrator_v2.py --mock")
    print("  - 真实模式: python tests/test_orchestrator_v2.py --real")
    print("=" * 60)
