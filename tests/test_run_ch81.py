import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import run_ch81
from run_ch81 import save_output


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "run_ch81.py"


def test_run_ch81_requires_no_args_and_supports_hint_flag():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--hint" in result.stdout


def test_save_output_writes_new_judge_subscores(tmp_path, monkeypatch):
    monkeypatch.setattr(run_ch81, "OUTPUT_DIR", tmp_path)
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
