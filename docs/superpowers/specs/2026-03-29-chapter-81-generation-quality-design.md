# Chapter 81 Generation Quality Adjustment Design

## Goal

Improve the chapter 81 minimal end-to-end generation loop so the generated text uses less purposeless dialogue and more narration-driven thematic cohesion, while preserving the current style fit, character voice, and single-chapter workflow.

## Scope

This design is intentionally narrow.

In scope:
- Adjust prompt assembly in `src/generation/context_assembler.py`
- Adjust automatic evaluation and rewrite feedback in `src/generation/literary_judge.py`
- Validate with the existing `run_ch81.py` single-chapter pipeline

Out of scope:
- `StoryState`
- `ForeshadowingKnowledgeBase`
- `StoryDirector`
- Batch generation for chapters 81–120
- New planner or chapter-outline subsystems
- Changes to `ContentWriter`

## Problem Statement

The current chapter 81 output is strong enough in diction and surface style to pass the existing judge, but it still has two quality problems that matter to the user:

1. Dialogue occupies too much of the chapter.
2. Some multi-character exchanges create local activity without sufficiently reinforcing the chapter's core themes: the decline of the Jia household and the deepening but unstable bond between Baoyu and Daiyu.

The current system under-detects these issues because it mainly checks style similarity, forbidden modern vocabulary, and foreshadowing payoff. It does not adequately measure chapter structure, dialogue density, or thematic concentration.

## Design Principles

1. Preserve what is already working.
   - Keep the current single-chapter loop.
   - Keep the current style and character knowledge sources.
   - Keep the current rewrite mechanism.

2. Change logic, not architecture.
   - Do not add a new planning layer.
   - Do not introduce a separate chapter skeleton generator.
   - Do not expand into later roadmap tasks.

3. Prefer explicit chapter guidance over implicit hope.
   - The prompt should state how the chapter should be organized.
   - The judge should evaluate the exact failure modes the user observed.

4. Keep evaluation lightweight and explainable.
   - Use simple heuristics that are easy to understand and tune.
   - Produce actionable rewrite feedback instead of vague approval.

## Proposed Approach

### 1. Strengthen prompt structure in `ContextAssembler`

`ContextAssembler` currently provides source-style examples, character state, foreshadowing instructions, and general requirements. The main weakness is that it does not strongly control chapter organization. The model receives good materials, but not enough guidance about how to distribute narration versus dialogue or how to keep the chapter emotionally and thematically centered.

The fix is to add an explicit chapter-organization block to the user prompt.

#### New prompt requirements

The prompt should explicitly require the chapter to follow this progression:

1. **Opening atmosphere and family condition**
   - Begin with autumnal scenery, household atmosphere, and signs of inner decline.
   - Establish that the Jia household still appears orderly on the surface while carrying inward strain.

2. **Character-centered emotional progression**
   - Move from household atmosphere into the Baoyu–Daiyu emotional thread.
   - Use narration, gesture, silence, and setting as primary carriers of feeling.
   - Use dialogue sparingly and only when it advances the relationship or clarifies tension.

3. **Controlled social scene**
   - If a group scene appears, it should not become a round-robin of voices.
   - Group interaction should serve the larger chapter mood and reveal decline, restraint, or emotional undercurrent.

4. **Closing hook**
   - End with external movement, incoming news, or another disturbance that naturally leads into the next chapter.

#### New narrative constraints

The prompt should also add clear constraints such as:

- The chapter must be narration-led rather than dialogue-led.
- Dialogue must not appear in long uninterrupted stretches.
- Each dialogue passage must serve at least one of these functions:
  - deepen Baoyu and Daiyu's emotional line,
  - reveal household decline or pressure,
  - set up the next turn of events.
- The chapter should return repeatedly to the central themes rather than drifting into lively but low-purpose conversation.

#### Theme elevation

The existing foreshadowing guidance is useful but too weak for this problem. The prompt should add a distinct **chapter theme** section that explicitly names:

- the household's decline,
- the deep but threatened bond between Baoyu and Daiyu.

This theme block should sit alongside, not replace, the existing foreshadowing instructions. Foreshadowing remains about later movement; the theme block controls the emotional center of the current chapter.

### 2. Extend `LiteraryJudge` with dialogue-balance and theme-focus evaluation

`LiteraryJudge` currently computes:
- style similarity,
- voice safety via forbidden modern words,
- foreshadowing payoff.

That is why the current output can score well even when its internal chapter balance is not ideal.

The judge should add two new internal dimensions.

#### `dialogue_balance_score`

This score should estimate whether the chapter is too dependent on direct speech.

Recommended heuristics:

- Split text into paragraphs.
- Count dialogue-dominant paragraphs using quote markers such as `“”` and direct-speech patterns.
- Penalize long runs of consecutive dialogue-dominant paragraphs.
- Penalize a high ratio of dialogue-dominant paragraphs to total paragraphs.
- Reward chapters where narrative/scenic paragraphs clearly outnumber dialogue-dominant paragraphs.

This should stay heuristic-based rather than attempting deep parsing. The goal is not perfect classification; the goal is to catch obviously dialogue-heavy drafts.

#### `theme_focus_score`

This score should estimate whether the chapter repeatedly returns to its intended thematic center.

Recommended signals:

