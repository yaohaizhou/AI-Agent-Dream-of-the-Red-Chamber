"""伏笔知识库：管理原著静态伏笔和动态新增伏笔。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ForeshadowingTask:
    must_payoff: List[str]
    should_plant: List[str]
    active_threads: List[str]


class ForeshadowingKnowledgeBase:
    def __init__(
        self,
        canonical_path: str = "data/knowledge_base/foreshadowing/canonical.json",
    ):
        self.canonical: List[Dict[str, Any]] = []
        path = Path(canonical_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        if path.exists():
            self.canonical = json.loads(path.read_text(encoding="utf-8"))

    def get_chapter_tasks(
        self,
        chapter_num: int,
        active_dynamic: Optional[List[str]] = None,
    ) -> ForeshadowingTask:
        must_payoff: List[str] = []
        active_threads: List[str] = []

        for foreshadowing in self.canonical:
            if foreshadowing["status"] == "pending":
                lo, hi = foreshadowing["expected_payoff_range"]
                hint = foreshadowing["hint_text"]
                if lo <= chapter_num <= hi:
                    must_payoff.append(
                        f'{foreshadowing["character"]}的伏笔："{hint}"'
                    )
                elif chapter_num < lo:
                    active_threads.append(hint)

        return ForeshadowingTask(
            must_payoff=must_payoff,
            should_plant=[],
            active_threads=active_threads + (active_dynamic or []),
        )

    def mark_resolved(self, foreshadowing_id: str) -> None:
        for foreshadowing in self.canonical:
            if foreshadowing["id"] == foreshadowing_id:
                foreshadowing["status"] = "resolved"
                break
