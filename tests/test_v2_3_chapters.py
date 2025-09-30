#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2架构端到端测试 - 生成3回内容
验证完整工作流程的实际效果
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.agents.orchestrator import OrchestratorAgent


async def test_v2_3_chapters():
    """V2架构端到端测试 - 生成3回"""
    print("\n" + "=" * 80)
    print("🚀 开始V2架构端到端测试 - 生成3回内容")
    print("=" * 80)
    
    # 1. 初始化
    print("\n[1] 初始化系统...")
    settings = Settings()
    orchestrator = OrchestratorAgent(settings)
    
    # 2. 准备输入
    print("\n[2] 准备测试输入...")
    test_input = {
        "ending": "贾府衰败势如流 往昔繁华化虚无",
        "chapters": 3,  # 生成3回
        "use_mock": False  # 使用真实API
    }
    
    print(f"   - 用户结局: {test_input['ending']}")
    print(f"   - 生成回数: {test_input['chapters']}")
    print(f"   - 测试模式: 真实API调用")
    
    # 3. 执行流程
    print("\n[3] 执行V2工作流程...")
    print("   预计耗时: ~5-8分钟")
    print("   预计成本: ~$3-5")
    print("\n   工作流程:")
    print("   ├─ 步骤1: 数据预处理")
    print("   ├─ 步骤2: 策略规划")
    print("   ├─ 步骤3: 章节规划 (V2新增)")
    print("   ├─ 步骤4: 内容生成 (使用chapter_plan)")
    print("   ├─ 步骤5: 质量评估")
    print("   └─ 步骤6: 格式化输出")
    
    start_time = datetime.now()
    
    try:
        result = await orchestrator.process(test_input)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 4. 检查结果
        print("\n[4] 检查测试结果...")
        
        if result.success:
            print("   ✓ 流程执行成功!")
            
            # 提取结果数据
            data = result.data
            
            # 数据完整性检查
            print("\n   数据完整性检查:")
            checks = {
                "knowledge_base": data.get("knowledge_base") is not None,
                "strategy": data.get("strategy") is not None,
                "chapter_plan": data.get("chapter_plan") is not None,
                "content": data.get("content") is not None,
                "quality": data.get("quality") is not None
            }
            
            for key, status in checks.items():
                symbol = "✓" if status else "✗"
                if key == "chapter_plan":
                    print(f"   {symbol} {key}: {'存在' if status else '缺失'} [V2新增]")
                else:
                    print(f"   {symbol} {key}: {'存在' if status else '缺失'}")
            
            # 章节规划详情
            if checks["chapter_plan"]:
                chapter_plan = data.get("chapter_plan", {})
                metadata = chapter_plan.get("metadata", {})
                chapters = chapter_plan.get("chapters", [])
                
                print(f"\n   章节规划摘要:")
                print(f"   - 规划版本: {metadata.get('version', 'unknown')}")
                print(f"   - 规划章节数: {len(chapters)}")
                print(f"   - 起始章节: 第{metadata.get('start_chapter', 81)}回")
                
                print(f"\n   生成的章节标题:")
                for i, ch in enumerate(chapters, 1):
                    title = ch.get("chapter_title", {})
                    first = title.get("first_part", "")
                    second = title.get("second_part", "")
                    chapter_num = ch.get("chapter_number", 80 + i)
                    print(f"   第{chapter_num}回: {first} / {second}")
            
            # 生成内容详情
            if checks["content"]:
                content_data = data.get("content", {})
                chapters = content_data.get("chapters", [])
                stats = content_data.get("generation_stats", {})
                
                print(f"\n   生成内容统计:")
                print(f"   - 生成章节数: {len(chapters)}")
                print(f"   - 成功率: {stats.get('success_rate', 0)*100:.1f}%")
                print(f"   - 平均长度: {stats.get('average_length', 0):.0f}字")
                
                # 显示每回的内容预览
                print(f"\n   内容预览:")
                for i, chapter in enumerate(chapters, 1):
                    preview = chapter[:100] if len(chapter) > 100 else chapter
                    print(f"   第{80+i}回 ({len(chapter)}字): {preview}...")
            
            # 质量评估详情
            if checks["quality"]:
                quality = data.get("quality", {})
                overall_score = quality.get("overall_score", 0)
                quality_level = quality.get("quality_level", "未知")
                dimension_scores = quality.get("dimension_scores", {})
                
                print(f"\n   质量评估结果:")
                print(f"   - 综合评分: {overall_score}/10")
                print(f"   - 质量等级: {quality_level}")
                
                if dimension_scores:
                    print(f"   - 各维度评分:")
                    for dim, score in dimension_scores.items():
                        print(f"     · {dim}: {score}/10")
            
            # 耗时统计
            print(f"\n   执行统计:")
            print(f"   - 总耗时: {duration:.2f}秒 ({duration/60:.1f}分钟)")
            print(f"   - 平均每回: {duration/3:.2f}秒")
            
            # 保存结果
            output_dir = project_root / "output" / f"v2_test_3chapters_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存章节内容
            if checks["content"]:
                chapters = data.get("content", {}).get("chapters", [])
                for i, chapter in enumerate(chapters, 1):
                    chapter_file = output_dir / f"chapter_{80+i:03d}.txt"
                    chapter_file.write_text(chapter, encoding='utf-8')
                    print(f"\n   ✓ 已保存: {chapter_file}")
            
            # 保存章节规划
            if checks["chapter_plan"]:
                plan_file = output_dir / "chapter_plan.json"
                plan_file.write_text(
                    json.dumps(data.get("chapter_plan"), ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
                print(f"   ✓ 已保存: {plan_file}")
            
            # 保存质量报告
            if checks["quality"]:
                quality_file = output_dir / "quality_report.json"
                quality_file.write_text(
                    json.dumps(data.get("quality"), ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
                print(f"   ✓ 已保存: {quality_file}")
            
            # 保存完整结果
            summary_file = output_dir / "test_summary.json"
            summary = {
                "test_info": {
                    "test_name": "V2架构3回端到端测试",
                    "test_time": datetime.now().isoformat(),
                    "duration_seconds": duration,
                    "chapters_requested": 3
                },
                "data_integrity": checks,
                "performance": {
                    "total_time": duration,
                    "time_per_chapter": duration / 3
                }
            }
            summary_file.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f"   ✓ 已保存: {summary_file}")
            
            print("\n" + "=" * 80)
            print("✅ V2架构端到端测试完成！")
            print("=" * 80)
            
            # 测试结论
            all_passed = all(checks.values())
            if all_passed:
                print("\n🎉 测试结论: 全部通过！V2架构工作正常！")
            else:
                print("\n⚠️  测试结论: 部分检查未通过，请查看详情")
            
            return True
            
        else:
            print(f"   ✗ 流程执行失败: {result.message}")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常:")
        print(f"   错误: {str(e)}")
        import traceback
        print(f"\n{traceback.format_exc()}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("V2架构端到端测试")
    print("测试目标: 生成3回内容，验证完整工作流程")
    print("=" * 80)
    
    # 确认执行
    print("\n⚠️  注意:")
    print("  - 将调用真实的GPT-5 API")
    print("  - 预计耗时: 5-8分钟")
    print("  - 预计成本: $3-5")
    print("  - 生成章节: 第81-83回")
    
    try:
        user_input = input("\n是否继续? [y/N]: ")
        if user_input.lower() != 'y':
            print("\n已取消测试。")
            sys.exit(0)
    except EOFError:
        print("\n检测到非交互式环境，自动开始测试...")
    
    # 运行测试
    success = asyncio.run(test_v2_3_chapters())
    
    sys.exit(0 if success else 1)
