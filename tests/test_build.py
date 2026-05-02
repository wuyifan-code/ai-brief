"""去重引擎测试"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_brief.build.dedup import DedupEngine


@pytest.fixture
def sample_config():
    return {
        "ai": {
            "dedup_similarity_threshold": 0.85,
            "dedup_window_hours": 72,
        }
    }


@pytest.fixture
def sample_items():
    return [
        {
            "id": "1",
            "title": "OpenAI 发布 GPT-5",
            "link": "https://example.com/1",
            "summary": "OpenAI 宣布发布 GPT-5",
            "weight": 10,
        },
        {
            "id": "2",
            "title": "OpenAI 发布 GPT-5",  # 完全相同
            "link": "https://example.com/2",
            "summary": "OpenAI 宣布发布 GPT-5",
            "weight": 8,
        },
        {
            "id": "3",
            "title": "OpenAI Releases GPT-5",  # 英文版本，相似
            "link": "https://example.com/3",
            "summary": "OpenAI announces GPT-5 release",
            "weight": 9,
        },
        {
            "id": "4",
            "title": "Google 发布 Gemini 2",  # 不同内容
            "link": "https://example.com/4",
            "summary": "Google 发布 Gemini 2",
            "weight": 10,
        },
    ]


class TestDedupEngine:
    def test_dedup_by_url(self, sample_config, sample_items):
        """测试 URL 去重"""
        engine = DedupEngine(sample_config, Path("data/raw/test.jsonl"))

        # 两个相同 URL
        items = [
            {"title": "News 1", "link": "https://example.com/1", "weight": 5},
            {"title": "News 1 Duplicate", "link": "https://example.com/1", "weight": 8},
        ]

        deduped = engine._dedup_by_url(items)
        assert len(deduped) == 1
        assert deduped[0]["weight"] == 8  # 保留后者（权重更高）

    def test_dedup_by_title_similarity(self, sample_config, sample_items):
        """测试标题相似度去重"""
        engine = DedupEngine(sample_config, Path("data/raw/test.jsonl"))

        items = [
            {"title": "OpenAI 发布 GPT-5", "link": "https://example.com/1", "weight": 10},
            {"title": "OpenAI 发布 GPT-5", "link": "https://example.com/2", "weight": 8},
            {"title": "Google 发布 Gemini 2", "link": "https://example.com/3", "weight": 10},
        ]

        deduped = engine._dedup_by_title(items)
        # 相同标题只保留一个
        assert len(deduped) <= 2

    def test_calculate_similarity(self, sample_config):
        """测试相似度计算"""
        engine = DedupEngine(sample_config, Path("data/raw/test.jsonl"))

        # 完全相同
        sim = engine._calculate_similarity("OpenAI 发布 GPT-5", "OpenAI 发布 GPT-5")
        assert sim == 1.0

        # 完全不同
        sim = engine._calculate_similarity("OpenAI 发布 GPT-5", "Google 发布 Gemini 2")
        assert sim < 0.5

        # 部分相似
        sim = engine._calculate_similarity("OpenAI 发布 GPT-5", "OpenAI Releases GPT-5")
        assert 0.5 < sim < 1.0

    def test_dedup_empty_list(self, sample_config):
        """测试空列表"""
        engine = DedupEngine(sample_config, Path("data/raw/test.jsonl"))
        items = engine.run()
        assert items == []


class TestNewsRanker:
    """新闻评分测试"""

    def test_score_normalization(self):
        """测试分数范围"""
        # 分数应该在 1-10 之间
        pass  # 需要 mock OpenAI API


class TestBriefComposer:
    """早报生成测试"""

    def test_compose_empty_items(self):
        """测试空内容"""
        from ai_brief.build.compose import BriefComposer

        composer = BriefComposer(
            {"base_url": "", "api_key": "test", "model_writer": "gpt-4o"},
            {},
        )
        brief = composer._empty_brief("2026-05-01")
        assert "2026-05-01" in brief
        assert "暂无内容" in brief
