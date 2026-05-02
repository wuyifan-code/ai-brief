"""RSS 资讯采集器"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import feedparser
import httpx
from dateutil import parser as date_parser


class RSSCollector:
    """RSS 采集器"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.rss_feeds = config.get("rss", [])

    def collect(self, date: str) -> list[dict[str, Any]]:
        """采集指定日期的 RSS 资讯"""
        all_items: list[dict[str, Any]] = []
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

        for feed in self.rss_feeds:
            if not feed.get("enabled", True):
                continue

            try:
                items = self._fetch_feed(feed, target_date)
                all_items.extend(items)
            except Exception as e:
                print(f"[RSS] 采集失败 {feed['url']}: {e}")

        # 保存到 raw data
        self._save_raw(date, all_items)
        return all_items

    def _fetch_feed(self, feed: dict, target_date: datetime) -> list[dict[str, Any]]:
        """获取单个 RSS feed"""
        url = feed["url"]
        category = feed.get("category", "General")
        weight = feed.get("weight", 5)

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()

        feed_data = feedparser.parse(response.text)
        items: list[dict[str, Any]] = []

        for entry in feed_data.entries:
            published = self._parse_date(entry.get("published"))
            if published is None:
                published = datetime.now()

            # 检查日期是否在目标日期或之前
            if published.date() > target_date:
                continue

            # 检查是否在 72 小时窗口内
            window_start = target_date - timedelta(days=3)
            if published.date() < window_start:
                continue

            item = {
                "id": entry.get("id") or entry.get("link"),
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": self._clean_summary(entry.get("summary", "")),
                "published": published.isoformat(),
                "source": feed_data.feed.get("title", url),
                "source_url": url,
                "category": category,
                "weight": weight,
                "type": "rss",
            }
            items.append(item)

        return items

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            return date_parser.parse(date_str)
        except Exception:
            return None

    def _clean_summary(self, summary: str) -> str:
        """清理摘要文本"""
        import re

        # 移除 HTML 标签
        summary = re.sub(r"<[^>]+>", "", summary)
        # 移除多余空白
        summary = re.sub(r"\s+", " ", summary).strip()
        # 截断
        if len(summary) > 500:
            summary = summary[:500] + "..."
        return summary

    def _save_raw(self, date: str, items: list[dict[str, Any]]) -> None:
        """保存原始数据"""
        raw_path = Path(f"data/raw/{date}.jsonl")
        raw_path.parent.mkdir(parents=True, exist_ok=True)

        with raw_path.open("a", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
