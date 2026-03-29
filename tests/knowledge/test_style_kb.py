import shutil
from pathlib import Path

import numpy as np
import pytest
import tempfile
from src.knowledge.builder import build_style_kb
from src.knowledge.style_kb import StyleKnowledgeBase, StyleChunk


class DummyEmbeddings:
    def encode(self, texts, normalize_embeddings=True):
        vectors = []
        for text in texts:
            seed = sum(ord(ch) for ch in text)
            vectors.append([
                float((seed % 97) + 1),
                float((len(text) % 89) + 1),
                float((text.count("道") + text.count("问") + text.count("答") + 1)),
            ])
        return np.array(vectors, dtype=float)


def make_test_kb(tmp_dir):
    kb = StyleKnowledgeBase(persist_dir=tmp_dir)
    chunks = [
        StyleChunk(
            text="只见宝玉歪在榻上，手执一卷《庄子》，却并未翻动。",
            chapter_num=27,
            paragraph_type="narrative",
            characters_present=["贾宝玉"],
            location="怡红院",
            emotional_tone="闲散",
        ),
        StyleChunk(
            text="黛玉道：'你这话从何说起？'宝玉笑道：'好妹妹，你别恼。'",
            chapter_num=32,
            paragraph_type="dialogue",
            characters_present=["林黛玉", "贾宝玉"],
            location="潇湘馆",
            emotional_tone="哀愁",
        ),
    ]
    kb.add_chunks(chunks)
    return kb


def test_count(tmp_path):
    kb = make_test_kb(str(tmp_path))
    assert kb.count() == 2


def test_search_returns_results(tmp_path):
    kb = make_test_kb(str(tmp_path))
    results = kb.search("宝玉读书", top_k=2)
    assert len(results) >= 1
    assert isinstance(results[0], str)


def test_search_filter_by_paragraph_type(tmp_path):
    kb = make_test_kb(str(tmp_path))
    results = kb.search("宝玉对话", paragraph_type="dialogue", top_k=2)
    assert len(results) >= 1
    # All returned texts should come from dialogue chunks
    assert "道：" in results[0] or "笑道" in results[0]


def test_search_empty_kb(tmp_path):
    kb = StyleKnowledgeBase(persist_dir=str(tmp_path))
    results = kb.search("任意查询", top_k=3)
    assert results == []


def test_build_style_kb_rebuilds_cleanly_and_persists_dialogue_search(tmp_path, monkeypatch):
    source = tmp_path / "hongloumeng_sample.md"
    source.write_text(
        "### 第一回\n\n"
        "贾宝玉在窗前看雨，听见檐下铁马叮当，想起连日家中琐事，心中烦闷，却又不好向人诉说，只得独自出神。\n\n"
        "黛玉道：“你这话从何说起？”宝玉笑道：“好妹妹，你别恼，我不过见你连日无精打采，所以特来解闷。”二人你一言我一语，说了许久。\n\n"
        "### 第二回\n\n"
        "王熙凤向众人说道：“今日且先歇息，明日再议。”众人听了，方各自散去，院中灯影摇曳，丫鬟婆子仍来回照应，不敢稍懈。\n",
        encoding="utf-8",
    )
    persist_dir = tmp_path / "style"
    persist_dir.mkdir()
    (persist_dir / "stale.txt").write_text("stale", encoding="utf-8")

    monkeypatch.setattr(StyleKnowledgeBase, "model", property(lambda self: DummyEmbeddings()))

    kb = build_style_kb(source=str(source), persist_dir=str(persist_dir))
    assert kb.count() > 0

    sqlite_path = persist_dir / "chroma.sqlite3"
    assert sqlite_path.exists()

    shutil.copy2(sqlite_path, sqlite_path.with_suffix(".bak"))
    sqlite_path.chmod(0o444)

    rebuilt = build_style_kb(source=str(source), persist_dir=str(persist_dir))
    assert rebuilt.count() > 0
    assert not (persist_dir / "stale.txt").exists()
    assert (tmp_path / "characters" / "canonical.json").exists()

    persisted = StyleKnowledgeBase(persist_dir=str(persist_dir))
    dialogue_results = persisted.search("宝玉和黛玉对话", paragraph_type="dialogue", top_k=3)
    assert dialogue_results
    assert any("道" in result for result in dialogue_results)
