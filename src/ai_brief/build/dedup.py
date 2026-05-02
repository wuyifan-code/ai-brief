"""去重引擎"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


class DedupEngine:
    """去重引擎"""

    def __init__(self, config: dict[str, Any], raw_data_path: Path):
        self.config = config
        self.raw_data_path = raw_data_path
        self.ai_config = config.get("ai", {})
        self.similarity_threshold = self.ai_config.get("dedup_similarity_threshold", 0.85)
        self.window_hours = self.ai_config.get("dedup_window_hours", 72)

    def run(self) -> list[dict[str, Any]]:
        """执行去重"""
        # 加载原始数据
        items = self._load_raw_data()

        # 按 URL 去重
        items = self._dedup_by_url(items)

        # 按标题相似度去重
        items = self._dedup_by_title(items)

        # 与历史数据去重（72小时窗口）
        items = self._dedup_against_history(items)

        return items

    def _load_raw_data(self) -> list[dict[str, Any]]:
        """加载原始数据"""
        if not self.raw_data_path.exists():
            return []

        items = []
        with self.raw_data_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items

    def _dedup_by_url(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """基于 URL 完全匹配去重"""
        seen_urls: set[str] = set()
        deduped: list[dict[str, Any]] = []

        for item in items:
            url = item.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduped.append(item)
            elif not url:
                deduped.append(item)

        return deduped

    def _dedup_by_title(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """基于标题相似度去重"""
        deduped: list[dict[str, Any]] = []

        for item in items:
            title = item.get("title", "").lower()
            is_duplicate = False

            for existing in deduped:
                existing_title = existing.get("title", "").lower()
                similarity = self._calculate_similarity(title, existing_title)

                if similarity >= self.similarity_threshold:
                    # 保留权重更高的
                    if item.get("weight", 0) > existing.get("weight", 0):
                        deduped.remove(existing)
                        deduped.append(item)
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduped.append(item)

        return deduped

    def _dedup_against_history(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """与历史数据去重"""
        history = self._load_history()
        deduped: list[dict[str, Any]] = []

        for item in items:
            is_duplicate = False
            title = item.get("title", "").lower()

            for history_item in history:
                history_title = history_item.get("title", "").lower()
                similarity = self._calculate_similarity(title, history_title)

                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduped.append(item)

        return deduped

    def _load_history(self) -> list[dict[str, Any]]:
        """加载历史数据（72小时窗口）"""
        history: list[dict[str, Any]] = []
        cutoff = datetime.now() - timedelta(hours=self.window_hours)

        data_dir = Path("data/processed")
        if not data_dir.exists():
            return history

        for file in data_dir.glob("*.json"):
            try:
                file_date = datetime.strptime(file.stem, "%Y-%m-%d")
                if file_date >= cutoff:
                    with file.open(encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            history.extend(data)
            except ValueError:
                continue

        return history

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算两个字符串的相似度"""
        return SequenceMatcher(None, s1, s2).ratio()

    def save_processed(self, date: str, items: list[dict[str, Any]]) -> Path:
        """保存处理后的数据"""
        output_path = Path(f"data/processed/{date}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        return output_path
