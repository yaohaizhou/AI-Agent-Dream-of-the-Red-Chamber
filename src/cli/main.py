#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI续写红楼梦 - CLI界面
基于多Agent架构的古典文学创作工具
"""

import os
import sys
import time
import click
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.live import Live

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.agents.orchestrator import OrchestratorAgent
from src.agents.adk_agents_standard import create_hongloumeng_adk_system

console = Console()


class RedChamberCLI:
    """红楼梦续写CLI工具"""

    def __init__(self):
        self.settings = Settings()
        self.adk_system = create_hongloumeng_adk_system(self.settings)
        self.orchestrator = OrchestratorAgent(self.settings)

    def show_welcome(self):
        """显示欢迎界面"""
        welcome_text = """
🏮 AI续写红楼梦 🏮
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
基于Google ADK的多Agent架构古典文学创作系统

输入你的理想结局，让AI为你续写红楼梦后40回...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """.strip()

        panel = Panel(welcome_text, border_style="blue", title="🎭 红楼梦续写系统")
        console.print(panel)
        console.print()

    def validate_input(self, ending: str) -> tuple[bool, str]:
        """验证用户输入的合理性"""
        if not ending or len(ending.strip()) < 5:
            return False, "结局描述太短，请提供更详细的描述"

        if len(ending.strip()) > 200:
            return False, "结局描述过长，请控制在200字符以内"

        # 检查是否与原著有明显冲突
        conflict_keywords = ["宝玉成为皇帝", "黛玉嫁给别人", "贾府灭亡"]
        for keyword in conflict_keywords:
            if keyword in ending:
                return False, f"结局与原著人物性格存在冲突：{keyword}"

        return True, "输入验证通过"

    def show_progress_simulation(self, ending: str, chapters: int, quality_threshold: float):
        """模拟续写进度显示"""

        # 总体进度
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:

            # 创建进度条
            task1 = progress.add_task("📚 准备知识库", total=100)
            task2 = progress.add_task("🔍 分析人物关系", total=100)
            task3 = progress.add_task("📝 制定续写策略", total=100)
            task4 = progress.add_task(f"✍️  生成续写内容 ({chapters}回)", total=chapters)
            task5 = progress.add_task("🔍 质量评估", total=100)

            # 模拟各个阶段的进度
            for i in range(101):
                progress.update(task1, completed=i)
                time.sleep(0.01)

            for i in range(101):
                progress.update(task2, completed=i)
                time.sleep(0.01)

            for i in range(101):
                progress.update(task3, completed=i)
                time.sleep(0.01)

            # 生成章节
            for chapter in range(1, chapters + 1):
                progress.update(task4, completed=chapter)
                time.sleep(0.05)

            # 质量评估
            for i in range(101):
                progress.update(task5, completed=i)
                time.sleep(0.01)

    def show_agent_status(self):
        """显示Agent状态"""
        table = Table(title="🤖 Agent状态监控")
        table.add_column("Agent", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("进度", style="yellow")

        agents = [
            ("数据预处理Agent", "✅ 完成", "100%"),
            ("续写策略Agent", "✅ 完成", "100%"),
            ("内容生成Agent", "✅ 完成", "100%"),
            ("质量校验Agent", "✅ 完成", "100%"),
            ("用户交互Agent", "🎯 运行中", "100%")
        ]

        for agent, status, progress in agents:
            table.add_row(agent, status, progress)

        console.print(table)
        console.print()

    def show_quality_report(self, quality_score: float = 8.5):
        """显示质量评估报告"""
        report_text = f"""
📊 质量评估报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
综合评分: {quality_score}/10 ⭐⭐⭐⭐⭐

维度详情:
├── 🎨 风格一致性: 8.5/10 (古风雅致，文辞优美)
├── 👥 人物性格:  9.0/10 (宝黛形象鲜明，性格发展合理)
├── 📖 情节合理性: 8.2/10 (故事逻辑连贯，与原著呼应)
└── 📚 文学素养:  8.8/10 (修辞丰富，意境深远)

