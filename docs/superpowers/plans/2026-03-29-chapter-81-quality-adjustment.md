# Chapter 81 Quality Adjustment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the chapter 81 minimal generation loop produce less dialogue-heavy and more theme-focused text by tightening prompt structure and extending automatic evaluation.

**Architecture:** Keep the existing `run_ch81.py -> ContextAssembler -> ContentWriter -> LiteraryJudge` loop intact. Improve first-pass generation by making `ContextAssembler` specify chapter organization and theme explicitly, then improve rewrite convergence by making `LiteraryJudge` score dialogue balance and theme focus and feed those failures back into the existing rewrite loop.

**Tech Stack:** Python, pytest, numpy, existing generation pipeline, existing style/character knowledge bases.

---

## File Structure

### Files to modify
- `src/generation/context_assembler.py`
  - Add explicit chapter-theme and chapter-organization prompt sections.
  - Add narration-vs-dialogue constraints without changing the public `assemble()` interface.
- `src/generation/literary_judge.py`
  - Extend `JudgementResult` with two new sub-scores.
  - Add lightweight paragraph-based heuristics for dialogue balance and theme focus.
  - Reweight final scoring and expand feedback.
- `run_ch81.py`
  - Surface the new sub-scores in the text report so validation output reflects the new judging dimensions.
- `tests/generation/test_context_assembler.py`
  - Add assertions for the new prompt sections and structural constraints.
- `tests/generation/test_literary_judge.py`
  - Add tests for dialogue-heavy penalties, theme-focus rewards, and expanded feedback.

### Files to keep unchanged
- `src/generation/content_writer.py`
- `src/knowledge/*`
- orchestration and later-phase roadmap files

---

### Task 1: Strengthen chapter structure prompts in `ContextAssembler`

**Files:**
- Modify: `src/generation/context_assembler.py:11-125`
- Test: `tests/generation/test_context_assembler.py:50-109`

- [x] **Step 1: Write the failing tests**

Add these tests to `tests/generation/test_context_assembler.py` below the existing prompt tests:

```python
def test_user_prompt_contains_chapter_theme_block(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉"],
        scene_description="秋日宝黛在园中对话，感时伤怀",
        emotional_tone="哀愁",
    )
    _, user_prompt = assembler.assemble(spec)

    assert "【本章主题】" in user_prompt
    assert "家运将衰" in user_prompt
    assert "宝黛情深而前景未明" in user_prompt


def test_user_prompt_contains_chapter_organization_block(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉", "王熙凤"],
        scene_description="家宴之后宝黛再会，外头忽有急信",
        emotional_tone="哀愁",
    )
    _, user_prompt = assembler.assemble(spec)

    assert "【本章章法】" in user_prompt
    assert "先写秋意与家势" in user_prompt
    assert "再入人物情事" in user_prompt
    assert "末段须以外部消息或动静收束" in user_prompt


def test_user_prompt_limits_dialogue_density(tmp_path, monkeypatch):
    style_kb = make_kb(tmp_path, monkeypatch)
    char_kb = CharacterKnowledgeBase()
    assembler = ContextAssembler(style_kb, char_kb)

    spec = SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉", "薛宝钗"],
        scene_description="众人小宴后各怀心事",
        emotional_tone="哀愁",
    )
    _, user_prompt = assembler.assemble(spec)

    assert "叙述须多于对话" in user_prompt
    assert "不得连缀成长段轮番答话" in user_prompt
    assert "每段对话都须承担" in user_prompt
```

