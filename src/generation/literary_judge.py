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

        overall = style_score * 0.40 + voice_score * 0.35 + foreshadowing_score * 0.25
        feedback = self._build_feedback(style_score, voice_score, text)
        passed = overall >= self.THRESHOLD and voice_score >= 7.0

        return JudgementResult(
            score=round(overall, 2),
            style_score=round(style_score, 2),
            voice_score=round(voice_score, 2),
            foreshadowing_score=round(foreshadowing_score, 2),
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

    def _build_feedback(self, style_score: float, voice_score: float, text: str) -> str:
        issues: List[str] = []
        if style_score < 6.5:
            issues.append("叙事风格与原著相似度不足，需更贴近原著语势并减少白话句式")
        found_forbidden = [word for word in FORBIDDEN_WORD_LIST if word in text]
        if voice_score < 7.0 and found_forbidden:
            issues.append(f"出现现代词汇：{'、'.join(found_forbidden)}")
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
