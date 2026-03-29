#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行第81回 Phase 1 最小闭环。"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.generation.content_writer import ContentWriter
from src.generation.context_assembler import ContextAssembler, SceneSpec
from src.generation.literary_judge import LiteraryJudge
from src.knowledge.builder import build_style_kb
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.knowledge.style_kb import StyleKnowledgeBase

DEFAULT_HINT = "宝玉和黛玉终成眷属，贾府中兴"
STYLE_KB_DIR = "data/knowledge_base/style"
OUTPUT_DIR = Path("outputs") / "phase1"
CH81_SCENE = SceneSpec(
    chapter_num=81,
    characters=["贾宝玉", "林黛玉", "薛宝钗", "王熙凤"],
    scene_description="第八十回后，贾府诸人表面如常，内里各怀心事；宝玉与黛玉再会，情意更深而前景未明",
    emotional_tone="哀愁",
    previous_summary=(
        "前八十回已写至贾府繁华渐露衰象，宝玉与黛玉情深而多阻，宝钗亦牵连其中，"
        "王熙凤强撑家政而内外交困。第八十一回须承接此势，写出盛筵将散前的人情波动。"
    ),
    foreshadowing_should_plant=["家运将衰", "宝黛情深而终难两全"],
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行第81回 Phase 1 最小闭环")
    parser.add_argument(
        "--hint",
        default=DEFAULT_HINT,
        help="续写提示词，默认使用项目内置结局提示",
    )
    return parser.parse_args()


def load_style_kb() -> StyleKnowledgeBase:
    persist_path = Path(STYLE_KB_DIR)
    if persist_path.exists():
        kb = StyleKnowledgeBase(persist_dir=str(persist_path))
        if kb.count() > 0:
            return kb
        kb.close()
    return build_style_kb(persist_dir=STYLE_KB_DIR)


def save_output(text: str, result) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "chapter_81.txt"
    report_path = OUTPUT_DIR / "chapter_81_report.txt"
    output_path.write_text(text, encoding="utf-8")
    report_path.write_text(
        "\n".join([
            f"score={result.score}",
            f"style_score={result.style_score}",
            f"voice_score={result.voice_score}",
            f"foreshadowing_score={result.foreshadowing_score}",
            f"passed={result.passed}",
            f"feedback={result.feedback}",
        ]),
        encoding="utf-8",
    )
    return output_path


async def main(hint: str) -> int:
    print("=" * 60)
    print("📚 AI续写红楼梦 · Phase 1 · 第81回")
    print("=" * 60)

    settings = Settings()

    print("\n[1/4] 加载/构建风格层知识库...")
    style_kb = load_style_kb()
    char_kb = CharacterKnowledgeBase()

    print("[2/4] 组装上下文 prompt...")
    assembler = ContextAssembler(style_kb, char_kb)
    spec = SceneSpec(**CH81_SCENE.__dict__)
    if hint:
        spec.user_hint = hint
        print(f"      读者方向：{hint}")

    system_msg, user_prompt = assembler.assemble(spec)
    print(f"      system_msg: {len(system_msg)} 字符")
    print(f"      user_prompt: {len(user_prompt)} 字符")

    print("[3/4] 调用模型生成第81回...")
    writer = ContentWriter(settings)
    raw_text = await writer.write(system_msg, user_prompt, chapter_num=81)
    if not raw_text:
        print("❌ 生成失败，请检查 API 配置。")
        style_kb.close()
        return 1

    print("[4/4] LiteraryJudge 评分...")
    judge = LiteraryJudge(style_kb, char_kb)
    final_text, result = await judge.judge_and_rewrite(raw_text, spec, writer, assembler)
    output_path = save_output(final_text, result)
    style_kb.close()

    print("\n" + "=" * 60)
    print("📊 运行结果")
    print("=" * 60)
    print(f"✅ 输出文件: {output_path}")
    print(f"📊 综合评分: {result.score:.2f}/10.0")
    print(f"🪞 风格分: {result.style_score:.2f}")
    print(f"🗣️ 人声分: {result.voice_score:.2f}")
    print(f"🔮 伏笔分: {result.foreshadowing_score:.2f}")
    print(f"✅ 是否通过: {'是' if result.passed else '否'}")
    print(f"💬 反馈: {result.feedback}")
    return 0


if __name__ == "__main__":
    try:
        args = parse_args()
        raise SystemExit(asyncio.run(main(args.hint)))
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        raise SystemExit(130)