- [x] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/generation/test_context_assembler.py -q
```

Expected: FAIL because `【本章主题】`, `【本章章法】`, and the new dialogue-balance constraints are not present in the prompt yet.

- [x] **Step 3: Write the minimal implementation**

Update `src/generation/context_assembler.py` so `_build_user()` emits the new sections. Keep `assemble()` and `SceneSpec` compatible. Replace the current `_build_user()` body with this version and add the two helpers below it:

```python
    def _build_user(self, spec: SceneSpec) -> str:
        parts: List[str] = []

        if spec.previous_summary:
            parts += ["【前情提要】", spec.previous_summary, ""]

        character_lines = self._build_character_constraints(spec.characters)
        if character_lines:
            parts += ["【本章人物状态】"] + character_lines + [""]

        parts += ["【本章主题}", *self._build_theme_lines(spec), ""]
        parts += ["【本章章法】", *self._build_structure_lines(spec), ""]
        parts += ["【叙述约束】", *self._build_narration_constraints(), ""]

        if spec.foreshadowing_must_payoff:
            parts.append("【本章伏笔指令】")
            parts.append("必须兑现：")
            for item in spec.foreshadowing_must_payoff:
                parts.append(f"- {item}")
            parts.append("")

        if spec.foreshadowing_should_plant:
            if "【本章伏笔指令】" not in parts:
                parts.append("【本章伏笔指令】")
            parts.append("建议埋设：")
            for item in spec.foreshadowing_should_plant:
                parts.append(f"- {item}")
            parts.append("")

        if spec.user_hint:
            parts += ["【读者方向（本章须体现）】", spec.user_hint, ""]

        parts += [
            "【续写任务】",
            f"请续写《红楼梦》第{spec.chapter_num}回，约2500字。",
            f"场景：{spec.scene_description}",
            f"情感基调：{spec.emotional_tone}",
            f"禁用现代词汇：{FORBIDDEN_WORDS}",
            "要求：",
            "1. 开头须自然承接前情。",
            "2. 对话须贴合人物身份与性情。",
            "3. 结尾须留下可引下回的余意或悬念。",
            "4. 严格模仿 system 中提供的原著范例语感。",
            "5. 不得出现现代口语、解释腔和网文化抒情。",
        ]
        return "\n".join(parts)

    def _build_theme_lines(self, spec: SceneSpec) -> List[str]:
        lines = [
            "- 家运将衰：须写出贾府表面如常、内里吃紧的气象。",
            "- 宝黛情深而前景未明：须写出二人相知愈深，却更觉世事难凭。",
        ]
        if spec.foreshadowing_should_plant:
            lines.extend(f"- 伏脉关联：{item}" for item in spec.foreshadowing_should_plant)
        return lines

    def _build_structure_lines(self, spec: SceneSpec) -> List[str]:
        del spec
        return [
            "- 先写秋意与家势，以景与人心相映，点出衰飒之感。",
            "- 再入人物情事，以叙述、动作、神色、停顿承托情绪，不可径以长对答铺写。",
            "- 若写多人同席或同场，不得连缀成长段轮番答话，须使场面服务于家势与情势。",
            "- 末段须以外部消息或动静收束，使下回有可接之变。",
        ]

    def _build_narration_constraints(self) -> List[str]:
        return [
            "- 叙述须多于对话，景物、动作、神情、心事要成为主要承载。",
            "- 对话不可接连数段铺陈，尤不可只图热闹。",
            "- 每段对话都须承担推进情意、显出家势、或引出后变三者之一。",
            "- 章中须反复回扣秋意、衰象、隐忧，不可写散。",
        ]
```

Immediately fix the typo in the inserted block header so the line is exactly:

```python
        parts += ["【本章主题】", *self._build_theme_lines(spec), ""]
```

- [x] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/generation/test_context_assembler.py -q
```

Expected: PASS, including the three new tests and the existing prompt tests.

- [x] **Step 5: Commit**

Run:
```bash
git add tests/generation/test_context_assembler.py src/generation/context_assembler.py
git commit -m "feat: tighten chapter 81 prompt structure"
```

---

### Task 2: Add dialogue-balance and theme-focus scoring to `LiteraryJudge`

**Files:**
- Modify: `src/generation/literary_judge.py:19-120`
- Test: `tests/generation/test_literary_judge.py:22-115`

