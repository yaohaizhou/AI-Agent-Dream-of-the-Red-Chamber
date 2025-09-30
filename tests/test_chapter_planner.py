#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ChapterPlannerAgent
验证章节规划功能
@author: heai
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.agents.real.chapter_planner_agent import ChapterPlannerAgent


async def test_chapter_planner_mock():
    """测试ChapterPlannerAgent的Mock模式（快速测试，不调用API）"""
    
    print("=" * 60)
    print("ChapterPlannerAgent 测试 - MOCK模式")
    print("=" * 60)
    
    # 1. 初始化设置和Agent
    print("\n[1] 初始化ChapterPlannerAgent (Mock模式)...")
    settings = Settings()
    settings.use_mock_chapter_planner = True  # 启用mock模式
    agent = ChapterPlannerAgent(settings)
    print(f"✓ Agent已创建: {agent.name}")
    print(f"  模式: MOCK (不调用API)")
    print(f"  状态: {agent.status}")
    
    # 2. 准备测试数据
    print("\n[2] 准备测试数据...")
    input_data = {
        "user_ending": "贾府衰败势如流 往昔繁华化虚无",
        "overall_strategy": {
            "user_ending": "贾府衰败势如流 往昔繁华化虚无",
            "compatibility_score": 0.95,
            "narrative_approach": "渐进式发展",
            "major_themes": ["家族命运", "爱情悲剧", "人性觉醒"]
        },
        "knowledge_base": {
            "characters": {
                "贾宝玉": {"description": "性格纯真，不喜功名"},
                "林黛玉": {"description": "聪慧多才，多愁善感"},
                "薛宝钗": {"description": "端庄贤惠，世故圆滑"}
            }
        },
        "chapters_count": 10,  # Mock模式可以测试更多回
        "start_chapter": 81
    }
    print("✓ 测试数据准备完成")
    print(f"  规划章节: {input_data['start_chapter']}-{input_data['start_chapter'] + input_data['chapters_count'] - 1}回")
    
    # 3. 执行章节规划
    print("\n[3] 执行章节规划 (Mock模式)...")
    import time
    start_time = time.time()
    
    result = await agent.process(input_data)
    
    elapsed = time.time() - start_time
    print(f"  耗时: {elapsed:.2f}秒")
    
    # 4. 检查结果
    print("\n[4] 检查规划结果...")
    if result.success:
        print("✓ 章节规划成功!")
        chapters_plan = result.data
        
        # 显示前3回的标题
        chapters = chapters_plan.get("chapters", [])
        print(f"\n  已规划{len(chapters)}回，前3回标题:")
        for chapter in chapters[:3]:
            title = chapter.get("chapter_title", {})
            print(f"  第{chapter.get('chapter_number')}回: {title.get('first_part')} / {title.get('second_part')}")
        
        # 保存结果
        output_file = project_root / "output" / "test_chapters_plan_mock.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chapters_plan, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Mock规划结果已保存到: {output_file}")
        print("\n✅ Mock模式测试通过！")
    else:
        print("✗ 章节规划失败!")
        print(f"  错误: {result.message}")