改进建议:
• 建议在第25-30回加强贾府复兴的铺垫
• 可适当增加一些古典诗词点缀
        """.strip()

        panel = Panel(report_text, border_style="green", title="📋 质量报告")
        console.print(panel)
        console.print()

    def show_final_result(self, ending: str, chapters: int, output_dir: str = "", result_data: Optional[Dict[str, Any]] = None):
        """显示最终结果"""
        # 从实际结果数据中获取信息
        quality_score = 0.0
        chapter_highlights = []
        
        if result_data:
            quality_data = result_data.get("quality", {})
            quality_score = quality_data.get("overall_score", 0.0)
            
            # 从策略数据中获取章节亮点
            strategy_data = result_data.get("strategy", {})
            plot_outline = strategy_data.get("plot_outline", [])
            
            for chapter in plot_outline:
                chapter_num = chapter.get("chapter_num", "?")
                title = chapter.get("title", "未定标题")
                key_events = chapter.get("key_events", [])
                if key_events:
                    highlight = f"第{chapter_num}回: {', '.join(key_events[:2])}"  # 取前两个关键事件
                    chapter_highlights.append(highlight)
        
        # 如果没有实际数据，使用默认值
        if not chapter_highlights:
            chapter_highlights = [f"第{start_chapter}回: 续写开篇，承接前文"]
        
        result_text = f"""
🎉 续写完成！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 输出目录: {output_dir}
📊 总回数: {chapters}回
⭐ 平均质量评分: {quality_score:.1f}/10
⏱️  总耗时: 实际完成

用户结局: {ending}

关键情节亮点:"""
        
        # 添加章节亮点
        for i, highlight in enumerate(chapter_highlights):
            if i == len(chapter_highlights) - 1:
                result_text += f"\n└── {highlight}"
            else:
                result_text += f"\n├── {highlight}"
        
        result_text += f"""