- [x] **Step 1: Write the failing tests**

Add these constants and tests to `tests/generation/test_literary_judge.py` after `BAD_TEXT`:

```python
DIALOGUE_HEAVY_TEXT = """
宝玉道：\"林妹妹，你今日可好？\"
黛玉道：\"也不过如此。\"
宝玉道：\"我心里惦着你。\"
黛玉道：\"你又来哄我。\"
宝玉道：\"我几时哄你了？\"
黛玉道：\"谁知道呢。\"
"""

THEME_FOCUSED_TEXT = """
如今贾府表面仍照旧例行事，内里却渐见支绌之象。秋气一天紧似一天，园中草木也带出衰声。
宝玉自外头回来，见潇湘馆竹影沉沉，心下先有三分怅惘。黛玉虽只淡淡说了两句，眉间眼底却都是欲说还休之意。
二人并不多话，只因彼此都知眼前光景一年不似一年，便连这一点相见之情，也像隔着风露与世事。
说话间，外头忽有人来传急信，满园静气顿时一变，越发显出繁华将尽而事变将来的意思。
"""


def test_dialogue_heavy_text_gets_lower_dialogue_balance_score(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(DIALOGUE_HEAVY_TEXT, make_spec())
    assert result.dialogue_balance_score < 7.0


def test_theme_focused_text_gets_higher_theme_focus_score(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(THEME_FOCUSED_TEXT, make_spec())
    assert result.theme_focus_score >= 8.0


def test_dialogue_heavy_text_feedback_mentions_dialogue_density(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(DIALOGUE_HEAVY_TEXT, make_spec())
    assert "对话" in result.feedback


def test_judgement_result_exposes_new_subscores(tmp_path, monkeypatch):
    judge = make_judge(tmp_path, monkeypatch)
    result = judge.judge(THEME_FOCUSED_TEXT, make_spec())
    assert hasattr(result, "dialogue_balance_score")
    assert hasattr(result, "theme_focus_score")
```

Replace `GOOD_TEXT` with a version that is narrative-led so the pass expectation still makes sense after the new scoring rules:

```python
GOOD_TEXT = """
且说那日天色阴沉，潇湘馆前竹影筛窗，落叶无声。宝玉缓步来到阶前，见黛玉倚窗而坐，虽只淡淡抬头，眉间却先有几分秋意。
宝玉低声问了一句安，黛玉也只答了一句。二人并不多说，而彼此心上都明白眼前光景一年紧似一年，连这一点相见之情也添了几分难言之重。
忽听外头脚步忙乱，似有急话传来，馆中清寂之气顿时一变。
"""
```

Update `make_spec()` so it carries the same thematic target as the real chapter:

```python
def make_spec():
    return SceneSpec(
        chapter_num=81,
        characters=["贾宝玉", "林黛玉"],
        scene_description="宝黛秋日相遇",
        emotional_tone="哀愁",
        foreshadowing_should_plant=["家运将衰", "宝黛情深而终难两全"],
    )
```