- Presence of decline-related language, imagery, or circumstances: autumn chill, thinning splendor, inward strain, tightening household conditions, subdued festivity.
- Presence of Baoyu–Daiyu emotional tension: concern, restraint, foreboding, mutual understanding under pressure.
- Presence of chapter-closing instability or suspended expectation.
- Penalty when large portions of the chapter appear socially busy without contributing to those lines.

This should be implemented with lightweight lexical and structural signals, not a new semantic retrieval subsystem.

### 3. Reweight overall scoring and feedback

The overall score should be updated so the new dimensions materially affect pass/fail outcomes.

Target behavior:
- A text with strong diction but excessive dialogue should no longer pass comfortably.
- A text with acceptable style but weak thematic concentration should be pushed into rewrite.
- A text that preserves style while improving narration balance and theme cohesion should pass.

The feedback builder should also become specific.

Instead of only reporting generic quality success, it should be able to say things like:
- dialogue is too dense,
- too many consecutive dialogue-heavy paragraphs,
- thematic focus on household decline is weak,
- Baoyu–Daiyu scenes are emotionally relevant but insufficiently integrated with the chapter's main pressure,
- closing movement does not create enough downstream tension.

That feedback will then be injected into the rewrite prompt by the existing `judge_and_rewrite()` loop.

### 4. Keep the rewrite loop, but make it finally useful for this failure mode

The rewrite loop already exists and should remain unchanged in structure.

What changes is the quality of the feedback it sends back into generation.

Expected effect:
- First draft may still overshoot into dialogue.
- Judge flags dialogue density and weak thematic concentration.
- Rewrite prompt explicitly asks for more narration, tighter thematic return, and more functional dialogue.
- Second draft has a much better chance of converging toward the user's target.

## File-Level Changes

### `src/generation/context_assembler.py`

Planned changes:
- Add a chapter-theme block in `_build_user()`.
- Add a chapter-organization block in `_build_user()`.
- Add explicit narration-vs-dialogue constraints in `_build_user()`.
- Keep existing style examples, character state, and foreshadowing sections.
- Avoid large refactors unless a small helper is needed to keep prompt construction readable.

Responsibility after change:
- Not just “assemble context,” but also define the chapter's structural intent clearly enough that the model writes with better balance.

### `src/generation/literary_judge.py`

Planned changes:
- Add helper methods for dialogue-balance scoring.
- Add helper methods for theme-focus scoring.
- Update `JudgementResult` if needed so these dimensions can be inspected or surfaced.
- Reweight the final score formula.
- Update pass/fail gating so the new dimensions matter.
- Expand feedback generation to mention dialogue density and thematic drift.

Responsibility after change:
- Evaluate not just local style safety but also chapter-level balance and thematic cohesion.

### `run_ch81.py`

Planned changes:
- No required structural change.
- If output reporting needs to expose the new sub-scores for debugging, that is acceptable, but only if it stays small and directly useful.

Responsibility after change:
- Remain the validation entrypoint for the minimal loop.

## Data Flow After Change

1. `run_ch81.py` creates `SceneSpec` and assembles prompt context.
2. `ContextAssembler` produces:
   - style examples,
   - character state,
   - foreshadowing instructions,
   - explicit chapter themes,
   - explicit chapter organization and dialogue constraints.
3. `ContentWriter` generates a draft.
4. `LiteraryJudge` evaluates:
   - style similarity,
   - voice safety,
   - foreshadowing,
   - dialogue balance,
   - theme focus.
5. If the draft fails, `judge_and_rewrite()` sends targeted feedback back through the same prompt assembly path.
6. The best passing draft is written to `outputs/phase1/chapter_81.txt` with its report.

## Testing Strategy

Validation should stay tightly scoped to chapter 81.

### Functional validation

- Run the existing `run_ch81.py` flow with real generation.
- Inspect the produced chapter manually.
- Confirm the generated text:
  - contains more narration relative to dialogue,
  - keeps dialogue shorter and more purposeful,
  - makes the Jia household decline feel more present,
  - keeps Baoyu–Daiyu interaction emotionally central,
  - ends with a stronger next-chapter pull.

### Judge validation

Use the generated report to confirm that:
- the new dimensions appear in scoring or feedback,
- dialogue-heavy drafts are no longer treated as unproblematic,
- rewrite feedback points at concrete problems instead of only giving broad approval.

### Regression expectations

The change is successful only if all of the following remain true:
- style remains recognizably close to the original source mode,
- forbidden modern vocabulary checks still work,
- foreshadowing scoring still works,
- the single-chapter workflow remains runnable without introducing new infrastructure.

## Success Criteria

This design succeeds when all of the following are true:

1. The generated chapter still feels stylistically aligned with the current strong result.
2. Dialogue is visibly less dominant.
3. The chapter's emotional and thematic line is more concentrated.
4. The automatic judge can detect the exact failure mode the user identified.
5. The work remains a focused improvement to the chapter 81 minimal loop rather than an expansion into later architecture.

## Alternatives Considered

### Only change the judge
Rejected because it would detect problems later without sufficiently preventing them during first-pass generation.

### Add a separate chapter skeleton generator
Rejected because it is a larger architectural move that belongs with later roadmap tasks, not with this focused adjustment.

### Change `ContentWriter`
Rejected because the issue is not model transport or generation API behavior. The leverage is in prompt structure and evaluation.
