#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 入口：连续续写多回，每回可指定用户引导。

用法：
  python3 run_continuation.py --chapters 3
  python3 run_continuation.py --chapters 3 --hints "让宝玉收到一封匿名信" "" "元春宫中传来噩耗"
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings
from src.generation.content_writer import ContentWriter
from src.generation.context_assembler import ContextAssembler
from src.generation.literary_judge import JudgementResult, LiteraryJudge
from src.knowledge.builder import build_style_kb
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase
from src.knowledge.style_kb import StyleKnowledgeBase
from src.story.director import StoryDirector
from src.story.prophecy_analyst import ProphecyAnalyst
from src.story.story_state import StoryState

STYLE_KB_DIR = "data/knowledge_base/style"
STATE_DIR = "outputs/state"
OUTPUT_BASE_DIR = Path("outputs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="连续续写多回红楼梦")
    parser.add_argument("--chapters", type=int, default=3, help="要生成的章节数")
    parser.add_argument("--hints", nargs="*", default=[], help="逐章提示词列表")
    return parser.parse_args()


def load_style_kb() -> StyleKnowledgeBase:
    persist_path = Path(STYLE_KB_DIR)
    if persist_path.exists():
        kb = StyleKnowledgeBase(persist_dir=str(persist_path))
        if kb.count() > 0:
            return kb
        kb.close()
    return build_style_kb(persist_dir=STYLE_KB_DIR)


def save_chapter(out_dir: Path, chapter_num: int, text: str, result: JudgementResult) -> Path:
    chapter_file = out_dir / f"chapter_{chapter_num:03d}.md"
    chapter_file.write_text(
        f"# 第{chapter_num}回\n\n{text}\n\n"
        f"---\n*得分：{result.score:.2f} · 风格：{result.style_score:.2f} · 人物：{result.voice_score:.2f}*\n",
        encoding="utf-8",
    )
    return chapter_file


def summarize_text(text: str, limit: int = 120) -> str:
    compact = "".join(line.strip() for line in text.splitlines() if line.strip())
    return compact[:limit]


async def generate_one_chapter(
    chapter_num: int,
    user_hint: str | None,
    director: StoryDirector,
    assembler: ContextAssembler,
    writer: ContentWriter,
    judge: LiteraryJudge,
    analyst: ProphecyAnalyst,
    state: StoryState,
    out_dir: Path,
) -> tuple[Path | None, JudgementResult | None]:
    print(f"\n{'=' * 50}")
    print(f"📖 生成第{chapter_num}回")
    if user_hint:
        print(f"   读者方向：{user_hint}")

    spec = director.make_spec(chapter_num, user_hint=user_hint or None)
    system_msg, user_prompt = assembler.assemble(spec)

    print("   调用 gpt-5.4...")
    raw_text = await writer.write(system_msg, user_prompt, chapter_num)
    if not raw_text:
        print(f"   ❌ 第{chapter_num}回生成失败")
        return None, None

    final_text, result = await judge.judge_and_rewrite(raw_text, spec, writer, assembler)
    print(f"   得分：{result.score:.2f}/10.0  {'✅' if result.passed else '⚠️'}")

    chapter_path = save_chapter(out_dir, chapter_num, final_text, result)
    analysis = analyst.analyze(
        text=final_text,
        state=state,
        chapter_num=chapter_num,
        chapter_summary=summarize_text(final_text),
    )
    state.update_from_analysis(analysis)
    state.save(chapter_num)
    return chapter_path, result


async def main(chapters: int, hints: list[str]) -> int:
    settings = Settings()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUT_BASE_DIR / f"continuation_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("📚 AI续写红楼梦 · Phase 2")
    print("=" * 60)
    print(f"输出目录：{out_dir}")
    print(f"续写章数：{chapters}")

    style_kb = load_style_kb()
    char_kb = CharacterKnowledgeBase()
    foreshadowing_kb = ForeshadowingKnowledgeBase()
    state = StoryState.load_latest(STATE_DIR)

    assembler = ContextAssembler(style_kb, char_kb)
    writer = ContentWriter(settings)
    judge = LiteraryJudge(style_kb, char_kb)
    analyst = ProphecyAnalyst()
    director = StoryDirector(state, foreshadowing_kb)

    start = state.current_chapter + 1
    generated: list[tuple[int, Path, JudgementResult]] = []

    try:
        for i in range(chapters):
            chapter_num = start + i
            hint = hints[i] if i < len(hints) and hints[i] else None
            chapter_path, result = await generate_one_chapter(
                chapter_num=chapter_num,
                user_hint=hint,
                director=director,
                assembler=assembler,
                writer=writer,
                judge=judge,
                analyst=analyst,
                state=state,
                out_dir=out_dir,
            )
            if chapter_path is None or result is None:
                style_kb.close()
                return 1
            generated.append((chapter_num, chapter_path, result))
    finally:
        style_kb.close()

    print(f"\n🎉 完成！共生成 {len(generated)} 回，保存于 {out_dir}")
    for chapter_num, chapter_path, result in generated:
        print(f"第{chapter_num}回：{chapter_path} · {result.score:.2f}/10.0")
    return 0


if __name__ == "__main__":
    try:
        args = parse_args()
        raise SystemExit(asyncio.run(main(args.chapters, args.hints)))
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        raise SystemExit(130)
