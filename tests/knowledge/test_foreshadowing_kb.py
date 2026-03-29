import json
from pathlib import Path

from src.knowledge.foreshadowing_kb import ForeshadowingKnowledgeBase


def write_canonical(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "id": "f001",
                    "source_chapter": 5,
                    "hint_text": "玉带林中挂，金簪雪里埋",
                    "character": "林黛玉",
                    "expected_payoff_range": [95, 115],
                    "payoff_keywords": ["黛玉", "病逝"],
                    "status": "pending",
                },
                {
                    "id": "f002",
                    "source_chapter": 5,
                    "hint_text": "二十年来辨是非，榴花开处照宫闱",
                    "character": "元春",
                    "expected_payoff_range": [83, 92],
                    "payoff_keywords": ["元春", "宫中"],
                    "status": "pending",
                },
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_get_chapter_tasks_returns_must_payoff_in_payoff_window(tmp_path):
    canonical = tmp_path / "canonical.json"
    write_canonical(canonical)
    kb = ForeshadowingKnowledgeBase(canonical_path=str(canonical))

    tasks = kb.get_chapter_tasks(83)

    assert tasks.must_payoff == ['元春的伏笔："二十年来辨是非，榴花开处照宫闱"']


def test_get_chapter_tasks_generates_should_plant_from_future_threads(tmp_path):
    canonical = tmp_path / "canonical.json"
    write_canonical(canonical)
    kb = ForeshadowingKnowledgeBase(canonical_path=str(canonical))

    tasks = kb.get_chapter_tasks(83)

    assert '林黛玉的伏笔待续："玉带林中挂，金簪雪里埋"' in tasks.should_plant


def test_get_chapter_tasks_keeps_dynamic_threads_in_active_threads(tmp_path):
    canonical = tmp_path / "canonical.json"
    write_canonical(canonical)
    kb = ForeshadowingKnowledgeBase(canonical_path=str(canonical))

    tasks = kb.get_chapter_tasks(83, active_dynamic=["宝玉疑心有人暗中传信"])

    assert "宝玉疑心有人暗中传信" in tasks.active_threads


def test_mark_resolved_persists_to_canonical_file(tmp_path):
    canonical = tmp_path / "canonical.json"
    write_canonical(canonical)
    kb = ForeshadowingKnowledgeBase(canonical_path=str(canonical))

    kb.mark_resolved("f002")

    reloaded = ForeshadowingKnowledgeBase(canonical_path=str(canonical))
    resolved = next(item for item in reloaded.canonical if item["id"] == "f002")
    assert resolved["status"] == "resolved"
