"""RSS 采集器测试"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_brief.collect.rss import RSSCollector


@pytest.fixture
def sample_config():
    return {
        "rss": [
            {
                "url": "https://example.com/feed.xml",
                "category": "AI",
                "weight": 8,
                "enabled": True,
            }
        ]
    }


@pytest.fixture
def sample_feed_content():
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Example Feed</title>
        <link>https://example.com</link>
        <item>
            <title>Test News</title>
            <link>https://example.com/news/1</link>
            <description>This is a test news item.</description>
            <pubDate>Thu, 01 May 2026 10:00:00 GMT</pubDate>
        </item>
        <item>
            <title>Another News</title>
            <link>https://example.com/news/2</link>
            <description>Another test news item.</description>
            <pubDate>Tue, 29 Apr 2026 10:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""


class TestRSSCollector:
    def test_collect_valid_feed(self, sample_config, sample_feed_content):
        """测试正常 RSS 采集"""
        collector = RSSCollector(sample_config)

        with patch("httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = sample_feed_content
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            items = collector.collect("2026-05-01")

            assert len(items) == 1  # 只能采集到 2026-05-01 及之前的
            assert items[0]["title"] == "Test News"
            assert items[0]["link"] == "https://example.com/news/1"
            assert items[0]["category"] == "AI"

    def test_collect_empty_feed(self, sample_config):
        """测试空 feed"""
        collector = RSSCollector(sample_config)

        empty_feed = """<?xml version="1.0"?>
<rss><channel><title>Empty</title></channel></rss>"""

        with patch("httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = empty_feed
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            items = collector.collect("2026-05-01")
            assert len(items) == 0

    def test_collect_disabled_feed(self, sample_config):
        """测试禁用的 feed"""
        sample_config["rss"][0]["enabled"] = False
        collector = RSSCollector(sample_config)

        items = collector.collect("2026-05-01")
        assert len(items) == 0

    def test_collect_outdated_item(self, sample_config, sample_feed_content):
        """测试过滤过期内容"""
        collector = RSSCollector(sample_config)

        # 4 天前的内容应该被过滤
        old_date = (datetime.now() - timedelta(days=4)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        old_feed = sample_feed_content.replace("Tue, 29 Apr 2026", old_date[:16])

        with patch("httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = old_feed
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            items = collector.collect("2026-05-01")
            # 4 天前 > 3 天窗口期，应该被过滤
            assert len(items) == 0

    def test_clean_summary(self, sample_config):
        """测试摘要清理"""
        collector = RSSCollector(sample_config)

        # 测试 HTML 标签移除
        summary = collector._clean_summary("<p>Test <b>bold</b> content</p>")
        assert "<" not in summary
        assert ">" not in summary
        assert "Test bold content" in summary

        # 测试超长内容截断
        long_summary = "a" * 600
        summary = collector._clean_summary(long_summary)
        assert len(summary) <= 503  # 500 + "..."