- [x] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/generation/test_literary_judge.py -q
```

Expected: FAIL because `JudgementResult` does not yet expose `dialogue_balance_score` or `theme_focus_score`, and the judge does not yet mention dialogue density in feedback.

- [x] **Step 3: Write the minimal implementation**

Update `src/generation/literary_judge.py` with the following changes.

First, replace `JudgementResult` with:

```python
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
```

Then replace `judge()` with:

```python
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
            style_score=style_score,
            voice_score=voice_score,
            dialogue_balance_score=dialogue_balance_score,
            theme_focus_score=theme_focus_score,
            text=text,
        )
        passed = (
            overall >= self.THRESHOLD
            and voice_score >= 7.0
            and dialogue_balance_score >= 6.5
            and theme_focus_score >= 6.5
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
```

Add these helpers below `_score_foreshadowing()`:

```python
    def _score_dialogue_balance(self, text: str) -> float:
        paragraphs = self._split_paragraphs(text)
        if not paragraphs:
            return 5.0

        dialogue_flags = [self._is_dialogue_dominant(paragraph) for paragraph in paragraphs]
        dialogue_count = sum(dialogue_flags)
        ratio = dialogue_count / len(paragraphs)

        longest_run = 0
        current_run = 0
        for is_dialogue in dialogue_flags:
            if is_dialogue:
                current_run += 1
                longest_run = max(longest_run, current_run)
            else:
                current_run = 0

        score = 9.0
        score -= ratio * 4.0
        if longest_run >= 3:
            score -= (longest_run - 2) * 1.2
        if dialogue_count == len(paragraphs):
            score -= 1.0
        return float(np.clip(score, 3.0, 10.0))

    def _score_theme_focus(self, text: str, spec: SceneSpec) -> float:
        keywords = [
            "秋", "风", "叶", "寒", "冷", "清寂", "萧瑟", "衰", "愁", "隐忧",
            "家运", "家势", "支绌", "吃紧", "不似从前", "宝玉", "黛玉", "情", "泪", "心事",
            "变故", "急信", "外头", "消息", "下回", "不宁",
        ]
        if spec.foreshadowing_should_plant:
            keywords.extend(spec.foreshadowing_should_plant)

        hits = sum(1 for keyword in keywords if keyword and keyword in text)
        paragraphs = self._split_paragraphs(text)
        paragraph_hits = sum(1 for paragraph in paragraphs if any(keyword in paragraph for keyword in keywords))

        score = 4.5
        score += min(hits * 0.25, 3.0)
        if paragraphs:
            score += min(paragraph_hits / len(paragraphs) * 2.5, 2.5)
        if any(token in text for token in ["急信", "消息", "变故", "外头"]):
            score += 0.7
        return float(np.clip(score, 3.0, 10.0))

    def _split_paragraphs(self, text: str) -> List[str]:
        return [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]

    def _is_dialogue_dominant(self, paragraph: str) -> bool:
        quote_count = paragraph.count("“") + paragraph.count("”") + paragraph.count('"') + paragraph.count("‘") + paragraph.count("’")
        speech_markers = ["道", "说道", "笑道", "问", "答", "低声", "叹道"]
        marker_hits = sum(paragraph.count(marker) for marker in speech_markers)
        return quote_count >= 2 or marker_hits >= 2
```

Then replace `_build_feedback()` with:

```python
    def _build_feedback(
        self,
        style_score: float,
        voice_score: float,
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

        if dialogue_balance_score < 6.5:
            issues.append("对话偏密，叙述承托不足，须压缩连续对白并增补景物、动作、心绪描写")

        if theme_focus_score < 6.5:
            issues.append("主题聚拢不足，须反复回扣家运衰象与宝黛情深而前景未明之势")

        if not issues:
            return "内容质量较好，叙述与主题较为集中。"
        return "需要改进：" + "；".join(issues)
```

- [x] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/generation/test_literary_judge.py -q
```

Expected: PASS, including the existing pass/fail tests and the new sub-score/feedback tests.

- [x] **Step 5: Commit**

Run:
```bash
git add tests/generation/test_literary_judge.py src/generation/literary_judge.py
git commit -m "feat: score dialogue balance and theme focus"
```

---

### Task 3: Surface new judge signals in the chapter 81 report

**Files:**
- Modify: `run_ch81.py:59-75,114-123`
- Test: `tests/test_run_ch81.py:10-19`

- [x] **Step 1: Write the failing test**

Extend `tests/test_run_ch81.py` with a pure formatting test so the reporting contract is explicit without requiring a real model call:

```python
from types import SimpleNamespace

from run_ch81 import save_output


def test_save_output_writes_new_judge_subscores(tmp_path, monkeypatch):
    monkeypatch.setattr("run_ch81.OUTPUT_DIR", tmp_path)
    result = SimpleNamespace(
        score=8.4,
        style_score=8.2,
        voice_score=8.5,
        foreshadowing_score=9.0,
        dialogue_balance_score=7.3,
        theme_focus_score=8.1,
        passed=True,
        feedback="内容质量较好，叙述与主题较为集中。",
    )

    output_path = save_output("正文", result)
    report = (tmp_path / "chapter_81_report.txt").read_text(encoding="utf-8")

    assert output_path == tmp_path / "chapter_81.txt"
    assert "dialogue_balance_score=7.3" in report
    assert "theme_focus_score=8.1" in report
```

- [x] **Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_run_ch81.py -q
```

Expected: FAIL because `save_output()` does not yet write the new sub-score lines.

- [x] **Step 3: Write the minimal implementation**

Update `run_ch81.py` in `save_output()` so the report lines become:

```python
    report_path.write_text(
        "\n".join([
            f"score={result.score}",
            f"style_score={result.style_score}",
            f"voice_score={result.voice_score}",
            f"foreshadowing_score={result.foreshadowing_score}",
            f"dialogue_balance_score={result.dialogue_balance_score}",
            f"theme_focus_score={result.theme_focus_score}",
            f"passed={result.passed}",
            f"feedback={result.feedback}",
        ]),
        encoding="utf-8",
    )
```

Then update the printed runtime summary in `main()` to include:

```python
    print(f"🗨️ 对话平衡分: {result.dialogue_balance_score:.2f}")
    print(f"🎯 主题聚拢分: {result.theme_focus_score:.2f}")
```

Place those lines between the existing foreshadowing line and the pass/fail line.

- [x] **Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_run_ch81.py -q
```

Expected: PASS for both the existing CLI help test and the new report-formatting test.

- [x] **Step 5: Run the focused regression suite**

Run:
```bash
pytest tests/generation/test_context_assembler.py tests/generation/test_literary_judge.py tests/test_run_ch81.py -q
```

Expected: PASS across all targeted tests.

- [x] **Step 6: Validate the real chapter 81 loop**

Run:
```bash
python run_ch81.py
```

Expected:
- Command exits with code 0.
- `outputs/phase1/chapter_81.txt` is regenerated.
- `outputs/phase1/chapter_81_report.txt` contains `dialogue_balance_score=` and `theme_focus_score=` lines.
- Manual inspection shows less dialogue dominance and stronger thematic concentration than the earlier draft.

- [x] **Step 7: Commit**

Run:
```bash
git add tests/test_run_ch81.py run_ch81.py outputs/phase1/chapter_81_report.txt outputs/phase1/chapter_81.txt
git commit -m "feat: expose chapter 81 quality balance signals"
```

If `outputs/phase1/*` is intentionally not tracked in this repository state, omit those two output files from `git add` and commit only:

```bash
git add tests/test_run_ch81.py run_ch81.py
git commit -m "feat: expose chapter 81 quality balance signals"
```

---

## Self-Review

### Spec coverage
- Prompt structure changes: covered by Task 1.
- Dialogue-balance and theme-focus scoring: covered by Task 2.
- Better rewrite feedback: covered by Task 2.
- Validation through the existing single-chapter loop: covered by Task 3.
- No expansion into later roadmap systems: enforced by file scope across all tasks.

### Placeholder scan
- No `TODO`, `TBD`, or deferred placeholders remain.
- Every code-changing step includes concrete code blocks.
- Every validation step includes exact commands and expected outcomes.

### Type consistency
- `JudgementResult` consistently includes `dialogue_balance_score` and `theme_focus_score` in Task 2 and Task 3.
- `save_output()` in Task 3 consumes the same names introduced in Task 2.
- `ContextAssembler` public interface remains unchanged, so Task 1 does not introduce downstream signature drift.