async def test_chapter_planner():
    """测试ChapterPlannerAgent的基本功能（真实API调用）"""
    
    print("=" * 60)
    print("ChapterPlannerAgent 测试 - 真实API模式")
    print("=" * 60)
    
    # 1. 初始化设置和Agent
    print("\n[1] 初始化ChapterPlannerAgent...")
    settings = Settings()
    agent = ChapterPlannerAgent(settings)
    print(f"✓ Agent已创建: {agent.name}")
    print(f"  状态: {agent.status}")
    
    # 2. 准备测试数据
    print("\n[2] 准备测试数据...")
    input_data = {
        "user_ending": "贾府衰败势如流 往昔繁华化虚无",
        "overall_strategy": {
            "user_ending": "贾府衰败势如流 往昔繁华化虚无",
            "compatibility_score": 0.95,
            "narrative_approach": "渐进式发展",
            "major_themes": ["家族命运", "爱情悲剧", "人性觉醒"],
            "character_fates": {
                "贾宝玉": "出家",
                "林黛玉": "香消玉殒",
                "薛宝钗": "独守空闺"
            }
        },
        "knowledge_base": {
            "characters": {
                "贾宝玉": {"description": "性格纯真，不喜功名"},
                "林黛玉": {"description": "聪慧多才，多愁善感"},
                "薛宝钗": {"description": "端庄贤惠，世故圆滑"}
            },
            "relationships": {},
            "plotlines": []
        },
        "chapters_count": 5,  # 先测试5回，完整的是40回
        "start_chapter": 81
    }
    print("✓ 测试数据准备完成")
    print(f"  用户结局: {input_data['user_ending']}")
    print(f"  规划章节: {input_data['start_chapter']}-{input_data['start_chapter'] + input_data['chapters_count'] - 1}回")
    
    # 3. 执行章节规划
    print("\n[3] 执行章节规划...")
    print("  注意: 这将调用GPT-5 API，可能需要几分钟时间...")
    
    result = await agent.process(input_data)
    
    # 4. 检查结果
    print("\n[4] 检查规划结果...")
    if result.success:
        print("✓ 章节规划成功!")
        print(f"  消息: {result.message}")
        
        # 解析结果数据
        chapters_plan = result.data
        
        # 显示元数据
        print("\n--- 元数据 ---")
        metadata = chapters_plan.get("metadata", {})
        print(f"  版本: {metadata.get('version')}")
        print(f"  创建时间: {metadata.get('created_at')}")
        print(f"  总章节数: {metadata.get('total_chapters')}")
        print(f"  范围: 第{metadata.get('start_chapter')}-{metadata.get('end_chapter')}回")
        
        # 显示全局结构
        print("\n--- 全局结构 ---")
        global_structure = chapters_plan.get("global_structure", {})
        
        narrative_phases = global_structure.get("narrative_phases", {})
        print(f"  叙事阶段数: {len(narrative_phases)}")
        for phase_name, phase_info in narrative_phases.items():
            chapters = phase_info.get("chapters", [])
            if chapters:
                print(f"  - {phase_name}: 第{min(chapters)}-{max(chapters)}回 ({len(chapters)}回)")
            else:
                print(f"  - {phase_name}: 无章节")
            desc = phase_info.get('description', '')
            if desc:
                print(f"    描述: {desc[:40]}...")
        
        major_plotlines = global_structure.get("major_plotlines", [])
        print(f"\n  主要剧情线: {len(major_plotlines)}条")
        for plotline in major_plotlines:
            print(f"  - {plotline.get('name')}")
            print(f"    优先级: {plotline.get('priority')}")
            print(f"    涉及章节: {len(plotline.get('chapters_involved', []))}回")
        
        # 显示章节详情
        print("\n--- 章节详情 ---")
        chapters = chapters_plan.get("chapters", [])
        print(f"  已规划章节数: {len(chapters)}")
        
        for i, chapter in enumerate(chapters[:3], 1):  # 只显示前3回
            print(f"\n  [{i}] 第{chapter.get('chapter_number')}回")
            title = chapter.get("chapter_title", {})
            print(f"      标题: {title.get('first_part', '')} / {title.get('second_part', '')}")
            print(f"      阶段: {chapter.get('narrative_phase')}")
            
            main_chars = chapter.get("main_characters", [])
            print(f"      主要角色: {', '.join([c.get('name', '') for c in main_chars])}")
            
            plot_points = chapter.get("main_plot_points", [])
            print(f"      情节点数: {len(plot_points)}")
            if plot_points:
                print(f"      首个情节: {plot_points[0].get('event', '')[:40]}...")
        
        if len(chapters) > 3:
            print(f"\n  ... 还有 {len(chapters) - 3} 回未显示")
        
        # 显示角色分布
        print("\n--- 角色分布 ---")
        char_dist = chapters_plan.get("character_distribution", {})
        char_stats = char_dist.get("character_distribution", {})
        print(f"  统计角色数: {char_dist.get('total_characters', 0)}")
        print(f"  分布平衡度: {char_dist.get('distribution_balance', 0.0)}")
        
        # 显示主要角色出场情况
        main_chars = ["贾宝玉", "林黛玉", "薛宝钗"]
        for char_name in main_chars:
            if char_name in char_stats:
                stats = char_stats[char_name]
                print(f"\n  {char_name}:")
                print(f"    总出场: {stats.get('total_appearances', 0)}回")
                print(f"    主角回数: {len(stats.get('primary_role_chapters', []))}回")
                print(f"    配角回数: {len(stats.get('secondary_role_chapters', []))}回")
        
        # 显示一致性验证
        print("\n--- 一致性验证 ---")
        validation = chapters_plan.get("validation", {})
        print(f"  验证通过: {validation.get('is_consistent', False)}")
        print(f"  检查项: {validation.get('total_checks', 0)}")
        print(f"  通过项: {validation.get('passed_checks', 0)}")
        
        issues = validation.get("issues", [])
        if issues:
            print(f"\n  ⚠ 发现问题:")
            for issue in issues:
                print(f"    - {issue}")
        
        suggestions = validation.get("suggestions", [])
        if suggestions:
            print(f"\n  💡 改进建议:")
            for suggestion in suggestions[:3]:  # 只显示前3条
                print(f"    - {suggestion}")
        
        # 5. 保存结果
        print("\n[5] 保存规划结果...")
        output_file = project_root / "output" / "test_chapters_plan.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chapters_plan, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 规划结果已保存到: {output_file}")
        
        print("\n" + "=" * 60)
        print("测试完成！ChapterPlannerAgent运行正常。")
        print("=" * 60)
        
    else:
        print("✗ 章节规划失败!")
        print(f"  错误信息: {result.message}")
        print(f"  状态: {agent.status}")
        
        if result.data:
            print(f"\n  详细信息:")
            print(json.dumps(result.data, ensure_ascii=False, indent=2))