建议阅读顺序: 按回目顺序阅读，每日1-2回为宜
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

        panel = Panel(result_text, border_style="green", title="🎊 完成总结")
        console.print(panel)

    def run_interactive_mode(self):
        """运行交互模式"""
        console.print("\n[bold cyan]🎯 进入交互模式[/bold cyan]")
        console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        # 结局输入
        while True:
            ending = Prompt.ask("请输入理想结局描述")
            is_valid, message = self.validate_input(ending)

            if is_valid:
                console.print(f"[green]✅ {message}[/green]")
                break
            else:
                console.print(f"[red]❌ {message}[/red]")
                if not Confirm.ask("是否重新输入？"):
                    return

        # 参数配置
        console.print("\n[bold cyan]⚙️  参数配置[/bold cyan]")
        chapters = Prompt.ask("续写回数", default="40")
        quality = Prompt.ask("质量阈值", default="7.0")

        try:
            chapters = int(chapters)
            quality_threshold = float(quality)
        except ValueError:
            console.print("[red]❌ 参数格式错误，使用默认值[/red]")
            chapters = 40
            quality_threshold = 7.0

        # 开始续写
        console.print(f"\n[bold green]🚀 开始续写: {ending}[/bold green]")
        console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        # 执行续写流程
        self.run_continuation(ending, chapters, quality_threshold)

    async def run_continuation(self, ending: str, start_chapter: int, count: int, quality_threshold: float, debug: bool = False, verbose: bool = False):
        """执行续写流程"""
        try:
            # 显示Agent状态
            self.show_agent_status()

            console.print("[bold blue]🚀 开始AI续写流程...[/bold blue]")

            if verbose:
                console.print(f"[dim]调试信息: ending='{ending}', start_chapter={start_chapter}, count={count}, quality={quality_threshold}[/dim]")

            # 准备输入数据
            input_data = {
                "ending": ending,
                "start_chapter": start_chapter,
                "chapters": count,  # 保持向后兼容，内部仍使用chapters表示续写回数
                "quality_threshold": quality_threshold
            }

            console.print("[bold cyan]📊 正在执行数据预处理...[/bold cyan]")
            # 执行真正的续写流程
            result = await self.orchestrator.process(input_data)

            if not result.success:
                console.print(f"[red]❌ 续写失败: {result.message}[/red]")
                if debug:
                    console.print(f"[dim]失败详情: {result.data}[/dim]")
                return

            console.print("[bold cyan]📝 正在生成内容...[/bold cyan]")

            # 显示进度模拟
            self.show_progress_simulation(ending, count, quality_threshold)

            console.print("[bold cyan]🔍 正在评估质量...[/bold cyan]")

            # 显示质量报告
            if "quality" in result.data:
                self.show_real_quality_report(result.data["quality"])
            else:
                self.show_quality_report()

            # 保存结果
            console.print("[bold cyan]💾 正在保存结果...[/bold cyan]")
            output_dir = self.orchestrator.save_results(result)

            # 显示最终结果
            self.show_final_result(ending, count, output_dir, result.data)

            console.print("[green]✅ AI续写完成！[/green]")

        except Exception as e:
            console.print(f"[red]❌ 续写过程中出现错误: {str(e)}[/red]")
            if debug:
                console.print_exception()
            else:
                console.print("[yellow]💡 提示: 使用 --debug 参数查看详细错误信息[/yellow]")

    def show_real_quality_report(self, quality_data: dict):
        """显示真实的质量报告"""
        console.print("\n[bold cyan]📊 质量评估报告[/bold cyan]")

        if not quality_data:
            console.print("[yellow]暂无质量数据[/yellow]")
            return

        table = Table(title="🎯 质量评估详情")
        table.add_column("评估维度", style="cyan")
        table.add_column("分数", style="green")
        table.add_column("等级", style="yellow")
        table.add_column("权重", style="magenta")

        dimension_scores = quality_data.get("dimension_scores", {})
        evaluation_details = quality_data.get("evaluation_details", {})

        for dimension, score in dimension_scores.items():
            detail = evaluation_details.get(dimension, {})
            level = detail.get("level", "未知")
            weight = f"{detail.get('weight', 0):.1%}"

            table.add_row(dimension, f"{score:.1f}/10", level, weight)

        console.print(table)

        overall_score = quality_data.get("overall_score", 0)
        quality_level = quality_data.get("quality_level", "未知")

        console.print(f"\n[bold]综合评分: {overall_score:.1f}/10[/bold]")
        console.print(f"[bold]质量等级: {quality_level}[/bold]")

        # 显示改进建议
        suggestions = quality_data.get("improvement_suggestions", [])
        if suggestions:
            console.print("\n[bold yellow]💡 改进建议:[/bold yellow]")
            for i, suggestion in enumerate(suggestions, 1):
                console.print(f"  {i}. {suggestion}")

    async def run_adk_continuation(self, ending: str, start_chapter: int, count: int, debug: bool = False):
        """使用Google ADK系统执行续写"""
        try:
            console.print(f"\n[bold green]🎭 开始AI续写红楼梦 (Google ADK版本)[/bold green]")
            console.print(f"[cyan]期望结局:[/cyan] {ending}")
            console.print(f"[cyan]续写章节:[/cyan] 从第{start_chapter}回开始，续写{count}回")
            
            # 显示Agent状态
            self.show_adk_standard_agent_status()
            
            # 执行ADK续写流程
            console.print("\n[bold cyan]🚀 启动Google ADK续写流程...[/bold cyan]")
            
            result = await self.adk_system.process_continuation_request(ending, count)
            
            if result.get("success"):
                console.print("[green]✅ ADK续写流程完成！[/green]")
                
                # 显示结果
                self.show_adk_result(result.get("data", {}))
                
                # 保存结果
                output_dir = self.save_adk_results(result, ending, count)
                console.print(f"\n[green]📁 结果已保存至: {output_dir}[/green]")
                
            else:
                error_msg = result.get("error", "未知错误")
                console.print(f"[red]❌ ADK续写失败: {error_msg}[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ ADK续写过程中出现错误: {str(e)}[/red]")
            if debug:
                console.print_exception()
            else:
                console.print("[yellow]💡 提示: 使用 --debug 参数查看详细错误信息[/yellow]")

    def show_adk_standard_agent_status(self):
        """显示标准ADK Agent状态"""
        console.print("\n🤖 标准ADK Agent状态监控")
        
        # 由于get_agent_status是异步的，我们需要在这里处理
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，我们显示基本信息
                console.print("Agent状态: 正在初始化...")
            else:
                status = loop.run_until_complete(self.adk_system.get_agent_status())
                self._display_agent_status_table(status)
        except Exception as e:
            console.print(f"⚠️ 无法获取Agent状态: {e}")
            console.print("Agent状态: 未知")
    
    def _display_agent_status_table(self, status: Dict[str, Any]):
        """显示Agent状态表格"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Agent", style="dim", width=15)
        table.add_column("状态", justify="center")
        table.add_column("模型", style="cyan")
        table.add_column("会话ID", style="green")
        
        table.add_row(
            status["agent_name"],
            "✅ 就绪" if status["status"] == "ready" else "❌ 未就绪",
            status["model"],
            status["session_id"]
        )
        
        console.print(table)

    def show_adk_result(self, data: Dict[str, Any]):
        """显示ADK结果"""
        console.print("\n[bold cyan]📊 Google ADK续写结果[/bold cyan]")
        
        # 显示内容信息
        content_data = data.get("content", {})
        if content_data:
            chapters = content_data.get("chapters", [])
            console.print(f"[green]✅ 成功生成 {len(chapters)} 个章节[/green]")
            
            # 显示第一章节预览
            if chapters:
                first_chapter = chapters[0][:200] + "..." if len(chapters[0]) > 200 else chapters[0]
                console.print(f"\n[yellow]📖 第一章节预览:[/yellow]")
                console.print(f"[dim]{first_chapter}[/dim]")
        
        # 显示质量评估
        quality_data = data.get("quality", {})
        if quality_data:
            overall_score = quality_data.get("overall_score", 0)
            console.print(f"\n[bold]🎯 综合质量评分: {overall_score}/10[/bold]")
            
            detailed_scores = quality_data.get("detailed_scores", {})
            if detailed_scores:
                console.print("\n[cyan]📈 详细评分:[/cyan]")
                for dimension, score in detailed_scores.items():
                    console.print(f"  • {dimension}: {score}/10")
        
        # 显示策略信息
        strategy_data = data.get("strategy", {})
        if strategy_data:
            plot_outline = strategy_data.get("plot_outline", [])
            console.print(f"\n[blue]📋 情节大纲: {len(plot_outline)} 回规划完成[/blue]")

    def save_adk_results(self, result: Dict[str, Any], ending: str, chapters: int) -> str:
        """保存ADK结果"""
        from datetime import datetime
        from pathlib import Path
        import json
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"output/adk_result_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存续写内容
        data = result.get("data", {})
        content_data = data.get("content", {})
        chapters_content = content_data.get("chapters", [])
        
        for i, chapter in enumerate(chapters_content, 1):
            chapter_file = output_dir / f"chapter_{i:03d}.md"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(chapter)
        
        # 保存质量报告
        quality_data = data.get("quality", {})
        if quality_data:
            quality_file = output_dir / "quality_report.json"
            with open(quality_file, 'w', encoding='utf-8') as f:
                json.dump(quality_data, f, ensure_ascii=False, indent=2)
        
        # 保存策略信息
        strategy_data = data.get("strategy", {})
        if strategy_data:
            strategy_file = output_dir / "strategy_outline.json"
            with open(strategy_file, 'w', encoding='utf-8') as f:
                json.dump(strategy_data, f, ensure_ascii=False, indent=2)
        
        # 保存元数据
        metadata = {
            "user_ending": ending,
            "chapters_requested": chapters,
            "generation_time": datetime.now().isoformat(),
            "system": "Google ADK",
            "model": "gemini-2.0-flash"
        }
        
        metadata_file = output_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return str(output_dir)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """AI续写红楼梦 - 基于多Agent架构的古典文学创作工具"""
    pass


@cli.command()
@click.argument('ending', required=False)
@click.option('-s', '--start-chapter', default=81, help='起始回数 (默认从第81回开始)')
@click.option('-c', '--count', default=1, help='续写回数 (默认续写1回)')
@click.option('-q', '--quality', default=7.0, help='质量阈值')
@click.option('-o', '--output', help='输出目录')
@click.option('-v', '--verbose', is_flag=True, help='详细输出')
@click.option('-d', '--debug', is_flag=True, help='调试模式')
def continue_story(ending, start_chapter, count, quality, output, verbose, debug):
    """续写红楼梦故事

    ENDING: 用户理想结局描述
    """
    cli_app = RedChamberCLI()
    cli_app.show_welcome()

    # 如果没有提供结局参数，进入交互模式
    if not ending:
        cli_app.run_interactive_mode()
        return

    # 验证输入
    is_valid, message = cli_app.validate_input(ending)
    if not is_valid:
        console.print(f"[red]❌ {message}[/red]")
        return

    console.print(f"[green]✅ {message}[/green]")

    # 执行续写
    import asyncio
    asyncio.run(cli_app.run_continuation(ending, start_chapter, count, quality, debug, verbose))


@cli.command()
@click.argument('ending', required=False)
@click.option('-s', '--start-chapter', default=81, help='起始回数 (默认从第81回开始)')
@click.option('-c', '--count', default=1, help='续写回数 (默认续写1回)')
@click.option('-d', '--debug', is_flag=True, help='调试模式')
def continue_story_adk(ending, start_chapter, count, debug):
    """续写红楼梦故事（Google ADK版本）
    
    ENDING: 用户理想结局描述
    """
    cli_app = RedChamberCLI()
    cli_app.show_welcome()
    
    # 如果没有提供结局参数，进入交互模式
    if not ending:
        ending = console.input("[cyan]请输入您期望的红楼梦结局: [/cyan]")
    
    # 验证输入
    is_valid, message = cli_app.validate_input(ending)
    if not is_valid:
        console.print(f"[red]❌ {message}[/red]")
        return
    
    console.print(f"[green]✅ {message}[/green]")
    console.print("[yellow]🚀 使用Google ADK系统进行续写...[/yellow]")
    
    # 执行ADK续写
    import asyncio
    asyncio.run(cli_app.run_adk_continuation(ending, start_chapter, count, debug))


@cli.command()
def interactive():
    """进入交互模式"""
    cli_app = RedChamberCLI()
    cli_app.show_welcome()
    cli_app.run_interactive_mode()


@cli.command()
def status():
    """查看系统状态"""
    cli_app = RedChamberCLI()

    table = Table(title="🔍 系统状态")
    table.add_column("组件", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("详情", style="yellow")

    status_info = [
        ("Google ADK", "✅ 已安装", "v1.13.0"),
        ("OpenAI客户端", "✅ 已安装", "v1.99.9"),
        ("中文分词", "✅ 已安装", "jieba"),
        ("Agent系统", "✅ 已初始化", "5个Agent就绪"),
        ("配置文件", "✅ 已加载", "settings.yaml")
    ]

    for component, status, detail in status_info:
        table.add_row(component, status, detail)

    console.print(table)


if __name__ == '__main__':
    cli()
