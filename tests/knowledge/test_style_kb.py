import pytest
import tempfile
from src.knowledge.style_kb import StyleKnowledgeBase, StyleChunk


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
