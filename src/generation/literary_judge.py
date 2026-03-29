from __future__ import annotations

from dataclasses import dataclass
from typing import List, TYPE_CHECKING

import numpy as np

from src.generation.context_assembler import FORBIDDEN_WORDS, ContextAssembler, SceneSpec
from src.knowledge.character_kb import CharacterKnowledgeBase
from src.knowledge.style_kb import StyleKnowledgeBase

if TYPE_CHECKING:
    from src.generation.content_writer import ContentWriter


FORBIDDEN_WORD_LIST = [word.strip() for word in FORBIDDEN_WORDS.split("、") if word.strip()]


@dataclass
class JudgementResult:
    score: float
    style_score: float
    voice_score: float
    foreshadowing_score: float
    dialogue_balance_score: float
    theme_focus_score: float
    feedback: str
    passed: bool


class LiteraryJudge:
    THRESHOLD = 7.0
    MAX_RETRIES = 3

    def __init__(self, style_kb: StyleKnowledgeBase, character_kb: CharacterKnowledgeBase):
        self.style_kb = style_kb
        self.character_kb = character_kb

    def judge(self, text: str, spec: SceneSpec) -> JudgementResult:
        style_score = self._score_style(text, spec)
        voice_score = self._score_voice(text, spec.characters)
        foreshadowing_score = self._score_foreshadowing(text, spec.foreshadowing_must_payoff)
        dialogue_balance_score = self._score_dialogue_balance(text)
        theme_focus_score = self._score_theme_focus(text, spec)

        overall = (
            style_score * 0.28
            + voice_score * 0.20
            + foreshadowing_score * 0.12
            + dialogue_balance_score * 0.20
            + theme_focus_score * 0.20
        )
        feedback = self._build_feedback(
            style_score,
            voice_score,
            foreshadowing_score,
            dialogue_balance_score,
            theme_focus_score,
            text,
        )
        passed = (
            overall >= self.THRESHOLD
            and voice_score >= 7.0
            and dialogue_balance_score >= 6.0
            and theme_focus_score >= 6.0
        )

        return JudgementResult(
            score=round(overall, 2),
            style_score=round(style_score, 2),
            voice_score=round(voice_score, 2),
            foreshadowing_score=round(foreshadowing_score, 2),
            dialogue_balance_score=round(dialogue_balance_score, 2),
            theme_focus_score=round(theme_focus_score, 2),
            feedback=feedback,
            passed=passed,
        )

    def _score_style(self, text: str, spec: SceneSpec) -> float:
        examples = self.style_kb.search(spec.scene_description, top_k=3)
        if not examples:
            return 6.0
        model = self.style_kb.model
        sample = text[:800]
        text_emb = np.array(model.encode([sample], normalize_embeddings=True), dtype=float)
        example_embs = np.array(model.encode(examples, normalize_embeddings=True), dtype=float)
        text_norm = np.linalg.norm(text_emb, axis=1, keepdims=True)
        example_norms = np.linalg.norm(example_embs, axis=1, keepdims=True)
        text_emb = text_emb / np.clip(text_norm, 1e-8, None)
        example_embs = example_embs / np.clip(example_norms, 1e-8, None)
        sims = np.dot(text_emb, example_embs.T)[0]
        avg = float(np.mean(sims))
        return float(np.clip((avg + 1.0) / 2.0 * 7.0 + 3.0, 3.0, 10.0))

    def _score_voice(self, text: str, characters: List[str]) -> float:
        del characters
        violations = [word for word in FORBIDDEN_WORD_LIST if word in text]
        if not violations:
            return 8.5
        penalty = len(violations) * 2.0
        return float(np.clip(9.5 - penalty, 3.0, 10.0))

    def _score_foreshadowing(self, text: str, must_payoff: List[str]) -> float:
        if not must_payoff:
            return 9.0
        fulfilled = sum(
            1 for item in must_payoff
            if any(keyword.strip() and keyword.strip() in text for keyword in item.split("/"))
        )
        return float(10.0 * fulfilled / len(must_payoff))

    def _score_dialogue_balance(self, text: str) -> float:
        paragraphs = self._split_paragraphs(text)
        if not paragraphs:
            return 5.0

        dominant_flags = [self._is_dialogue_dominant(paragraph) for paragraph in paragraphs]
        dialogue_count = sum(dominant_flags)
        narrative_count = len(paragraphs) - dialogue_count
        dialogue_ratio = dialogue_count / len(paragraphs)
        longest_run = self._longest_true_run(dominant_flags)

        score = 8.8
        if dialogue_count == len(paragraphs):
            score -= 2.2
        if narrative_count <= dialogue_count:
            score -= 1.0
        score -= dialogue_ratio * 2.2
        score -= max(0, longest_run - 1) * 0.8
        return float(np.clip(score, 3.0, 10.0))

    def _score_theme_focus(self, text: str, spec: SceneSpec) -> float:
        paragraphs = self._split_paragraphs(text)
        if not paragraphs:
            return 5.0

        decline_hits = self._count_keyword_hits(
            text,
            ["秋", "风", "叶", "寒", "冷", "清寂", "萧瑟", "衰", "支绌", "吃紧", "不似从前", "家势", "家运"],
        )
        emotion_hits = self._count_keyword_hits(
            text,
            ["宝玉", "黛玉", "心", "泪", "忧", "愁", "怅惘", "相知", "情", "欲说还休"],
        )
        closing_hits = self._count_keyword_hits(
            text,
            ["外头", "急信", "消息", "动静", "忽", "变", "不宁", "下回"],
        )
        thematic_paragraphs = sum(
            1 for paragraph in paragraphs
            if self._count_keyword_hits(paragraph, ["秋", "衰", "家", "宝玉", "黛玉", "情", "忧", "变", "信", "风", "叶"]) >= 2
        )

        score = 4.8
        score += min(2.0, decline_hits * 0.35)
        score += min(2.0, emotion_hits * 0.30)
        score += min(1.2, closing_hits * 0.50)
        score += min(1.2, thematic_paragraphs * 0.30)

        if spec.chapter_num == 81:
            if any(theme in text for theme in ["家运", "家势", "支绌", "不似从前"]):
                score += 0.4
            if "宝玉" in text and "黛玉" in text:
                score += 0.4

        return float(np.clip(score, 3.0, 10.0))

    def _split_paragraphs(self, text: str) -> List[str]:
        return [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]

    def _is_dialogue_dominant(self, paragraph: str) -> bool:
        quote_markers = ['“', '”', '"', '‘', '’', "'"]
        quote_count = sum(paragraph.count(marker) for marker in quote_markers)
        speech_markers = ["道", "说道", "问", "答", "笑道", "叹道"]
        speech_count = sum(paragraph.count(marker) for marker in speech_markers)
        if quote_count >= 2:
            return True
        return speech_count >= 2 and len(paragraph) < 90

    def _longest_true_run(self, flags: List[bool]) -> int:
        longest = 0
        current = 0
        for flag in flags:
            if flag:
                current += 1
                longest = max(longest, current)
            else:
                current = 0
        return longest

    def _count_keyword_hits(self, text: str, keywords: List[str]) -> int:
        return sum(1 for keyword in keywords if keyword and keyword in text)

    def _build_feedback(
        self,
        style_score: float,
        voice_score: float,
        foreshadowing_score: float,
        dialogue_balance_score: float,
        theme_focus_score: float,
        text: str,
    ) -> str:
        issues: List[str] = []
        if style_score < 6.5:
            issues.append("叙事风格与原著相似度不足，需更贴近原著语势并减少白话句式")
        found_forbidden = [word for word in FORBIDDEN_WORD_LIST if word in text]
        if voice_score < 7.0 and found_forbidden:
            issues.append(f"出现现代词汇：{'、'.join(found_forbidden)}")
        if foreshadowing_score < 6.5:
            issues.append("伏笔兑现不足，须补足前文已点出的关节")
        if dialogue_balance_score < 6.5:
            issues.append("对话偏密，叙述承托不足，须压缩连续对白并增补景物、动作、心绪描写")
        if theme_focus_score < 6.5:
            issues.append("主题聚拢不足，须反复回扣家运衰象与宝黛情深而前景未明之势")
        if not issues:
            return "内容质量良好，无明显问题。"
        return "需要改进：" + "；".join(issues)

    async def judge_and_rewrite(
        self,
        text: str,
        spec: SceneSpec,
        writer: "ContentWriter",
        assembler: ContextAssembler,
    ) -> tuple[str, JudgementResult]:
        best_text, best_result = text, self.judge(text, spec)

        for _ in range(self.MAX_RETRIES):
            if best_result.passed:
                break
            system_msg, user_prompt = assembler.assemble(spec)
            user_prompt += f"\n\n【上次评审反馈，本次须针对以下问题改写】\n{best_result.feedback}"
            new_text = await writer.write(system_msg, user_prompt, spec.chapter_num)
            if not new_text:
                break
            new_result = self.judge(new_text, spec)
            if new_result.score > best_result.score:
                best_text, best_result = new_text, new_result

        return best_text, best_result