async def test_default_structure():
    """测试默认结构生成（不调用API）"""
    
    print("\n" + "=" * 60)
    print("测试默认结构生成（离线模式）")
    print("=" * 60)
    
    settings = Settings()
    agent = ChapterPlannerAgent(settings)
    
    # 测试默认全局结构
    print("\n[1] 测试默认全局结构...")
    global_structure = agent._create_default_global_structure(81, 40, "测试结局")
    
    print(f"✓ 叙事阶段: {len(global_structure['narrative_phases'])}")
    for phase_name, phase_info in global_structure['narrative_phases'].items():
        chapters = phase_info['chapters']
        print(f"  - {phase_name}: {min(chapters)}-{max(chapters)} ({len(chapters)}回)")
    
    print(f"\n✓ 主要剧情线: {len(global_structure['major_plotlines'])}")
    for plotline in global_structure['major_plotlines']:
        print(f"  - {plotline['name']}: {len(plotline['chapters_involved'])}回")
    
    # 测试默认章节详情
    print("\n[2] 测试默认章节详情...")
    chapter_detail = agent._create_default_chapter_detail(81, "setup")
    
    print(f"✓ 章节号: {chapter_detail['chapter_number']}")
    print(f"  标题: {chapter_detail['chapter_title']['first_part']} / {chapter_detail['chapter_title']['second_part']}")
    print(f"  主要角色: {len(chapter_detail['main_characters'])}位")
    print(f"  情节点: {len(chapter_detail['main_plot_points'])}个")
    
    print("\n✓ 默认结构生成功能正常")


if __name__ == "__main__":
    import sys
    
    print("\n开始测试 ChapterPlannerAgent\n")
    
    # 先测试默认结构（不需要API）
    asyncio.run(test_default_structure())
    
    # 检查命令行参数
    run_mode = "mock"  # 默认运行mock模式
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--full', '-f', 'full']:
            run_mode = "full"
        elif sys.argv[1] in ['--mock', '-m', 'mock']:
            run_mode = "mock"
    else:
        # 询问运行模式
        print("\n" + "=" * 60)
        try:
            user_input = input("\n选择测试模式:\n  1. Mock模式 (快速，不调用API) [默认]\n  2. 完整模式 (调用GPT-5 API)\n请选择 [1/2]: ")
            if user_input == '2':
                run_mode = "full"
        except EOFError:
            print("\n检测到非交互式环境，使用Mock模式。")
    
    if run_mode == "mock":
        print("\n使用Mock模式测试...")
        asyncio.run(test_chapter_planner_mock())
    else:
        print("\n使用完整模式测试...")
        asyncio.run(test_chapter_planner())
    
    print("\n" + "=" * 60)
    print("提示:")
    print("  - Mock模式: python tests/test_chapter_planner.py --mock")
    print("  - 完整模式: python tests/test_chapter_planner.py --full")
    print("=" * 60)
